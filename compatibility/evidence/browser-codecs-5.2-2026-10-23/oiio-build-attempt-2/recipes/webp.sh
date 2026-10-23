#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Original Blender 5.2 libwebp 1.6.0, including encoder, decoder, mux and demux.
set -euo pipefail
source "$(dirname "$0")/codec-common.sh"
bc_prepare webp libwebp-1.6.0.tar.gz \
  https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0.tar.gz \
  e4ab7009bf0629fd11982d4c2aa83964cf244cffba7347ecd39019a9e38c4564 \
  libwebp-1.6.0

# These match Blender's original utility exclusions. The libraries stay on.
# Generic C avoids host CPU detection and preserves the original codec APIs.
bc_configure \
  -DWEBP_ENABLE_SIMD=OFF \
  -DWEBP_USE_THREAD=ON \
  -DWEBP_BUILD_LIBWEBPMUX=ON \
  -DWEBP_BUILD_WEBP_JS=OFF \
  -DWEBP_BUILD_ANIM_UTILS=OFF \
  -DWEBP_BUILD_CWEBP=OFF \
  -DWEBP_BUILD_DWEBP=OFF \
  -DWEBP_BUILD_GIF2WEBP=OFF \
  -DWEBP_BUILD_IMG2WEBP=OFF \
  -DWEBP_BUILD_VWEBP=OFF \
  -DWEBP_BUILD_WEBPINFO=OFF \
  -DWEBP_BUILD_WEBPMUX=OFF \
  -DWEBP_BUILD_EXTRAS=OFF \
  -DWEBP_BUILD_FUZZTEST=OFF
bc_install lib/libwebp.a lib/libwebpmux.a lib/libwebpdemux.a lib/libsharpyuv.a
