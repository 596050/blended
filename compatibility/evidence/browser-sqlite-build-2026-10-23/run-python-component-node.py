#!/usr/bin/env python3
"""Execute unchanged original test bodies on the standalone Wasm CPython build."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    node = repo.parent / "runtime/browser-sqlite-work/gessa/tools/emsdk/node/22.16.0_64bit/bin/node"
    build_path = artifact / "build.json"
    build = json.loads(build_path.read_text())
    if not build["completed_successfully"]:
        raise ValueError("component build did not succeed")
    for entry in build["artifacts"]:
        actual = identity(artifact / Path(entry["path"]).name)
        if any(actual[key] != entry[key] for key in ("bytes", "sha256")):
            raise ValueError("compiled component artifact changed")
    helper = evidence / "component-results.py"
    spec = importlib.util.spec_from_file_location("component_results", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    command = [str(node), str(artifact / "python-sqlite.js")]
    report = {"schema": 1, "kind": "standalone-wasm-cpython-original-module-node",
              "started_utc": datetime.now(timezone.utc).isoformat(), "command": command, "cwd": str(artifact),
              "capture_driver": identity(Path(__file__).resolve()), "output_parser": identity(helper),
              "build_receipt": identity(build_path), "node": identity(node),
              "artifact_inputs": build["artifacts"], "original_blender_invocation_executed": False,
              "original_test_assertions_modified": False, "strict_blender_browser_test_passes": 0,
              "full_feature_parity": False}
    started = time.monotonic()
    result = subprocess.run(command, cwd=artifact, capture_output=True, timeout=180)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    report.update(returncode=result.returncode, elapsed_seconds=round(time.monotonic() - started, 6),
                  finished_utc=datetime.now(timezone.utc).isoformat())
    report["logs"] = [identity(output / name) for name in ("stdout.log", "stderr.log")]
    combined = (result.stdout + b"\n" + result.stderr).decode("utf-8", "replace")
    report["case_reconciliation"] = module.reconcile_output(combined, build["expected_case_ids"], result.returncode)
    report["completed_successfully"] = report["case_reconciliation"]["complete_original_module_pass_in_component"]
    (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["completed_successfully"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
