"""Keep original product/test flags while resolving genuine system dependencies."""
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
previous = evidence / "configure-with-native-libs.json"
dependency_receipt = evidence / "host-dependency-packages.json"
result_path = evidence / "configure-with-host-deps.json"
log_path = evidence / "configure-with-host-deps.log"
build = workspace / "runtime/product-native-configure-host-deps"
host = workspace / "runtime/product-host-deps/root"
if result_path.exists() or log_path.exists() or build.exists():
    raise RuntimeError("configuration output already exists; retain immutable attempts")


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


old = json.loads(previous.read_text())
dependencies = json.loads(dependency_receipt.read_text())
if dependencies.get("status") != "verified_extracted":
    raise RuntimeError("official host dependencies are not verified")
if dependencies["host_package_status_before"] != dependencies["host_package_status_after"]:
    raise RuntimeError("host package status unexpectedly changed")
command = list(old["command"])
command[command.index("-B") + 1] = str(build)
command.extend(["-DCMAKE_FIND_ROOT_PATH=" + str(host), "-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER",
                "-DPKG_CONFIG_EXECUTABLE=" + str(host / "usr/bin/pkgconf")])
overrides = dict(old["environment_overrides"])
overrides.update(
    LD_LIBRARY_PATH=overrides["LD_LIBRARY_PATH"] + ":" + str(host / "usr/lib/x86_64-linux-gnu"),
    PKG_CONFIG_SYSROOT_DIR=str(host),
    PKG_CONFIG_LIBDIR=":".join(str(host / relative) for relative in
                               ("usr/lib/x86_64-linux-gnu/pkgconfig", "usr/share/pkgconfig")),
)
environment = dict(os.environ)
environment.update(overrides)
now = lambda: datetime.now(timezone.utc).isoformat()
record = {"schema": 1, "source_commit": old["source_commit"], "command": command,
          "environment_overrides": overrides, "prior_configuration_receipt": identity(previous),
          "host_dependency_receipt": identity(dependency_receipt),
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
        destination = evidence / ("host-deps-" + Path(name).name)
        shutil.copyfile(path, destination)
        record.setdefault("generated_configuration_files", []).append(identity(destination))
result_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({key: record[key] for key in ("returncode", "configured", "tests_executed")}))
print(log_path.read_text()[-8000:])
raise SystemExit(process.returncode)
