#!/usr/bin/env python3
"""Capture new evidence-consumer regressions; do not run original Blender tests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent / "regressions"


def now():
    return datetime.now(timezone.utc).isoformat()


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def inputs():
    tracked = subprocess.check_output([
        "git", "-C", str(ROOT), "ls-files", "tools/*.py", "tools/*.json", "patches/**",
        "compatibility/candidate-suites/**", "compatibility/package-overlays/**",
        "tests/test_reconcile_unittest_matrix.py",
    ], text=True).splitlines()
    paths = [*(ROOT / name for name in tracked), ROOT / "tests/test_source_producer_profiles.py", Path(__file__)]
    paths.extend(sorted((OUTPUT.parent / "sources").rglob("*")))
    return [pin(path) for path in sorted(set(paths)) if path.is_file()]


def main():
    OUTPUT.mkdir()
    before = inputs()
    write(OUTPUT / "source-inputs-before.json", before)
    result = {"schema": 1, "kind": "captured-evidence-consumer-regressions",
              "started_utc": now(), "status": "running", "commands": [],
              "base_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
              "scope": "Normalizer compatibility and exact producer profile infrastructure tests only.",
              "original_blender_tests_executed": 0, "full_feature_parity": False}
    write(OUTPUT / "execution.json", result)
    started = time.monotonic()
    for label, pattern in (("existing-normalizer", "test_reconcile_unittest_matrix.py"),
                           ("exact-producer-profiles", "test_source_producer_profiles.py")):
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
        row = {"name": label, "argv": command, "cwd": str(ROOT), "started_utc": now()}
        stdout, stderr = OUTPUT / (label + ".stdout.log"), OUTPUT / (label + ".stderr.log")
        with stdout.open("xb") as out, stderr.open("xb") as err:
            completed = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, timeout=600)
        row.update(returncode=completed.returncode, finished_utc=now(), stdout=pin(stdout), stderr=pin(stderr))
        result["commands"].append(row)
        write(OUTPUT / "execution.json", result)
        print(json.dumps({"name": label, "returncode": completed.returncode}), flush=True)
    after = inputs()
    write(OUTPUT / "source-inputs-after.json", after)
    ok = all(row["returncode"] == 0 for row in result["commands"]) and before == after
    result.update(finished_utc=now(), elapsed_seconds=time.monotonic() - started,
                  status="passed" if ok else "failed", source_inputs_unchanged=before == after,
                  source_inputs_before=pin(OUTPUT / "source-inputs-before.json"),
                  source_inputs_after=pin(OUTPUT / "source-inputs-after.json"))
    write(OUTPUT / "execution.json", result)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
