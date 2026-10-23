#!/usr/bin/env python3
"""Run the exact compiled SQLite diagnostic in Chrome and retain raw events."""
import asyncio
from datetime import datetime, timezone
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

from playwright.async_api import async_playwright


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


async def main():
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    chrome = repo.parent / "runtime/chrome/chrome-linux64/chrome"
    output = evidence / "sqlite-component-browser"
    output.mkdir(exist_ok=False)
    html = output / "index.html"
    html.write_text('''<!doctype html><meta charset="utf-8"><title>SQLite component diagnostic</title>
<script>
var Module = {
  print: function (message) { console.log(message); },
  printErr: function (message) { console.error(message); },
  onExit: function (code) { window.sqliteProbeExit = code; },
  onAbort: function (reason) { window.sqliteProbeAbort = String(reason); }
};
</script><script src="../sqlite-component-node/probe.js"></script>\n''')
    request_events = []

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            request_events.append({"message": format % args})

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(evidence)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = "http://127.0.0.1:" + str(server.server_port) + "/sqlite-component-browser/index.html"
    report = {"schema": 1, "kind": "sqlite-wasm-component-browser-diagnostic",
              "started_utc": datetime.now(timezone.utc).isoformat(), "url": url,
              "capture_driver": identity(Path(__file__).resolve()), "chrome": identity(chrome),
              "input_files": [identity(path) for path in (html, evidence / "sqlite-component-node/probe.js",
                                                          evidence / "sqlite-component-node/probe.wasm")],
              "launch_arguments": ["--no-sandbox", "--disable-dev-shm-usage"],
              "console_events": [], "page_errors": [], "original_blender_tests_executed": False,
              "full_feature_parity": False}
    started = time.monotonic()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(executable_path=str(chrome), args=report["launch_arguments"], headless=True)
            report["browser_version"] = browser.version
            page = await browser.new_page()
            page.on("console", lambda event: report["console_events"].append({"type": event.type, "text": event.text}))
            page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
            await page.goto(url)
            await page.wait_for_function("window.sqliteProbeExit !== undefined || window.sqliteProbeAbort !== undefined", timeout=90000)
            report["runtime_exit"] = await page.evaluate("window.sqliteProbeExit === undefined ? null : window.sqliteProbeExit")
            report["runtime_abort"] = await page.evaluate("window.sqliteProbeAbort === undefined ? null : window.sqliteProbeAbort")
            await browser.close()
    except Exception as error:
        report["harness_error"] = type(error).__name__ + ": " + str(error)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    records = []
    for event in report["console_events"]:
        try:
            value = json.loads(event["text"])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("kind") == "sqlite-wasm-component-diagnostic":
            records.append(value)
    report["component_observations"] = records
    report["completed_successfully"] = (report.get("runtime_exit") == 0 and report.get("runtime_abort") is None
                                         and not report["page_errors"] and len(records) == 1)
    report["request_events"] = request_events
    report["elapsed_seconds"] = round(time.monotonic() - started, 6)
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["completed_successfully"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
