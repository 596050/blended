#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Original Blender 5.2 libaom 3.13.1 and the exact upstream Blender patch.
set -euo pipefail
source "$(dirname "$0")/codec-common.sh"
bc_prepare aom libaom-3.13.1.tar.gz \
  https://storage.googleapis.com/aom-releases/libaom-3.13.1.tar.gz \
  19e45a5a7192d690565229983dad900e76b513a02306c12053fb9a262cbeca7d \
  libaom-3.13.1

BC_AOM_PATCH="$BC_ROOT/upstream/build_files/build_environment/patches/aom_6d2b7f71b98bfa28e372b1f2d85f137280bdb3de.diff"
bc_check_sha256 "$BC_AOM_PATCH" 5cb6ce17857a5283521d507dd834e6a45f8749468eeea1d2a9fd5f2e3e7544ea
patch --batch --fuzz=0 -p1 -d "$BC_SOURCE" < "$BC_AOM_PATCH"

# AOM's generic C backend avoids native assembly and CPU probing. Encoding,
# decoding, high bit depth and pthread support retain their upstream settings.
# A static archive is required by this Emscripten link profile.
bc_configure \
  -DAOM_TARGET_CPU=generic \
  -DCONFIG_AV1_ENCODER=1 \
  -DCONFIG_AV1_DECODER=1 \
  -DCONFIG_AV1_HIGHBITDEPTH=1 \
  -DCONFIG_MULTITHREAD=1 \
  -DENABLE_TESTDATA=OFF \
  -DENABLE_TESTS=OFF \
  -DENABLE_TOOLS=OFF \
  -DENABLE_EXAMPLES=OFF \
  -DENABLE_DOCS=OFF
bc_install lib/libaom.a include/aom/aom_encoder.h include/aom/aom_decoder.h
