#!/usr/bin/env python3
"""Run every frozen original unittest invocation in an immutable native plan.

Each job gets a fresh browser and engine. Unexpanded source declarations remain
in the matrix. A source plan is not a configured CTest inventory and this runner
does not claim full Blender test or feature parity.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

try:
    from .unittest_cohort import UPSTREAM_SHA, load_manifest, read_bound_json
except ImportError:
    from unittest_cohort import UPSTREAM_SHA, load_manifest, read_bound_json

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def file_record(path):
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def resolve_manifest_record(record, repo_root):
    """Resolve repository-relative source-plan records independently of cwd."""
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise ValueError("manifest record requires a path")
    path = Path(record["path"])
    path = path.resolve() if path.is_absolute() else (Path(repo_root) / path).resolve()
    if "bytes" in record and (type(record["bytes"]) is not int or record["bytes"] != path.stat().st_size):
        raise ValueError("manifest record byte count differs from the frozen file")
    return path


def overlay_inputs(receipt, base_asset):
    """Require both augmentation inputs without replacing base build provenance."""
    if bool(receipt) != bool(base_asset):
        raise ValueError("package overlay requires both its receipt and the original base archive")
    if receipt is None:
        return None
    for path in (receipt, base_asset):
        if not Path(path).is_file() or Path(path).is_symlink():
            raise ValueError("package overlay inputs must be regular files: " + str(path))
    return {"receipt": Path(receipt).resolve(), "base_asset": Path(base_asset).resolve()}


def harness_sources(root):
    """Freeze reviewed optional patch inputs with the actual runner code."""
    root = Path(root)
    candidates = [*sorted((root / "tools").glob("*.py")),
                  root / "tools/upstream_invocations_5_2.json",
                  *sorted((root / "compatibility/package-overlays").glob("*.json"))]
    for directory in ("browser-numerics", "browser-sqlite", "browser-codecs"):
        candidates.extend(sorted((root / "patches" / directory).rglob("*")))
    return [path for path in candidates if path.is_file() and not path.is_symlink()
            and "__pycache__" not in path.relative_to(root).parts and path.suffix not in (".pyc", ".pyo")]


def suite_source_arguments(catalog, source_root):
    """Omit local paths to use the probe's exact pinned source downloads."""
    if source_root is None:
        return []
    arguments = []
    for suite in catalog["suites"]:
        for source in [suite, *suite.get("support_files", [])]:
            arguments.extend(["--suite", str((Path(source_root) / source["upstream_path"]).resolve())])
    return arguments


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-inventory", required=True, type=Path)
    parser.add_argument("--native-inventory-sha256", required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT,
                        help="Root for repository-relative manifest paths in the immutable source plan")
    parser.add_argument("--source-root", type=Path,
                        help="Optional local original source tree; otherwise fetch each script/helper by its pinned hash and size")
    parser.add_argument("--fixture-root", type=Path, help="Verified original tests/files payload tree")
    parser.add_argument("--resource-root", type=Path, help="Verified original non-test source resource tree")
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--source-build-receipt", required=True, type=Path)
    parser.add_argument("--package-overlay-receipt", type=Path,
                        help="Explicit augmentation receipt; every probe verifies the actual archive transformation")
    parser.add_argument("--package-base-asset", type=Path,
                        help="Original source-built archive required to verify a package augmentation")
    parser.add_argument("--browser-executable", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 4 or not 1 <= args.timeout <= 600:
        parser.error("jobs must be 1 to 4 and timeout must be 1 to 600 seconds")
    try:
        overlay = overlay_inputs(args.package_overlay_receipt, args.package_base_asset)
    except ValueError as error:
        parser.error(str(error))
    inventory = read_bound_json(args.native_inventory, args.native_inventory_sha256)
    if inventory.get("upstream_commit") != UPSTREAM_SHA or not isinstance(inventory.get("registrations"), list):
        parser.error("native source plan does not identify the selected upstream revision")
    output = args.output.resolve()
    if output.exists():
        parser.error("choose a new output directory; prior matrix evidence cannot be overwritten")
    # Validate every frozen manifest before any execution. Its receipt supplies
    # the independent native denominator; browser discovery cannot create it.
    jobs, rows, names = [], [], set()
    for entry in inventory["registrations"]:
        row = {key: entry.get(key) for key in ("source_declaration_index", "line", "ctest_name",
                                              "state", "reason", "native_status", "expected_cases")}
        row["browser_state"] = "blocked_before_browser_execution"
        rows.append(row)
        if entry["state"] != "native_inventory_frozen":
            continue
        name = entry.get("ctest_name")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_]+", name) or name in names:
            parser.error("duplicate or invalid original registration identity")
        names.add(name)
        pin = entry["manifest"]
        manifest_path = resolve_manifest_record(pin, args.repo_root)
        catalog = load_manifest(manifest_path, pin["sha256"])
        if catalog["original_invocation"]["ctest_name"] != name:
            parser.error("native plan and frozen manifest name different registrations")
        row.update(browser_state="not_run", manifest=file_record(manifest_path))
        jobs.append((row, manifest_path, catalog))
    output.mkdir(parents=True)
    shutil.copyfile(args.native_inventory, output / "native-discovery-inventory.json")
    shutil.copyfile(args.source_build_receipt, output / "source-build.json")
    if overlay:
        shutil.copyfile(overlay["receipt"], output / "package-overlay.json")
    snapshot = output / "harness"
    files = []
    for source in harness_sources(ROOT):
        relative = source.relative_to(ROOT)
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        files.append({"path": relative.as_posix(), "bytes": destination.stat().st_size, "sha256": digest(destination)})
    harness = {"schema": 1, "files": files, "purpose": "Immutable runner bytes for this matrix execution"}
    (output / "harness-manifest.json").write_text(json.dumps(harness, indent=2) + "\n")
    matrix = {"schema": 1, "upstream_commit": UPSTREAM_SHA, "started_utc": now(), "finished_utc": None,
              "native_inventory": file_record(output / "native-discovery-inventory.json"),
              "harness_manifest": file_record(output / "harness-manifest.json"),
              "source_build_receipt": file_record(output / "source-build.json"),
              "asset": file_record(args.asset), "browser_executable": file_record(args.browser_executable),
              "python_executable": file_record(sys.executable), "jobs": args.jobs,
              "configured_ctest_inventory": False, "all_upstream_test_parity": False,
              "full_feature_parity": False, "registrations": rows}
    if overlay:
        matrix["package_overlay_receipt"] = file_record(output / "package-overlay.json")
        matrix["package_base_asset"] = file_record(overlay["base_asset"])
    def save():
        states = {}
        for row in rows:
            states[row["browser_state"]] = states.get(row["browser_state"], 0) + 1
        matrix["browser_state_counts"] = states
        (output / "matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    save()

    def execute(job):
        row, manifest_path, catalog = job
        destination = output / row["ctest_name"]
        destination.mkdir()
        command = [sys.executable, str(snapshot / "tools/probe_browser_port.py"),
                   "--asset", str(args.asset.resolve()), "--source-build-receipt", str((output / "source-build.json").resolve()),
                   "--suite-manifest", str(manifest_path), "--suite-manifest-sha256", row["manifest"]["sha256"],
                   "--browser-executable", str(args.browser_executable.resolve()), "--output", str(destination),
                   "--timeout", str(args.timeout)]
        command.extend(suite_source_arguments(catalog, args.source_root))
        if args.fixture_root:
            command.extend(["--fixture-root", str(args.fixture_root.resolve())])
        if args.resource_root:
            command.extend(["--resource-root", str(args.resource_root.resolve())])
        if overlay:
            command.extend(["--package-overlay-receipt", str(output / "package-overlay.json"),
                            "--package-base-asset", str(overlay["base_asset"])])
        process = {"started_utc": now(), "command": command, "timed_out": False,
                   "timeout_seconds": args.timeout + 120, "returncode": None}
        with (destination / "host-process.log").open("wb") as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                process["returncode"] = child.wait(timeout=args.timeout + 120)
            except subprocess.TimeoutExpired:
                process["timed_out"] = True
                os.killpg(child.pid, signal.SIGKILL)
                process["returncode"] = child.wait()
        process["finished_utc"] = now()
        process["log"] = file_record(destination / "host-process.log")
        (destination / "host-process.json").write_text(json.dumps(process, indent=2) + "\n")
        receipt = destination / "qualification.json"
        update = {"host_process": file_record(destination / "host-process.json"), "browser_state": "missing_receipt"}
        if receipt.is_file():
            report = json.loads(receipt.read_text())
            update.update(browser_state=report.get("status", "invalid_receipt"),
                          browser_receipt=file_record(receipt), browser_reason=report.get("reason"),
                          browser_summary=report.get("summary"))
        if process["timed_out"]:
            update["browser_state"] = "host_timed_out"
        return row, update

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(execute, job): job[0] for job in jobs}
        for future in as_completed(futures):
            row = futures[future]
            try:
                _, update = future.result()
                row.update(update)
            except Exception as exc:
                row.update(browser_state="host_error", browser_reason=str(exc))
            save()
            print(json.dumps({"ctest_name": row["ctest_name"], "state": row["browser_state"],
                              "expected_cases": row.get("expected_cases")}), flush=True)
    matrix["finished_utc"] = now()
    save()
    print(json.dumps({"matrix": str(output / "matrix.json"), "counts": matrix["browser_state_counts"],
                      "all_upstream_test_parity": False}), flush=True)
    return 0 if jobs and all(row["browser_state"] == "passed" for row, _, _ in jobs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
