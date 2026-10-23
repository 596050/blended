#!/usr/bin/env python3
"""Capture original browser font images and run the exact idiff command on host.

This is a separately identified diagnostic. The original browser tests still
fail their missing-comparator assertion. Its output is image-oracle evidence,
never a passing original browser suite or browser subprocess implementation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import traceback

try:
    from . import font_image_oracle as oracle
    from . import probe_browser_port as browser_probe
    from .unittest_cohort import case_id, load_manifest, read_bound_json
except ImportError:
    import font_image_oracle as oracle
    import probe_browser_port as browser_probe
    from unittest_cohort import case_id, load_manifest, read_bound_json

ROOT = Path(__file__).resolve().parents[1]
NON_IMAGE_CASES = {
    "TestStressInvalidCodepoints.test_embedded_null_raises",
    "TestStressInvalidCodepoints.test_surrogates_raise",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path, relative_to):
    path = Path(path).resolve()
    return {"path": os.path.relpath(path, relative_to), "bytes": path.stat().st_size, "sha256": digest(path)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compare_captured_images(report, manifest, qualification, output, executable, expression):
    suite = manifest["suites"][0]
    capture = qualification["execution"].get("font_image_capture", {})
    require(capture.get("schema") == 1 and capture.get("original_failures_preserved") is True,
            "browser image observer did not finish")
    require(capture.get("errors") == [], "browser image observer reported errors")
    expected_ids = set(suite["case_ids"]) - NON_IMAGE_CASES
    require(NON_IMAGE_CASES.issubset(suite["case_ids"]), "original non-image case inventory changed")
    images = capture.get("images")
    require(isinstance(images, list) and 0 < len(images) <= oracle.MAX_IMAGES, "browser image capture inventory is invalid")
    identities = [case_id(image["case_id"]) for image in images]
    require(len(identities) == len(set(identities)) and set(identities) == expected_ids,
            "browser image capture differs from the independent complete native image case inventory")
    raw_suite = qualification["execution"]["suites"][0]
    require([case_id(value) for value in raw_suite["discovered_ids"]] == suite["case_ids"],
            "browser discovered a different original case inventory")
    require(raw_suite["testsRun"] == len(suite["case_ids"]) and raw_suite["failures"] == len(expected_ids) and raw_suite["errors"] == 0,
            "original browser outcomes differ from the missing-comparator diagnostic precondition")
    failures = {case_id(event["id"]): event for event in raw_suite["outcomes"]
                if event["kind"] == "test" and event["status"] == "failed"}
    require(set(failures) == expected_ids and all("idiff not found, set IDIFF_BIN or install OpenImageIO" in row["detail"] for row in failures.values()),
            "original browser failures were not preserved")
    require(qualification["status"] == "failed" and qualification["selected_suites_passed"] is False,
            "host image evidence cannot replace the original browser failure status")
    fixtures = {row["relative_path"]: row for row in suite["fixture_files"]}
    image_root, diff_root, log_root = output / "images", output / "diffs", output / "idiff"
    for directory in (image_root, diff_root, log_root):
        directory.mkdir()
    total = 0
    results = report["images"]
    for image in images:
        require(image["source_sha256"] == oracle.SOURCE_SHA256, "captured image source changed")
        reference = image["reference"]
        expected_ref = fixtures.get(reference["relative_path"])
        require(expected_ref is not None and reference == {key: expected_ref[key] for key in reference},
                "captured reference differs from the original fixture")
        ref_path = output / "browser/fixtures" / reference["relative_path"]
        require(ref_path.is_file() and digest(ref_path) == reference["sha256"] and ref_path.stat().st_size == reference["bytes"],
                "host reference differs from the exact browser-mounted reference")
        for threshold in ("idiff_fail", "idiff_fail_percent"):
            value = image[threshold]
            require(type(value) in (float, int) and math.isfinite(value) and float(value).hex() == image[threshold + "_hex"],
                    "observed original comparator threshold changed in transport")
        data = oracle.decode_image(image)
        total += len(data)
        require(total <= oracle.MAX_TOTAL_BYTES, "browser output export exceeds its total byte bound")
        image_path = image_root / image["filename"]
        with image_path.open("xb") as stream:
            stream.write(data)
        command = oracle.original_command(expression, {**image, "reference_path": ref_path, "output_path": image_path}, executable, diff_root)
        stem = image_path.stem
        process = {"command": command, "started_utc": now(), "returncode": None, "timeout_seconds": 30,
                   "timed_out": False, "capture_output": True, "text": True}
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
            process["returncode"] = result.returncode
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            process["timed_out"] = True
            stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
            stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        process["finished_utc"] = now()
        for name, text in (("stdout", stdout), ("stderr", stderr)):
            path = log_root / (stem + "." + name + ".txt")
            with path.open("x", encoding="utf-8") as stream:
                stream.write(text)
            process[name] = pin(path, output)
        code = process["returncode"]
        status = "passed" if code in (0, 1) else "image_mismatch" if code == 2 else "comparator_error"
        diff_path = Path(command[command.index("-o") + 1])
        row = {key: value for key, value in image.items() if key != "data_b64"}
        row.update(status=status, image=pin(image_path, output), reference_file=pin(ref_path, output),
                   diff=pin(diff_path, output) if diff_path.is_file() else None, process=process,
                   original_browser_test_status="failed", original_comparator_accepted_returncodes=[0, 1])
        results.append(row)
    require(total == capture.get("total_bytes"), "captured image aggregate byte count changed")
    report["counts"] = {"native_image_cases": len(expected_ids), "captured_images": len(images),
                        "captured_bytes": total, "host_idiff_passed": sum(row["status"] == "passed" for row in results),
                        "host_idiff_image_mismatch": sum(row["status"] == "image_mismatch" for row in results),
                        "host_idiff_errors": sum(row["status"] == "comparator_error" for row in results)}
    report["all_original_image_cases_captured"] = True
    report["status"] = "passed" if all(row["status"] == "passed" for row in results) else "failed"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-manifest", required=True, type=Path)
    parser.add_argument("--suite-manifest-sha256", required=True)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--source-build-receipt", required=True, type=Path)
    parser.add_argument("--browser-executable", required=True, type=Path)
    parser.add_argument("--idiff-executable", required=True, type=Path)
    parser.add_argument("--toolchain-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        parser.error("choose a fresh diagnostic directory; raw evidence cannot be overwritten")
    output.mkdir(parents=True)
    report = {"schema": 1, "scope": "host-assisted original font image oracle only", "status": "blocked",
              "started_utc": now(), "finished_utc": None, "full_parity": False,
              "original_browser_tests_passed": False, "browser_subprocess_implemented": False,
              "tests_modified": False, "comparison_tolerances_modified": False,
              "all_original_image_cases_captured": False, "counts": None, "images": []}
    try:
        require(0 < args.timeout <= 600, "browser timeout must be between 1 and 600 seconds")
        manifest = read_bound_json(args.suite_manifest, args.suite_manifest_sha256)
        load_manifest(args.suite_manifest, args.suite_manifest_sha256)
        suite, execution = manifest["suites"][0], manifest["execution"]
        require(suite["upstream_path"] == oracle.SOURCE_PATH and suite["sha256"] == oracle.SOURCE_SHA256,
                "diagnostic requires the exact reviewed original font source")
        require(execution["script_args"] in (["--mode=BUFFER"], ["--mode=VFONT", "--use-vfont-render"]),
                "diagnostic requires the unchanged original BUFFER or VFONT CTest invocation")
        tool = next(row for row in execution["host_tools"] if row["environment"] == "IDIFF_BIN")
        executable = args.idiff_executable.resolve()
        require(executable.is_file() and digest(executable) == tool["sha256"] and executable.stat().st_size == tool["bytes"],
                "host idiff differs from the exact independently observed native comparator")
        toolchain = json.loads(args.toolchain_receipt.read_text())
        require(all(toolchain["OpenImageIO"]["idiff"][key] == tool[key] for key in ("sha256", "bytes")),
                "host toolchain receipt differs from the native comparator")
        source_path = args.source_root / suite["upstream_path"]
        source = source_path.read_bytes()
        require(hashlib.sha256(source).hexdigest() == oracle.SOURCE_SHA256 and len(source) == suite["bytes"],
                "original font source changed")
        expression = oracle.comparator_expression(source)
        native_path = args.suite_manifest.resolve().parent / manifest["native_discovery"]["path"]
        report.update(upstream=manifest["upstream"], ctest_name=execution["ctest_name"],
                      manifest=pin(args.suite_manifest, output), native_receipt=pin(native_path, output),
                      toolchain_receipt=pin(args.toolchain_receipt, output), comparator=pin(executable, output),
                      source=pin(source_path, output), comparator_expression=expression)
        source_copy = output / "sources" / suite["upstream_path"]
        source_copy.parent.mkdir(parents=True)
        source_copy.write_bytes(source)
        report["preserved_source"] = pin(source_copy, output)
        harness = output / "harness"
        harness.mkdir()
        for path in sorted((ROOT / "tools").glob("*.py")):
            shutil.copyfile(path, harness / path.name)
        report["harness"] = [pin(path, output) for path in sorted(harness.iterdir())]

        ordinary_payload = browser_probe.python_payload
        def capture_payload(*payload_args, **payload_kwargs):
            code = oracle.instrument_payload(ordinary_payload(*payload_args, **payload_kwargs))
            with (output / "observer.py").open("x", encoding="utf-8") as stream:
                stream.write(code)
            return code
        browser_probe.python_payload = capture_payload
        browser_args = ["--suite-manifest", str(args.suite_manifest.resolve()),
                        "--suite-manifest-sha256", args.suite_manifest_sha256,
                        "--suite", str(source_path.resolve()), "--fixture-root", str(args.fixture_root.resolve()),
                        "--asset", str(args.asset.resolve()), "--source-build-receipt", str(args.source_build_receipt.resolve()),
                        "--browser-executable", str(args.browser_executable.resolve()),
                        "--output", str(output / "browser"), "--timeout", str(args.timeout)]
        try:
            report["browser_probe_exit_code"] = browser_probe.main(browser_args)
        finally:
            browser_probe.python_payload = ordinary_payload
        qualification_path = output / "browser/qualification.json"
        report["browser_receipt"] = pin(qualification_path, output)
        qualification = json.loads(qualification_path.read_text())
        report["original_browser_status"] = qualification["status"]
        report["original_browser_summary"] = qualification["summary"]
        require(qualification.get("execution") is not None, "browser did not reach the original tests")
        report["observer"] = pin(output / "observer.py", output)
        require(report["observer"]["sha256"] == qualification["runner_sha256"], "captured runner source does not match actual browser execution")
        compare_captured_images(report, manifest, qualification, output, executable, expression)
        require(digest(executable) == tool["sha256"], "host comparator bytes changed during execution")
    except Exception as error:
        report["status"] = "failed"
        report["reason"] = str(error)
        report["traceback"] = traceback.format_exc()
    finally:
        report["finished_utc"] = now()
        path = output / "font-image-oracle.json"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "scope": report["scope"], "counts": report["counts"],
                          "original_browser_tests_passed": False, "report": str(path)}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
