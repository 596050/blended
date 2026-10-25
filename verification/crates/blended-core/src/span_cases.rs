// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked port. Original file/identity/body hashes: span-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::spans::{Span,MutableSpan};
use core::cell::Cell;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
 // The original ImplicitConversions case has only compile-time assertions.
 pub fn passed(&self)->bool{self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{$r.check(core::ptr::eq($a,$b),stringify!($a pointer-equals $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
fn span_eq(report:&mut Report,expected:&[i32],actual:&[i32]){
 eq!(report,expected.len(),actual.len());
 if expected.len()==actual.len(){for i in 0..expected.len(){eq!(report,expected[i],actual[i]);}}
}
fn initializer_helper(report:&mut Report,span:Span<'_,i32>){
 eq!(report,span.len(),4);eq!(report,span.at(0),3);eq!(report,span.at(1),6);eq!(report,span.at(2),8);eq!(report,span.at(3),9);
}
// Capability checks are compiled, not replaced by runtime Boolean constants.
fn require_into<A:Into<B>,B>(){}
macro_rules! not_into {($a:ty,$b:ty)=>{const _:fn()=||{
 trait AmbiguousIfInto<M>{fn check(){}}
 impl<T:?Sized> AmbiguousIfInto<()> for T{}
 struct HasConversion;
 impl<T:?Sized+Into<$b>> AmbiguousIfInto<HasConversion> for T{}
 let _=<$a as AmbiguousIfInto<_>>::check;
};};}

// source/blender/blenlib/tests/BLI_span_test.cc:14
pub fn span__FromSmallVector()->Report{let mut report=Report::default();
let a=vec![1,2,3];let a_span=Span::from_slice(&a);
eq!(report,a_span.len(),3);eq!(report,a_span.at(0),1);eq!(report,a_span.at(1),2);eq!(report,a_span.at(2),3);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:24
pub fn span__AddConstToPointer()->Report{let mut report=Report::default();
let mut a=0_i32;let vec=vec![&mut a as *mut i32];let span=Span::from_slice(&vec);
let const_span:Span<'_,*const i32>=span.into();eq!(report,const_span.len(),1);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:33
pub fn span__IsReferencing()->Report{let mut report=Report::default();
let array=[3,5,8].map(Cell::new);let span=MutableSpan::from_cells(&array);
eq!(report,span.len(),3);eq!(report,span.at(1),5);array[1].set(10);eq!(report,span.at(1),10);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:43
pub fn span__DropBack()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_back(2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),4);eq!(report,slice.at(1),5);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:52
pub fn span__DropBackAll()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_back(a.len());eq!(report,slice.len(),0);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:59
pub fn span__DropFront()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_front(1);
eq!(report,slice.len(),3);eq!(report,slice.at(0),5);eq!(report,slice.at(1),6);eq!(report,slice.at(2),7);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:69
pub fn span__DropFrontLargeN()->Report{let mut report=Report::default();
let a:Vec<Cell<i32>>=vec![1,2,3,4,5].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).drop_front(100);let slice2=MutableSpan::from_cells(&a).drop_front(100);
yes!(report,slice1.is_empty());yes!(report,slice2.is_empty());
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:78
pub fn span__DropFrontAll()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_front(a.len());eq!(report,slice.len(),0);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:85
pub fn span__TakeFront()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).take_front(2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),4);eq!(report,slice.at(1),5);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:94
pub fn span__TakeFrontLargeN()->Report{let mut report=Report::default();
let a:Vec<Cell<i32>>=vec![4,5,6,7].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).take_front(100);let slice2=MutableSpan::from_cells(&a).take_front(100);
eq!(report,slice1.len(),4);eq!(report,slice2.len(),4);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:103
pub fn span__TakeBack()->Report{let mut report=Report::default();
let a=vec![5,6,7,8];let slice=Span::from_slice(&a).take_back(2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),7);eq!(report,slice.at(1),8);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:112
pub fn span__TakeBackLargeN()->Report{let mut report=Report::default();
let a:Vec<Cell<i32>>=vec![3,4,5,6].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).take_back(100);let slice2=MutableSpan::from_cells(&a).take_back(100);
eq!(report,slice1.len(),4);eq!(report,slice2.len(),4);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:121
pub fn span__Slice()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).slice(1,2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),5);eq!(report,slice.at(1),6);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:130
pub fn span__SliceEmpty()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let slice=Span::from_slice(&a).slice(2,0);eq!(report,slice.len(),0);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:137
pub fn span__SliceRange()->Report{let mut report=Report::default();
let a=vec![1,2,3,4,5];let slice=Span::from_slice(&a).slice_range(crate::data_structures::IndexRange::new(2,2));
eq!(report,slice.len(),2);eq!(report,slice.at(0),3);eq!(report,slice.at(1),4);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:146
pub fn span__SliceLargeN()->Report{let mut report=Report::default();
let a:Vec<Cell<i32>>=vec![1,2,3,4,5].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).slice_safe(3,100);let slice2=MutableSpan::from_cells(&a).slice_safe(3,100);
eq!(report,slice1.len(),2);eq!(report,slice2.len(),2);eq!(report,slice1.at(0),4);eq!(report,slice2.at(0),4);eq!(report,slice1.at(1),5);eq!(report,slice2.at(1),5);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:159
pub fn span__Contains()->Report{let mut report=Report::default();
let a=vec![4,5,6,7];let a_span=Span::from_slice(&a);
yes!(report,a_span.contains(4));yes!(report,a_span.contains(5));yes!(report,a_span.contains(6));yes!(report,a_span.contains(7));no!(report,a_span.contains(3));no!(report,a_span.contains(8));
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:171
pub fn mutable_span__Contains()->Report{let mut report=Report::default();
let a:Vec<Cell<i32>>=vec![4,5,6,7].into_iter().map(Cell::new).collect();let a_span=MutableSpan::from_cells(&a);
yes!(report,a_span.contains(4));yes!(report,a_span.contains(5));yes!(report,a_span.contains(6));yes!(report,a_span.contains(7));no!(report,a_span.contains(3));no!(report,a_span.contains(8));
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:183
pub fn span__Count()->Report{let mut report=Report::default();
let a=vec![2,3,4,3,3,2,2,2,2];let a_span=Span::from_slice(&a);
eq!(report,a_span.count(1),0);eq!(report,a_span.count(2),5);eq!(report,a_span.count(3),3);eq!(report,a_span.count(4),1);eq!(report,a_span.count(5),0);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:203
pub fn span__FromInitializerList()->Report{let mut report=Report::default();
initializer_helper(&mut report,Span::from_slice(&[3,6,8,9]));
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:208
pub fn span__FromVector()->Report{let mut report=Report::default();
let a=vec![1,2,3,4];let a_span=Span::from_slice(&a);
eq!(report,a_span.len(),4);eq!(report,a_span.at(0),1);eq!(report,a_span.at(1),2);eq!(report,a_span.at(2),3);eq!(report,a_span.at(3),4);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:219
pub fn span__FromArray()->Report{let mut report=Report::default();
let a=[5,6];let a_span=Span::from_slice(&a);eq!(report,a_span.len(),2);eq!(report,a_span.at(0),5);eq!(report,a_span.at(1),6);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:228
pub fn span__Fill()->Report{let mut report=Report::default();
let a=[4,5,6,7,8].map(Cell::new);let a_span=MutableSpan::from_cells(&a);a_span.fill(1);
eq!(report,a[0].get(),1);eq!(report,a[1].get(),1);eq!(report,a[2].get(),1);eq!(report,a[3].get(),1);eq!(report,a[4].get(),1);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:240
pub fn span__FillIndices()->Report{let mut report=Report::default();
let a=[0,0,0,0,0].map(Cell::new);let a_span=MutableSpan::from_cells(&a);a_span.fill_indices(&[0,2,3],1);
eq!(report,a[0].get(),1);eq!(report,a[1].get(),0);eq!(report,a[2].get(),1);eq!(report,a[3].get(),1);eq!(report,a[4].get(),0);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:252
pub fn span__SizeInBytes()->Report{let mut report=Report::default();
let a=[0_i32;10];let a_span=Span::from_slice(&a);
eq!(report,a_span.size_in_bytes(),core::mem::size_of_val(&a));eq!(report,a_span.size_in_bytes(),40);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:260
pub fn span__FirstLast()->Report{let mut report=Report::default();
let a=[6,7,8,9];let a_span=Span::from_slice(&a);
eq!(report,a_span.first(),6);eq!(report,a_span.last(0),9);eq!(report,a_span.last(1),8);eq!(report,a_span.last(2),7);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:270
pub fn span__FirstLast_OneElement()->Report{let mut report=Report::default();
let a=3;let a_span=Span::from_slice(core::slice::from_ref(&a));
eq!(report,a_span.first(),3);eq!(report,a_span.last(0),3);eq!(report,a_span.last(0),3);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:279
pub fn span__ContainsPtr()->Report{let mut report=Report::default();
let a=[5,6,7];let other=10;let a_span=Span::from_slice(&a);
yes!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(0)));yes!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(1)));yes!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(2)));no!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(3)));
let ptr_before=(a.as_ptr() as usize).wrapping_sub(1) as *const i32;
no!(report,a_span.contains_ptr(ptr_before));no!(report,a_span.contains_ptr(&other));
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:293
pub fn span__FirstIndex()->Report{let mut report=Report::default();
let a=[4,5,4,2,5];let a_span=Span::from_slice(&a);
eq!(report,a_span.first_index(4),0);eq!(report,a_span.first_index(5),1);eq!(report,a_span.first_index(2),3);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:303
pub fn span__CastSameSize()->Report{let mut report=Report::default();
let mut value=0_i32;let a=[&mut value as *mut i32,core::ptr::null_mut(),core::ptr::null_mut(),core::ptr::null_mut()];let a_span=Span::from_slice(&a);
let new_a_span=a_span.cast::<*mut f32>();eq!(report,a_span.len(),4);eq!(report,new_a_span.len(),4);
peq!(report,a_span.at(0),&mut value as *mut i32);peq!(report,new_a_span.at(0),(&mut value as *mut i32).cast::<f32>());
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:317
pub fn span__CastSmallerSize()->Report{let mut report=Report::default();
let a=[3_u32,4,5,6];let a_span=Span::from_slice(&a);let new_a_span=a_span.cast::<u16>();
eq!(report,a_span.len(),4);eq!(report,new_a_span.len(),8);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:327
pub fn span__CastLargerSize()->Report{let mut report=Report::default();
let a=[4_u16,5,6,7];let a_span=Span::from_slice(&a);let new_a_span=a_span.cast::<u32>();
eq!(report,a_span.len(),4);eq!(report,new_a_span.len(),2);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:337
pub fn span__VoidPointerSpan()->Report{let mut report=Report::default();
let mut a=core::mem::MaybeUninit::<i32>::uninit();let mut b=core::mem::MaybeUninit::<f32>::uninit();let mut c=core::mem::MaybeUninit::<f64>::uninit();
let mut func1=|span:Span<'_,*mut ()>|{eq!(report,span.len(),3);};
func1(Span::from_slice(&[a.as_mut_ptr().cast(),b.as_mut_ptr().cast(),c.as_mut_ptr().cast()]));
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:347
pub fn span__CopyFrom()->Report{let mut report=Report::default();
let src=[5,6,7,8];let dst=[1,2,3,4].map(Cell::new);
eq!(report,dst[2].get(),3);MutableSpan::from_cells(&dst).copy_from(Span::from_slice(&src));
eq!(report,dst[0].get(),5);eq!(report,dst[1].get(),6);eq!(report,dst[2].get(),7);eq!(report,dst[3].get(),8);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:360
pub fn span__ReverseIterator()->Report{let mut report=Report::default();
let src=[4,5,6,7];let span=Span::from_slice(&src);let mut reversed_vec=Vec::new();
for value in span.iter().rev(){reversed_vec.push(value);}
eq!(report,reversed_vec.len(),4);span_eq(&mut report,&reversed_vec,&[7,6,5,4]);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:373
pub fn span__ReverseMutableSpan()->Report{let mut report=Report::default();
let src0:[Cell<i32>;0]=[];let span0=MutableSpan::from_cells(&src0);span0.reverse();span_eq(&mut report,&span0.to_vec(),&[]);
let src1=[4].map(Cell::new);let span1=MutableSpan::from_cells(&src1);span1.reverse();span_eq(&mut report,&span1.to_vec(),&[4]);
let src2=[4,5].map(Cell::new);let span2=MutableSpan::from_cells(&src2);span2.reverse();span_eq(&mut report,&span2.to_vec(),&[5,4]);
let src5=[4,5,6,7,8].map(Cell::new);let span5=MutableSpan::from_cells(&src5);span5.reverse();span_eq(&mut report,&span5.to_vec(),&[8,7,6,5,4]);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:396
pub fn span__MutableReverseIterator()->Report{let mut report=Report::default();
let src=[4,5,6,7].map(Cell::new);let span=MutableSpan::from_cells(&src);let mut reversed_vec=Vec::new();
for cell in span.iter().rev(){reversed_vec.push(cell.get());cell.set(cell.get()+10);}
eq!(report,reversed_vec.len(),4);span_eq(&mut report,&reversed_vec,&[7,6,5,4]);span_eq(&mut report,&src.iter().map(Cell::get).collect::<Vec<_>>(),&[14,15,16,17]);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:411
pub fn span__Constexpr()->Report{let mut report=Report::default();
const SRC:[i32;3]=[3,2,1];const SPAN:Span<'static,i32>=Span::from_slice(&SRC);
const _:()=assert!(SPAN.at(2)==1);
const _:()=assert!(SPAN.len()==3);
const _:()=assert!(SPAN.slice(1,2).len()==2);
const _:()=assert!(!SPAN.has_duplicates_linear());
const IC:bool=SPAN.first_index(1)==2;
const _:()=assert!(IC);
eq!(report,SPAN.slice(1,2).len(),2);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:426
pub fn span__ImplicitConversions()->Report{let mut report=Report::default();
type Src0=MutableSpan<'static,i32>;type Dst0=Span<'static,i32>;
const _:fn()=require_into::<Src0,Dst0>;
type Src1=Span<'static,*mut i32>;type Dst1=Span<'static,*const i32>;
const _:fn()=require_into::<Src1,Dst1>;
type Src2=MutableSpan<'static,*mut i32>;type Dst2=Span<'static,*mut i32>;
const _:fn()=require_into::<Src2,Dst2>;
type Src3=MutableSpan<'static,*mut i32>;type Dst3=Span<'static,*const i32>;
const _:fn()=require_into::<Src3,Dst3>;
type Src4=MutableSpan<'static,*mut i32>;type Dst4=MutableSpan<'static,*const i32>;
const _:fn()=require_into::<Src4,Dst4>;
type Src5=MutableSpan<'static,*const i32>;type Dst5=MutableSpan<'static,*mut i32>;
not_into!(Src5,Dst5);
type Src6=Span<'static,*const i32>;type Dst6=Span<'static,*mut i32>;
not_into!(Src6,Dst6);
type Src7=Span<'static,*mut i32>;type Dst7=MutableSpan<'static,*const i32>;
not_into!(Src7,Dst7);
report
}

// source/blender/blenlib/tests/BLI_span_test.cc:438
pub fn span__Comparison()->Report{let mut report=Report::default();
let a=[3,4,5];let b=[3,4,5,6];
no!(report,Span::from_slice(&a)==Span::from_slice(&b));no!(report,Span::from_slice(&b)==Span::from_slice(&a));yes!(report,Span::from_slice(&a)==Span::from_slice(&b).take_front(3));yes!(report,Span::from_slice(&a)==Span::from_slice(&a));yes!(report,Span::from_slice(&b)==Span::from_slice(&b));
yes!(report,Span::from_slice(&a)!=Span::from_slice(&b));yes!(report,Span::from_slice(&b)!=Span::from_slice(&a));no!(report,Span::from_slice(&a)!=Span::from_slice(&b).take_front(3));no!(report,Span::from_slice(&a)!=Span::from_slice(&a));
report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("span.FromSmallVector",span__FromSmallVector,4),
("span.AddConstToPointer",span__AddConstToPointer,1),
("span.IsReferencing",span__IsReferencing,3),
("span.DropBack",span__DropBack,3),
("span.DropBackAll",span__DropBackAll,1),
("span.DropFront",span__DropFront,4),
("span.DropFrontLargeN",span__DropFrontLargeN,2),
("span.DropFrontAll",span__DropFrontAll,1),
("span.TakeFront",span__TakeFront,3),
("span.TakeFrontLargeN",span__TakeFrontLargeN,2),
("span.TakeBack",span__TakeBack,3),
("span.TakeBackLargeN",span__TakeBackLargeN,2),
("span.Slice",span__Slice,3),
("span.SliceEmpty",span__SliceEmpty,1),
("span.SliceRange",span__SliceRange,3),
("span.SliceLargeN",span__SliceLargeN,6),
("span.Contains",span__Contains,6),
("mutable_span.Contains",mutable_span__Contains,6),
("span.Count",span__Count,5),
("span.FromInitializerList",span__FromInitializerList,5),
("span.FromVector",span__FromVector,5),
("span.FromArray",span__FromArray,3),
("span.Fill",span__Fill,5),
("span.FillIndices",span__FillIndices,5),
("span.SizeInBytes",span__SizeInBytes,2),
("span.FirstLast",span__FirstLast,4),
("span.FirstLast_OneElement",span__FirstLast_OneElement,3),
("span.ContainsPtr",span__ContainsPtr,6),
("span.FirstIndex",span__FirstIndex,3),
("span.CastSameSize",span__CastSameSize,4),
("span.CastSmallerSize",span__CastSmallerSize,2),
("span.CastLargerSize",span__CastLargerSize,2),
("span.VoidPointerSpan",span__VoidPointerSpan,1),
("span.CopyFrom",span__CopyFrom,5),
("span.ReverseIterator",span__ReverseIterator,6),
("span.ReverseMutableSpan",span__ReverseMutableSpan,12),
("span.MutableReverseIterator",span__MutableReverseIterator,11),
("span.Constexpr",span__Constexpr,1),
("span.ImplicitConversions",span__ImplicitConversions,0),
("span.Comparison",span__Comparison,9),
];
