# Real SQLite and CPython component build evidence

The pinned SQLite 3.51.3 library and CPython 3.13.13's original `_sqlite3`
extension compiled successfully with Emscripten 6.0.5. The separate SQLite C
diagnostic executed successfully in both Node and Chrome. The original Blender
disk hash module remains blocked in the standalone Python component because its
unchanged package initializer imports `bpy`.

**This evidence adds zero original Blender browser test passes.** The full
Blender browser artifact must be rebuilt and its original test invocation must
execute before the 12 disk hash cases can receive browser outcomes.

## Completed attempts

| Attempt | Actual outcome | Interpretation |
| --- | --- | --- |
| `sqlite-attempt-1` | Exit 2 | Source extraction could not restore archived ownership in the sandbox. |
| `sqlite-attempt-2` | Exit 1 | SQLite compiled, but the cache recorder rejected the SDK's legitimate confined `clang` symlink. |
| `sqlite-attempt-3` | Exit 0, 26.010186 seconds | Real SQLite archive built and verified cache receipt recorded. |
| `python-attempt-1` | Exit 0, 552.195481 seconds | Native bootstrap, Emscripten CPython build, original `_sqlite3` configure checks, symbol checks and archive harvesting completed. |
| `sqlite-component-node` | Compile exit 0; runtime exit 0 | Separate C diagnostic exercised the actual SQLite archive in Node 22.16.0. |
| `sqlite-component-browser` | Runtime exit 0 | The same C diagnostic artifact exercised the actual SQLite archive in Chrome 155.0.8059.39. |
| `original-disk-hash-node-attempt-1` | Runtime exit 1; 0 of 12 cases observed | Original module import stopped at `ModuleNotFoundError: No module named 'bpy'`. |
| `original-disk-hash-browser-attempt-1` | Runtime exit 1; 0 of 12 cases observed | Chrome reproduced the same original package import blocker. |
| `native-python-diagnostic-1` | Runtime exit 1 | A separately authored binding diagnostic made an invalid serialization assumption for a WAL-derived image. |
| `python-sqlite-browser-diagnostic-1` | Runtime exit 1 | The same diagnostic source raised the same exception at the same line in Chrome. This is not a completed binding diagnostic pass or evidence of a browser-only defect. |

Each attempt retains its original command, inputs, raw output, actual exit and
capture-driver identity. Earlier attempts and their original preparation inputs
were not rewritten when the build setup was corrected. `summary.json` binds
every listed receipt and states the remaining gate explicitly.

## What was implemented

The patchset is `patches/browser-sqlite/manifest.json`, SHA-256
`4c3d9fe421f461854a77abc36fa1580dba3e11abbeb39f3d7bf409bf36e8a57d`.
It applies to port commit
`0e02e84b2bc5d9b27a6dc6e275443292f781fbad`, whose original Blender source is
`fbe6228777e7d9afefcd61a413844e790ae75db7`. It changes the dependency recipe and
archive harvesting. SQLite source, CPython source, Blender source and original
tests remain unchanged.

The successful SQLite archive is 2,209,218 bytes, SHA-256
`378e64a8e79e067fa415fe1ec83553e8c4452a4d6c707f4da7b5b830ea7a826b`.
The resulting Python archive is 43,312,012 bytes, SHA-256
`dbda24c657a982107b4add2eb680a9942f9ec3c4afbe00c2ef378375bc4c51e7`.
The real `PyInit__sqlite3` and SQLite core/WAL symbols were required before the
new harvest cache was accepted. The cache scope binds the recipes, source
archives, compiler, selected headers and archives, and Python's `sqlite3`
package. It does not claim integrity coverage for every unrelated stdlib file.

Build job counts were bounded to one. The CPython capture records a minimum free
disk reserve of 12,252,954,624 bytes and maximum child resident memory of
322,128 KiB. Exact source, SDK and browser identities are retained in the source
fetch, SDK and execution receipts.

## Original module blocker

`original-disk-hash-inputs.json` binds all six source files to the original
Blender archive and freezes the exact 12 native case identities. The standalone
component preloads those same bytes and the harvested Python standard library.
The original test imports `_bpy_internal.disk_file_hash_service`; that package's
initializer imports `bpy` at line 23. A standalone CPython archive does not
include Blender's `bpy` application module.

Both actual executions stopped before unittest discovery. Their receipts retain
all 12 expected IDs as missing, with zero observed case outcomes and zero strict
Blender browser passes. No stub `bpy`, package-initializer bypass, copied test
implementation, altered assertion or selector was used. The rebuilt Blender
application is the remaining execution environment required by this module.

## Separate diagnostic scope

The successful C diagnostic covers WAL with simultaneous read-write and
read-only URI connections, exclusive and immediate transactions, UPSERT
RETURNING, rollback, foreign-key cascade, integrity checks, and closing and
reopening a database within one filesystem instance. It does not establish
browser reload durability, cross-tab locking or the complete application's
feature parity.

The initial Python binding diagnostic successfully reached the call after
`deserialize`, then its query of a WAL-derived serialized image raised
`sqlite3.OperationalError: unable to open database file`. The byte-identical
diagnostic produces the same exception with native Blender's Python and SQLite.
The failed diagnostic is preserved as version 1. Any corrected diagnostic is a
new experiment under
`compatibility/evidence/browser-sqlite-python-validation-2026-10-23/` and does
not replace either original failed attempt or any original Blender case result.

## Recovery and relocation

`python-component-build/` and `python-diagnostic-build-1/` preserve byte-identical
copies of the runtime build receipts and logs. The first also preserves the
complete file identity inventory used to package the harvested standard library.
`preservation.json` maps the original runtime paths to these durable copies.
Original receipts retain their historical absolute paths; their bytes were not
rewritten to make them appear newly executed after relocation.

`python-component-artifacts.tar.gz` preserves both actual JavaScript profiles,
their shared Wasm and preload data, and the six unchanged original Blender
source files. It is 7,231,803 bytes, SHA-256
`9b8db00743eb2f6429ec58485495a477158e9ec02b36334b1932622bf4b2cb2e`.
`preservation.json` binds every archived member and verifies that the two
profiles used byte-identical Wasm and preload payloads. To reconstruct a profile,
place its `python-sqlite.js` together with the two files under `common/`; keep
their original `python-sqlite.wasm` and `python-sqlite.data` filenames. This
reconstructs the measured standalone component, not a Blender application.

`freeze-completed-evidence.py` created the copies, checked all archive members and
produced the summary. All completed evidence under this directory is frozen.
