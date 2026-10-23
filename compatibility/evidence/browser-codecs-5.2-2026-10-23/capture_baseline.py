#!/usr/bin/env python3
"""Reconcile the recorded unchanged ImBuf suite's codec gaps, without rerunning it."""
import hashlib
import json
from pathlib import Path


def main():
    output = Path(__file__).resolve().parent
    repo = output.parents[2]
    native_path = repo / "compatibility/evidence/unittest-native-5.2-2026-10-23/imbuf_py_api/native_reference.json"
    browser_path = repo / "compatibility/evidence/unittest-browser-essentials-5.2-2026-10-23/imbuf_py_api/qualification.json"
    manifest_path = repo / "compatibility/candidate-suites/unittest-main-5.2/imbuf_py_api.json"
    native, browser = (json.loads(path.read_text()) for path in (native_path, browser_path))
    left, right = (row["execution"]["suites"][0] for row in (native, browser))
    assert left["sha256"] == right["sha256"] == "cc97ac9e6a3d1854d87f3937dd273765b37a4a11322b947bd33ef43c9b92ff4e"
    assert left["upstream_path"] == right["upstream_path"] == "tests/python/bl_imbuf_py_api.py"
    assert sorted(left["discovered_ids"]) == sorted(right["discovered_ids"])
    native_subtests = {row["id"]: row for row in left["outcomes"] if row["kind"] == "subtest"}
    browser_subtests = {row["id"]: row for row in right["outcomes"] if row["kind"] == "subtest"}
    assert len(native_subtests) == len([row for row in left["outcomes"] if row["kind"] == "subtest"])
    assert len(browser_subtests) == len([row for row in right["outcomes"] if row["kind"] == "subtest"])

    def identity(path):
        return {"path": path.relative_to(repo).as_posix(), "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    missing = sorted(set(native_subtests) - set(browser_subtests))
    unexpected = sorted(set(browser_subtests) - set(native_subtests))
    errors = [row for row in right["outcomes"] if row["status"] != "passed"]
    report = {"schema": 1, "kind": "recorded-original-imbuf-codec-gap",
              "inputs": {"native": identity(native_path), "browser": identity(browser_path), "frozen_manifest": identity(manifest_path)},
              "upstream_test": {"path": left["upstream_path"], "sha256": left["sha256"]},
              "native_parent_inventory": len(left["discovered_ids"]), "browser_parent_inventory": len(right["discovered_ids"]),
              "native_subtest_events": len(native_subtests), "browser_subtest_events": len(browser_subtests),
              "missing_subtest_ids": missing, "unexpected_subtest_ids": unexpected,
              "browser_nonpassing_events": errors, "native_original_counters": {key: left[key] for key in ("testsRun", "errors", "failures", "expected_failures", "skipped")},
              "browser_original_counters": {key: right[key] for key in ("testsRun", "errors", "failures", "expected_failures", "skipped")},
              "browser_parent_summary": browser["summary"]["totals"],
              "native_process_returncode": native["process"].get("returncode"),
              "browser_runtime_exit_code": browser["execution_mode"].get("runtime_exit_code"),
              "new_blender_cases_executed": 0, "full_feature_parity": False,
              "acceptance_obligation": "A rebuilt browser artifact must execute all 80 original parent IDs and all 57 native subtest IDs under the original invocation, assertions and tolerances. Existing parent passes do not discharge missing conditional subtests."}
    assert (report["native_parent_inventory"], len(native_subtests), len(browser_subtests), len(missing), len(errors)) == (80, 57, 43, 14, 3)
    target = output / "baseline-gap.json"
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"missing_subtests": len(missing), "nonpassing_events": len(errors), "output": identity(target)}))


if __name__ == "__main__":
    main()
