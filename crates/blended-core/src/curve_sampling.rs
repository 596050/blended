// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Rust adaptation of BLI_length_parameterize.hh and intern/length_parameterize.cc.
// This serial kernel preserves the exercised sampling semantics, not native task scheduling.
pub trait CurveValue:Copy {
    fn distance(self,other:Self)->f32;
    fn blend(self,other:Self,factor:f32)->Self;
}
impl CurveValue for f32 {
    fn distance(self,other:Self)->f32{(self-other).abs()}
    fn blend(self,other:Self,t:f32)->Self{self*(1.0-t)+other*t}
}
impl<const N:usize> CurveValue for [f32;N] {
    fn distance(self,other:Self)->f32{let mut square=0.0;for i in 0..N{let d=self[i]-other[i];square+=d*d;}square.sqrt()}
    fn blend(self,other:Self,t:f32)->Self{core::array::from_fn(|i|self[i]*(1.0-t)+other[i]*t)}
}
pub fn segments_num(points:usize,cyclic:bool)->usize{if cyclic{points}else{points.checked_sub(1).expect("An open curve needs a point")}}
pub fn accumulate_lengths<T:CurveValue>(values:&[T],cyclic:bool,lengths:&mut[f32]){
    let expected=if cyclic && values.len()<=1{0}else{segments_num(values.len(),cyclic)};
    assert_eq!(lengths.len(),expected);
    let mut total=0.0;
    for i in 0..values.len().saturating_sub(1){total+=values[i].distance(values[i+1]);lengths[i]=total;}
    if cyclic && values.len()>1{*lengths.last_mut().unwrap()=total+values[values.len()-1].distance(values[0]);}
}
fn validate_lengths(lengths:&[f32]){assert!(!lengths.is_empty());assert!(lengths.windows(2).all(|p|p[0]<=p[1]));}
pub fn sample_at_length(lengths:&[f32],position:f32)->(i32,f32){
    assert!(!lengths.is_empty() && position>=0.0);
    if position>=lengths[lengths.len()-1]{return ((lengths.len()-1) as i32,1.0);}
    let i=lengths.partition_point(|&end|end<=position);
    let start=if i==0{0.0}else{lengths[i-1]};let length=lengths[i]-start;
    let inverse=if length==0.0{0.0}else{1.0/length};
    (i as i32,(position-start)*inverse)
}
pub fn sample_uniform(lengths:&[f32],include_last:bool,indices:&mut[i32],factors:&mut[f32]){
    validate_lengths(lengths);assert_eq!(indices.len(),factors.len());assert!(!indices.is_empty());
    if indices.len()==1{indices[0]=0;factors[0]=0.0;return;}
    let total=lengths[lengths.len()-1];let step=total/((indices.len()-usize::from(include_last)) as f32);
    for i in 0..indices.len(){let (index,t)=sample_at_length(lengths,total.min(i as f32*step));indices[i]=index;factors[i]=t;}
}
pub fn sample_at_lengths(lengths:&[f32],samples:&[f32],indices:&mut[i32],factors:&mut[f32]){
    validate_lengths(lengths);assert_eq!(samples.len(),indices.len());assert_eq!(indices.len(),factors.len());
    assert!(samples.windows(2).all(|p|p[0]<=p[1]));
    for (i,&position) in samples.iter().enumerate(){let(index,t)=sample_at_length(lengths,position);indices[i]=index;factors[i]=t;}
}
pub fn interpolate<T:CurveValue>(src:&[T],indices:&[i32],factors:&[f32],dst:&mut[T]){
    assert!(!src.is_empty());assert_eq!(indices.len(),factors.len());assert_eq!(indices.len(),dst.len());
    for i in 0..dst.len(){let previous=usize::try_from(indices[i]).expect("Negative segment index");assert!(previous<src.len());let next=if previous==src.len()-1{0}else{previous+1};dst[i]=src[previous].blend(src[next],factors[i]);}
}
