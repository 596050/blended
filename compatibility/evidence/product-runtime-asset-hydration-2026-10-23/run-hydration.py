"""Retain a bounded host process receipt for the exact asset hydration attempt."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


directory = Path(__file__).resolve().parent
repo = directory.parents[2]
script = directory / "hydrate-assets.py"
log_path = directory / "host.log"
receipt_path = directory / "host-process.json"
if log_path.exists() or receipt_path.exists():
    raise RuntimeError("retain the original host attempt")


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


command = [sys.executable, str(script)]
record = {"schema": 1, "command": command, "cwd": str(repo), "hydrator": identity(script),
          "runner": identity(Path(__file__)), "started_utc": datetime.now(timezone.utc).isoformat(),
          "timeout_seconds": 600, "minimum_free_disk_bytes": 4 * 1024 ** 3,
          "termination_reason": None, "tests_executed": 0, "builds_started": 0}
started = time.monotonic()
with log_path.open("xb") as log:
    process = subprocess.Popen(command, cwd=repo, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    while process.poll() is None:
        if time.monotonic() - started > record["timeout_seconds"]:
            record["termination_reason"] = "elapsed_time_bound"
        elif shutil.disk_usage(repo).free < record["minimum_free_disk_bytes"]:
            record["termination_reason"] = "free_disk_bound"
        if record["termination_reason"]:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            break
        time.sleep(1)
record.update(returncode=process.returncode, finished_utc=datetime.now(timezone.utc).isoformat(),
              elapsed_seconds=time.monotonic() - started, log=identity(log_path),
              hydration_report=identity(directory / "report.json") if (directory / "report.json").is_file() else None)
with receipt_path.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps(record, indent=2))
raise SystemExit(0 if record["returncode"] == 0 and not record["termination_reason"] else 1)
