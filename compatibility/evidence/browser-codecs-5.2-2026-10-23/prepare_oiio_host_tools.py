#!/usr/bin/env python3
"""Install the enclosing driver's exact CMake/Ninja wheel pins privately."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

REQUIREMENTS = """cmake==4.0.3 --hash=sha256:d840e780c48c5df1330879d50615176896e8e6eee554507d21ce8e2f1a5f0ff8
ninja==1.13.0 --hash=sha256:fb46acf6b93b8dd0322adc3a4945452a4e774b75b91293bafcc7b7f8e6517dfa
"""


def identity(path):
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output, target = args.output.resolve(), args.target.resolve()
    assert not output.exists() and not target.exists()
    output.mkdir(parents=True)
    requirements = output / "requirements.txt"
    requirements.write_text(REQUIREMENTS)
    argv = [str(args.python.resolve()), "-m", "pip", "install", "--disable-pip-version-check", "--no-deps", "--require-hashes",
            "--only-binary=:all:", "--target", str(target), "-r", str(requirements)]
    report = {"schema": 1, "kind": "codec-validation-host-tool-installation", "argv": argv,
              "started_at": datetime.now(timezone.utc).isoformat(), "requirements": identity(requirements),
              "runner": identity(Path(__file__).resolve()), "blender_cases_executed": 0}
    started = time.monotonic()
    log = output / "install.log"
    with log.open("wb") as stream:
        process = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=300)
    report.update(returncode=process.returncode, completed_at=datetime.now(timezone.utc).isoformat(),
                  duration_seconds=round(time.monotonic() - started, 6), log=identity(log))
    if process.returncode == 0:
        report["binaries"] = [identity(target / "cmake/data/bin/cmake"), identity(target / "bin/ninja")]
    (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"returncode": process.returncode, "receipt": str(output / "execution.json")}))
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
