#!/usr/bin/env python3
"""Run the unchanged source-derived bevel driver with an explicit browser launcher."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"
sys.path.insert(0, str(REPO / "tools"))
from browser_package_overlay import verify_overlay_receipt
from probe_browser_port import extract_asset, serve
from playwright.sync_api import sync_playwright

NATIVE_FIRST = REPO / "compatibility/evidence/bmesh-bevel-source-native-5.2-2026-10-23"
NATIVE_GOOD = REPO / "compatibility/evidence/bmesh-bevel-source-native-elevated-5.2-2026-10-23"
SOURCE_PIN = "fbe6228777e7d9afefcd61a413844e790ae75db7"
NATIVE_SUMMARY_SHA = "54b9c3e3bfe5504dc151ed534dd7039fec0d85a15315ac61e0860002b5ee949d"
NATIVE_RECEIPT_SHA = "4e3a34d7bb949b6bd7e4c6a050ea4c62c41958ccdc5b672a8c5b4e004aaee48d"
NATIVE_COMMAND_SHA = "7c3b0da36e5552299dfe97e40c87fafde231e4587525cafa631d799b83734d09"
NATIVE_PARSER_SHA = "98f2ebc9f46b28a0452e4e0dcb37c256d76ec76a24213475ae0d8795eabf1d33"
ARTIFACT_SHA = "3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910"
SOURCE_RECEIPT_SHA = "5ed2a839fc340d16de08a096be3db74506a4cffdaaa87f40fbd1553810b53ce3"


def identity(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def expected(path, sha):
    measured = identity(path)
    if measured["sha256"] != sha:
        raise ValueError("input SHA256 differs from frozen native/artifact evidence: " + str(path))
    return measured


def write_new(path, obj):
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(obj, indent=2) + "\n")


def snapshot_helpers():
    return [identity(path) for path in (
        HERE / "run-browser.py", HERE / "launcher.js", HERE / "launcher.html",
        REPO / "tools/probe_browser_port.py", REPO / "tools/browser_package_overlay.py")]


def run(output, timeout):
    output.mkdir(parents=False, exist_ok=False)
    began = time.monotonic()
    receipt = {"schema": 1, "kind": "original-bmesh-bevel-browser-invocation", "status": "blocked",
               "started_utc": datetime.now(timezone.utc).isoformat(), "upstream_commit": SOURCE_PIN,
               "configured_ctest_execution": False, "original_invocation_kind": "source-derived original Blender command",
               "scope": "unchanged original bevel driver on the measured Essentials engine with a new evidence-only launcher",
               "original_ui_shell_used": False, "source_correspondence_verified": False,
               "full_feature_parity": False, "timeout_seconds": timeout, "errors": [],
               "timed_out": False, "page_errors": [], "failed_requests": [], "browser_crashed": False,
               "test_files_modified": False, "oracle_modified": False,
               "capture_inputs_before": snapshot_helpers()}
    original_inputs = []
    chrome = None
    server = None
    browser = None
    page = None
    console_events = []
    state = {}
    raw_events = []
    with (output / "original-stdout.log").open("x", encoding="utf-8") as stdout_log, \
         (output / "original-stderr.log").open("x", encoding="utf-8") as stderr_log, \
         (output / "browser-console.jsonl").open("x", encoding="utf-8") as console_log, \
         (output / "launcher-events.jsonl").open("x", encoding="utf-8") as event_log, \
         (output / "chrome.stdout.log").open("xb") as chrome_stdout, \
         (output / "chrome.stderr.log").open("xb") as chrome_stderr, \
         tempfile.TemporaryDirectory(prefix="bevel-browser-", dir=RUNTIME) as temp:
        work = Path(temp)
        try:
            if shutil.disk_usage(work).free < 4 * 1024**3:
                raise RuntimeError("free disk reserve is below 4 GiB")
            receipt["native_summary"] = expected(NATIVE_GOOD / "summary.json", NATIVE_SUMMARY_SHA)
            receipt["native_execution"] = expected(NATIVE_GOOD / "execution.json", NATIVE_RECEIPT_SHA)
            receipt["native_prospective_command"] = expected(NATIVE_GOOD / "prospective-command.json", NATIVE_COMMAND_SHA)
            receipt["original_log_parser"] = expected(NATIVE_FIRST / "run-native.py", NATIVE_PARSER_SHA)
            native_summary = json.loads((NATIVE_GOOD / "summary.json").read_text())
            native_command = json.loads((NATIVE_GOOD / "prospective-command.json").read_text())
            command = native_command["command"]
            if command[-2:] != ["--", "--run-all-tests"]:
                raise ValueError("native invocation is not the original complete comparison driver")
            if not native_summary["exact_original_source_helper_fixture_preserved"]:
                raise ValueError("native original input closure is not verified")
            if native_summary["observed_original_native_passes_in_completed_invocation"] != 88:
                raise ValueError("native frozen runtime observations differ")
            for row in native_command["inputs"]:
                observed = expected(Path(row["path"]), row["sha256"])
                if observed["bytes"] != row["bytes"]:
                    raise ValueError("native input byte length changed")
                original_inputs.append(observed)
            receipt["original_inputs_before"] = original_inputs
            asset = RUNTIME / "brush-package-overlay-5.2/blender-source-development-essentials.tar.gz"
            base_asset = RUNTIME / "source/blender-source-development.tar.gz"
            source_receipt = REPO / "compatibility/evidence/runtime-context-2026-10-23/source-build.json"
            overlay_receipt = REPO / "compatibility/evidence/brush-package-overlay-5.2-2026-10-23/package-overlay.json"
            receipt["artifact"] = expected(asset, ARTIFACT_SHA)
            receipt["base_source_build_receipt"] = expected(source_receipt, SOURCE_RECEIPT_SHA)
            receipt["package_verification"] = verify_overlay_receipt(
                overlay_receipt, source_receipt, base_archive=base_asset, augmented_archive=asset)
            extract_asset(asset, work / "engine")
            engine_root = work / "engine/blender-source-development"
            binary = engine_root / "bin"
            receipt["actual_engine_files"] = [identity(binary / name) for name in (
                "blender_browser.js", "blender_browser.wasm", "blender_browser.data")]
            shell = work / "launcher"
            shell.mkdir()
            for name in ("launcher.html", "launcher.js"):
                shutil.copyfile(HERE / name, shell / name)
            files = []
            for index, row in enumerate(original_inputs):
                if not (row["path"].endswith(".py") or row["path"].endswith(".blend")):
                    continue
                name = "original-input-" + str(index)
                shutil.copyfile(row["path"], shell / name)
                files.append({"virtual_path": row["path"], "url": "/" + name,
                              "bytes": row["bytes"], "sha256": row["sha256"]})
            if len(files) != 3:
                raise ValueError("expected exactly the original script, helper, and fixture")
            environment = {
                "BLENDER_SYSTEM_RESOURCES": "/bw", "BLENDER_SYSTEM_PYTHON": "/bw/python",
                "BLENDER_SYSTEM_SCRIPTS": "/bw/scripts", "BLENDER_SYSTEM_DATAFILES": "/bw/datafiles",
                "BLENDER_USER_RESOURCES": "/projects", "TMPDIR": "/projects/.recovery",
                **native_command["environment_overrides"],
            }
            if any(name in environment for name in ("BLENDER_TEST_UPDATE", "BLENDER_VERBOSE")):
                raise ValueError("oracle update or verbose environment key must be absent")
            manifest = {"schema": 1, "command": command, "cwd": native_command["cwd"],
                        "environment": environment, "files": files, "upstream_commit": SOURCE_PIN}
            write_new(output / "input-manifest.json", manifest)
            shutil.copyfile(output / "input-manifest.json", shell / "input-manifest.json")
            receipt["input_manifest"] = identity(output / "input-manifest.json")
            receipt["command"] = command
            receipt["cwd"] = native_command["cwd"]
            receipt["argv0_note"] = "Original argv[0] string is preserved through thisProgram; executed code is the separately measured Wasm engine."
            receipt["browser_environment"] = environment
            chrome_path = RUNTIME / "chrome/chrome-linux64/chrome"
            receipt["browser_executable"] = identity(chrome_path)
            profile = work / "chrome-profile"
            chrome_args = [str(chrome_path), "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                           "--disable-gpu-watchdog", "--enable-unsafe-webgpu", "--enable-unsafe-swiftshader",
                           "--use-angle=swiftshader", "--remote-debugging-address=127.0.0.1",
                           "--remote-debugging-port=0", "--user-data-dir=" + str(profile), "about:blank"]
            receipt["chrome_command"] = chrome_args
            write_new(output / "prospective-command.json", {k: v for k, v in receipt.items() if k != "package_verification"})
            server = serve(shell, binary, "launcher.html", output)
            receipt["origin"] = "http://127.0.0.1:" + str(server.server_port)
            chrome = subprocess.Popen(chrome_args, stdout=chrome_stdout, stderr=chrome_stderr, start_new_session=True)
            deadline = time.monotonic() + 30
            port_file = profile / "DevToolsActivePort"
            while not port_file.exists() and time.monotonic() < deadline and chrome.poll() is None:
                time.sleep(0.05)
            if not port_file.exists():
                raise RuntimeError("Chrome did not expose its local DevTools endpoint; returncode=" + str(chrome.poll()))
            debug_port = int(port_file.read_text().splitlines()[0])
            def on_console(message):
                item = {"kind": message.type, "text": message.text, "location": message.location}
                console_events.append(item)
                console_log.write(json.dumps(item) + "\n")
                console_log.flush()
                prefix = "BEVEL_BROWSER_EVENT "
                if message.text.startswith(prefix):
                    event = json.loads(message.text[len(prefix):])
                    raw_events.append(event)
                    event_log.write(json.dumps(event) + "\n")
                    event_log.flush()
                    if event["kind"] in ("stdout", "stderr"):
                        log = stdout_log if event["kind"] == "stdout" else stderr_log
                        log.write(event["detail"] + "\n")
                        log.flush()
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:" + str(debug_port))
                receipt["browser_version"] = browser.version
                context = browser.contexts[0]
                page = context.new_page()
                page.set_viewport_size({"width": 1280, "height": 720})
                page.on("console", on_console)
                page.on("pageerror", lambda error: receipt["page_errors"].append(str(error)))
                page.on("requestfailed", lambda request: receipt["failed_requests"].append(
                    {"url": request.url, "failure": request.failure}))
                page.on("crash", lambda: receipt.update(browser_crashed=True))
                execution_began = time.monotonic()
                page.goto(receipt["origin"], wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_function("window.__bevelEvidence?.finished === true", timeout=timeout * 1000)
                except Exception as error:
                    if "Timeout" in type(error).__name__:
                        receipt["timed_out"] = True
                    raise
                finally:
                    receipt["execution_elapsed_seconds"] = round(time.monotonic() - execution_began, 6)
                    try:
                        state = page.evaluate("window.__bevelEvidence || {}")
                    except Exception as error:
                        receipt["errors"].append("state capture: " + str(error))
                    try:
                        session = browser.new_browser_cdp_session()
                        session.send("Browser.close")
                    except Exception as error:
                        receipt["browser_close_note"] = str(error)
            browser = None
        except Exception as error:
            receipt["errors"].append(type(error).__name__ + ": " + str(error))
            (output / "harness-exception.txt").write_text(traceback.format_exc())
        finally:
            if chrome is not None:
                try:
                    chrome.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    receipt["chrome_forced_termination"] = True
                    os.killpg(chrome.pid, signal.SIGTERM)
                    try:
                        chrome.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(chrome.pid, signal.SIGKILL)
                        chrome.wait(timeout=10)
                receipt["actual_chrome_process_returncode"] = chrome.returncode
            if server is not None:
                server.shutdown()
                server.server_close()
    receipt["runtime_state"] = state
    write_new(output / "browser-state.json", state)
    receipt["observed_console_events"] = len(console_events)
    receipt["event_stream_matches_browser_state"] = raw_events == state.get("events", []) and bool(raw_events)
    receipt["capture_inputs_after"] = snapshot_helpers()
    receipt["capture_inputs_unchanged"] = receipt["capture_inputs_before"] == receipt["capture_inputs_after"]
    receipt["original_inputs_after"] = [identity(row["path"]) for row in original_inputs]
    receipt["original_host_inputs_unchanged"] = bool(original_inputs) and original_inputs == receipt["original_inputs_after"]
    spec = importlib.util.spec_from_file_location("frozen_native_bevel_parser", NATIVE_FIRST / "run-native.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native_summary = json.loads((NATIVE_GOOD / "summary.json").read_text())
    declarations = [row["original_source_declaration"] for row in native_summary["case_evidence"]]
    observation = module.original_observations((output / "original-stdout.log").read_text(), declarations)
    receipt["original_stdout_observations"] = observation
    checks = {
        "runtime_initialized": state.get("runtimeInitialized") is True,
        "original_command_observed_at_runtime_exit": state.get("actualArgvAtRuntimeExit") == receipt.get("command"),
        "original_cwd_observed_before_main": state.get("actualCwdBeforeMain") == receipt.get("cwd") and bool(receipt.get("cwd")),
        "oracle_update_and_verbose_keys_absent": state.get("forbiddenEnvironmentKeysAbsent") is True,
        "environment_matches_declared": state.get("preMainEnvironment") == receipt.get("browser_environment") and bool(receipt.get("browser_environment")),
        "pre_main_original_bytes_verified": len(state.get("mountedFilesBeforeMain", [])) == 3 and all(
            row.get("byte_for_byte_equal_to_verified_input") is True for row in state.get("mountedFilesBeforeMain", [])),
        "exit_original_bytes_verified": len(state.get("mountedFilesAtRuntimeExit", [])) == 3 and all(
            row.get("byte_for_byte_equal_to_verified_input") is True for row in state.get("mountedFilesAtRuntimeExit", [])),
        "automatic_main_only": state.get("automaticMain") is True and state.get("manualMainCalls") == 0,
        "exactly_one_successful_runtime_exit": state.get("runtimeExitCodes") == [0],
        "no_runtime_abort_or_launcher_error": not state.get("aborts") and not state.get("errors") and bool(state),
        "no_host_or_page_errors": not receipt["errors"] and not receipt["page_errors"] and not receipt["browser_crashed"],
        "no_failed_requests": not receipt["failed_requests"],
        "no_timeout": receipt["timed_out"] is False,
        "chrome_process_exited_successfully": receipt.get("actual_chrome_process_returncode") == 0 and not receipt.get("chrome_forced_termination"),
        "console_stream_complete": receipt["event_stream_matches_browser_state"],
        "capture_inputs_unchanged": receipt["capture_inputs_unchanged"],
        "original_host_inputs_unchanged": receipt["original_host_inputs_unchanged"],
        "all_native_runtime_names_observed_once": not observation["missing_declared_names"] and not observation["unexpected_names"] and not observation["duplicate_names"],
        "all_original_mesh_oracles_passed": observation["observed_passes"] == len(native_summary["case_evidence"]) and not observation["observed_failures"] and not observation["observed_ambiguous_or_incomplete"],
    }
    receipt["qualification_checks"] = checks
    receipt["qualified_original_invocation"] = all(checks.values())
    receipt["qualified_original_browser_passes"] = observation["observed_passes"] if all(checks.values()) else 0
    receipt["status"] = "passed" if all(checks.values()) else "failed_or_blocked"
    native_by_name = {row["name"]: row for row in native_summary["case_evidence"]}
    receipt["native_browser_case_reconciliation"] = [{
        "name": row["name"], "native_status": native_by_name.get(row["name"], {}).get("status"),
        "browser_observed_status": row["status"], "source_declaration": row.get("original_source_declaration"),
        "qualified_browser_status": row["status"] if all(checks.values()) else "invocation_not_qualified",
    } for row in observation["observations"]]
    receipt["completed_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["elapsed_seconds"] = round(time.monotonic() - began, 6)
    receipt["raw_evidence"] = [identity(path) for path in sorted(output.iterdir()) if path.is_file()]
    write_new(output / "execution.json", receipt)
    print(json.dumps({"status": receipt["status"], "receipt": identity(output / "execution.json"),
                      "runtime_exit_codes": state.get("runtimeExitCodes"),
                      "observed_starts": observation["observed_starts"], "observed_passes": observation["observed_passes"],
                      "observed_failures": observation["observed_failures"],
                      "qualified_original_browser_passes": receipt["qualified_original_browser_passes"],
                      "failed_checks": [key for key, value in checks.items() if not value]}), flush=True)
    return 0 if receipt["qualified_original_invocation"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    raise SystemExit(run(args.output.resolve(), args.timeout_seconds))
