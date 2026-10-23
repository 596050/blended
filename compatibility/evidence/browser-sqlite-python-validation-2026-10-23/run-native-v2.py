#!/usr/bin/env python3
"""Run the same separate binding diagnostic with Blender's real native Python."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    here = Path(__file__).resolve().parent
    repo = here.parents[2]
    native = repo.parent / "runtime/native/blender-5.2.0-linux-x64/5.2/python/bin/python3.13"
    source = here / "probe_python_sqlite_v2.py"
    output = here / "native-v2"
    output.mkdir(exist_ok=False)
    command = [str(native), str(source)]
    report = {"schema": 1, "kind": "native-cpython-sqlite-diagnostic-comparison-v2",
              "started_utc": datetime.now(timezone.utc).isoformat(), "command": command,
              "capture_driver": identity(Path(__file__).resolve()),
              "inputs": [identity(native), identity(source)],
              "original_blender_tests_executed": False, "strict_blender_browser_test_passes": 0,
              "full_feature_parity": False}
    started = time.monotonic()
    with (output / "stdout.log").open("xb") as stdout, (output / "stderr.log").open("xb") as stderr:
        process = subprocess.run(command, cwd=output, stdout=stdout, stderr=stderr, timeout=60)
    marker = "BLENDED_SQLITE_PYTHON_DIAGNOSTIC "
    report["observations"] = [json.loads(line[len(marker):]) for line in (output / "stdout.log").read_text().splitlines() if line.startswith(marker)]
    report.update(returncode=process.returncode, elapsed_seconds=round(time.monotonic() - started, 6),
                  finished_utc=datetime.now(timezone.utc).isoformat(),
                  logs=[identity(output / "stdout.log"), identity(output / "stderr.log")])
    report["completed_successfully"] = (process.returncode == 0 and len(report["observations"]) == 1
                                         and report["observations"][0].get("diagnostic_version") == 2)
    (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["completed_successfully"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
