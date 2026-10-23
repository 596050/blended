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
use crate::curve_sampling::*;
// Translated upstream helpers, including every EXPECT_NEAR in test_uniform_lengths.
fn calculate_lengths<T:CurveValue>(values:&[T],cyclic:bool)->Vec<f32>{
 let mut lengths=vec![0.0;segments_num(values.len(),cyclic)];
 accumulate_lengths(values,cyclic,&mut lengths);lengths
}
fn test_uniform_lengths<T:CurveValue>(report:&mut Report,values:&[T]){
 let segment_length=values[0].distance(*values.last().unwrap())/((values.len()-1) as f32);
 for i in 0..values.len()-1{near!(report,values[i].distance(values[i+1]),segment_length,1e-5);}
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:31
pub fn length_parameterize__FloatSimple()->Report{let mut report=Report::default();

  let mut values:Vec<f32> = vec![(0) as f32, (1) as f32, (4) as f32];
  let mut lengths:Vec<f32> = calculate_lengths(&values, false);

  let mut indices:Vec<i32> = vec![0_i32;4];
  let mut factors:Vec<f32> = vec![0.0_f32;4];
  sample_uniform(&lengths, true, &mut indices, &mut factors);
  let mut results:Vec<f32> = vec![0.0_f32;4];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<f32> = vec![(0.0_f32) as f32, (1.33333_f32) as f32, (2.66667_f32) as f32, (4.0_f32) as f32];
  for i in 0..results.len() {
    near!(report, results[i], expected[i], 1e-5);
  }
  test_uniform_lengths(&mut report, &results);

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:53
pub fn length_parameterize__Float()->Report{let mut report=Report::default();

  let mut values:Vec<f32> = vec![(1) as f32, (2) as f32, (3) as f32, (5) as f32, (10) as f32];
  let mut lengths:Vec<f32> = calculate_lengths(&values, false);

  let mut indices:Vec<i32> = vec![0_i32;20];
  let mut factors:Vec<f32> = vec![0.0_f32;20];
  sample_uniform(&lengths, true, &mut indices, &mut factors);
  let mut results:Vec<f32> = vec![0.0_f32;20];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<f32> = vec![(1.0_f32) as f32, (1.47368_f32) as f32, (1.94737_f32) as f32, (2.42105_f32) as f32, (2.89474_f32) as f32, (3.36842_f32) as f32, (3.84211_f32) as f32, (4.31579_f32) as f32, (4.78947_f32) as f32, (5.26316_f32) as f32, (5.73684_f32) as f32, (6.21053_f32) as f32, (6.68421_f32) as f32, (7.1579_f32) as f32, (7.63158_f32) as f32, (8.10526_f32) as f32, (8.57895_f32) as f32, (9.05263_f32) as f32, (9.52632_f32) as f32, (10.0_f32) as f32];
  for i in 0..results.len() {
    near!(report, results[i], expected[i], 1e-5);
  }
  test_uniform_lengths(&mut report, &results);

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:74
pub fn length_parameterize__Float2()->Report{let mut report=Report::default();

  let mut values:Vec<[f32;2]> = vec![[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]];
  let mut lengths:Vec<f32> = calculate_lengths(&values, false);

  let mut indices:Vec<i32> = vec![0_i32;12];
  let mut factors:Vec<f32> = vec![0.0_f32;12];
  sample_uniform(&lengths, true, &mut indices, &mut factors);
  let mut results:Vec<[f32;2]> = vec![[0.0_f32;2];12];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<[f32;2]> = vec![[(0.0_f32) as f32, (0.0_f32) as f32], [(0.272727_f32) as f32, (0.0_f32) as f32], [(0.545455_f32) as f32, (0.0_f32) as f32], [(0.818182_f32) as f32, (0.0_f32) as f32], [(1.0_f32) as f32, (0.0909091_f32) as f32], [(1.0_f32) as f32, (0.363636_f32) as f32], [(1.0_f32) as f32, (0.636364_f32) as f32], [(1.0_f32) as f32, (0.909091_f32) as f32], [(0.818182_f32) as f32, (1.0_f32) as f32], [(0.545455_f32) as f32, (1.0_f32) as f32], [(0.272727_f32) as f32, (1.0_f32) as f32], [(0.0_f32) as f32, (1.0_f32) as f32]];
  for i in 0..results.len() {
    near!(report, results[i][0], expected[i][0], 1e-5);
    near!(report, results[i][1], expected[i][1], 1e-5);
  }

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:104
pub fn length_parameterize__Float2Cyclic()->Report{let mut report=Report::default();

  let mut values:Vec<[f32;2]> = vec![[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]];
  let mut lengths:Vec<f32> = calculate_lengths(&values, true);

  let mut indices:Vec<i32> = vec![0_i32;12];
  let mut factors:Vec<f32> = vec![0.0_f32;12];
  sample_uniform(&lengths, false, &mut indices, &mut factors);
  let mut results:Vec<[f32;2]> = vec![[0.0_f32;2];12];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<[f32;2]> = vec![[(0.0_f32) as f32, (0.0_f32) as f32], [(0.333333_f32) as f32, (0.0_f32) as f32], [(0.666667_f32) as f32, (0.0_f32) as f32], [(1.0_f32) as f32, (0.0_f32) as f32], [(1.0_f32) as f32, (0.333333_f32) as f32], [(1.0_f32) as f32, (0.666667_f32) as f32], [(1.0_f32) as f32, (1.0_f32) as f32], [(0.666667_f32) as f32, (1.0_f32) as f32], [(0.333333_f32) as f32, (1.0_f32) as f32], [(0.0_f32) as f32, (1.0_f32) as f32], [(0.0_f32) as f32, (0.666667_f32) as f32], [(0.0_f32) as f32, (0.333333_f32) as f32]];
  for i in 0..results.len() {
    near!(report, results[i][0], expected[i][0], 1e-5);
    near!(report, results[i][1], expected[i][1], 1e-5);
  }

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:134
pub fn length_parameterize__LineMany()->Report{let mut report=Report::default();

  let mut values:Vec<f32> = vec![(1) as f32, (2) as f32];
  let mut lengths:Vec<f32> = calculate_lengths(&values, false);

  let mut indices:Vec<i32> = vec![0_i32;5007];
  let mut factors:Vec<f32> = vec![0.0_f32;5007];
  sample_uniform(&lengths, true, &mut indices, &mut factors);
  let mut results:Vec<f32> = vec![0.0_f32;5007];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<f32> = vec![(1.9962_f32) as f32, (1.9964_f32) as f32, (1.9966_f32) as f32, (1.9968_f32) as f32, (1.997_f32) as f32, (1.9972_f32) as f32, (1.9974_f32) as f32, (1.9976_f32) as f32, (1.9978_f32) as f32, (1.998_f32) as f32, (1.9982_f32) as f32, (1.9984_f32) as f32, (1.9986_f32) as f32, (1.9988_f32) as f32, (1.999_f32) as f32, (1.9992_f32) as f32, (1.9994_f32) as f32, (1.9996_f32) as f32, (1.9998_f32) as f32, (2.0_f32) as f32];
  for i in 0..expected.len() {
    near!(report, results[results.len()-20..][i], expected[i], 1e-5);
  }

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:153
pub fn length_parameterize__CyclicMany()->Report{let mut report=Report::default();

  let mut values:Vec<[f32;2]> = vec![[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]];
  let mut lengths:Vec<f32> = calculate_lengths(&values, true);

  let mut indices:Vec<i32> = vec![0_i32;5007];
  let mut factors:Vec<f32> = vec![0.0_f32;5007];
  sample_uniform(&lengths, false, &mut indices, &mut factors);
  let mut results:Vec<[f32;2]> = vec![[0.0_f32;2];5007];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<[f32;2]> = vec![[(0) as f32, (0.0159776) as f32], [(0) as f32, (0.0151787) as f32], [(0) as f32, (0.0143797) as f32], [(0) as f32, (0.013581) as f32], [(0) as f32, (0.0127821) as f32], [(0) as f32, (0.0119832) as f32], [(0) as f32, (0.0111842) as f32], [(0) as f32, (0.0103855) as f32], [(0) as f32, (0.00958657) as f32], [(0) as f32, (0.00878763) as f32], [(0) as f32, (0.00798869) as f32], [(0) as f32, (0.00718999) as f32], [(0) as f32, (0.00639105) as f32], [(0) as f32, (0.00559211) as f32], [(0) as f32, (0.00479317) as f32], [(0) as f32, (0.00399446) as f32], [(0) as f32, (0.00319552) as f32], [(0) as f32, (0.00239658) as f32], [(0) as f32, (0.00159764) as f32], [(0) as f32, (0.000798941) as f32]];
  for i in 0..expected.len() {
    near!(report, results[results.len()-20..][i][0], expected[i][0], 1e-5);
    near!(report, results[results.len()-20..][i][1], expected[i][1], 1e-5);
  }

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:175
pub fn length_parameterize__InterpolateColor()->Report{let mut report=Report::default();

  let mut values:Vec<[f32;2]> = vec![[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]];
  let mut lengths:Vec<f32> = calculate_lengths(&values, true);

  let mut colors:Vec<[f32;4]> = vec![[(0) as f32, (0) as f32, (0) as f32, (1) as f32], [(1) as f32, (0) as f32, (0) as f32, (1) as f32], [(1) as f32, (1) as f32, (0) as f32, (1) as f32], [(0) as f32, (1) as f32, (0) as f32, (1) as f32]];

  let mut indices:Vec<i32> = vec![0_i32;10];
  let mut factors:Vec<f32> = vec![0.0_f32;10];
  sample_uniform(&lengths, false, &mut indices, &mut factors);
  let mut results:Vec<[f32;4]> = vec![[0.0_f32;4];10];
  interpolate(&colors, &indices, &factors, &mut results);
  let mut expected:Vec<[f32;4]> = vec![[(0) as f32, (0) as f32, (0) as f32, (1) as f32], [(0.4) as f32, (0) as f32, (0) as f32, (1) as f32], [(0.8) as f32, (0) as f32, (0) as f32, (1) as f32], [(1) as f32, (0.2) as f32, (0) as f32, (1) as f32], [(1) as f32, (0.6) as f32, (0) as f32, (1) as f32], [(1) as f32, (1) as f32, (0) as f32, (1) as f32], [(0.6) as f32, (1) as f32, (0) as f32, (1) as f32], [(0.2) as f32, (1) as f32, (0) as f32, (1) as f32], [(0) as f32, (0.8) as f32, (0) as f32, (1) as f32], [(0) as f32, (0.4) as f32, (0) as f32, (1) as f32]];
  for i in 0..results.len() {
    near!(report, results[i][0], expected[i][0], 1e-6);
    near!(report, results[i][1], expected[i][1], 1e-6);
    near!(report, results[i][2], expected[i][2], 1e-6);
    near!(report, results[i][3], expected[i][3], 1e-6);
  }

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:207
pub fn length_parameterize__ArbitraryFloatSimple()->Report{let mut report=Report::default();

  let mut values:Vec<f32> = vec![(0) as f32, (1) as f32, (4) as f32];
  let mut lengths:Vec<f32> = calculate_lengths(&values, false);

  let mut sample_lengths:Vec<f32> = vec![(0.5_f32) as f32, (1.5_f32) as f32, (2.0_f32) as f32, (4.0_f32) as f32];
  let mut indices:Vec<i32> = vec![0_i32;4];
  let mut factors:Vec<f32> = vec![0.0_f32;4];
  sample_at_lengths(&lengths, &sample_lengths, &mut indices, &mut factors);
  let mut results:Vec<f32> = vec![0.0_f32;4];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<f32> = vec![(0.5_f32) as f32, (1.5_f32) as f32, (2.0_f32) as f32, (4.0_f32) as f32];
  for i in 0..results.len() {
    near!(report, results[i], expected[i], 1e-5);
  }

report
}

// source/blender/blenlib/tests/BLI_length_parameterize_test.cc:229
pub fn length_parameterize__ArbitraryFloat2()->Report{let mut report=Report::default();

  let mut values:Vec<[f32;2]> = vec![[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]];
  let mut lengths:Vec<f32> = calculate_lengths(&values, true);

  let mut sample_lengths:Vec<f32> = vec![(0.5_f32) as f32, (1.5_f32) as f32, (2.0_f32) as f32, (2.0_f32) as f32, (2.1_f32) as f32, (2.5_f32) as f32, (3.5_f32) as f32, (3.6_f32) as f32, (3.8_f32) as f32, (3.85_f32) as f32, (3.90_f32) as f32, (4.0_f32) as f32];
  let mut indices:Vec<i32> = vec![0_i32;12];
  let mut factors:Vec<f32> = vec![0.0_f32;12];
  sample_at_lengths(&lengths, &sample_lengths, &mut indices, &mut factors);
  let mut results:Vec<[f32;2]> = vec![[0.0_f32;2];12];
  interpolate(&values, &indices, &factors, &mut results);
  let mut expected:Vec<[f32;2]> = vec![[(0.5_f32) as f32, (0.0_f32) as f32], [(1.0_f32) as f32, (0.5_f32) as f32], [(1.0_f32) as f32, (1.0_f32) as f32], [(1.0_f32) as f32, (1.0_f32) as f32], [(0.9_f32) as f32, (1.0_f32) as f32], [(0.5_f32) as f32, (1.0_f32) as f32], [(0.0_f32) as f32, (0.5_f32) as f32], [(0.0_f32) as f32, (0.4_f32) as f32], [(0.0_f32) as f32, (0.2_f32) as f32], [(0.0_f32) as f32, (0.15_f32) as f32], [(0.0_f32) as f32, (0.1_f32) as f32], [(0.0_f32) as f32, (0.0_f32) as f32]];
  for i in 0..results.len() {
    near!(report, results[i][0], expected[i][0], 1e-5);
    near!(report, results[i][1], expected[i][1], 1e-5);
  }

report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("length_parameterize.FloatSimple",length_parameterize__FloatSimple,7),
("length_parameterize.Float",length_parameterize__Float,39),
("length_parameterize.Float2",length_parameterize__Float2,24),
("length_parameterize.Float2Cyclic",length_parameterize__Float2Cyclic,24),
("length_parameterize.LineMany",length_parameterize__LineMany,20),
("length_parameterize.CyclicMany",length_parameterize__CyclicMany,40),
("length_parameterize.InterpolateColor",length_parameterize__InterpolateColor,40),
("length_parameterize.ArbitraryFloatSimple",length_parameterize__ArbitraryFloatSimple,4),
("length_parameterize.ArbitraryFloat2",length_parameterize__ArbitraryFloat2,24),
];
