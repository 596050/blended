"""Retry the exact strict product configuration with official OptiX headers."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
previous = evidence / "configure-with-host-deps.json"
optix_receipt = evidence / "optix-headers.json"
result_path = evidence / "configure-with-optix.json"
log_path = evidence / "configure-with-optix.log"
build = workspace / "runtime/product-native-configure-optix"
if result_path.exists() or log_path.exists() or build.exists():
    raise RuntimeError("configuration output already exists; retain immutable attempts")


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


old = json.loads(previous.read_text())
optix = json.loads(optix_receipt.read_text())
if optix.get("returncode") != 0 or optix.get("commit") != "f60c1e44f18426f426a2ed948f28515b3cf67b8a":
    raise RuntimeError("official OptiX headers are not pinned")
command = list(old["command"])
command[command.index("-B") + 1] = str(build)
command.append("-DOPTIX_ROOT_DIR=" + str(workspace / "runtime/product-optix-8.0.0"))
environment = dict(os.environ)
environment.update(old["environment_overrides"])
now = lambda: datetime.now(timezone.utc).isoformat()
record = {"schema": 1, "source_commit": old["source_commit"], "command": command,
          "environment_overrides": old["environment_overrides"], "prior_configuration_receipt": identity(previous),
          "optix_header_receipt": identity(optix_receipt),
          "test_flags_preserved": [value for value in command if value.startswith("-DWITH_")],
          "feature_flags_disabled_for_configuration": [], "started_utc": now(), "finished_utc": None,
          "returncode": None, "configured": False, "tests_executed": 0,
          "runtime_enumeration_complete": False}
with log_path.open("wb") as log:
    process = subprocess.run(command, env=environment, cwd=repo, stdout=log, stderr=subprocess.STDOUT)
record.update(returncode=process.returncode, configured=process.returncode == 0, finished_utc=now(), log=identity(log_path))
for name in ("CMakeCache.txt", "CMakeFiles/CMakeConfigureLog.yaml"):
    path = build / name
    if path.is_file():
        destination = evidence / ("optix-" + Path(name).name)
        shutil.copyfile(path, destination)
        record.setdefault("generated_configuration_files", []).append(identity(destination))
result_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({key: record[key] for key in ("returncode", "configured", "tests_executed")}))
print(log_path.read_text()[-8000:])
raise SystemExit(process.returncode)
