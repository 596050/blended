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

# Match Blender's selected AV1 backends. Emscripten embeds both backends into
# libheif instead of requiring native dynamic plugin loading.
bc_configure \
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
