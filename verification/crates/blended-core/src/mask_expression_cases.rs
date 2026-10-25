// SPDX-FileCopyrightText: 2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked adapter; original identities, bodies and helper hashes are in mask-expression-ports.json.
#![allow(non_snake_case,unused_mut)]
use crate::mask_expressions::{IndexMask,ExprBuilder,Expr};
use crate::data_structures::IndexRange;
use crate::priority_heaps::BlenderRng;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
// Tuples are (start, size), exactly like the original IndexRange initializers.
fn mask(ranges:&[(i64,i64)])->IndexMask{IndexMask::from_ranges(ranges.iter().map(|&(start,size)|IndexRange::new(start,size)))}
fn random_bools(rng:&mut BlenderRng,size:usize)->Vec<bool>{
 let mut bools=vec![false;size];let mut i=0;
 while i<size{
  let chunk_size=(size-i).min((rng.get_int32()%5000+1) as usize);
  let chunk_type=rng.get_int32()%4;
  let density=rng.get_int32() as f32/2147483648.0_f32;
  for value in &mut bools[i..i+chunk_size]{
   *value=if chunk_type==0{true}else if chunk_type==1{false}else{rng.get_int32() as f32/2147483648.0_f32<density};
  }
  i+=chunk_size;
 }
 bools
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:18
pub fn index_mask_expression__Union()->Report{let mut report=Report::default();
let mask_a=mask(&[(5,1),(50,100),(100_000,1)]);let mask_b=mask(&[(10,10),(60,1),(200,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_a).into(),(&mask_b).into()]);let union_mask=expr.evaluate();
eq!(report,union_mask,mask(&[(5,1),(10,10),(50,100),(200,1),(100_000,1)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:33
pub fn index_mask_expression__UnionMulti()->Report{let mut report=Report::default();
let mask_a=mask(&[(3,1),(5,1),(6,1),(8,1),(9,1)]);let mask_b=mask(&[(4,1),(6,1),(7,1),(12,1)]);let mask_c=mask(&[(0,1),(5,1)]);let mask_d=mask(&[(6,1),(7,1),(10,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_a).into(),(&mask_b).into(),(&mask_c).into(),(&mask_d).into()]);let union_mask=expr.evaluate();
eq!(report,union_mask,mask(&[(0,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),(10,1),(12,1)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:48
pub fn index_mask_expression__IntersectMulti()->Report{let mut report=Report::default();
let mask_a=mask(&[(3,1),(5,1),(6,1),(8,1),(9,1)]);let mask_b=mask(&[(2,1),(5,1),(6,1),(10,1)]);let mask_c=mask(&[(4,1),(5,1),(6,1)]);let mask_d=mask(&[(1,1),(5,1),(10,1)]);
let builder=ExprBuilder::new();let expr=builder.intersect([(&mask_a).into(),(&mask_b).into(),(&mask_c).into(),(&mask_d).into()]);let intersect_mask=expr.evaluate();
eq!(report,intersect_mask,mask(&[(5,1)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:63
pub fn index_mask_expression__DifferenceMulti()->Report{let mut report=Report::default();
let mask_a=mask(&[(1,1),(2,1),(3,1),(5,1),(6,1),(7,1),(9,1),(10,1)]);let mask_b=mask(&[(2,1),(5,1),(6,1),(10,1)]);let mask_c=mask(&[(4,1),(5,1),(6,1)]);let mask_d=mask(&[(1,1),(5,1),(10,1)]);
let builder=ExprBuilder::new();let expr=builder.subtract((&mask_a).into(),[(&mask_b).into(),(&mask_c).into(),(&mask_d).into()]);let difference_mask=expr.evaluate();
eq!(report,difference_mask,mask(&[(3,1),(7,1),(9,1)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:78
pub fn index_mask_expression__Intersection()->Report{let mut report=Report::default();
let mask_a=mask(&[(5,1),(50,100),(100_000,1)]);let mask_b=mask(&[(5,1),(6,1),(100,100),(80000,1),(100_000,1)]);
let builder=ExprBuilder::new();let expr=builder.intersect([(&mask_a).into(),(&mask_b).into()]);let intersection_mask=expr.evaluate();
eq!(report,intersection_mask,mask(&[(5,1),(100,50),(100_000,1)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:93
pub fn index_mask_expression__Difference()->Report{let mut report=Report::default();
let mask_a=mask(&[(5,1),(50,100),(100_000,1)]);let mask_b=mask(&[(5,1),(60,1),(100,20)]);
let builder=ExprBuilder::new();let expr=builder.subtract((&mask_a).into(),[(&mask_b).into()]);let difference_mask=expr.evaluate();
eq!(report,difference_mask,mask(&[(50,10),(61,39),(120,30),(100_000,1)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:108
pub fn index_mask_expression__FizzBuzz()->Report{let mut report=Report::default();
let mask_3=IndexMask::from_every_nth(3,11,0);let mask_5=IndexMask::from_every_nth(5,11,0);
{let builder=ExprBuilder::new();let expr=builder.merge([(&mask_3).into(),(&mask_5).into()]);let result=expr.evaluate();
eq!(report,result,mask(&[(0,1),(3,1),(5,1),(6,1),(9,1),(10,1),(12,1),(15,1),(18,1),(20,1),(21,1),(24,1),(25,1),(27,1),(30,1),(35,1),(40,1),(45,1),(50,1)]));}
{let builder=ExprBuilder::new();let expr=builder.intersect([(&mask_3).into(),(&mask_5).into()]);let result=expr.evaluate();eq!(report,result,mask(&[(0,1),(15,1),(30,1)]));}
{let builder=ExprBuilder::new();let expr=builder.subtract((&mask_3).into(),[(&mask_5).into()]);let result=expr.evaluate();eq!(report,result,mask(&[(3,1),(6,1),(9,1),(12,1),(18,1),(21,1),(24,1),(27,1)]));}
{let builder=ExprBuilder::new();let expr=builder.merge([builder.intersect([(&mask_3).into(),(&mask_5).into()]),builder.subtract((&mask_3).into(),[(&mask_5).into()])]);let result=expr.evaluate();eq!(report,result,mask(&[(0,1),(3,1),(6,1),(9,1),(12,1),(15,1),(18,1),(21,1),(24,1),(27,1),(30,1)]));}
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:145
pub fn index_mask_expression__UnionToFullRange()->Report{let mut report=Report::default();
let mask_1=mask(&[(2,1),(4,1),(5,1),(7,1)]);let mask_2=mask(&[(6,1),(8,1)]);let mask_3=mask(&[(1,1),(3,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_1).into(),(&mask_2).into(),(&mask_3).into()]);let result=expr.evaluate();
yes!(report,result.to_range().is_some());eq!(report,result.to_range().unwrap(),IndexRange::from_begin_end_inclusive(1,8));eq!(report,result.segments_num(),1);
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:160
pub fn index_mask_expression__UnionIndividualIndices()->Report{let mut report=Report::default();
let mask_1=mask(&[(3,1)]);let mask_2=mask(&[(6,1)]);let mask_3=mask(&[(5,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_1).into(),(&mask_2).into(),(&mask_3).into()]);let result=expr.evaluate();
eq!(report,result,mask(&[(3,1),(5,1),(6,1)]));eq!(report,result.segments_num(),1);
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:174
pub fn index_mask_expression__UnionLargeRanges()->Report{let mut report=Report::default();
let mask_a=IndexMask::from_range(IndexRange::new(0,1_000_000));let mask_b=IndexMask::from_range(IndexRange::new(900_000,1_100_000));
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_a).into(),(&mask_b).into()]);let result_mask=expr.evaluate();
eq!(report,result_mask,IndexMask::from_range(IndexRange::new(0,2_000_000)));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:187
pub fn index_mask_expression__SubtractSmall()->Report{let mut report=Report::default();
let mask_a=mask(&[(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1)]);let mask_b=mask(&[(5,1),(7,1)]);let mask_c=mask(&[(8,1)]);
let builder=ExprBuilder::new();let expr=builder.subtract((&mask_a).into(),[(&mask_b).into(),(&mask_c).into()]);let result=expr.evaluate();
eq!(report,result,mask(&[(3,1),(4,1),(6,1),(9,1)]));eq!(report,result.segments_num(),1);
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:202
pub fn index_mask_expression__RangeTerms()->Report{let mut report=Report::default();
let builder=ExprBuilder::new();let range_a=IndexRange::from_begin_end(30_000,50_000);let range_b=IndexRange::from_begin_end(40_000,100_000);let range_c=IndexRange::from_begin_end(45_000,48_000);
let expr=builder.subtract(builder.merge([range_a.into(),range_b.into()]),[range_c.into()]);let result_mask=expr.evaluate();
eq!(report,result_mask,IndexMask::from_ranges([IndexRange::from_begin_end(30_000,45_000),IndexRange::from_begin_end(48_000,100_000)]));
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:220
pub fn index_mask_expression__SingleMask()->Report{let mut report=Report::default();
let mask=mask(&[(5,1),(6,1),(8,1),(9,1)]);let builder=ExprBuilder::new();let expr=builder.merge([(&mask).into()]);let result=expr.evaluate();eq!(report,result,mask);
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:232
pub fn index_mask_expression__SubtractSelf()->Report{let mut report=Report::default();
let mask=mask(&[(6,1),(8,1),(10,1),(100,1)]);let builder=ExprBuilder::new();let expr=builder.subtract((&mask).into(),[(&mask).into()]);let result=expr.evaluate();yes!(report,result.is_empty());
report
}

// source/blender/blenlib/tests/BLI_index_mask_expression_test.cc:264
pub fn index_mask_expression__Fuzzy()->Report{let mut report=Report::default();
let mut rng=BlenderRng::new(0);
for _iteration in 0..50{
 let size=(rng.get_int32()%200_000+1) as usize;
 let a_bools=random_bools(&mut rng,size);let b_bools=random_bools(&mut rng,size);let c_bools=random_bools(&mut rng,size);
 let a=IndexMask::from_bools(&a_bools);let b=IndexMask::from_bools(&b_bools);let c=IndexMask::from_bools(&c_bools);let universe=IndexRange::from_size(size as i64);
 let expected=|predicate:&dyn Fn(usize)->bool|IndexMask::from_predicate(universe,|i|predicate(i as usize));
 eq!(report,a.complement_range(universe),expected(&|i|!a_bools[i]));
 eq!(report,a.complement(&b),expected(&|i|b_bools[i]&&!a_bools[i]));
 {let builder=ExprBuilder::new();eq!(report,builder.merge([(&a).into(),(&b).into(),(&c).into()]).evaluate(),expected(&|i|a_bools[i]||b_bools[i]||c_bools[i]));}
 {let builder=ExprBuilder::new();eq!(report,builder.intersect([(&a).into(),(&b).into()]).evaluate(),expected(&|i|a_bools[i]&&b_bools[i]));}
 {let builder=ExprBuilder::new();eq!(report,builder.subtract((&a).into(),[(&b).into(),(&c).into()]).evaluate(),expected(&|i|a_bools[i]&&!b_bools[i]&&!c_bools[i]));}
 {let builder=ExprBuilder::new();eq!(report,builder.subtract(builder.merge([(&a).into(),(&b).into()]),[builder.intersect([(&b).into(),(&c).into()])]).evaluate(),expected(&|i|(a_bools[i]||b_bools[i])&&!(b_bools[i]&&c_bools[i])));}
}
report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("index_mask_expression.Union",index_mask_expression__Union,1),
("index_mask_expression.UnionMulti",index_mask_expression__UnionMulti,1),
("index_mask_expression.IntersectMulti",index_mask_expression__IntersectMulti,1),
("index_mask_expression.DifferenceMulti",index_mask_expression__DifferenceMulti,1),
("index_mask_expression.Intersection",index_mask_expression__Intersection,1),
("index_mask_expression.Difference",index_mask_expression__Difference,1),
("index_mask_expression.FizzBuzz",index_mask_expression__FizzBuzz,4),
("index_mask_expression.UnionToFullRange",index_mask_expression__UnionToFullRange,3),
("index_mask_expression.UnionIndividualIndices",index_mask_expression__UnionIndividualIndices,2),
("index_mask_expression.UnionLargeRanges",index_mask_expression__UnionLargeRanges,1),
("index_mask_expression.SubtractSmall",index_mask_expression__SubtractSmall,2),
("index_mask_expression.RangeTerms",index_mask_expression__RangeTerms,1),
("index_mask_expression.SingleMask",index_mask_expression__SingleMask,1),
("index_mask_expression.SubtractSelf",index_mask_expression__SubtractSelf,1),
("index_mask_expression.Fuzzy",index_mask_expression__Fuzzy,300),
];
