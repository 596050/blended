#!/usr/bin/env python3
"""Record patch regressions and a real static codec package/runtime diagnostic."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def identity(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    package = repo / "patches/browser-codecs"
    work, sdk, output = args.work.resolve(), args.sdk.resolve(), args.output.resolve()
    assert not output.exists()
    output.mkdir(parents=True)
    shutil.copyfile(Path(__file__).resolve(), output / "executed-runner.py")
    shutil.copytree(package, output / "package", ignore=shutil.ignore_patterns("__pycache__"))
    prefix = work / "gessa/lib/wasm"
    source = output / "cmake-source"
    source.mkdir()
    shutil.copyfile(package / "codec_probe.cpp", source / "codec_probe.cpp")
    cmake = """cmake_minimum_required(VERSION 3.20)
project(OriginalCodecDependencyDiagnostic LANGUAGES C CXX)
find_package(Threads REQUIRED)
set(WITH_IMAGE_CINEON ON)
set(WITH_IMAGE_OPENJPEG ON)
set(WITH_IMAGE_WEBP ON)
list(PREPEND CMAKE_MODULE_PATH "@MODULES@")
include("@FRAGMENT@")
if(NOT WEBP_FOUND OR NOT OPENJPEG_FOUND)
  message(FATAL_ERROR "Original Blender codec modules did not resolve")
endif()
add_executable(codec_probe codec_probe.cpp)
target_compile_features(codec_probe PRIVATE cxx_std_17)
target_compile_options(codec_probe PRIVATE -pthread -fexceptions)
target_link_libraries(codec_probe PRIVATE WebP::webp WebP::webpdemux WebP::libwebpmux WebP::sharpyuv openjp2 heif)
target_link_options(codec_probe PRIVATE -pthread -fexceptions -sNODERAWFS -sEXIT_RUNTIME=1 -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=67108864 -sPTHREAD_POOL_SIZE=2 -sPROXY_TO_PTHREAD -sSTACK_SIZE=8388608)
""".replace("@MODULES@", str(evidence / "sources/blender/build_files/cmake/Modules")).replace("@FRAGMENT@", str(package / "image_codecs.cmake"))
    (source / "CMakeLists.txt").write_text(cmake)
    build = work / output.name / "build"
    run_directory = work / output.name / "runtime"
    run_directory.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "CC", "CXX", "AR", "RANLIB"):
        environment.pop(key, None)
    node = sdk / "node/22.16.0_64bit/bin/node"
    environment.update(EM_CACHE=str(work / "emscripten-cache"), EMSDK_PYTHON=sys.executable,
                       EMCC_CORES="1", CMAKE_BUILD_PARALLEL_LEVEL="1", MAKEFLAGS="-j1",
                       PYTHONDONTWRITEBYTECODE="1", EMSDK_QUIET="1")
    host_tools = repo.parent / "runtime/browser-python/bin"
    environment["PATH"] = os.pathsep.join((str(sdk / "upstream/emscripten"), str(node.parent), str(host_tools), environment["PATH"]))
    report = {"schema": 1, "kind": "browser-codec-patch-and-dependency-validation", "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(), "runner": identity(Path(__file__).resolve()),
              "manifest": identity(package / "manifest.json"), "compiler": identity(sdk / "upstream/bin/clang"),
              "node": identity(node), "jobs": 1, "cache": environment["EM_CACHE"],
              "libraries_before": [identity(p) for p in sorted((prefix / "lib").glob("*.a"))],
              "commands": [], "blender_cases_executed": 0, "full_feature_parity": False,
              "limit": "Patch integrity regressions, static package import and a standalone Node/Wasm codec diagnostic. These are not original Blender cases or browser application results."}

    def save():
        (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv, cwd, expected=0, timeout=180):
        row = {"name": name, "argv": [str(v) for v in argv], "cwd": str(cwd),
               "started_at": datetime.now(timezone.utc).isoformat(), "expected_returncode": expected}
        report["commands"].append(row)
        save()
        log = output / (name + ".log")
        start = time.monotonic()
        with log.open("wb") as stream:
            try:
                result = subprocess.run(argv, cwd=cwd, env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
                row.update(returncode=result.returncode, timed_out=False)
            except subprocess.TimeoutExpired:
                row.update(returncode=None, timed_out=True)
        row.update(completed_at=datetime.now(timezone.utc).isoformat(), duration_seconds=round(time.monotonic() - start, 6), log=identity(log))
        save()
        print(json.dumps({"name": name, "returncode": row["returncode"], "timed_out": row["timed_out"]}), flush=True)
        if row["timed_out"] or row["returncode"] != expected:
            raise RuntimeError("Unexpected command outcome: " + name)

    try:
        run("patch-regressions", [sys.executable, package / "test_patch.py"], repo)
        run("shell-syntax", ["bash", "-n", package / "recipes/codec-common.sh"], repo)
        run("configure", [sdk / "upstream/emscripten/emcmake", host_tools / "cmake", "-S", source, "-B", build,
                          "-G", "Unix Makefiles", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_C_FLAGS=-pthread -fexceptions",
                          "-DCMAKE_CXX_FLAGS=-pthread -fexceptions", "-DLIBDIR=" + str(prefix)], repo)
        run("link", [host_tools / "cmake", "--build", build, "--parallel", "1"], repo)
        run("runtime", [node, build / "codec_probe.js"], run_directory)
        report["runtime_outputs"] = [identity(p) for p in sorted(run_directory.iterdir()) if p.is_file()]
        report["binaries"] = [identity(p) for p in (build / "codec_probe.js", build / "codec_probe.wasm")]
        report["libraries_after"] = [identity(p) for p in sorted((prefix / "lib").glob("*.a"))]
        if report["libraries_before"] != report["libraries_after"]:
            raise RuntimeError("Dependency archives changed during validation")
        shutil.copyfile(build / "CMakeCache.txt", output / "CMakeCache.txt")
        report["status"] = "dependency_validation_passed"
    except Exception as exc:
        report.update(status="failed", reason=str(exc))
        raise
    finally:
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
