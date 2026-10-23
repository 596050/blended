#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 blender-web contributors
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Build OpenImageIO with the original pinned image codecs for wasm, static, -pthread. Version pinned from
# upstream/build_files/build_environment/cmake/versions.cmake (OPENIMAGEIO_VERSION).
#
# blenlib PUBLIC-links OpenImageIO::OpenImageIO (dependency_targets.cmake:143) so
# this is on the M1 tier-(a) gtest critical path. We enable ONLY the readers the
# headless core needs plus WebP, JPEG2000, HEIF/AVIF and DPX; disable features that
# costs host-side tool builds or extra deps we have not cross-compiled:
#   - no OIIO tools (oiiotool/iconvert/... are host binaries we can't run in wasm)
#   - no Python bindings, no plugin DSO loading (EMBEDPLUGINS on = static formats)
#   - no Raw/JXL/GIF/DICOM/Ptex/FFmpeg/OpenVDB/Nuke/OpenCV/Qt/
#     Freetype/OCIO/TBB
#   - USE_SIMD=0: never let OIIO probe the HOST (x86 sse4.2) — the wasm stack is
#     -pthread only (no -msimd128), matching openjph/tiff.
#   - USE_EXTERNAL_PUGIXML=OFF: use OIIO's bundled pugixml (avoids building it).
# See notes/deps-oiio.md for the cross-compile host-tool analysis.
# Rebuild unconditionally: the old trimmed OIIO config cannot qualify this profile.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PREFIX="$ROOT/lib/wasm"
SCRATCH="$ROOT/build-deps/openimageio"
CACHE="$ROOT/build-deps/_cache"
NPROC="${BLENDED_BUILD_JOBS:-1}"
case "$NPROC" in 1|2|3|4) ;; *) echo "codec builds require 1 to 4 jobs" >&2; exit 2 ;; esac
export EMCC_CORES="$NPROC"
source "$ROOT/scripts/deps/codec-common.sh"

OIIO_VERSION="3.1.13.1"
OIIO_URL="https://github.com/AcademySoftwareFoundation/OpenImageIO/archive/refs/tags/v${OIIO_VERSION}.tar.gz"
OIIO_MD5="9f6f083900680b79ca4a136270103844"
TARBALL="$CACHE/OpenImageIO-${OIIO_VERSION}.tar.gz"

CONFIG_MARKER="$PREFIX/lib/cmake/OpenImageIO/OpenImageIOConfig.cmake"

# --- prerequisites from the shared prefix (build them if missing) ---
[ -f "$PREFIX/lib/cmake/Imath/ImathConfig.cmake" ]                  || bash "$ROOT/scripts/deps/imath.sh"
[ -f "$PREFIX/lib/cmake/OpenEXR/OpenEXRConfig.cmake" ]              || bash "$ROOT/scripts/deps/openexr.sh"
[ -f "$PREFIX/lib/cmake/tiff/tiff-config.cmake" ]                   || bash "$ROOT/scripts/deps/libtiff.sh"
[ -f "$PREFIX/lib/libpng16.a" ]                                     || bash "$ROOT/scripts/deps/libpng.sh"
[ -f "$PREFIX/lib/libjpeg.a" ]                                      || bash "$ROOT/scripts/deps/libjpeg.sh"
[ -f "$PREFIX/lib/cmake/fmt/fmt-config.cmake" ]                     || bash "$ROOT/scripts/deps/fmt.sh"
[ -f "$PREFIX/share/cmake/tsl-robin-map/tsl-robin-mapConfig.cmake" ] || bash "$ROOT/scripts/deps/robinmap.sh"
[ -f "$PREFIX/lib/libz.a" ]                                         || bash "$ROOT/scripts/deps/zlib.sh"
# OpenColorIO is a HARD dependency of OIIO 3.1 (color_ocio.cpp is unconditional).
[ -f "$PREFIX/lib/cmake/OpenColorIO/OpenColorIOConfig.cmake" ]      || bash "$ROOT/scripts/deps/opencolorio.sh"
EXPAT_DIR="$(dirname "$(ls "$PREFIX"/lib/cmake/expat-*/expat-config.cmake | head -1)")"

# Codec prerequisites were built explicitly by the selected build driver.
for BC_LIB in webp webpmux webpdemux sharpyuv openjp2 aom heif; do
  test -s "$PREFIX/lib/lib${BC_LIB}.a" || { echo "missing codec: $BC_LIB" >&2; exit 1; }
done
: "${EM_CACHE:?Set EM_CACHE to a build-specific directory}"
BC_EM_CACHE="$EM_CACHE"
# shellcheck disable=SC1091
source "$ROOT/tools/emsdk/emsdk_env.sh"
export EM_CACHE="$BC_EM_CACHE"

mkdir -p "$CACHE" "$SCRATCH"
if [ ! -f "$TARBALL" ]; then
  curl -fL --retry 3 -o "$TARBALL" "$OIIO_URL"
fi
GOT_MD5="$(md5 -q "$TARBALL" 2>/dev/null || md5sum "$TARBALL" | awk '{print $1}')"
if [ "$GOT_MD5" != "$OIIO_MD5" ]; then
  echo "openimageio: MD5 mismatch (got $GOT_MD5 want $OIIO_MD5)" >&2
  exit 1
fi

bc_check_sha256 "$TARBALL" 0fc59b8e2708ded02d3793b8f3331f037ed49bfcde38158f05ac0e876ebb85b7

SRC="$SCRATCH/OpenImageIO-${OIIO_VERSION}"
rm -rf "$SRC"
tar -xzf "$TARBALL" -C "$SCRATCH"

# --- source patch: OIIO 3.1 marks OpenColorIO REQUIRED but then references the
# OpenColorIO::OpenColorIO target UNCONDITIONALLY (externalpackages.cmake), so a
# USE_OPENCOLORIO=OFF build dies in get_target_property on a non-existent target.
# Blender never hits this (it builds WITH OCIO). We don't need OCIO inside OIIO
# for M1 — Blender links OCIO directly — so guard the target reference. See
# notes/deps-oiio.md. Idempotent (source re-extracted each run).
EXTPKG="$SRC/src/cmake/externalpackages.cmake"
sed -i \
  's/^if (NOT OPENCOLORIO_INCLUDES)$/if (NOT OPENCOLORIO_INCLUDES AND TARGET OpenColorIO::OpenColorIO)/' \
  "$EXTPKG"
# ...and libOpenImageIO unconditionally LINKS OpenColorIO::OpenColorIO. The OCIO
# source paths are all #ifdef USE_OPENCOLORIO (definition only added when the
# package is found), so making the link itself conditional yields a valid
# OCIO-less library. Rebuild OIIO with OCIO if a consumer ever needs its
# ImageBufAlgo::colorconvert (Blender does not — it links intern/opencolorio).
sed -i \
  's/^\( *\)OpenColorIO::OpenColorIO$/\1$<TARGET_NAME_IF_EXISTS:OpenColorIO::OpenColorIO>/' \
  "$SRC/src/libOpenImageIO/CMakeLists.txt"

# --- wasm platform porting: OIIO's libutil has __linux__/__APPLE__/... branches
# that don't include Emscripten (musl libc). Teach it about __EMSCRIPTEN__:
#   * musl provides strcasecmp_l/strncasecmp_l in <strings.h> -> take the glibc
#     branch; add the include.
#   * emscripten needs <unistd.h> for isatty()/usleep() (the __linux__ include
#     block is skipped).
#   * this_program_path(): no /proc or dyld in the sandbox -> r=0 (empty path),
#     matching the __GNU__/_WIN32 "can't determine" path.
SU="$SRC/src/libutil"
# Add __EMSCRIPTEN__ to every glibc-family guard (the c_loc locale def AND the
# strcasecmp_l/strncasecmp_l branches must flip together, else one references a
# c_loc the other never defined). musl provides both the _l funcs and newlocale.
sed -i 's/defined(__GLIBC__)/defined(__GLIBC__) || defined(__EMSCRIPTEN__)/g' \
  "$SU/strutil.cpp"
perl -0777 -i -pe 's{#include <OpenImageIO/platform.h>\n}{#include <OpenImageIO/platform.h>\n#include <strings.h>  // emscripten/musl: strcasecmp_l\n#include <locale.h>   // emscripten/musl: newlocale/LC_ALL_MASK\n}' \
  "$SU/strutil.cpp"
# emscripten needs <unistd.h> for isatty()/usleep() (the __linux__ include block
# is skipped on this platform).
perl -0777 -i -pe 's{#include <OpenImageIO/platform.h>\n}{#include <OpenImageIO/platform.h>\n#ifdef __EMSCRIPTEN__\n#  include <unistd.h>\n#  include <sys/ioctl.h>\n#  include <emscripten/heap.h>\n#endif\n}' \
  "$SU/sysutil.cpp"
# A browser has no host-RAM syscall. Reporting zero trips OIIO_ASSERT during
# every Blender boot and can poison cache-sizing heuristics. The maximum
# growable Wasm heap is the actual address-space budget available to this
# process and is supplied without a JSPI/Asyncify round-trip.
perl -0777 -i -pe 's{#else\n    // No idea what platform this is\n    OIIO_ASSERT\(\n        0 && "Need to implement Sysutil::physical_memory on this platform"\);}{#elif defined(__EMSCRIPTEN__)\n    return emscripten_get_heap_max();\n\n#else\n    // No idea what platform this is\n    OIIO_ASSERT(\n        0 && "Need to implement Sysutil::physical_memory on this platform");}' \
  "$SU/sysutil.cpp"
# this_program_path(): no /proc or dyld in the sandbox. Fold __EMSCRIPTEN__ into
# the existing "can't determine -> r=0" elif so it returns an empty path instead
# of tripping the unimplemented-platform static assert.
sed -i 's/#elif defined(__GNU__) || defined(__OpenBSD__) || defined(_WIN32)/#elif defined(__GNU__) || defined(__OpenBSD__) || defined(_WIN32) || defined(__EMSCRIPTEN__)/' \
  "$SU/sysutil.cpp"
# ustring::TableRep — the libc++ branch pokes std::string's private __long fields
# (__cap_/__size_/__data_) for long strings, assuming a specific libc++ layout.
# Emscripten's libc++ std::string layout does NOT match, so ustring::string()
# comes back EMPTY for any string >= the SSO threshold (e.g. "ResolutionUnit", 14
# chars, is "long" on wasm32) while c_str() stays correct. That empty string()
# breaks OIIO's PNG writer (put_parameter reads name().string(), fails to skip
# "ResolutionUnit", and emits a tEXt chunk with an EMPTY keyword -> libpng
# "tEXt: invalid keyword" -> every PNG-with-metadata write aborts). OIIO already
# EXCLUDES aarch64 from this branch (falls to the safe `str = strref` copy);
# exclude __EMSCRIPTEN__ the same way. Costs one extra small alloc per interned
# long string; buys correct ustring::string() everywhere on wasm.
sed -i 's/#elif defined(_LIBCPP_VERSION) \&\& !defined(__aarch64__)/#elif defined(_LIBCPP_VERSION) \&\& !defined(__aarch64__) \&\& !defined(__EMSCRIPTEN__)/' \
  "$SU/ustring.cpp"

BUILD="$SCRATCH/build"
rm -rf "$BUILD"

# -fexceptions: OIIO throws/catches; wasm needs it explicitly (matches TBB consumers).
CFLAGS="-pthread -fexceptions"

emcmake cmake -S "$SRC" -B "$BUILD" -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DCMAKE_PREFIX_PATH="$PREFIX" \
  -DCMAKE_CXX_STANDARD=17 \
  -DBUILD_SHARED_LIBS=OFF \
  -DLINKSTATIC=ON \
  -DOpenImageIO_REQUIRED_DEPS="TIFF;OpenEXR;PNG;libjpeg-turbo;fmt;Robinmap;ZLIB;OpenColorIO;WebP;OpenJPEG;Libheif" \
  -DOpenImageIO_BUILD_MISSING_DEPS="" \
  -DOIIO_BUILD_TOOLS=OFF \
  -DOIIO_BUILD_TESTS=OFF \
  -DBUILD_TESTING=OFF \
  -DBUILD_DOCS=OFF \
  -DINSTALL_DOCS=OFF \
  -DINSTALL_FONTS=OFF \
  -DEMBEDPLUGINS=ON \
  -DUSE_SIMD=0 \
  -DSTOP_ON_WARNING=OFF \
  -DUSE_EXTERNAL_PUGIXML=OFF \
  -DUSE_PYTHON=OFF \
  -DUSE_TBB=OFF \
  -DUSE_OPENCOLORIO=ON \
  -DUSE_FREETYPE=OFF \
  -DUSE_QT=OFF \
  -DUSE_NUKE=OFF \
  -DUSE_OPENCV=OFF \
  -DUSE_OPENVDB=OFF \
  -DUSE_FFMPEG=OFF \
  -DUSE_WEBP=ON \
  -DUSE_OPENJPEG=ON \
  -DUSE_LIBHEIF=ON \
  -DUSE_LIBRAW=OFF \
  -DUSE_JXL=OFF \
  -DUSE_GIF=OFF \
  -DUSE_DCMTK=OFF \
  -DUSE_PTEX=OFF \
  -DUSE_DICOM=OFF \
  -DUSE_R3DSDK=OFF \
  -DUSE_BZIP2=OFF \
  -DWebP_DIR="$PREFIX/share/WebP/cmake" \
  -DOpenJPEG_DIR="$PREFIX/lib/cmake/openjpeg-2.5" \
  -DLibheif_DIR="$PREFIX/lib/cmake/libheif" \
  -DOpenEXR_ROOT="$PREFIX" \
  -DImath_ROOT="$PREFIX" \
  -Dfmt_ROOT="$PREFIX" \
  -DRobinmap_ROOT="$PREFIX" \
  -DROBINMAP_INCLUDE_DIR="$PREFIX/include" \
  -DImath_DIR="$PREFIX/lib/cmake/Imath" \
  -DOpenEXR_DIR="$PREFIX/lib/cmake/OpenEXR" \
  -DOpenColorIO_DIR="$PREFIX/lib/cmake/OpenColorIO" \
  -Dyaml-cpp_DIR="$PREFIX/lib/cmake/yaml-cpp" \
  -Dexpat_DIR="$EXPAT_DIR" \
  -Dexpat_INCLUDE_DIR="$PREFIX/include" \
  -Dexpat_LIBRARY="$PREFIX/lib/libexpat.a" \
  -Dpystring_ROOT="$PREFIX" \
  -Dpystring_INCLUDE_DIR="$PREFIX/include" \
  -Dpystring_LIBRARY="$PREFIX/lib/libpystring.a" \
  -Dminizip-ng_INCLUDE_DIR="$PREFIX/include/minizip-ng/minizip" \
  -Dminizip-ng_LIBRARY="$PREFIX/lib/libminizip.a" \
  -Dlibdeflate_DIR="$PREFIX/lib/cmake/libdeflate" \
  -Dopenjph_DIR="$PREFIX/lib/cmake/openjph" \
  -Dfmt_DIR="$PREFIX/lib/cmake/fmt" \
  -DTIFF_DIR="$PREFIX/lib/cmake/tiff" \
  -DPNG_DIR="$PREFIX/lib/cmake/PNG" \
  -Dlibjpeg-turbo_DIR="$PREFIX/lib/cmake/libjpeg-turbo" \
  -Dtsl-robin-map_DIR="$PREFIX/share/cmake/tsl-robin-map" \
  -DZLIB_ROOT="$PREFIX" \
  -DZLIB_INCLUDE_DIR="$PREFIX/include" \
  -DZLIB_LIBRARY="$PREFIX/lib/libz.a" \
  -DJPEG_ROOT="$PREFIX" \
  -DJPEG_INCLUDE_DIR="$PREFIX/include" \
  -DJPEG_LIBRARY="$PREFIX/lib/libjpeg.a" \
  -DPNG_ROOT="$PREFIX" \
  -DPNG_PNG_INCLUDE_DIR="$PREFIX/include" \
  -DPNG_LIBRARY="$PREFIX/lib/libpng16.a" \
  -DTIFF_INCLUDE_DIR="$PREFIX/include" \
  -DTIFF_LIBRARY="$PREFIX/lib/libtiff.a" \
  -DCMAKE_C_FLAGS="$CFLAGS" \
  -DCMAKE_CXX_FLAGS="$CFLAGS"

emmake cmake --build "$BUILD" --target install -j"$NPROC"

if [ ! -f "$CONFIG_MARKER" ]; then
  echo "openimageio: install did not produce $CONFIG_MARKER" >&2
  exit 1
fi

# --- link test: construct a real ImageSpec through emcc (pulls OIIO symbols) ---
VDIR="$SCRATCH/verify"
mkdir -p "$VDIR"
cat > "$VDIR/t.cpp" <<'EOF'
#include <cstdio>
#include <emscripten/heap.h>
#include <OpenImageIO/imageio.h>
#include <OpenImageIO/sysutil.h>
#include <OpenImageIO/typedesc.h>
#include <libheif/heif.h>
int main() {
  for (const char *format : {"webp", "jpeg2000", "heif", "dpx"}) {
    if (!OIIO::ImageInput::create(format) || !OIIO::ImageOutput::create(format)) {
      std::fprintf(stderr, "Missing required static OIIO plugin: %s\n", format);
      return 2;
    }
  }
  if (!heif_have_encoder_for_format(heif_compression_AV1) ||
      !heif_have_decoder_for_format(heif_compression_AV1)) {
    std::fprintf(stderr, "Missing required static AV1 encoder or decoder\n");
    return 3;
  }
  OIIO::ImageSpec spec(64, 48, 4, OIIO::TypeDesc::UINT8);
  // exercise a non-trivial method so the linker keeps real OIIO code
  std::string s = spec.serialize(OIIO::ImageSpec::SerialText);
  const size_t memory = OIIO::Sysutil::physical_memory();
  const size_t heap_size = emscripten_get_heap_size();
  const size_t heap_max = emscripten_get_heap_max();
  std::printf("physical_memory=%zu heap_size=%zu heap_max=%zu\n",
              memory, heap_size, heap_max);
  return (spec.width == 64 && spec.height == 48 && !s.empty()
          && memory == heap_max && memory > heap_size) ? 0 : 1;
}
EOF
LIBS="$(ls \
  "$PREFIX"/lib/libOpenImageIO.a \
  "$PREFIX"/lib/libOpenImageIO_Util.a \
  "$PREFIX"/lib/libOpenColorIO.a \
  "$PREFIX"/lib/libwebp.a \
  "$PREFIX"/lib/libwebpmux.a \
  "$PREFIX"/lib/libwebpdemux.a \
  "$PREFIX"/lib/libsharpyuv.a \
  "$PREFIX"/lib/libopenjp2.a \
  "$PREFIX"/lib/libheif.a \
  "$PREFIX"/lib/libaom.a \
  "$PREFIX"/lib/libtiff.a \
  "$PREFIX"/lib/libOpenEXR*.a \
  "$PREFIX"/lib/libIlmThread*.a \
  "$PREFIX"/lib/libIex*.a \
  "$PREFIX"/lib/libImath*.a \
  "$PREFIX"/lib/libpng16.a \
  "$PREFIX"/lib/libjpeg.a \
  "$PREFIX"/lib/libdeflate.a \
  "$PREFIX"/lib/libopenjph.a \
  "$PREFIX"/lib/libzstd.a \
  "$PREFIX"/lib/libfmt.a \
  "$PREFIX"/lib/libyaml-cpp.a \
  "$PREFIX"/lib/libexpat.a \
  "$PREFIX"/lib/libpystring.a \
  "$PREFIX"/lib/libminizip.a \
  "$PREFIX"/lib/libz.a 2>/dev/null)"
em++ -pthread -fexceptions -std=c++17 -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=33554432 \
  -I"$PREFIX/include" \
  "$VDIR/t.cpp" -Wl,--start-group $LIBS -Wl,--end-group -o "$VDIR/t.js"
test -f "$VDIR/t.wasm"
node "$VDIR/t.js"
echo "openimageio: verify static codecs, AV1 backends, link and physical-memory runtime OK"

rm -rf "$SCRATCH"
echo "openimageio ${OIIO_VERSION}: installed to $PREFIX (config: lib/cmake/OpenImageIO)"
