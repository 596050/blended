#!/usr/bin/env python3
"""Finite reviewed adapter for every pinned BLI_span_test.cc declaration.

The original complete file and body hashes are required; unknown identities fail.
Read-only views retain aliasing with Cell-backed mutable storage. C++ implicit
conversions become explicit Rust From/Into capabilities, including negatives.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
PATH='source/blender/blenlib/tests/BLI_span_test.cc'
BLOB='9ff9fb5391b81d999a231e6785cb7efa07beaf6a'
HEAD='''// SPDX-FileCopyrightText: 2023 Blender Authors
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
'''
BODIES={
'FromSmallVector':'''let a=vec![1,2,3];let a_span=Span::from_slice(&a);
eq!(report,a_span.len(),3);eq!(report,a_span.at(0),1);eq!(report,a_span.at(1),2);eq!(report,a_span.at(2),3);''',
'AddConstToPointer':'''let mut a=0_i32;let vec=vec![&mut a as *mut i32];let span=Span::from_slice(&vec);
let const_span:Span<'_,*const i32>=span.into();eq!(report,const_span.len(),1);''',
'IsReferencing':'''let array=[3,5,8].map(Cell::new);let span=MutableSpan::from_cells(&array);
eq!(report,span.len(),3);eq!(report,span.at(1),5);array[1].set(10);eq!(report,span.at(1),10);''',
'DropBack':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_back(2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),4);eq!(report,slice.at(1),5);''',
'DropBackAll':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_back(a.len());eq!(report,slice.len(),0);''',
'DropFront':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_front(1);
eq!(report,slice.len(),3);eq!(report,slice.at(0),5);eq!(report,slice.at(1),6);eq!(report,slice.at(2),7);''',
'DropFrontLargeN':'''let a:Vec<Cell<i32>>=vec![1,2,3,4,5].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).drop_front(100);let slice2=MutableSpan::from_cells(&a).drop_front(100);
yes!(report,slice1.is_empty());yes!(report,slice2.is_empty());''',
'DropFrontAll':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).drop_front(a.len());eq!(report,slice.len(),0);''',
'TakeFront':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).take_front(2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),4);eq!(report,slice.at(1),5);''',
'TakeFrontLargeN':'''let a:Vec<Cell<i32>>=vec![4,5,6,7].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).take_front(100);let slice2=MutableSpan::from_cells(&a).take_front(100);
eq!(report,slice1.len(),4);eq!(report,slice2.len(),4);''',
'TakeBack':'''let a=vec![5,6,7,8];let slice=Span::from_slice(&a).take_back(2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),7);eq!(report,slice.at(1),8);''',
'TakeBackLargeN':'''let a:Vec<Cell<i32>>=vec![3,4,5,6].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).take_back(100);let slice2=MutableSpan::from_cells(&a).take_back(100);
eq!(report,slice1.len(),4);eq!(report,slice2.len(),4);''',
'Slice':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).slice(1,2);
eq!(report,slice.len(),2);eq!(report,slice.at(0),5);eq!(report,slice.at(1),6);''',
'SliceEmpty':'''let a=vec![4,5,6,7];let slice=Span::from_slice(&a).slice(2,0);eq!(report,slice.len(),0);''',
'SliceRange':'''let a=vec![1,2,3,4,5];let slice=Span::from_slice(&a).slice_range(crate::data_structures::IndexRange::new(2,2));
eq!(report,slice.len(),2);eq!(report,slice.at(0),3);eq!(report,slice.at(1),4);''',
'SliceLargeN':'''let a:Vec<Cell<i32>>=vec![1,2,3,4,5].into_iter().map(Cell::new).collect();
let slice1=Span::from_cells(&a).slice_safe(3,100);let slice2=MutableSpan::from_cells(&a).slice_safe(3,100);
eq!(report,slice1.len(),2);eq!(report,slice2.len(),2);eq!(report,slice1.at(0),4);eq!(report,slice2.at(0),4);eq!(report,slice1.at(1),5);eq!(report,slice2.at(1),5);''',
'Contains':'''let a=vec![4,5,6,7];let a_span=Span::from_slice(&a);
yes!(report,a_span.contains(4));yes!(report,a_span.contains(5));yes!(report,a_span.contains(6));yes!(report,a_span.contains(7));no!(report,a_span.contains(3));no!(report,a_span.contains(8));''',
'mutable_span.Contains':'''let a:Vec<Cell<i32>>=vec![4,5,6,7].into_iter().map(Cell::new).collect();let a_span=MutableSpan::from_cells(&a);
yes!(report,a_span.contains(4));yes!(report,a_span.contains(5));yes!(report,a_span.contains(6));yes!(report,a_span.contains(7));no!(report,a_span.contains(3));no!(report,a_span.contains(8));''',
'Count':'''let a=vec![2,3,4,3,3,2,2,2,2];let a_span=Span::from_slice(&a);
eq!(report,a_span.count(1),0);eq!(report,a_span.count(2),5);eq!(report,a_span.count(3),3);eq!(report,a_span.count(4),1);eq!(report,a_span.count(5),0);''',
'FromInitializerList':'''initializer_helper(&mut report,Span::from_slice(&[3,6,8,9]));''',
'FromVector':'''let a=vec![1,2,3,4];let a_span=Span::from_slice(&a);
eq!(report,a_span.len(),4);eq!(report,a_span.at(0),1);eq!(report,a_span.at(1),2);eq!(report,a_span.at(2),3);eq!(report,a_span.at(3),4);''',
'FromArray':'''let a=[5,6];let a_span=Span::from_slice(&a);eq!(report,a_span.len(),2);eq!(report,a_span.at(0),5);eq!(report,a_span.at(1),6);''',
'Fill':'''let a=[4,5,6,7,8].map(Cell::new);let a_span=MutableSpan::from_cells(&a);a_span.fill(1);
eq!(report,a[0].get(),1);eq!(report,a[1].get(),1);eq!(report,a[2].get(),1);eq!(report,a[3].get(),1);eq!(report,a[4].get(),1);''',
'FillIndices':'''let a=[0,0,0,0,0].map(Cell::new);let a_span=MutableSpan::from_cells(&a);a_span.fill_indices(&[0,2,3],1);
eq!(report,a[0].get(),1);eq!(report,a[1].get(),0);eq!(report,a[2].get(),1);eq!(report,a[3].get(),1);eq!(report,a[4].get(),0);''',
'SizeInBytes':'''let a=[0_i32;10];let a_span=Span::from_slice(&a);
eq!(report,a_span.size_in_bytes(),core::mem::size_of_val(&a));eq!(report,a_span.size_in_bytes(),40);''',
'FirstLast':'''let a=[6,7,8,9];let a_span=Span::from_slice(&a);
eq!(report,a_span.first(),6);eq!(report,a_span.last(0),9);eq!(report,a_span.last(1),8);eq!(report,a_span.last(2),7);''',
'FirstLast_OneElement':'''let a=3;let a_span=Span::from_slice(core::slice::from_ref(&a));
eq!(report,a_span.first(),3);eq!(report,a_span.last(0),3);eq!(report,a_span.last(0),3);''',
'ContainsPtr':'''let a=[5,6,7];let other=10;let a_span=Span::from_slice(&a);
yes!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(0)));yes!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(1)));yes!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(2)));no!(report,a_span.contains_ptr(a.as_ptr().wrapping_add(3)));
let ptr_before=(a.as_ptr() as usize).wrapping_sub(1) as *const i32;
no!(report,a_span.contains_ptr(ptr_before));no!(report,a_span.contains_ptr(&other));''',
'FirstIndex':'''let a=[4,5,4,2,5];let a_span=Span::from_slice(&a);
eq!(report,a_span.first_index(4),0);eq!(report,a_span.first_index(5),1);eq!(report,a_span.first_index(2),3);''',
'CastSameSize':'''let mut value=0_i32;let a=[&mut value as *mut i32,core::ptr::null_mut(),core::ptr::null_mut(),core::ptr::null_mut()];let a_span=Span::from_slice(&a);
let new_a_span=a_span.cast::<*mut f32>();eq!(report,a_span.len(),4);eq!(report,new_a_span.len(),4);
peq!(report,a_span.at(0),&mut value as *mut i32);peq!(report,new_a_span.at(0),(&mut value as *mut i32).cast::<f32>());''',
'CastSmallerSize':'''let a=[3_u32,4,5,6];let a_span=Span::from_slice(&a);let new_a_span=a_span.cast::<u16>();
eq!(report,a_span.len(),4);eq!(report,new_a_span.len(),8);''',
'CastLargerSize':'''let a=[4_u16,5,6,7];let a_span=Span::from_slice(&a);let new_a_span=a_span.cast::<u32>();
eq!(report,a_span.len(),4);eq!(report,new_a_span.len(),2);''',
'VoidPointerSpan':'''let mut a=core::mem::MaybeUninit::<i32>::uninit();let mut b=core::mem::MaybeUninit::<f32>::uninit();let mut c=core::mem::MaybeUninit::<f64>::uninit();
let mut func1=|span:Span<'_,*mut ()>|{eq!(report,span.len(),3);};
func1(Span::from_slice(&[a.as_mut_ptr().cast(),b.as_mut_ptr().cast(),c.as_mut_ptr().cast()]));''',
'CopyFrom':'''let src=[5,6,7,8];let dst=[1,2,3,4].map(Cell::new);
eq!(report,dst[2].get(),3);MutableSpan::from_cells(&dst).copy_from(Span::from_slice(&src));
eq!(report,dst[0].get(),5);eq!(report,dst[1].get(),6);eq!(report,dst[2].get(),7);eq!(report,dst[3].get(),8);''',
'ReverseIterator':'''let src=[4,5,6,7];let span=Span::from_slice(&src);let mut reversed_vec=Vec::new();
for value in span.iter().rev(){reversed_vec.push(value);}
eq!(report,reversed_vec.len(),4);span_eq(&mut report,&reversed_vec,&[7,6,5,4]);''',
'ReverseMutableSpan':'''let src0:[Cell<i32>;0]=[];let span0=MutableSpan::from_cells(&src0);span0.reverse();span_eq(&mut report,&span0.to_vec(),&[]);
let src1=[4].map(Cell::new);let span1=MutableSpan::from_cells(&src1);span1.reverse();span_eq(&mut report,&span1.to_vec(),&[4]);
let src2=[4,5].map(Cell::new);let span2=MutableSpan::from_cells(&src2);span2.reverse();span_eq(&mut report,&span2.to_vec(),&[5,4]);
let src5=[4,5,6,7,8].map(Cell::new);let span5=MutableSpan::from_cells(&src5);span5.reverse();span_eq(&mut report,&span5.to_vec(),&[8,7,6,5,4]);''',
'MutableReverseIterator':'''let src=[4,5,6,7].map(Cell::new);let span=MutableSpan::from_cells(&src);let mut reversed_vec=Vec::new();
for cell in span.iter().rev(){reversed_vec.push(cell.get());cell.set(cell.get()+10);}
eq!(report,reversed_vec.len(),4);span_eq(&mut report,&reversed_vec,&[7,6,5,4]);span_eq(&mut report,&src.iter().map(Cell::get).collect::<Vec<_>>(),&[14,15,16,17]);''',
'Constexpr':'''const SRC:[i32;3]=[3,2,1];const SPAN:Span<'static,i32>=Span::from_slice(&SRC);
const _:()=assert!(SPAN.at(2)==1);
const _:()=assert!(SPAN.len()==3);
const _:()=assert!(SPAN.slice(1,2).len()==2);
const _:()=assert!(!SPAN.has_duplicates_linear());
const IC:bool=SPAN.first_index(1)==2;
const _:()=assert!(IC);
eq!(report,SPAN.slice(1,2).len(),2);''',
'ImplicitConversions':'''type Src0=MutableSpan<'static,i32>;type Dst0=Span<'static,i32>;
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
not_into!(Src7,Dst7);''',
'Comparison':'''let a=[3,4,5];let b=[3,4,5,6];
no!(report,Span::from_slice(&a)==Span::from_slice(&b));no!(report,Span::from_slice(&b)==Span::from_slice(&a));yes!(report,Span::from_slice(&a)==Span::from_slice(&b).take_front(3));yes!(report,Span::from_slice(&a)==Span::from_slice(&a));yes!(report,Span::from_slice(&b)==Span::from_slice(&b));
yes!(report,Span::from_slice(&a)!=Span::from_slice(&b));yes!(report,Span::from_slice(&b)!=Span::from_slice(&a));no!(report,Span::from_slice(&a)!=Span::from_slice(&b).take_front(3));no!(report,Span::from_slice(&a)!=Span::from_slice(&a));'''
}
COUNTS=[4,1,3,3,1,4,2,1,3,2,3,2,3,1,3,6,6,6,5,5,5,3,5,5,2,4,3,6,3,4,2,2,1,5,6,12,11,1,0,9]

def generate(root=ROOT):
    if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong pinned reference')
    raw=(root/'.upstream/blender'/PATH).read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:raise ValueError('Upstream span source changed')
    text=raw.decode();source_sha=hashlib.sha256(raw).hexdigest();original=list(extract(text))
    if len(original)!=40 or len(BODIES)!=40:raise ValueError('Changed complete source universe')
    output=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
    for index,((identity,body,line),count) in enumerate(zip(original,COUNTS)):
        code=BODIES[identity if identity.startswith('mutable_span.') else identity.split('.')[1]];fn=identity.replace('.','__')
        output+=f'\n// {PATH}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();\n{code}\nreport\n}}\n'
        native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::span_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
        case=dict(id=identity,path=PATH,line=line,source_sha256=source_sha,source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=len(re.findall(r'\bEXPECT_[A-Z_]+',body)),expected_runtime_assertions=count,index=index,status='ported_unexecuted')
        if count==0:case.update(assertion_free_smoke=True,compile_time_only=True)
        cases.append(case)
    output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    target='crates/blended-core/src/span_cases.rs';(root/target).write_text(output)
    (root/'crates/blended-core/tests/upstream_spans.rs').write_text(native)
    (root/'tests/upstream/blender/BLI_span_test.cc').write_bytes(raw)
    from inventory import scan_cpp
    statics=[c for c in scan_cpp(text,PATH) if c['kind']=='static_assert']
    if len(statics)!=13:raise ValueError('Changed original compile-time universe')
    compile_cases=[]
    for index,c in enumerate(statics):
        compile_cases.append(dict(id=c['identity'],path=PATH,line=c['line'],kind='static_assert',source_sha256=source_sha,rust_function='span__Constexpr' if index<5 else 'span__ImplicitConversions',target_path=target,target_module='span_cases',assertion_count=1,runtime_assertions=0,source_condition=text.splitlines()[c['line']-1].strip(),condition_index=index,status='ported_unexecuted',category='const_value' if index<5 else 'allowed_conversion' if index<10 else 'forbidden_conversion'))
    (root/'compatibility/span-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,cases=cases,complete_blender_test_port=False,notes='All 40 runtime declarations, including the zero-runtime-assertion conversion case. All 13 original BLI_STATIC_ASSERT predicates are mapped separately. Rust From/Into expresses allowed and forbidden conversion capabilities, not implicit C++ syntax. Cell storage keeps aliasing; raw-pointer equality is not replaced by value equality; casts preserve bytes. Out-of-range empty-view pointer location is clamped safely and not claimed as native UB parity.'),indent=2)+'\n')
    (root/'compatibility/span-static-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,cases=compile_cases,complete_blender_test_port=False),indent=2)+'\n')
    return cases,compile_cases
if __name__=='__main__':
    cases,static=generate();print(json.dumps(dict(runtime_cases=len(cases),assertions=sum(c['expected_runtime_assertions'] for c in cases),compile_time_cases=len(static))))
