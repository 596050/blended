"""Run the unchanged four-case brush invocation with a verified package overlay."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


root = Path(__file__).resolve().parent
repo = root.parents[2]
workspace = repo.parent
output = root / "bl_brush-local-server"
output.mkdir(exist_ok=False)
command = [
    sys.executable, str(root / "harness/tools/probe_browser_port.py"),
    "--asset", str(workspace / "runtime/brush-package-overlay-5.2/blender-source-development-essentials.tar.gz"),
    "--source-build-receipt", str(root / "base-source-build.json"),
    "--package-overlay-receipt", str(root / "package-overlay.json"),
    "--package-base-asset", str(workspace / "runtime/source/blender-source-development.tar.gz"),
    "--suite-manifest", str(repo / "compatibility/candidate-suites/unittest-main-5.2/bl_brush.json"),
    "--suite-manifest-sha256", "9f82a905c156ac80df0a689ea0a8c2a7961eb69ea651af68b4a7a5ed1bb24f73",
    "--suite", str(workspace / "runtime/upstream-5.2/tests/python/sculpt_paint/brush_asset_test.py"),
    "--browser-executable", str(workspace / "runtime/chrome/chrome-linux64/chrome"),
    "--timeout", "240", "--output", str(output),
]
now = lambda: datetime.now(timezone.utc).isoformat()
record = {"schema": 1, "started_utc": now(), "command": command, "timed_out": False,
          "returncode": None, "timeout_seconds": 360,
          "scope": "Original four-case brush invocation on separately identified original-resource augmented package"}
with (output / "host-process.log").open("wb") as log:
    process = subprocess.Popen(command, cwd=repo, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        record["returncode"] = process.wait(timeout=360)
    except subprocess.TimeoutExpired:
        record["timed_out"] = True
        os.killpg(process.pid, signal.SIGKILL)
        record["returncode"] = process.wait()
record["finished_utc"] = now()
path = output / "host-process.log"
record["log"] = {"path": path.name, "bytes": path.stat().st_size,
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
(output / "host-process.json").write_text(json.dumps(record, indent=2) + "\n")
path = output / "qualification.json"
report = json.loads(path.read_text()) if path.is_file() else {}
print(json.dumps({"returncode": record["returncode"], "status": report.get("status"),
                  "totals": (report.get("summary") or {}).get("totals"), "reason": report.get("reason"),
                  "evidence": str(path)}, indent=2))
raise SystemExit(record["returncode"])
