#!/usr/bin/env python3
"""Capture additional original Linux test registrations in a fresh configuration."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUNTIME = ROOT.parent / "runtime"
sys.path.insert(0, str(ROOT))
from tools.test_registration_inventory import inventory_ctest


def identity(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest}


def write(path, data):
    with path.open("x") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


previous_path = ROOT / "compatibility/evidence/product-configure-2026-10-23/configure-with-optix.json"
previous = json.loads(previous_path.read_bytes())
assert previous["configured"] is True and previous["returncode"] == 0
build = RUNTIME / "product-native-configure-expanded-tests"
if build.exists() or (OUT / "configure.json").exists():
    raise RuntimeError("choose fresh output; previous configuration evidence is immutable")
flags = [
    "WITH_GPU_MESH_PAINT_TESTS", "WITH_GPU_RENDER_TESTS_VULKAN",
    "WITH_STORM_TESTS_VULKAN", "WITH_CYCLES_TEST_OSL", "WITH_TESTS_EXPERIMENTAL",
    "WITH_LINUX_OFFICIAL_RELEASE_TESTS", "WITH_SYSTEM_PYTHON_TESTS",
]
command = list(previous["command"])
command[command.index("-B") + 1] = str(build)
command.extend("-D" + flag + "=ON" for flag in flags)
system_python = Path("/usr/bin/python3").resolve(strict=True)
command.append("-DTEST_SYSTEM_PYTHON_EXE=" + str(system_python))
environment = dict(os.environ)
environment.update(previous["environment_overrides"])
record = {
    "schema": 1, "source_commit": previous["source_commit"], "command": command,
    "environment_overrides": previous["environment_overrides"],
    "base_configuration": identity(previous_path), "tool": identity(Path(__file__)),
    "additional_test_flags": flags, "system_python": identity(system_python),
    "feature_flags_disabled": [], "started_utc": now(), "finished_utc": None,
    "configured": False, "returncode": None, "tests_executed": 0,
    "runtime_enumeration_complete": False, "full_feature_parity": False,
    "scope": "Additional Linux Release test registration profile; other platforms, build modes, GPU devices and runtime leaves remain unqualified.",
}
with (OUT / "configure.log").open("xb") as stream:
    result = subprocess.run(command, cwd=ROOT, env=environment, stdout=stream,
                            stderr=subprocess.STDOUT, timeout=300)
record.update(returncode=result.returncode, configured=result.returncode == 0,
              finished_utc=now(), log=identity(OUT / "configure.log"))
for relative in ("CMakeCache.txt", "CMakeFiles/CMakeConfigureLog.yaml"):
    source = build / relative
    if source.is_file():
        target = OUT / source.name
        shutil.copyfile(source, target)
        record.setdefault("generated_files", []).append(identity(target))
write(OUT / "configure.json", record)
if result.returncode:
    print(json.dumps({"configured": False, "returncode": result.returncode, "log": str(OUT / "configure.log")}))
    raise SystemExit(result.returncode)

cache = OUT / "CMakeCache.txt"
cache_options = {}
for line in cache.read_text().splitlines():
    if line and not line.startswith(("#", "//")) and ":" in line and "=" in line:
        key, value = line.split("=", 1)
        name, kind = key.split(":", 1)
        cache_options[name] = {"type": kind, "value": value}
command = [str(RUNTIME / "browser-python/bin/ctest"), "--test-dir", str(build),
           "--show-only=json-v1", "--build-config", "Release"]
capture = {"argv": command, "started_utc": now(), "unfiltered_capture": True}
with (OUT / "ctest.json").open("xb") as stdout, (OUT / "ctest.stderr.txt").open("xb") as stderr:
    result = subprocess.run(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, timeout=120)
capture.update(returncode=result.returncode, finished_utc=now(), stdout=identity(OUT / "ctest.json"),
               stderr=identity(OUT / "ctest.stderr.txt"))
inventory = inventory_ctest((OUT / "ctest.json").read_text(), source_commit=record["source_commit"],
                            build_config_sha256=identity(cache)["sha256"], configuration="Release", provenance=capture)
write(OUT / "inventory.json", inventory)
generated = []
for path in sorted(build.rglob("CTestTestfile.cmake")):
    generated.append({**identity(path), "relative_path": path.relative_to(build).as_posix(),
                      "text": path.read_text()})
write(OUT / "generated-ctest-files.json", {"files": generated})
summary = {
    "schema": 1, "source_commit": record["source_commit"], "configuration": identity(OUT / "configure.json"),
    "cache": identity(cache), "capture": capture, "inventory": identity(OUT / "inventory.json"),
    "generated_registrations": identity(OUT / "generated-ctest-files.json"),
    "registration_count": len(inventory["registrations"]), "generated_file_count": len(generated),
    "requested_additional_test_options": {name: cache_options.get(name) for name in flags},
    "source_and_configuration_reconciliation_complete": False, "runtime_enumeration_complete": False,
    "tests_executed": 0, "full_feature_parity": False,
    "limitations": [
        "Registration commands are not leaf cases and have not been executed by this capture.",
        "This is one expanded Linux configuration, not every operating system, build mode or hardware device.",
        "Most registered executables are not built in this independent directory.",
        "Product fixture hydration is a separately recorded operation.",
    ],
}
write(OUT / "summary.json", summary)
print(json.dumps({"configured": True, "ctest_exit": result.returncode,
                  "registrations": summary["registration_count"], "tests_executed": 0}))
raise SystemExit(result.returncode)
