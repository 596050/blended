#!/usr/bin/env python3
"""Retain the actual evidence runner process return code and unmodified byte logs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_new(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def main():
    if len(sys.argv) != 2 or "/" in sys.argv[1] or sys.argv[1] in (".", ".."):
        raise ValueError("provide one new attempt directory basename")
    attempt = HERE / sys.argv[1]
    host = HERE / (sys.argv[1] + "-host")
    host.mkdir(exist_ok=False)
    if attempt.exists():
        raise FileExistsError("the attempt must be new")
    command = [str(RUNTIME / "browser-python/bin/python"), str(HERE / "run-browser-v2.py"),
               "--output", str(attempt), "--timeout-seconds", "180"]
    receipt = {"schema": 1, "kind": "browser-bevel-host-process-capture", "command": command,
               "cwd": str(REPO), "capture_script": identity(Path(__file__).resolve()),
               "runner_before": identity(HERE / "run-browser-v2.py"),
               "started_utc": datetime.now(timezone.utc).isoformat(),
               "deadline_seconds": 300, "timed_out": False}
    write_new(host / "prospective-command.json", receipt)
    began = time.monotonic()
    with (host / "stdout.log").open("xb") as stdout, (host / "stderr.log").open("xb") as stderr:
        process = subprocess.Popen(command, cwd=REPO, stdout=stdout, stderr=stderr)
        try:
            process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            receipt["timed_out"] = True
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=15)
    receipt["actual_process_returncode"] = process.returncode
    receipt["elapsed_seconds"] = round(time.monotonic() - began, 6)
    receipt["runner_after"] = identity(HERE / "run-browser-v2.py")
    receipt["runner_unchanged"] = receipt["runner_before"] == receipt["runner_after"]
    receipt["stdout"] = identity(host / "stdout.log")
    receipt["stderr"] = identity(host / "stderr.log")
    if (attempt / "execution.json").is_file():
        receipt["child_receipt"] = identity(attempt / "execution.json")
    write_new(host / "execution.json", receipt)
    print(json.dumps(receipt), flush=True)
    return 0 if process.returncode == 0 and not receipt["timed_out"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
