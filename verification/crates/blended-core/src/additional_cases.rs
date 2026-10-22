// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Literal inputs, expected results and assertion types from five pinned Blender files.
// See compatibility/additional-ports.json. Not whole-application parity.
#![allow(non_snake_case, unused_mut, unused_parens, clippy::excessive_precision)]
use crate::scalar_math as m;
#[derive(Debug, Default)]
pub struct Report { pub assertions: u32, pub failures: Vec<String> }
impl Report {
    fn check(&mut self, ok: bool, expression: &str, line: u32) {
        self.assertions += 1;
        if !ok { self.failures.push(format!("line {line}: {expression}")); }
    }
    pub fn passed(&self) -> bool { self.assertions > 0 && self.failures.is_empty() }
}
fn equal<T: PartialEq>(a: T, b: T) -> bool { a == b }
fn float_equal(a: f32, b: f32) -> bool {
    if a.is_nan() || b.is_nan() { return false; }
    fn ordered(x: f32) -> u32 {
        let bits=x.to_bits();
        if bits & 0x80000000 != 0 { (!bits).wrapping_add(1) } else { bits | 0x80000000 }
    }
    ordered(a).abs_diff(ordered(b)) <= 4
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let a=$a;$r.check(equal(a,$b as _),stringify!($a == $b),line!());}};}
macro_rules! feq {($r:expr,$a:expr,$b:expr)=>{{$r.check(float_equal($a as f32,$b as f32),stringify!($a ~= $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{let (a,b,e)=($a as f64,$b as f64,$e as f64);$r.check((a-b).abs()<=e,stringify!($a ~= $b within $e),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}

// source/blender/blenlib/tests/BLI_math_base_test.cc:17
pub fn math_base__CompareFFRelativeValid() -> Report {
let mut r=Report::default();
yes!(r, core::mem::size_of::<f32>() == core::mem::size_of::<i32>());
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:22
pub fn math_base__CompareFFRelativeNormal() -> Report {
let mut r=Report::default();
let f1: f32 = 1.99999988_f32;
let f2: f32 = 2.00000000_f32;
let f3: f32 = 2.00000048_f32;
let f4: f32 = 2.10000000_f32;
let max_diff: f32 = f32::EPSILON * 0.1_f32;
yes!(r, m::compare_ff_relative((f1) as f32, (f2) as f32, (max_diff) as f32, 1));
yes!(r, m::compare_ff_relative((f2) as f32, (f1) as f32, (max_diff) as f32, 1));
yes!(r, m::compare_ff_relative((f3) as f32, (f2) as f32, (max_diff) as f32, 2));
yes!(r, m::compare_ff_relative((f2) as f32, (f3) as f32, (max_diff) as f32, 2));
no!(r, m::compare_ff_relative((f3) as f32, (f2) as f32, (max_diff) as f32, 1));
no!(r, m::compare_ff_relative((f2) as f32, (f3) as f32, (max_diff) as f32, 1));
no!(r, m::compare_ff_relative((f3) as f32, (f2) as f32, (-1.0_f32) as f32, 1));
no!(r, m::compare_ff_relative((f2) as f32, (f3) as f32, (-1.0_f32) as f32, 1));
yes!(r, m::compare_ff_relative((f3) as f32, (f2) as f32, (-1.0_f32) as f32, 2));
yes!(r, m::compare_ff_relative((f2) as f32, (f3) as f32, (-1.0_f32) as f32, 2));
no!(r, m::compare_ff_relative((f4) as f32, (f2) as f32, (max_diff) as f32, 64));
no!(r, m::compare_ff_relative((f2) as f32, (f4) as f32, (max_diff) as f32, 64));
yes!(r, m::compare_ff_relative((f1) as f32, (f3) as f32, (max_diff) as f32, 64));
yes!(r, m::compare_ff_relative((f3) as f32, (f1) as f32, (max_diff) as f32, 64));
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:53
pub fn math_base__CompareFFRelativeZero() -> Report {
let mut r=Report::default();
let f0: f32 = 0.0_f32;
let f1: f32 = 4.2038954e-045_f32;
let fn0: f32 = -0.0_f32;
let fn1: f32 = -2.8025969e-045_f32;
let max_diff: f32 = f32::EPSILON * 0.1_f32;
yes!(r, m::compare_ff_relative((f0) as f32, (f1) as f32, (-1.0_f32) as f32, 3));
yes!(r, m::compare_ff_relative((f1) as f32, (f0) as f32, (-1.0_f32) as f32, 3));
no!(r, m::compare_ff_relative((f0) as f32, (f1) as f32, (-1.0_f32) as f32, 2));
no!(r, m::compare_ff_relative((f1) as f32, (f0) as f32, (-1.0_f32) as f32, 2));
yes!(r, m::compare_ff_relative((f0) as f32, (f1) as f32, (max_diff) as f32, 2));
yes!(r, m::compare_ff_relative((f1) as f32, (f0) as f32, (max_diff) as f32, 2));
yes!(r, m::compare_ff_relative((fn0) as f32, (f1) as f32, (-1.0_f32) as f32, 3));
yes!(r, m::compare_ff_relative((f1) as f32, (fn0) as f32, (-1.0_f32) as f32, 3));
no!(r, m::compare_ff_relative((fn0) as f32, (f1) as f32, (-1.0_f32) as f32, 2));
no!(r, m::compare_ff_relative((f1) as f32, (fn0) as f32, (-1.0_f32) as f32, 2));
yes!(r, m::compare_ff_relative((fn0) as f32, (f1) as f32, (max_diff) as f32, 2));
yes!(r, m::compare_ff_relative((f1) as f32, (fn0) as f32, (max_diff) as f32, 2));
yes!(r, m::compare_ff_relative((fn0) as f32, (fn1) as f32, (-1.0_f32) as f32, 2));
yes!(r, m::compare_ff_relative((fn1) as f32, (fn0) as f32, (-1.0_f32) as f32, 2));
no!(r, m::compare_ff_relative((fn0) as f32, (fn1) as f32, (-1.0_f32) as f32, 1));
no!(r, m::compare_ff_relative((fn1) as f32, (fn0) as f32, (-1.0_f32) as f32, 1));
yes!(r, m::compare_ff_relative((fn0) as f32, (fn1) as f32, (max_diff) as f32, 1));
yes!(r, m::compare_ff_relative((fn1) as f32, (fn0) as f32, (max_diff) as f32, 1));
yes!(r, m::compare_ff_relative((f0) as f32, (fn1) as f32, (-1.0_f32) as f32, 2));
yes!(r, m::compare_ff_relative((fn1) as f32, (f0) as f32, (-1.0_f32) as f32, 2));
no!(r, m::compare_ff_relative((f0) as f32, (fn1) as f32, (-1.0_f32) as f32, 1));
no!(r, m::compare_ff_relative((fn1) as f32, (f0) as f32, (-1.0_f32) as f32, 1));
yes!(r, m::compare_ff_relative((f0) as f32, (fn1) as f32, (max_diff) as f32, 1));
yes!(r, m::compare_ff_relative((fn1) as f32, (f0) as f32, (max_diff) as f32, 1));
yes!(r, m::compare_ff_relative((fn0) as f32, (f0) as f32, (-1.0_f32) as f32, 0));
yes!(r, m::compare_ff_relative((f0) as f32, (fn0) as f32, (-1.0_f32) as f32, 0));
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:95
pub fn math_base__UlpDiffFF() -> Report {
let mut r=Report::default();
eq!(r, m::ulp_diff_ff((0.0) as f32, (0.0) as f32), 0);
eq!(r, m::ulp_diff_ff((0.0) as f32, (-0.0) as f32), 0);
eq!(r, m::ulp_diff_ff((-0.0) as f32, (-0.0) as f32), 0);
eq!(r, m::ulp_diff_ff((1.0) as f32, (1.0) as f32), 0);
eq!(r, m::ulp_diff_ff((1.0) as f32, (2.0) as f32), 1 << 23);
eq!(r, m::ulp_diff_ff((2.0) as f32, (4.0) as f32), 1 << 23);
eq!(r, m::ulp_diff_ff((-1.0) as f32, (-2.0) as f32), 1 << 23);
eq!(r, m::ulp_diff_ff((-2.0) as f32, (-4.0) as f32), 1 << 23);
eq!(r, m::ulp_diff_ff((-1.0) as f32, (1.0) as f32), 0x7f000000);
eq!(r, m::ulp_diff_ff((0.0) as f32, (1.0) as f32), 0x3f800000);
eq!(r, m::ulp_diff_ff((-0.0) as f32, (1.0) as f32), 0x3f800000);
eq!(r, m::ulp_diff_ff((0.0) as f32, (-1.0) as f32), 0x3f800000);
eq!(r, m::ulp_diff_ff((-0.0) as f32, (-1.0) as f32), 0x3f800000);
eq!(r, m::ulp_diff_ff((f32::INFINITY) as f32, (-f32::INFINITY) as f32), 0xff000000_u32);
eq!(r, m::ulp_diff_ff((f32::NAN) as f32, (f32::NAN) as f32), 0xffffffff_u32);
eq!(r, m::ulp_diff_ff((f32::NAN) as f32, (1.0) as f32), 0xffffffff_u32);
eq!(r, m::ulp_diff_ff((1.0) as f32, (f32::NAN) as f32), 0xffffffff_u32);
eq!(r, m::ulp_diff_ff((-f32::NAN) as f32, (1.0) as f32), 0xffffffff_u32);
eq!(r, m::ulp_diff_ff((1.0) as f32, (-f32::NAN) as f32), 0xffffffff_u32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:118
pub fn math_base__Log2FloorU() -> Report {
let mut r=Report::default();
eq!(r, m::log2_floor_u(0), 0);
eq!(r, m::log2_floor_u(1), 0);
eq!(r, m::log2_floor_u(2), 1);
eq!(r, m::log2_floor_u(3), 1);
eq!(r, m::log2_floor_u(4), 2);
eq!(r, m::log2_floor_u(5), 2);
eq!(r, m::log2_floor_u(6), 2);
eq!(r, m::log2_floor_u(7), 2);
eq!(r, m::log2_floor_u(8), 3);
eq!(r, m::log2_floor_u(9), 3);
eq!(r, m::log2_floor_u(123456), 16);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:133
pub fn math_base__Log2CeilU() -> Report {
let mut r=Report::default();
eq!(r, m::log2_ceil_u(0), 0);
eq!(r, m::log2_ceil_u(1), 0);
eq!(r, m::log2_ceil_u(2), 1);
eq!(r, m::log2_ceil_u(3), 2);
eq!(r, m::log2_ceil_u(4), 2);
eq!(r, m::log2_ceil_u(5), 3);
eq!(r, m::log2_ceil_u(6), 3);
eq!(r, m::log2_ceil_u(7), 3);
eq!(r, m::log2_ceil_u(8), 3);
eq!(r, m::log2_ceil_u(9), 4);
eq!(r, m::log2_ceil_u(123456), 17);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:148
pub fn math_base__CeilPowerOf10() -> Report {
let mut r=Report::default();
eq!(r, m::ceil_power_of_10((0) as f32), 0);
eq!(r, m::ceil_power_of_10((1) as f32), 1);
eq!(r, m::ceil_power_of_10((1e-6_f32) as f32), 1e-6_f32);
near!(r, m::ceil_power_of_10((100.1_f32) as f32), 1000.0_f32, 1e-4_f32);
near!(r, m::ceil_power_of_10((99.9_f32) as f32), 100.0_f32, 1e-4_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:157
pub fn math_base__FloorPowerOf10() -> Report {
let mut r=Report::default();
eq!(r, m::floor_power_of_10((0) as f32), 0);
eq!(r, m::floor_power_of_10((1) as f32), 1);
eq!(r, m::floor_power_of_10((1e-6_f32) as f32), 1e-6_f32);
near!(r, m::floor_power_of_10((100.1_f32) as f32), 100.0_f32, 1e-4_f32);
near!(r, m::floor_power_of_10((99.9_f32) as f32), 10.0_f32, 1e-4_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:166
pub fn math_base__MinVectorAndFloat() -> Report {
let mut r=Report::default();
eq!(r, m::min_f32((1.0_f32) as f32, (2.0_f32) as f32), 1.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:171
pub fn math_base__ClampInt() -> Report {
let mut r=Report::default();
eq!(r, m::clamp_i32(111, -50, 101), 101);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:176
pub fn math_base__StepLessThan() -> Report {
let mut r=Report::default();
eq!(r, m::step((0.5_f32) as f32, (0.3_f32) as f32), 0.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:181
pub fn math_base__StepGreaterThan() -> Report {
let mut r=Report::default();
eq!(r, m::step((0.5_f32) as f32, (0.6_f32) as f32), 1.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:186
pub fn math_base__StepExact() -> Report {
let mut r=Report::default();
eq!(r, m::step((0.5_f32) as f32, (0.5_f32) as f32), 1.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:191
pub fn math_base__Midpoint() -> Report {
let mut r=Report::default();
near!(r, m::midpoint((100.0_f32) as f32, (200.0_f32) as f32), 150.0_f32, 1e-4_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:196
pub fn math_base__InterpolateInt() -> Report {
let mut r=Report::default();
eq!(r, m::interpolate_i32(100, 200, (0.4_f32) as f32), 140);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:201
pub fn math_base__FlooredFMod() -> Report {
let mut r=Report::default();
feq!(r, m::floored_fmod((3.27_f32) as f32, (1.57_f32) as f32), 0.12999988_f32);
feq!(r, m::floored_fmod((327.0_f32) as f32, (47.0_f32) as f32), 45.0_f32);
feq!(r, m::floored_fmod((-0.1_f32) as f32, (1.0_f32) as f32), 0.9_f32);
feq!(r, m::floored_fmod((-0.9_f32) as f32, (1.0_f32) as f32), 0.1_f32);
feq!(r, m::floored_fmod((-100.1_f32) as f32, (1.0_f32) as f32), 0.90000153_f32);
feq!(r, m::floored_fmod((-0.1_f32) as f32, (12345.0_f32) as f32), 12344.9_f32);
feq!(r, m::floored_fmod((12345.1_f32) as f32, (12345.0_f32) as f32), 0.099609375_f32);
feq!(r, m::floored_fmod((12344.999_f32) as f32, (12345.0_f32) as f32), 12344.999_f32);
feq!(r, m::floored_fmod((12345.0_f32) as f32, (12345.0_f32) as f32), 0.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_test.cc:214
pub fn math_base__ModPeriodic() -> Report {
let mut r=Report::default();
feq!(r, m::mod_periodic_f32((3.27_f32) as f32, (1.57_f32) as f32), 0.12999988_f32);
feq!(r, m::mod_periodic_f32((327.0_f32) as f32, (47.0_f32) as f32), 45.0_f32);
feq!(r, m::mod_periodic_f32((-0.1_f32) as f32, (1.0_f32) as f32), 0.9_f32);
feq!(r, m::mod_periodic_f32((-0.9_f32) as f32, (1.0_f32) as f32), 0.1_f32);
feq!(r, m::mod_periodic_f32((-100.1_f32) as f32, (1.0_f32) as f32), 0.90000153_f32);
feq!(r, m::mod_periodic_f32((-0.1_f32) as f32, (12345.0_f32) as f32), 12344.9_f32);
feq!(r, m::mod_periodic_f32((12345.1_f32) as f32, (12345.0_f32) as f32), 0.099609375_f32);
feq!(r, m::mod_periodic_f32((12344.999_f32) as f32, (12345.0_f32) as f32), 12344.999_f32);
feq!(r, m::mod_periodic_f32((12345.0_f32) as f32, (12345.0_f32) as f32), 0.0_f32);
eq!(r, m::mod_periodic_i32(1, 10), 1);
eq!(r, m::mod_periodic_i32(11, 10), 1);
eq!(r, m::mod_periodic_i32(-1, 10), 9);
eq!(r, m::mod_periodic_i32(-11, 10), 9);
eq!(r, m::mod_periodic_i32(1, 1), 0);
eq!(r, m::mod_periodic_i32(0, 99999), 0);
eq!(r, m::mod_periodic_i32(99999, 99999), 0);
eq!(r, m::mod_periodic_i32(i32::MAX / 2, i32::MAX / 2), 0);
eq!(r, m::mod_periodic_i32(i32::MIN / 2, i32::MAX / 2), i32::MAX / 2 - 1);
eq!(r, m::mod_periodic_i64(1, 10), 1);
eq!(r, m::mod_periodic_i64(11, 10), 1);
eq!(r, m::mod_periodic_i64(-1, 10), 9);
eq!(r, m::mod_periodic_i64(-11, 10), 9);
eq!(r, m::mod_periodic_i64(1, 1), 0);
eq!(r, m::mod_periodic_i64(0, 99999), 0);
eq!(r, m::mod_periodic_i64(99999, 99999), 0);
r
}

// source/blender/blenlib/tests/BLI_math_base_safe_test.cc:11
pub fn math_base__SafePowf() -> Report {
let mut r=Report::default();
feq!(r, m::safe_powf((4.0_f32) as f32, (3.0_f32) as f32), 64.0_f32);
feq!(r, m::safe_powf((3.2_f32) as f32, (5.6_f32) as f32), 674.2793796_f32);
feq!(r, m::safe_powf((4.0_f32) as f32, (-2.0_f32) as f32), 0.0625_f32);
feq!(r, m::safe_powf((6.0_f32) as f32, (-3.2_f32) as f32), 0.003235311_f32);
feq!(r, m::safe_powf((-4.0_f32) as f32, (6) as f32), 4096.0_f32);
feq!(r, m::safe_powf((-3.0_f32) as f32, (5.5) as f32), 0.0_f32);
feq!(r, m::safe_powf((-2.5_f32) as f32, (-4.0_f32) as f32), 0.0256_f32);
feq!(r, m::safe_powf((-3.7_f32) as f32, (-4.5_f32) as f32), 0.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_safe_test.cc:23
pub fn math_base__SafeModf() -> Report {
let mut r=Report::default();
feq!(r, m::safe_modf((3.4) as f32, (2.2_f32) as f32), 1.2_f32);
feq!(r, m::safe_modf((3.4) as f32, (-2.2_f32) as f32), 1.2_f32);
feq!(r, m::safe_modf((-3.4) as f32, (-2.2_f32) as f32), -1.2_f32);
feq!(r, m::safe_modf((-3.4) as f32, (0.0_f32) as f32), 0.0_f32);
feq!(r, m::safe_modf((0.0_f32) as f32, (3.0_f32) as f32), 0.0_f32);
feq!(r, m::safe_modf((55.0_f32) as f32, (10.0_f32) as f32), 5.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_base_safe_test.cc:33
pub fn math_base__SafeLogf() -> Report {
let mut r=Report::default();
feq!(r, m::safe_logf((3.3_f32) as f32, (2.5_f32) as f32), 1.302995247_f32);
feq!(r, m::safe_logf((0.0_f32) as f32, (3.0_f32) as f32), 0.0_f32);
feq!(r, m::safe_logf((3.0_f32) as f32, (0.0_f32) as f32), 0.0_f32);
feq!(r, m::safe_logf((-2.0_f32) as f32, (4.3_f32) as f32), 0.0_f32);
feq!(r, m::safe_logf((2.0_f32) as f32, (-4.3_f32) as f32), 0.0_f32);
feq!(r, m::safe_logf((-2.0_f32) as f32, (-4.3_f32) as f32), 0.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_bits_test.cc:11
pub fn math_bits__BitscanReverseClearUint() -> Report {
let mut r=Report::default();

  let mut a: u32 = 1234;
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 21);
  eq!(r, a, 210);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 24);
  eq!(r, a, 82);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 25);
  eq!(r, a, 18);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 27);
  eq!(r, a, 2);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 30);
  eq!(r, a, 0);

  a = 3563987529;
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 0);
  eq!(r, a, 1416503881);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 1);
  eq!(r, a, 342762057);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 3);
  eq!(r, a, 74326601);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 5);
  eq!(r, a, 7217737);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 9);
  eq!(r, a, 3023433);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 10);
  eq!(r, a, 926281);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 12);
  eq!(r, a, 401993);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 13);
  eq!(r, a, 139849);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 14);
  eq!(r, a, 8777);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 18);
  eq!(r, a, 585);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 22);
  eq!(r, a, 73);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 25);
  eq!(r, a, 9);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 28);
  eq!(r, a, 1);
  eq!(r, m::bitscan_reverse_clear_uint(&mut a), 31);
  eq!(r, a, 0);

r
}

// source/blender/blenlib/tests/BLI_math_bits_test.cc:56
pub fn math_bits__PopCount() -> Report {
let mut r=Report::default();
{
 eq!(r,m::count_bits_i(0),0); eq!(r,m::count_bits_uint64(0),0);
}
{
 let value:i32=(1<<0)|(1<<5)|(1<<7);
 let count_32=m::count_bits_i(value); let count_64=m::count_bits_uint64(value as u64);
 eq!(r,count_32,3);eq!(r,count_64,3);
}
{
 let value:u64=(1u64<<0)|(1u64<<50);let count=m::count_bits_uint64(value);eq!(r,count,2);
}
{let value:i32=-1;let count=m::count_bits_i(value);eq!(r,count,32);}
{let value:u64=u64::MAX;let count=m::count_bits_uint64(value);eq!(r,count,64);}
r
}

// source/blender/blenlib/tests/BLI_math_solvers_test.cc:11
pub fn math_solvers__Tridiagonal1() -> Report {
let mut r=Report::default();

  let a: [f32; 1] = [1.0];  
  let b: [f32; 1] = [2.0];
  let c: [f32; 1] = [1.0];  
  let d: [f32; 1] = [4.0];
  let mut x = [0.0_f32; 1];

  yes!(r, m::tridiagonal_solve(&a, &b, &c, &d, &mut x, 1));
  feq!(r, x[0], 2);

r
}

// source/blender/blenlib/tests/BLI_math_solvers_test.cc:23
pub fn math_solvers__Tridiagonal3() -> Report {
let mut r=Report::default();

  let a: [f32; 3] = [1.0, 2.0, 3.0];  
  let b: [f32; 3] = [4.0, 5.0, 6.0];
  let c: [f32; 3] = [7.0, 8.0, 9.0];  
  let d: [f32; 3] = [18.0, 36.0, 24.0];
  let mut x = [0.0_f32; 3];

  yes!(r, m::tridiagonal_solve(&a, &b, &c, &d, &mut x, 3));
  feq!(r, x[0], 1);
  feq!(r, x[1], 2);
  feq!(r, x[2], 3);

r
}

// source/blender/blenlib/tests/BLI_math_solvers_test.cc:37
pub fn math_solvers__CyclicTridiagonal1() -> Report {
let mut r=Report::default();

  let a: [f32; 1] = [1.0];
  let b: [f32; 1] = [2.0];
  let c: [f32; 1] = [1.0];
  let d: [f32; 1] = [4.0];
  let mut x = [0.0_f32; 1];

  yes!(r, m::tridiagonal_solve_cyclic(&a, &b, &c, &d, &mut x, 1));
  feq!(r, x[0], 1);

r
}

// source/blender/blenlib/tests/BLI_math_solvers_test.cc:49
pub fn math_solvers__CyclicTridiagonal2() -> Report {
let mut r=Report::default();

  let a: [f32; 2] = [1.0, 2.0];
  let b: [f32; 2] = [3.0, 4.0];
  let c: [f32; 2] = [5.0, 6.0];
  let d: [f32; 2] = [15.0, 16.0];
  let mut x = [0.0_f32; 2];

  yes!(r, m::tridiagonal_solve_cyclic(&a, &b, &c, &d, &mut x, 2));
  feq!(r, x[0], 1);
  feq!(r, x[1], 2);

r
}

// source/blender/blenlib/tests/BLI_math_solvers_test.cc:62
pub fn math_solvers__CyclicTridiagonal3() -> Report {
let mut r=Report::default();

  let a: [f32; 3] = [1.0, 2.0, 3.0];
  let b: [f32; 3] = [4.0, 5.0, 6.0];
  let c: [f32; 3] = [7.0, 8.0, 9.0];
  let d: [f32; 3] = [21.0, 36.0, 33.0];
  let mut x = [0.0_f32; 3];

  yes!(r, m::tridiagonal_solve_cyclic(&a, &b, &c, &d, &mut x, 3));
  feq!(r, x[0], 1);
  feq!(r, x[1], 2);
  feq!(r, x[2], 3);

r
}

// source/blender/blenlib/tests/BLI_math_time_test.cc:11
pub fn math_time__SecondsExplode() -> Report {
let mut r=Report::default();
let seconds:f64=2.0*86400.0+13.0*3600.0+33.0*60.0+9.0+369.0*0.001;
let epsilon=1e-8_f64;
let t=m::seconds_decompose(seconds,[true,true,true,true,true]);
near!(r,2.0,t[0],epsilon); near!(r,13.0,t[1],epsilon); near!(r,33.0,t[2],epsilon); near!(r,9.0,t[3],epsilon); near!(r,369.0,t[4],epsilon);
let t=m::seconds_decompose(seconds,[false,true,true,true,false]);
near!(r,61.0,t[1],epsilon); near!(r,33.0,t[2],epsilon); near!(r,9.369,t[3],epsilon);
let t=m::seconds_decompose(seconds,[false,false,false,true,false]);
near!(r,seconds,t[3],epsilon);
let t=m::seconds_decompose(seconds,[true,false,true,false,true]);
near!(r,2.0,t[0],epsilon); near!(r,813.0,t[2],epsilon); near!(r,9369.0,t[4],epsilon);
r
}

pub const CASES: &[(&str,fn()->Report)] = &[
("math_base.CompareFFRelativeValid",math_base__CompareFFRelativeValid),
("math_base.CompareFFRelativeNormal",math_base__CompareFFRelativeNormal),
("math_base.CompareFFRelativeZero",math_base__CompareFFRelativeZero),
("math_base.UlpDiffFF",math_base__UlpDiffFF),
("math_base.Log2FloorU",math_base__Log2FloorU),
("math_base.Log2CeilU",math_base__Log2CeilU),
("math_base.CeilPowerOf10",math_base__CeilPowerOf10),
("math_base.FloorPowerOf10",math_base__FloorPowerOf10),
("math_base.MinVectorAndFloat",math_base__MinVectorAndFloat),
("math_base.ClampInt",math_base__ClampInt),
("math_base.StepLessThan",math_base__StepLessThan),
("math_base.StepGreaterThan",math_base__StepGreaterThan),
("math_base.StepExact",math_base__StepExact),
("math_base.Midpoint",math_base__Midpoint),
("math_base.InterpolateInt",math_base__InterpolateInt),
("math_base.FlooredFMod",math_base__FlooredFMod),
("math_base.ModPeriodic",math_base__ModPeriodic),
("math_base.SafePowf",math_base__SafePowf),
("math_base.SafeModf",math_base__SafeModf),
("math_base.SafeLogf",math_base__SafeLogf),
("math_bits.BitscanReverseClearUint",math_bits__BitscanReverseClearUint),
("math_bits.PopCount",math_bits__PopCount),
("math_solvers.Tridiagonal1",math_solvers__Tridiagonal1),
("math_solvers.Tridiagonal3",math_solvers__Tridiagonal3),
("math_solvers.CyclicTridiagonal1",math_solvers__CyclicTridiagonal1),
("math_solvers.CyclicTridiagonal2",math_solvers__CyclicTridiagonal2),
("math_solvers.CyclicTridiagonal3",math_solvers__CyclicTridiagonal3),
("math_time.SecondsExplode",math_time__SecondsExplode),
];
