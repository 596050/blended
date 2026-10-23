# Infrastructure regression execution

The complete ordinary infrastructure suite ran through `capture.py` with the
real CMake executable selected by `BLENDED_INVENTORY_CMAKE`.

- 337 tests ran in the unittest-reported 132.245 seconds.
- The process returned 0, reported `OK`, and skipped zero tests.
- Before/after inventories match for all 137 selected implementation,
  manifest, cache-contract and original port-preimage files.
- Raw stdout, stderr, actual command, interpreter, CMake identity, timings and
  source hashes are preserved in `execution.json` and its bound files.

This adds the real codec patch regressions to ordinary unittest discovery and
exercises database preparation, stale-cache rejection, driver integration and
optional build-receipt validation. Negative tests deliberately provoke failures;
their captured exceptions do not indicate a failed overall test process.

The existing Git HEAD at execution time is `88f5a032ca4fcd26f75ca5f72de27373c27af4db`.
The new implementation bytes were uncommitted and are identified by the retained
file inventory. This is infrastructure evidence and contributes zero original
Blender test passes. All upstream-test and full-feature parity flags stay false.
