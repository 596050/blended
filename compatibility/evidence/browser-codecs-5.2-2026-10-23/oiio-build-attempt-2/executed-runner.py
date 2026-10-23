#!/usr/bin/env python3
"""Build the pinned OIIO prerequisite recipes and selected codec patch at one job."""
from __future__ import annotations
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

RECIPES = ["zlib", "zstd", "fmt", "robinmap", "imath", "libdeflate", "openjph", "openexr",
           "libjpeg", "libpng", "libtiff", "expat", "yamlcpp", "pystring", "minizipng", "opencolorio",
           "webp", "openjpeg", "aom", "libheif", "openimageio"]


def identity(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start-at", choices=RECIPES, default=RECIPES[0])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    package = repo / "patches/browser-codecs"
    work, sdk, output = args.work.resolve(), args.sdk.resolve(), args.output.resolve()
    assert not output.exists()
    output.mkdir(parents=True)
    shutil.copyfile(Path(__file__).resolve(), output / "executed-runner.py")
    port = work / "oiio-port"
    private_sdk = port / "tools/emsdk"
    manifest = identity(package / "manifest.json")
    report = {"schema": 1, "kind": "pinned-openimageio-wasm-build-validation", "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(), "runner": identity(Path(__file__).resolve()),
              "manifest": manifest, "compiler": identity(sdk / "upstream/bin/clang"),
              "sdk_source": str(sdk), "sdk_view": str(private_sdk), "jobs": 1,
              "source_materialization": "Selected immutable source files verified against the pinned Git blob inventory; not a complete Blender source checkout.",
              "commands": [], "blender_cases_executed": 0, "full_feature_parity": False,
              "limit": "Original port dependency recipes and selected codec/OIIO integration build only. No Blender executable or upstream Blender test execution."}

    def save():
        (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")

    source_rows = json.loads((evidence / "source-inputs.json").read_text())["sources"]
    port.mkdir(parents=True, exist_ok=True)
    if not args.resume:
        assert args.start_at == RECIPES[0]
        assert not (port / "scripts").exists()
        for row in source_rows:
            if row["repository"] == "gessa-ai/blender-web":
                local = evidence / row["path"]
                assert identity(local)["sha256"] == row["sha256"]
                destination = port / row["upstream_path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(local, destination)
        patch_rel = Path("build_files/build_environment/patches/aom_6d2b7f71b98bfa28e372b1f2d85f137280bdb3de.diff")
        destination = port / "upstream" / patch_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(evidence / "sources/blender" / patch_rel, destination)
        # Hard-link immutable tool payloads; copy SDK metadata/scripts separately.
        # Every directory is private, and the cache is separately writable.
        private_sdk.mkdir(parents=True, exist_ok=False)
        for entry in sdk.iterdir():
            if entry.name in (".git", "downloads", "zips"):
                continue
            destination = private_sdk / entry.name
            if entry.is_dir():
                shutil.copytree(entry, destination, symlinks=True, copy_function=os.link,
                                ignore=shutil.ignore_patterns("cache", "__pycache__"))
            elif entry.is_symlink():
                destination.symlink_to(os.readlink(entry))
            else:
                shutil.copy2(entry, destination)
        sdk_cache = private_sdk / "upstream/emscripten/cache"
        assert not sdk_cache.exists()
        sdk_cache.symlink_to(work / "emscripten-cache", target_is_directory=True)
    else:
        assert private_sdk.is_dir()
        report["prior_dependency_prefix"] = [identity(path) for path in sorted((port / "lib/wasm/lib").glob("*.a"))]
        report["resume_start_at"] = args.start_at
        patched_paths = {entry["path"] for entry in json.loads((package / "manifest.json").read_text())["files"]}
        for row in source_rows:
            if row["repository"] == "gessa-ai/blender-web" and row["upstream_path"] not in patched_paths:
                assert identity(port / row["upstream_path"])["sha256"] == row["sha256"]

    assert identity(private_sdk / "upstream/bin/clang")["sha256"] == report["compiler"]["sha256"]
    cache = port / "build-deps/_cache"
    cache.mkdir(parents=True, exist_ok=True)
    for archive in (work / "cache").glob("*.tar.gz"):
        destination = cache / archive.name
        if not destination.exists():
            destination.symlink_to(archive)
    shims = port / "validation-shims"
    shims.mkdir(exist_ok=True)
    real_getconf = shutil.which("getconf")
    real_curl = shutil.which("curl")
    assert real_getconf and real_curl
    (shims / "getconf").write_text(f"#!{sys.executable}\nimport subprocess,sys\nif sys.argv[1:]==['_NPROCESSORS_ONLN']: print(1)\nelse: sys.exit(subprocess.call([{real_getconf!r},*sys.argv[1:]]))\n")
    (shims / "curl").write_text(f"""#!{sys.executable}
import hashlib,json,os,subprocess,sys
from pathlib import Path
args=sys.argv[1:]
result=subprocess.run([{real_curl!r},*args])
if result.returncode==0 and '-o' in args:
 p=Path(args[args.index('-o')+1])
 row={{'argv':args,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'path':str(p)}}
 with Path(os.environ['BLENDED_CODEC_DOWNLOADS']).open('a') as f: f.write(json.dumps(row)+'\\n')
sys.exit(result.returncode)
""")
    for path in shims.iterdir():
        path.chmod(0o755)
    shutil.copytree(shims, output / "shims")
    host_tools = repo.parent / "runtime/browser-python/bin"
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "CC", "CXX", "AR", "RANLIB"):
        environment.pop(key, None)
    environment.update(EM_CACHE=str(private_sdk / "upstream/emscripten/cache"), EMSDK_PYTHON=sys.executable,
                       EMCC_CORES="1", CMAKE_BUILD_PARALLEL_LEVEL="1", MAKEFLAGS="-j1", BLENDED_BUILD_JOBS="1",
                       PYTHONDONTWRITEBYTECODE="1", EMSDK_QUIET="1", BLENDED_CODEC_DOWNLOADS=str(output / "downloads.jsonl"))
    environment["PATH"] = os.pathsep.join((str(shims), str(host_tools), environment["PATH"]))
    report["environment"] = {key: environment[key] for key in ("EM_CACHE", "EMCC_CORES", "CMAKE_BUILD_PARALLEL_LEVEL", "MAKEFLAGS", "BLENDED_BUILD_JOBS")}

    def run(name, argv, timeout=2400):
        row = {"name": name, "argv": [str(value) for value in argv], "cwd": str(port),
               "started_at": datetime.now(timezone.utc).isoformat()}
        report["commands"].append(row)
        save()
        started = time.monotonic()
        log = output / (name + ".log")
        with log.open("wb") as stream:
            process = subprocess.Popen(argv, cwd=port, env=environment, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            while True:
                try:
                    process.wait(timeout=30)
                    row.update(returncode=process.returncode, timed_out=False)
                    break
                except subprocess.TimeoutExpired:
                    elapsed = time.monotonic() - started
                    print(json.dumps({"name": name, "elapsed_seconds": round(elapsed, 2), "log_bytes": log.stat().st_size}), flush=True)
                    if elapsed > timeout:
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        row.update(returncode=process.returncode, timed_out=True)
                        break
        row.update(completed_at=datetime.now(timezone.utc).isoformat(), duration_seconds=round(time.monotonic() - started, 6), log=identity(log))
        save()
        print(json.dumps({"name": name, "returncode": row["returncode"], "seconds": row["duration_seconds"]}), flush=True)
        if row["timed_out"] or row["returncode"] != 0:
            raise RuntimeError(name + " failed")

    try:
        run("apply-codecs", [sys.executable, package / "apply.py", "--port-root", port, "--receipt", output / "patch-application.json",
                             "--expected-manifest-sha256", manifest["sha256"]], timeout=60)
        report["recipes"] = [identity(port / "scripts/deps" / (name + ".sh")) for name in RECIPES]
        shutil.copytree(port / "scripts/deps", output / "recipes")
        for name in RECIPES[RECIPES.index(args.start_at):]:
            run(name, ["bash", port / "scripts/deps" / (name + ".sh")])
        report["libraries"] = [identity(path) for path in sorted((port / "lib/wasm/lib").glob("*.a"))]
        report["status"] = "openimageio_dependency_build_passed"
    except Exception as exc:
        report.update(status="failed", reason=str(exc))
        raise
    finally:
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
