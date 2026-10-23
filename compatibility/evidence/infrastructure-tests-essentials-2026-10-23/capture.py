#!/usr/bin/env python3
"""Retain the actual infrastructure test process and its source-file identities."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CMAKE = ROOT.parent / "runtime/browser-python/bin/cmake"


def identity(path, name=None):
    path = Path(path)
    with path.open("rb") as stream:
        value = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": name or str(path.resolve()), "bytes": path.stat().st_size, "sha256": value}


def write_json(name, value):
    path = OUT / name
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return identity(path, name)


def source_inputs():
    files = []
    for folder in ("tools", "tests", "patches", "compatibility/package-overlays"):
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                if path.is_symlink():
                    raise ValueError("test source input must be a regular file: " + str(path))
                files.append(identity(path, path.relative_to(ROOT).as_posix()))
    return files


assert not (OUT / "execution.json").exists(), "previous execution evidence is immutable"
before = source_inputs()
before_ref = write_json("source-inputs-before.json", before)
version = subprocess.run([str(CMAKE), "--version"], cwd=ROOT, capture_output=True, check=True)
git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True).stdout.decode().strip()
status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, capture_output=True, check=True)
(OUT / "working-tree-before.log").write_bytes(status.stdout)
command = ["env", "BLENDED_INVENTORY_CMAKE=" + str(CMAKE), "python3", "-m", "unittest", "discover", "-s", "tests", "-q"]
started = datetime.now(timezone.utc).isoformat()
tick = time.monotonic()
print(json.dumps({"status": "running", "command": command, "cwd": str(ROOT)}), flush=True)
try:
    process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=900)
    stdout, stderr, returncode, timed_out = process.stdout, process.stderr, process.returncode, False
except subprocess.TimeoutExpired as exc:
    stdout, stderr, returncode, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
elapsed = time.monotonic() - tick
finished = datetime.now(timezone.utc).isoformat()
for name, data in (("stdout.log", stdout), ("stderr.log", stderr)):
    with (OUT / name).open("xb") as stream:
        stream.write(data)
after = source_inputs()
after_ref = write_json("source-inputs-after.json", after)
text = stderr.decode("utf-8", errors="replace")
summaries = re.findall(r"^Ran ([0-9]+) tests? in ([0-9.]+)s$", text, re.MULTILINE)
results = re.findall(r"^(OK(?: \([^\n]+\))?|FAILED(?: \([^\n]+\))?)$", text, re.MULTILINE)
summary = None
if summaries and results:
    count, duration = summaries[-1]
    skipped = re.search(r"skipped=([0-9]+)", results[-1])
    summary = {"tests_run": int(count), "reported_duration_seconds": float(duration),
               "result": results[-1], "skipped": int(skipped.group(1)) if skipped else 0}
receipt = {
    "schema": 1, "kind": "infrastructure-regression-execution", "command": command,
    "cwd": str(ROOT), "started_utc": started, "finished_utc": finished,
    "duration_seconds": elapsed, "returncode": returncode, "timed_out": timed_out,
    "unittest_summary": summary, "stdout": identity(OUT / "stdout.log", "stdout.log"),
    "stderr": identity(OUT / "stderr.log", "stderr.log"),
    "python": {**identity(Path(shutil.which("python3")).resolve()), "version": sys.version},
    "cmake": {**identity(CMAKE), "version_output": version.stdout.decode()},
    "capture_tool": identity(Path(__file__), "capture.py"), "git_head_before": git_head,
    "working_tree_before": identity(OUT / "working-tree-before.log", "working-tree-before.log"),
    "source_inputs_before": before_ref, "source_inputs_after": after_ref,
    "source_inputs_unchanged": before == after,
    "source_identity_scope": "All regular files under tools, tests, patches and compatibility/package-overlays, excluding Python bytecode caches. This is not a complete working-tree or runtime dependency snapshot; the existing Git HEAD also predates uncommitted changes recorded in the status log.",
    "claim_limit": "Infrastructure regressions only. This process does not imply that all Blender tests passed or that application feature parity is complete.",
    "all_upstream_test_parity": False, "full_feature_parity": False,
}
receipt["status"] = "passed" if returncode == 0 and not timed_out and before == after and summary and summary["result"].startswith("OK") else "failed"
reference = write_json("execution.json", receipt)
print(json.dumps({"status": receipt["status"], "summary": summary, "source_inputs_unchanged": before == after, "receipt": reference}), flush=True)
raise SystemExit(0 if receipt["status"] == "passed" else 1)
