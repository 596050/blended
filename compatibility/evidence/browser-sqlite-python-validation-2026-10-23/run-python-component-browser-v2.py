#!/usr/bin/env python3
"""Capture original-module attempts or a separately identified binding diagnostic."""
import argparse
import asyncio
from datetime import datetime, timezone
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

from playwright.async_api import async_playwright


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


async def run(args):
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    artifact = args.artifact_root.resolve()
    build_path = artifact / "build.json"
    build = json.loads(build_path.read_text())
    expected_kind = ("standalone-wasm-cpython-sqlite-build" if args.mode == "original-module"
                     else "standalone-wasm-cpython-sqlite-diagnostic-build")
    if build["kind"] != expected_kind or not build["completed_successfully"]:
        raise ValueError("component build identity does not match the requested diagnostic scope")
    for entry in build["artifacts"]:
        actual = identity(artifact / Path(entry["path"]).name)
        if any(actual[key] != entry[key] for key in ("bytes", "sha256")):
            raise ValueError("component artifact changed before browser execution")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    html = output / "index.html"
    html.write_text('''<!doctype html><meta charset="utf-8"><title>CPython SQLite component</title>
<script>
var Module = {
  print: function (message) { console.log(message); },
  printErr: function (message) { console.error(message); },
  onExit: function (code) { window.componentExit = code; },
  onAbort: function (reason) { window.componentAbort = String(reason); }
};
</script><script src="python-sqlite.js"></script>\n''')
    request_events = []

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if urlsplit(self.path).path == "/index.html":
                data = html.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                super().do_GET()

        def end_headers(self):
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            super().end_headers()

        def log_message(self, format, *args):
            request_events.append({"message": format % args})

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(artifact)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    chrome = repo.parent / "runtime/chrome/chrome-linux64/chrome"
    url = "http://127.0.0.1:" + str(server.server_port) + "/index.html"
    helper = evidence / "component-results.py"
    report = {"schema": 1, "kind": "standalone-wasm-cpython-browser-" + args.mode,
              "started_utc": datetime.now(timezone.utc).isoformat(), "url": url,
              "capture_driver": identity(Path(__file__).resolve()), "chrome": identity(chrome),
              "build_receipt": identity(build_path), "artifact_inputs": build["artifacts"],
              "html": identity(html), "launch_arguments": ["--no-sandbox", "--disable-dev-shm-usage"],
              "console_events": [], "page_errors": [], "original_blender_invocation_executed": False,
              "strict_blender_browser_test_passes": 0, "full_feature_parity": False}
    started = time.monotonic()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(executable_path=str(chrome), args=report["launch_arguments"], headless=True)
            report["browser_version"] = browser.version
            page = await browser.new_page()
            page.on("console", lambda event: report["console_events"].append({"type": event.type, "text": event.text}))
            page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
            await page.goto(url)
            await page.wait_for_function("window.componentExit !== undefined || window.componentAbort !== undefined", timeout=120000)
            report["runtime_exit"] = await page.evaluate("window.componentExit === undefined ? null : window.componentExit")
            report["runtime_abort"] = await page.evaluate("window.componentAbort === undefined ? null : window.componentAbort")
            report["cross_origin_isolated"] = await page.evaluate("crossOriginIsolated")
            await browser.close()
    except Exception as error:
        report["harness_error"] = type(error).__name__ + ": " + str(error)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    text = "\n".join(event["text"] for event in report["console_events"])
    (output / "browser.log").write_text(text + "\n")
    report["browser_log"] = identity(output / "browser.log")
    if args.mode == "original-module":
        spec = importlib.util.spec_from_file_location("component_results", helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report["output_parser"] = identity(helper)
        report["case_reconciliation"] = module.reconcile_output(text, build["expected_case_ids"], report.get("runtime_exit"))
        successful_observation = report["case_reconciliation"]["complete_original_module_pass_in_component"]
    else:
        marker = "BLENDED_SQLITE_PYTHON_DIAGNOSTIC "
        observations = [json.loads(line[len(marker):]) for line in text.splitlines() if line.startswith(marker)]
        report["component_observations"] = observations
        required = ("actual_builtin_extension", "wal_dual_connection", "parameter_binding_text_integer_float",
                    "utf8_file_hash", "upsert_returning", "rollback", "python_function_and_trace_callbacks",
                    "row_factory", "backup_and_serialization", "foreign_key_cascade", "close_reopen_same_filesystem",
                    "integrity_check")
        successful_observation = (len(observations) == 1 and observations[0].get("kind") == "cpython-sqlite-component-diagnostic"
                                  and all(observations[0].get(key) is True for key in required)
                                  and observations[0].get("sqlite_version") == "3.51.3"
                                  and observations[0].get("python_version") == [3, 13, 13]
                                  and observations[0].get("diagnostic_version") == 2
                                  and observations[0].get("wal_deserialization_expected_error") == {
                                      "type": "OperationalError", "code": 14, "name": "SQLITE_CANTOPEN",
                                      "message": "unable to open database file"})
    report["completed_successfully"] = (type(report.get("runtime_exit")) is int and report["runtime_exit"] == 0
                                         and report.get("runtime_abort") is None and not report["page_errors"]
                                         and successful_observation)
    report["request_events"] = request_events
    report["elapsed_seconds"] = round(time.monotonic() - started, 6)
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["completed_successfully"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("original-module", "binding-diagnostic"), required=True)
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
