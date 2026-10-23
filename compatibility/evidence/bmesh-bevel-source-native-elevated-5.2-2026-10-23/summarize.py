#!/usr/bin/env python3
"""Reconcile the preserved environment attempts without changing either receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "bmesh-bevel-source-native-5.2-2026-10-23"


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    output = HERE / "summary.json"
    if output.exists():
        raise FileExistsError("summary already frozen")
    first, retry = (json.loads((directory / "execution.json").read_text()) for directory in (ORIGINAL, HERE))
    first_plan, retry_plan = (json.loads((directory / "prospective-command.json").read_text()) for directory in (ORIGINAL, HERE))
    assert first["actual_process_returncode"] == -15 and first["timed_out"] and not first["completed_successfully"]
    assert retry["actual_process_returncode"] == 0 and not retry["timed_out"] and retry["completed_successfully"]
    assert first_plan["command"] == retry_plan["command"] and first_plan["cwd"] == retry_plan["cwd"]
    assert first_plan["environment_overrides"] == retry_plan["environment_overrides"]
    assert first_plan["inputs"] == retry_plan["inputs"] == first["inputs_after"] == retry["inputs_after"]
    assert first["native_executable"] == retry["native_executable"]
    expected_names = [row["name"] for row in first_plan["static_declared_specs"]]
    assert len(expected_names) == len(set(expected_names)) == 88
    verified_attempts = []
    for label, directory, report in (("restricted-sandbox", ORIGINAL, first), ("elevated-local", HERE, retry)):
        log = directory / "original-driver.log"
        assert identity(log) == report["raw_log"]
        text = log.read_text()
        starts = re.findall(r"^START (.+) test\.$", text, re.M)
        passes = re.findall(r"^PASSED (.+) test successfully\.$", text, re.M)
        failures = re.findall(r"^FAILED (.+) test with the following: *$", text, re.M)
        comparisons = re.findall(r"^Mesh Comparison : (.+)$", text, re.M)
        validation = re.findall(r"^Mesh Validation : (.+)$", text, re.M)
        assert starts == passes == expected_names
        assert not failures and comparisons == ["Same"] * 88 and validation == ["Valid"] * 88
        observations = report["original_case_observations"]
        assert observations["observed_passes"] == 88 and observations["observed_starts"] == 88
        assert not any(observations[key] for key in ("duplicate_names", "missing_declared_names", "unexpected_names"))
        verified_attempts.append({"environment": label, "receipt": identity(directory / "execution.json"),
                                  "prospective_command": identity(directory / "prospective-command.json"),
                                  "raw_log": identity(log), "actual_process_returncode": report["actual_process_returncode"],
                                  "timed_out": report["timed_out"], "elapsed_seconds": report["elapsed_seconds"],
                                  "observed_original_start_markers": len(starts), "observed_original_pass_markers": len(passes),
                                  "observed_same_geometry_results": len(comparisons), "observed_valid_mesh_results": len(validation),
                                  "original_invocation_completed_successfully": report["completed_successfully"],
                                  "original_sources_and_fixture_unchanged": report["all_original_inputs_unchanged"],
                                  "child_max_rss_kib": report["child_max_rss_kib"]})
    for entry in first_plan["inputs"]:
        assert identity(Path(entry["path"])) == entry
    cases = retry["original_case_observations"]["observations"]
    summary = {
        "schema": 1, "kind": "source-derived-original-bmesh-bevel-native-summary",
        "created_utc": datetime.now(timezone.utc).isoformat(), "summary_driver": identity(Path(__file__).resolve()),
        "source_commit": retry["source_commit"], "native_executable": retry["native_executable"],
        "source_declaration_index": 49, "ctest_name_from_source": "bmesh_bevel",
        "original_invocation_kind": "source-derived original Blender command", "configured_ctest_execution": False,
        "original_argv_and_cwd_identical_across_attempts": True,
        "exact_original_source_helper_fixture_preserved": True,
        "fixture_identity": first_plan["inputs"][-1], "fixture_original_pointer": first_plan["fixture_original_pointer"],
        "source_archive": first_plan["source_archive"], "declaration_catalog": first_plan["declaration_catalog"],
        "native_source_build_correspondence_verified": first_plan["native_source_build_correspondence_verified"],
        "attempts": verified_attempts,
        "completed_native_original_invocations": 1, "unique_observed_original_cases": len(cases),
        "observed_original_native_passes_in_completed_invocation": 88,
        "observed_original_native_failures": 0, "observed_ambiguous_or_incomplete_cases": 0,
        "missing_declared_names": [], "unexpected_names": [], "duplicate_names": [],
        "case_evidence": cases,
        "counting_rule": "The same 88 identities appeared in both attempts. Count each only once for the completed elevated source-derived native invocation; the first timed-out invocation never qualifies as completed.",
        "first_attempt_measurement_caveat": {
            "invalid_fields": ["sampled_process_peak_rss_kib", "sampled_process_peak_thread_count"],
            "reason": "The restricted sandbox child PID was not verified against the procfs command line. A separate host PID observation showed the sampled PID did not identify Blender. Those original sampled values are retained but are not usable resource measurements.",
            "usable_measurement": "child_max_rss_kib comes from the kernel's waited-child resource accounting, not procfs PID lookup."},
        "retry_measurements": {
            "sampled_procfs_identity_verified": retry["sampled_procfs_identity_verified"],
            "sampled_peak_rss_kib": retry["sampled_process_peak_rss_kib"],
            "sampled_peak_threads": retry["sampled_process_peak_thread_count"],
            "environment_thread_requests_limit_all_blender_pools": False},
        "original_assertions_or_tolerances_modified": False,
        "original_full_suite_comparison_preserved": True, "oracle_update_environment_absent": True,
        "selected_829_browser_ledger_modified": False, "product_5_4_native_counts_modified": False,
        "browser_tests_executed": False, "browser_test_passes": 0,
        "complete_test_denominator": False, "full_feature_parity": False,
    }
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(identity(output), indent=2))


if __name__ == "__main__":
    main()
