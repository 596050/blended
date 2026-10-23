#!/usr/bin/env python3
"""Reconcile one frozen original mesh-operators execution without rerunning it."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main():
    output = HERE / "summary.json"
    if output.exists():
        raise FileExistsError("summary already frozen")
    report = json.loads((HERE / "execution.json").read_text())
    plan = json.loads((HERE / "prospective-command.json").read_text())
    assert identity(HERE / "prospective-command.json") == report["prospective_command"]
    assert identity(HERE / "run-native.py") == plan["capture_driver"] == report["capture_driver"]
    assert identity(HERE / "original-driver.log") == report["raw_log"]
    assert plan["native_executable"] == report["native_executable"]
    assert identity(Path(plan["native_executable"]["path"])) == plan["native_executable"]
    assert report["actual_process_returncode"] == 0 and report["completed_successfully"]
    assert not report["timed_out"] and report["termination_reason"] is None
    assert not plan["configured_ctest_execution"] and not report["configured_ctest_execution"]
    assert plan["oracle_update_environment_absent"]
    assert plan["command"][-2:] == ["--", "--run-all-tests"]
    assert "--run-test" not in plan["command"]
    assert plan["timeout_seconds"] == 180
    assert plan["inputs"] == report["inputs_after"]
    for item in plan["inputs"]:
        assert identity(Path(item["path"])) == item

    declaration = plan["original_declaration"]
    assert declaration["source_declaration_index"] == 74
    cmake = (HERE / "source" / declaration["source_path"]).read_text()
    cmake_start = sum(len(line) for line in cmake.splitlines(keepends=True)[:declaration["line"] - 1])
    assert cmake[cmake_start:].lstrip().startswith(declaration["text"])
    script_path = HERE / "source/tests/python/operators.py"
    script_text = script_path.read_text()
    tree = ast.parse(script_text)
    original_main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    assignment = next(node for node in original_main.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "tests" for target in node.targets))
    declarations = []
    for node in assignment.value.elts:
        assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "SpecMeshTest"
        assert len(node.args) == 4 and not node.keywords
        declarations.append({"name": ast.literal_eval(node.args[0]), "line": node.lineno,
                             "upstream_path": "tests/python/operators.py",
                             "source_sha256": identity(script_path)["sha256"],
                             "spec_sha256": hashlib.sha256(ast.get_source_segment(script_text, node).encode()).hexdigest()})
    assert declarations == plan["static_declared_specs"]
    declared_names = [item["name"] for item in declarations]
    assert len(declared_names) == len(set(declared_names)) == 105

    text = (HERE / "original-driver.log").read_text()
    starts = re.findall(r"^START (.+) test\.$", text, re.M)
    passes = re.findall(r"^PASSED (.+) test successfully\.$", text, re.M)
    failures = re.findall(r"^FAILED (.+) test with the following: *$", text, re.M)
    comparisons = re.findall(r"^Mesh Comparison : (.+)$", text, re.M)
    validation = re.findall(r"^Mesh Validation : (.+)$", text, re.M)
    assert starts == passes == declared_names
    assert not failures and comparisons == ["Same"] * len(passes) and validation == ["Valid"] * len(passes)
    assert text.splitlines()[-1] == "Blender quit"
    cases = report["original_case_observations"]["observations"]
    assert [item["name"] for item in cases] == starts
    assert [item["original_source_declaration"] for item in cases] == declarations
    assert all(item["status"] == "passed" and item["mesh_comparison"] == ["Same"]
               and item["mesh_validation"] == ["Valid"] for item in cases)
    for item in cases:
        assert text.splitlines()[item["start_log_line"] - 1] == f"START {item['name']} test."
    observations = report["original_case_observations"]
    assert observations["observed_starts"] == len(starts) and observations["observed_passes"] == len(passes)
    assert not any(observations[key] for key in ("observed_failures", "observed_ambiguous_or_incomplete",
                                                "duplicate_names", "missing_declared_names", "unexpected_names"))
    summary = {
        "schema": 1, "kind": "source-derived-original-mesh-operators-native-summary",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "summary_driver": identity(Path(__file__).resolve()),
        "source_commit": report["source_commit"], "source_archive": plan["source_archive"],
        "source_declaration_index": 74, "ctest_name_from_source": "operators",
        "original_declaration": declaration, "declaration_catalog": plan["declaration_catalog"],
        "original_invocation_kind": "source-derived original Blender command",
        "configured_ctest_execution": False,
        "execution_environment": plan["execution_environment"],
        "native_executable": plan["native_executable"],
        "prior_native_release_receipt": plan["prior_native_release_receipt"],
        "native_source_build_correspondence_verified": plan["native_source_build_correspondence_verified"],
        "prospective_command": identity(HERE / "prospective-command.json"),
        "execution_receipt": identity(HERE / "execution.json"),
        "raw_log": identity(HERE / "original-driver.log"),
        "actual_process_returncode": report["actual_process_returncode"],
        "elapsed_seconds": report["elapsed_seconds"],
        "timed_out": report["timed_out"], "termination_reason": report["termination_reason"],
        "timeout_seconds": plan["timeout_seconds"],
        "completed_native_original_invocations": 1,
        "unique_observed_original_cases": len(cases),
        "observed_original_native_passes_in_completed_invocation": len(passes),
        "observed_original_native_failures": len(failures),
        "observed_ambiguous_or_incomplete_cases": 0,
        "missing_declared_names": [], "unexpected_names": [], "duplicate_names": [],
        "case_evidence": cases,
        "counting_rule": "Case credit comes only from the actual original START/PASSED/Results output and successful process exit. Static declarations identify cases and detect omissions; they never create passes.",
        "exact_original_source_helper_fixture_preserved": True,
        "inputs": plan["inputs"],
        "fixture_identity": plan["inputs"][-1], "fixture_original_pointer": plan["fixture_original_pointer"],
        "fixture_payload_source": plan["fixture_payload_source"],
        "fixture_reuse_reason": plan["fixture_reuse_reason"],
        "test_selection": plan["test_selection"],
        "environment_overrides": plan["environment_overrides"],
        "original_assertions_or_tolerances_modified": False,
        "original_full_suite_comparison_preserved": True,
        "oracle_update_environment_absent": True,
        "measurements": {
            "sampled_procfs_identity_verified": report["sampled_procfs_identity_verified"],
            "sampled_peak_rss_kib": report["sampled_process_peak_rss_kib"],
            "sampled_peak_threads": report["sampled_process_peak_thread_count"],
            "kernel_child_max_rss_kib": report["child_max_rss_kib"],
            "environment_thread_requests_limit_all_blender_pools": False},
        "selected_829_browser_ledger_modified": False,
        "product_5_4_native_counts_modified": False,
        "browser_tests_executed": False, "browser_test_passes": 0,
        "complete_test_denominator": False, "full_feature_parity": False,
    }
    with output.open("x") as stream:
        stream.write(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(identity(output), indent=2))


if __name__ == "__main__":
    main()
