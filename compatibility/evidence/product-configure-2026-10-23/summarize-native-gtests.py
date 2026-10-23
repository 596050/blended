"""Consolidate hash-verified original native observations without changing receipts."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import xml.etree.ElementTree as ET


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
sys.path.insert(0, str(repo))
from tools.test_registration_inventory import gtest_source_case_id

root = repo / "compatibility/evidence/product-native-gtest-2026-10-23"
output = root / "summary.json"
case_output = root / "source-qualified-observations.json"
if output.exists() or case_output.exists():
    raise RuntimeError("preserve the original native summary")
configuration_path = evidence / "configure-with-optix.json"
configuration = json.loads(configuration_path.read_text())
commit = configuration["source_commit"]
source_root = Path(configuration["command"][configuration["command"].index("-S") + 1])
build = Path(configuration["command"][configuration["command"].index("-B") + 1])
archive_path = workspace / "runtime/blender-product-94363991.tar.gz"


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def verify(reference):
    actual = identity(Path(reference["path"]))
    if actual != reference:
        raise ValueError("bound evidence changed: " + reference["path"])
    return actual


archive_identity = identity(archive_path)
if archive_identity["sha256"] != "e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7":
    raise ValueError("pinned original source archive mismatch")
cache_identity = identity(build / "CMakeCache.txt")
configuration_identity = identity(configuration_path)
batch_path = root / "libmv-capture-batch.json"
batch = json.loads(batch_path.read_text())
if batch.get("all_captures_succeeded") is not True or len(batch["invocations"]) != 32:
    raise ValueError("LibMV batch is incomplete")
paths = [root / name / "native-reference.json" for name in
         ("atomic", "guardedalloc", "BLI-source-identities", "makesdna", "shader_tool")]
paths.extend(Path(item["native_reference"]["path"]) for item in batch["invocations"])
for item in batch["invocations"]:
    verify(item["native_reference"])
    verify(item["stdout"])
    verify(item["stderr"])
source_files = {}
source_contents = {}
invocations = []
observations = []
name_locations = defaultdict(set)
outcomes = Counter()
discovered_total = 0
unfiltered_total = 0

with tarfile.open(archive_path, "r:gz") as archive:
    def verify_source(path):
        if path not in source_files:
            gtest_source_case_id("source.validation", source_commit=commit, source_path=path,
                                 source_sha256="0" * 64, source_line=1)
            original = archive.extractfile(archive.getmember("blender-" + commit + "/" + path)).read()
            if (source_root / path).read_bytes() != original:
                raise ValueError("declaration source differs from pinned archive: " + path)
            source_files[path] = {"path": path, "bytes": len(original),
                                  "sha256": hashlib.sha256(original).hexdigest(),
                                  "line_count": len(original.splitlines()), "verified_against_archive": True}
            source_contents[path] = original
        return source_files[path]

    for path in paths:
        reference_identity = identity(path)
        reference = json.loads(path.read_text())
        if reference["source_commit"] != commit or reference["source_configuration_receipt"] != configuration_identity:
            raise ValueError("different source or build configuration in native reference")
        if reference["build_config_sha256"] != cache_identity["sha256"]:
            raise ValueError("different CMake cache in native reference")
        verify(reference["build_receipt"])
        build_receipt = json.loads(Path(reference["build_receipt"]["path"]).read_text())
        if build_receipt["cache_before"] != cache_identity or build_receipt["cache_after"] != cache_identity:
            raise ValueError("build changed the original CMake cache")
        verify(build_receipt["log"])
        verify(build_receipt["generated_target_rules"])
        verify(reference["artifact"])
        if build_receipt["artifact"] != reference["artifact"]:
            raise ValueError("capture binary differs from built binary")
        for stage in reference["stages"]:
            verify(stage["stdout"])
            verify(stage["stderr"])
            if stage["returncode"] != 0 or stage["timed_out"]:
                raise ValueError("native stage failed: " + str(path) + " " + stage["name"])
        verify(reference["gtest_xml"])
        verify(reference["ctest_junit"])
        listings = {}
        for label in ("registered", "unfiltered"):
            record = reference["inventories"][label]
            verify(record["inventory"])
            listings[label] = json.loads(Path(record["inventory"]["path"]).read_text())
        xml = ET.parse(reference["gtest_xml"]["path"]).getroot()
        xml_cases = [(suite, node) for suite in xml.findall("testsuite") for node in suite.findall("testcase")]
        if len(xml_cases) != len(reference["cases"]) or len(xml_cases) != int(xml.get("tests")):
            raise ValueError("original XML count differs from capture")
        actual_counts = Counter()
        local_ids = []
        for (suite, node), captured in zip(xml_cases, reference["cases"]):
            attributes = dict(node.attrib)
            name = attributes.get("classname", suite.get("name", "")) + "." + attributes["name"]
            if captured["attributes"] != attributes or captured["identity"] != name:
                raise ValueError("captured case differs from original XML")
            if node.findall("failure"):
                outcome = "failed"
            elif node.findall("error"):
                outcome = "error"
            elif node.findall("skipped"):
                outcome = "skipped"
            elif attributes.get("status") == "notrun" or attributes.get("result") == "suppressed":
                outcome = "not_run"
            elif attributes.get("status") == "run" and attributes.get("result") == "completed":
                outcome = "passed"
            else:
                outcome = "unknown"
            if captured["outcome"] != outcome:
                raise ValueError("captured outcome differs from original XML")
            source_path, source_line = attributes["file"], int(attributes["line"])
            source = verify_source(source_path)
            if not 1 <= source_line <= source["line_count"]:
                raise ValueError("original XML source line is outside pinned declaration file")
            case_id = gtest_source_case_id(name, source_commit=commit, source_path=source_path,
                                           source_sha256=source["sha256"], source_line=source_line)
            if captured.get("case_id", case_id) != case_id:
                raise ValueError("source-qualified case identity mismatch")
            local_ids.append(case_id)
            name_locations[name].add((source_path, source_line))
            actual_counts[outcome] += 1
            observations.append({"case_id": case_id, "identity": name, "outcome": outcome,
                                 "ctest_name": reference["original_registration"]["identity"],
                                 "native_reference_sha256": reference_identity["sha256"],
                                 "source_path": source_path, "source_line": source_line,
                                 "source_sha256": source["sha256"], "identity_status": "source_qualified"})
        if len(local_ids) != len(set(local_ids)):
            raise ValueError("ambiguous source-qualified identity within an invocation")
        if actual_counts != Counter(reference["observed_outcome_counts"]):
            raise ValueError("original XML outcome totals differ from native reference")
        listed_names = Counter(case["identity"] for case in listings["registered"]["cases"])
        captured_names = Counter(case["identity"] for case in reference["cases"])
        if listed_names != captured_names:
            raise ValueError("registered listing and XML name multiplicities differ")
        discovered, unfiltered = len(listings["registered"]["cases"]), len(listings["unfiltered"]["cases"])
        discovered_total += discovered
        unfiltered_total += unfiltered
        outcomes.update(actual_counts)
        invocations.append({"ctest_name": reference["original_registration"]["identity"],
                            "target": build_receipt["target"], "native_reference": reference_identity,
                            "artifact": reference["artifact"], "build_receipt": reference["build_receipt"],
                            "registered_discovered": discovered, "unfiltered_discovered": unfiltered,
                            "registered_disabled": listings["registered"]["counts"]["disabled"],
                            "unfiltered_disabled": listings["unfiltered"]["counts"]["disabled"],
                            "registered_inventory_blockers": listings["registered"]["blockers"],
                            "unfiltered_inventory_blockers": listings["unfiltered"]["blockers"],
                            "classification": "empty_runtime_listing" if discovered == 0 else "native_cases_observed",
                            "xml_observations": len(xml_cases),
                            "executed": sum(1 for _, node in xml_cases if node.get("status") == "run"),
                            **{label: actual_counts[label] for label in
                               ("passed", "skipped", "failed", "error", "not_run", "unknown")},
                            "ctest_returncode": reference["execution"]["returncode"],
                            "source_identities_resolved": True,
                            "build_elapsed_seconds": build_receipt["elapsed_seconds"],
                            "browser_cases_executed": 0})
    empty_source = verify_source("intern/libmv/libmv/simple_pipeline/resect_test.cc")
    empty_source_lines = source_contents[empty_source["path"]].decode().splitlines()
    disabled_block_start = next(n for n, line in enumerate(empty_source_lines, 1) if line == "#if 0")
    disabled_block_end = max(n for n, line in enumerate(empty_source_lines, 1) if line == "#endif")

id_counts = Counter(case["case_id"] for case in observations)
case_record = {"schema": 1, "source_commit": commit, "source_archive": archive_identity,
               "build_config_sha256": cache_identity["sha256"], "observations": observations,
               "verified_original_declaration_files": source_files,
               "browser_cases_executed": 0, "all_upstream_tests_enumerated": False}
case_output.write_text(json.dumps(case_record, indent=2) + "\n")
summary = {
    "schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Selected original native CTest invocations, not a complete Blender test denominator",
    "source_commit": commit, "source_archive": archive_identity,
    "source_configuration_receipt": configuration_identity, "build_config": cache_identity,
    "configured_base_inventory": identity(repo / "compatibility/evidence/product-ctest-configured-2026-10-23/summary.json"),
    "expanded_configuration_evidence_directory": "compatibility/evidence/product-expanded-config-2026-10-23",
    "fixture_candidate_hydration_receipt": identity(repo / "compatibility/evidence/product-fixture-hydration-2026-10-23/report.json"),
    "libmv_batch": identity(batch_path), "invocations": invocations,
    "counts": {"ctest_invocations": len(invocations), "ctest_invocations_exit_zero": len(invocations),
               "empty_runtime_registrations": sum(item["registered_discovered"] == 0 for item in invocations),
               "nonempty_runtime_registrations": sum(item["registered_discovered"] > 0 for item in invocations),
               "registered_discovered": discovered_total, "unfiltered_discovered": unfiltered_total,
               "registered_disabled": sum(item["registered_disabled"] for item in invocations),
               "unfiltered_disabled": sum(item["unfiltered_disabled"] for item in invocations),
               "xml_observations": len(observations), "executed": sum(item["executed"] for item in invocations),
               "unique_source_qualified_cases": len(id_counts),
               **{label: outcomes[label] for label in ("passed", "skipped", "failed", "error", "not_run", "unknown")}},
    "count_definitions": {
        "ctest_invocations_exit_zero": "Process exits only; the empty runtime invocation contributes no case passes.",
        "executed": "Original XML status=run, including a case that enters the test body and calls GTEST_SKIP.",
        "passed": "Original XML completed outcome without failure, error, or skip.",
        "registered_disabled": "GTest disabled names in the actual registered runtime listing.",
        "not_run": "Original XML notrun or suppressed observations, distinct from inventory-only discovery records.",
    },
    "source_qualified_observations": identity(case_output),
    "duplicate_names_with_distinct_sources": {name: [{"path": path, "line": line} for path, line in sorted(locations)]
                                               for name, locations in name_locations.items() if len(locations) > 1},
    "repeated_source_qualified_cases": {key: count for key, count in id_counts.items() if count > 1},
    "empty_runtime_registration": {"ctest_name": "libmv_resect", "native_case_passes": 0,
                                   "classification": "empty_runtime_listing", "blocker_retained": True,
                                   "parity_qualified": False,
                                   "source": empty_source, "upstream_disabled_block":
                                   {"directive": "#if 0", "start_line": disabled_block_start, "end_line": disabled_block_end}},
    "summary_script": identity(Path(__file__)),
    "source_identity_adapter": identity(repo / "tools/test_registration_inventory.py"),
    "browser_cases_executed": 0, "browser_parity": False,
    "runtime_enumeration_complete": False, "all_upstream_tests_enumerated": False,
    "remaining_obligations": [
        "Build and enumerate remaining configured original test binaries and Python drivers.",
        "Reconcile source registrations and optional build/platform/backend configurations.",
        "Resolve runtime fixture dependencies outside the hydrated candidate set.",
        "Execute matched browser artifacts using the same original source-qualified identities.",
        "Keep the original non-Apple shader_tool.MatrixConstructors skip separate from a passing assertion.",
    ],
}
output.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({"summary": identity(output), "counts": summary["counts"],
                  "duplicate_names_with_distinct_sources": summary["duplicate_names_with_distinct_sources"]}, indent=2))
