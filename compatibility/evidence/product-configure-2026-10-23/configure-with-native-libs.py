"""Configure the exact product target with unchanged test flags and verified libraries."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


root = Path(__file__).resolve().parent
repo = root.parents[2]
workspace = repo.parent
previous = root / "configure-with-gcc14.json"
hydration = root / "native-library-hydration.json"
result_path = root / "configure-with-native-libs.json"
log_path = root / "configure-with-native-libs.log"
build = workspace / "runtime/product-native-configure-full"
if result_path.exists() or log_path.exists() or build.exists():
    raise RuntimeError("configuration output already exists; use a new immutable attempt")


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


old = json.loads(previous.read_text())
verified = json.loads(hydration.read_text())
if verified.get("status") != "verified" or verified.get("source_commit") != old["source_commit"]:
    raise RuntimeError("required exact native library hydration is not verified")
command = list(old["command"])
command[command.index("-B") + 1] = str(build)
command.append("-DLIBDIR=" + str(workspace / "runtime/product-native-libs/linux_x64"))
environment = dict(os.environ)
environment.update(old["environment_overrides"])
now = lambda: datetime.now(timezone.utc).isoformat()
record = {"schema": 1, "source_commit": old["source_commit"], "command": command,
          "environment_overrides": old["environment_overrides"],
          "prior_configuration_receipt": identity(previous), "library_hydration_receipt": identity(hydration),
          "test_flags_preserved": [value for value in command if value.startswith("-DWITH_")],
          "feature_flags_disabled_for_configuration": [], "started_utc": now(), "finished_utc": None,
          "returncode": None, "configured": False, "tests_executed": 0,
          "runtime_enumeration_complete": False}
with log_path.open("wb") as log:
    process = subprocess.run(command, env=environment, cwd=repo, stdout=log, stderr=subprocess.STDOUT)
record.update(returncode=process.returncode, configured=process.returncode == 0, finished_utc=now(), log=identity(log_path))
for name in ["CMakeCache.txt", "CMakeFiles/CMakeConfigureLog.yaml"]:
    path = build / name
    if path.is_file():
        destination = root / ("native-libs-" + Path(name).name)
        shutil.copyfile(path, destination)
        record.setdefault("generated_configuration_files", []).append(identity(destination))
result_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({key: record[key] for key in ("returncode", "configured", "tests_executed")}))
print(log_path.read_text()[-6000:])
raise SystemExit(process.returncode)
