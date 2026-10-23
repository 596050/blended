"""Read original unittest verbose output without changing its runner or tests."""
import re


def reconcile_output(text, expected_ids, runtime_exit):
    expected = set(expected_ids)
    if len(expected) != len(expected_ids):
        raise ValueError("frozen expected case list contains duplicates")
    observed = []
    summaries = []
    terminal_ok = []
    for line in text.splitlines():
        match = re.fullmatch(r"(test\S+) \(([^)]+)\) \.\.\. (.+)", line)
        if match:
            method, qualified, status = match.groups()
            case_id = qualified.removeprefix("__main__.")
            if case_id not in expected and case_id + "." + method in expected:
                case_id += "." + method
            mapped = {"ok": "passed", "FAIL": "failed", "ERROR": "error",
                      "expected failure": "expected_failure", "unexpected success": "unexpected_success"}.get(status)
            if mapped is None:
                mapped = "skipped" if status.startswith("skipped ") else "unrecognized"
            observed.append({"id": case_id, "status": mapped, "original_verbose_line": line})
        match = re.fullmatch(r"Ran (\d+) tests? in ([0-9.]+)s", line)
        if match:
            summaries.append({"testsRun": int(match.group(1)), "elapsed_seconds": float(match.group(2))})
        if line == "OK" or line.startswith("OK ("):
            terminal_ok.append(line)
    actual = [entry["id"] for entry in observed]
    passed = sum(entry["status"] == "passed" for entry in observed)
    complete = (runtime_exit == 0 and len(observed) == len(expected_ids) and len(set(actual)) == len(actual)
                and set(actual) == expected and len(summaries) == 1 and summaries[0]["testsRun"] == len(expected_ids)
                and passed == len(expected_ids) and terminal_ok == ["OK"])
    return {"expected_case_ids": expected_ids, "observed_cases": observed, "original_summaries": summaries,
            "terminal_summaries": terminal_ok, "component_case_passes": passed,
            "missing_case_ids": sorted(expected - set(actual)), "unexpected_case_ids": sorted(set(actual) - expected),
            "complete_original_module_pass_in_component": complete,
            "original_blender_invocation_executed": False, "strict_blender_browser_test_passes": 0,
            "full_feature_parity": False}
