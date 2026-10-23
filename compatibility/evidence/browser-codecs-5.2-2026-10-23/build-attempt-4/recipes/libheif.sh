#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Original Blender 5.2 libheif 1.20.2 with its original AOM encoder/decoder.
set -euo pipefail
source "$(dirname "$0")/codec-common.sh"
bc_prepare libheif libheif-1.20.2.tar.gz \
  https://github.com/strukturag/libheif/releases/download/v1.20.2/libheif-1.20.2.tar.gz \
  68ac9084243004e0ef3633f184eeae85d615fe7e4444373a0a21cebccae9d12a \
  libheif-1.20.2
test -s "$BC_PREFIX/lib/libaom.a"

# Blender uses libheif's original C API inside OIIO. Its standalone JavaScript
# bindings are unused, and their raw-pointer conversions fail with SDK 6.0.5.
# Guard only that wrapper include; retain the original codec implementations.
BC_HEIF_PATCH="$BC_ROOT/scripts/deps/libheif-static-c-api.patch"
bc_check_sha256 "$BC_HEIF_PATCH" c87e160de9c1bda6262062fa4317d72450a5a564ee356f89cceb6d436f7db455
bc_check_sha256 "$BC_SOURCE/libheif/api/libheif/heif.cc" 3ecfc021816ce9013f7b5285a61961be2f8504dd505ce2405f82639a0d7783a2
patch --batch --fuzz=0 -d "$BC_SOURCE" -p1 < "$BC_HEIF_PATCH"
bc_check_sha256 "$BC_SOURCE/libheif/api/libheif/heif.cc" 12b0d0fe77f06d4fa4861469638c2bb832c22edea9c63e9055567ec7cabb6ff3

# Match Blender's selected AV1 backends. Emscripten embeds both backends into
# libheif instead of requiring native dynamic plugin loading.
bc_configure \
  -DCMAKE_CXX_FLAGS="-pthread -fexceptions -DLIBHEIF_DISABLE_EMBIND" \
  -DENABLE_PLUGIN_LOADING=OFF \
  -DWITH_AOM_ENCODER=ON \
  -DWITH_AOM_DECODER=ON \
  -DWITH_AOM_ENCODER_PLUGIN=OFF \
  -DWITH_AOM_DECODER_PLUGIN=OFF \
  -DWITH_DAV1D=OFF \
  -DWITH_FFMPEG_DECODER=OFF \
  -DWITH_JPEG_ENCODER=OFF \
  -DWITH_JPEG_DECODER=OFF \
  -DWITH_KVAZAAR=OFF \
  -DWITH_LIBDE265=OFF \
  -DWITH_LIBSHARPYUV=OFF \
  -DWITH_OPENJPH_ENCODER=OFF \
  -DWITH_OpenH264_DECODER=OFF \
  -DWITH_OpenJPEG_DECODER=OFF \
  -DWITH_OpenJPEG_ENCODER=OFF \
  -DWITH_RAV1E=OFF \
  -DWITH_SvtEnc=OFF \
  -DWITH_UVG266=OFF \
  -DWITH_VVDEC=OFF \
  -DWITH_VVENC=OFF \
  -DWITH_X265=OFF \
  -DAOM_INCLUDE_DIR="$BC_PREFIX/include" \
  -DAOM_LIBRARY="$BC_PREFIX/lib/libaom.a" \
  -DENABLE_MULTITHREADING_SUPPORT=ON \
  -DWITH_EXAMPLES=OFF \
  -DWITH_EXAMPLE_HEIF_VIEW=OFF \
  -DWITH_GDK_PIXBUF=OFF \
  -DBUILD_TESTING=OFF
bc_install lib/libheif.a include/libheif/heif.h
