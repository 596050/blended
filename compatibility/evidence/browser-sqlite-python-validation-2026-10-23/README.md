# Separate CPython SQLite binding diagnostic, version 2

The same diagnostic source completed with exit code 0 in native Blender's Python
and the actual Emscripten CPython component in Chrome 155.0.8059.39. Both used
CPython 3.13.13 and SQLite 3.51.3. The browser imported the real statically built
`_sqlite3` extension from the successful dependency build.

**This is a separately authored component diagnostic. It adds zero original
Blender browser test passes.** The original 12 disk hash cases still require the
rebuilt Blender application with real `bpy`. Their earlier import failures remain
preserved in `browser-sqlite-build-2026-10-23/`.

## Why version 2 exists

Version 1 attempted to query a database deserialized from a WAL-mode image. That
same source raised `sqlite3.OperationalError: unable to open database file` with
both native Blender's Python and the browser component. Those raw failures and
the original diagnostic source remain unchanged.

[SQLite's original deserialize contract](https://www.sqlite.org/c3ref/deserialize.html)
documents that WAL-mode serialized images produce `SQLITE_CANTOPEN` when used.
Version 2 explicitly verifies that rejection, including its actual numeric code
14 and name. A separate successful serialization round trip uses a fresh
ordinary in-memory database. No database header bytes, original Blender sources,
original tests or original assertions were modified. `precondition-reference.json`
records the documentation used to correct this diagnostic's own precondition.

## Actual observations

| Scope | Native Python | Chrome component |
| --- | --- | --- |
| Process/runtime completion | Exit 0 | Exit 0; no runtime abort or page errors |
| Python and SQLite versions | 3.13.13 and 3.51.3 | 3.13.13 and 3.51.3 |
| WAL connections | Read-write and read-only URI connections succeeded | Same |
| Parameter binding | Text, integer and floating-point values preserved | Same |
| File hashing | The fixed UTF-8 input matched the asserted SHA-256 | Same |
| Transactions | Exclusive/immediate transactions, UPSERT RETURNING and rollback succeeded | Same |
| Python integration | UDF callback, trace callback and row factory succeeded | Same |
| Backup | SQLite copied the live database to an in-memory connection | Same |
| WAL image deserialization | Expected `SQLITE_CANTOPEN` was observed | Same |
| Normal image serialization | Serialized and deserialized content matched | Same |
| Foreign keys | Delete cascade succeeded | Same |
| Reopen and integrity | Database reopened within the same filesystem instance; integrity checks returned `ok` | Same |
| Extension form | Native shared extension | Built-in WebAssembly extension |

The raw output differs in the expected extension packaging metadata:
`actual_builtin_extension` is false natively and true in the browser. Every
other reported field is equal. `freeze-v2-evidence.py` checks this exact difference
and binds both executions and the byte-identical diagnostic source in
`summary.json`. The Chrome console's unrelated missing favicon is preserved in
the raw output.

## Recovery and limits

`component-build-v2/` preserves the exact runtime build receipt, build log,
diagnostic entrypoint and generated JavaScript. The Wasm and preload payload are
byte-identical to the prior measured Python component and are already preserved
under `common/` in
`../browser-sqlite-build-2026-10-23/python-component-artifacts.tar.gz`.
The summary hashes the archive and verifies both members. Place the version 2
JavaScript together with those original `python-sqlite.wasm` and
`python-sqlite.data` files to reconstruct this measured component. Historical
receipt paths remain intact; copies are mapped by hash without rewriting history.

This evidence does not establish complete Python stdlib coverage, browser reload
durability, cross-tab or cross-process locking, arbitrary native extension
loading, the original 12 Blender case outcomes, or full Blender feature parity.
