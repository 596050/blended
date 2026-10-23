#!/usr/bin/env python3
"""Freeze all original operator outcomes, including the two real failures."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load_expected(path, digest):
    measured = identity(path)
    if measured["sha256"] != digest:
        raise ValueError("frozen evidence changed: " + str(path))
    return json.loads(path.read_text()), measured


native, native_id = load_expected(HERE.parent / "mesh-operators-source-native-5.2-2026-10-23/summary.json",
    "fff5cc16a4b72b4913b9c98ce25055eff66c8061417351d3f3c273a1915cb02e")
attempt, attempt_id = load_expected(HERE / "attempt-01-elevated/execution.json",
    "81690d892a6fd3f5323ddb3d5666323fdfcce54c4b276c0566688cafe20770bb")
host, host_id = load_expected(HERE / "attempt-01-elevated-host/execution.json",
    "cef8c30ac2898489afd8dfeff3122e74357932519f0e3a5560a6eb915b4350de")
source_basis, source_basis_id = load_expected(HERE / "source-basis.json",
    "99011b8e5dca5e99efcc01cdf6d73db8b02285a62430d47f3065135723423479")
if host["child_receipt"] != attempt_id or host["actual_process_returncode"] != 1 or host["timed_out"]:
    raise ValueError("capture process does not match the actual failed invocation")
failed_checks = sorted(key for key, value in attempt["qualification_checks"].items() if not value)
if failed_checks != ["all_original_mesh_oracles_passed", "exactly_one_successful_runtime_exit"]:
    raise ValueError("an unaccounted execution or observation blocker remains")
if attempt["qualified_original_invocation"] or attempt["qualified_original_browser_passes"] != 0:
    raise ValueError("the failed whole invocation must not qualify")
if attempt["runtime_state"]["runtimeExitCodes"] != [1] or attempt["actual_chrome_process_returncode"] != 0:
    raise ValueError("runtime and browser exits differ from the original failure observation")
observations = attempt["original_stdout_observations"]["observations"]
native_by_name = {case["name"]: case for case in native["case_evidence"]}
if len(observations) != len(native_by_name) or len(observations) != 105 or {row["name"] for row in observations} != set(native_by_name):
    raise ValueError("native and browser runtime case identities do not reconcile")
cases = []
for row in observations:
    native_row = native_by_name[row["name"]]
    declaration = row["original_source_declaration"]
    if native_row["original_source_declaration"] != declaration or native_row["status"] != "passed":
        raise ValueError("source binding or successful native reference changed")
    case_id = ":".join((attempt["upstream_commit"], "operators", declaration["upstream_path"],
                        str(declaration["line"]), row["name"], declaration["spec_sha256"]))
    cases.append({"case_id": case_id, "name": row["name"], "native_status": native_row["status"],
                  "browser_observed_status": row["status"], "source_declaration": declaration,
                  "browser_stdout_line": row["start_log_line"],
                  "original_mesh_comparison": row["mesh_comparison"],
                  "original_mesh_validation": row["mesh_validation"],
                  "whole_invocation_qualified": False})
failed = [case for case in cases if case["browser_observed_status"] == "failed"]
if [case["name"] for case in failed] != ["IcosphereFill", "IcosphereFillUseBeautyFalse"]:
    raise ValueError("original failed case set differs")
if not all(case["original_mesh_comparison"] == ["The edge topology is different"] and
           case["original_mesh_validation"] == ["Valid"] for case in failed):
    raise ValueError("original failed comparator classification differs")
stdout = HERE / "attempt-01-elevated/original-stdout.log"
context = REPO / "compatibility/evidence/runtime-context-2026-10-23"
summary = {
    "schema": 1, "kind": "original-mesh-operators-native-browser-comparison",
    "created_utc": datetime.now(timezone.utc).isoformat(), "summary_driver": identity(Path(__file__).resolve()),
    "upstream_commit": attempt["upstream_commit"], "ctest_name_from_source": "operators",
    "source_declaration_index": 74, "source_declaration_path": "tests/python/CMakeLists.txt", "source_declaration_line": 703,
    "configured_ctest_execution": False,
    "native_reference": native_id, "browser_execution": attempt_id, "capture_host_execution": host_id,
    "artifact": attempt["artifact"], "base_source_build_receipt": attempt["base_source_build_receipt"],
    "actual_engine_files": attempt["actual_engine_files"], "launcher_profile_id": attempt["launcher_profile_id"],
    "launcher_and_capture_identities": attempt["capture_inputs_before"],
    "launcher_derivation": identity(HERE / "launcher-derivation.json"),
    "browser_version": attempt["browser_version"],
    "browser_runtime_build_banner": [line for line in stdout.read_text().splitlines() if line.startswith("Blender 5.2.0")],
    "browser_execution_elapsed_seconds_including_load": attempt["execution_elapsed_seconds"],
    "native_execution_elapsed_seconds": native["elapsed_seconds"],
    "native_original_cases_executed": 105, "native_original_passes": 105,
    "browser_original_cases_executed": 105, "browser_original_observed_passes": 103,
    "browser_original_observed_failures": 2, "browser_original_skips": 0,
    "browser_missing_original_cases": [], "browser_unexpected_original_cases": [], "browser_duplicated_original_names": [],
    "original_invocation_completed": True, "original_invocation_passed": False,
    "execution_and_observation_integrity_verified": True,
    "qualified_original_browser_passes_under_whole_invocation_gate": 0,
    "qualified_original_pass_pairs_under_whole_invocation_gate": 0,
    "failed_qualification_checks": failed_checks,
    "original_command_and_cwd_preserved": True, "original_script_helper_and_fixture_preserved": True,
    "oracle_update_environment_key_absent": True,
    "browser_byte_preservation_observed_at": "Original Blender quit stdout, after every original case result and before Emscripten runtime teardown.",
    "runtime_exit_codes": [1], "chrome_process_returncode": 0, "capture_host_returncode": 1,
    "raw_stdout": identity(stdout), "raw_stderr": identity(HERE / "attempt-01-elevated/original-stderr.log"),
    "original_failure_cases": failed, "cases": cases, "source_basis": source_basis_id,
    "runtime_context_evidence": [identity(context / name) for name in ("native-context.json", "CMakeCache.txt", "source-build.json")],
    "failure_classification": "Original browser mesh comparator reports different edge topology for two valid meshes that pass the native reference.",
    "resource_or_observer_failure": False,
    "root_cause_reproduced": False,
    "unresolved_cause": "The current evidence does not distinguish divergent fill output from a comparator difference or identify a numerical, sorting, backend, or other source cause.",
    "original_ui_shell_used": False, "source_correspondence_verified": False,
    "prior_829_case_ledger_modified": False, "full_feature_parity": False,
}
with (HERE / "summary.json").open("x") as stream:
    stream.write(json.dumps(summary, indent=2) + "\n")
print(json.dumps(identity(HERE / "summary.json")))
