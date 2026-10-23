#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Build the SQLite version selected by the original Blender 5.2 dependency pin.
# The real upstream amalgamation and Unix VFS remain unmodified.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PREFIX="$ROOT/lib/wasm"
CACHE="$ROOT/build-deps/_cache"
SCRATCH="$ROOT/build-deps/sqlite-blended"
ARCHIVE="sqlite-autoconf-3510300.tar.gz"
URL="https://www.sqlite.org/2026/$ARCHIVE"
SHA256="81f5be397049b0cae1b167f2225af7646fc0f82e4a9b3c48c9ea3a533e21d77a"

# emsdk_env.sh assigns its own cache. Keep the explicitly selected private cache.
BLENDED_CALLER_EM_CACHE="${EM_CACHE:-}"
source "$ROOT/tools/emsdk/emsdk_env.sh"
if [ -n "$BLENDED_CALLER_EM_CACHE" ]; then
  export EM_CACHE="$BLENDED_CALLER_EM_CACHE"
fi

if python3 "$ROOT/scripts/deps/sqlite-cache.py" verify sqlite "$ROOT"; then
  echo "sqlite 3.51.3: verified existing source, compiler, recipe, library and headers"
  exit 0
fi

mkdir -p "$CACHE" "$SCRATCH" "$PREFIX/lib" "$PREFIX/include"
if [ ! -f "$CACHE/$ARCHIVE" ]; then
  curl -fL --retry 3 --max-time 900 -o "$CACHE/$ARCHIVE.part" "$URL"
  printf '%s  %s\n' "$SHA256" "$CACHE/$ARCHIVE.part" | sha256sum --check --status
  mv "$CACHE/$ARCHIVE.part" "$CACHE/$ARCHIVE"
fi
printf '%s  %s\n' "$SHA256" "$CACHE/$ARCHIVE" | sha256sum --check --status
BUILD="$(mktemp -d "$SCRATCH/build.XXXXXX")"
tar -xf "$CACHE/$ARCHIVE" -C "$BUILD"
SRC="$BUILD/sqlite-autoconf-3510300"

# Original upstream Unix features, plus the native release's configure defaults.
# Preserve WAL, file locking, transactions, real SQL evaluation and load-extension
# API support. Browser filesystem/process limits remain runtime test obligations.
DEFINES=(
  -DSQLITE_SECURE_DELETE -DSQLITE_ENABLE_COLUMN_METADATA
  -DSQLITE_ENABLE_FTS3 -DSQLITE_ENABLE_FTS3_PARENTHESIS
  -DSQLITE_SOUNDEX -DSQLITE_ENABLE_UNLOCK_NOTIFY -DSQLITE_OMIT_LOOKASIDE=1
  -DSQLITE_ENABLE_DBSTAT_VTAB -DSQLITE_ENABLE_UPDATE_DELETE_LIMIT=1
  -DSQLITE_ENABLE_LOAD_EXTENSION -DSQLITE_LIKE_DOESNT_MATCH_BLOBS
  -DSQLITE_MAX_SCHEMA_RETRY=25 -DSQLITE_ENABLE_PREUPDATE_HOOK
  -DSQLITE_ENABLE_SESSION -DSQLITE_ENABLE_STMTVTAB -DSQLITE_MAX_VARIABLE_NUMBER=250000
  -DSQLITE_ENABLE_RTREE -DSQLITE_ENABLE_GEOPOLY -DSQLITE_THREADSAFE=1
  -DSQLITE_ENABLE_FTS4 -DSQLITE_ENABLE_FTS5 -DSQLITE_ENABLE_MATH_FUNCTIONS
  -DSQLITE_ENABLE_PERCENTILE -DSQLITE_DEFAULT_AUTOVACUUM=1
)
emcc -O2 -fexceptions -matomics -mbulk-memory -fPIC "${DEFINES[@]}" \
  -c "$SRC/sqlite3.c" -o "$BUILD/sqlite3.o"
emar rcs "$BUILD/libsqlite3.a" "$BUILD/sqlite3.o"
emranlib "$BUILD/libsqlite3.a"
emnm --defined-only "$BUILD/libsqlite3.a" > "$BUILD/defined-symbols.txt"
for name in sqlite3_open_v2 sqlite3_exec sqlite3_wal_checkpoint_v2 sqlite3_libversion sqlite3_serialize; do
  grep -Eq "[[:space:]]T[[:space:]]${name}$" "$BUILD/defined-symbols.txt"
done
install -m644 "$SRC/sqlite3.h" "$PREFIX/include/sqlite3.h"
install -m644 "$SRC/sqlite3ext.h" "$PREFIX/include/sqlite3ext.h"
install -m644 "$BUILD/libsqlite3.a" "$PREFIX/lib/.libsqlite3.a.tmp.$$"
mv "$PREFIX/lib/.libsqlite3.a.tmp.$$" "$PREFIX/lib/libsqlite3.a"
python3 "$ROOT/scripts/deps/sqlite-cache.py" record sqlite "$ROOT"
echo "sqlite 3.51.3: compiled genuine upstream library with WAL and original feature configuration"
