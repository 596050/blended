#!/usr/bin/env python3
"""Freeze the completed browser bevel outcome separately from existing ledgers."""
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
        raise ValueError("frozen execution receipt changed: " + str(path))
    return json.loads(path.read_text()), measured


native_path = REPO / "compatibility/evidence/bmesh-bevel-source-native-elevated-5.2-2026-10-23/summary.json"
native, native_id = load_expected(native_path, "54b9c3e3bfe5504dc151ed534dd7039fec0d85a15315ac61e0860002b5ee949d")
attempt, attempt_id = load_expected(HERE / "attempt-03-v2-elevated/execution.json",
    "0391eb0a049f23c5f636799abf2328ed4a64a850add6f1f793778444a0f8c217")
host, host_id = load_expected(HERE / "attempt-03-v2-elevated-host/execution.json",
    "b5fc1c46c311d90db13f340c16b650d802395e2c013d55ec3f9a0c782da381ed")
if not attempt["qualified_original_invocation"] or not all(attempt["qualification_checks"].values()):
    raise ValueError("browser invocation did not qualify")
if host["actual_process_returncode"] != 0 or host["timed_out"] or host["child_receipt"] != attempt_id:
    raise ValueError("host process did not successfully capture this exact receipt")
observations = attempt["original_stdout_observations"]["observations"]
native_cases = native["case_evidence"]
if len(observations) != len(native_cases) or len(observations) != 88:
    raise ValueError("runtime case sets differ from both successful observed invocations")
native_by_name = {case["name"]: case for case in native_cases}
if len(native_by_name) != 88 or {row["name"] for row in observations} != set(native_by_name):
    raise ValueError("original case names are missing, duplicated, or unexpected")
cases = []
for row in observations:
    native_row = native_by_name[row["name"]]
    declaration = row["original_source_declaration"]
    if native_row["original_source_declaration"] != declaration or row["status"] != native_row["status"] or row["status"] != "passed":
        raise ValueError("source-qualified case observations differ")
    case_id = ":".join((attempt["upstream_commit"], "bmesh_bevel", declaration["upstream_path"],
                        str(declaration["line"]), row["name"], declaration["spec_sha256"]))
    cases.append({"case_id": case_id, "name": row["name"], "native_status": native_row["status"],
                  "browser_status": row["status"], "source_declaration": declaration,
                  "browser_stdout_line": row["start_log_line"],
                  "original_mesh_comparison": row["mesh_comparison"],
                  "original_mesh_validation": row["mesh_validation"]})
attempt_rows = []
for name in ("attempt-01", "attempt-02-elevated", "attempt-03-v2-elevated"):
    data = json.loads((HERE / name / "execution.json").read_text())
    process = json.loads((HERE / (name + "-host") / "execution.json").read_text())
    attempt_rows.append({"attempt": name, "receipt": identity(HERE / name / "execution.json"),
                         "host_receipt": identity(HERE / (name + "-host") / "execution.json"),
                         "observed_original_passes": data["original_stdout_observations"]["observed_passes"],
                         "qualified_original_browser_passes": data["qualified_original_browser_passes"],
                         "runtime_exit_codes": data["runtime_state"].get("runtimeExitCodes", []),
                         "chrome_returncode": data.get("actual_chrome_process_returncode"),
                         "capture_host_returncode": process["actual_process_returncode"],
                         "failed_checks": [key for key, value in data["qualification_checks"].items() if not value],
                         "errors": data["errors"]})
stdout_path = HERE / "attempt-03-v2-elevated/original-stdout.log"
summary = {
    "schema": 1, "kind": "original-bmesh-bevel-native-browser-comparison",
    "created_utc": datetime.now(timezone.utc).isoformat(), "summary_driver": identity(Path(__file__).resolve()),
    "upstream_commit": attempt["upstream_commit"], "ctest_name_from_source": "bmesh_bevel",
    "source_declaration_index": 49, "source_declaration_path": "tests/python/CMakeLists.txt", "source_declaration_line": 517,
    "configured_ctest_execution": False,
    "native_reference": native_id, "browser_execution": attempt_id, "capture_host_execution": host_id,
    "artifact": attempt["artifact"], "base_source_build_receipt": attempt["base_source_build_receipt"],
    "actual_engine_files": attempt["actual_engine_files"], "launcher_profile_id": attempt["launcher_profile_id"],
    "launcher_and_capture_identities": attempt["capture_inputs_before"],
    "browser_version": attempt["browser_version"],
    "browser_runtime_build_banner": [line for line in stdout_path.read_text().splitlines() if line.startswith("Blender 5.2.0")],
    "browser_execution_elapsed_seconds_including_load": attempt["execution_elapsed_seconds"],
    "native_execution_elapsed_seconds": 2.116751,
    "native_and_browser_original_case_sets_equal": True,
    "original_case_count_observed_in_each_completed_invocation": len(cases),
    "source_qualified_original_pass_pairs": len(cases),
    "original_failures_in_qualified_browser_invocation": 0, "original_skips_in_qualified_browser_invocation": 0,
    "original_case_ids_missing_in_browser": [], "original_case_ids_unexpected_in_browser": [],
    "original_case_names_duplicated_in_browser": [],
    "original_command_and_cwd_preserved": True, "original_script_helper_and_fixture_preserved": True,
    "oracle_update_environment_key_absent": True,
    "browser_byte_preservation_observed_at": "Original Blender quit stdout, after every original case result and before Emscripten runtime teardown.",
    "runtime_exit_codes": attempt["runtime_state"]["runtimeExitCodes"],
    "chrome_process_returncode": attempt["actual_chrome_process_returncode"],
    "capture_host_returncode": host["actual_process_returncode"],
    "raw_stdout": identity(stdout_path), "raw_stderr": identity(HERE / "attempt-03-v2-elevated/original-stderr.log"),
    "attempts": attempt_rows, "cases": cases,
    "limitations": [
        "This is a separate original custom mesh-driver invocation with a new evidence-only launcher, outside the frozen unittest matrices and ledgers.",
        "The original source-derived command is preserved; no configured CTest run is claimed.",
        "The existing Essentials package engine was not rebuilt for this execution, and source-build correspondence is not independently established.",
        "The CPU mesh oracles do not establish rendered image, UI, GPU hardware, or whole-application parity.",
        "Browser stderr retains the existing missing external Python binary warning; Chromium's software GPU diagnostics are retained without inferring hardware capability.",
    ],
    "original_ui_shell_used": False, "source_correspondence_verified": False,
    "prior_829_case_ledger_modified": False, "full_feature_parity": False,
}
with (HERE / "summary.json").open("x") as stream:
    stream.write(json.dumps(summary, indent=2) + "\n")
print(json.dumps(identity(HERE / "summary.json")))
