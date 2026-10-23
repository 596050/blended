#!/usr/bin/env python3
"""Capture a new infrastructure execution after recovery; no Blender credit."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def sources():
    paths = set()
    for name in ("tools", "tests", "patches", "compatibility/candidate-suites",
                 "compatibility/package-overlays"):
        paths.update(path for path in (ROOT / name).rglob("*")
                     if path.is_file() and not path.is_symlink()
                     and "__pycache__" not in path.parts and path.suffix != ".pyc")
    paths.update((ROOT / "upstream.lock.json", ROOT / ".github/workflows/test-parity-ledger.yml",
                  Path(__file__).resolve()))
    return [{**identity(path), "path": path.relative_to(ROOT).as_posix()}
            for path in sorted(paths)]


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    receipt = OUT / "execution.json"
    if receipt.exists():
        raise SystemExit("Refusing to overwrite an infrastructure execution receipt")
    cmake = ROOT / "runtime/cmake-host/cmake/data/bin/cmake"
    if not cmake.is_file():
        raise SystemExit("Pinned CMake executable is unavailable")
    before = sources()
    (OUT / "source-inputs.json").write_text(json.dumps(before, indent=2) + "\n")
    environment = os.environ.copy()
    environment["BLENDED_INVENTORY_CMAKE"] = str(cmake)
    argv = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    record = {
        "schema": 1, "kind": "infrastructure-test-execution", "status": "running",
        "started_utc": utc(), "cwd": str(ROOT), "argv": argv,
        "python": {"version": sys.version, "executable": identity(Path(sys.executable).resolve())},
        "cmake": identity(cmake), "cxx": identity(Path(shutil.which("c++")).resolve()),
        "platform": platform.platform(),
        "environment_overrides": {"BLENDED_INVENTORY_CMAKE": str(cmake)},
        "source_inputs": identity(OUT / "source-inputs.json"),
        "blender_cases_executed": 0, "original_blender_cases_qualified": 0,
        "full_feature_parity": False,
        "recovery_scope": "New execution over restored and newly authored code; not a recreation of the lost 369-test receipt."
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    start = time.monotonic()
    result = None
    timed_out = False
    with (OUT / "stdout.log").open("wb") as stdout, (OUT / "stderr.log").open("wb") as stderr:
        try:
            result = subprocess.run(argv, cwd=ROOT, env=environment, stdout=stdout,
                                    stderr=stderr, timeout=600, check=False)
        except subprocess.TimeoutExpired:
            timed_out = True
    after = sources()
    (OUT / "source-inputs-after.json").write_text(json.dumps(after, indent=2) + "\n")
    stderr_text = (OUT / "stderr.log").read_text(errors="replace")
    summary = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", stderr_text, flags=re.M)
    matches = re.findall(r"^(OK(?: \(.*\))?|FAILED \(.*\))$", stderr_text, flags=re.M)
    record.update(
        finished_utc=utc(), elapsed_seconds=time.monotonic() - start,
        returncode=None if result is None else result.returncode, timed_out=timed_out,
        source_inputs_after=identity(OUT / "source-inputs-after.json"),
        source_inputs_unchanged=before == after, source_file_count=len(before),
        stdout=identity(OUT / "stdout.log"), stderr=identity(OUT / "stderr.log"),
        unittest_summary={"tests": int(summary[-1][0]), "seconds": float(summary[-1][1]),
                          "result": matches[-1] if matches else None} if summary else None)
    passed = (result is not None and result.returncode == 0 and not timed_out
              and before == after and bool(summary) and matches == ["OK"])
    record["status"] = "passed" if passed else "failed"
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in
                     ("status", "returncode", "elapsed_seconds", "source_file_count",
                      "source_inputs_unchanged", "unittest_summary")}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
