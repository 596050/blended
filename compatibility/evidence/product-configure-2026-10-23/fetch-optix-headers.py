"""Fetch NVIDIA's official minimal OptiX 8.0 headers, preserving the enabled backend."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2].parent
destination = workspace / "runtime/product-optix-8.0.0"
result_path = evidence / "optix-headers.json"
log_path = evidence / "optix-headers.log"
if result_path.exists() or log_path.exists() or destination.exists():
    raise RuntimeError("OptiX fetch output already exists; retain immutable attempts")


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


now = lambda: datetime.now(timezone.utc).isoformat()
command = ["git", "clone", "--depth", "1", "--branch", "v8.0.0",
           "https://github.com/NVIDIA/optix-dev.git", str(destination)]
record = {"schema": 1, "command": command, "started_utc": now(),
          "repository": "https://github.com/NVIDIA/optix-dev", "tag": "v8.0.0",
          "purpose": "official headers for the product source's OptiX>=8.0.0 requirement",
          "tests_executed": 0, "runtime_gpu_support_verified": False}
with log_path.open("wb") as log:
    process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
record.update(returncode=process.returncode, finished_utc=now(), log=identity(log_path))
if process.returncode == 0:
    record["commit"] = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
    record["files"] = [identity(path) for path in sorted(destination.rglob("*"))
                       if path.is_file() and ".git" not in path.relative_to(destination).parts]
    record["optix_version_define"] = [line for line in (destination / "include/optix.h").read_text().splitlines()
                                      if line.startswith("#define OPTIX_VERSION ")]
    record["git_status"] = subprocess.check_output(["git", "-C", str(destination), "status", "--short"], text=True)
result_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({key: record.get(key) for key in ("returncode", "commit", "optix_version_define")}))
raise SystemExit(process.returncode)
