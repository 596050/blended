# Browser worker and IPC implementation contract

**The next bounded implementation is a real browser spawn backend, duplex IPC and child lifecycle support, plus working Python threads inside the child.** Fixing `socketpair()` alone cannot complete the original downloader invocation. This directory contains read-only analysis and a proposed contract. It contains no backend implementation, new test execution or new browser pass.

## Observed failure versus later source blockers

The frozen original `script_http_downloader` invocation has eight exact native case identities. Its existing native receipt reports eight passes. The existing browser receipt reports seven passes and one error: `BackgroundDownloaderProcessTest.test_start_stop` reaches `Pipe(duplex=True)`, then `socket.socketpair()`'s fallback socket creation, and raises **ENOSYS, errno 52**. The original driver and browser exit with code 1. The first failure occurs before a child is launched.

The following are source-inferred later blockers, not newly observed runtime failures:

| Boundary | Exact pinned-source finding |
| --- | --- |
| Spawn selection | Blender explicitly requests `multiprocessing.get_context(method='spawn')`; its target is the original `_download_queued_items` function. |
| Resource tracker | CPython's current POSIX spawn launcher imports `resource_tracker`, which imports `_posixshmem`. The actual packaged configuration marks `_posixshmem` unavailable. |
| Launch and completion | The current launcher needs inherited descriptors, `os.pipe()`, `_posixsubprocess.fork_exec` and child polling via `os.waitpid()`. `_posixsubprocess` is unavailable. Inspected Emscripten libc includes unavailable exec/fork/wait implementations. Cross-build `HAVE_FORK=1` does not establish usable processes. |
| Python executable | Existing browser logs warn that the Python binary is missing. The unchanged embedding code sets `sys.executable=None` under that condition. A launcher must provide an actual execution target and process semantics. |
| Synchronization | The packaged `_multiprocessing.py` is the port's local-only semaphore shim. It has no shared handle or name; `_rebuild` makes a fresh semaphore. CPython also explicitly marks its real `_multiprocessing` extension unavailable on Emscripten, independently of pthread flags. |
| Child threading | The unchanged target creates RX and TX Python threads, a Queue and a threading Event, then joins the threads during shutdown. The current Python recipe lacks `--enable-wasm-pthreads`. The final Blender host is threaded, so actual child thread behavior still requires measurement rather than inference from that flag alone. |

The two multiprocessing Events on `BackgroundDownloader` remain in the parent in this invocation. Passing this test therefore would not establish transferable Event/SemLock parity.

## Smallest useful implementation boundaries

1. **Browser spawn context.** Add an Emscripten backend beneath the existing `get_context('spawn')` and `Process` APIs. Start a fresh isolated CPython instance with independent heap/module state. Preserve preparation data, argv, cwd, environment, import paths and `__main__` reconstruction. Load the original target, options and dependency closure. Track real startup, liveness, exit and daemon cleanup.

2. **Duplex Connection transport.** Implement ordered arbitrary pickle messages, framing, partial transfers, bounded buffering, backpressure, nonblocking `poll(0)`, receive timeouts and correct endpoint closure/errors. Transfer a real endpoint capability to the child. Its RX and TX threads must use the same channel concurrently. A synchronous-capable transport, such as shared buffers with atomic state and a broker, is needed while Python remains inside its polling loops. A callback-only `postMessage` queue must have an explicit suspension strategy or it can deadlock when its event loop is occupied.

3. **Real child threading and synchronization.** Build and validate a child interpreter with working Thread, Event, Queue, sleep, GIL/TLS and joins. A separately packaged CPython build with consistent wasm pthread compile/link settings is the recommended starting point. Keep browser UI work outside blocking Python. Replace the existing semaphore shim with genuinely shared state before advertising cross-worker synchronization. No fake `_posixshmem`, fork result, process liveness or SHUTDOWN response can satisfy this contract.

The existing application's source and tests remain unchanged. Implement these capabilities at the CPython/browser runtime boundary, not as special cases for the downloader class or its test names. The proposal lists separate general backend checks for isolation, large bidirectional messages, backpressure, abrupt death, real child threads and cleanup. Those checks carry no original Blender test credit.

## Exact original acceptance gate

Rerun the complete frozen eight-case invocation on a newly measured artifact. Preserve every native case identity, original assertion, timeout, entry point and absence of extra filters or skips. Require both the original driver and browser to complete successfully.

The original start/stop case specifically requires:

- A queued download before start raises `RuntimeError`.
- After start, shutdown-requested and shutdown-complete are false, while subprocess-alive is true.
- Three `update()` calls complete without unexpected callback/error.
- The finally block shuts down the living child; the second `shutdown()` call is safe.
- Afterwards, both shutdown flags are true and subprocess-alive is false.

The real child must execute the unchanged target, receive its SHUTDOWN message and finish. Keep the original five-second shutdown bound and one-second thread joins. `proposal.json` records the exact source text and line of every assertion in all eight original cases. These tests deliberately do not exercise real HTTP traffic; a pass would not establish browser networking, TLS or complete multiprocessing parity.

## Concrete documentation overlap

The resource-complete documentation attempt passed its `sphinx_doc_gen` subtest, then failed at the original `subprocess.run()` with **ENOTSUP, errno 138**. CPython explicitly rejects subprocesses on Emscripten.

The reusable Python worker launcher could support that path, but it also needs the original argv, exit code and coherent filesystem visibility. The child must run `sphinx_stub_gen.py` with the parent-generated RST input and unchanged `--strict-docs`, return 0, and leave a real stubs directory containing `.pyi` files for the original assertions. It also requires `docutils`; the frozen preload has no docutils package paths. This static finding is not a new runtime import test. `PYTHON_BIN` was unavailable in the observed browser receipt. Do not use `--skip-stubs` or treat this proposal as arbitrary native-executable support.

## Evidence and boundaries

`source-bindings.json` hashes the inspected original Blender 5.2 archive, CPython 3.13.13 archive, original port recipe and existing receipts. It verifies the base artifact's JS, data and Wasm files, reads its generated preload metadata without executing JavaScript, and compares the actually packaged downloader and Python library bytes against the original archives. It also preserves the exact packaged Python configuration and semaphore shim.

`proposal.json` is the full source-bound contract. `existing-observations.json` extracts earlier results without changing their raw receipts. The only command executed for preparation reconstructed a new evidence copy of the original port recipe from a verified patch; its exact hash matches the old build receipt. Production sources, tools, tests, frozen plans and earlier receipts are unchanged. No build or Blender invocation was started.

General design references: [CPython multiprocessing](https://docs.python.org/3.13/library/multiprocessing.html), [Emscripten pthread requirements](https://emscripten.org/docs/porting/pthreads.html), and [Atomics.wait restrictions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics/wait). The frozen source snapshots determine the version-specific findings.
