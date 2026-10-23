#!/usr/bin/env python3
"""Compile and execute a real SQLite component diagnostic, not Blender tests."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    repo = Path(__file__).resolve().parents[3]
    work = repo.parent / "runtime/browser-sqlite-work"
    port = work / "gessa"
    sdk = port / "tools/emsdk"
    output = Path(__file__).resolve().parent / "sqlite-component-node"
    output.mkdir(exist_ok=False)
    source = repo / "patches/browser-sqlite/probe_sqlite.c"
    program = output / "probe.js"
    compiler = sdk / "upstream/emscripten/emcc"
    node = sdk / "node/22.16.0_64bit/bin/node"
    env = os.environ.copy()
    overrides = {"EM_CONFIG": str(sdk / ".emscripten"), "EM_CACHE": str(work / "emscripten-cache"),
                 "EMSDK_NODE": str(node), "EMCC_CORES": "1"}
    env.update(overrides)
    commands = [[str(compiler), "-O2", "-fexceptions", "-matomics", "-mbulk-memory",
                 "-I" + str(port / "lib/wasm/include"), str(source), str(port / "lib/wasm/lib/libsqlite3.a"),
                 "-lm", "-sENVIRONMENT=web,node", "-sEXIT_RUNTIME=1", "-sALLOW_MEMORY_GROWTH=1",
                 "-sASSERTIONS=1", "-o", str(program)], [str(node), str(program)]]
    report = {"schema": 1, "kind": "sqlite-wasm-component-diagnostic", "started_utc": datetime.now(timezone.utc).isoformat(),
              "capture_driver": identity(Path(__file__).resolve()), "environment_overrides": overrides,
              "input_files": [identity(path) for path in (source, compiler, node, port / "lib/wasm/lib/libsqlite3.a",
                                                           port / "lib/wasm/include/sqlite3.h", port / "scripts/deps/sqlite-patchset.json")],
              "commands": [], "original_blender_tests_executed": False, "full_feature_parity": False}
    success = True
    for label, command in zip(("compile", "execute"), commands):
        started = time.monotonic()
        log = output / (label + ".log")
        with log.open("xb") as stream:
            process = subprocess.run(command, cwd=output, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=240)
        report["commands"].append({"argv": command, "cwd": str(output), "returncode": process.returncode,
                                   "elapsed_seconds": round(time.monotonic() - started, 6), "log": identity(log)})
        if process.returncode:
            success = False
            break
    report["artifacts"] = [identity(path) for path in (program, program.with_suffix(".wasm")) if path.is_file()]
    report["completed_successfully"] = success
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
