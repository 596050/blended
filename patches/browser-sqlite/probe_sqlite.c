/* Component diagnostic only. This does not replace any original Blender test. */
#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void require_ok(int result, sqlite3 *database, const char *operation)
{
  if (result != SQLITE_OK) {
    fprintf(stderr, "SQLite diagnostic %s: rc=%d %s\n", operation, result,
            database ? sqlite3_errmsg(database) : "no database");
    exit(1);
  }
}

static void execute(sqlite3 *database, const char *sql)
{
  require_ok(sqlite3_exec(database, sql, NULL, NULL, NULL), database, sql);
}

static void require_text(sqlite3 *database, const char *sql, const char *expected)
{
  sqlite3_stmt *statement = NULL;
  require_ok(sqlite3_prepare_v2(database, sql, -1, &statement, NULL), database, sql);
  const int step = sqlite3_step(statement);
  const unsigned char *actual = step == SQLITE_ROW ? sqlite3_column_text(statement, 0) : NULL;
  if (actual == NULL || strcmp((const char *)actual, expected) != 0) {
    fprintf(stderr, "SQLite diagnostic query mismatch: %s; rc=%d got=%s expected=%s\n",
            sql, step, actual ? (const char *)actual : "<no row>", expected);
    exit(1);
  }
  require_ok(sqlite3_finalize(statement), database, "finalize");
}

int main(void)
{
  sqlite3 *writer = NULL;
  sqlite3 *reader = NULL;
  require_ok(sqlite3_open_v2("/tmp/sqlite-component-probe.sqlite", &writer,
                            SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE, NULL), writer, "open writer");
  execute(writer, "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=1;");
  require_text(writer, "PRAGMA journal_mode=WAL", "wal");
  execute(writer, "PRAGMA synchronous=normal;");
  execute(writer, "CREATE TABLE parent(id INTEGER PRIMARY KEY, value TEXT NOT NULL);"
                  "CREATE TABLE child(id INTEGER REFERENCES parent(id) ON DELETE CASCADE);");
  require_ok(sqlite3_open_v2("file:/tmp/sqlite-component-probe.sqlite?mode=ro", &reader,
                            SQLITE_OPEN_READONLY | SQLITE_OPEN_URI, NULL), reader, "open read-only URI");
  execute(reader, "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=1;");
  require_text(reader, "PRAGMA journal_mode=WAL", "wal");
  execute(reader, "PRAGMA synchronous=normal;");
  execute(writer, "BEGIN EXCLUSIVE;");
  require_text(writer, "INSERT INTO parent(id,value) VALUES(1,'first') "
                       "ON CONFLICT(id) DO UPDATE SET value=excluded.value RETURNING value", "first");
  execute(writer, "INSERT INTO child VALUES(1); COMMIT;");
  execute(reader, "BEGIN IMMEDIATE;");
  require_text(reader, "SELECT value FROM parent WHERE id=1", "first");
  execute(reader, "ROLLBACK;");
  execute(writer, "BEGIN EXCLUSIVE; UPDATE parent SET value='rolled back' WHERE id=1; ROLLBACK;");
  require_text(reader, "SELECT value FROM parent WHERE id=1", "first");
  execute(writer, "DELETE FROM parent WHERE id=1;");
  require_text(reader, "SELECT COUNT(*) FROM child", "0");
  require_text(writer, "PRAGMA integrity_check", "ok");
  execute(writer, "INSERT INTO parent VALUES(2,'reopened');");
  require_ok(sqlite3_close(reader), reader, "close reader");
  require_ok(sqlite3_close(writer), writer, "close writer and checkpoint");
  writer = NULL;
  require_ok(sqlite3_open_v2("file:/tmp/sqlite-component-probe.sqlite?mode=ro", &reader,
                            SQLITE_OPEN_READONLY | SQLITE_OPEN_URI, NULL), reader, "reopen read-only");
  require_text(reader, "SELECT value FROM parent WHERE id=2", "reopened");
  require_text(reader, "PRAGMA integrity_check", "ok");
  require_ok(sqlite3_close(reader), reader, "close reopened database");
  printf("{\"kind\":\"sqlite-wasm-component-diagnostic\",\"sqlite_version\":\"%s\","
         "\"threadsafe_compile_mode\":%d,\"wal_dual_connection\":true,"
         "\"upsert_returning\":true,\"rollback\":true,\"foreign_key_cascade\":true,"
         "\"close_reopen_same_filesystem\":true,\"integrity_check\":true,"
         "\"original_blender_tests_executed\":false,\"full_feature_parity\":false}\n",
         sqlite3_libversion(), sqlite3_threadsafe());
  return 0;
}
