#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Shared setup for the optional original Blender 5.2 codec dependencies.
# Recipes are installed in the pinned port's scripts/deps directory.

bc_check_sha256() {
  python3 - "$1" "$2" <<'PY'
import hashlib
from pathlib import Path
import sys
p = Path(sys.argv[1])
h = hashlib.sha256(p.read_bytes()).hexdigest()
if h != sys.argv[2]:
    raise SystemExit(f"SHA256 mismatch for {p}: {h}")
PY
}

bc_prepare() {
  BC_NAME="$1"
  BC_FILENAME="$2"
  BC_URL="$3"
  BC_SHA256="$4"
  BC_TOPDIR="$5"
  BC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  BC_PREFIX="$BC_ROOT/lib/wasm"
  BC_SCRATCH="$BC_ROOT/build-deps/$BC_NAME"
  BC_CACHE="$BC_ROOT/build-deps/_cache"
  BC_JOBS="${BLENDED_BUILD_JOBS:-1}"
  case "$BC_JOBS" in 1|2|3|4) ;; *) echo "codec builds require 1 to 4 jobs" >&2; exit 2 ;; esac
  : "${EM_CACHE:?Set EM_CACHE to a build-specific directory before running codec recipes}"

  # shellcheck disable=SC1091
  source "$BC_ROOT/tools/emsdk/emsdk_env.sh"
  mkdir -p "$BC_CACHE" "$BC_PREFIX"
  BC_TARBALL="$BC_CACHE/$BC_FILENAME"
  if [ ! -f "$BC_TARBALL" ]; then
    curl -fL --retry 3 -o "$BC_TARBALL" "$BC_URL"
  fi
  bc_check_sha256 "$BC_TARBALL" "$BC_SHA256"

  # Reconfigure each recipe from verified source. An old archive or CMake
  # marker must not silently qualify a different codec feature profile.
  rm -rf "$BC_SCRATCH"
  mkdir -p "$BC_SCRATCH"
  python3 - "$BC_TARBALL" "$BC_SCRATCH" "$BC_TOPDIR" <<'PY'
from pathlib import Path, PurePosixPath
import sys
import tarfile
archive, scratch, expected_root = sys.argv[1:]
with tarfile.open(archive) as source:
    for member in source.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != expected_root:
            raise SystemExit(f"Unexpected archive path: {member.name}")
    source.extractall(scratch, filter="data")
assert (Path(scratch) / expected_root / "CMakeLists.txt").is_file()
PY
  BC_SOURCE="$BC_SCRATCH/$BC_TOPDIR"
  BC_BUILD="$BC_SCRATCH/build"
}

bc_configure() {
  emcmake cmake -S "$BC_SOURCE" -B "$BC_BUILD" -G "Unix Makefiles" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_INSTALL_PREFIX="$BC_PREFIX" \
    -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_PREFIX_PATH="$BC_PREFIX" \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_C_FLAGS="-pthread -fexceptions" \
    -DCMAKE_CXX_FLAGS="-pthread -fexceptions" \
    "$@"
}

bc_install() {
  emmake cmake --build "$BC_BUILD" --target install --parallel "$BC_JOBS"
  local artifact
  for artifact in "$@"; do
    test -s "$BC_PREFIX/$artifact" || { echo "missing codec artifact: $artifact" >&2; exit 1; }
  done
}
