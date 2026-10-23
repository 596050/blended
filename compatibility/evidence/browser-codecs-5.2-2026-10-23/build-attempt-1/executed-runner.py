#!/usr/bin/env python3
"""Capture bounded real Wasm codec recipe builds; no Blender tests are run."""
import argparse
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


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--sdk", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--recipes", nargs="+", choices=("webp", "openjpeg", "aom", "libheif"), default=["webp", "openjpeg", "aom", "libheif"])
    args = parser.parse_args()
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    work, sdk, output = args.work.resolve(), args.sdk.resolve(), args.output.resolve()
    assert not output.exists()
    output.mkdir(parents=True)
    port = work / "gessa"
    recipes = port / "scripts/deps"
    recipes.mkdir(parents=True, exist_ok=True)
    (port / "tools").mkdir(exist_ok=True)
    sdk_link = port / "tools/emsdk"
    if sdk_link.exists():
        assert sdk_link.resolve() == sdk
    else:
        sdk_link.symlink_to(sdk, target_is_directory=True)
    for p in (repo / "patches/browser-codecs/recipes").glob("*.sh"):
        shutil.copyfile(p, recipes / p.name)
    cache = port / "build-deps/_cache"
    cache.mkdir(parents=True, exist_ok=True)
    for p in (work / "cache").glob("*.tar.gz"):
        q = cache / p.name
        if q.exists():
            assert digest(q)["sha256"] == digest(p)["sha256"]
        else:
            q.symlink_to(p)
    patch_rel = Path("build_files/build_environment/patches/aom_6d2b7f71b98bfa28e372b1f2d85f137280bdb3de.diff")
    patch = port / "upstream" / patch_rel
    patch.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(evidence / "sources/blender" / patch_rel, patch)
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "CC", "CXX", "AR", "RANLIB"):
        environment.pop(key, None)
    environment.update(EM_CACHE=str(work / "emscripten-cache"), EMSDK_PYTHON=sys.executable,
                       BLENDED_BUILD_JOBS="1", CMAKE_BUILD_PARALLEL_LEVEL="1", MAKEFLAGS="-j1",
                       PYTHONDONTWRITEBYTECODE="1", EMSDK_QUIET="1")
    record = {"schema": 1, "kind": "browser-codec-recipe-build-validation", "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(), "work": str(work),
              "runner": digest(Path(__file__).resolve()), "jobs": 1,
              "cache": environment["EM_CACHE"], "sdk": str(sdk),
              "compiler": digest(sdk / "upstream/bin/clang"),
              "emcc": digest(sdk / "upstream/emscripten/emcc"),
              "recipes": [digest(p) for p in sorted(recipes.glob("*.sh"))],
              "upstream_aom_patch": digest(patch), "commands": [],
              "blender_cases_executed": 0, "browser_feature_parity": False,
              "limit": "Real codec dependency compilation for wasm32 with the pinned Emscripten toolchain. This is not a rebuilt Blender artifact or an original Blender test execution."}
    assert record["compiler"]["sha256"] == "5f46543b5574cb152d33f37c324837f5468dc4c1ce95b166c6cd04343d7b6d2d"
    assert record["emcc"]["sha256"] == "498eba9b6aacffca1c358ba340fc7b37015d7867cb211c7f2d45784ee9310f03"

    def save():
        (output / "execution.json").write_text(json.dumps(record, indent=2) + "\n")

    try:
        for name in args.recipes:
            command = ["bash", str(recipes / (name + ".sh"))]
            row = {"name": name, "argv": command, "cwd": str(port), "started_at": datetime.now(timezone.utc).isoformat()}
            record["commands"].append(row)
            save()
            log = output / (name + ".log")
            started = time.monotonic()
            with log.open("wb") as stream:
                process = subprocess.Popen(command, cwd=port, env=environment, stdout=stream,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                while True:
                    try:
                        rc = process.wait(timeout=30)
                        row.update(returncode=rc, timed_out=False)
                        break
                    except subprocess.TimeoutExpired:
                        elapsed = time.monotonic() - started
                        print(json.dumps({"recipe": name, "elapsed_seconds": round(elapsed, 2), "log_bytes": log.stat().st_size}), flush=True)
                        if elapsed > 1800:
                            os.killpg(process.pid, signal.SIGTERM)
                            try:
                                process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                process.wait()
                            row.update(returncode=process.returncode, timed_out=True)
                            break
            row.update(completed_at=datetime.now(timezone.utc).isoformat(), duration_seconds=round(time.monotonic() - started, 6), log=digest(log))
            save()
            print(json.dumps({"recipe": name, "returncode": row["returncode"], "duration_seconds": row["duration_seconds"]}), flush=True)
            if row["returncode"] != 0 or row["timed_out"]:
                raise RuntimeError(f"{name} recipe failed; see {log}")
        record["artifacts"] = [digest(path) for path in sorted((port / "lib/wasm/lib").glob("*.a"))]
        record["status"] = "recipe_builds_passed"
    except Exception as exc:
        record.update(status="failed", reason=str(exc))
        raise
    finally:
        record["completed_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
