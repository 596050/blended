#!/usr/bin/env python3
"""Execute one additional original CTest driver with its registered command."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUNTIME = ROOT.parent / "runtime"
target = "script_validate_on_system_python"


def identity(path):
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def now():
    return datetime.now(timezone.utc).isoformat()


configuration = json.loads((OUT / "configure.json").read_bytes())
assert configuration["configured"] and configuration["returncode"] == 0
listing = json.loads((OUT / "ctest.json").read_bytes())
registrations = [row for row in listing["tests"] if row["name"] == target]
assert len(registrations) == 1
original = registrations[0]
command = [str(RUNTIME / "browser-python/bin/ctest"), "--test-dir",
           str(RUNTIME / "product-native-configure-expanded-tests"), "--build-config", "Release",
           "--tests-regex", "^" + target + "$", "--no-tests=error", "--output-on-failure",
           "--output-junit", str(OUT / "system-python-junit.xml")]
record = {
    "schema": 1, "kind": "selected-original-ctest-execution", "source_commit": configuration["source_commit"],
    "configuration": identity(OUT / "configure.json"), "ctest_listing": identity(OUT / "ctest.json"),
    "original_registration": original, "original_script": identity(Path(original["command"][1])),
    "command": command, "tool": identity(Path(__file__)), "started_utc": now(),
    "selected_registration_count": 1, "runtime_leaf_enumeration_complete": False,
    "browser_parity": False, "full_feature_parity": False,
    "scope": "Only this original system-Python driver is selected; a CTest success is not an inferred leaf-case count.",
}
environment = dict(os.environ)
environment.update(configuration["environment_overrides"])
record["environment_overrides"] = configuration["environment_overrides"]
with (OUT / "system-python.log").open("xb") as log:
    result = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=300)
record.update(finished_utc=now(), returncode=result.returncode, log=identity(OUT / "system-python.log"))
if (OUT / "system-python-junit.xml").is_file():
    record["ctest_junit"] = identity(OUT / "system-python-junit.xml")
with (OUT / "system-python-execution.json").open("x") as stream:
    stream.write(json.dumps(record, indent=2) + "\n")
print(json.dumps({"registration": target, "ctest_returncode": result.returncode,
                  "runtime_leaf_count": None, "browser_parity": False}))
raise SystemExit(result.returncode)
