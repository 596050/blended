// SPDX-FileCopyrightText: 2024-2026 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked tests; see compatibility/pixel-format-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::pixel_formats as m;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$v:expr)=>{{$r.check($v,stringify!($v),line!());}};}
fn array_eq<T:PartialEq+Copy>(report:&mut Report,a:&[T],b:&[T],n:usize){for i in 0..n{eq!(report,a[i],b[i]);}}

// source/blender/blenlib/tests/BLI_math_half_test.cc:17
pub fn math_half__half_to_float_scalar()->Report{let mut report=Report::default();
eq!(report, m::half_to_float(0), 0.0_f32);
  eq!(report, m::half_to_float(1), 5.960464478e-08_f32);
  eq!(report, m::half_to_float(32), 1.907348633e-06_f32);
  eq!(report, m::half_to_float(37), 2.205371857e-06_f32);
  eq!(report, m::half_to_float(511), 3.045797348e-05_f32);
  eq!(report, m::half_to_float(999), 5.954504013e-05_f32);
  eq!(report, m::half_to_float(1024), 6.103515625e-05_f32);
  eq!(report, m::half_to_float(1357), 8.088350296e-05_f32);
  eq!(report, m::half_to_float(6789), 0.003183364868_f32);
  eq!(report, m::half_to_float(16383), 1.999023438_f32);
  eq!(report, m::half_to_float(16384), 2.0_f32);
  eq!(report, m::half_to_float(31743), 65504.0_f32);
  eq!(report, m::half_to_float(31744), f32::INFINITY);
  yes!(report, m::half_to_float(31746).is_nan());
  yes!(report, m::half_to_float(32767).is_nan());
  eq!(report, m::half_to_float(32768), -0.0_f32);
  eq!(report, m::half_to_float(32769), -5.960464478e-08_f32);
  eq!(report, m::half_to_float(46765), -0.4172363281_f32);
  eq!(report, m::half_to_float(54501), -78.3125_f32);
  eq!(report, m::half_to_float(64511), -65504.0_f32);
  eq!(report, m::half_to_float(64512), -f32::INFINITY);
  yes!(report, m::half_to_float(64513).is_nan());
  yes!(report, m::half_to_float(65535).is_nan());
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:44
pub fn math_half__float_to_half_scalar()->Report{let mut report=Report::default();
eq!(report, m::float_to_half(0.0_f32), 0);
  eq!(report, m::float_to_half(f32::MIN_POSITIVE), 0);
  eq!(report, m::float_to_half(5.960464478e-08_f32), 1);
  eq!(report, m::float_to_half(1.907348633e-06_f32), 32);
  eq!(report, m::float_to_half(2.205371857e-06_f32), 37);
  eq!(report, m::float_to_half(3.045797348e-05_f32), 511);
  eq!(report, m::float_to_half(5.954504013e-05_f32), 999);
  eq!(report, m::float_to_half(6.103515625e-05_f32), 1024);
  eq!(report, m::float_to_half(8.088350296e-05_f32), 1357);
  eq!(report, m::float_to_half(0.003183364868_f32), 6789);
  eq!(report, m::float_to_half(0.1_f32), 11878);
  eq!(report, m::float_to_half(1.0_f32), 15360);
  eq!(report, m::float_to_half(1.999023438_f32), 16383);
  eq!(report, m::float_to_half(1.999523438_f32), 16384);
  eq!(report, m::float_to_half(2.0_f32), 16384);
  eq!(report, m::float_to_half(11.0_f32), 18816);
  eq!(report, m::float_to_half(65504.0_f32), 31743);
  eq!(report, m::float_to_half(65535.0_f32), 31744);               
  eq!(report, m::float_to_half(1.0e6_f32), 31744);                 
  eq!(report, m::float_to_half(f32::INFINITY), 31744);
  eq!(report, m::float_to_half(f32::MAX), 31744);
  eq!(report, m::float_to_half(f32::from_bits(0x7fc00000)), 32256);
  eq!(report, m::float_to_half(-0.0_f32), 32768);
  eq!(report, m::float_to_half(-5.960464478e-08_f32), 32769);
  eq!(report, m::float_to_half(-0.4172363281_f32), 46765);
  eq!(report, m::float_to_half(-1.0_f32), 48128);
  eq!(report, m::float_to_half(-78.3125_f32), 54501);
  eq!(report, m::float_to_half(-123.5_f32), 55224);
  eq!(report, m::float_to_half(-65504.0_f32), 64511);
  eq!(report, m::float_to_half(-65536.0_f32), 64512);                
  eq!(report, m::float_to_half(-1.0e6_f32), 64512);                  
  eq!(report, m::float_to_half(-f32::INFINITY), 64512);
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:82
pub fn math_half__float_to_half_make_finite_scalar()->Report{let mut report=Report::default();
eq!(report, m::float_to_half_make_finite(0.0_f32), 0);
  eq!(report, m::float_to_half_make_finite(f32::MIN_POSITIVE), 0);
  eq!(report, m::float_to_half_make_finite(5.960464478e-08_f32), 1);
  eq!(report, m::float_to_half_make_finite(1.907348633e-06_f32), 32);
  eq!(report, m::float_to_half_make_finite(2.205371857e-06_f32), 37);
  eq!(report, m::float_to_half_make_finite(3.045797348e-05_f32), 511);
  eq!(report, m::float_to_half_make_finite(5.954504013e-05_f32), 999);
  eq!(report, m::float_to_half_make_finite(6.103515625e-05_f32), 1024);
  eq!(report, m::float_to_half_make_finite(8.088350296e-05_f32), 1357);
  eq!(report, m::float_to_half_make_finite(0.003183364868_f32), 6789);
  eq!(report, m::float_to_half_make_finite(0.1_f32), 11878);
  eq!(report, m::float_to_half_make_finite(1.0_f32), 15360);
  eq!(report, m::float_to_half_make_finite(1.999023438_f32), 16383);
  eq!(report, m::float_to_half_make_finite(1.999523438_f32), 16384);
  eq!(report, m::float_to_half_make_finite(2.0_f32), 16384);
  eq!(report, m::float_to_half_make_finite(11.0_f32), 18816);
  eq!(report, m::float_to_half_make_finite(65504.0_f32), 31743);
                                        
  eq!(report, m::float_to_half_make_finite(65535.0_f32), 31743);
  eq!(report, m::float_to_half_make_finite(1.0e6_f32), 31743);
  eq!(report, m::float_to_half_make_finite(f32::INFINITY), 31743);
  eq!(report, m::float_to_half_make_finite(f32::MAX), 31743);
                            
  eq!(report, m::float_to_half_make_finite(f32::from_bits(0x7fc00000)), 0);
  eq!(report, m::float_to_half_make_finite(f32::from_bits(0x7fa00000)), 0);
  eq!(report, m::float_to_half_make_finite(-0.0_f32), 32768);
  eq!(report, m::float_to_half_make_finite(-5.960464478e-08_f32), 32769);
  eq!(report, m::float_to_half_make_finite(-0.4172363281_f32), 46765);
  eq!(report, m::float_to_half_make_finite(-1.0_f32), 48128);
  eq!(report, m::float_to_half_make_finite(-78.3125_f32), 54501);
  eq!(report, m::float_to_half_make_finite(-123.5_f32), 55224);
  eq!(report, m::float_to_half_make_finite(-65504.0_f32), 64511);
                                                  
  eq!(report, m::float_to_half_make_finite(-65536.0_f32), 64511);
  eq!(report, m::float_to_half_make_finite(-1.0e6_f32), 64511);
  eq!(report, m::float_to_half_make_finite(-f32::INFINITY), 64511);
                                      
  eq!(report, m::float_to_half_make_finite(-f32::from_bits(0x7fc00000)), 32768);
  eq!(report, m::float_to_half_make_finite(-f32::from_bits(0x7fa00000)), 32768);
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:127
pub fn math_half__half_to_float_array()->Report{let mut report=Report::default();
let mut src:[u16;13]=[0, 1, 6789, 16383, 16384, 31743, 31744, 32768, 32769, 46765, 54501, 64511, 64512];
                                                                                
  let mut exp:[f32;14]=[0.0_f32,
      5.960464478e-08_f32,
      0.003183364868_f32,
      1.999023438_f32,
      2.0_f32,
      65504.0_f32,
      f32::INFINITY,
      -0.0_f32,
      -5.960464478e-08_f32,
      -0.4172363281_f32,
      -78.3125_f32,
      -65504.0_f32,
      -f32::INFINITY,
      1.2345_f32,];
  let mut dst:[f32;14]=[0.0_f32;14];
  dst[13] = 1.2345_f32;

  m::half_to_float_array(&src, &mut dst, 13);
  array_eq(&mut report, &exp, &dst, 14);
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:155
pub fn math_half__half_to_float_array_flush_to_zero()->Report{let mut report=Report::default();
let mut src:[u16;8]=[0, 1, 32, 511, 1023, 1024, 32769, 33791];
  let mut exp:[f32;8]=[0.0_f32,
      5.960464478e-08_f32,
      1.907348633e-06_f32,
      3.045797348e-05_f32,
      6.097555160e-05_f32,
      6.103515625e-05_f32,
      -5.960464478e-08_f32,
      -6.097555160e-05_f32,];
  let mut dst:[f32;8]=[0.0_f32;8];

  {
    let _flush_to_zero=m::ScopedFlushToZero::new();
    m::half_to_float_array(&src, &mut dst, 8);
  }

  array_eq(&mut report, &exp, &dst, 8);
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:180
pub fn math_half__float_to_half_array()->Report{let mut report=Report::default();
let mut src:[f32;13]=[0.0_f32,
                         5.960464478e-08_f32,
                         0.003183364868_f32,
                         1.999023438_f32,
                         2.0_f32,
                         65504.0_f32,
                         f32::INFINITY,
                         -0.0_f32,
                         -5.960464478e-08_f32,
                         -0.4172363281_f32,
                         -78.3125_f32,
                         -65504.0_f32,
                         -f32::INFINITY];
                                                                                
  let mut exp:[u16;14]=[0, 1, 6789, 16383, 16384, 31743, 31744, 32768, 32769, 46765, 54501, 64511, 64512, 12345];
  let mut dst:[u16;14]=[0_u16;14];
  dst[13] = 12345;

  m::float_to_half_array(&src, &mut dst, 13);
  array_eq(&mut report, &exp, &dst, 14);
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:205
pub fn math_half__float_to_half_clamp_array()->Report{let mut report=Report::default();
let mut src:[f32;17]=[0.0_f32,
      5.960464478e-08_f32,
      0.003183364868_f32,
      1.999023438_f32,
      2.0_f32,
      65504.0_f32,
      f32::INFINITY,
      -0.0_f32,
      -5.960464478e-08_f32,
      -0.4172363281_f32,
      -78.3125_f32,
      -65504.0_f32,
      -f32::INFINITY,
      100000.0_f32,
      -100000.0_f32,
      f32::from_bits(0x7fc00000),
      -f32::from_bits(0x7fc00000),];
                                                                                
  let mut exp:[u16;18]=[0,
                            1,
                            6789,
                            16383,
                            16384,
                            25552,
                            25552,
                            32768,
                            32769,
                            46765,
                            51456,
                            51456,
                            51456,
                            25552,
                            51456,
                            0,
                            0,
                            12345];
  let mut dst:[u16;18]=[0_u16;18];
  dst[17] = 12345;
  m::float_to_half_clamp_array(&src, &mut dst, 17, -10.0_f32, 1000.0_f32);
  array_eq(&mut report, &exp, &dst, 18);
report
}

// source/blender/blenlib/tests/BLI_math_half_test.cc:251
pub fn math_half__float_to_half_make_finite_array()->Report{let mut report=Report::default();
let mut src:[f32;17]=[0.0_f32,
      5.960464478e-08_f32,
      0.003183364868_f32,
      1.999023438_f32,
      2.0_f32,
      65504.0_f32,
      f32::INFINITY,
      -0.0_f32,
      -5.960464478e-08_f32,
      -0.4172363281_f32,
      -78.3125_f32,
      -65504.0_f32,
      -f32::INFINITY,
      100000.0_f32,
      -100000.0_f32,
      f32::from_bits(0x7fc00000),
      -f32::from_bits(0x7fc00000),];
                                                                                
  let mut exp:[u16;18]=[0,
                            1,
                            6789,
                            16383,
                            16384,
                            31743,
                            31743,
                            32768,
                            32769,
                            46765,
                            54501,
                            64511,
                            64511,
                            31743,
                            64511,
                            0,
                            32768,
                            12345];
  let mut dst:[u16;18]=[0_u16;18];
  dst[17] = 12345;
  m::float_to_half_make_finite_array(&src, &mut dst, 17);
  array_eq(&mut report, &exp, &dst, 18);
report
}

// source/blender/blenlib/tests/BLI_normalized_int_test.cc:11
pub fn normalized_int__roundtrip()->Report{let mut report=Report::default();

  {
    let a:[f32;4]=[-1.0_f32, 1.0_f32 / 127.0_f32, 64.0_f32 / 127.0_f32, 1.0_f32];
    eq!(report, m::char4_norm(a).to_float(), a);
  }
  {
    let a:[f32;4]=[0.0_f32, 1.0_f32 / 255.0_f32, 128.0_f32 / 255.0_f32, 1.0_f32];
    eq!(report, m::uchar4_norm(a).to_float(), a);
  }
  {
    let a:[f32;4]=[-1.0_f32, 1.0_f32 / 32767.0_f32, 128.0_f32 / 32767.0_f32, 1.0_f32];
    eq!(report, m::short4_norm(a).to_float(), a);
  }
  {
    let a:[f32;2]=[-1.0_f32, 1.0_f32 / 32767.0_f32];
    eq!(report, m::short2_norm(a).to_float(), a);
  }
  {
    let a:[f32;4]=[0.0_f32, 1.0_f32 / 65535.0_f32, 64.0_f32 / 65535.0_f32, 1.0_f32];
    eq!(report, m::ushort4_norm(a).to_float(), a);
  }
  {
    let a:[f32;4]=[-1.0_f32, 1.0_f32 / 511.0_f32, 128.0_f32 / 511.0_f32, 1.0_f32];
    eq!(report, m::int1010102_norm(a).to_float(), a);
  }
  {
    let a:[f32;4]=[0.0_f32, 1.0_f32 / 1023.0_f32, 64.0_f32 / 1023.0_f32, 1.0_f32];
    eq!(report, m::uint1010102_norm(a).to_float(), a);
  }

report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("math_half.half_to_float_scalar",math_half__half_to_float_scalar,23),
("math_half.float_to_half_scalar",math_half__float_to_half_scalar,32),
("math_half.float_to_half_make_finite_scalar",math_half__float_to_half_make_finite_scalar,35),
("math_half.half_to_float_array",math_half__half_to_float_array,14),
("math_half.half_to_float_array_flush_to_zero",math_half__half_to_float_array_flush_to_zero,8),
("math_half.float_to_half_array",math_half__float_to_half_array,14),
("math_half.float_to_half_clamp_array",math_half__float_to_half_clamp_array,18),
("math_half.float_to_half_make_finite_array",math_half__float_to_half_make_finite_array,18),
("normalized_int.roundtrip",normalized_int__roundtrip,7),
];
