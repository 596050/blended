#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Original Blender 5.2 OpenJPEG 2.5.3; original encoder and decoder are retained.
set -euo pipefail
source "$(dirname "$0")/codec-common.sh"
bc_prepare openjpeg openjpeg-v2.5.3.tar.gz \
  https://github.com/uclouvain/openjpeg/archive/v2.5.3.tar.gz \
  368fe0468228e767433c9ebdea82ad9d801a3ad1e4234421f352c8b06e7aa707 \
  openjpeg-2.5.3
bc_configure \
  -DBUILD_STATIC_LIBS=ON \
  -DBUILD_CODEC=OFF \
  -DBUILD_TESTING=OFF \
  -DBUILD_UNIT_TESTS=OFF \
  -DBUILD_DOC=OFF \
  -DOPJ_USE_THREAD=ON
bc_install lib/libopenjp2.a include/openjpeg-2.5/openjpeg.h
