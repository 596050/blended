// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from hash-locked Blender test sources; do not edit expected values.
#![allow(non_snake_case,non_upper_case_globals,unused_mut,unused_assignments,unused_parens,unused_macros)]
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b within $e),line!());}};}
macro_rules! near4 {($r:expr,$a:expr,$b:expr,$e:expr)=>{{let a=$a;let b=$b;for i in 0..4 {near!($r,a[i],b[i],$e);}}};}
use crate::image_sampling::*;
const float_tolerance:f32=(0.00005_f32) as f32;
const image_width:usize=(3) as usize;
const image_height:usize=(3) as usize;
const image_char:[u8;36]=[(255) as u8, (254) as u8, (217) as u8, (216) as u8, (230) as u8, (230) as u8, (230) as u8, (230) as u8, (240) as u8, (160) as u8, (90) as u8, (20) as u8, (0) as u8, (1) as u8, (2) as u8, (3) as u8, (62) as u8, (72) as u8, (82) as u8, (92) as u8, (126) as u8, (127) as u8, (128) as u8, (129) as u8, (1) as u8, (2) as u8, (3) as u8, (4) as u8, (73) as u8, (108) as u8, (153) as u8, (251) as u8, (128) as u8, (129) as u8, (130) as u8, (131) as u8];
const image_fl:[f32;36]=[(255) as f32, (254) as f32, (217) as f32, (216) as f32, (230) as f32, (230) as f32, (230) as f32, (230) as f32, (240) as f32, (160) as f32, (90) as f32, (20) as f32, (0) as f32, (1) as f32, (2) as f32, (3) as f32, (62) as f32, (72) as f32, (82) as f32, (92) as f32, (126) as f32, (127) as f32, (128) as f32, (129) as f32, (1) as f32, (2) as f32, (3) as f32, (4) as f32, (73) as f32, (108) as f32, (153) as f32, (251) as f32, (128) as f32, (129) as f32, (130) as f32, (131) as f32];

// source/blender/blenlib/tests/BLI_math_interp_test.cc:27
pub fn math_interp__NearestCharExactSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(73) as u8, (108) as u8, (153) as u8, (251) as u8];
  res = interpolate_nearest_border_byte(&image_char, image_width, image_height, (1.0_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(240) as u8, (160) as u8, (90) as u8, (20) as u8];
  res = interpolate_nearest_border_byte(&image_char, image_width, image_height, (2.0_f32) as f32, (0.0_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:38
pub fn math_interp__NearestCharHalfwaySamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(0) as u8, (1) as u8, (2) as u8, (3) as u8];
  res = interpolate_nearest_border_byte(&image_char, image_width, image_height, (0.5_f32) as f32, (1.5_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(255) as u8, (254) as u8, (217) as u8, (216) as u8];
  res = interpolate_nearest_border_byte(&image_char, image_width, image_height, (0.5_f32) as f32, (0.5_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:49
pub fn math_interp__NearestFloatExactSamples()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(73.0_f32) as f32, (108.0_f32) as f32, (153.0_f32) as f32, (251.0_f32) as f32];
  res = interpolate_nearest_border_fl(&image_fl, image_width, image_height, (1.0_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[f32;4] = [(240.0_f32) as f32, (160.0_f32) as f32, (90.0_f32) as f32, (20.0_f32) as f32];
  res = interpolate_nearest_border_fl(&image_fl, image_width, image_height, (2.0_f32) as f32, (0.0_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:60
pub fn math_interp__NearestFloatHalfwaySamples()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(0.0_f32) as f32, (1.0_f32) as f32, (2.0_f32) as f32, (3.0_f32) as f32];
  res = interpolate_nearest_border_fl(&image_fl, image_width, image_height, (0.5_f32) as f32, (1.5_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[f32;4] = [(255.0_f32) as f32, (254.0_f32) as f32, (217.0_f32) as f32, (216.0_f32) as f32];
  res = interpolate_nearest_border_fl(&image_fl, image_width, image_height, (0.5_f32) as f32, (0.5_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:71
pub fn math_interp__BilinearCharExactSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(73) as u8, (108) as u8, (153) as u8, (251) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (1.0_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(240) as u8, (160) as u8, (90) as u8, (20) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (2.0_f32) as f32, (0.0_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:82
pub fn math_interp__BilinearCharHalfwayUSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(31) as u8, (37) as u8, (42) as u8, (48) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0.5_f32) as f32, (1.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(243) as u8, (242) as u8, (224) as u8, (223) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0.5_f32) as f32, (0.0_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:93
pub fn math_interp__BilinearCharHalfwayVSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(1) as u8, (2) as u8, (3) as u8, (4) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0.0_f32) as f32, (1.5_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(127) as u8, (128) as u8, (129) as u8, (130) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (2.0_f32) as f32, (1.5_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:104
pub fn math_interp__BilinearCharSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(136) as u8, (133) as u8, (132) as u8, (130) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (0.625_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(219) as u8, (191) as u8, (167) as u8, (142) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (1.4_f32) as f32, (0.1_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:116
pub fn math_interp__BilinearFloatSamples()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(135.9375_f32) as f32, (133.28125_f32) as f32, (131.5625_f32) as f32, (129.84375_f32) as f32];
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (0.625_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  let mut exp2:[f32;4] = [(219.36_f32) as f32, (191.2_f32) as f32, (166.64_f32) as f32, (142.08_f32) as f32];
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (1.4_f32) as f32, (0.1_f32) as f32);
  near4!(report, exp2, res, float_tolerance);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:127
pub fn math_interp__BilinearCharPartiallyOutsideImageBorder()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(1) as u8, (1) as u8, (2) as u8, (2) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(9) as u8, (11) as u8, (15) as u8, (22) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  eq!(report, exp2, res);
  let mut exp3:[u8;4] = [(173) as u8, (115) as u8, (65) as u8, (14) as u8];
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  eq!(report, exp3, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:141
pub fn math_interp__BilinearCharPartiallyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u32;4] = [(1) as u32, (2) as u32, (3) as u32, (4) as u32];
  res = interpolate_bilinear_byte(&image_char, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, (res).map(|v|v as u32));
  let mut exp2:[u32;4] = [(87) as u32, (113) as u32, (147) as u32, (221) as u32];
  res = interpolate_bilinear_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  eq!(report, exp2, (res).map(|v|v as u32));
  let mut exp3:[u32;4] = [(240) as u32, (160) as u32, (90) as u32, (20) as u32];
  res = interpolate_bilinear_byte(&image_char, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  eq!(report, exp3, (res).map(|v|v as u32));

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:155
pub fn math_interp__BilinearCharPartiallyOutsideImageWrap()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(65) as u8, (66) as u8, (67) as u8, (68) as u8];
  res = interpolate_bilinear_wrap_byte(&image_char, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(218) as u8, (203) as u8, (190) as u8, (182) as u8];
  res = interpolate_bilinear_wrap_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  eq!(report, exp2, res);
  let mut exp3:[u8;4] = [(229) as u8, (171) as u8, (114) as u8, (64) as u8];
  res = interpolate_bilinear_wrap_byte(&image_char, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  eq!(report, exp3, res);
                                                                                                   
                         
  res = interpolate_bilinear_wrap_byte(&image_char, image_width, image_height, (f32::INFINITY) as f32, (-f32::INFINITY) as f32);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:173
pub fn math_interp__BilinearFloatPartiallyOutsideImageBorder()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(0.5_f32) as f32, (1) as f32, (1.5_f32) as f32, (2) as f32];
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  let mut exp2:[f32;4] = [(8.675_f32) as f32, (11.325_f32) as f32, (14.725_f32) as f32, (22.1_f32) as f32];
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  near4!(report, exp2, res, float_tolerance);
  let mut exp3:[f32;4] = [(172.8_f32) as f32, (115.2_f32) as f32, (64.8_f32) as f32, (14.4_f32) as f32];
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  near4!(report, exp3, res, float_tolerance);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:187
pub fn math_interp__BilinearFloatPartiallyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(1.0_f32) as f32, (2.0_f32) as f32, (3.0_f32) as f32, (4.0_f32) as f32];
  res = interpolate_bilinear_fl(&image_fl, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  let mut exp2:[f32;4] = [(86.75_f32) as f32, (113.25_f32) as f32, (147.25_f32) as f32, (221.0_f32) as f32];
  res = interpolate_bilinear_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  near4!(report, exp2, res, float_tolerance);
  let mut exp3:[f32;4] = [(240.0_f32) as f32, (160.0_f32) as f32, (90.0_f32) as f32, (20.0_f32) as f32];
  res = interpolate_bilinear_fl(&image_fl, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  near4!(report, exp3, res, float_tolerance);
                                                                                             
                   
  let mut exp4:[f32;4] = [(240) as f32, (160) as f32, (90) as f32, (20) as f32];
  res = interpolate_bilinear_fl(&image_fl, image_width, image_height, (1e10_f32) as f32, (-1e10_f32) as f32);
  eq!(report, exp4, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:206
pub fn math_interp__BilinearFloatPartiallyOutsideImageWrap()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(64.5_f32) as f32, (65.5_f32) as f32, (66.5_f32) as f32, (67.5_f32) as f32];
  interpolate_bilinear_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (-0.5_f32) as f32, (2.0_f32) as f32, InterpWrapMode::Repeat, InterpWrapMode::Repeat);
  near4!(report, exp1, res, float_tolerance);
  res = interpolate_bilinear_wrap_fl(&image_fl, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  near4!(report, exp1, res, float_tolerance);

  let mut exp2:[f32;4] = [(217.92502_f32) as f32, (202.57501_f32) as f32, (190.22501_f32) as f32, (181.85_f32) as f32];
  interpolate_bilinear_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (1.25_f32) as f32, (2.9_f32) as f32, InterpWrapMode::Repeat, InterpWrapMode::Repeat);
  near4!(report, exp2, res, float_tolerance);
  res = interpolate_bilinear_wrap_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  near4!(report, exp2, res, float_tolerance);

  let mut exp3:[f32;4] = [(228.96_f32) as f32, (171.27998_f32) as f32, (114.32_f32) as f32, (63.84_f32) as f32];
  interpolate_bilinear_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (2.2_f32) as f32, (-0.1_f32) as f32, InterpWrapMode::Repeat, InterpWrapMode::Repeat);
  near4!(report, exp3, res, float_tolerance);
  res = interpolate_bilinear_wrap_fl(&image_fl, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  near4!(report, exp3, res, float_tolerance);

                         
  let mut exp4:[f32;4] = [(191.5_f32) as f32, (191.0_f32) as f32, (163.5_f32) as f32, (163.0_f32) as f32];
  interpolate_bilinear_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (-0.5_f32) as f32, (2.75_f32) as f32, InterpWrapMode::Extend, InterpWrapMode::Repeat);
  near4!(report, exp4, res, float_tolerance);
  interpolate_bilinear_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (-0.5_f32) as f32, (5.75_f32) as f32, InterpWrapMode::Extend, InterpWrapMode::Repeat);
  near4!(report, exp4, res, float_tolerance);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:275
pub fn math_interp__BilinearCharFullyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp:[u8;4] = [(0) as u8, (0) as u8, (0) as u8, (0) as u8];
                         
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (-1.5_f32) as f32, (0) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (-1.1_f32) as f32, (0) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (3) as f32, (0) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (5) as f32, (0) as f32);
  eq!(report, exp, res);

                         
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0) as f32, (-3.2_f32) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0) as f32, (-1.5_f32) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0) as f32, (3.1_f32) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_byte(&image_char, image_width, image_height, (0) as f32, (500.0_f32) as f32);
  eq!(report, exp, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:300
pub fn math_interp__BilinearFloatFullyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp:[f32;4] = [(0) as f32, (0) as f32, (0) as f32, (0) as f32];
                         
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (-1.5_f32) as f32, (0) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (-1.1_f32) as f32, (0) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (3) as f32, (0) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (5) as f32, (0) as f32);
  eq!(report, exp, res);

                         
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (0) as f32, (-3.2_f32) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (0) as f32, (-1.5_f32) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (0) as f32, (3.1_f32) as f32);
  eq!(report, exp, res);
  res = interpolate_bilinear_border_fl(&image_fl, image_width, image_height, (0) as f32, (500.0_f32) as f32);
  eq!(report, exp, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:325
pub fn math_interp__CubicBSplineCharExactSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(69) as u8, (90) as u8, (116) as u8, (172) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (1.0_f32) as f32, (2.0_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(218) as u8, (163) as u8, (115) as u8, (66) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (2.0_f32) as f32, (0.0_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:336
pub fn math_interp__CubicBSplineCharSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(142) as u8, (136) as u8, (131) as u8, (128) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (0.625_f32) as f32);
  eq!(report, exp1, res);
  let mut exp2:[u8;4] = [(202) as u8, (177) as u8, (154) as u8, (132) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (1.4_f32) as f32, (0.1_f32) as f32);
  eq!(report, exp2, res);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:347
pub fn math_interp__CubicBSplineFloatSamples()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(142.14418_f32) as f32, (136.255798_f32) as f32, (130.87924_f32) as f32, (127.85243_f32) as f32];
  res = interpolate_cubic_bspline_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (0.625_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  let mut exp2:[f32;4] = [(202.36082_f32) as f32, (177.13397_f32) as f32, (154.21078_f32) as f32, (132.30153_f32) as f32];
  res = interpolate_cubic_bspline_fl(&image_fl, image_width, image_height, (1.4_f32) as f32, (0.1_f32) as f32);
  near4!(report, exp2, res, float_tolerance);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:358
pub fn math_interp__CubicBSplineCharPartiallyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(2) as u8, (4) as u8, (6) as u8, (8) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  eq!(report, (exp1).map(|v|v as i32), (res).map(|v|v as i32));
  let mut exp2:[u8;4] = [(85) as u8, (107) as u8, (135) as u8, (195) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  eq!(report, (exp2).map(|v|v as i32), (res).map(|v|v as i32));
  let mut exp3:[u8;4] = [(225) as u8, (161) as u8, (105) as u8, (49) as u8];
  res = interpolate_cubic_bspline_byte(&image_char, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  eq!(report, (exp3).map(|v|v as i32), (res).map(|v|v as i32));

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:372
pub fn math_interp__CubicBSplineFloatPartiallyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(2.29861_f32) as f32, (3.92014_f32) as f32, (5.71528_f32) as f32, (8.430554_f32) as f32];
  res = interpolate_cubic_bspline_fl(&image_fl, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  interpolate_cubic_bspline_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (-0.5_f32) as f32, (2.0_f32) as f32, InterpWrapMode::Extend, InterpWrapMode::Extend);
  near4!(report, exp1, res, float_tolerance);

  let mut exp2:[f32;4] = [(85.41022_f32) as f32, (107.21497_f32) as f32, (135.13849_f32) as f32, (195.49146_f32) as f32];
  res = interpolate_cubic_bspline_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  near4!(report, exp2, res, float_tolerance);
  interpolate_cubic_bspline_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (1.25_f32) as f32, (2.9_f32) as f32, InterpWrapMode::Extend, InterpWrapMode::Extend);
  near4!(report, exp2, res, float_tolerance);

  let mut exp3:[f32;4] = [(224.73579_f32) as f32, (160.66783_f32) as f32, (104.63521_f32) as f32, (48.60260_f32) as f32];
  res = interpolate_cubic_bspline_fl(&image_fl, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  near4!(report, exp3, res, float_tolerance);
  interpolate_cubic_bspline_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (2.2_f32) as f32, (-0.1_f32) as f32, InterpWrapMode::Extend, InterpWrapMode::Extend);
  near4!(report, exp3, res, float_tolerance);

                             
  let mut exp4:[f32;4] = [(122.66441_f32) as f32, (89.68848_f32) as f32, (60.85706_f32) as f32, (32.02566_f32) as f32];
  interpolate_cubic_bspline_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (2.2_f32) as f32, (-0.1_f32) as f32, InterpWrapMode::Border, InterpWrapMode::Border);
  near4!(report, exp4, res, float_tolerance);

  let mut exp5:[f32;4] = [(189.57422_f32) as f32, (157.32167_f32) as f32, (122.71796_f32) as f32, (95.81750_f32) as f32];
  interpolate_cubic_bspline_wrapmode_fl(&image_fl, &mut res, image_width, image_height, 4, (2.2_f32) as f32, (-0.1_f32) as f32, InterpWrapMode::Repeat, InterpWrapMode::Repeat);
  near4!(report, exp5, res, float_tolerance);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:443
pub fn math_interp__CubicMitchellCharExactSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(72) as u8, (101) as u8, (140) as u8, (223) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (1.0_f32) as f32, (2.0_f32) as f32);
  eq!(report, (exp1).map(|v|v as i32), (res).map(|v|v as i32));
  let mut exp2:[u8;4] = [(233) as u8, (162) as u8, (99) as u8, (37) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (2.0_f32) as f32, (0.0_f32) as f32);
  eq!(report, (exp2).map(|v|v as i32), (res).map(|v|v as i32));

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:454
pub fn math_interp__CubicMitchellCharSamples()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(135) as u8, (132) as u8, (130) as u8, (127) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (0.625_f32) as f32);
  eq!(report, (exp1).map(|v|v as i32), (res).map(|v|v as i32));
  let mut exp2:[u8;4] = [(216) as u8, (189) as u8, (167) as u8, (143) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (1.4_f32) as f32, (0.1_f32) as f32);
  eq!(report, (exp2).map(|v|v as i32), (res).map(|v|v as i32));

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:466
pub fn math_interp__CubicMitchellFloatSamples()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(134.5659_f32) as f32, (131.91309_f32) as f32, (130.17685_f32) as f32, (126.66989_f32) as f32];
  res = interpolate_cubic_mitchell_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (0.625_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  let mut exp2:[f32;4] = [(216.27115_f32) as f32, (189.30673_f32) as f32, (166.93599_f32) as f32, (143.31964_f32) as f32];
  res = interpolate_cubic_mitchell_fl(&image_fl, image_width, image_height, (1.4_f32) as f32, (0.1_f32) as f32);
  near4!(report, exp2, res, float_tolerance);

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:477
pub fn math_interp__CubicMitchellCharPartiallyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[u8;4] = [0;4];
  let mut exp1:[u8;4] = [(0) as u8, (0) as u8, (0) as u8, (0) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  eq!(report, (exp1).map(|v|v as i32), (res).map(|v|v as i32));
  let mut exp2:[u8;4] = [(88) as u8, (116) as u8, (151) as u8, (228) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  eq!(report, (exp2).map(|v|v as i32), (res).map(|v|v as i32));
  let mut exp3:[u8;4] = [(239) as u8, (159) as u8, (89) as u8, (19) as u8];
  res = interpolate_cubic_mitchell_byte(&image_char, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  eq!(report, (exp3).map(|v|v as i32), (res).map(|v|v as i32));

report
}

// source/blender/blenlib/tests/BLI_math_interp_test.cc:491
pub fn math_interp__CubicMitchellFloatPartiallyOutsideImage()->Report{let mut report=Report::default();

  let mut res:[f32;4] = [0.0;4];
  let mut exp1:[f32;4] = [(0) as f32, (0) as f32, (0) as f32, (0) as f32];
  res = interpolate_cubic_mitchell_fl(&image_fl, image_width, image_height, (-0.5_f32) as f32, (2.0_f32) as f32);
  near4!(report, exp1, res, float_tolerance);
  let mut exp2:[f32;4] = [(87.98676_f32) as f32, (115.63634_f32) as f32, (151.13014_f32) as f32, (228.19823_f32) as f32];
  res = interpolate_cubic_mitchell_fl(&image_fl, image_width, image_height, (1.25_f32) as f32, (2.9_f32) as f32);
  near4!(report, exp2, res, float_tolerance);
  let mut exp3:[f32;4] = [(238.6136_f32) as f32, (158.58293_f32) as f32, (88.55761_f32) as f32, (18.53225_f32) as f32];
  res = interpolate_cubic_mitchell_fl(&image_fl, image_width, image_height, (2.2_f32) as f32, (-0.1_f32) as f32);
  near4!(report, exp3, res, float_tolerance);

report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("math_interp.NearestCharExactSamples",math_interp__NearestCharExactSamples,2),
("math_interp.NearestCharHalfwaySamples",math_interp__NearestCharHalfwaySamples,2),
("math_interp.NearestFloatExactSamples",math_interp__NearestFloatExactSamples,2),
("math_interp.NearestFloatHalfwaySamples",math_interp__NearestFloatHalfwaySamples,2),
("math_interp.BilinearCharExactSamples",math_interp__BilinearCharExactSamples,2),
("math_interp.BilinearCharHalfwayUSamples",math_interp__BilinearCharHalfwayUSamples,2),
("math_interp.BilinearCharHalfwayVSamples",math_interp__BilinearCharHalfwayVSamples,2),
("math_interp.BilinearCharSamples",math_interp__BilinearCharSamples,2),
("math_interp.BilinearFloatSamples",math_interp__BilinearFloatSamples,8),
("math_interp.BilinearCharPartiallyOutsideImageBorder",math_interp__BilinearCharPartiallyOutsideImageBorder,3),
("math_interp.BilinearCharPartiallyOutsideImage",math_interp__BilinearCharPartiallyOutsideImage,3),
("math_interp.BilinearCharPartiallyOutsideImageWrap",math_interp__BilinearCharPartiallyOutsideImageWrap,3),
("math_interp.BilinearFloatPartiallyOutsideImageBorder",math_interp__BilinearFloatPartiallyOutsideImageBorder,12),
("math_interp.BilinearFloatPartiallyOutsideImage",math_interp__BilinearFloatPartiallyOutsideImage,13),
("math_interp.BilinearFloatPartiallyOutsideImageWrap",math_interp__BilinearFloatPartiallyOutsideImageWrap,32),
("math_interp.BilinearCharFullyOutsideImage",math_interp__BilinearCharFullyOutsideImage,8),
("math_interp.BilinearFloatFullyOutsideImage",math_interp__BilinearFloatFullyOutsideImage,8),
("math_interp.CubicBSplineCharExactSamples",math_interp__CubicBSplineCharExactSamples,2),
("math_interp.CubicBSplineCharSamples",math_interp__CubicBSplineCharSamples,2),
("math_interp.CubicBSplineFloatSamples",math_interp__CubicBSplineFloatSamples,8),
("math_interp.CubicBSplineCharPartiallyOutsideImage",math_interp__CubicBSplineCharPartiallyOutsideImage,3),
("math_interp.CubicBSplineFloatPartiallyOutsideImage",math_interp__CubicBSplineFloatPartiallyOutsideImage,32),
("math_interp.CubicMitchellCharExactSamples",math_interp__CubicMitchellCharExactSamples,2),
("math_interp.CubicMitchellCharSamples",math_interp__CubicMitchellCharSamples,2),
("math_interp.CubicMitchellFloatSamples",math_interp__CubicMitchellFloatSamples,8),
("math_interp.CubicMitchellCharPartiallyOutsideImage",math_interp__CubicMitchellCharPartiallyOutsideImage,3),
("math_interp.CubicMitchellFloatPartiallyOutsideImage",math_interp__CubicMitchellFloatPartiallyOutsideImage,12),
];
