// SPDX-License-Identifier: GPL-3.0-or-later
//! Initial vector operations. Passing a subset of tests is not full parity.
pub fn clamp_f32<const N: usize>(v: &mut [f32; N], min: f32, max: f32) {
    assert!(min <= max, "invalid clamp bounds");
    for x in v { if *x < min { *x = min; } if *x > max { *x = max; } }
}
pub fn clamp_i32(v: [i32; 3], lo: [i32; 3], hi: [i32; 3]) -> [i32; 3] {
    std::array::from_fn(|i| v[i].clamp(lo[i], hi[i]))
}
// Ordered comparisons preserve an initial NaN. f32::min/max would not.
pub fn min3(values: &[[f32;3]]) -> Option<[f32;3]> {
    let mut result = *values.first()?;
    for v in &values[1..] { for i in 0..3 { if v[i] < result[i] { result[i] = v[i]; } } }
    Some(result)
}
pub fn max3(values: &[[f32;3]]) -> Option<[f32;3]> {
    let mut result = *values.first()?;
    for v in &values[1..] { for i in 0..3 { if v[i] > result[i] { result[i] = v[i]; } } }
    Some(result)
}
pub fn lerp_f32(a: [f32;3], b: [f32;3], t: f32) -> [f32;3] {
    std::array::from_fn(|i| a[i] * (1.0-t) + b[i] * t)
}
pub fn lerp_i32(a: [i32;3], b: [i32;3], t: f32) -> [i32;3] {
    lerp_f32(a.map(|x| x as f32), b.map(|x| x as f32), t).map(|x| x as i32)
}
/// Nonnegative dividends and positive divisors only; other domains rejected.
pub fn divide_ceil3(a: [i32;3], b: [i32;3]) -> Option<[i32;3]> {
    let mut out = [0;3];
    for i in 0..3 {
        if a[i] < 0 || b[i] <= 0 { return None; }
        out[i] = i32::try_from((i64::from(a[i]) + i64::from(b[i]) - 1) / i64::from(b[i])).ok()?;
    }
    Some(out)
}
pub fn ceil_multiple3(a: [i32;3], b: [i32;3]) -> Option<[i32;3]> {
    let q = divide_ceil3(a,b)?;
    Some([q[0].checked_mul(b[0])?,q[1].checked_mul(b[1])?,q[2].checked_mul(b[2])?])
}
pub fn sign3(v: [i32;3]) -> [i32;3] { v.map(i32::signum) }
pub fn sqrt3(v: [f32;3]) -> [f32;3] { v.map(f32::sqrt) }
pub fn safe_sqrt3(v: [f32;3]) -> [f32;3] { v.map(|x| if x < 0.0 {0.0} else {x.sqrt()}) }
pub fn rcp3(v: [f32;3]) -> [f32;3] { v.map(|x| 1.0/x) }
pub fn safe_rcp3(v: [f32;3]) -> [f32;3] { v.map(|x| if x == 0.0 {0.0} else {1.0/x}) }
pub fn exp3(v: [f32;3]) -> [f32;3] { v.map(f32::exp) }
pub fn log3(v: [f32;3]) -> [f32;3] { v.map(f32::ln) }
pub fn square3(v: [f32;3]) -> [f32;3] { v.map(|x| x*x) }
