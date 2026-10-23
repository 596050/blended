"""Capture actual unbuilt CTest registrations without treating them as leaf cases."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
configuration = evidence / "configure-with-optix.json"
capture_root = repo / "compatibility/evidence/product-ctest-configured-2026-10-23"
if capture_root.exists():
    raise RuntimeError("CTest capture already exists; retain immutable attempts")
capture_root.mkdir()
sys.path.insert(0, str(repo))
from tools.test_registration_inventory import inventory_ctest


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


configured = json.loads(configuration.read_text())
if configured.get("configured") is not True or configured.get("returncode") != 0:
    raise RuntimeError("product configuration did not succeed")
build = Path(configured["command"][configured["command"].index("-B") + 1])
cache = build / "CMakeCache.txt"
build_config_sha256 = identity(cache)["sha256"]
environment = dict(os.environ)
environment.update(configured["environment_overrides"])
command = [str(workspace / "runtime/browser-python/bin/ctest"), "--test-dir", str(build),
           "--show-only=json-v1", "--build-config", "Release"]
stdout_path = capture_root / "ctest.json"
stderr_path = capture_root / "ctest.stderr.txt"
now = lambda: datetime.now(timezone.utc).isoformat()
started = now()
with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
    process = subprocess.run(command, env=environment, cwd=repo, stdout=stdout, stderr=stderr)
provenance = {"argv": command, "returncode": process.returncode, "started_utc": started,
              "finished_utc": now(), "source_configuration_receipt": identity(configuration),
              "unfiltered_capture": True, "compiled_test_executables": False,
              "stdout": identity(stdout_path), "stderr": identity(stderr_path)}
if process.returncode:
    (capture_root / "failed-capture.json").write_text(json.dumps(provenance, indent=2) + "\n")
    raise SystemExit(process.returncode)
inventory = inventory_ctest(stdout_path.read_text(), source_commit=configured["source_commit"],
                            build_config_sha256=build_config_sha256, configuration="Release", provenance=provenance)
inventory_path = capture_root / "ctest-registration-inventory.json"
inventory_path.write_text(json.dumps(inventory, indent=2) + "\n")
generated = []
for path in sorted(build.rglob("CTestTestfile.cmake")):
    generated.append({"relative_path": str(path.relative_to(build)), **identity(path), "content": path.read_text()})
generated_path = capture_root / "generated-ctest-files.json"
generated_path.write_text(json.dumps(generated, indent=2) + "\n")
cache_values = {}
for line in cache.read_text().splitlines():
    if line.startswith(("#", "//")) or "=" not in line or ":" not in line.split("=", 1)[0]:
        continue
    key_type, value = line.split("=", 1)
    name, value_type = key_type.split(":", 1)
    cache_values[name] = {"type": value_type, "value": value}
summary = {
    "schema": 1, "source_commit": configured["source_commit"], "source_configuration_receipt": identity(configuration),
    "build_directory": str(build), "cache": identity(cache), "build_config_sha256": build_config_sha256,
    "capture": provenance, "inventory": identity(inventory_path), "generated_registrations": identity(generated_path),
    "configured_ctest_registration_count": len(inventory["registrations"]),
    "generated_ctest_file_count": len(generated),
    "commands_unavailable_before_compilation": sum(item["command_status"] == "unavailable"
                                                   for item in inventory["registrations"]),
    "disabled_registration_count": sum(item["disabled"] is True for item in inventory["registrations"]),
    "configuration_options": {name: value for name, value in cache_values.items()
                              if name.startswith("WITH_") or name in ("CYCLES_TEST_DEVICES", "TEST_SYSTEM_PYTHON_EXE")},
    "tests_executed": 0, "runtime_leaf_cases_discovered": 0,
    "registration_enumeration_complete": False, "runtime_enumeration_complete": False,
    "full_feature_parity": False,
    "limitations": [
        "CTest driver registrations are not expanded GoogleTest/Python/custom-driver cases.",
        "This capture describes one exact Release configuration, not every supported configuration.",
        "Source registration and feature/configuration reconciliation remains required.",
        "The source test asset directories exist, but their exact LFS payloads were not yet fully hydrated at capture.",
        "Optional mesh-paint, Vulkan render, Cycles OSL, experimental, Linux release and system-Python test flags remain at upstream defaults.",
        "Platform/backend-specific runtime cases require additional supported configurations and hardware profiles.",
    ],
}
(capture_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({key: summary[key] for key in ("configured_ctest_registration_count", "generated_ctest_file_count",
                                               "commands_unavailable_before_compilation", "tests_executed")}))
