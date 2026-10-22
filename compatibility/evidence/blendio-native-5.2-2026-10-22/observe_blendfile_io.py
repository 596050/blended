#!/usr/bin/env python3
"""Observe the unchanged Blender blend-file custom driver, without patching it.

Run in Blender's embedded Python 3.12+ interpreter. PY_RETURN and PY_UNWIND
distinguish actual normal returns from exceptional exits. Neither test methods,
assertions, the upstream main function, nor TestHelper.run_all_tests are replaced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import traceback

UPSTREAM_COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"
SOURCE_HASHES = {
    "bl_blendfile_io.py": "8bdb127eef664597061e455cad061959d59a66ce5ed54e4f35a73d3753802700",
    "bl_blendfile_utils.py": "f36545a691afe5a06229b394ee6c8a3537675dbaa85a987819899eea0cc61f02",
}
EXPECTED_CASES = [
    "TestBlendFileSaveLoadBasic.test_save_load",
    "TestBlendFileSavePartial.test_save_load",
    "TestIdRuntimeTag.test_basics",
    "TestIdRuntimeTag.test_linking",
]
MARKER = "BLENDED_BLEND_IO_RESULT:"


def file_record(path, relative_to=None):
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(relative_to)) if relative_to else path.name,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def source_records(directory):
    rows = [file_record(directory / name) for name in SOURCE_HASHES]
    for row in rows:
        if row["sha256"] != SOURCE_HASHES[row["path"]]:
            raise RuntimeError("unchanged upstream source hash mismatch: " + row["path"])
    return rows


def output_inventory(directory):
    if not directory.exists():
        return []
    return [file_record(path, directory) for path in sorted(directory.rglob("*")) if path.is_file()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    source_dir, output_dir = args.source_dir.resolve(), args.output_dir.resolve()
    source = source_dir / "bl_blendfile_io.py"
    helper = source_dir / "bl_blendfile_utils.py"
    report = {
        "schema": 1,
        "scope": "unchanged Blender 5.2.0 custom-driver blend-file I/O suite only",
        "upstream_commit": UPSTREAM_COMMIT,
        "assertions_modified": False,
        "test_callables_replaced": False,
        "helper_driver_replaced": False,
        "entrypoint": "runpy.run_path(original_source, run_name='__main__')",
        "observation": "CPython sys.monitoring PY_START, PY_RETURN and PY_UNWIND",
        "expected_cases": EXPECTED_CASES,
        "expected_count": len(EXPECTED_CASES),
        "identity": {},
        "source_files": [],
        "cases": [],
        "driver_events": [],
        "observer_errors": [],
        "module_exception": None,
        "module_returned_normally": False,
        "browser_executed": False,
        "full_facet_parity": False,
        "full_feature_parity": False,
    }
    case_by_id = {}
    tool_id = None
    caught = None
    old_argv = sys.argv[:]
    event_numbers = []

    def event_record(kind, code, value, frame):
        """Observe original frames. Never let an observer error enter a test."""
        try:
            if code.co_filename == str(helper) and code.co_name == "run_all_tests":
                instance = frame.f_locals.get("self")
                row = {"class": type(instance).__name__, "event": kind}
                if kind == "unwind":
                    row["exception"] = {"type": type(value).__name__, "message": str(value)}
                report["driver_events"].append(row)
                return
            caller = frame.f_back
            if (caller is None or caller.f_code.co_filename != str(helper) or
                    caller.f_code.co_name != "run_all_tests"):
                return
            instance = caller.f_locals.get("self")
            method = caller.f_locals.get("inst_attr_id", "")
            if (frame.f_locals.get("self") is not instance or
                    not isinstance(method, str) or not method.startswith("test_")):
                return
            stage = {"setUp": "setup", "tearDown": "teardown"}.get(code.co_name)
            if stage is None and code.co_name == method:
                stage = "body"
            if stage is None:
                return
            case_id = type(instance).__name__ + "." + method
            if case_id not in case_by_id:
                row = {"id": case_id, "events": [], "files_before": output_inventory(output_dir)}
                case_by_id[case_id] = row
                report["cases"].append(row)
            row = case_by_id[case_id]
            event = {"phase": stage, "event": kind}
            if kind == "unwind":
                event["exception"] = {"type": type(value).__name__, "message": str(value)}
            row["events"].append(event)
            if stage == "teardown" and kind in ("return", "unwind"):
                row["files_after"] = output_inventory(output_dir)
        except BaseException:
            report["observer_errors"].append(traceback.format_exc())

    def started(code, instruction_offset):
        event_record("start", code, None, sys._getframe(1))

    def returned(code, instruction_offset, value):
        event_record("return", code, value, sys._getframe(1))

    def unwound(code, instruction_offset, exception):
        event_record("unwind", code, exception, sys._getframe(1))

    try:
        import bpy

        def text(value):
            return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)

        report["identity"] = {
            "version": list(bpy.app.version),
            "version_string": bpy.app.version_string,
            "build_hash": text(bpy.app.build_hash),
            "build_branch": text(bpy.app.build_branch),
            "binary_path": bpy.app.binary_path,
            "python_version": sys.version,
        }
        report["source_files"] = source_records(source_dir)
        if "bl_blendfile_utils" in sys.modules:
            raise RuntimeError("upstream helper is already imported; require an isolated interpreter")
        if output_dir.exists() and any(output_dir.iterdir()):
            raise RuntimeError("output directory must be empty before original test execution")
        monitoring = getattr(sys, "monitoring", None)
        if monitoring is None:
            raise RuntimeError("per-case observer requires CPython sys.monitoring")
        tool_id = next((i for i in range(5, -1, -1) if monitoring.get_tool(i) is None), None)
        if tool_id is None:
            raise RuntimeError("no unused CPython monitoring tool ID")
        monitoring.use_tool_id(tool_id, "blended_original_blendfile_io")
        callbacks = [(monitoring.events.PY_START, started),
                     (monitoring.events.PY_RETURN, returned),
                     (monitoring.events.PY_UNWIND, unwound)]
        event_numbers = [event for event, _ in callbacks]
        for event, callback in callbacks:
            monitoring.register_callback(tool_id, event, callback)
        monitoring.set_events(tool_id, sum(event_numbers))
        # The original __main__ block performs its own argument normalization,
        # preference change, TESTS iteration, construction and helper dispatch.
        sys.argv = [str(source), "--", "--output-dir", str(output_dir)]
        runpy.run_path(str(source), run_name="__main__")
        report["module_returned_normally"] = True
    except BaseException:
        caught = sys.exc_info()
        report["module_exception"] = traceback.format_exc()
    finally:
        if tool_id is not None:
            sys.monitoring.set_events(tool_id, 0)
            for event in event_numbers:
                sys.monitoring.register_callback(tool_id, event, None)
            sys.monitoring.free_tool_id(tool_id)
        sys.argv = old_argv

    expected_events = [(phase, kind) for phase in ("setup", "body", "teardown")
                       for kind in ("start", "return")]
    for row in report["cases"]:
        actual = [(event["phase"], event["event"]) for event in row["events"]]
        row["status"] = "passed" if actual == expected_events else "failed"
        before = {file["path"]: file for file in row["files_before"]}
        after = {file["path"]: file for file in row.get("files_after", [])}
        row["new_or_changed_outputs"] = [record for path, record in after.items() if before.get(path) != record]
    observed_ids = [row["id"] for row in report["cases"]]
    report["missing_case_ids"] = [case_id for case_id in EXPECTED_CASES if case_id not in observed_ids]
    report["unexpected_case_ids"] = [case_id for case_id in observed_ids if case_id not in EXPECTED_CASES]
    report["generated_files"] = output_inventory(output_dir)
    try:
        report["source_files_after"] = source_records(source_dir)
        report["source_bytes_preserved"] = report["source_files"] == report["source_files_after"]
        imported = sys.modules.get("bl_blendfile_utils")
        report["helper_import_path"] = str(Path(imported.__file__).resolve()) if imported else None
        report["expected_helper_imported"] = report["helper_import_path"] == str(helper)
    except BaseException:
        report["observer_errors"].append(traceback.format_exc())
    expected_driver_events = [{"class": class_name, "event": event}
                              for class_name in ("TestBlendFileSaveLoadBasic", "TestBlendFileSavePartial", "TestIdRuntimeTag")
                              for event in ("start", "return")]
    identity = report["identity"]
    report["runtime_identity_verified"] = (identity.get("version") == [5, 2, 0] and
                                           identity.get("build_hash") in (UPSTREAM_COMMIT, UPSTREAM_COMMIT[:12]))
    report["status"] = "passed" if (
        report["runtime_identity_verified"] and report["module_returned_normally"] and
        report.get("source_bytes_preserved") and report.get("expected_helper_imported") and
        not report["observer_errors"] and observed_ids == EXPECTED_CASES and
        report["driver_events"] == expected_driver_events and
        all(row["status"] == "passed" for row in report["cases"])
    ) else "failed"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(MARKER + json.dumps(report, sort_keys=True), flush=True)
    if caught is not None:
        raise caught[1].with_traceback(caught[2])
    if report["status"] != "passed":
        raise RuntimeError("original custom-driver qualification did not satisfy its fixed four-case inventory")


if __name__ == "__main__":
    main()
