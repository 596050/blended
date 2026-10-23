# Real SQLite support for the pinned browser port

This optional dependency patchset enables CPython's original `_sqlite3` extension
against the original SQLite 3.51.3 amalgamation. Blender 5.2 and the native
reference use this SQLite version. The source archives, original port recipe,
patch, preparation files and resulting recipe are bound to exact hashes in
`manifest.json`.

The patchset does not change SQLite source, CPython source, Blender source,
original tests, assertions, tolerances, expected failures or test selections.
It changes dependency configuration and archive harvesting. The previously
disabled `_sqlite3` module is compiled from CPython's own C implementation; the
actual SQLite archive is merged into `libpython3.13.a` with CPython's existing
companion archives. The recipe checks for defined `PyInit__sqlite3`,
`sqlite3_open_v2`, `sqlite3_exec` and `sqlite3_wal_checkpoint_v2` symbols before
recording a successful harvest.

## Source and build configuration

| Input | Pinned identity |
| --- | --- |
| Browser port | `gessa-ai/blender-web` commit `0e02e84b2bc5d9b27a6dc6e275443292f781fbad` |
| Original Blender source | `fbe6228777e7d9afefcd61a413844e790ae75db7`, Blender 5.2 |
| CPython | 3.13.13, original Blender MD5 and additional SHA-256 in the manifest |
| SQLite | 3.51.3, original Blender SHA-1 and additional SHA-256 in the manifest |
| Emscripten | 6.0.5, exact SDK and compiler identities in the manifest |

The SQLite recipe retains the Unix features selected by Blender's
`build_files/build_environment/cmake/sqlite.cmake`, including WAL, transactions,
foreign keys, FTS, RTREE, GEOPOLY, session and pre-update support. It uses the real
Unix VFS. The recipe also retains the native configuration's math, percentile and
auto-vacuum defaults. `SQLITE_THREADSAFE=1` is compiled, and the object carries the
atomics and bulk-memory features needed by the port's final shared-memory link.
Actual multi-thread and multi-process behavior still requires runtime tests.

CPython receives explicit `LIBSQLITE3_CFLAGS` and `LIBSQLITE3_LIBS`, so its normal
configure checks inspect this pinned library instead of selecting the SDK's
separate SQLite port. Loadable-extension API support is compiled as in the native
configuration. This does not establish that a browser can load arbitrary native
extensions.

## Source-build driver integration

The enclosing driver must first verify the selected port and Blender source
commits. Then, before taking dependency recipe identities, call:

```python
from tools.prepare_browser_sqlite import apply_patchset

receipt = apply_patchset(
    port_root,
    manifest_path,
    expected_manifest_sha256,
    receipt_path,  # optional; an existing different receipt is never overwritten
)
environment.update(receipt["environment"])
```

`load_patchset(manifest_path, expected_manifest_sha256)` provides validation
without preparing the checkout. Both APIs return JSON-serializable dictionaries.
The selected hash must come from the reviewed build configuration. A manifest
cannot establish its own authority by declaring its own hash.

Insert `sqlite` immediately before `python` in the dependency order, then run the
normal recipe list. Record the returned application receipt, all input identities
and the actual recipe identities in the source-build receipt and package
provenance. An artifact built with this patchset has a new identity and requires
its own original test execution.

The standalone preparation CLI is:

```sh
python3 tools/prepare_browser_sqlite.py \
  --port-root /absolute/path/to/pinned/port \
  --manifest patches/browser-sqlite/manifest.json \
  --manifest-sha256 REVIEWED_MANIFEST_SHA256 \
  --receipt /absolute/path/to/new/preparation.json
```

Supply the driver's private `EM_CACHE` to both recipes. They preserve it across
`emsdk_env.sh`, which otherwise assigns the SDK's own default cache. Set
`MAKEFLAGS`, `CMAKE_BUILD_PARALLEL_LEVEL`, `PYTHON_CPU_COUNT` and `EMCC_CORES` to
the declared job limit; CPython's stdlib compilation and Emscripten's system
library builder can otherwise choose their own worker counts. The original
port's `getconf _NPROCESSORS_ONLN` usage also needs the driver's existing job-limit
shim.

## Cache validity

The copied `sqlite-cache.py` helper verifies the selected patchset, recipes,
source archives, compiler entrypoint and actual compiler binary. It binds the
SQLite archive and headers, and the Python archive, Python headers and Python
`sqlite3` package files. A missing receipt, changed input, changed harvested
output or older Python archive without this verified build forces a rebuild.
The Python recipe's previous existence-only check cannot accept an old archive
built with `_sqlite3=n/a`.

These are dependency enablement receipts. They do not claim to verify every
unrelated file in the harvested Python installation. The source-build driver's
complete dependency inventory remains responsible for the final package's
overall harvested-file identity.

Preparation accepts only the original Python recipe or the exact already-patched
result. Unexpected helpers, path traversal, symlinked preparation destinations,
changed patch context and different existing receipts are rejected. The cache
verifier rejects symlinked sources and outputs; it allows the SDK's own `clang`
entrypoint only with a confined, hashed actual compiler target.

## Validation and scope

The dated evidence directory is
`compatibility/evidence/browser-sqlite-build-2026-10-23/`. It preserves genuine
failed setup attempts alongside the successful SQLite compile.

The complete patched CPython recipe also finished successfully in 552.195481
seconds with one build job. Its normal configure checks enabled `_sqlite3`, and
the resulting archive passed the real extension and SQLite symbol checks.
`python-attempt-1/` retains its full raw build output and verified harvest receipt.

The same compiled SQLite WebAssembly diagnostic has executed with exit code 0
in the pinned Node runtime and Chrome 155.0.8059.39. It exercised real SQL with
WAL and read-write/read-only URI connections, exclusive and immediate
transactions, UPSERT RETURNING, rollback, foreign-key cascade, integrity checks,
and close/reopen within the same filesystem instance. `probe_sqlite.c` contains
this separate diagnostic. These are component observations and are not counted
as original Blender test passes.

The unchanged original disk hash module was then attempted with the actual
standalone CPython archive in Node and Chrome. Both exited 1 before discovering
any of the 12 expected cases: the original package initializer imports `bpy`,
which requires the complete Blender application. All 12 remain unobserved in
these component attempts. A separate Python binding diagnostic also retains its
initial failed serialization assumption, reproduced with the same source in
native Blender's Python and Chrome. The evidence summary distinguishes these
failures from the successful builds and C diagnostic.

An original Blender test result requires execution of the unchanged original
test on the rebuilt Blender artifact, with its native case identities and
original driver context. Successful library compilation, a standalone Python
component result, or this SQLite diagnostic cannot substitute for that result.
Browser reload durability, cross-tab locking, arbitrary dynamic extensions and
the complete Blender application's feature parity are not established by these
component checks.
