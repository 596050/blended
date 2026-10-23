"""Build selected original standalone GTest targets with bounded local resources."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
configuration = evidence / "configure-with-optix.json"
capture_root = repo / "compatibility/evidence/product-native-gtest-2026-10-23"
capture_root.mkdir(exist_ok=True)
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


target_directories = {"atomic_test": "intern/atomic", "guardedalloc_test": "intern/guardedalloc",
                      "BLI_test": "source/blender/blenlib", "makesdna_test": "source/blender/makesdna/tests",
                      "shader_tool_test": "source/blender/gpu/shader_tool", "cycles_test": "intern/cycles/test"}
target_directories.update({'libmv_predict_tracks_test': 'intern/libmv', 'libmv_tracks_test': 'intern/libmv', 'libmv_scoped_ptr_test': 'intern/libmv', 'libmv_vector_test': 'intern/libmv', 'libmv_array_nd_test': 'intern/libmv', 'libmv_convolve_test': 'intern/libmv', 'libmv_image_test': 'intern/libmv', 'libmv_sample_test': 'intern/libmv', 'libmv_tuple_test': 'intern/libmv', 'libmv_euclidean_resection_test': 'intern/libmv', 'libmv_fundamental_test': 'intern/libmv', 'libmv_homography_test': 'intern/libmv', 'libmv_nviewtriangulation_test': 'intern/libmv', 'libmv_panography_test': 'intern/libmv', 'libmv_projection_test': 'intern/libmv', 'libmv_resection_test': 'intern/libmv', 'libmv_triangulation_test': 'intern/libmv', 'libmv_dogleg_test': 'intern/libmv', 'libmv_function_derivative_test': 'intern/libmv', 'libmv_levenberg_marquardt_test': 'intern/libmv', 'libmv_numeric_test': 'intern/libmv', 'libmv_poly_test': 'intern/libmv', 'libmv_camera_intrinsics_test': 'intern/libmv', 'libmv_detect_test': 'intern/libmv', 'libmv_intersect_test': 'intern/libmv', 'libmv_keyframe_selection_test': 'intern/libmv', 'libmv_modal_solver_test': 'intern/libmv', 'libmv_resect_test': 'intern/libmv', 'libmv_brute_region_tracker_test': 'intern/libmv', 'libmv_klt_region_tracker_test': 'intern/libmv', 'libmv_pyramid_region_tracker_test': 'intern/libmv', 'libmv_parallel_for_test': 'intern/libmv'})
selected = sys.argv[1:] or ['libmv_predict_tracks_test', 'libmv_tracks_test', 'libmv_scoped_ptr_test', 'libmv_vector_test', 'libmv_array_nd_test', 'libmv_convolve_test', 'libmv_image_test', 'libmv_sample_test', 'libmv_tuple_test', 'libmv_euclidean_resection_test', 'libmv_fundamental_test', 'libmv_homography_test', 'libmv_nviewtriangulation_test', 'libmv_panography_test', 'libmv_projection_test', 'libmv_resection_test', 'libmv_triangulation_test', 'libmv_dogleg_test', 'libmv_function_derivative_test', 'libmv_levenberg_marquardt_test', 'libmv_numeric_test', 'libmv_poly_test', 'libmv_camera_intrinsics_test', 'libmv_detect_test', 'libmv_intersect_test', 'libmv_keyframe_selection_test', 'libmv_modal_solver_test', 'libmv_resect_test', 'libmv_brute_region_tracker_test', 'libmv_klt_region_tracker_test', 'libmv_pyramid_region_tracker_test', 'libmv_parallel_for_test']
if len(set(selected)) != len(selected) or any(target not in target_directories for target in selected):
    raise ValueError("select distinct known original CMake targets")
targets = [(target, target_directories[target]) for target in selected]
for target, relative in targets:
    command = [str(workspace / "runtime/browser-python/bin/cmake"), "--build", str(build),
               "--target", target, "--parallel", "2"]
    log_path = capture_root / (target + "-build.log")
    if log_path.exists() or (capture_root / (target + "-build.json")).exists():
        raise RuntimeError("native target build output already exists; retain immutable attempts")
    record = {"schema": 1, "source_commit": configured["source_commit"], "target": target,
              "command": command, "environment_overrides": configured["environment_overrides"],
              "source_configuration_receipt": identity(configuration), "cache_before": identity(build / "CMakeCache.txt"),
              "resource_usage_before": usage(), "started_utc": now(), "parallel_jobs": 2,
              "maximum_elapsed_seconds": 1200, "minimum_free_disk_bytes": 4 * 1024 ** 3,
              "build_script": identity(Path(__file__)),
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
