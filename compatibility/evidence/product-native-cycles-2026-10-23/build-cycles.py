"""Build the original cycles_test target within the approved initial resource bound."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


directory = Path(__file__).resolve().parent
repo = directory.parents[2]
workspace = repo.parent
assessment_path = repo / "compatibility/evidence/product-native-gtest-2026-10-23/remaining-build-assessment.json"
configuration_path = repo / "compatibility/evidence/product-configure-2026-10-23/configure-with-optix.json"
assessment = json.loads(assessment_path.read_text())
configuration = json.loads(configuration_path.read_text())
build = Path(assessment["build_directory"])
target = assessment["targets"]["cycles_test"]
log_path = directory / "build.log"
samples_path = directory / "resource-samples.jsonl"
receipt_path = directory / "build.json"
if any(path.exists() for path in (log_path, samples_path, receipt_path)):
    raise RuntimeError("retain the original bounded Cycles build attempt")
now = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def numeric_fields(path):
    return {key: int(value) for key, value in (line.split() for line in path.read_text().splitlines())}


def usage(group=None):
    memory = numeric_fields(Path("/sys/fs/cgroup/memory.stat"))
    events = numeric_fields(Path("/sys/fs/cgroup/memory.events"))
    rss, members = 0, []
    if group is not None:
        for candidate in Path("/proc").iterdir():
            if not candidate.name.isdigit():
                continue
            try:
                raw = (candidate / "stat").read_text()
                fields = raw[raw.rindex(")") + 2:].split()
                if int(fields[2]) == group:
                    resident = int(fields[21]) * os.sysconf("SC_PAGE_SIZE")
                    rss += resident
                    members.append({"pid": int(candidate.name), "rss_bytes": resident,
                                    "command": raw[raw.index("(") + 1:raw.rindex(")")]})
            except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
                continue
    return {"time_utc": now(), "free_disk_bytes": shutil.disk_usage(build).free,
            "cgroup_memory_current_bytes": int(Path("/sys/fs/cgroup/memory.current").read_text()),
            "cgroup_memory_limit_bytes": int(Path("/sys/fs/cgroup/memory.max").read_text()),
            "cgroup_memory_anon_bytes": memory.get("anon", 0),
            "cgroup_memory_file_bytes": memory.get("file", 0),
            "cgroup_memory_kernel_bytes": memory.get("kernel", 0),
            "cgroup_memory_sock_bytes": memory.get("sock", 0),
            "cgroup_memory_events": events, "build_process_group_rss_bytes": rss,
            "build_process_group_members": members}


if identity(assessment_path)["sha256"] != "100c2593c5f41e3cf88d108957f9c16691ca754ce0d3b5fd242790c3a8a4f3f0":
    raise RuntimeError("original build assessment changed")
if identity(build / "CMakeCache.txt") != assessment["build_config"]:
    raise RuntimeError("original configured CMake cache changed")
if identity(configuration_path) != assessment["configuration_receipt"]:
    raise RuntimeError("original configuration receipt changed")
if configuration["source_commit"] != "94363991e7dcf39e2d70614aa002ab6f67764a5d":
    raise RuntimeError("unexpected original source commit")
environment = dict(os.environ)
environment.update(configuration["environment_overrides"])
command = target["suggested_command_not_executed"]
if command[-4:] != ["--target", "cycles_test", "--parallel", "1"]:
    raise RuntimeError("expected original cycles_test target and one compiler job")
before = usage()
if before["cgroup_memory_limit_bytes"] > 8 * 1024 ** 3:
    raise RuntimeError("memory cap exceeds the approved 8 GiB bound")
if before["free_disk_bytes"] < 4 * 1024 ** 3:
    raise RuntimeError("free disk is below the required reserve")
record = {
    "schema": 1, "source_commit": configuration["source_commit"], "target": "cycles_test",
    "repository_checkpoint": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
    "command": command, "cwd": str(repo), "environment_overrides": configuration["environment_overrides"],
    "influential_environment": {key: environment[key] for key in
                               ("PATH", "LD_LIBRARY_PATH", "CC", "CXX", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS",
                                "MAKEFLAGS", "CMAKE_BUILD_PARALLEL_LEVEL", "PKG_CONFIG_SYSROOT_DIR", "PKG_CONFIG_LIBDIR")
                               if key in environment},
    "source_configuration_receipt": identity(configuration_path), "build_assessment": identity(assessment_path),
    "cache_before": identity(build / "CMakeCache.txt"), "build_script": identity(Path(__file__)),
    "started_utc": now(), "parallel_jobs": 1, "maximum_elapsed_seconds": 1200,
    "minimum_free_disk_bytes": 4 * 1024 ** 3, "cgroup_memory_limit_bytes": before["cgroup_memory_limit_bytes"],
    "maximum_build_process_group_rss_bytes": 6 * 1024 ** 3,
    "maximum_non_file_memory_bytes": 7 * 1024 ** 3,
    "memory_policy": "Existing 8 GiB cgroup cap; stop on OOM event, 6 GiB build-group RSS, or 7 GiB anon+kernel+socket memory. File cache alone is not an OOM signal.",
    "resource_usage_before": before, "termination_reason": None,
    "tests_executed": 0, "test_passes": 0, "browser_cases_executed": 0,
}
peak_rss = peak_anon = peak_current = 0
started = time.monotonic()
with log_path.open("xb") as log, samples_path.open("x") as samples:
    process = subprocess.Popen(command, env=environment, cwd=repo, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    while process.poll() is None:
        observed = usage(process.pid)
        samples.write(json.dumps(observed, sort_keys=True) + "\n")
        samples.flush()
        peak_rss = max(peak_rss, observed["build_process_group_rss_bytes"])
        peak_anon = max(peak_anon, observed["cgroup_memory_anon_bytes"])
        peak_current = max(peak_current, observed["cgroup_memory_current_bytes"])
        non_file = sum(observed[key] for key in ("cgroup_memory_anon_bytes", "cgroup_memory_kernel_bytes", "cgroup_memory_sock_bytes"))
        if time.monotonic() - started > record["maximum_elapsed_seconds"]:
            record["termination_reason"] = "elapsed_time_limit"
        elif observed["free_disk_bytes"] < record["minimum_free_disk_bytes"]:
            record["termination_reason"] = "free_disk_limit"
        elif any(observed["cgroup_memory_events"].get(key, 0) > before["cgroup_memory_events"].get(key, 0)
                 for key in ("oom", "oom_kill", "oom_group_kill")):
            record["termination_reason"] = "cgroup_oom_event"
        elif observed["build_process_group_rss_bytes"] > record["maximum_build_process_group_rss_bytes"]:
            record["termination_reason"] = "build_process_group_memory_margin"
        elif non_file > record["maximum_non_file_memory_bytes"]:
            record["termination_reason"] = "cgroup_non_file_memory_margin"
        if record["termination_reason"]:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            break
        time.sleep(1)
record.update(returncode=process.returncode, finished_utc=now(), elapsed_seconds=time.monotonic() - started,
              resource_usage_after=usage(), peak_sampled_build_group_rss_bytes=peak_rss,
              peak_sampled_cgroup_anon_bytes=peak_anon, peak_sampled_cgroup_memory_current_bytes=peak_current,
              log=identity(log_path), resource_samples=identity(samples_path),
              cache_after=identity(build / "CMakeCache.txt"))
artifact = build / "bin/tests/cycles_test"
cache_unchanged = record["cache_before"] == record["cache_after"]
if process.returncode == 0 and not record["termination_reason"] and artifact.is_file() and cache_unchanged:
    record.update(status="built", artifact=identity(artifact))
else:
    record["status"] = "build_failed_or_incomplete"
record["configuration_unchanged"] = cache_unchanged
generated = []
target_directory = build / "intern/cycles/test/CMakeFiles/cycles_test.dir"
for name in ("flags.make", "link.txt", "DependInfo.cmake", "build.make"):
    path = target_directory / name
    if path.is_file():
        generated.append({**identity(path), "content": path.read_text()})
rules_path = directory / "generated-target-rules.json"
with rules_path.open("x") as stream:
    json.dump(generated, stream, indent=2)
    stream.write("\n")
record["generated_target_rules"] = identity(rules_path)
with receipt_path.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps({key: record[key] for key in
                  ("target", "status", "returncode", "elapsed_seconds", "termination_reason",
                   "peak_sampled_build_group_rss_bytes", "configuration_unchanged")}, indent=2))
raise SystemExit(0 if record["status"] == "built" else 1)
