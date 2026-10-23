#!/usr/bin/env python3
"""Create new versioned observer files; never alter the failed v1 evidence."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def replace_one(text, old, new):
    if text.count(old) != 1:
        raise ValueError("expected exactly one original observer fragment: " + old[:80])
    return text.replace(old, new, 1)


def write_new(name, text):
    with (HERE / name).open("x") as stream:
        stream.write(text)


script = (HERE / "launcher.js").read_text()
script = replace_one(script, '      print: line => emit("stdout", String(line)),', '''      print: line => {
        emit("stdout", String(line));
        if (String(line) === "Blender quit") {
          state.originalQuitObservations = (state.originalQuitObservations || 0) + 1;
          state.originalQuitStdoutSequence = state.events.at(-1).sequence;
          try {
            state.mountedFilesAtOriginalQuit = inspectFiles(config, inputs);
            emit("original_inputs_observed_at_original_quit", {
              original_quit_stdout_sequence: state.originalQuitStdoutSequence,
              files: state.mountedFilesAtOriginalQuit,
              boundary: "original Blender quit stdout before Emscripten runtime teardown",
            });
          } catch (error) {
            state.originalQuitFileObservationError = String(error);
            emit("original_quit_file_observation_error", String(error));
          }
        }
      },''')
script = replace_one(script, '''        try {
          state.mountedFilesAtRuntimeExit = inspectFiles(config, inputs);
        } catch (error) {
          state.exitFileObservationError = String(error);
        }
        emit("runtime_exit", {code, actual_argv: state.actualArgvAtRuntimeExit,
             files: state.mountedFilesAtRuntimeExit || null,
             file_observation_error: state.exitFileObservationError || null});''', '''        emit("runtime_exit", {code, actual_argv: state.actualArgvAtRuntimeExit,
             filesystem_capture_boundary: "original Blender quit stdout before runtime teardown",
             original_quit_stdout_sequence: state.originalQuitStdoutSequence});''')
write_new("launcher-v2.js", script)
html = replace_one((HERE / "launcher.html").read_text(), '/launcher.js', '/launcher-v2.js')
write_new("launcher-v2.html", html)

runner = (HERE / "run-browser.py").read_text()
runner = replace_one(runner, 'HERE / "run-browser.py", HERE / "launcher.js", HERE / "launcher.html",',
                     'Path(__file__).resolve(), HERE / "launcher-v2.js", HERE / "launcher-v2.html",\n        NATIVE_FIRST / "run-native.py", NATIVE_GOOD / "summary.json", NATIVE_GOOD / "prospective-command.json",')
runner = replace_one(runner, '    original_inputs = []', '    original_inputs = []\n    expected_mounted_rows = []')
runner = replace_one(runner, '               "original_ui_shell_used": False, "source_correspondence_verified": False,',
                     '               "launcher_profile_id": "original-bmesh-bevel-essentials-chromium-custom-launcher-v2",\n               "original_ui_shell_used": False, "source_correspondence_verified": False,')
runner = replace_one(runner, 'for name in ("launcher.html", "launcher.js"):', 'for name in ("launcher-v2.html", "launcher-v2.js"):')
runner = replace_one(runner, 'server = serve(shell, binary, "launcher.html", output)',
                     'server = serve(shell, binary, "launcher-v2.html", output)')
runner = replace_one(runner, '''            if len(files) != 3:
                raise ValueError("expected exactly the original script, helper, and fixture")''', '''            if len(files) != 3:
                raise ValueError("expected exactly the original script, helper, and fixture")
            expected_mounted_rows = [{"virtual_path": row["virtual_path"], "bytes": row["bytes"],
                                      "sha256_of_verified_input": row["sha256"],
                                      "byte_for_byte_equal_to_verified_input": True} for row in files]''')
runner = replace_one(runner, '''    spec = importlib.util.spec_from_file_location("frozen_native_bevel_parser", NATIVE_FIRST / "run-native.py")''', '''    receipt["original_log_parser_reverified_before_import"] = expected(NATIVE_FIRST / "run-native.py", NATIVE_PARSER_SHA)
    spec = importlib.util.spec_from_file_location("frozen_native_bevel_parser", NATIVE_FIRST / "run-native.py")''')
runner = replace_one(runner, '''    checks = {''', '''    original_quit_events = [event for event in raw_events if event["kind"] == "stdout" and event["detail"] == "Blender quit"]
    byte_boundary_events = [event for event in raw_events if event["kind"] == "original_inputs_observed_at_original_quit"]
    runtime_exit_events = [event for event in raw_events if event["kind"] == "runtime_exit"]
    original_case_events = [event for event in raw_events if event["kind"] == "stdout" and event["detail"].startswith(
        ("START ", "PASSED ", "FAILED ", "Mesh Comparison : ", "Mesh Validation : "))]
    complete_boundary = (
        len(original_quit_events) == len(byte_boundary_events) == len(runtime_exit_events) == 1 and
        bool(original_case_events) and state.get("originalQuitObservations") == 1 and
        max(event["sequence"] for event in original_case_events) < original_quit_events[0]["sequence"] and
        original_quit_events[0]["sequence"] + 1 == byte_boundary_events[0]["sequence"] < runtime_exit_events[0]["sequence"] and
        state.get("originalQuitStdoutSequence") == original_quit_events[0]["sequence"] and
        byte_boundary_events[0]["detail"].get("files") == expected_mounted_rows)
    receipt["original_quit_byte_observation_boundary_verified"] = complete_boundary
    receipt["expected_mounted_file_rows"] = expected_mounted_rows
    checks = {''')
runner = replace_one(runner, '''        "pre_main_original_bytes_verified": len(state.get("mountedFilesBeforeMain", [])) == 3 and all(
            row.get("byte_for_byte_equal_to_verified_input") is True for row in state.get("mountedFilesBeforeMain", [])),
        "exit_original_bytes_verified": len(state.get("mountedFilesAtRuntimeExit", [])) == 3 and all(
            row.get("byte_for_byte_equal_to_verified_input") is True for row in state.get("mountedFilesAtRuntimeExit", [])),''', '''        "pre_main_original_bytes_verified": len(expected_mounted_rows) == 3 and state.get("mountedFilesBeforeMain") == expected_mounted_rows,
        "original_bytes_unchanged_at_original_quit": len(expected_mounted_rows) == 3 and state.get("mountedFilesAtOriginalQuit") == expected_mounted_rows,
        "byte_observation_after_all_original_case_results_before_runtime_exit": complete_boundary,''')
write_new("run-browser-v2.py", runner)

capture = (HERE / "capture-process.py").read_text().replace('"run-browser.py"', '"run-browser-v2.py"')
write_new("capture-process-v2.py", capture)
