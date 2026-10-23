#!/usr/bin/env python3
"""Bind a proposed implementation boundary to exact original source assertions."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def identity(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(REPO)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def anchor(relative, needle):
    path = HERE / relative
    text = path.read_text()
    lines = [index + 1 for index, line in enumerate(text.splitlines()) if needle in line]
    if not lines:
        raise ValueError("source anchor missing: " + needle)
    return {"file": identity(path), "matching_lines": lines, "needle": needle}


def main():
    out = HERE / "proposal.json"
    if out.exists():
        raise FileExistsError("proposal already frozen")
    bindings = json.loads((HERE / "source-bindings.json").read_text())
    existing = json.loads((HERE / "existing-observations.json").read_text())
    manifest = json.loads((REPO / "compatibility/candidate-suites/unittest-main-5.2/script_http_downloader.json").read_text())
    test_relative = "source/blender/tests/python/bl_http_downloader.py"
    test_text = (HERE / test_relative).read_text()
    test_tree = ast.parse(test_text)
    source_cases = []
    for cls in test_tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef) or not method.name.startswith("test_"):
                continue
            assertions = []
            for call in ast.walk(method):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and isinstance(call.func.value, ast.Name) and call.func.value.id == "self"
                        and (call.func.attr.startswith("assert") or call.func.attr == "fail")):
                    assertions.append({"line": call.lineno, "source": ast.get_source_segment(test_text, call)})
            source_cases.append({"id": cls.name + "." + method.name, "line": method.lineno,
                                 "method_sha256": hashlib.sha256(ast.get_source_segment(test_text, method).encode()).hexdigest(),
                                 "assertion_calls": sorted(assertions, key=lambda item: item["line"])})
    source_cases.sort(key=lambda item: item["id"])
    assert [item["id"] for item in source_cases] == manifest["suites"][0]["case_ids"]
    app = "source/blender/scripts/modules/_bpy_internal/http/downloader.py"
    py = "source/cpython-3.13.13/"
    blockers = [
        {"id": "duplex-pipe", "evidence_kind": "observed-runtime-failure",
         "finding": "The original start/stop case fails at Pipe(duplex=True), through socket.socketpair fallback, with OSError errno 52 ENOSYS. The original driver and browser both exit 1.",
         "sources": [anchor(app, "my_side, subprocess_side = _mp_context.Pipe(duplex=True)"),
                     anchor(py + "Lib/multiprocessing/connection.py", "s1, s2 = socket.socketpair()"),
                     anchor(py + "Tools/wasm/config.site-wasm32-emscripten", "ac_cv_func_socketpair=no")]},
        {"id": "spawn-resource-tracker", "evidence_kind": "source-inferred-later-blocker",
         "finding": "The application explicitly selects spawn. Its current POSIX launcher imports resource_tracker, which unconditionally imports _posixshmem on posix. The actual packaged configuration marks _posixshmem n/a. This path was not reached by the failing original invocation.",
         "sources": [anchor(app, "multiprocessing.get_context(method='spawn')"),
                     anchor(py + "Lib/multiprocessing/popen_spawn_posix.py", "from . import resource_tracker"),
                     anchor(py + "Lib/multiprocessing/resource_tracker.py", "import _posixshmem"),
                     anchor(py + "configure.ac", "[_posixshmem],")]},
        {"id": "spawn-exec-and-reap", "evidence_kind": "source-inferred-later-blocker",
         "finding": "The current spawn launcher needs descriptor inheritance, os.pipe, util.spawnv_passfds, _posixsubprocess.fork_exec, and inherited popen_fork polling via os.waitpid. _posixsubprocess is n/a in the packaged configuration; Emscripten's inspected libc includes unavailable exec/fork/wait implementations. HAVE_FORK=1 and HAVE_VFORK=1 in cross-build config do not establish functional processes.",
         "sources": [anchor(py + "Lib/multiprocessing/util.py", "import _posixsubprocess"),
                     anchor(py + "Lib/multiprocessing/popen_spawn_posix.py", "util.spawnv_passfds"),
                     anchor(py + "Lib/multiprocessing/popen_fork.py", "os.waitpid(self.pid, flag)"),
                     anchor("source/emscripten-6.0.5/system/lib/libc/emscripten_libc_stubs.c", "weak int execve"),
                     anchor("source/emscripten-6.0.5/system/lib/libc/emscripten_libc_stubs.c", "weak pid_t fork"),
                     anchor("source/emscripten-6.0.5/system/lib/libc/emscripten_syscall_stubs.c", "weak pid_t __syscall_wait4")]},
        {"id": "interpreter-identity", "evidence_kind": "observed-warning-and-source-inferred-launch-gap",
         "finding": "Existing browser logs warn that the Python executable is unavailable. The original embedding code sets sys.executable to None in that condition. Worker launch must provide a real Python execution target, preparation metadata, import paths and child result/exit status; a path placeholder alone supplies none of those capabilities.",
         "sources": [anchor("source/blender/source/blender/python/intern/bpy_interface.cc", "Unable to find the Python binary"),
                     anchor("source/blender/source/blender/python/intern/bpy_interface.cc", 'PySys_SetObject("executable", Py_None)'),
                     anchor(py + "Lib/multiprocessing/spawn.py", "set_executable(sys.executable)")]},
        {"id": "semaphores-and-child-threads", "evidence_kind": "source-inferred-capability-gap-and-required-validation",
         "finding": "The base artifact installs the port's single-process SemLock shim. It has no shared handle/name and _rebuild creates a fresh semaphore, so it is not transferable worker synchronization. CPython explicitly marks _multiprocessing n/a even if pthread flags change. The unchanged downloader child starts real RX and TX Python threads. Its two multiprocessing Events remain in the parent for this test, so this invocation alone does not establish cross-process Event/SemLock parity. The current recipe lacks --enable-wasm-pthreads; actual child thread behavior must be measured, since the final Blender host itself is threaded.",
         "sources": [anchor("source/port/scripts/deps/python-shims/_multiprocessing.py", "self.handle = None"),
                     anchor("source/port/scripts/deps/python-shims/_multiprocessing.py", "return SemLock(kind, 1, maxvalue, name, False)"),
                     anchor(py + "configure.ac", "[_multiprocessing],"),
                     anchor(app, "rx_thread.start()"), anchor(app, "tx_thread.start()"),
                     anchor(py + "configure.ac", "AC_ARG_ENABLE([wasm-pthreads]")]},
    ]
    proposal = {
        "schema": 1, "kind": "proposed-browser-worker-ipc-source-contract",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "proposal_driver": identity(Path(__file__).resolve()),
        "source_bindings": identity(HERE / "source-bindings.json"),
        "existing_observations": identity(HERE / "existing-observations.json"),
        "status": "read-only-analysis-not-implemented",
        "source_commit": bindings["source_commit"], "port_commit": bindings["port_commit"],
        "python_version": "3.13.13", "emscripten_version": "6.0.5",
        "current_original_http_invocation": {
            "source": identity(HERE / test_relative), "registration": manifest["execution"],
            "expected_exact_case_ids": manifest["suites"][0]["case_ids"],
            "existing_native_passes": 8, "existing_browser_passes": 7, "existing_browser_errors": 1,
            "new_execution_in_this_analysis": False},
        "blockers": blockers,
        "minimum_general_implementation_boundaries": [
            {"id": "browser-spawn-context", "seam": "CPython multiprocessing context and new browser Popen backend, plus a packaged Python Worker launcher",
             "required": ["Keep get_context('spawn') and the original public Process API. Launch an isolated fresh CPython instance with its own heap and module state; do not map Process to a thread in the existing interpreter.",
                          "Preserve spawn preparation data, argv, cwd, environment, sys.path and __main__ reconstruction. Use the original target and ForkingPickler reduction semantics; execute the real _download_queued_items function with original options.",
                          "Package the original _bpy_internal modules and the exact required pure-Python dependency closure, including requests, urllib3 and cattrs. Expose the unchanged staged original main script when spawn preparation needs it.",
                          "Track real child startup, running, exit code, death, sentinel/readiness and daemon cleanup. Process.is_alive() must read actual child state, including during synchronous parent shutdown."]},
            {"id": "worker-duplex-connections", "seam": "multiprocessing Pipe/Connection browser transport and handle reduction",
             "required": ["Implement a real bidirectional ordered byte channel usable by arbitrary Python targets. Keep actual pickle payloads, framing, partial transfer, bounded buffering/backpressure, nonblocking poll(0), blocking receive and timeouts.",
                          "Serialize the child endpoint as a real channel capability. Preserve close ownership, EOFError/BrokenPipeError behavior, wakeups and cancellation when an endpoint or worker dies.",
                          "Support the existing child RX and TX threads concurrently; do not hard-code SHUTDOWN, return synthetic report values, or schedule the target in the parent's Python heap.",
                          "Choose a synchronous-capable Worker transport, such as bounded SharedArrayBuffer channels with atomic state and a host broker. A postMessage-only implementation whose callbacks require a blocked Python event loop cannot satisfy the current busy poll loops without an explicit suspension mechanism.",
                          "Run blocking Python away from the browser UI thread. Bind cross-origin-isolation prerequisites and worker startup/pthread pool readiness to the artifact rather than extending the original five-second shutdown limit."]},
            {"id": "real-thread-and-synchronization-support", "seam": "CPython dependency recipe, _thread runtime and a genuine browser synchronization backend",
             "required": ["Build and execute the child interpreter with working threading.Thread, Event, Queue, sleep and joins. The original function must start both RX and TX threads and exit normally after SHUTDOWN.",
                          "The recommended separately packaged child build enables CPython wasm pthreads and uses consistent -pthread compile/link flags. Verify TLS, GIL and wakeup behavior in Chrome; a threaded final host does not prove an independently launched child works.",
                          "Provide actual inter-worker synchronization for any advertised transferable multiprocessing Event/SemLock. Replace the existing local-only shim before claiming that broader API. Resource lifecycle must be tracked by the browser backend; importing a fake _posixshmem or returning fake fork/wait results is insufficient."]},
            {"id": "shared-interpreter-launch-service", "seam": "reusable browser Python launch, filesystem and process-result service",
             "required": ["Make the worker launch/liveness service reusable by subprocess for Python commands, with actual argv, environment, cwd, standard streams, return code, wait and cancellation semantics.",
                          "Define coherent file visibility for parent-generated inputs and child-created outputs. A snapshot without synchronized writes cannot satisfy documentation stub output checks or real downloads.",
                          "Keep arbitrary native executables and shell support explicitly unsupported until implemented. This proposal does not provide idiff or arbitrary operating-system process execution."]},
        ],
        "original_source_bound_acceptance": {
            "unchanged_full_invocation": "Run the frozen original script_http_downloader manifest on a new measured browser artifact, with all eight exact native IDs, no additional filters or skips, and successful original driver plus browser process completion.",
            "exact_original_case_sources": source_cases,
            "start_stop_sequence": [
                "queue_download before start must raise RuntimeError.",
                "After the real start: shutdown_requested=False, shutdown_complete=False, subprocess_alive=True.",
                "Three original update() calls must complete without unexpected callback/error.",
                "The original finally block shuts down the living child; the subsequent second shutdown() call must remain safe.",
                "After shutdown: shutdown_requested=True, shutdown_complete=True, subprocess_alive=False.",
                "The real child must receive the original SHUTDOWN message, run the unchanged target's exit path and terminate. The original loop's five-second bound and one-second thread joins remain unchanged."],
            "additional_general_backend_checks_not_blender_test_credit": [
                "A child executes arbitrary importable Python targets in an isolated interpreter; parent globals are not shared or silently modified.",
                "Duplex transfer preserves arbitrary picklable values, multiple messages, payloads larger than the transport buffer and both directions under backpressure.",
                "poll(0) is genuinely nonblocking; receive, timed waits, EOF, broken-pipe and abrupt child death report real state.",
                "Two real child threads run concurrently with child main, use Event/Queue and join without deadlock while the parent remains inside its synchronous shutdown loop.",
                "Repeated spawn/stop and failed startup leave no live worker, transport handle or synchronization resource behind.",
                "Advertised cross-worker Event/SemLock state survives reduction/rebuild and is shared, unlike the current local-only shim."],
            "not_established_by_the_eight_original_cases": ["actual HTTP transfers", "browser Fetch/CORS integration", "TLS behavior", "download cancellation during real network I/O", "arbitrary subprocess executables", "complete multiprocessing API parity"]},
        "documentation_overlap": {
            "observed": "With original documentation resources mounted, sphinx_doc_gen passes its subtest. The original sphinx_stub_gen subprocess call fails with OSError errno 138 ENOTSUP because subprocess.Popen rejects Emscripten.",
            "sources": [anchor("source/blender/tests/python/bl_pyapi_doc_gen.py", "result = subprocess.run("),
                        anchor(py + "Lib/subprocess.py", "_can_fork_exec = sys.platform not in"),
                        anchor(py + "Lib/subprocess.py", "if not _can_fork_exec:"),
                        anchor("source/blender/doc/python_api/sphinx_stub_gen.py", "from docutils import nodes")],
            "original_argv": ["PYTHON_BIN or sys.executable", "original sphinx_stub_gen.py", "generated rst_dir", "-o", "stubs_dir", "--strict-docs"],
            "acceptance": "Run that real child, retain --strict-docs, require actual returncode 0, the original stubs directory and at least one generated .pyi. Keep both original subtests and full parent outcome; never use --skip-stubs.",
            "extra_prerequisites": ["A real child interpreter identity; the browser receipt reports PYTHON_BIN unavailable.",
                                    "Exact docutils dependency closure in the child. The frozen preload contains zero docutils package paths; source inspection alone is not a runtime import test.",
                                    "Coherent parent RST input and child .pyi output visibility before the original temporary-directory cleanup."],
            "not_solved_by_a_pipe_only_fix": True},
        "design_references": [
            {"url": "https://docs.python.org/3.13/library/multiprocessing.html", "role": "General spawn/isolation contract; inspected 3.13.13 source, not moving documentation, is the implementation authority."},
            {"url": "https://emscripten.org/docs/porting/pthreads.html", "role": "Thread compile/link flags, worker pool readiness and main-thread blocking constraints."},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics/wait", "role": "SharedArrayBuffer waiting is unavailable on the browser main thread."}],
        "implementation_completed": False, "new_tests_executed": 0, "new_browser_passes": 0,
        "production_code_modified": False, "original_tests_or_assertions_modified": False,
        "historical_receipts_modified": False, "full_feature_parity": False,
    }
    with out.open("x") as stream:
        stream.write(json.dumps(proposal, indent=2) + "\n")
    print(json.dumps(identity(out), indent=2))


if __name__ == "__main__":
    main()
