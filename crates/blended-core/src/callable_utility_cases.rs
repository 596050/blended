// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Test-first translations of the complete pinned FunctionRef, random-access
// iterator mixin and SessionUID test files. Implementations intentionally live
// in separate modules so the pre-implementation commit fails to compile.
#![allow(non_snake_case)]
use crate::function_ref_compat::{FunctionRef0,FunctionRef1,FunctionRef2};
use crate::random_access_compat::DoublingIterator;
use crate::session_uid_compat::generate_session_uid;
use core::cell::Cell;

#[derive(Debug,Default)]
pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check(bool::from($a),stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!bool::from($a),stringify!(!$a),line!());}};}

fn perform_binary_operation(mut operation:FunctionRef2<'_,i32,i32,i32>,a:i32,b:i32)->i32{operation.call(a,b)}
fn add_two_numbers(a:i32,b:i32)->i32{a+b}

pub fn function_ref__StatelessLambda()->Report{
 let mut report=Report::default();let mut f=|a:i32,b:i32|a-b;
 let result=perform_binary_operation(FunctionRef2::new(&mut f),4,6);eq!(report,result,-2);report
}
pub fn function_ref__StatefullLambda()->Report{
 let mut report=Report::default();let factor=10;let mut f=|a:i32,b:i32|factor*(a+b);
 let result=perform_binary_operation(FunctionRef2::new(&mut f),2,3);eq!(report,result,50);report
}
pub fn function_ref__StandaloneFunction()->Report{
 let mut report=Report::default();let mut f:fn(i32,i32)->i32=add_two_numbers;
 let result=perform_binary_operation(FunctionRef2::new(&mut f),10,5);eq!(report,result,15);report
}
pub fn function_ref__ConstantFunction()->Report{
 let mut report=Report::default();let mut f=||42;let mut reference=FunctionRef0::new(&mut f);
 eq!(report,reference.call(),42);report
}
pub fn function_ref__MutableStatefullLambda()->Report{
 let mut report=Report::default();let mut counter=0;let mut f=||{let current=counter;counter+=1;current};
 let mut reference=FunctionRef0::new(&mut f);
 eq!(report,reference.call(),0);eq!(report,reference.call(),1);eq!(report,reference.call(),2);report
}
pub fn function_ref__Null()->Report{
 let mut report=Report::default();let mut reference=FunctionRef0::<i32>::empty();no!(report,reference.is_some());
 let mut f=||1;reference=FunctionRef0::new(&mut f);yes!(report,reference.is_some());
 reference=FunctionRef0::empty();no!(report,reference.is_some());report
}
pub fn function_ref__CopyDoesNotReferenceFunctionRef()->Report{
 let mut report=Report::default();let mut f1=||1;let mut f2=||2;
 let mut x=FunctionRef0::new(&mut f1);let mut y=x;x=FunctionRef0::new(&mut f2);
 let _=&x;eq!(report,y.call(),1);report
}
pub fn function_ref__CopyDoesNotReferenceFunctionRef2()->Report{
 let mut report=Report::default();let mut f=||1;
 let mut x=FunctionRef0::<i32>::empty();let mut y=FunctionRef0::new(&mut f);let z=y;x=z;y=FunctionRef0::empty();
 let _=&y;eq!(report,x.call(),1);report
}
pub fn function_ref__ReferenceAnotherFunctionRef()->Report{
 let mut report=Report::default();let mut f1=||1;let mut f2=||2;
 let x=Cell::new(FunctionRef0::new(&mut f1));let mut f3=||{let mut current=x.get();current.call()};
 let mut y=FunctionRef0::new(&mut f3);eq!(report,y.call(),1);
 x.set(FunctionRef0::new(&mut f2));eq!(report,y.call(),2);report
}
pub fn function_ref__InitializeWithNull()->Report{
 let mut report=Report::default();let f=FunctionRef2::<i32,i32,i32>::empty();no!(report,f.is_some());report
}
fn overload_string(_f:FunctionRef1<'_,String,()>)->i32{1}
fn overload_int(_f:FunctionRef1<'_,i32,()>)->i32{2}
pub fn function_ref__OverloadSelection()->Report{
 let mut report=Report::default();let mut f1=|_x:String|{};let mut f2=|_x:i32|{};
 eq!(report,overload_string(FunctionRef1::new(&mut f1)),1);
 eq!(report,overload_int(FunctionRef1::new(&mut f2)),2);report
}
pub fn function_ref__FalsyStdFunction()->Report{
 let mut report=Report::default();
 let fn_ref1=FunctionRef0::<()>::empty();let mut f2=||{};let fn_ref2=FunctionRef0::new(&mut f2);
 no!(report,fn_ref1.is_some());yes!(report,fn_ref2.is_some());
 let fn_ref3=FunctionRef0::<()>::empty();let mut f4=||{};let fn_ref4=FunctionRef0::new(&mut f4);
 no!(report,fn_ref3.is_some());yes!(report,fn_ref4.is_some());report
}
pub fn function_ref__FalsyFunctionPointer()->Report{
 let mut report=Report::default();let fn_ref1=FunctionRef0::<()>::from_fn_ptr(None);
 fn do_nothing(){} let fn_ref2=FunctionRef0::<()>::from_fn_ptr(Some(do_nothing));
 no!(report,fn_ref1.is_some());yes!(report,fn_ref2.is_some());report
}
pub fn random_access_iterator_mixin__DoublingIterator()->Report{
 let mut report=Report::default();let array=[3,6,1,2];let begin=DoublingIterator::new(&array);let end=begin.offset(array.len() as isize);
 let mut values=Vec::new();let mut it=begin;while it!=end{values.push(it.value());it=it.offset(1);}
 eq!(report,values.len(),4_usize);eq!(report,values[0],6);eq!(report,values[1],12);eq!(report,values[2],2);eq!(report,values[3],4);report
}
pub fn SessionUID__GenerateBasic()->Report{
 let mut report=Report::default();let uid=generate_session_uid();yes!(report,uid.is_generated());
 let uid1=generate_session_uid();let uid2=generate_session_uid();no!(report,uid1==uid2);report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
 ("function_ref.StatelessLambda",function_ref__StatelessLambda,1),
 ("function_ref.StatefullLambda",function_ref__StatefullLambda,1),
 ("function_ref.StandaloneFunction",function_ref__StandaloneFunction,1),
 ("function_ref.ConstantFunction",function_ref__ConstantFunction,1),
 ("function_ref.MutableStatefullLambda",function_ref__MutableStatefullLambda,3),
 ("function_ref.Null",function_ref__Null,3),
 ("function_ref.CopyDoesNotReferenceFunctionRef",function_ref__CopyDoesNotReferenceFunctionRef,1),
 ("function_ref.CopyDoesNotReferenceFunctionRef2",function_ref__CopyDoesNotReferenceFunctionRef2,1),
 ("function_ref.ReferenceAnotherFunctionRef",function_ref__ReferenceAnotherFunctionRef,2),
 ("function_ref.InitializeWithNull",function_ref__InitializeWithNull,1),
 ("function_ref.OverloadSelection",function_ref__OverloadSelection,2),
 ("function_ref.FalsyStdFunction",function_ref__FalsyStdFunction,4),
 ("function_ref.FalsyFunctionPointer",function_ref__FalsyFunctionPointer,2),
 ("random_access_iterator_mixin.DoublingIterator",random_access_iterator_mixin__DoublingIterator,5),
 ("SessionUID.GenerateBasic",SessionUID__GenerateBasic,2),
];
