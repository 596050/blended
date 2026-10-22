# Native Blender 5.2 custom-driver I/O evidence

This is evidence for the four original methods in `tests/python/bl_blendfile_io.py` at Blender commit `fbe6228777e7d9afefcd61a413844e790ae75db7`. It establishes native execution only. No browser, filesystem persistence, exchange, deployed application, or full-facet parity is claimed.

## Invocation and observations

The observer executes the original source with `runpy.run_path(..., run_name="__main__")` and gives the original main block `--output-dir`. The source itself performs argument normalization, sets the thumbnail preference, constructs the original three classes, and invokes unchanged `TestHelper.run_all_tests`. That helper calls `setUp`, each callable `test_*` method in its original `dir(self)` order, and `tearDown`, propagating an exception immediately.

CPython `sys.monitoring` events record actual starts, normal returns, and exceptional unwinds. A method is recorded as passed only after the exact six-event sequence: setup start/return, body start/return, teardown start/return. The four fixed method IDs and all three helper-driver normal returns are required. The observer replaces no upstream callable or assertion and rethrows any upstream exception after recording evidence. The official binary reported Python 3.13.13; this monitoring API requires Python 3.12 or later.

`native-io-proof.json` binds the official archive, executable, observer, host runner, source files, command, log, outcomes, and final file inventory. `execution.json` retains each phase event and per-method output inventories. `native-io.log` is the complete native stdout/stderr log. Both original source files were verified before and after execution.

## Reproduction

Use a compatible Linux x64 host, the official Blender 5.2.0 archive and its extracted executable, and the two exact upstream source files listed in the cohort manifest. Run from this evidence directory:

```sh
python3 run_native_io_proof.py \
  --binary /absolute/path/blender-5.2.0-linux-x64/blender \
  --archive /absolute/path/blender-5.2.0-linux-x64.tar.xz \
  --source-dir /absolute/path/exact-upstream-tests \
  --output /absolute/path/new-empty-proof-directory
```

The helper must be named `bl_blendfile_utils.py` beside `bl_blendfile_io.py`. The runner refuses changed archive, executable, or source bytes and refuses an existing nonempty output directory. The native binary is launched with `--background --factory-startup --threads 1 --python-exit-code 1`.

## Generated files and browser transfer

Six final files are retained in the original scratch proof directory recorded by the command. They total about 2.5 MB. Their hashes identify this run's bytes, not deterministic cross-platform reference outputs. `test_basics` and `test_linking` deliberately share `blendfileTestIdRuntimeTag.blend`; the later save changes that file and its backup. Per-method before/after inventories retain those transitions. The final `.blend1` retains the immediately preceding basic-test main file; an earlier backup is overwritten by the original test behavior.

A browser adapter should place both unchanged sources beside each other in a unique virtual directory, preserve a meaningful `__file__`, use a fresh writable output directory, invoke original `__main__`, and retain the same fixed method inventory. After the execution marker, retrieve each reported output through the engine's filesystem interface, checking relative path confinement, byte count, and SHA-256 against the in-engine inventory. Keep files together for library path resolution. A file's hash checks transfer integrity; it is not a native/browser equivalence assertion.

Do not run a standard unittest loader on this module: its classes require the custom `args` constructor, and the original helper is the test driver. Do not infer individual passes from module exit or file existence. A native exchange audit of retrieved browser files is a separate result; OPFS persistence, reload recovery, user file pickers, and downloads require separate cohorts.
