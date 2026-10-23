#!/usr/bin/env python3
"""Link the harvested real CPython+SQLite archive with unchanged original tests.

The output is a standalone WebAssembly component, not a Blender artifact. Test
execution and case accounting are separate subsequent observations.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port-root", type=Path, required=True)
    parser.add_argument("--original-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    port, original, output = args.port_root.resolve(), args.original_root.resolve(), args.output.resolve()
    evidence = Path(__file__).resolve().parent
    repo = evidence.parents[2]
    original_receipt = evidence / "original-disk-hash-inputs.json"
    original_inputs = json.loads(original_receipt.read_text())
    expected_files = {entry["upstream_path"] for entry in original_inputs["files"]}
    actual_files = {path.relative_to(original).as_posix() for path in original.rglob("*") if path.is_file() or path.is_symlink()}
    if actual_files != expected_files:
        raise ValueError("original source directory differs from the archived closure")
    for entry in original_inputs["files"]:
        path = original / entry["upstream_path"]
        actual = identity(path)
        if path.is_symlink() or any(actual[key] != entry[key] for key in ("bytes", "sha256")):
            raise ValueError("original test or implementation file changed")
    output.mkdir(parents=True, exist_ok=False)
    sdk = port / "tools/emsdk"
    prefix = port / "lib/wasm"
    compiler = sdk / "upstream/emscripten/emcc"
    source = repo / "patches/browser-sqlite/python_component_main.c"
    pre_js = repo / "patches/browser-sqlite/python_component_pre.js"
    env = os.environ.copy()
    overrides = {"EM_CONFIG": str(sdk / ".emscripten"), "EM_CACHE": str(port.parent / "emscripten-cache"),
                 "EMSDK_NODE": str(sdk / "node/22.16.0_64bit/bin/node"), "EMCC_CORES": "1",
                 "BLENDED_SQLITE_PATCHSET_SHA256": identity(port / "scripts/deps/sqlite-patchset.json")["sha256"]}
    env.update(overrides)
    verify = ["python3", str(port / "scripts/deps/sqlite-cache.py"), "verify", "python", str(port)]
    verification = subprocess.run(verify, env=env, capture_output=True, text=True, check=False)
    (output / "cache-verification.log").write_text(verification.stdout + verification.stderr)
    if verification.returncode:
        raise RuntimeError("harvested Python cache is not verified")
    stdlib = prefix / "lib/python3.13"
    stdlib_files = []
    for path in sorted(stdlib.rglob("*")):
        if path.is_symlink():
            raise ValueError("unexpected symlink in harvested stdlib")
        if path.is_file():
            record = identity(path)
            record["relative_path"] = path.relative_to(stdlib).as_posix()
            stdlib_files.append(record)
    (output / "stdlib-files.json").write_text(json.dumps(stdlib_files, indent=2) + "\n")
    program = output / "python-sqlite.js"
    command = [str(compiler), "-O2", "-g0", "-fexceptions", "-matomics", "-mbulk-memory",
               "-I" + str(prefix / "include/python3.13"), "-I" + str(prefix / "include"), str(source),
               str(prefix / "lib/libpython3.13.a"), "-sUSE_ZLIB=1", "-lm", "-sALLOW_MEMORY_GROWTH=1",
               "-sSTACK_SIZE=5242880", "-sEXIT_RUNTIME=1", "-sASSERTIONS=1", "-sENVIRONMENT=web,node",
               "-sFORCE_FILESYSTEM=1", "--pre-js", str(pre_js),
               "--preload-file", str(stdlib) + "@/usr/local/lib/python3.13",
               "--preload-file", str(original) + "@/original", "-o", str(program)]
    report = {"schema": 1, "kind": "standalone-wasm-cpython-sqlite-build",
              "started_utc": datetime.now(timezone.utc).isoformat(), "command": command, "cwd": str(output),
              "environment_overrides": overrides, "capture_driver": identity(Path(__file__).resolve()),
              "input_files": [identity(path) for path in (source, pre_js, compiler, prefix / "lib/libpython3.13.a",
                                                           prefix / "include/python3.13/Python.h", prefix / "include/python3.13/pyconfig.h",
                                                           prefix / "include/sqlite3.h", port / "scripts/deps/sqlite-patchset.json",
                                                           original_receipt, output / "stdlib-files.json")],
              "cache_verification": {"command": verify, "returncode": verification.returncode,
                                     "log": identity(output / "cache-verification.log")},
              "original_source_files": original_inputs["files"], "expected_case_ids": original_inputs["expected_case_ids"],
              "original_blender_invocation_executed": False, "original_test_assertions_modified": False,
              "strict_blender_browser_test_passes": 0, "full_feature_parity": False}
    started = time.monotonic()
    with (output / "build.log").open("xb") as log:
        result = subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    report.update(returncode=result.returncode, completed_successfully=result.returncode == 0,
                  elapsed_seconds=round(time.monotonic() - started, 6), finished_utc=datetime.now(timezone.utc).isoformat())
    report["build_log"] = identity(output / "build.log")
    report["artifacts"] = [identity(path) for path in (program, program.with_suffix(".wasm"), program.with_suffix(".data")) if path.is_file()]
    (output / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
