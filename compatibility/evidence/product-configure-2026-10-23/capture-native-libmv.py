"""Capture every successfully built original LibMV CTest invocation once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
capture_root = repo / "compatibility/evidence/product-native-gtest-2026-10-23"
capture_script = evidence / "capture-native-gtest.py"
batch_path = capture_root / "libmv-capture-batch.json"
if batch_path.exists():
    raise RuntimeError("retain the original batch receipt")


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


build_receipts = sorted(capture_root.glob("libmv_*-build.json"))
if len(build_receipts) != 32:
    raise RuntimeError("expected exactly 32 completed LibMV target build receipts")
batch = {"schema": 1, "capture_script": identity(capture_script), "batch_script": identity(Path(__file__)),
         "started_utc": datetime.now(timezone.utc).isoformat(), "invocations": [],
         "browser_cases_executed": 0, "all_upstream_tests_enumerated": False}
for build_receipt in build_receipts:
    build = json.loads(build_receipt.read_text())
    target = build["target"]
    if build["status"] != "built" or build["returncode"] != 0 or not target.endswith("_test"):
        raise RuntimeError("original LibMV target was not built successfully")
    ctest_name = target.removesuffix("_test")
    command = [sys.executable, str(capture_script), ctest_name, target]
    stdout_path = capture_root / (ctest_name + "-capture.stdout.txt")
    stderr_path = capture_root / (ctest_name + "-capture.stderr.txt")
    if stdout_path.exists() or stderr_path.exists():
        raise RuntimeError("retain the original LibMV capture logs")
    item = {"ctest_name": ctest_name, "target": target, "command": command,
            "build_receipt": identity(build_receipt), "started_utc": datetime.now(timezone.utc).isoformat()}
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.run(command, cwd=repo, stdout=stdout, stderr=stderr)
    reference_path = capture_root / ctest_name / "native-reference.json"
    item.update(returncode=process.returncode, finished_utc=datetime.now(timezone.utc).isoformat(),
                stdout=identity(stdout_path), stderr=identity(stderr_path),
                native_reference=identity(reference_path) if reference_path.is_file() else None)
    batch["invocations"].append(item)
    batch_path.write_text(json.dumps(batch, indent=2) + "\n")
    print(json.dumps({"ctest_name": ctest_name, "capture_returncode": process.returncode,
                      "reference_created": reference_path.is_file()}), flush=True)
batch["finished_utc"] = datetime.now(timezone.utc).isoformat()
batch["all_captures_succeeded"] = all(item["returncode"] == 0 and item["native_reference"] is not None
                                       for item in batch["invocations"])
batch_path.write_text(json.dumps(batch, indent=2) + "\n")
raise SystemExit(0 if batch["all_captures_succeeded"] else 1)
