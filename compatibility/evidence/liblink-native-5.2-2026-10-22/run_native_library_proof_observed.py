#!/usr/bin/env python3
"""Run the unchanged complete liblink entrypoint in the exact official native executable."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[2]
PIN = "fbe6228777e7d9afefcd61a413844e790ae75db7"
BINARY = WORKSPACE / "research_tests/native_ref/blender-5.2.0-linux-x64/blender"
ARCHIVE = WORKSPACE / "research_tests/native_ref/blender-5.2.0-linux-x64.tar.xz"
EXPECTED_BINARY_SHA = "83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27"
EXPECTED_ARCHIVE_SHA = "96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48"
EXPECTED_ARCHIVE_BYTES = 384441228


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main():
    manifest_path = ROOT / "input-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["upstream"]["commit"] == PIN
    for row in manifest["sources"] + manifest["assets"]:
        assert fingerprint(ROOT / row["local_path"]) == {key: row[key] for key in ("bytes", "sha256")}
    binary_identity, archive_identity = fingerprint(BINARY), fingerprint(ARCHIVE)
    assert binary_identity["sha256"] == EXPECTED_BINARY_SHA
    assert archive_identity == {"bytes": EXPECTED_ARCHIVE_BYTES, "sha256": EXPECTED_ARCHIVE_SHA}
    output = ROOT / "native-proof"
    output.mkdir(exist_ok=False)
    observer = ROOT / "observe_blendfile_liblink.py"
    log_path = output / "native-library.log"
    result_path = output / "execution.json"
    flags = ["--background", "--factory-startup", "--threads", "1", "--disable-autoexec", "--python-exit-code", "1"]
    command = [str(BINARY), *flags, "--python", str(observer), "--", "--source-dir", str(ROOT / "sources"),
               "--fixture-dir", str(ROOT / "fixtures"), "--output-dir", str(output / "files"),
               "--report", str(result_path)]
    receipt = {"schema": 1, "status": "running", "upstream_commit": PIN,
               "native_archive": {"url": "https://download.blender.org/release/Blender5.2/blender-5.2.0-linux-x64.tar.xz", **archive_identity},
               "native_executable": {"path": str(BINARY), **binary_identity},
               "input_manifest": fingerprint(manifest_path), "observer": fingerprint(observer),
               "command": command, "timeout_seconds": 180, "expected_cases": 17,
               "browser_executed": False, "full_feature_parity": False}
    start = time.monotonic()
    try:
        with log_path.open("wb") as stream:
            process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                     timeout=180, check=False)
        receipt["process_returncode"] = process.returncode
    except subprocess.TimeoutExpired:
        receipt["timeout"] = True
        receipt["process_returncode"] = None
    receipt["elapsed_seconds"] = time.monotonic() - start
    receipt["log"] = fingerprint(log_path)
    if result_path.is_file():
        result = json.loads(result_path.read_text())
        receipt["execution"] = fingerprint(result_path)
        receipt["observed_cases"] = len(result["cases"])
        receipt["passed_cases"] = sum(row["status"] == "passed" for row in result["cases"])
        receipt["module_returned_normally"] = result["module_returned_normally"]
        receipt["generated_files"] = result["generated_files"]
        receipt["status"] = "passed" if receipt["process_returncode"] == 0 and result["status"] == "passed" else "failed"
    else:
        receipt["status"] = "blocked"
    (output / "native-library-proof.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt.get(key) for key in ("status", "expected_cases", "observed_cases", "passed_cases", "elapsed_seconds", "process_returncode")}))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
