// SPDX-FileCopyrightText: 2018 Blender Authors
// SPDX-FileCopyrightText: 2026 Blended contributors
// Diagnostic extraction of Blender intern/eigen/intern/matrix.cc.
// SPDX-License-Identifier: GPL-2.0-or-later
#include <Eigen/Core>
#include <Eigen/Dense>
#include <cstring>
#ifndef PROBE_INVERSE_NAME
#define PROBE_INVERSE_NAME inverse_sse
#endif
extern "C" bool PROBE_INVERSE_NAME(const float *matrix, float *inverse) {
  Eigen::Map<Eigen::Matrix4f> M = Eigen::Map<Eigen::Matrix4f>((float *)matrix);
  Eigen::Matrix4f R;
  bool invertible = true;
  M.computeInverseWithCheck(R, invertible, 0.0f);
  if (!invertible) R = Eigen::Matrix4f::Zero();
  memcpy(inverse, R.data(), sizeof(float) * 16);
  return invertible;
}
