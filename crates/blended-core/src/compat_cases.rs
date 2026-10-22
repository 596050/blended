// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Rust translations of the 17 runtime TEST cases in
// source/blender/blenlib/tests/BLI_math_vector_test.cc at
// 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// The separate signed-zero hash static_assert is NOT ported.
use crate::math::*;
type Case = (&'static str, fn() -> bool);
pub const CASES: [Case; 17] = [
    ("math_vector.ClampVecWithFloats", clamp_vec_with_floats),
    ("math_vector.test_invert_v3_safe", test_invert_v3_safe),
    ("math_vector.Clamp", clamp),
    ("math_vector.MinList", min_list),
    ("math_vector.MaxList", max_list),
    ("math_vector.InterpolateInt", interpolate_int),
    ("math_vector.InterpolateFloat", interpolate_float),
    ("math_vector.CeilToMultiple", ceil_to_multiple),
    ("math_vector.DivideCeil", divide_ceil),
    ("math_vector.Sign", sign),
    ("math_vector.sqrt", sqrt),
    ("math_vector.safe_sqrt", safe_sqrt),
    ("math_vector.rcp", rcp),
    ("math_vector.safe_rcp", safe_rcp),
    ("math_vector.exp", exp),
    ("math_vector.log", log),
    ("math_vector.square", square),
];
// Preserve EXPECT_FLOAT_EQ's four-ULP comparison, including signed zero.
fn ulps_equal(a: f32, b: f32) -> bool {
    if a.is_nan() || b.is_nan() { return false; }
    fn ordered(x: f32) -> u32 {
        let bits = x.to_bits();
        if bits & 0x8000_0000 != 0 { !bits + 1 } else { bits | 0x8000_0000 }
    }
    ordered(a).abs_diff(ordered(b)) <= 4
}
fn eqf<const N: usize>(a: [f32; N], b: [f32; N]) -> bool {
    a.into_iter().zip(b).all(|(x,y)| ulps_equal(x,y))
}
fn near(a: [f32;3], b: [f32;3]) -> bool {
    a.into_iter().zip(b).all(|(x,y)| (x-y).abs() <= 1e-6_f32)
}
fn clamp_vec_with_floats() -> bool {
    let mut a = [-1.0, -1.0]; let mut b = [0.5, 0.5]; let mut c = [2.0, 2.0];
    clamp_f32(&mut a, 0.0, 1.0); clamp_f32(&mut b, 0.0, 1.0); clamp_f32(&mut c, 0.0, 1.0);
    eqf(a, [0.0,0.0]) && eqf(b,[0.5,0.5]) && eqf(c,[1.0,1.0])
}
fn test_invert_v3_safe() -> bool {
    eqf(safe_rcp3([0.0,2.0,3.0]),[0.0,0.5,0.33333333333_f32])
    && eqf(safe_rcp3([1.0,2.0,3.0]),rcp3([1.0,2.0,3.0]))
}
fn clamp() -> bool {
    clamp_i32([0,100,-100],[5,40,-95],[7,45,5]) == [5,45,-95]
    && clamp_i32([0,100,-100],[-50;3],[50;3]) == [0,50,-50]
}
fn min_list() -> bool {
    let inf = f32::INFINITY;
    let Some(r) = min3(&[[f32::NAN,2.0,3.0],[0.0,f32::NAN,2.0],[2.0,4.0,f32::NAN]]) else { return false; };
    min3(&[[1.0,2.0,3.0]]) == Some([1.0,2.0,3.0])
    && min3(&[[1.0,2.0,3.0],[0.0,5.0,2.0]]) == Some([0.0,2.0,2.0])
    && min3(&[[1.0,2.0,3.0],[0.0,5.0,2.0],[2.0,4.0,1.5]]) == Some([0.0,2.0,1.5])
    && min3(&[[inf,2.0,3.0],[0.0,-inf,inf],[2.0,4.0,-inf]]) == Some([0.0,-inf,-inf])
    && r[0].is_nan() && r[1] == 2.0 && r[2] == 2.0
}
fn max_list() -> bool {
    let inf = f32::INFINITY;
    let Some(r) = max3(&[[f32::NAN,2.0,3.0],[0.0,f32::NAN,2.0],[2.0,4.0,f32::NAN]]) else { return false; };
    max3(&[[1.0,2.0,3.0]]) == Some([1.0,2.0,3.0])
    && max3(&[[1.0,2.0,3.0],[0.0,5.0,2.0]]) == Some([1.0,5.0,3.0])
    && max3(&[[1.0,2.0,3.0],[0.0,5.0,2.0],[2.0,4.0,1.5]]) == Some([2.0,5.0,3.0])
    && max3(&[[inf,2.0,3.0],[0.0,-inf,inf],[2.0,4.0,-inf]]) == Some([inf,4.0,inf])
    && r[0].is_nan() && r[1] == 4.0 && r[2] == 3.0
}
fn interpolate_int() -> bool { lerp_i32([0,-100,50],[0,100,100],0.75) == [0,50,87] }
fn interpolate_float() -> bool { eqf(lerp_f32([40.0,-100.0,50.0],[20.0,100.0,100.0],0.5), [30.0,0.0,75.0]) }
fn ceil_to_multiple() -> bool { ceil_multiple3([21,16,0],[8,16,15]) == Some([24,16,0]) }
fn divide_ceil() -> bool { divide_ceil3([21,16,0],[8,16,15]) == Some([3,1,0]) }
fn sign() -> bool { sign3([-21,16,0]) == [-1,1,0] }
fn sqrt() -> bool { near(sqrt3([1.0,4.0,9.0]), [1.0,2.0,3.0]) }
fn safe_sqrt() -> bool { near(safe_sqrt3([1.0,-4.0,9.0]), [1.0,0.0,3.0]) }
fn rcp() -> bool { near(rcp3([1.0,2.0,4.0]), [1.0,0.5,0.25]) }
fn safe_rcp() -> bool { near(safe_rcp3([1.0,0.0,4.0]), [1.0,0.0,0.25]) }
fn exp() -> bool { near(exp3([1.0,2.0,3.0]), [2.718281828459045_f32,7.38905609893065_f32,20.085536923187668_f32]) }
fn log() -> bool { near(log3([1.0,2.0,3.0]), [0.0,0.69314718056_f32,1.09861228867_f32]) }
fn square() -> bool { near(square3([1.0,2.0,3.0]), [1.0,4.0,9.0]) }
