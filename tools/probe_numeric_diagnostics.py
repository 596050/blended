#!/usr/bin/env python3
"""Run or compare non-acceptance numerical diagnostics on pinned Blender builds.

The payload is transported unchanged to both engines. Completed diagnostics do
not count as passing Blender tests. Unknown build identity remains blocked even
when numerical observations can be paired and inspected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import traceback

try:
    from . import probe_browser_port as browser_probe
    from . import probe_native_reference as native_probe
except ImportError:
    import probe_browser_port as browser_probe
    import probe_native_reference as native_probe

Blocked = browser_probe.Blocked
MARKER = "BLENDED_NUMERIC_DIAGNOSTICS:"
SECTIONS = ("vector_cases", "screw_cases")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def decode_marker_lines(lines):
    """Decode one complete object while retaining non-JSON runtime suffixes.

    The browser shell can concatenate a GPU log message after Python's final
    closing brace. Its complete observations remain useful, but that suffix
    must remain a blocker. Truncation and multiple results are never recovered.
    """
    records = [line[len(MARKER):] for line in lines if line.startswith(MARKER)]
    if len(records) != 1:
        raise Blocked("expected exactly one complete numerical diagnostic result marker")
    if MARKER in records[0]:
        raise Blocked("duplicate numerical diagnostic result marker in one console event")
    try:
        decoder = json.JSONDecoder()
        result, end = decoder.raw_decode(records[0].lstrip())
        canonical(result)
    except (ValueError, TypeError) as error:
        raise Blocked("numeric diagnostic result marker contains invalid or incomplete JSON") from error
    if not isinstance(result, dict) or result.get("schema") != 1 or result.get("diagnostic_only") is not True:
        raise Blocked("result is not a schema-1 non-acceptance diagnostic object")
    suffix = records[0].lstrip()[end:]
    if suffix.strip():
        try:
            decoder.raw_decode(suffix.lstrip())
        except ValueError:
            pass
        else:
            raise Blocked("extra JSON value after numerical diagnostic result")
    else:
        suffix = ""
    return result, suffix


def parse_marker_lines(lines):
    """Strict parser for consumers that cannot retain transport blockers."""
    result, suffix = decode_marker_lines(lines)
    if suffix:
        raise Blocked("runtime text followed the complete numerical diagnostic JSON")
    return result


def capture_execution(lines, report):
    result, suffix = decode_marker_lines(lines)
    report["execution"] = result
    report["transport"] = {"protocol": "marker-prefixed-json-v1", "result_markers": 1,
                           "recovered_json_prefix": bool(suffix), "trailing_runtime_text": suffix or None}
    if suffix:
        report["blockers"].append({"scope": "transport", "reason": "runtime text followed complete diagnostic JSON",
                                   "trailing_runtime_text": suffix})
    return result


def assess_execution(result):
    if not isinstance(result, dict) or result.get("schema") != 1 or result.get("diagnostic_only") is not True:
        raise Blocked("diagnostic payload scope or schema changed")
    inputs = {}
    errors = list(result.get("errors", []))
    for section in SECTIONS:
        rows = result.get(section)
        expected = result.get("expected_counts", {}).get(section)
        if (not isinstance(rows, list) or not isinstance(expected, int) or
                isinstance(expected, bool) or expected <= 0 or len(rows) != expected):
            raise Blocked("diagnostic cases missing or count changed: " + section)
        if any(not isinstance(row, dict) for row in rows):
            raise Blocked("diagnostic cases are not structured objects: " + section)
        ids = [row.get("id") for row in rows]
        if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
            raise Blocked("diagnostic case IDs missing or duplicated: " + section)
        if any("inputs" not in row for row in rows):
            raise Blocked("diagnostic input identity missing: " + section)
        inputs[section] = sorted(({"id": row["id"], "inputs": row["inputs"]} for row in rows), key=lambda row: row["id"])
        for row in rows:
            if row.get("error") or row.get("errors"):
                errors.append({"section": section, "id": row["id"],
                               "error": row.get("error") or row.get("errors")})
    blockers = [{"scope": "diagnostic_execution", "reason": str(error)} for error in errors]
    verified = False
    try:
        browser_probe.validate_build_identity(result.get("identity", {}))
        verified = True
    except Blocked as error:
        blockers.append({"scope": "provenance", "reason": str(error)})
    return {"status": "blocked" if blockers else "completed",
            "diagnostics_complete": not errors,
            "upstream_build_hash_verified": verified,
            "input_manifest_sha256": hashlib.sha256(canonical(inputs).encode()).hexdigest(),
            "counters": {section: len(result[section]) for section in SECTIONS},
            "blockers": blockers}


def differences(native, browser, path=""):
    """Retain exact scalar values, including the payload's IEEE bit strings."""
    if type(native) is not type(browser):
        return [{"field": path, "native": native, "browser": browser}]
    if isinstance(native, dict):
        result = []
        for key in sorted(set(native) | set(browser)):
            field = path + "/" + str(key).replace("~", "~0").replace("/", "~1")
            if key not in native or key not in browser:
                result.append({"field": field, "native": native.get(key), "browser": browser.get(key),
                               "missing_from": "native" if key not in native else "browser"})
            else:
                result.extend(differences(native[key], browser[key], field))
        return result
    if isinstance(native, list):
        if len(native) != len(browser):
            return [{"field": path, "native_length": len(native), "browser_length": len(browser),
                     "unpaired": True}]
        return [difference for index, (a, b) in enumerate(zip(native, browser))
                for difference in differences(a, b, path + "/" + str(index))]
    return [] if native == browser else [{"field": path, "native": native, "browser": browser}]


def compare_reports(native, browser):
    report = {"schema": 1, "diagnostic_only": True, "acceptance_status": "not_evaluated",
              "full_parity": False, "status": "blocked", "pairing_complete": False,
              "diagnostics_complete": False, "upstream_build_hash_verified": False,
              "cases": [], "blockers": [],
              "counters": {"paired_cases": 0, "cases_with_differences": 0, "different_fields": 0}}
    try:
        payload_hash = native.get("payload", {}).get("sha256", "")
        if (not re.fullmatch(r"[0-9a-f]{64}", payload_hash) or
                browser.get("payload", {}).get("sha256") != payload_hash):
            raise Blocked("native and browser diagnostic payload hashes differ or are missing")
        report["payload_sha256"] = payload_hash
        assessments = {}
        for name, source, module in (("native", native, native_probe), ("browser", browser, browser_probe)):
            if (source.get("engine") != name or source.get("diagnostic_only") is not True or
                    source.get("upstream", {}).get("commit") != browser_probe.UPSTREAM_SHA):
                raise Blocked("diagnostic report engine, scope, or upstream identity differs: " + name)
            artifact = source.get("artifact", {})
            if artifact.get("observed_sha256") != module.ASSET_SHA256 or artifact.get("observed_bytes") != module.ASSET_BYTES:
                raise Blocked("diagnostic artifact differs from the pinned release: " + name)
            assessments[name] = assess_execution(source["execution"])
            for blocker in source.get("blockers", []) + assessments[name]["blockers"]:
                tagged = {"engine": name, **blocker}
                if tagged not in report["blockers"]:
                    report["blockers"].append(tagged)
        if assessments["native"]["input_manifest_sha256"] != assessments["browser"]["input_manifest_sha256"]:
            raise Blocked("native and browser case IDs or input parameters differ")
        report["input_manifest_sha256"] = assessments["native"]["input_manifest_sha256"]
        topology_paired = True
        for section in SECTIONS:
            browser_rows = {row["id"]: row for row in browser["execution"][section]}
            for row in native["execution"][section]:
                other = browser_rows[row["id"]]
                signature = row.get("topology_sha256", "")
                if section == "screw_cases" and (
                        not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{64}", signature) or
                        signature != other.get("topology_sha256")):
                    topology_paired = False
                    report["blockers"].append({"scope": "topology_pairing", "case_id": row["id"],
                                               "reason": "mesh topology signatures differ or are missing; index pairing refused"})
                    continue
                observed = differences({k: v for k, v in row.items() if k not in {"id", "inputs"}},
                                       {k: v for k, v in other.items() if k not in {"id", "inputs"}})
                report["cases"].append({"section": section, "id": row["id"], "inputs": row["inputs"],
                                        "different_fields": len(observed), "differences": observed})
                report["counters"]["paired_cases"] += 1
                report["counters"]["cases_with_differences"] += bool(observed)
                report["counters"]["different_fields"] += len(observed)
        report["pairing_complete"] = topology_paired
        report["diagnostics_complete"] = all(value["diagnostics_complete"] for value in assessments.values())
        report["upstream_build_hash_verified"] = all(value["upstream_build_hash_verified"] for value in assessments.values())
    except (Blocked, KeyError, TypeError, ValueError) as error:
        report["blockers"].append({"scope": "pairing", "reason": str(error)})
    report["status"] = "blocked" if report["blockers"] else "completed"
    return report


def verify_archive(args, work, report):
    module = native_probe if args.engine == "native" else browser_probe
    archive = args.asset.resolve() if args.asset else work / ("native.tar.xz" if args.engine == "native" else "browser.tar.gz")
    if not args.asset:
        browser_probe.download(module.ASSET_URL, archive, module.ASSET_BYTES)
    if not archive.is_file() or archive.stat().st_size != module.ASSET_BYTES:
        raise Blocked("diagnostic artifact missing or byte count differs from pinned release")
    report["artifact"]["observed_bytes"] = archive.stat().st_size
    report["artifact"]["observed_sha256"] = browser_probe.digest(archive)
    if report["artifact"]["observed_sha256"] != module.ASSET_SHA256:
        raise Blocked("diagnostic artifact checksum differs from pinned release")
    unpacked = work / "unpacked"
    unpacked.mkdir()
    if args.engine == "native":
        report["extraction"] = native_probe.extract_reference(archive, unpacked)
    else:
        browser_probe.extract_asset(archive, unpacked)
    return unpacked


def run_native(args, work, unpacked, payload, log_path, report):
    binary = (unpacked / native_probe.ARCHIVE_ROOT / "blender").resolve()
    if not binary.is_relative_to(unpacked.resolve()) or not binary.is_file():
        raise Blocked("native diagnostic executable is missing or escapes extracted archive")
    report["executable"] = {"path": str(binary.relative_to(unpacked)), "sha256": browser_probe.digest(binary)}
    runner = work / "diagnostics.py"
    runner.write_bytes(payload)
    flags = ["--background", "--factory-startup", "--threads", "1", "--python-exit-code", "1"]
    report["process"] = {"flags": flags, "timeout_seconds": args.timeout}
    with log_path.open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run([str(binary), *flags, "--python", str(runner)], cwd=work,
                                    stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout, check=False)
        except subprocess.TimeoutExpired as error:
            raise Blocked("native diagnostics exceeded execution timeout") from error
    report["process"]["returncode"] = result.returncode
    with log_path.open(encoding="utf-8", errors="replace") as log:
        execution = capture_execution(log, report)
    if result.returncode:
        report["blockers"].append({"scope": "native_runtime",
                                   "reason": "native diagnostic process exited with code " + str(result.returncode)})
    return execution


def run_browser(args, work, unpacked, payload, log_path, report):
    boots, engines = list(unpacked.rglob("boot-windowed.js")), list(unpacked.rglob("blender_browser.js"))
    if len(boots) != 1 or len(engines) != 1:
        raise Blocked("browser release layout has no unambiguous engine and shell")
    shell, binary = boots[0].parent, engines[0].parent
    entry = "windowed.html" if (shell / "windowed.html").is_file() else "index.html"
    if not (shell / entry).is_file():
        raise Blocked("browser release entry page missing")
    report["engine_files"] = [{"path": str(path.relative_to(unpacked)), "sha256": browser_probe.digest(path),
                                "bytes": path.stat().st_size} for path in sorted(binary.iterdir()) if path.is_file()]
    report["shell"] = {"entry": entry, "boot_sha256": browser_probe.digest(boots[0]), "modified": False}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise Blocked("Playwright is not installed") from error
    server = browser_probe.serve(shell, binary, entry, args.output.resolve())
    messages, runtime_errors = [], []
    try:
        with sync_playwright() as playwright:
            flags = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-watchdog",
                     "--enable-unsafe-webgpu", "--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
            launch = {"headless": True, "args": flags}
            executable = args.browser_executable or shutil.which("google-chrome")
            if executable:
                launch["executable_path"] = executable
            browser = playwright.chromium.launch(**launch)
            report["browser"] = {"version": browser.version, "flags": flags}
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            def console(message):
                value = message.text
                with log_path.open("a", encoding="utf-8") as log:
                    log.write(message.type + " " + value + "\n")
                if value.startswith(MARKER):
                    messages.append(value)

            page.on("console", console)
            page.on("pageerror", lambda error: runtime_errors.append(str(error)))
            page.on("crash", lambda: runtime_errors.append("browser page crashed"))
            page.add_init_script("window.__BW_PYEXPR = " + json.dumps(payload.decode("utf-8")) + ";")
            url = "http://127.0.0.1:" + str(server.server_port) + "/"
            response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if response is None or response.status != 200:
                raise Blocked("local diagnostic browser page did not return HTTP 200")
            capability = page.evaluate("""async () => {
                const adapter = navigator.gpu ? await navigator.gpu.requestAdapter() : null;
                return {crossOriginIsolated, sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
                    adapter: adapter ? {vendor: adapter.info?.vendor, architecture: adapter.info?.architecture,
                        device: adapter.info?.device, description: adapter.info?.description,
                        isFallbackAdapter: adapter.info?.isFallbackAdapter ?? adapter.isFallbackAdapter ?? null} : null};
            }""")
            report["capabilities"] = capability
            report["profile"] = browser_probe.adapter_profile(capability["adapter"])
            report["adapter_measurement_scope"] = "Independent navigator.gpu adapter probe; engine-selected adapter is not instrumented."
            if not capability["crossOriginIsolated"] or not capability["sharedArrayBuffer"] or not capability["adapter"]:
                raise Blocked("cross-origin isolation, SharedArrayBuffer, or WebGPU adapter unavailable")
            deadline = time.monotonic() + args.timeout
            while not messages and time.monotonic() < deadline:
                if runtime_errors:
                    raise Blocked("browser runtime error: " + runtime_errors[0])
                if page.evaluate("window.__bwDevHooksAllowed === false"):
                    raise Blocked("release disables Python diagnostic hook; unchanged artifact preserved")
                page.wait_for_timeout(250)
            execution = capture_execution(messages, report)
            for error in runtime_errors:
                report["blockers"].append({"scope": "browser_runtime", "reason": error})
            browser.close()
            return execution
    finally:
        report["browser_errors"] = runtime_errors
        server.shutdown()
        server.server_close()


def run(args):
    module = native_probe if args.engine == "native" else browser_probe
    args.output.mkdir(parents=True, exist_ok=True)
    stem = args.engine + "-numeric-diagnostics"
    log_path = args.output / (stem + ".log")
    log_path.write_text("", encoding="utf-8")
    report = {"schema": 1, "engine": args.engine, "diagnostic_only": True,
              "acceptance_status": "not_evaluated", "full_parity": False,
              "status": "blocked", "diagnostics_complete": False, "hardware_verified": False,
              "upstream_build_hash_verified": False, "source_correspondence_verified": False,
              "started_utc": browser_probe.now(), "execution": None, "blockers": [],
              "profile": "native-reference" if args.engine == "native" else "chromium-webgpu-unclassified",
              "upstream": {"repository": "blender/blender", "commit": browser_probe.UPSTREAM_SHA, "version": "5.2.0"},
              "transport_sources": [{"path": path.name, "sha256": browser_probe.digest(path)}
                                    for path in (Path(__file__), Path(browser_probe.__file__), Path(native_probe.__file__))],
              "artifact": {"url": module.ASSET_URL, "expected_sha256": module.ASSET_SHA256, "expected_bytes": module.ASSET_BYTES}}
    if args.engine == "browser":
        report["candidate"] = {"repository": "gessa-ai/blender-web", "tag": "v0.1.1",
                               "source_commit": browser_probe.PORT_SOURCE_SHA}
    try:
        if not 1 <= args.timeout <= 600:
            raise Blocked("execution timeout must be between 1 and 600 seconds")
        payload = args.payload.read_bytes()
        if not payload or len(payload) > 1_000_000:
            raise Blocked("diagnostic payload is empty or exceeds 1 MB")
        saved_payload = args.output / "numeric-diagnostic-payload.py"
        saved_payload.write_bytes(payload)
        report["payload"] = {"path": saved_payload.name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
        with tempfile.TemporaryDirectory(prefix="blended-numeric-" + args.engine + "-") as temporary:
            work = Path(temporary)
            unpacked = verify_archive(args, work, report)
            execution = (run_native if args.engine == "native" else run_browser)(args, work, unpacked, payload, log_path, report)
            runtime_blockers = report["blockers"][:]
            report.update(assess_execution(execution))
            report["blockers"].extend(runtime_blockers)
            if report["blockers"]:
                report["status"] = "blocked"
    except Exception as error:
        report["status"] = "blocked"
        report["blockers"].append({"scope": "infrastructure", "reason": str(error)})
        if not isinstance(error, Blocked):
            report["traceback"] = traceback.format_exc()
    finally:
        report["finished_utc"] = browser_probe.now()
        report["log"] = {"path": log_path.name, "sha256": browser_probe.digest(log_path), "bytes": log_path.stat().st_size}
        (args.output / (stem + ".json")).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run", help="Collect one engine's diagnostic observations")
    runner.add_argument("--engine", choices=("native", "browser"), required=True)
    runner.add_argument("--asset", type=Path, help="Already downloaded exact pinned archive")
    runner.add_argument("--payload", type=Path, default=Path(__file__).with_name("blender_numeric_diagnostics.py"))
    runner.add_argument("--output", type=Path, required=True)
    runner.add_argument("--timeout", type=int, default=240)
    runner.add_argument("--browser-executable")
    comparison = commands.add_parser("compare", help="Pair matching inputs and retain exact scalar/bit differences")
    comparison.add_argument("--native", type=Path, required=True)
    comparison.add_argument("--browser", type=Path, required=True)
    comparison.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        report = run(args)
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        report = compare_reports(json.loads(args.native.read_text()), json.loads(args.browser.read_text()))
        report["source_reports"] = [{"engine": name, "path": path.name, "sha256": browser_probe.digest(path)}
                                    for name, path in (("native", args.native), ("browser", args.browser))]
        (args.output / "numeric-diagnostic-comparison.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "diagnostic_only": True,
                      "counters": report.get("counters"), "blockers": report["blockers"]}))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
