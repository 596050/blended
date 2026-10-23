"""Real CPython SQLite binding diagnostic; this is not an original Blender test."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile


assert sqlite3.sqlite_version == "3.51.3"
with tempfile.TemporaryDirectory(prefix="real-sqlite-component-") as temporary:
    root = Path(temporary)
    database = root / "database.sqlite"
    data_file = root / "unicode-file.txt"
    data_file.write_text("😺 Laksa & Quercus 😻", encoding="utf-8")
    hexdigest = hashlib.sha256(data_file.read_bytes()).hexdigest()
    assert hexdigest == "43231d711ce5992cd9090ffa5cbb8779148e291bc1472353cdeebd040bef0b93"
    writer = sqlite3.connect(database, isolation_level=None)
    writer.execute("PRAGMA busy_timeout=5000")
    writer.execute("PRAGMA foreign_keys=1")
    assert writer.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
    writer.execute("PRAGMA synchronous=normal")
    writer.executescript("""
        CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL);
        CREATE TABLE hashes(file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
                            value TEXT NOT NULL, size INTEGER NOT NULL, mtime REAL NOT NULL);
    """)
    reader = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, isolation_level=None)
    reader.execute("PRAGMA busy_timeout=5000")
    reader.execute("PRAGMA foreign_keys=1")
    assert reader.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
    reader.execute("PRAGMA synchronous=normal")
    writer.execute("BEGIN EXCLUSIVE")
    row = writer.execute("INSERT INTO files(id,path) VALUES(?,?) ON CONFLICT(id) "
                         "DO UPDATE SET path=excluded.path RETURNING id,path", (1, str(data_file))).fetchone()
    assert row == (1, str(data_file))
    state = data_file.stat()
    expected = (hexdigest, state.st_size, state.st_mtime)
    writer.execute("INSERT INTO hashes VALUES(?,?,?,?)", (1, *expected))
    writer.execute("COMMIT")
    reader.execute("BEGIN IMMEDIATE")
    assert reader.execute("SELECT value,size,mtime FROM hashes WHERE file_id=?", (1,)).fetchone() == expected
    reader.execute("ROLLBACK")
    writer.execute("BEGIN EXCLUSIVE")
    writer.execute("UPDATE hashes SET value=? WHERE file_id=1", ("rollback-marker",))
    writer.execute("ROLLBACK")
    assert reader.execute("SELECT value FROM hashes").fetchone() == (hexdigest,)
    callbacks = []
    writer.set_trace_callback(callbacks.append)
    writer.create_function("python_identity", 1, lambda value: value)
    assert writer.execute("SELECT python_identity(?)", (hexdigest,)).fetchone() == (hexdigest,)
    assert callbacks and "python_identity" in callbacks[-1]
    writer.set_trace_callback(None)
    reader.row_factory = sqlite3.Row
    row = reader.execute("SELECT value,size,mtime FROM hashes").fetchone()
    assert row["value"] == hexdigest and tuple(row) == expected
    reader.row_factory = None
    backup = sqlite3.connect(":memory:")
    writer.backup(backup)
    assert backup.execute("SELECT value,size,mtime FROM hashes").fetchone() == expected
    image = backup.serialize()
    restored = sqlite3.connect(":memory:")
    restored.deserialize(image)
    assert restored.execute("SELECT value,size,mtime FROM hashes").fetchone() == expected
    restored.close()
    backup.close()
    writer.execute("DELETE FROM files WHERE id=1")
    assert reader.execute("SELECT COUNT(*) FROM hashes").fetchone() == (0,)
    assert writer.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    writer.execute("INSERT INTO files VALUES(2, 'close-reopen')")
    reader.close()
    writer.close()
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as reopened:
        assert reopened.execute("SELECT path FROM files WHERE id=2").fetchone() == ("close-reopen",)
        assert reopened.execute("PRAGMA integrity_check").fetchone() == ("ok",)

print("BLENDED_SQLITE_PYTHON_DIAGNOSTIC " + json.dumps({
    "kind": "cpython-sqlite-component-diagnostic",
    "python_version": list(sys.version_info[:3]),
    "sqlite_version": sqlite3.sqlite_version,
    "actual_builtin_extension": "_sqlite3" in sys.builtin_module_names,
    "wal_dual_connection": True,
    "parameter_binding_text_integer_float": True,
    "utf8_file_hash": True,
    "upsert_returning": True,
    "rollback": True,
    "python_function_and_trace_callbacks": True,
    "row_factory": True,
    "backup_and_serialization": True,
    "foreign_key_cascade": True,
    "close_reopen_same_filesystem": True,
    "integrity_check": True,
    "original_blender_tests_executed": False,
    "full_feature_parity": False,
}), flush=True)
