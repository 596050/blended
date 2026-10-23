#!/usr/bin/env python3
"""Capture one real optional dependency recipe under explicit resource bounds."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port-root", type=Path, required=True)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--recipe", choices=("sqlite", "python"), required=True)
    parser.add_argument("--timeout", type=int, default=2400)
    args = parser.parse_args()
    port = args.port_root.resolve()
    attempt = args.attempt.resolve()
    attempt.mkdir(parents=True, exist_ok=True)
    result_path = attempt / "execution.json"
    log_path = attempt / "build.log"
    if result_path.exists() or log_path.exists():
        raise ValueError("attempt output already exists")
    work = port.parent
    env = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONPATH", "CC", "CXX", "AR", "RANLIB", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS"):
        env.pop(key, None)
    overrides = {
        "PATH": str(work / "shims") + os.pathsep + env["PATH"],
        "EM_CACHE": str(work / "emscripten-cache"),
        "BLENDED_SQLITE_PATCHSET_SHA256": identity(port / "scripts/deps/sqlite-patchset.json")["sha256"],
        "BLENDED_BUILD_JOBS": "1", "MAKEFLAGS": "-j1", "CMAKE_BUILD_PARALLEL_LEVEL": "1", "PYTHON_CPU_COUNT": "1", "EMCC_CORES": "1",
    }
    env.update(overrides)
    command = ["bash", str(port / ("scripts/deps/" + args.recipe + ".sh"))]
    inputs = [identity(port / ("scripts/deps/" + name)) for name in ("sqlite-patchset.json", "sqlite.sh", "sqlite-cache.py", "python.sh")]
    free_before = shutil.disk_usage(work).free
    if free_before < 4 * 1024**3:
        raise RuntimeError("insufficient disk reserve before dependency build")
    started = time.monotonic()
    report = {"schema": 1, "command": command, "cwd": str(port), "environment_overrides": overrides,
              "input_files": inputs, "capture_driver": identity(Path(__file__).resolve()),
              "started_utc": datetime.now(timezone.utc).isoformat(), "timeout_seconds": args.timeout,
              "minimum_disk_reserve_bytes": 4 * 1024**3, "free_bytes_before": free_before,
              "browser_tests_executed": False, "full_feature_parity": False}
    reason = None
    free_min = free_before
    with log_path.open("xb") as log:
        child = subprocess.Popen(command, cwd=port, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        while child.poll() is None:
            time.sleep(2)
            free_min = min(free_min, shutil.disk_usage(work).free)
            if time.monotonic() - started > args.timeout:
                reason = "timeout"
            elif free_min < 4 * 1024**3:
                reason = "disk reserve exhausted"
            if reason:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                break
        returncode = child.wait()
    report.update({"returncode": returncode, "termination_reason": reason,
                   "elapsed_seconds": round(time.monotonic() - started, 6),
                   "finished_utc": datetime.now(timezone.utc).isoformat(),
                   "free_bytes_minimum": free_min, "child_max_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                   "log": identity(log_path), "completed_successfully": returncode == 0 and reason is None})
    stamp = port / ("lib/wasm/share/blended/" + args.recipe + "-sqlite-cache.json")
    if stamp.is_file():
        destination = attempt / "harvest-cache.json"
        shutil.copyfile(stamp, destination)
        report["harvest_cache"] = identity(destination)
    result_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["completed_successfully"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
