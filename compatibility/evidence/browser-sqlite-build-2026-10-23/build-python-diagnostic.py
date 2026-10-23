#!/usr/bin/env python3
"""Relink only a diagnostic entrypoint around the verified real Python archive."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os
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
    parser.add_argument("--reference-build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    previous_path = args.reference_build.resolve()
    previous = json.loads(previous_path.read_text())
    if not previous["completed_successfully"]:
        raise ValueError("reference CPython component build did not succeed")
    for entry in previous["input_files"]:
        actual = identity(Path(entry["path"]))
        if any(actual[key] != entry[key] for key in ("bytes", "sha256")):
            raise ValueError("a reference compiler, source, header or library changed")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[3]
    diagnostic = repo / "patches/browser-sqlite/probe_python_sqlite.py"
    program = output / "python-sqlite.js"
    pre_js = output / "diagnostic-pre.js"
    source = diagnostic.read_text()
    pre_js.write_text("Module.arguments = " + json.dumps(["-c", source]) + ";\n"
                      "Module.preRun = Module.preRun || [];\n"
                      "Module.preRun.push(function () {\n"
                      "  ENV.PYTHONHOME = '/usr/local';\n"
                      "  ENV.PYTHONDONTWRITEBYTECODE = '1';\n"
                      "  ENV.PYTHONUNBUFFERED = '1';\n"
                      "});\n")
    command = previous["command"][:]
    command[command.index("--pre-js") + 1] = str(pre_js)
    command[command.index("-o") + 1] = str(program)
    env = os.environ.copy()
    env.update(previous["environment_overrides"])
    report = {"schema": 1, "kind": "standalone-wasm-cpython-sqlite-diagnostic-build",
              "started_utc": datetime.now(timezone.utc).isoformat(), "command": command, "cwd": str(output),
              "environment_overrides": previous["environment_overrides"], "reference_build": identity(previous_path),
              "capture_driver": identity(Path(__file__).resolve()), "diagnostic_source": identity(diagnostic),
              "pre_js": identity(pre_js), "inherited_verified_inputs": previous["input_files"],
              "original_blender_invocation_executed": False, "strict_blender_browser_test_passes": 0,
              "full_feature_parity": False}
    started = time.monotonic()
    with (output / "build.log").open("xb") as log:
        result = subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    report.update(returncode=result.returncode, completed_successfully=result.returncode == 0,
                  elapsed_seconds=round(time.monotonic() - started, 6), finished_utc=datetime.now(timezone.utc).isoformat())
    report["build_log"] = identity(output / "build.log")
    report["artifacts"] = [identity(path) for path in (program, program.with_suffix(".wasm"), program.with_suffix(".data")) if path.is_file()]
    (output / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
