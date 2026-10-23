// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-3.0-or-later
//! The pinned BLI DefaultHash<float> and three-component vector combination.
pub const fn hash_f32(value:f32)->u64 {
    if value==0.0 {0} else {value.to_bits() as u64}
}
pub const fn hash_float3(values:[f32;3])->u64 {
    hash_f32(values[0]) ^ hash_f32(values[1]).wrapping_mul(19349669) ^ hash_f32(values[2]).wrapping_mul(83492791)
}
