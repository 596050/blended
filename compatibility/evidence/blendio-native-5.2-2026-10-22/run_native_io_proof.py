#!/usr/bin/env python3
"""Reproduce the four-method proof using the verified official native release."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from observe_blendfile_io import EXPECTED_CASES, SOURCE_HASHES, UPSTREAM_COMMIT

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
REFERENCE = WORKSPACE / "research_tests/native_ref"
BINARY = REFERENCE / "blender-5.2.0-linux-x64/blender"
ARCHIVE = REFERENCE / "blender-5.2.0-linux-x64.tar.xz"
ARCHIVE_SHA256 = "96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48"
BINARY_SHA256 = "83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27"


def record(path, relative_to=None):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return {"path": str(path.relative_to(relative_to)) if relative_to else str(path),
            "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=BINARY)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--source-dir", type=Path, default=ROOT.parent / "sources")
    parser.add_argument("--output", type=Path, default=ROOT / "native-proof")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("choose a fresh proof directory")
    output.mkdir(parents=True, exist_ok=True)
    binary = args.binary.resolve()
    archive, executable = record(args.archive.resolve()), record(binary)
    if archive["bytes"] != 384441228 or archive["sha256"] != ARCHIVE_SHA256:
        raise RuntimeError("native archive does not match the pinned official release")
    if executable["sha256"] != BINARY_SHA256:
        raise RuntimeError("native executable differs from the verified reference")
    sources = output / "sources"
    sources.mkdir()
    source_records = []
    for name, expected in SOURCE_HASHES.items():
        source = args.source_dir / name
        measured = record(source)
        if measured["sha256"] != expected:
            raise RuntimeError("source differs from the exact pinned upstream file: " + name)
        destination = sources / name
        shutil.copyfile(source, destination)
        row = record(destination, output)
        data = destination.read_bytes()
        row["upstream_path"] = "tests/python/" + name
        row["upstream_url"] = "https://github.com/blender/blender/blob/" + UPSTREAM_COMMIT + "/" + row["upstream_path"]
        row["git_blob_sha1"] = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        source_records.append(row)
    observer = ROOT / "observe_blendfile_io.py"
    command = [str(binary), "--background", "--factory-startup", "--threads", "1",
               "--python-exit-code", "1", "--python", str(observer), "--",
               "--source-dir", str(sources), "--output-dir", str(output / "generated"),
               "--report", str(output / "execution.json")]
    receipt = {"schema": 1, "scope": "candidate native custom-driver I/O qualification",
               "upstream_commit": UPSTREAM_COMMIT, "expected_cases": EXPECTED_CASES,
               "browser_executed": False, "full_facet_parity": False, "full_feature_parity": False,
               "official_archive": archive, "executable": executable,
               "observer": record(observer), "host_runner": record(Path(__file__)), "source_files": source_records,
               "source_bytes_preserved": None, "command": command, "status": "running"}
    receipt_path = output / "native-io-proof.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    started = time.monotonic()
    log = output / "native-io.log"
    with log.open("wb") as stream:
        process = subprocess.run(command, cwd=output, stdout=stream, stderr=subprocess.STDOUT,
                                 timeout=120, check=False)
    receipt["returncode"] = process.returncode
    receipt["elapsed_seconds"] = time.monotonic() - started
    receipt["log"] = record(log, output)
    receipt["source_bytes_preserved"] = all(record(sources / name)["sha256"] == expected
                                             for name, expected in SOURCE_HASHES.items())
    execution_path = output / "execution.json"
    if execution_path.is_file():
        receipt["execution_file"] = record(execution_path, output)
        execution = json.loads(execution_path.read_text())
        receipt["identity"] = execution["identity"]
        receipt["cases"] = execution["cases"]
        receipt["generated_files"] = execution["generated_files"]
        receipt["status"] = "passed" if (process.returncode == 0 and execution["status"] == "passed" and
                                           receipt["source_bytes_preserved"]) else "failed"
    else:
        receipt["status"] = "failed"
        receipt["reason"] = "no per-case observer receipt; module exit cannot establish individual results"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "returncode": process.returncode,
                      "cases": [{"id": case["id"], "status": case["status"]} for case in receipt.get("cases", [])],
                      "generated_files": len(receipt.get("generated_files", [])),
                      "receipt": str(receipt_path)}), flush=True)
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
