#!/usr/bin/env python3
"""Compile and capture the unmodified-library standalone DPX diagnostic."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"
CLOSURE_SHA256 = "a5b45d82760da309eec24df47a0319f88a1a7d2b1d1c09703d0dfc9385cfef4f"
MINIMUM_FREE_BYTES = 4 * 1024**3


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def references(value):
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"} <= value.keys():
            yield value
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def verify_inputs(closure):
    expected = {}
    for row in references(closure):
        # CI archive rows are comparison records with prefix-relative paths,
        # not claims that the independently built local archives equal them.
        if not Path(row["path"]).is_absolute():
            continue
        old = expected.setdefault(row["path"], row)
        if (old["bytes"], old["sha256"]) != (row["bytes"], row["sha256"]):
            raise ValueError("conflicting input identities")
    actual = []
    for path, row in sorted(expected.items()):
        measured = identity(path)
        if (measured["bytes"], measured["sha256"]) != (row["bytes"], row["sha256"]):
            raise ValueError("standalone input changed: " + path)
        actual.append(measured)
    for row in closure["prefix_aliases"]:
        path = Path(row["path"])
        if not path.is_symlink() or os.readlink(path) != row["link_text"] or str(path.resolve()) != row["target"]["path"]:
            raise ValueError("installed prefix alias changed")
    return actual


def save(path, report):
    path.write_text(json.dumps(report, indent=2) + "\n")


def main():
    closure_path = HERE / "input-closure.json"
    if identity(closure_path)["sha256"] != CLOSURE_SHA256:
        raise ValueError("reviewed standalone input closure changed")
    closure = json.loads(closure_path.read_text())
    before = verify_inputs(closure)
    if shutil.disk_usage(HERE).free < MINIMUM_FREE_BYTES:
        raise RuntimeError("required 4 GiB disk reserve is unavailable")
    output = HERE / "baseline-attempt-01"
    output.mkdir(exist_ok=False)
    work = RUNTIME / "dpx-memory-io-diagnostic-5.2-2026-10-23"
    work.mkdir(exist_ok=False)
    build = work / "baseline-build"
    build.mkdir()
    sdk, prefix = Path(closure["sdk_root"]), Path(closure["prefix_root"])
    cache_source = sdk / "upstream/emscripten/cache"
    cache = work / "emscripten-cache"
    cache_source_before = [{"relative_path": str(path.relative_to(cache_source)),
                            **identity(path)} for path in sorted(cache_source.rglob("*")) if path.is_file()]
    shutil.copytree(cache_source, cache, symlinks=False)
    cache_copies = []
    for row in cache_source_before:
        copied = identity(cache / row["relative_path"])
        if (copied["bytes"], copied["sha256"]) != (row["bytes"], row["sha256"]):
            raise ValueError("private SDK cache copy changed bytes")
        cache_copies.append({"source": row, "copied": copied})

    node = sdk / "node/22.16.0_64bit/bin/node"
    environment = {name: os.environ[name] for name in ("PATH", "HOME") if name in os.environ}
    environment["PATH"] = os.pathsep.join((str(RUNTIME / "browser-python/bin"),
        str(sdk / "upstream/emscripten"), str(node.parent), environment.get("PATH", "/usr/bin:/bin")))
    environment.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", PYTHONDONTWRITEBYTECODE="1", EM_CACHE=str(cache),
        EM_CONFIG=str(sdk / ".emscripten"), EMSDK=str(sdk), EMSDK_QUIET="1", EMCC_CORES="1",
        CMAKE_BUILD_PARALLEL_LEVEL="1", MAKEFLAGS="-j1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
    if "BLENDER_TEST_UPDATE" in environment:
        raise ValueError("unexpected oracle-update environment key")
    common = ["-O2", "-pthread", "-fexceptions", "-std=c++17", "-DOIIO_STATIC_DEFINE=1", "-I" + str(prefix / "include")]
    compile_command = [str(sdk / "upstream/emscripten/em++"), *common,
        "-MD", "-MF", str(build / "dpx-probe.d"), "-c", str(HERE / "dpx-probe.cpp"), "-o", str(build / "dpx-probe.o")]
    # This is the exact archive set selected by the retained OIIO recipe's
    # successful static-link smoke. Alternate PNG alias/decoder/wrapper archives
    # that were not in that command remain verified inputs, but are not added.
    excluded_alternate_archives = {"libpng.a", "libtiffxx.a", "libwebpdecoder.a"}
    libraries = [row for row in closure["independently_bound_static_libraries"]
                 if Path(row["path"]).name not in excluded_alternate_archives]
    link_command = [str(sdk / "upstream/emscripten/em++"), *common, str(build / "dpx-probe.o"),
        "-sMALLOC=dlmalloc", "-sWASM_BIGINT", "-sALLOW_MEMORY_GROWTH", "-sINITIAL_MEMORY=536870912",
        "-sPROXY_TO_PTHREAD", "-sEXIT_RUNTIME=1", "-sPTHREAD_POOL_SIZE=8", "-sSTACK_SIZE=33554432",
        "-sDEFAULT_PTHREAD_STACK_SIZE=8388608", "-sNODERAWFS", "--profiling-funcs",
        "-Wl,--start-group", *[row["path"] for row in libraries], "-Wl,--end-group", "-o", str(build / "dpx-probe.js")]
    native_command = [closure["native_blender"]["path"], "--background", "--console-crash-handler", "--factory-startup",
        "--debug-memory", "--debug-exit-on-error", "--python-exit-code", "1", "--python-expr",
        "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'", "--python",
        str(HERE / "regenerate-native-inputs.py"), "--", str(output / "regenerated-inputs")]
    operations = []
    for origin in ("file-created", "memory-created"):
        for route in ("memory", "file"):
            operations.append({"name": origin + "-" + route, "origin": origin, "route": route,
                "command": [str(node), str(build / "dpx-probe.js"), route,
                    str(output / "regenerated-inputs" / (origin + ".dpx")),
                    str(output / (origin + "-" + route + ".pixels"))]})
    report = {"schema": 1, "kind": "unmodified-library-standalone-DPX-diagnostic", "status": "running",
        "profile_id": closure["profile_id"], "started_utc": now(), "capture_script": identity(__file__),
        "input_closure": identity(closure_path), "input_observations_before": before,
        "sdk_cache_copy": cache_copies, "environment_mode": "exact allowlist, all values retained",
        "environment": environment, "cwd": str(REPO), "jobs": 1, "linked_libraries": libraries,
        "planned_commands": {"native_input_regeneration": native_command, "compile": compile_command,
                             "link": link_command, "runtime_operations": operations},
        "bounds_seconds": {"native_input_regeneration": 60, "compile": 180, "link": 180, "each_runtime": 30},
        "free_bytes_before": shutil.disk_usage(HERE).free, "minimum_free_bytes": MINIMUM_FREE_BYTES,
        "commands": [], "original_Blender_test_cases_executed": 0, "qualification_credit": 0,
        "local_static_archives_unmodified": True, "local_archives_equal_CI_bytes_claimed": False,
        "input_bytes_captured_from_failing_browser": False, "full_parity": False}
    receipt_path = output / "execution.json"
    save(output / "prospective-command.json", report)
    report["prospective_command"] = identity(output / "prospective-command.json")
    save(receipt_path, report)

    def run(name, command, timeout, require_zero):
        if shutil.disk_usage(HERE).free < MINIMUM_FREE_BYTES:
            raise RuntimeError("required free disk reserve fell below 4 GiB")
        row = {"name": name, "argv": command, "cwd": str(REPO), "started_utc": now(),
               "timeout_seconds": timeout, "expected_zero_for_preparation": require_zero}
        report["commands"].append(row)
        save(receipt_path, report)
        started = time.monotonic()
        process = None
        timed_out = False
        termination = []
        with (output / (name + ".stdout.log")).open("xb") as stdout, (output / (name + ".stderr.log")).open("xb") as stderr:
            try:
                process = subprocess.Popen(command, cwd=REPO, env=environment, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    termination.append({"signal": "SIGTERM", "utc": now()})
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        termination.append({"signal": "SIGKILL", "utc": now()})
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
            except Exception as error:
                row["capture_error"] = {"type": type(error).__name__, "message": str(error)}
                if process is not None and process.poll() is None:
                    termination.append({"signal": "SIGKILL", "utc": now(), "reason": "capture error"})
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            finally:
                row.update(actual_returncode=process.returncode if process is not None else None,
                    timeout_occurred=timed_out, termination_events=termination,
                    finished_utc=now(), elapsed_seconds=time.monotonic() - started)
        row["stdout"] = identity(output / (name + ".stdout.log"))
        row["stderr"] = identity(output / (name + ".stderr.log"))
        save(receipt_path, report)
        print(json.dumps({"name": name, "actual_returncode": row["actual_returncode"],
                          "timeout_occurred": timed_out, "qualification_credit": 0}), flush=True)
        if require_zero and (row["actual_returncode"] != 0 or timed_out or row.get("capture_error")):
            raise RuntimeError("diagnostic preparation failed: " + name)
        return row

    try:
        run("native-input-regeneration", native_command, 60, True)
        regenerated = output / "regenerated-inputs"
        report["regenerated_inputs_before"] = [identity(path) for path in sorted(regenerated.iterdir()) if path.is_file()]
        run("compile", compile_command, 180, True)
        dependency_text = (build / "dpx-probe.d").read_text().replace("\\\n", " ")
        dependencies = dependency_text.split(":", 1)[1].split()
        report["actual_compile_header_inputs"] = [identity(Path(path)) for path in sorted(set(dependencies))]
        shutil.copyfile(build / "dpx-probe.d", output / "compile-dependencies.d")
        report["compiled_object"] = identity(build / "dpx-probe.o")
        run("link", link_command, 180, True)
        report["standalone_artifacts"] = [identity(build / name) for name in ("dpx-probe.o", "dpx-probe.js", "dpx-probe.wasm")]
        for operation in operations:
            run(operation["name"], operation["command"], 30, False)
        report["status"] = "all_four_standalone_operations_captured"
    except Exception as error:
        report["status"] = "diagnostic_preparation_or_capture_failed"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        try:
            after = verify_inputs(closure)
            report["input_observations_after"] = after
            report["original_input_closure_preserved"] = before == after
            if before != after:
                raise ValueError("standalone input closure changed")
        except Exception as error:
            report["original_input_closure_preserved"] = False
            report["preservation_error"] = {"type": type(error).__name__, "message": str(error)}
            report["status"] = "diagnostic_input_integrity_failed"
        if (output / "regenerated-inputs").exists():
            report["regenerated_inputs_after"] = [identity(path) for path in sorted((output / "regenerated-inputs").iterdir()) if path.is_file()]
            report["regenerated_inputs_preserved"] = report.get("regenerated_inputs_before") == report["regenerated_inputs_after"]
        report["raw_pixel_outputs"] = [identity(path) for path in sorted(output.glob("*.pixels"))]
        report["free_bytes_after"] = shutil.disk_usage(HERE).free
        report["finished_utc"] = now()
        save(receipt_path, report)
    print(json.dumps({"receipt": identity(receipt_path), "status": report["status"], "qualification_credit": 0}), flush=True)
    return 0 if report["status"] == "all_four_standalone_operations_captured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
