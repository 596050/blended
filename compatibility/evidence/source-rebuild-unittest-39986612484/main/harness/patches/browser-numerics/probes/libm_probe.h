/* SPDX-FileCopyrightText: 2026 Blended contributors
 * SPDX-License-Identifier: Apache-2.0 */
#ifndef BLENDED_LIBM_PROBE_H
#define BLENDED_LIBM_PROBE_H
#include <stdint.h>
#include <math.h>
#define GET_FLOAT_WORD(w,d) do { union { float f; uint32_t u; } v = { (d) }; (w) = v.u; } while (0)
#define SET_FLOAT_WORD(d,w) do { union { uint32_t u; float f; } v = { (w) }; (d) = v.f; } while (0)
#endif
