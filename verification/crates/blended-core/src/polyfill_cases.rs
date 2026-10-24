// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Original helper assertions and source-locked input polygons.
// See compatibility/polyfill-ports.json for observable combination-loop behaviour.
#![allow(non_snake_case,unused_mut)]
use crate::polyfill as p;
use std::collections::BTreeMap;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,passed:bool,expression:&str,line:u32){self.assertions+=1;if !passed{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! ne {($r:expr,$a:expr,$b:expr)=>{{$r.check($a!=$b,stringify!($a != $b),line!());}};}
macro_rules! yes {($r:expr,$v:expr)=>{{$r.check($v,stringify!($v),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b),line!());}};}

// Original test helper maths remain separate from the production implementation.
fn cross(a:[f32;2],b:[f32;2],c:[f32;2])->f32{(a[0]-b[0])*(b[1]-c[1])+(a[1]-b[1])*(c[0]-b[0])}
fn triangle_area(a:[f32;2],b:[f32;2],c:[f32;2])->f32{(0.5_f32*cross(a,b,c)).abs()}
fn polygon_area(poly:&[[f32;2]])->f32{
 let mut last=poly[poly.len()-1];let mut value=0.0_f32;
 for &co in poly{value+=(last[0]-co[0])*(co[1]+last[1]);last=co;}
 (0.5_f32*value).abs()
}
fn simple(report:&mut Report,poly_num:usize,tris:&[[u32;3]]){
 let mut used=vec![0_i32;poly_num];
 for tri in tris{
  for j in 0..3{ne!(report,u32::MAX,tri[j]);used[tri[j] as usize]+=1;}
  ne!(report,tri[0],tri[1]);ne!(report,tri[1],tri[2]);ne!(report,tri[2],tri[0]);
 }
 for i in 0..poly_num{ne!(report,0_i32,used[i]);}
}
fn edge(a:u32,b:u32)->(u32,u32){if a<b{(a,b)}else{(b,a)}}
fn topology(report:&mut Report,poly_num:usize,tris:&[[u32;3]]){
 let mut edges:BTreeMap<(u32,u32),i32>=BTreeMap::new();
 for tri in tris{for j in 0..3{*edges.entry(edge(tri[j],tri[(j+1)%3])).or_insert(0)+=1;}}
 eq!(report,edges.len() as u32,(poly_num+poly_num-3) as u32);
 for i in 0..poly_num{let key=edge(i as u32,((i+1)%poly_num) as u32);yes!(report,edges.contains_key(&key));eq!(report,*edges.get(&key).expect("Original topology lookup precondition"),1_i32);}
 // Original Map iteration order is unspecified here. Only its Boolean predicate
 // is asserted, so sorted-map iteration preserves every observable assertion.
 for &value in edges.values(){yes!(report,value==1||value==2);}
}
fn winding(report:&mut Report,poly:&[[f32;2]],tris:&[[u32;3]]){
 let mut count=[0_u32;2];
 for t in tris{let w=cross(poly[t[0] as usize],poly[t[1] as usize],poly[t[2] as usize]);if w.abs()>f32::EPSILON{count[usize::from(w<0.0)]+=1;}}
 yes!(report,count[0]==0||count[1]==0);
}
fn area(report:&mut Report,poly:&[[f32;2]],tris:&[[u32;3]]){
 let expected=polygon_area(poly);let mut actual=0.0_f32;let eps_abs=0.00001_f32;let eps=if expected>1.0{expected*eps_abs}else{eps_abs};
 for t in tris{actual+=triangle_area(poly[t[0] as usize],poly[t[1] as usize],poly[t[2] as usize]);}
 near!(report,expected,actual,eps);
}
fn nonzero(report:&mut Report,poly:&[[f32;2]],tris:&[[u32;3]]){
 let mut total=0_u32;
 for t in tris{if triangle_area(poly[t[0] as usize],poly[t[1] as usize],poly[t[2] as usize])<1e-6_f32{total+=1;}}
 eq!(report,total,0_u32);
}
fn check(report:&mut Report,flag:u32,poly:&[[f32;2]],tris:&[[u32;3]]){
 simple(report,poly.len(),tris);topology(report,poly.len(),tris);
 if flag&1==0{winding(report,poly,tris);area(report,poly,tris);if flag&2!=0{nonzero(report,poly,tris);}}
 // USE_OBJ_PREVIEW is disabled in the pinned source: its helper is a no-op.
}
fn template(report:&mut Report,flag:u32,poly:&[[f32;2]],tris:&mut [[u32;3]]){
 for tri in tris.iter_mut(){*tri=[u32::MAX;3];}
 p::triangulate_into(poly,0,tris);
 check(report,flag,poly,tris);
 p::beautify(poly,tris);
 check(report,flag,poly,tris);
}
fn flip_sign(report:&mut Report,flag:u32,poly:&[[f32;2]],tris:&mut [[u32;3]]){
 let mut copy=vec![[0.0_f32;2];poly.len()];
 for flip_x in 0..2{for flip_y in 0..2{
  let sx=if flip_x!=0{-1.0_f32}else{1.0_f32};let sy=if flip_y!=0{-1.0_f32}else{1.0_f32};
  for i in 0..poly.len(){copy[i]=[poly[i][0]*sx,poly[i][1]*sy];}
  template(report,flag,&copy,tris);
 }}
}
fn run_original(report:&mut Report,flag:u32,poly:&[[f32;2]]){
 let mut copy=poly.to_vec();let mut tris=vec![[u32::MAX;3];poly.len()-2];
 for reversed in 0..2{
  if reversed!=0{copy.reverse();}
  for _cycle in 0..poly.len(){
   // Deliberately passes poly, not copy, exactly like the pinned original helper.
   flip_sign(report,flag,poly,&mut tris);
   copy.rotate_left(1);
  }
 }
}

/// Source-locked input data, not expectations produced by the triangulator.
pub fn fixture(name:&str)->Vec<[f32;2]>{
 const SOURCE:&str=include_str!("polyfill_fixture.cc");
 let marker=format!("TEST(polyfill2d, {name})");
 let body=SOURCE.split_once(&marker).expect("Unknown original case").1;
 let values=body.split_once("const float poly[][2] = {").expect("Original fixture declaration").1.split_once("};").expect("Original fixture terminator").0;
 let numbers=values.split(|c:char|c==','||c=='{'||c=='}'||c.is_ascii_whitespace()).filter(|s|!s.is_empty()).map(|s|s.strip_suffix('f').unwrap_or(s).parse::<f32>().expect("Source-locked numeric literal")).collect::<Vec<_>>();
 assert_eq!(numbers.len()%2,0);numbers.chunks_exact(2).map(|v|[v[0],v[1]]).collect()
}

macro_rules! original_case {($f:ident,$name:literal,$flag:expr)=>{pub fn $f()->Report{let mut r=Report::default();let poly=fixture($name);run_original(&mut r,$flag,&poly);r}};}
original_case!(polyfill2d__TriangleCCW,"TriangleCCW",0);
original_case!(polyfill2d__SquareCCW,"SquareCCW",0);
original_case!(polyfill2d__SquareCW,"SquareCW",0);
original_case!(polyfill2d__Starfleet,"Starfleet",0);
original_case!(polyfill2d__StarfleetDegenerate,"StarfleetDegenerate",0);
original_case!(polyfill2d__3Colinear,"3Colinear",0);
original_case!(polyfill2d__4Colinear,"4Colinear",0);
original_case!(polyfill2d__UnorderedColinear,"UnorderedColinear",0);
original_case!(polyfill2d__PlusShape,"PlusShape",0);
original_case!(polyfill2d__StarShape,"StarShape",0);
original_case!(polyfill2d__UShape,"UShape",0);
original_case!(polyfill2d__Spiral,"Spiral",0);
original_case!(polyfill2d__TestFlipCode,"TestFlipCode",0);
original_case!(polyfill2d__SelfIntersect,"SelfIntersect",1);
original_case!(polyfill2d__SelfTouch,"SelfTouch",0);
original_case!(polyfill2d__SelfOverlap,"SelfOverlap",1);
original_case!(polyfill2d__TestDavData,"TestDavData",0);
original_case!(polyfill2d__Issue815,"Issue815",0);
original_case!(polyfill2d__Issue207_1,"Issue207_1",1);
original_case!(polyfill2d__Issue207_11,"Issue207_11",0);
original_case!(polyfill2d__Issue1407,"Issue1407",0);
original_case!(polyfill2d__Issue1407_pt,"Issue1407_pt",0);
original_case!(polyfill2d__IssueT40777_colinear,"IssueT40777_colinear",0);
original_case!(polyfill2d__IssueT41986_axis_align,"IssueT41986_axis_align",0);
original_case!(polyfill2d__IssueT52834_axis_align_co_linear,"IssueT52834_axis_align_co_linear",0);
original_case!(polyfill2d__IssueT67109_axis_align_co_linear_a,"IssueT67109_axis_align_co_linear_a",0);
original_case!(polyfill2d__IssueT67109_axis_align_co_linear_b,"IssueT67109_axis_align_co_linear_b",0);
original_case!(polyfill2d__IssueT67109_axis_align_co_linear_c,"IssueT67109_axis_align_co_linear_c",0);
original_case!(polyfill2d__Issue103913_axis_align_co_linear_no_zero_area_tri,"Issue103913_axis_align_co_linear_no_zero_area_tri",2);

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("polyfill2d.TriangleCCW",polyfill2d__TriangleCCW,1008),
("polyfill2d.SquareCCW",polyfill2d__SquareCCW,2048),
("polyfill2d.SquareCW",polyfill2d__SquareCW,2048),
("polyfill2d.Starfleet",polyfill2d__Starfleet,2048),
("polyfill2d.StarfleetDegenerate",polyfill2d__StarfleetDegenerate,3440),
("polyfill2d.3Colinear",polyfill2d__3Colinear,1008),
("polyfill2d.4Colinear",polyfill2d__4Colinear,2048),
("polyfill2d.UnorderedColinear",polyfill2d__UnorderedColinear,3440),
("polyfill2d.PlusShape",polyfill2d__PlusShape,23040),
("polyfill2d.StarShape",polyfill2d__StarShape,9728),
("polyfill2d.UShape",polyfill2d__UShape,15680),
("polyfill2d.Spiral",polyfill2d__Spiral,41984),
("polyfill2d.TestFlipCode",polyfill2d__TestFlipCode,36720),
("polyfill2d.SelfIntersect",polyfill2d__SelfIntersect,3280),
("polyfill2d.SelfTouch",polyfill2d__SelfTouch,23040),
("polyfill2d.SelfOverlap",polyfill2d__SelfOverlap,22656),
("polyfill2d.TestDavData",polyfill2d__TestDavData,105200),
("polyfill2d.Issue815",polyfill2d__Issue815,9728),
("polyfill2d.Issue207_1",polyfill2d__Issue207_1,18832),
("polyfill2d.Issue207_11",polyfill2d__Issue207_11,208880),
("polyfill2d.Issue1407",polyfill2d__Issue1407,2048),
("polyfill2d.Issue1407_pt",polyfill2d__Issue1407_pt,3440),
("polyfill2d.IssueT40777_colinear",polyfill2d__IssueT40777_colinear,66560),
("polyfill2d.IssueT41986_axis_align",polyfill2d__IssueT41986_axis_align,208880),
("polyfill2d.IssueT52834_axis_align_co_linear",polyfill2d__IssueT52834_axis_align_co_linear,396288),
("polyfill2d.IssueT67109_axis_align_co_linear_a",polyfill2d__IssueT67109_axis_align_co_linear_a,15680),
("polyfill2d.IssueT67109_axis_align_co_linear_b",polyfill2d__IssueT67109_axis_align_co_linear_b,15680),
("polyfill2d.IssueT67109_axis_align_co_linear_c",polyfill2d__IssueT67109_axis_align_co_linear_c,15680),
("polyfill2d.Issue103913_axis_align_co_linear_no_zero_area_tri",polyfill2d__Issue103913_axis_align_co_linear_no_zero_area_tri,274560),
];
