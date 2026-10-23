// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from pinned original matrix test bodies, not replacement expectations.
#![allow(non_snake_case,unused_mut,unused_parens,unused_variables,unused_assignments)]
use crate::numeric_vectors as v;
use crate::matrix_types as m;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! numeq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a as f64)==($b as f64),stringify!($a == $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b within $e),line!());}};}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:14
pub fn math_matrix_types__DefaultConstructor()->Report{let mut r=Report::default();
let mut m = m::M::<f32,2,2>::default();
  numeq!(r, m.get(0,0), 0.0_f32);
  numeq!(r, m.get(1,1), 0.0_f32);
  numeq!(r, m.get(0,1), 0.0_f32);
  numeq!(r, m.get(1,0), 0.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:23
pub fn math_matrix_types__StaticConstructor()->Report{let mut r=Report::default();
let mut m = m::M::<f32,2,2>::identity();
  numeq!(r, m.get(0,0), 1.0_f32);
  numeq!(r, m.get(1,1), 1.0_f32);
  numeq!(r, m.get(0,1), 0.0_f32);
  numeq!(r, m.get(1,0), 0.0_f32);

  m = m::M::<f32,2,2>::zero();
  numeq!(r, m.get(0,0), 0.0_f32);
  numeq!(r, m.get(1,1), 0.0_f32);
  numeq!(r, m.get(0,1), 0.0_f32);
  numeq!(r, m.get(1,0), 0.0_f32);

  m = m::M::<f32,2,2>::diagonal((2) as f64);
  numeq!(r, m.get(0,0), 2.0_f32);
  numeq!(r, m.get(1,1), 2.0_f32);
  numeq!(r, m.get(0,1), 0.0_f32);
  numeq!(r, m.get(1,0), 0.0_f32);

  m = m::M::<f32,2,2>::all((1) as f64);
  numeq!(r, m.get(0,0), 1.0_f32);
  numeq!(r, m.get(1,1), 1.0_f32);
  numeq!(r, m.get(0,1), 1.0_f32);
  numeq!(r, m.get(1,0), 1.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:50
pub fn math_matrix_types__VectorConstructor()->Report{let mut r=Report::default();
let mut m = m::M::<f32,3,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(1.0_f32) as &dyn v::Components, &(2.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(3.0_f32) as &dyn v::Components, &(4.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(5.0_f32) as &dyn v::Components, &(6.0_f32) as &dyn v::Components])) as &dyn v::Components])]);
  numeq!(r, m.get(0,0), 1.0_f32);
  numeq!(r, m.get(0,1), 2.0_f32);
  numeq!(r, m.get(1,0), 3.0_f32);
  numeq!(r, m.get(1,1), 4.0_f32);
  numeq!(r, m.get(2,0), 5.0_f32);
  numeq!(r, m.get(2,1), 6.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:61
pub fn math_matrix_types__SmallerMatrixConstructor()->Report{let mut r=Report::default();
let mut m2 = m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(1.0_f32) as &dyn v::Components, &(2.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(3.0_f32) as &dyn v::Components, &(4.0_f32) as &dyn v::Components])) as &dyn v::Components])]);
  let mut m3 = m::M::<f32,3,3>::from_matrix(&(m2));
  numeq!(r, m3.get(0,0), 1.0_f32);
  numeq!(r, m3.get(0,1), 2.0_f32);
  numeq!(r, m3.get(0,2), 0.0_f32);
  numeq!(r, m3.get(1,0), 3.0_f32);
  numeq!(r, m3.get(1,1), 4.0_f32);
  numeq!(r, m3.get(1,2), 0.0_f32);
  numeq!(r, m3.get(2,0), 0.0_f32);
  numeq!(r, m3.get(2,1), 0.0_f32);
  numeq!(r, m3.get(2,2), 1.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:76
pub fn math_matrix_types__ComponentMasking()->Report{let mut r=Report::default();
let mut m3 = m::M::<f32,3,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(1.1_f32) as &dyn v::Components, &(1.2_f32) as &dyn v::Components, &(1.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(2.1_f32) as &dyn v::Components, &(2.2_f32) as &dyn v::Components, &(2.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(3.1_f32) as &dyn v::Components, &(3.2_f32) as &dyn v::Components, &(3.3_f32) as &dyn v::Components])) as &dyn v::Components])]);
  let mut m2 = m::M::<f32,2,2>::from_matrix(&(m3));
  numeq!(r, m2.get(0,0), 1.1_f32);
  numeq!(r, m2.get(0,1), 1.2_f32);
  numeq!(r, m2.get(1,0), 2.1_f32);
  numeq!(r, m2.get(1,1), 2.2_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:86
pub fn math_matrix_types__PointerConversion()->Report{let mut r=Report::default();
let array=[1.0_f32,2.0_f32,3.0_f32,4.0_f32];
  let mut m2 = m::M::<f32,2,2>::from_flat(&array);
  numeq!(r, m2.get(0,0), 1.0_f32);
  numeq!(r, m2.get(0,1), 2.0_f32);
  numeq!(r, m2.get(1,0), 3.0_f32);
  numeq!(r, m2.get(1,1), 4.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:96
pub fn math_matrix_types__TypeConversion()->Report{let mut r=Report::default();
let mut m = m::M::<f32,3,2>::from_matrix(&(m::M::<f64,3,2>::from_cols([v::construct::<f64,2>(&[&(v::construct::<f64,2>(&[&(1.0_f32) as &dyn v::Components, &(2.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f64,2>(&[&(v::construct::<f64,2>(&[&(3.0_f32) as &dyn v::Components, &(4.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f64,2>(&[&(v::construct::<f64,2>(&[&(5.0_f32) as &dyn v::Components, &(6.0_f32) as &dyn v::Components])) as &dyn v::Components])])));
  numeq!(r, m.get(0,0), 1.0_f32);
  numeq!(r, m.get(0,1), 2.0_f32);
  numeq!(r, m.get(1,0), 3.0_f32);
  numeq!(r, m.get(1,1), 4.0_f32);
  numeq!(r, m.get(2,0), 5.0_f32);
  numeq!(r, m.get(2,1), 6.0_f32);

  let mut d = m::M::<f64,3,2>::from_matrix(&(m));
  numeq!(r, d.get(0,0), 1.0_f32);
  numeq!(r, d.get(0,1), 2.0_f32);
  numeq!(r, d.get(1,0), 3.0_f32);
  numeq!(r, d.get(1,1), 4.0_f32);
  numeq!(r, d.get(2,0), 5.0_f32);
  numeq!(r, d.get(2,1), 6.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:115
pub fn math_matrix_types__PointerArrayConversion()->Report{let mut r=Report::default();
let array=[[1.0_f32,2.0_f32],[3.0_f32,4.0_f32]];
  let ptr=&array;
  let mut m2 = m::M::<f32,2,2>::from_array(ptr);
  numeq!(r, m2.get(0,0), 1.0_f32);
  numeq!(r, m2.get(0,1), 2.0_f32);
  numeq!(r, m2.get(1,0), 3.0_f32);
  numeq!(r, m2.get(1,1), 4.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:126
pub fn math_matrix_types__ComponentAccess()->Report{let mut r=Report::default();
let mut m3 = m::M::<f32,3,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(1.1_f32) as &dyn v::Components, &(1.2_f32) as &dyn v::Components, &(1.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(2.1_f32) as &dyn v::Components, &(2.2_f32) as &dyn v::Components, &(2.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(3.1_f32) as &dyn v::Components, &(3.2_f32) as &dyn v::Components, &(3.3_f32) as &dyn v::Components])) as &dyn v::Components])]);
  numeq!(r, m3.get(0,0), 1.1_f32);
  numeq!(r, m3.get(0,1), 1.2_f32);
  numeq!(r, m3.get(1,0), 2.1_f32);
  numeq!(r, m3.get(1,1), 2.2_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:135
pub fn math_matrix_types__AddOperator()->Report{let mut r=Report::default();
let mut m3 = m::M::<f32,3,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(1.1_f32) as &dyn v::Components, &(1.2_f32) as &dyn v::Components, &(1.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(2.1_f32) as &dyn v::Components, &(2.2_f32) as &dyn v::Components, &(2.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(3.1_f32) as &dyn v::Components, &(3.2_f32) as &dyn v::Components, &(3.3_f32) as &dyn v::Components])) as &dyn v::Components])]);

  m3 = m3 + m::M::<f32,3,3>::diagonal((2) as f64);
  numeq!(r, m3.get(0,0), 3.1_f32);
  numeq!(r, m3.get(0,2), 1.3_f32);
  numeq!(r, m3.get(2,0), 3.1_f32);
  numeq!(r, m3.get(2,2), 5.3_f32);

  m3 += m::M::<f32,3,3>::diagonal((-1.0_f32) as f64);
  numeq!(r, m3.get(0,0), 2.1_f32);
  numeq!(r, m3.get(0,2), 1.3_f32);
  numeq!(r, m3.get(2,0), 3.1_f32);
  numeq!(r, m3.get(2,2), 4.3_f32);

  m3 += 1.0_f32;
  numeq!(r, m3.get(0,0), 3.1_f32);
  numeq!(r, m3.get(0,2), 2.3_f32);
  numeq!(r, m3.get(2,0), 4.1_f32);
  numeq!(r, m3.get(2,2), 5.3_f32);

  m3 = m3 + 1.0_f32;
  numeq!(r, m3.get(0,0), 4.1_f32);
  numeq!(r, m3.get(0,2), 3.3_f32);
  numeq!(r, m3.get(2,0), 5.1_f32);
  numeq!(r, m3.get(2,2), 6.3_f32);

  m3 = 1.0_f32 + m3;
  numeq!(r, m3.get(0,0), 5.1_f32);
  numeq!(r, m3.get(0,2), 4.3_f32);
  numeq!(r, m3.get(2,0), 6.1_f32);
  numeq!(r, m3.get(2,2), 7.3_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:170
pub fn math_matrix_types__SubtractOperator()->Report{let mut r=Report::default();
let mut m3 = m::M::<f32,3,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(10.0_f32) as &dyn v::Components, &(10.2_f32) as &dyn v::Components, &(10.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(20.1_f32) as &dyn v::Components, &(20.2_f32) as &dyn v::Components, &(20.3_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(30.1_f32) as &dyn v::Components, &(30.2_f32) as &dyn v::Components, &(30.3_f32) as &dyn v::Components])) as &dyn v::Components])]);

  m3 = m3 - m::M::<f32,3,3>::diagonal((2) as f64);
  numeq!(r, m3.get(0,0), 8.0_f32);
  numeq!(r, m3.get(0,2), 10.3_f32);
  numeq!(r, m3.get(2,0), 30.1_f32);
  numeq!(r, m3.get(2,2), 28.3_f32);

  m3 -= m::M::<f32,3,3>::diagonal((-1.0_f32) as f64);
  numeq!(r, m3.get(0,0), 9.0_f32);
  numeq!(r, m3.get(0,2), 10.3_f32);
  numeq!(r, m3.get(2,0), 30.1_f32);
  numeq!(r, m3.get(2,2), 29.3_f32);

  m3 -= 1.0_f32;
  numeq!(r, m3.get(0,0), 8.0_f32);
  numeq!(r, m3.get(0,2), 9.3_f32);
  numeq!(r, m3.get(2,0), 29.1_f32);
  numeq!(r, m3.get(2,2), 28.3_f32);

  m3 = m3 - 1.0_f32;
  numeq!(r, m3.get(0,0), 7.0_f32);
  numeq!(r, m3.get(0,2), 8.3_f32);
  numeq!(r, m3.get(2,0), 28.1_f32);
  numeq!(r, m3.get(2,2), 27.3_f32);

  m3 = 1.0_f32 - m3;
  numeq!(r, m3.get(0,0), -6.0_f32);
  numeq!(r, m3.get(0,2), -7.3_f32);
  numeq!(r, m3.get(2,0), -27.1_f32);
  numeq!(r, m3.get(2,2), -26.3_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:205
pub fn math_matrix_types__MultiplyOperator()->Report{let mut r=Report::default();
let mut m3 = m::M::<f32,3,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(1.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(2.0_f32) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(2.0_f32) as &dyn v::Components])) as &dyn v::Components])]);

  m3 = m3 * 2;
  numeq!(r, m3.get(0,0), 2.0_f32);
  numeq!(r, m3.get(2,2), 4.0_f32);

  m3 = 2 * m3;
  numeq!(r, m3.get(0,0), 4.0_f32);
  numeq!(r, m3.get(2,2), 8.0_f32);

  m3 *= 2;
  numeq!(r, m3.get(0,0), 8.0_f32);
  numeq!(r, m3.get(2,2), 16.0_f32);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:222
pub fn math_matrix_types__MatrixMultiplyOperator()->Report{let mut r=Report::default();
let mut a = m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components])]);
  let mut b = m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components])]);

  let mut result = a * b;
  numeq!(r, result.get(0,0), 23);
  numeq!(r, result.get(0,1), 34);
  numeq!(r, result.get(1,0), 31);
  numeq!(r, result.get(1,1), 46);

  result = a;
  result *= b;
  numeq!(r, result.get(0,0), 23);
  numeq!(r, result.get(0,1), 34);
  numeq!(r, result.get(1,0), 31);
  numeq!(r, result.get(1,1), 46);

                                 
  let mut result2 = m::M::<f32,4,4>::diagonal((2) as f64) * m::M::<f32,4,4>::diagonal((6) as f64);
  eq!(r, result2, m::M::<f32,4,4>::diagonal((12) as f64));

  let mut result3 = m::M::<f32,3,3>::diagonal((2) as f64) * m::M::<f32,3,3>::diagonal((6) as f64);
  eq!(r, result3, m::M::<f32,3,3>::diagonal((12) as f64));

                            
  let mut a4 = m::M::<f32,3,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components])) as &dyn v::Components])]);
  let mut b4 = m::M::<f32,2,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(11) as &dyn v::Components, &(7) as &dyn v::Components, &(5) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(13) as &dyn v::Components, &(11) as &dyn v::Components, &(17) as &dyn v::Components])) as &dyn v::Components])]);

  let mut expect4 = m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(57) as &dyn v::Components, &(80) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(131) as &dyn v::Components, &(172) as &dyn v::Components])) as &dyn v::Components])]);

  let mut result4 = a4 * b4;
  numeq!(r, result4.get(0,0), expect4.get(0,0));
  numeq!(r, result4.get(0,1), expect4.get(0,1));
  numeq!(r, result4.get(1,0), expect4.get(1,0));
  numeq!(r, result4.get(1,1), expect4.get(1,1));

  let mut a5 = m::M::<f32,3,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(3) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components])) as &dyn v::Components])]);
  let mut b5 = m::M::<f32,2,3>::from_cols([v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(11) as &dyn v::Components, &(7) as &dyn v::Components, &(5) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,3>(&[&(v::construct::<f32,3>(&[&(13) as &dyn v::Components, &(11) as &dyn v::Components, &(17) as &dyn v::Components])) as &dyn v::Components])]);

  let mut expect5 = m::M::<f32,2,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(57) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(131) as &dyn v::Components])) as &dyn v::Components])]);

  let mut result5 = a5 * b5;
  numeq!(r, result5.get(0,0), expect5.get(0,0));
  numeq!(r, result5.get(0,1), expect5.get(0,1));
  numeq!(r, result5.get(0,2), expect5.get(0,2));
  numeq!(r, result5.get(0,3), expect5.get(0,3));
  numeq!(r, result5.get(1,0), expect5.get(1,0));
  numeq!(r, result5.get(1,1), expect5.get(1,1));
  numeq!(r, result5.get(1,2), expect5.get(1,2));
  numeq!(r, result5.get(1,3), expect5.get(1,3));
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:275
pub fn math_matrix_types__VectorMultiplyOperator()->Report{let mut r=Report::default();
let mut mat = m::M::<f32,3,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components])) as &dyn v::Components])]);

  let result=mat * v::construct::<f32,3>(&[&(7) as &dyn v::Components, &(8) as &dyn v::Components, &(9) as &dyn v::Components]);
  numeq!(r, result[0], 76);
  numeq!(r, result[1], 100);

  let result2=v::construct::<f32,2>(&[&(2) as &dyn v::Components, &(3) as &dyn v::Components]) * mat;
  numeq!(r, result2[0], 8);
  numeq!(r, result2[1], 18);
  numeq!(r, result2[2], 28);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:289
pub fn math_matrix_types__ViewConstructor()->Report{let mut r=Report::default();
let mut mat = m::Shared::new(m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components, &(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(10) as &dyn v::Components, &(11) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]));

  let view = mat.view::<2,2>(1,1);
  numeq!(r, view.get(0,0), 6);
  numeq!(r, view.get(0,1), 7);
  numeq!(r, view.get(1,0), 10);
  numeq!(r, view.get(1,1), 11);

  let mut center = m::M::<f32,2,2>::from_matrix(&view.read());
  numeq!(r, center.get(0,0), 6);
  numeq!(r, center.get(0,1), 7);
  numeq!(r, center.get(1,0), 10);
  numeq!(r, center.get(1,1), 11);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:307
pub fn math_matrix_types__ViewFromCstyleMatrix()->Report{let mut r=Report::default();
let c_style_mat=m::cell_storage([[1.0_f32,2.0,3.0,4.0],[5.0,6.0,7.0,8.0],[9.0,10.0,11.0,12.0],[13.0,14.0,15.0,16.0]]);
  let c_mat_view=m::ReadView::<f32,4,4,4,4>::new(&c_style_mat,0,0);

  let c_mat_mutable_view=m::View::<f32,4,4,4,4>::new(&c_style_mat,0,0);

  let mut expect = m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(2) as &dyn v::Components, &(4) as &dyn v::Components, &(6) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(10) as &dyn v::Components, &(12) as &dyn v::Components, &(14) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(18) as &dyn v::Components, &(20) as &dyn v::Components, &(22) as &dyn v::Components, &(24) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(26) as &dyn v::Components, &(28) as &dyn v::Components, &(30) as &dyn v::Components, &(32) as &dyn v::Components])) as &dyn v::Components])]);

  let mut mat = m::M::<f32,4,4>::diagonal((2.0_f32) as f64) * c_mat_view.read();
  {near!(r, expect.get(0,0),mat.get(0,0),1e-8_f32);near!(r, expect.get(0,1),mat.get(0,1),1e-8_f32);near!(r, expect.get(0,2),mat.get(0,2),1e-8_f32);near!(r, expect.get(0,3),mat.get(0,3),1e-8_f32);near!(r, expect.get(1,0),mat.get(1,0),1e-8_f32);near!(r, expect.get(1,1),mat.get(1,1),1e-8_f32);near!(r, expect.get(1,2),mat.get(1,2),1e-8_f32);near!(r, expect.get(1,3),mat.get(1,3),1e-8_f32);near!(r, expect.get(2,0),mat.get(2,0),1e-8_f32);near!(r, expect.get(2,1),mat.get(2,1),1e-8_f32);near!(r, expect.get(2,2),mat.get(2,2),1e-8_f32);near!(r, expect.get(2,3),mat.get(2,3),1e-8_f32);near!(r, expect.get(3,0),mat.get(3,0),1e-8_f32);near!(r, expect.get(3,1),mat.get(3,1),1e-8_f32);near!(r, expect.get(3,2),mat.get(3,2),1e-8_f32);near!(r, expect.get(3,3),mat.get(3,3),1e-8_f32);};
c_mat_mutable_view.assign(c_mat_mutable_view.read() * (m::M::<f32,4,4>::diagonal((2.0_f32) as f64)));
  {near!(r, expect.get(0,0),c_mat_mutable_view.get(0,0),1e-8_f32);near!(r, expect.get(0,1),c_mat_mutable_view.get(0,1),1e-8_f32);near!(r, expect.get(0,2),c_mat_mutable_view.get(0,2),1e-8_f32);near!(r, expect.get(0,3),c_mat_mutable_view.get(0,3),1e-8_f32);near!(r, expect.get(1,0),c_mat_mutable_view.get(1,0),1e-8_f32);near!(r, expect.get(1,1),c_mat_mutable_view.get(1,1),1e-8_f32);near!(r, expect.get(1,2),c_mat_mutable_view.get(1,2),1e-8_f32);near!(r, expect.get(1,3),c_mat_mutable_view.get(1,3),1e-8_f32);near!(r, expect.get(2,0),c_mat_mutable_view.get(2,0),1e-8_f32);near!(r, expect.get(2,1),c_mat_mutable_view.get(2,1),1e-8_f32);near!(r, expect.get(2,2),c_mat_mutable_view.get(2,2),1e-8_f32);near!(r, expect.get(2,3),c_mat_mutable_view.get(2,3),1e-8_f32);near!(r, expect.get(3,0),c_mat_mutable_view.get(3,0),1e-8_f32);near!(r, expect.get(3,1),c_mat_mutable_view.get(3,1),1e-8_f32);near!(r, expect.get(3,2),c_mat_mutable_view.get(3,2),1e-8_f32);near!(r, expect.get(3,3),c_mat_mutable_view.get(3,3),1e-8_f32);};
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:323
pub fn math_matrix_types__ViewAssignment()->Report{let mut r=Report::default();
let mut mat = m::Shared::new(m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components, &(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(10) as &dyn v::Components, &(11) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]));
mat.view::<2,2>(1,1).assign(m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(-1) as &dyn v::Components, &(-2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(-3) as &dyn v::Components, &(-4) as &dyn v::Components])) as &dyn v::Components])]));

  let mut expect = m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(-1) as &dyn v::Components, &(-2) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(-3) as &dyn v::Components, &(-4) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]);
  {near!(r, expect.get(0,0),mat.get(0,0),1e-8_f32);near!(r, expect.get(0,1),mat.get(0,1),1e-8_f32);near!(r, expect.get(0,2),mat.get(0,2),1e-8_f32);near!(r, expect.get(0,3),mat.get(0,3),1e-8_f32);near!(r, expect.get(1,0),mat.get(1,0),1e-8_f32);near!(r, expect.get(1,1),mat.get(1,1),1e-8_f32);near!(r, expect.get(1,2),mat.get(1,2),1e-8_f32);near!(r, expect.get(1,3),mat.get(1,3),1e-8_f32);near!(r, expect.get(2,0),mat.get(2,0),1e-8_f32);near!(r, expect.get(2,1),mat.get(2,1),1e-8_f32);near!(r, expect.get(2,2),mat.get(2,2),1e-8_f32);near!(r, expect.get(2,3),mat.get(2,3),1e-8_f32);near!(r, expect.get(3,0),mat.get(3,0),1e-8_f32);near!(r, expect.get(3,1),mat.get(3,1),1e-8_f32);near!(r, expect.get(3,2),mat.get(3,2),1e-8_f32);near!(r, expect.get(3,3),mat.get(3,3),1e-8_f32);};
mat.view::<2,2>(2,2).assign(mat.view::<2,2>(0,0).read());
  let mut expect2 = m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(-1) as &dyn v::Components, &(-2) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(-3) as &dyn v::Components, &(1) as &dyn v::Components, &(2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(5) as &dyn v::Components, &(-1) as &dyn v::Components])) as &dyn v::Components])]);
  {near!(r, expect2.get(0,0),mat.get(0,0),1e-8_f32);near!(r, expect2.get(0,1),mat.get(0,1),1e-8_f32);near!(r, expect2.get(0,2),mat.get(0,2),1e-8_f32);near!(r, expect2.get(0,3),mat.get(0,3),1e-8_f32);near!(r, expect2.get(1,0),mat.get(1,0),1e-8_f32);near!(r, expect2.get(1,1),mat.get(1,1),1e-8_f32);near!(r, expect2.get(1,2),mat.get(1,2),1e-8_f32);near!(r, expect2.get(1,3),mat.get(1,3),1e-8_f32);near!(r, expect2.get(2,0),mat.get(2,0),1e-8_f32);near!(r, expect2.get(2,1),mat.get(2,1),1e-8_f32);near!(r, expect2.get(2,2),mat.get(2,2),1e-8_f32);near!(r, expect2.get(2,3),mat.get(2,3),1e-8_f32);near!(r, expect2.get(3,0),mat.get(3,0),1e-8_f32);near!(r, expect2.get(3,1),mat.get(3,1),1e-8_f32);near!(r, expect2.get(3,2),mat.get(3,2),1e-8_f32);near!(r, expect2.get(3,3),mat.get(3,3),1e-8_f32);};
mat.view::<2,2>(0,0).assign(mat.view::<2,2>(1,1).read());
  let mut expect3 = m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(-1) as &dyn v::Components, &(-2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(-3) as &dyn v::Components, &(1) as &dyn v::Components, &(-2) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(-3) as &dyn v::Components, &(1) as &dyn v::Components, &(2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(5) as &dyn v::Components, &(-1) as &dyn v::Components])) as &dyn v::Components])]);
  {near!(r, expect3.get(0,0),mat.get(0,0),1e-8_f32);near!(r, expect3.get(0,1),mat.get(0,1),1e-8_f32);near!(r, expect3.get(0,2),mat.get(0,2),1e-8_f32);near!(r, expect3.get(0,3),mat.get(0,3),1e-8_f32);near!(r, expect3.get(1,0),mat.get(1,0),1e-8_f32);near!(r, expect3.get(1,1),mat.get(1,1),1e-8_f32);near!(r, expect3.get(1,2),mat.get(1,2),1e-8_f32);near!(r, expect3.get(1,3),mat.get(1,3),1e-8_f32);near!(r, expect3.get(2,0),mat.get(2,0),1e-8_f32);near!(r, expect3.get(2,1),mat.get(2,1),1e-8_f32);near!(r, expect3.get(2,2),mat.get(2,2),1e-8_f32);near!(r, expect3.get(2,3),mat.get(2,3),1e-8_f32);near!(r, expect3.get(3,0),mat.get(3,0),1e-8_f32);near!(r, expect3.get(3,1),mat.get(3,1),1e-8_f32);near!(r, expect3.get(3,2),mat.get(3,2),1e-8_f32);near!(r, expect3.get(3,3),mat.get(3,3),1e-8_f32);};
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:350
pub fn math_matrix_types__ViewScalarOperators()->Report{let mut r=Report::default();
let mut mat = m::Shared::new(m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components, &(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(10) as &dyn v::Components, &(11) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]));

  let view = mat.view::<2,2>(1,1);
  numeq!(r, view.get(0,0), 6);
  numeq!(r, view.get(0,1), 7);
  numeq!(r, view.get(1,0), 10);
  numeq!(r, view.get(1,1), 11);
view.assign(view.read() + (1));
  numeq!(r, view.get(0,0), 7);
  numeq!(r, view.get(0,1), 8);
  numeq!(r, view.get(1,0), 11);
  numeq!(r, view.get(1,1), 12);
view.assign(view.read() - (2));
  numeq!(r, view.get(0,0), 5);
  numeq!(r, view.get(0,1), 6);
  numeq!(r, view.get(1,0), 9);
  numeq!(r, view.get(1,1), 10);
view.assign(view.read() * (4));
  numeq!(r, view.get(0,0), 20);
  numeq!(r, view.get(0,1), 24);
  numeq!(r, view.get(1,0), 36);
  numeq!(r, view.get(1,1), 40);

                                                                         
  let mut expect = m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(20) as &dyn v::Components, &(24) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(36) as &dyn v::Components, &(40) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]);
  {near!(r, expect.get(0,0),mat.get(0,0),1e-8_f32);near!(r, expect.get(0,1),mat.get(0,1),1e-8_f32);near!(r, expect.get(0,2),mat.get(0,2),1e-8_f32);near!(r, expect.get(0,3),mat.get(0,3),1e-8_f32);near!(r, expect.get(1,0),mat.get(1,0),1e-8_f32);near!(r, expect.get(1,1),mat.get(1,1),1e-8_f32);near!(r, expect.get(1,2),mat.get(1,2),1e-8_f32);near!(r, expect.get(1,3),mat.get(1,3),1e-8_f32);near!(r, expect.get(2,0),mat.get(2,0),1e-8_f32);near!(r, expect.get(2,1),mat.get(2,1),1e-8_f32);near!(r, expect.get(2,2),mat.get(2,2),1e-8_f32);near!(r, expect.get(2,3),mat.get(2,3),1e-8_f32);near!(r, expect.get(3,0),mat.get(3,0),1e-8_f32);near!(r, expect.get(3,1),mat.get(3,1),1e-8_f32);near!(r, expect.get(3,2),mat.get(3,2),1e-8_f32);near!(r, expect.get(3,3),mat.get(3,3),1e-8_f32);};
view.assign(-view.read());
  numeq!(r, view.get(0,0), -20);
  numeq!(r, view.get(0,1), -24);
  numeq!(r, view.get(1,0), -36);
  numeq!(r, view.get(1,1), -40);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:389
pub fn math_matrix_types__ViewMatrixMultiplyOperator()->Report{let mut r=Report::default();
let mut mat = m::Shared::new(m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components, &(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(10) as &dyn v::Components, &(11) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]));
  let view = mat.view::<2,2>(1,1);
view.assign(m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components])]));

  let mut result = view.read() * m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components])]);
  numeq!(r, result.get(0,0), 23);
  numeq!(r, result.get(0,1), 34);
  numeq!(r, result.get(1,0), 31);
  numeq!(r, result.get(1,1), 46);
view.assign(view.read() * (m::M::<f32,2,2>::from_cols([v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,2>(&[&(v::construct::<f32,2>(&[&(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components])])));
  numeq!(r, view.get(0,0), 23);
  numeq!(r, view.get(0,1), 34);
  numeq!(r, view.get(1,0), 31);
  numeq!(r, view.get(1,1), 46);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:408
pub fn math_matrix_types__ViewVectorMultiplyOperator()->Report{let mut r=Report::default();
let mut mat = m::Shared::new(m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components, &(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(10) as &dyn v::Components, &(11) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]));
  let view = mat.view::<2,3>(1,1);

  let result=view.read() * v::construct::<f32,2>(&[&(4) as &dyn v::Components, &(5) as &dyn v::Components]);
  numeq!(r, result[0], 74);
  numeq!(r, result[1], 83);
  numeq!(r, result[2], 92);

  let result2=v::construct::<f32,3>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components]) * view.read();
  numeq!(r, result2[0], 44);
  numeq!(r, result2[1], 68);
r
}

// source/blender/blenlib/tests/BLI_math_matrix_types_test.cc:423
pub fn math_matrix_types__ViewMatrixNormalize()->Report{let mut r=Report::default();
let mut mat = m::Shared::new(m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(1) as &dyn v::Components, &(2) as &dyn v::Components, &(3) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(5) as &dyn v::Components, &(6) as &dyn v::Components, &(7) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(9) as &dyn v::Components, &(10) as &dyn v::Components, &(11) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]));
mat.view::<3,3>(0,0).assign(m::normalize(mat.view::<3,3>(0,0).read()));

  let mut expect = m::M::<f32,4,4>::from_cols([v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(0.267261236) as &dyn v::Components, &(0.534522473) as &dyn v::Components, &(0.80178368) as &dyn v::Components, &(4) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(0.476731300) as &dyn v::Components, &(0.572077572) as &dyn v::Components, &(0.66742378) as &dyn v::Components, &(8) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(0.517891824) as &dyn v::Components, &(0.575435340) as &dyn v::Components, &(0.63297885) as &dyn v::Components, &(12) as &dyn v::Components])) as &dyn v::Components]), v::construct::<f32,4>(&[&(v::construct::<f32,4>(&[&(13) as &dyn v::Components, &(14) as &dyn v::Components, &(15) as &dyn v::Components, &(16) as &dyn v::Components])) as &dyn v::Components])]);
  {near!(r, expect.get(0,0),mat.get(0,0),1e-8_f32);near!(r, expect.get(0,1),mat.get(0,1),1e-8_f32);near!(r, expect.get(0,2),mat.get(0,2),1e-8_f32);near!(r, expect.get(0,3),mat.get(0,3),1e-8_f32);near!(r, expect.get(1,0),mat.get(1,0),1e-8_f32);near!(r, expect.get(1,1),mat.get(1,1),1e-8_f32);near!(r, expect.get(1,2),mat.get(1,2),1e-8_f32);near!(r, expect.get(1,3),mat.get(1,3),1e-8_f32);near!(r, expect.get(2,0),mat.get(2,0),1e-8_f32);near!(r, expect.get(2,1),mat.get(2,1),1e-8_f32);near!(r, expect.get(2,2),mat.get(2,2),1e-8_f32);near!(r, expect.get(2,3),mat.get(2,3),1e-8_f32);near!(r, expect.get(3,0),mat.get(3,0),1e-8_f32);near!(r, expect.get(3,1),mat.get(3,1),1e-8_f32);near!(r, expect.get(3,2),mat.get(3,2),1e-8_f32);near!(r, expect.get(3,3),mat.get(3,3),1e-8_f32);};
r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("math_matrix_types.DefaultConstructor",math_matrix_types__DefaultConstructor,4),
("math_matrix_types.StaticConstructor",math_matrix_types__StaticConstructor,16),
("math_matrix_types.VectorConstructor",math_matrix_types__VectorConstructor,6),
("math_matrix_types.SmallerMatrixConstructor",math_matrix_types__SmallerMatrixConstructor,9),
("math_matrix_types.ComponentMasking",math_matrix_types__ComponentMasking,4),
("math_matrix_types.PointerConversion",math_matrix_types__PointerConversion,4),
("math_matrix_types.TypeConversion",math_matrix_types__TypeConversion,12),
("math_matrix_types.PointerArrayConversion",math_matrix_types__PointerArrayConversion,4),
("math_matrix_types.ComponentAccess",math_matrix_types__ComponentAccess,4),
("math_matrix_types.AddOperator",math_matrix_types__AddOperator,20),
("math_matrix_types.SubtractOperator",math_matrix_types__SubtractOperator,20),
("math_matrix_types.MultiplyOperator",math_matrix_types__MultiplyOperator,6),
("math_matrix_types.MatrixMultiplyOperator",math_matrix_types__MatrixMultiplyOperator,22),
("math_matrix_types.VectorMultiplyOperator",math_matrix_types__VectorMultiplyOperator,5),
("math_matrix_types.ViewConstructor",math_matrix_types__ViewConstructor,8),
("math_matrix_types.ViewFromCstyleMatrix",math_matrix_types__ViewFromCstyleMatrix,32),
("math_matrix_types.ViewAssignment",math_matrix_types__ViewAssignment,48),
("math_matrix_types.ViewScalarOperators",math_matrix_types__ViewScalarOperators,36),
("math_matrix_types.ViewMatrixMultiplyOperator",math_matrix_types__ViewMatrixMultiplyOperator,8),
("math_matrix_types.ViewVectorMultiplyOperator",math_matrix_types__ViewVectorMultiplyOperator,5),
("math_matrix_types.ViewMatrixNormalize",math_matrix_types__ViewMatrixNormalize,16),
];
