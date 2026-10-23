// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Blender 94363991e7dcf39e2d70614aa002ab6f67764a5d
// source/blender/blenlib/tests/BLI_math_vector_test.cc:219
// This is evaluated by rustc in both native and wasm32 builds, not a runtime pass stub.
pub const VECTOR_SIGNED_ZERO_HASH: () = assert!(
    crate::hashing::hash_float3([0.0_f32,0.0_f32,0.0_f32]) ==
    crate::hashing::hash_float3([-0.0_f32,-0.0_f32,-0.0_f32]),
    "Blender vector signed-zero hash invariant"
);
