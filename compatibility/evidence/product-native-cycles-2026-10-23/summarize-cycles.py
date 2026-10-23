"""Reconcile immutable Cycles build, packaging, discovery, and execution receipts."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    path = HERE / name
    with path.open("x") as output:
        output.write(json.dumps(value, indent=2) + "\n")
    return identity(path)


build_path = HERE / "build.json"
build = read(build_path)
failed_path = HERE / "cycles/native-reference.json"
failed = read(failed_path)
registered_path = HERE / "cycles-runtime-libraries/native-reference.json"
registered = read(registered_path)
whole_path = HERE / "cycles-unfiltered-supplementary/native-reference.json"
whole = read(whole_path)
stage_path = HERE / "runtime-library-staging/report.json"
stage = read(stage_path)
observation_path = HERE / "procfs-memory-observation.json"
observation = read(observation_path)
prior_path = REPO / "compatibility/evidence/product-native-gtest-2026-10-23/summary.json"
prior = read(prior_path)
prior_cases_path = Path(prior["source_qualified_observations"]["path"])
assert identity(prior_cases_path) == prior["source_qualified_observations"]
prior_cases = read(prior_cases_path)["observations"]
assert build["returncode"] == 0 and build["status"] == "built"
assert stage["status"] == "verified_staged"
assert not failed["cases"] and failed["execution"]["returncode"] != 0
assert registered["artifact"] == whole["artifact"] == build["artifact"]
assert registered["all_observed_source_identities_resolved"] and whole["all_observed_source_identities_resolved"]
assert registered["name_multiplicities_match"] and whole["name_multiplicities_match"]
assert registered["execution"]["returncode"] == whole["execution"]["returncode"] == 0
reg_ids = {case["case_id"] for case in registered["cases"]}
whole_ids = {case["case_id"] for case in whole["cases"]}
prior_ids = {case["case_id"] for case in prior_cases}
assert len(reg_ids) == len(registered["cases"]) and len(whole_ids) == len(whole["cases"])
assert reg_ids < whole_ids and not (whole_ids & prior_ids)
additional = [case for case in whole["cases"] if case["case_id"] not in reg_ids]
for case in whole["cases"]:
    if case["case_id"] in reg_ids:
        original = next(item for item in registered["cases"] if item["case_id"] == case["case_id"])
        assert case["outcome"] == original["outcome"]
reconciliation = {
    "schema": 1,
    "source_commit": registered["source_commit"],
    "artifact": registered["artifact"],
    "registered_receipt": identity(registered_path),
    "supplementary_receipt": identity(whole_path),
    "registered_case_count": len(reg_ids),
    "whole_binary_case_count": len(whole_ids),
    "overlap_count": len(reg_ids & whole_ids),
    "additional_count": len(additional),
    "additional_counts_by_suite": dict(Counter(case["attributes"]["classname"] for case in additional)),
    "additional_cases": [{key: case[key] for key in ("case_id", "identity", "outcome", "source_location")} for case in additional],
    "all_overlapping_outcomes_agree": True,
    "additional_cases_executed_by_original_ctest_filter": False,
    "additional_cases_executed_by_supplementary_filter": True,
    "not_additive": "The 216 registered cases are included among the 242 supplementary results; count their source identities once.",
}
reconciliation_identity = write("additional-case-reconciliation.json", reconciliation)

# Bind the exact original code responsible for registration, macro expansion,
# CPU gating, and the full original leak-checking test entry point.
configuration = read(Path(registered["source_configuration_receipt"]["path"]))
source_root = Path(configuration["command"][configuration["command"].index("-S") + 1])
anchors = [
    ("intern/cycles/test/CMakeLists.txt", [29, 73], "The explicit source list contains .cpp wrappers; AVX2 wrappers are gated by APPLE and CXX_HAS_AVX2."),
    ("build_files/cmake/testing.cmake", [151, 164], "Configured registration passes source filenames to gtest_add_tests."),
    ("build_files/cmake/Modules/GTest.cmake", [338, 343], "The scanner reads listed files and regex matches literal declarations; it does not preprocess included headers."),
    ("build_files/cmake/Modules/GTest.cmake", [392, 413], "Collected suite names become the original explicit framework filter."),
    ("intern/cycles/test/util_half_test.cpp", [5, 6], "The util_half wrapper defines TEST_CATEGORY_NAME and includes its declaration header."),
    ("intern/cycles/test/util_half_avx2_test.cpp", [5, 14], "The util_half_avx2 wrapper defines ISA macros and includes the same header under an AVX2 guard."),
    ("intern/cycles/test/util_float8_avx2_test.cpp", [5, 14], "The util_avx2 wrapper defines ISA macros and includes util_float8_test.h."),
    ("intern/cycles/test/util_half_test.h", [14, 20], "The original AVX2 tests query runtime CPU support and use GTEST_SKIP when absent."),
    ("intern/cycles/test/util_float8_test.h", [13, 24], "The original vector tests query runtime CPU support; their early-return guard is preserved."),
    ("tests/gtests/testing/testing_main.cc", None, "The original test main, framework initialization, and guarded allocator checks are unchanged."),
]
source_evidence = []
with tarfile.open(Path(registered["source_archive"]["path"]), "r:gz") as archive:
    for relative, lines, interpretation in anchors:
        original = archive.extractfile("blender-" + registered["source_commit"] + "/" + relative).read()
        path = source_root / relative
        assert path.read_bytes() == original
        source_evidence.append({"source_path": relative, "line_range": lines, "identity": identity(path),
                                "verified_against_archive": True, "interpretation": interpretation})
    source_evidence_identity = write("source-registration-reconciliation.json", {
        "schema": 1, "source_commit": registered["source_commit"], "source_archive": registered["source_archive"],
        "original_sources": source_evidence,
        "conclusion": "The actual configured filter omits 26 compiled cases whose declarations live in included headers. The unfiltered runtime listing and separately executed original binary expose and test them.",
        "upstream_source_or_configuration_modified": False,
    })

cpu_text = Path("/proc/cpuinfo").read_text()
first_cpu = cpu_text.split("\n\n", 1)[0]
cpu_fields = {}
for line in first_cpu.splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        if key.strip() in {"vendor_id", "model name", "cpu family", "model", "stepping", "flags"}:
            cpu_fields[key.strip()] = value.strip()
host = write("host-observation.json", {
    "schema": 1, "observed_utc": datetime.now(timezone.utc).isoformat(),
    "platform": platform.platform(), "machine": platform.machine(), "libc": platform.libc_ver(),
    "logical_cpu_count": os.cpu_count(), "first_cpu_procfs_fields": cpu_fields,
    "cgroup_memory_max": Path("/sys/fs/cgroup/memory.max").read_text().strip(),
    "scope": "Read-only host observation after execution; not a cross-platform or GPU capability claim.",
})

samples = [json.loads(line) for line in (HERE / "resource-samples.jsonl").read_text().splitlines()]
memory = {
    "existing_cgroup_memory_limit_bytes": build["cgroup_memory_limit_bytes"],
    "original_process_group_rss_fields_valid": False,
    "original_process_group_rss_guard_valid": False,
    "original_process_group_rss_defect": "Namespace-local Popen PID was compared with outer /proc process-group IDs; the raw wrapper observed an unrelated PID. Do not use its process-group RSS values or claim its RSS guard enforced the threshold.",
    "valid_original_observations": "Cgroup metrics, kernel memory cap, OOM-event checks, non-file-memory checks, time bound, and free-disk checks are independent of that PID mapping.",
    "supplementary_observer": identity(observation_path),
    "supplementary_sample_count": observation["sample_count"],
    "supplementary_sampled_process_group_rss_peak_bytes": observation["peak_sampled_group_rss_bytes"],
    "supplementary_scope": observation["scope"],
    "original_sample_count": len(samples),
    "sampled_minimum_free_disk_bytes": min(sample["free_disk_bytes"] for sample in samples),
    "sampled_peak_cgroup_memory_current_bytes": max(sample["cgroup_memory_current_bytes"] for sample in samples),
    "cgroup_memory_current_includes_file_cache": True,
    "oom_events_before": build["resource_usage_before"]["cgroup_memory_events"],
    "oom_events_after": build["resource_usage_after"]["cgroup_memory_events"],
}

# Recount the previously recorded generated object rules without starting a build.
assessment_path = REPO / "compatibility/evidence/product-native-gtest-2026-10-23/remaining-build-assessment.json"
assessment = read(assessment_path)
build_directory = Path(assessment["build_directory"])
targets = {}
for name, target in assessment["targets"].items():
    objects = set()
    for rule in target["source_build_rules"]:
        path = Path(rule["path"])
        assert identity(path) == rule
        objects.update(re.findall(r"^([^\n:# ]+\.o):", path.read_text(), re.M))
    assert len(objects) == target["configured_object_rule_count"]
    remaining = sorted(item for item in objects if not (build_directory / item).is_file())
    targets[name] = {
        "configured_object_rule_count": len(objects),
        "existing_object_rule_count": len(objects) - len(remaining),
        "remaining_object_rule_count": len(remaining),
        "remaining_object_rules": remaining,
        "prior_remaining_object_rule_count": target["remaining_object_rule_count"],
        "prior_low_confidence_planning_wall_minutes_range": target["planning_wall_minutes_range"],
        "prior_additional_disk_budget_gib_range": target["additional_disk_budget_gib_range"],
    }
assessment_identity = write("remaining-build-assessment.json", {
    "schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
    "prior_assessment": identity(assessment_path), "build_config": build["cache_after"],
    "scope": "Object-file existence planning only; no claim to test counts, freshness, link completion, or build-time accuracy.",
    "targets": targets, "free_disk_bytes": shutil.disk_usage(WORKSPACE).free,
    "minimum_free_disk_reserve_bytes": 4 * 1024**3,
    "measured_cycles_wall_seconds": build["elapsed_seconds"],
    "measured_cycles_parallel_jobs": 1,
    "any_build_started_by_assessment": False, "tests_executed_by_assessment": 0,
    "caveats": ["Larger targets have unmeasured heavy template and link requirements; prior estimates remain low confidence.",
                "Existing files are not a proof that all generated dependencies are current.",
                "Runtime library staging required an additional 429,185,408 bytes after the build.",
                "Do not infer rendering, GPU, application, or browser parity from unit-test or object counts."],
})

combined_registered = Counter(case["outcome"] for case in [*prior_cases, *registered["cases"]])
combined_whole = Counter(case["outcome"] for case in [*prior_cases, *whole["cases"]])
summary = {
    "schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
    "source_commit": registered["source_commit"], "repository_checkpoint_before_work": build["repository_checkpoint"],
    "scope": "Native Cycles unit tests for one exact Linux configuration, with original registered and supplementary unfiltered invocations distinguished.",
    "build_receipt": identity(build_path), "build_returncode": build["returncode"],
    "build_wall_seconds": build["elapsed_seconds"], "build_parallel_jobs": 1,
    "build_config_before": build["cache_before"], "build_config_after": build["cache_after"],
    "source_configuration_receipt": registered["source_configuration_receipt"],
    "artifact": build["artifact"], "memory_observation_qualification": memory,
    "first_loader_failure": {"receipt": identity(failed_path), "executed_cases": 0, "test_success": False,
                             "reason": "Original configured library directory was empty; loader could not find libImath.so.30.",
                             "stages": [{"name": item["name"], "returncode": item["returncode"]} for item in failed["stages"]]},
    "runtime_library_staging": {"receipt": identity(stage_path), "tracked_entries": stage["selected_tracked_entries"],
                                "regular_files": stage["regular_file_count"], "symlinks": stage["symlink_count"],
                                "regular_file_bytes": stage["regular_file_bytes"],
                                "excluded_untracked_entry_count": len(stage["excluded_untracked_entries"]),
                                "original_generated_block_total_entries": stage["generated_entry_count"],
                                "binary_and_configuration_unchanged": True},
    "original_registered_execution": {"receipt": identity(registered_path), "ctest_name": "cycles", "original_ctest_invocation": True,
                                      "listed_cases": registered["inventories"]["registered"]["counts"]["cases"],
                                      "xml_reported_cases": len(registered["cases"]), "outcomes": registered["observed_outcome_counts"],
                                      "returncode": registered["execution"]["returncode"], "disabled": int(registered["xml_counters"]["disabled"]),
                                      "source_declaration_files": len(registered["verified_original_declaration_files"]),
                                      "all_source_identities_resolved": True},
    "whole_binary_supplementary_execution": {"receipt": identity(whole_path), "original_ctest_invocation": False,
                                            "framework_filter": "*", "listed_cases": registered["inventories"]["unfiltered"]["counts"]["cases"],
                                            "xml_reported_cases": len(whole["cases"]), "outcomes": whole["observed_outcome_counts"],
                                            "returncode": whole["execution"]["returncode"], "disabled": int(whole["xml_counters"]["disabled"]),
                                            "source_declaration_files": len(whole["verified_original_declaration_files"]),
                                            "all_source_identities_resolved": True},
    "additional_case_reconciliation": reconciliation_identity,
    "source_registration_reconciliation": source_evidence_identity,
    "host_observation": host,
    "prior_native_checkpoint": identity(prior_path),
    "disjoint_from_previous_source_qualified_ids": True,
    "combined_original_registered_source_identities": {"count": len(prior_ids | reg_ids), "outcomes": dict(combined_registered),
                                                       "distinct_original_ctest_registrations": 38, "retained_empty_original_registrations": 1},
    "combined_source_identities_including_supplementary": {"count": len(prior_ids | whole_ids), "outcomes": dict(combined_whole),
                                                          "additional_supplementary_only_cases": len(additional)},
    "remaining_build_assessment": assessment_identity,
    "summary_script": identity(Path(__file__)),
    "browser_cases_executed": 0, "browser_parity": False,
    "all_upstream_tests_enumerated": False, "runtime_enumeration_complete": False,
    "remaining_obligations": [
        "Build and runtime-expand remaining configured native test binaries and Python/application drivers.",
        "Reconcile required configuration, platform, rendering-device and feature variants against source registrations.",
        "Preserve the distinct source pin and runtime context when pairing browser and native outcomes.",
        "Whole application runtime, GPU execution, render-suite completion, and browser implementation remain unproven by this unit-test run.",
        "The original configured CTest filter still omits 26 compiled Cycles cases; the supplementary receipt does not modify that registration.",
    ],
}
summary_identity = write("summary.json", summary)
print(json.dumps({"summary": summary_identity, "registered_cases": len(reg_ids), "unfiltered_cases": len(whole_ids),
                  "additional_cases": len(additional), "remaining_target_object_counts": {name: value["remaining_object_rule_count"] for name, value in targets.items()}}))
