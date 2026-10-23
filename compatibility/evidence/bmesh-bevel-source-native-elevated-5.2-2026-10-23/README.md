# Original native bevel suite: completed local retry

The unchanged original Blender 5.2 `bmesh_bevel` invocation completed with
**process exit 0 in 2.116751 seconds**. The original driver emitted 88 distinct
case starts and 88 explicit passes. Every case reported `Mesh Comparison : Same`
and `Mesh Validation : Valid`. There were no missing, duplicated, unexpected or
ambiguous case identities. The source, helper and fixture hashes were unchanged
after execution.

This is a **source-derived original invocation**, not a configured CTest
execution. It adds zero browser passes and does not modify the selected
829-obligation browser ledger or the separate Blender 5.4 native results.

## Original inputs and command

The registration is declaration 49 at line 517 of the pinned
`tests/python/CMakeLists.txt`, under `if(TEST_SRC_DIR_EXISTS)`. The complete
checksum-bound catalog authenticates the original registration and context.
`bevel_operator.py`, `modules/mesh_test.py` and the CMake context were copied
byte-for-byte from the original source archive for commit
`fbe6228777e7d9afefcd61a413844e790ae75db7`.

The installed native Blender executable is SHA-256
`83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27`.
Its previously verified release archive and build identity are referenced by the
prospective receipt. This does not upgrade the earlier receipt's separate
source-build correspondence flag.

The original fixture `tests/files/modeling/bevel_regression.blend` is 2,387,547
bytes, SHA-256
`dad2aa2c02cb6ceb9e025b729e1886a95b3d744c10dce56503adbd15ec312771`.
The original 5.2 archive's LFS pointer supplies that identity. A cached payload
in the hydrated product tree matched it exactly and was copied into the isolated
5.2 evidence staging tree. No network download or newer-version fixture
substitution was used.

The complete argv is preserved prospectively in both attempts. It retains the
original background, factory-startup, debug-memory, debug-exit-on-error,
Python-exit-code and thumbnail-disabling parameters, then loads the original
fixture and runs the original script with `--run-all-tests`.

That last flag is essential: the original full-suite branch enables its actual
mesh comparison. The upstream `--run-test` branch disables comparison for visual
inspection, so it was not used. `BLENDER_TEST_UPDATE` was absent throughout, and
no golden object, source assertion, tolerance or test selection was changed.

## Why two attempts are preserved

The first attempt is retained unchanged under
`../bmesh-bevel-source-native-5.2-2026-10-23/`. It emitted all 88 pass results, then
failed to exit after reporting a PulseAudio mainloop permission error. The
180-second guard terminated it with return code -15. Its invocation-completion
status is false.

The parent authorized one retry in the elevated local environment. The retry
used exactly the same original argv, working directory, source/helper/fixture
bytes, native executable, declared numeric-library thread requests and
180-second timeout. It exited normally. Both raw logs and both prospective
receipts remain available; the first attempt was not rewritten or hidden.

The first capture's direct `/proc/<child-pid>` sampling was not valid across the
restricted PID namespace. Its recorded sampled RSS and thread count are retained
but explicitly excluded from resource conclusions. Its kernel child-resource
accounting reported 367,976 KiB maximum RSS. The retry verifies procfs command
identity before sampling; it observed 363,752 KiB sampled peak RSS and up to
18 threads. The environment requests therefore do not establish a one-thread
limit for all Blender worker pools.

## Case observations and counting

`execution.json` binds the original raw stdout and keeps each named start,
pass/fail marker and comparison/validation result. The static list of 88 literal
specifications is used only to detect missing or unexpected cases. Successful
outcomes come from original runtime output plus actual process completion.

`summarize.py` independently rereads both logs, verifies the exact original names
and every comparison/validation marker, checks unchanged argv and inputs, and
produces `summary.json`. The same 88 names in two attempts are counted once in
the completed source-derived native scope. No configured CTest inventory,
browser outcome, whole-suite denominator or full application parity is inferred.
