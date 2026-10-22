#!/usr/bin/env python3
"""Qualify a pinned Blender browser artifact using unchanged upstream tests.

This is a local browser qualification requesting a software GPU, not native-oracle,
hardware, deployed, or full Blender parity evidence. The observed adapter is
recorded separately. All failures still produce qualification.json.
Requires Playwright and a Chromium installation. No paid service is used.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.server
import json
from pathlib import Path, PurePosixPath
import secrets
import shutil
import socketserver
import tarfile
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request

UPSTREAM_SHA = "fbe6228777e7d9afefcd61a413844e790ae75db7"
PORT_SOURCE_SHA = "cc22090b88da63cc617d48b218f4945175928844"
ASSET_URL = "https://github.com/gessa-ai/blender-web/releases/download/v0.1.1/blender-web-local-v0.1.1.tar.gz"
ASSET_SHA256 = "1af405cd00d3471e105a39dad24a628aeb988f77b372c4c21bbf85ccbdca2ee0"
ASSET_BYTES = 108802132
SUITES = {
    "bl_pyapi_mathutils.py": "c5e252adc5fc80590faca2c667ba81d0ff732f682e1d866f1d4a0050b21a99af",
    "bl_pyapi_bmesh.py": "7dd9b28372ca371420c98e11bed49aff07f4fbe008c0fc1685cb9b5bc6721329",
}
SUITE_BYTES = {"bl_pyapi_mathutils.py": 41853, "bl_pyapi_bmesh.py": 32918}


class Blocked(RuntimeError):
    """Required execution infrastructure or provenance is unavailable."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def adapter_profile(adapter):
    """Classify observed fallback/software evidence without certifying hardware."""
    if not adapter:
        return "chromium-webgpu-unavailable"
    description = " ".join(str(adapter.get(key, "")) for key in
                           ("vendor", "architecture", "device", "description")).lower()
    if adapter.get("isFallbackAdapter") is True or any(
            name in description for name in ("swiftshader", "llvmpipe", "lavapipe", "software")):
        return "chromium-software-webgpu"
    return "chromium-webgpu-unverified"


def validate_build_identity(identity):
    """Unknown native reference identity cannot qualify an artifact as passing."""
    if identity.get("version") != [5, 2, 0]:
        raise Blocked("engine version differs from the pinned Blender 5.2.0 candidate")
    observed = str(identity.get("build_hash", "")).strip().lower()
    if observed in ("", "unknown", "none"):
        raise Blocked("engine build hash unavailable; executed suites do not establish reference provenance")
    if observed not in (UPSTREAM_SHA, UPSTREAM_SHA[:12]):
        raise Blocked("engine build hash differs from the candidate's pinned upstream reference: " + observed)


def validate_suite_execution(result, expected_sources):
    """Require complete top-level outcomes; subtests never inflate testsRun."""
    if result.get("exception"):
        raise RuntimeError("Python runner raised: " + result["exception"])
    rows = result.get("suites", [])
    if not expected_sources or len(rows) != len(expected_sources):
        raise RuntimeError("not every requested suite executed")
    for row, expected in zip(rows, expected_sources):
        if row["upstream_path"] != expected["upstream_path"] or row["sha256"] != expected["sha256"]:
            raise RuntimeError("suite identity changed during browser execution")
        ids = row["discovered_ids"]
        if (row["testsRun"] <= 0 or row["testsRun"] != row["discovered"] or
                row["discovered"] != len(ids) or len(set(ids)) != len(ids)):
            raise RuntimeError("suite ran zero tests or omitted/duplicated discovered tests")
        if any(row[key] for key in ("failures", "errors", "skipped", "expected_failures", "unexpected_successes")):
            raise RuntimeError("upstream suite is not completely passing: " + row["upstream_path"])
        top_level = [outcome for outcome in row["outcomes"] if outcome.get("kind") == "test"]
        if (len(top_level) != len(ids) or {outcome["id"] for outcome in top_level} != set(ids) or
                any(outcome["status"] != "passed" for outcome in row["outcomes"])):
            raise RuntimeError("complete passing outcomes were not recorded for every discovered test")


def summarize_execution(result, expected_sources, browser_errors=()):
    """Collect every suite failure and provenance blocker without double counts.

    A failing subtest and a later failure in its enclosing test are separate
    failure events but exactly one failed discovered test. A successful parent
    outcome is required to count a test as passed.
    """
    keys = ("discovered", "executed", "passed", "failed", "skipped",
            "expected_failures", "missing_outcomes", "failure_events", "subtest_events")
    totals = {key: 0 for key in keys}
    blockers, summaries = [], []
    rows = result.get("suites", [])
    expected_by_path = {entry["upstream_path"]: entry for entry in expected_sources}
    observed_paths = [row.get("upstream_path") for row in rows]
    if (not expected_sources or len(rows) != len(expected_sources) or
            len(set(observed_paths)) != len(observed_paths) or
            set(observed_paths) != set(expected_by_path)):
        blockers.append({"scope": "suite_inventory", "status": "failed",
                         "reason": "not every requested suite executed exactly once"})
    if result.get("exception"):
        blockers.append({"scope": "runner", "status": "failed", "reason": result["exception"]})
    for row in rows:
        path = row.get("upstream_path")
        counts = {key: 0 for key in keys}
        ids = list(dict.fromkeys(row.get("discovered_ids", [])))
        outcomes = row.get("outcomes", [])
        counts["discovered"], counts["executed"] = len(ids), row.get("testsRun", 0)
        counts["subtest_events"] = sum(item.get("kind") == "subtest" for item in outcomes)
        failure_events = [item for item in outcomes if item.get("status") in {"failed", "error", "unexpected_success"}]
        counts["failure_events"] = len(failure_events)
        for case_id in ids:
            related = [item for item in outcomes if item.get("id") == case_id or
                       (item.get("kind") == "subtest" and item.get("parent_id") == case_id)]
            statuses = {item.get("status") for item in related}
            if statuses & {"failed", "error", "unexpected_success"}:
                counts["failed"] += 1
            elif "skipped" in statuses:
                counts["skipped"] += 1
            elif "expected_failure" in statuses:
                counts["expected_failures"] += 1
            elif statuses == {"passed"} and any(item.get("kind") == "test" and
                                               item.get("id") == case_id for item in related):
                counts["passed"] += 1
            else:
                counts["missing_outcomes"] += 1
        suite_status = "passed"
        try:
            validate_suite_execution({"suites": [row], "exception": None},
                                     [expected_by_path[path]] if path in expected_by_path else [])
        except (RuntimeError, KeyError, TypeError, ValueError) as error:
            suite_status = "failed"
            blockers.append({"scope": "suite", "suite": path, "status": "failed", "reason": str(error)})
        summaries.append({"upstream_path": path, "status": suite_status, "counts": counts,
                          "failure_events": [{key: item.get(key) for key in ("id", "parent_id", "kind", "status")}
                                             for item in failure_events]})
        for key in keys:
            totals[key] += counts[key]
    suites_passed = not blockers
    identity = result.get("identity", {})
    hash_verified = str(identity.get("build_hash", "")).strip().lower() in (UPSTREAM_SHA, UPSTREAM_SHA[:12])
    try:
        validate_build_identity(identity)
    except Blocked as error:
        blockers.append({"scope": "provenance", "status": "blocked", "reason": str(error)})
    for error in browser_errors:
        blockers.append({"scope": "browser_runtime", "status": "failed", "reason": str(error)})
    status = ("failed" if any(b["status"] == "failed" for b in blockers) else
              "blocked" if blockers else "passed")
    return {"status": status, "selected_suites_passed": suites_passed,
            "upstream_build_hash_verified": hash_verified,
            "summary": {"expected_suites": len(expected_sources), "observed_suites": len(rows),
                        "totals": totals, "suites": summaries}, "blockers": blockers}


def download(url, destination, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "Blended-port-qualification/1"})
    size = 0
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as output:
        while data := response.read(1024 * 1024):
            size += len(data)
            if size > limit:
                raise Blocked("download exceeds declared byte bound: " + url)
            output.write(data)


def extract_asset(archive, directory):
    """Extract only confined regular files/directories from the verified archive."""
    with tarfile.open(archive, "r:gz") as package:
        members = package.getmembers()
        total = 0
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or "\\" in member.name:
                raise Blocked("unsafe archive path: " + member.name)
            if not (member.isdir() or member.isfile()):
                raise Blocked("unsupported archive link/special file: " + member.name)
            total += member.size
            if total > 2_000_000_000:
                raise Blocked("unpacked archive exceeds 2 GB qualification limit")
        package.extractall(directory, members=members, filter="data")


def python_payload(suites, marker):
    """Transport and execute whole source files without changing assertions."""
    encoded = [{**row, "source_b64": base64.b64encode(data).decode("ascii")}
               for row, data in suites]
    # The adapter loads the upstream module and uses its unittest loader. Only
    # the entry point is adapted; every discovered test and subtest is retained.
    return r'''
import base64, hashlib, json, sys, traceback, types, unittest
_blended_suites = json.loads(PAYLOAD_JSON)
_blended_marker = MARKER_JSON
_blended_report = {"suites": [], "identity": {}, "exception": None}
try:
    import bpy
    def _blended_text(value):
        return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
    _blended_report["identity"] = {
        "version": list(bpy.app.version),
        "version_string": bpy.app.version_string,
        "build_hash": _blended_text(bpy.app.build_hash),
        "build_branch": _blended_text(bpy.app.build_branch),
        "binary_path": bpy.app.binary_path,
    }
    class _BlendedResult(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.case_outcomes = []
        def _record(self, test, status, detail=None, kind="test", parent_id=None):
            self.case_outcomes.append({"id": test.id(), "kind": kind, "parent_id": parent_id,
                                       "status": status, "detail": detail})
        def addSuccess(self, test):
            super().addSuccess(test); self._record(test, "passed")
        def addFailure(self, test, err):
            super().addFailure(test, err); self._record(test, "failed", self._exc_info_to_string(err, test))
        def addError(self, test, err):
            super().addError(test, err); self._record(test, "error", self._exc_info_to_string(err, test))
        def addSkip(self, test, reason):
            super().addSkip(test, reason); self._record(test, "skipped", reason)
        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err); self._record(test, "expected_failure", self._exc_info_to_string(err, test))
        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test); self._record(test, "unexpected_success")
        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            self._record(subtest, "passed" if err is None else "failed",
                         None if err is None else self._exc_info_to_string(err, test),
                         kind="subtest", parent_id=test.id())
    def _blended_ids(suite):
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                yield from _blended_ids(test)
            else:
                yield test.id()
    for _blended_index, _blended_row in enumerate(_blended_suites):
        _blended_data = base64.b64decode(_blended_row["source_b64"])
        if hashlib.sha256(_blended_data).hexdigest() != _blended_row["sha256"]:
            raise RuntimeError("suite changed in transport")
        _blended_name = "blended_upstream_" + str(_blended_index)
        _blended_module = types.ModuleType(_blended_name)
        _blended_module.__file__ = "/" + _blended_row["upstream_path"]
        sys.modules[_blended_name] = _blended_module
        sys.argv = [_blended_module.__file__]
        exec(compile(_blended_data, _blended_module.__file__, "exec"), _blended_module.__dict__)
        _blended_suite = unittest.defaultTestLoader.loadTestsFromModule(_blended_module)
        _blended_expected = list(_blended_ids(_blended_suite))
        _blended_result = unittest.TextTestRunner(verbosity=2, resultclass=_BlendedResult).run(_blended_suite)
        _blended_report["suites"].append({
            "upstream_path": _blended_row["upstream_path"], "sha256": _blended_row["sha256"],
            "discovered_ids": _blended_expected, "discovered": len(_blended_expected),
            "testsRun": _blended_result.testsRun,
            "failures": len(_blended_result.failures), "errors": len(_blended_result.errors),
            "skipped": len(_blended_result.skipped),
            "expected_failures": len(_blended_result.expectedFailures),
            "unexpected_successes": len(_blended_result.unexpectedSuccesses),
            "outcomes": _blended_result.case_outcomes,
        })
except BaseException:
    _blended_report["exception"] = traceback.format_exc()
finally:
    print(_blended_marker + json.dumps(_blended_report, sort_keys=True), flush=True)
'''.replace("PAYLOAD_JSON", repr(json.dumps(encoded))).replace("MARKER_JSON", repr(marker))


def serve(shell, binary, entry, output):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          ".wasm": "application/wasm", ".js": "text/javascript",
                          ".data": "application/octet-stream"}

        def translate_path(self, path):
            rel = urllib.parse.unquote(urllib.parse.urlsplit(path).path)
            root = binary if rel.startswith("/bin/") else shell
            rel = rel[5:] if rel.startswith("/bin/") else rel.lstrip("/")
            if not rel:
                rel = entry
            resolved = (root / rel).resolve()
            if not resolved.is_relative_to(root.resolve()):
                return str(shell / "__blocked_path__")
            return str(resolved)

        def end_headers(self):
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, fmt, *args):
            with (output / "http.log").open("a", encoding="utf-8") as log:
                log.write((fmt % args) + "\n")

    class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    server = Server(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def probe(args, report):
    output = args.output.resolve()
    with tempfile.TemporaryDirectory(prefix="blended-port-probe-") as temporary:
        work = Path(temporary)
        archive = args.asset.resolve() if args.asset else work / "candidate.tar.gz"
        if args.asset is None:
            download(ASSET_URL, archive, ASSET_BYTES)
        if not archive.is_file():
            raise Blocked("candidate archive is missing")
        measured_digest = digest(archive)
        report["artifact"]["observed_sha256"] = measured_digest
        report["artifact"]["observed_bytes"] = archive.stat().st_size
        if measured_digest != ASSET_SHA256 or archive.stat().st_size != ASSET_BYTES:
            raise Blocked("candidate artifact does not match the pinned release asset")

        suites = []
        paths = args.suite or [work / name for name in SUITES]
        seen = set()
        for path in paths:
            name = path.name
            if name not in SUITES or name in seen:
                raise Blocked("unknown or duplicate pinned suite: " + name)
            seen.add(name)
            upstream_path = "tests/python/" + name
            url = "https://raw.githubusercontent.com/blender/blender/" + UPSTREAM_SHA + "/" + upstream_path
            if not args.suite:
                download(url, path, 1_000_000)
            if not path.is_file():
                raise Blocked("suite file missing: " + str(path))
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != SUITES[name] or len(data) != SUITE_BYTES[name]:
                raise Blocked("suite bytes differ from the immutable upstream source: " + name)
            row = {"upstream_path": upstream_path, "sha256": SUITES[name], "bytes": len(data), "url": url}
            suites.append((row, data))
        report["suite_sources"] = [row for row, _ in suites]

        unpacked = work / "unpacked"
        unpacked.mkdir()
        extract_asset(archive, unpacked)
        boots = list(unpacked.rglob("boot-windowed.js"))
        engines = list(unpacked.rglob("blender_browser.js"))
        if len(boots) != 1 or len(engines) != 1:
            raise Blocked("release layout has no unambiguous windowed shell and Blender engine")
        shell, binary = boots[0].parent, engines[0].parent
        entry = "windowed.html" if (shell / "windowed.html").is_file() else "index.html"
        if not (shell / entry).is_file():
            raise Blocked("release contains no windowed entry page")
        report["engine_files"] = [{"path": str(p.relative_to(unpacked)), "sha256": digest(p),
                                    "bytes": p.stat().st_size}
                                   for p in sorted(binary.iterdir()) if p.is_file()]
        report["shell"] = {"entry": entry, "boot_sha256": digest(boots[0]), "modified": False}
        server = serve(shell, binary, entry, output)
        report["url"] = "http://127.0.0.1:" + str(server.server_port) + "/"
        marker = "BLENDED_QUALIFICATION_" + secrets.token_hex(12) + ":"
        received = []
        browser_errors = []
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            server.shutdown()
            raise Blocked("Playwright is not installed") from error
        try:
            with sync_playwright() as playwright:
                flags = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-watchdog",
                         "--enable-unsafe-webgpu", "--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
                executable = args.browser_executable or shutil.which("google-chrome")
                launch = {"headless": True, "args": flags}
                if executable:
                    launch["executable_path"] = executable
                try:
                    browser = playwright.chromium.launch(**launch)
                except Exception as error:
                    raise Blocked("Chromium could not start: " + str(error)) from error
                report["browser"] = {"version": browser.version, "flags": flags}
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()

                def console(message):
                    text = message.text
                    with (output / "browser.log").open("a", encoding="utf-8") as log:
                        log.write(message.type + " " + text + "\n")
                    if text.startswith(marker):
                        try:
                            received.append(json.loads(text[len(marker):]))
                        except ValueError:
                            browser_errors.append("invalid qualification marker JSON")

                page.on("console", console)
                page.on("pageerror", lambda error: browser_errors.append(str(error)))
                page.on("crash", lambda: browser_errors.append("browser page crashed"))
                code = python_payload(suites, marker)
                page.add_init_script("window.__BW_PYEXPR = " + json.dumps(code) + ";")
                response = page.goto(report["url"], wait_until="domcontentloaded", timeout=60000)
                if response is None or response.status != 200:
                    raise Blocked("local candidate page did not return HTTP 200")
                capability = page.evaluate("""async () => {
                    const adapter = navigator.gpu ? await navigator.gpu.requestAdapter() : null;
                    return {crossOriginIsolated, sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
                        webgpu: !!navigator.gpu, adapter: adapter ? {
                            vendor: adapter.info?.vendor ?? null,
                            architecture: adapter.info?.architecture ?? null,
                            device: adapter.info?.device ?? null,
                            description: adapter.info?.description ?? null,
                            isFallbackAdapter: adapter.info?.isFallbackAdapter ?? adapter.isFallbackAdapter ?? null,
                            features: Array.from(adapter.features)
                        } : null};
                }""")
                report["capabilities"] = capability
                report["profile"] = adapter_profile(capability["adapter"])
                report["adapter_measurement_scope"] = (
                    "Independent navigator.gpu.requestAdapter probe; engine-selected adapter is not instrumented.")
                if not capability["crossOriginIsolated"] or not capability["sharedArrayBuffer"]:
                    raise Blocked("cross-origin isolation or SharedArrayBuffer unavailable")
                if not capability["adapter"]:
                    raise Blocked("WebGPU adapter unavailable")
                deadline = time.monotonic() + args.timeout
                while not received and time.monotonic() < deadline:
                    if browser_errors:
                        raise RuntimeError("browser runtime error: " + browser_errors[0])
                    if page.evaluate("window.__bwDevHooksAllowed === false"):
                        raise Blocked("artifact disables the Python test hook; unchanged release was preserved")
                    page.wait_for_timeout(250)
                report["browser_errors"] = browser_errors
                try:
                    page.screenshot(path=str(output / "candidate.png"))
                except Exception as error:
                    report["screenshot_error"] = str(error)
                if not received:
                    raise Blocked("timed out waiting for executed upstream tests; no pass inferred from boot")
                if len(received) != 1:
                    raise RuntimeError("duplicate qualification result markers")
                result = received[0]
                report["execution"] = result
                report.update(summarize_execution(result, report["suite_sources"], browser_errors))
                report["identity_limit"] = next((b["reason"] for b in report["blockers"]
                                                 if b["scope"] == "provenance"), None)
                report["reason"] = (
                    "Whole selected upstream unittest files passed on the pinned artifact in a local browser; "
                    "reported upstream build identity matched. Observed probe profile: " + report["profile"] + "."
                    if report["status"] == "passed" else
                    "; ".join(b["scope"] + ": " + b["reason"] for b in report["blockers"]))
                browser.close()
        finally:
            report["browser_errors"] = browser_errors
            server.shutdown()
            server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, help="Already-downloaded pinned v0.1.1 archive")
    parser.add_argument("--suite", action="append", type=Path, help="Exact pinned mathutils/bmesh test file; repeatable")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser-executable")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": 1, "status": "blocked", "started_utc": now(), "finished_utc": None,
        "scope": "selected upstream Python suite qualification only",
        "profile": "chromium-webgpu-unclassified", "deployed": False,
        "hardware_verified": False, "native_oracle_compared": False, "full_parity": False,
        "selected_suites_passed": False,
        "summary": None, "blockers": [],
        "source_correspondence_verified": False,
        "candidate": {"repository": "gessa-ai/blender-web", "tag": "v0.1.1", "source_commit": PORT_SOURCE_SHA},
        "upstream": {"repository": "blender/blender", "commit": UPSTREAM_SHA},
        "artifact": {"url": ASSET_URL, "expected_sha256": ASSET_SHA256, "expected_bytes": ASSET_BYTES},
        "suite_sources": [], "browser_errors": [], "execution": None,
    }
    try:
        if args.timeout <= 0 or args.timeout > 600:
            raise Blocked("timeout must be between 1 and 600 seconds")
        probe(args, report)
    except Blocked as error:
        report["status"], report["reason"] = "blocked", str(error)
        report["blockers"].append({"scope": "infrastructure", "status": "blocked", "reason": str(error)})
    except Exception as error:
        report["status"], report["reason"] = "failed", str(error)
        report["blockers"].append({"scope": "infrastructure", "status": "failed", "reason": str(error)})
        report["traceback"] = traceback.format_exc()
    finally:
        report["finished_utc"] = now()
        (args.output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "reason": report.get("reason"),
                          "evidence": str(args.output / "qualification.json")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
