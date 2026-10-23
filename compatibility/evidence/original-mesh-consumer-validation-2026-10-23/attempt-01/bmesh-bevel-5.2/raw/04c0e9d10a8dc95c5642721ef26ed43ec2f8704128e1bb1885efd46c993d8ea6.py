#!/usr/bin/env python3
"""Repeat the identical original invocation in the authorized local environment."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import time


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "bmesh-bevel-source-native-5.2-2026-10-23"
spec = importlib.util.spec_from_file_location("frozen_bevel_capture", ORIGINAL / "run-native.py")
original_capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original_capture)
identity = original_capture.identity
write_new = original_capture.write_new


def main():
    if (HERE / "prospective-command.json").exists():
        raise FileExistsError("this retry already started")
    first_path = ORIGINAL / "execution.json"
    first = json.loads(first_path.read_text())
    first_plan_path = ORIGINAL / "prospective-command.json"
    previous = json.loads(first_plan_path.read_text())
    assert first["timed_out"] and not first["completed_successfully"]
    assert identity(first_plan_path) == first["prospective_command"]
    assert identity(ORIGINAL / "run-native.py") == previous["capture_driver"]
    assert identity(Path(previous["native_executable"]["path"])) == previous["native_executable"]
    for entry in previous["inputs"]:
        assert identity(Path(entry["path"])) == entry
    env = os.environ.copy()
    if "BLENDER_TEST_UPDATE" in env:
        raise ValueError("original oracle update environment must remain absent")
    env.update(previous["environment_overrides"])
    prospective = {
        "schema": 1, "kind": "source-derived-original-blender-invocation-elevated-retry",
        "capture_driver": identity(Path(__file__).resolve()), "reused_capture_helper": identity(ORIGINAL / "run-native.py"),
        "original_attempt": identity(first_path), "original_prospective_command": identity(first_plan_path),
        "command": previous["command"], "cwd": previous["cwd"],
        "environment_overrides": previous["environment_overrides"],
        "environment_distinction": "Authorized elevated local execution; original attempt ran under the default restricted sandbox.",
        "reason": "All original case markers appeared, but the first process failed to exit after PulseAudio reported Operation not permitted and reached its 180-second timeout.",
        "original_argv_unchanged": True, "source_fixture_and_executable_identities_unchanged": True,
        "oracle_update_environment_absent": True,
        "verbose_environment_present": "BLENDER_VERBOSE" in env,
        "timeout_seconds": previous["timeout_seconds"], "minimum_disk_reserve_bytes": previous["minimum_disk_reserve_bytes"],
        "source_commit": previous["source_commit"], "inputs": previous["inputs"],
        "configured_ctest_execution": False, "browser_test_passes": 0, "full_feature_parity": False,
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    assert prospective["verbose_environment_present"] == previous["verbose_environment_present"]
    write_new(HERE / "prospective-command.json", prospective)
    if shutil.disk_usage(HERE).free < prospective["minimum_disk_reserve_bytes"]:
        raise RuntimeError("insufficient disk reserve")
    started = time.monotonic()
    peak_rss_kib, peak_threads, timed_out, termination = 0, 0, False, None
    sampled_procfs_identity_verified = False
    with (HERE / "original-driver.log").open("xb") as log:
        process = subprocess.Popen(prospective["command"], cwd=prospective["cwd"], env=env,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        while process.poll() is None:
            try:
                procfs_command = Path(f"/proc/{process.pid}/cmdline").read_bytes().split(b"\0")
                if procfs_command and procfs_command[-1] == b"":
                    procfs_command.pop()
                if procfs_command != [argument.encode() for argument in prospective["command"]]:
                    raise ProcessLookupError("procfs PID does not identify the actual Blender child")
                sampled_procfs_identity_verified = True
                status = Path(f"/proc/{process.pid}/status").read_text()
                rss = re.search(r"^VmRSS:\s+(\d+) kB$", status, re.M)
                threads = re.search(r"^Threads:\s+(\d+)$", status, re.M)
                peak_rss_kib = max(peak_rss_kib, int(rss[1]) if rss else 0)
                peak_threads = max(peak_threads, int(threads[1]) if threads else 0)
            except (FileNotFoundError, ProcessLookupError):
                pass
            if time.monotonic() - started >= prospective["timeout_seconds"]:
                timed_out, termination = True, "180-second timeout"
            elif shutil.disk_usage(HERE).free < prospective["minimum_disk_reserve_bytes"]:
                termination = "minimum disk reserve reached"
            if termination:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                break
            time.sleep(0.1)
        returncode = process.wait()
    observations = original_capture.original_observations((HERE / "original-driver.log").read_text(errors="replace"), previous["static_declared_specs"])
    after = [identity(Path(entry["path"])) for entry in previous["inputs"]]
    unchanged = after == previous["inputs"]
    completed = (returncode == 0 and not timed_out and termination is None and unchanged
                 and not observations["duplicate_names"] and not observations["missing_declared_names"]
                 and not observations["unexpected_names"] and observations["observed_starts"] > 0
                 and observations["observed_passes"] == observations["observed_starts"])
    report = {
        "schema": 1, "kind": "source-derived-original-blender-native-execution-elevated-retry",
        "prospective_command": identity(HERE / "prospective-command.json"),
        "capture_driver": identity(Path(__file__).resolve()), "reused_capture_helper": identity(ORIGINAL / "run-native.py"),
        "original_attempt_preserved": identity(first_path), "native_executable": previous["native_executable"],
        "source_commit": previous["source_commit"], "ctest_name_from_source": "bmesh_bevel",
        "configured_ctest_execution": False, "actual_process_started": True, "actual_process_returncode": returncode,
        "timed_out": timed_out, "termination_reason": termination,
        "elapsed_seconds": round(time.monotonic() - started, 6), "finished_utc": datetime.now(timezone.utc).isoformat(),
        "sampled_process_peak_rss_kib": peak_rss_kib if sampled_procfs_identity_verified else None,
        "sampled_process_peak_thread_count": peak_threads if sampled_procfs_identity_verified else None,
        "sampled_procfs_identity_verified": sampled_procfs_identity_verified,
        "child_max_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "raw_log": identity(HERE / "original-driver.log"), "original_case_observations": observations,
        "inputs_after": after, "all_original_inputs_unchanged": unchanged, "completed_successfully": completed,
        "original_blender_invocations_executed": 1, "browser_tests_executed": False, "browser_test_passes": 0,
        "full_feature_parity": False,
        "scope": "An original source-derived CPU bevel invocation in an authorized elevated local environment; not configured CTest or browser qualification.",
    }
    write_new(HERE / "execution.json", report)
    print(json.dumps({key: report[key] for key in ("actual_process_returncode", "timed_out", "elapsed_seconds",
                     "sampled_process_peak_rss_kib", "sampled_process_peak_thread_count", "all_original_inputs_unchanged", "completed_successfully")}, indent=2))
    print(json.dumps({key: value for key, value in observations.items() if key != "observations"}, indent=2))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
