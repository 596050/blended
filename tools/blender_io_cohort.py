"""Transport the original blend-file script and observe its custom test driver.

This adapter never substitutes unittest discovery, changes an assertion, or
replaces an upstream callable. Runtime identity is assessed by the shared probe.
The emitted program is self-contained for Blender's embedded Python interpreter.
"""
from __future__ import annotations

import base64
import json


RUNTIME_SOURCE = r'''
def _blended_run_original_io(encoded_suites, marker, output_root, wait_for_output_transfer):
    import base64
    import hashlib
    import json
    from pathlib import Path, PurePosixPath
    import runpy
    import sys
    import traceback

    report = {"identity": {}, "exception": None, "suites": [],
              "io_observation": {"entrypoint": "original __main__ via runpy.run_path",
                  "events": "CPython sys.monitoring PY_START/PY_RETURN/PY_UNWIND",
                  "assertions_modified": False, "test_callables_replaced": False,
                  "helper_driver_replaced": False, "cases": [], "driver_events": [],
                  "observer_errors": [], "module_returned_normally": False,
                  "source_bytes_preserved": False, "helper_import_verified": False},
              "generated_files": {"root": None, "files": []}}
    observation = report["io_observation"]
    tool_id = None
    event_numbers = []
    old_argv, old_path = sys.argv[:], sys.path[:]
    source_records = []
    root = source_dir = output_dir = main_path = helper_path = None
    row = None
    active = {}

    def digest(path):
        value = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(chunk)
        return value.hexdigest()

    def inventory():
        if output_dir is None or not output_dir.exists():
            return []
        files = []
        for path in sorted(output_dir.iterdir()):
            if path.is_symlink() or not path.is_file():
                raise RuntimeError("original I/O output is not a confined regular file: " + path.name)
            files.append({"path": path.name, "bytes": path.stat().st_size, "sha256": digest(path)})
        return files

    def decode_source(metadata, encoded):
        data = base64.b64decode(encoded, validate=True)
        if (type(metadata.get("bytes")) is not int or len(data) != metadata["bytes"] or
                hashlib.sha256(data).hexdigest() != metadata.get("sha256")):
            raise RuntimeError("original I/O source changed in transport: " + str(metadata.get("upstream_path")))
        path = PurePosixPath(metadata["upstream_path"])
        if path.is_absolute() or ".." in path.parts or "\\" in str(path) or not path.name.endswith(".py"):
            raise RuntimeError("invalid original I/O source path")
        return path.name, data

    def new_case(caller):
        instance = caller.f_locals.get("self")
        method = caller.f_locals.get("inst_attr_id", "")
        case = {"id": "blended_original." + type(instance).__name__ + "." + method,
                "events": [], "files_before": inventory()}
        observation["cases"].append(case)
        active[id(caller)] = case
        return case

    def event_record(kind, code, value, frame):
        # Callback failures must not enter or change the original execution.
        # They are retained and block qualification after the original call ends.
        try:
            if code.co_filename == str(helper_path) and code.co_name == "run_all_tests":
                entry = {"class": type(frame.f_locals.get("self")).__name__, "event": kind}
                if kind == "unwind":
                    entry["exception"] = {"type": type(value).__name__, "message": str(value)}
                observation["driver_events"].append(entry)
                if kind in ("return", "unwind"):
                    active.pop(id(frame), None)
                return
            caller = frame.f_back
            if (caller is None or caller.f_code.co_filename != str(helper_path) or
                    caller.f_code.co_name != "run_all_tests"):
                return
            instance = caller.f_locals.get("self")
            method = caller.f_locals.get("inst_attr_id", "")
            if (frame.f_locals.get("self") is not instance or
                    not isinstance(method, str) or not method.startswith("test_")):
                return
            phase = {"setUp": "setup", "tearDown": "teardown"}.get(code.co_name)
            if phase is None and code.co_name == method:
                phase = "body"
            if phase is None:
                return
            case = active.get(id(caller))
            if phase == "setup" and kind == "start":
                case = new_case(caller)
            elif case is None:
                case = new_case(caller)
            event = {"phase": phase, "event": kind}
            if kind == "unwind":
                event["exception"] = {"type": type(value).__name__, "message": str(value),
                                      "assertion_failure": isinstance(value, AssertionError)}
            case["events"].append(event)
            if phase == "teardown" and kind in ("return", "unwind"):
                case["files_after"] = inventory()
                active.pop(id(caller), None)
        except BaseException:
            observation["observer_errors"].append(traceback.format_exc())

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
        report["identity"] = {"version": list(bpy.app.version),
            "version_string": bpy.app.version_string, "build_hash": text(bpy.app.build_hash),
            "build_branch": text(bpy.app.build_branch), "binary_path": bpy.app.binary_path}
        report["execution_context"] = {"background": bpy.app.background,
            "window_present_at_entry": bpy.context.window is not None if hasattr(bpy, "context") else None}
        suites = json.loads(encoded_suites)
        if len(suites) != 1:
            raise RuntimeError("the original I/O cohort requires exactly one main script")
        row = suites[0]
        ids = row.get("case_ids", [])
        if (not ids or len(ids) != len(set(ids)) or row.get("expected_cases") != len(ids)):
            raise RuntimeError("original I/O fixed method inventory is invalid")
        observation["expected_case_ids"] = ids
        root = Path(output_root)
        if not root.is_absolute() or ".." in root.parts or root == Path(root.anchor):
            raise RuntimeError("original I/O output root must be a confined absolute directory")
        if root.is_symlink() or (root.exists() and any(root.iterdir())):
            raise RuntimeError("original I/O output root must be fresh and empty")
        root = root.resolve()
        source_dir, output_dir = root / "sources", root / "files"
        report["generated_files"]["root"] = str(output_dir)
        main_name, main_data = decode_source(row, row["source_b64"])
        expected_support = row.get("support_files", [])
        provided_support = row.get("_support_payloads", [])
        keys = ("upstream_path", "sha256", "bytes")
        if (len(expected_support) != len(provided_support) or
                [{key: value.get(key) for key in keys} for value in expected_support] !=
                [{key: value.get(key) for key in keys} for value in provided_support]):
            raise RuntimeError("original I/O support-source inventory changed")
        decoded = [(row, main_name, main_data)]
        for support in provided_support:
            name, data = decode_source(support, support["source_b64"])
            decoded.append((support, name, data))
        names = [name for _, name, _ in decoded]
        if len(set(names)) != len(names) or "bl_blendfile_utils.py" not in names:
            raise RuntimeError("original I/O requires a unique adjacent upstream helper")
        if "bl_blendfile_utils" in sys.modules:
            raise RuntimeError("original I/O helper is already imported; use an isolated interpreter")
        source_dir.mkdir(parents=True)
        output_dir.mkdir()
        for metadata, name, data in decoded:
            path = source_dir / name
            path.write_bytes(data)
            source_records.append({"upstream_path": metadata["upstream_path"],
                                   "path": str(path), "bytes": len(data), "sha256": metadata["sha256"]})
        observation["source_files"] = source_records
        main_path, helper_path = source_dir / main_name, source_dir / "bl_blendfile_utils.py"
        monitoring = getattr(sys, "monitoring", None)
        if monitoring is None:
            raise RuntimeError("original I/O per-case observation requires CPython sys.monitoring")
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
        sys.argv = [str(main_path), "--", "--output-dir", str(output_dir)]
        runpy.run_path(str(main_path), run_name="__main__")
        observation["module_returned_normally"] = True
    except BaseException:
        report["exception"] = traceback.format_exc()
    finally:
        if tool_id is not None:
            try:
                sys.monitoring.set_events(tool_id, 0)
                for event in event_numbers:
                    sys.monitoring.register_callback(tool_id, event, None)
                sys.monitoring.free_tool_id(tool_id)
            except BaseException:
                observation["observer_errors"].append(traceback.format_exc())
        sys.argv, sys.path = old_argv, old_path

    try:
        expected_events = [(phase, kind) for phase in ("setup", "body", "teardown")
                           for kind in ("start", "return")]
        outcomes = []
        for case in observation["cases"]:
            actual = [(event["phase"], event["event"]) for event in case["events"]]
            exceptions = [event for event in case["events"] if event["event"] == "unwind"]
            if any(not event["exception"]["assertion_failure"] for event in exceptions):
                status = "error"
            elif exceptions:
                status = "failed"
            else:
                status = "passed" if actual == expected_events else "error"
            case["status"] = status
            before = {file["path"]: file for file in case["files_before"]}
            case["new_or_changed_outputs"] = [file for file in case.get("files_after", [])
                                               if before.get(file["path"]) != file]
            outcomes.append({"id": case["id"], "kind": "test", "parent_id": None,
                             "status": status, "detail": None if status == "passed" else
                             json.dumps({"phase_events": case["events"]}, sort_keys=True)})
        observed_ids = [case["id"] for case in observation["cases"]]
        if row is not None:
            report["suites"].append({"upstream_path": row["upstream_path"], "sha256": row["sha256"],
                "discovered_ids": observed_ids, "discovered": len(observed_ids), "testsRun": len(observed_ids),
                "failures": sum(value["status"] == "failed" for value in outcomes),
                "errors": sum(value["status"] == "error" for value in outcomes),
                "skipped": 0, "expected_failures": 0, "unexpected_successes": 0, "outcomes": outcomes})
            expected_ids = ["blended_original." + value for value in row.get("case_ids", [])]
            observation["missing_case_ids"] = [value for value in expected_ids if value not in observed_ids]
            observation["unexpected_case_ids"] = [value for value in observed_ids if value not in expected_ids]
            class_names = list(dict.fromkeys(value.rsplit(".", 1)[0] for value in row.get("case_ids", [])))
            expected_driver = [{"class": name, "event": event} for name in class_names
                               for event in ("start", "return")]
            observation["driver_completed_as_expected"] = observation["driver_events"] == expected_driver
            if observed_ids != expected_ids or not observation["driver_completed_as_expected"]:
                observation["observer_errors"].append("fixed original method inventory or driver lifecycle is incomplete")
        observation["source_bytes_preserved"] = bool(source_records) and all(
            Path(value["path"]).stat().st_size == value["bytes"] and
            digest(Path(value["path"])) == value["sha256"] for value in source_records)
        imported = sys.modules.get("bl_blendfile_utils")
        imported_path = str(Path(imported.__file__).resolve()) if imported is not None else None
        observation["helper_import_path"] = imported_path
        observation["helper_import_verified"] = helper_path is not None and imported_path == str(helper_path)
        if not observation["source_bytes_preserved"] or not observation["helper_import_verified"]:
            observation["observer_errors"].append("unchanged source bytes or exact helper import could not be verified")
        report["generated_files"]["files"] = inventory()
    except BaseException:
        observation["observer_errors"].append(traceback.format_exc())
    if observation["observer_errors"] and report["exception"] is None:
        report["exception"] = "Original I/O observation failed: " + "\n".join(observation["observer_errors"])
    handshake = None
    if wait_for_output_transfer and root is not None and root.is_dir():
        import os
        handshake = {"required": True, "protocol": "blended-output-transfer-v1",
                     "token": hashlib.sha256(marker.encode("utf-8")).hexdigest(),
                     "ack_path": str(root / "transfer-ack.json"), "timeout_seconds": 60,
                     "exclusive_create_flags": os.O_WRONLY | os.O_CREAT | os.O_EXCL}
    report["output_transfer_handshake"] = handshake
    print(marker + json.dumps(report, sort_keys=True), flush=True)
    if handshake is not None:
        # This is after the complete original driver and after monitoring is
        # disabled. Keep WasmFS alive only until the host verifies output bytes.
        import time
        ack_path = Path(handshake["ack_path"])
        deadline = time.monotonic() + handshake["timeout_seconds"]
        while not ack_path.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not ack_path.is_file() or ack_path.is_symlink():
            raise RuntimeError("output transfer acknowledgement timed out or is not a regular file")
        with ack_path.open("rb") as stream:
            raw_ack = stream.read(16385)
        if len(raw_ack) > 16384:
            raise RuntimeError("output transfer acknowledgement exceeds its bound")
        ack = json.loads(raw_ack)
        if (not isinstance(ack, dict) or ack.get("protocol") != handshake["protocol"] or
                ack.get("token") != handshake["token"] or ack.get("status") != "verified" or
                ack.get("files") != report["generated_files"]["files"]):
            raise RuntimeError("output transfer acknowledgement did not verify the original file inventory")
'''


def python_payload(suites, marker, output_root, wait_for_output_transfer=False):
    """Embed exact main/helper bytes and the observer in one Blender program."""
    if len(suites) != 1:
        raise ValueError("the original I/O cohort requires one main script")
    if not isinstance(marker, str) or not marker:
        raise ValueError("a nonempty I/O result marker is required")
    if type(wait_for_output_transfer) is not bool:
        raise ValueError("output transfer wait must be boolean")
    encoded = [{**row, "source_b64": base64.b64encode(data).decode("ascii")}
               for row, data in suites]
    return RUNTIME_SOURCE + "\n_blended_run_original_io(" + ", ".join(
        repr(value) for value in (json.dumps(encoded), marker, str(output_root), wait_for_output_transfer)) + ")\n"
