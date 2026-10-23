"""Build selected original standalone GTest targets with bounded local resources."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
configuration = evidence / "configure-with-optix.json"
capture_root = repo / "compatibility/evidence/product-native-gtest-2026-10-23"
if capture_root.exists():
    raise RuntimeError("native build output already exists; retain immutable attempts")
capture_root.mkdir()
configured = json.loads(configuration.read_text())
if configured.get("configured") is not True:
    raise RuntimeError("product configuration is incomplete")
build = Path(configured["command"][configured["command"].index("-B") + 1])
environment = dict(os.environ)
environment.update(configured["environment_overrides"])
now = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def usage():
    return {"free_disk_bytes": shutil.disk_usage(build).free,
            "cgroup_memory_current": int(Path("/sys/fs/cgroup/memory.current").read_text()),
            "cgroup_memory_limit": int(Path("/sys/fs/cgroup/memory.max").read_text())}


targets = [("atomic_test", "intern/atomic"), ("guardedalloc_test", "intern/guardedalloc"),
           ("BLI_test", "source/blender/blenlib")]
for target, relative in targets:
    command = [str(workspace / "runtime/browser-python/bin/cmake"), "--build", str(build),
               "--target", target, "--parallel", "2"]
    log_path = capture_root / (target + "-build.log")
    record = {"schema": 1, "source_commit": configured["source_commit"], "target": target,
              "command": command, "environment_overrides": configured["environment_overrides"],
              "source_configuration_receipt": identity(configuration), "cache_before": identity(build / "CMakeCache.txt"),
              "resource_usage_before": usage(), "started_utc": now(), "parallel_jobs": 2,
              "maximum_elapsed_seconds": 1200, "minimum_free_disk_bytes": 4 * 1024 ** 3,
              "tests_executed": 0, "status": "pending", "termination_reason": None}
    started = time.monotonic()
    with log_path.open("wb") as log:
        process = subprocess.Popen(command, env=environment, cwd=repo, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        while process.poll() is None:
            if time.monotonic() - started > record["maximum_elapsed_seconds"]:
                record["termination_reason"] = "elapsed_time_limit"
            elif shutil.disk_usage(build).free < record["minimum_free_disk_bytes"]:
                record["termination_reason"] = "free_disk_limit"
            if record["termination_reason"]:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            time.sleep(1)
    artifact = build / "bin/tests" / target
    record.update(returncode=process.returncode, finished_utc=now(), elapsed_seconds=time.monotonic() - started,
                  resource_usage_after=usage(), log=identity(log_path), cache_after=identity(build / "CMakeCache.txt"))
    if process.returncode == 0 and artifact.is_file() and not record["termination_reason"]:
        record.update(status="built", artifact=identity(artifact))
    else:
        record["status"] = "build_failed_or_incomplete"
    generated = []
    target_directory = build / relative / "CMakeFiles" / (target + ".dir")
    for name in ("flags.make", "link.txt", "DependInfo.cmake", "build.make"):
        path = target_directory / name
        if path.is_file():
            generated.append({**identity(path), "content": path.read_text()})
    generated_path = capture_root / (target + "-build-rules.json")
    generated_path.write_text(json.dumps(generated, indent=2) + "\n")
    record["generated_target_rules"] = identity(generated_path)
    (capture_root / (target + "-build.json")).write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in ("target", "status", "returncode", "elapsed_seconds")}), flush=True)
    if record["status"] != "built":
        print(log_path.read_text()[-6000:], flush=True)
        raise SystemExit(1)
