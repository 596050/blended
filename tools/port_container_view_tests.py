#!/usr/bin/env python3
"""Finite reviewed adapter for two complete source files, not a general translator.

Mutable lookups and type-erased views borrow backing storage. Unique-pointer keys
retain address identity rather than Rust Box's pointee-value equality. Original
fixture setup executes once per suite, not as invented runtime assertions.
"""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={'BLI_multi_value_map_test.cc':'858a23ba5f319ca69f0c675e1bce0a22cb1886bdd377115f79e8dbaed95ade26','BLI_generic_span_test.cc':'82a5c3d10cdc7a7665df1b0900ef50fcbbea4bfd538be90f6c1ea761ecf92b16'}
HEAD='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked translations; complete originals retained under tests/upstream.
#![allow(non_snake_case,unused_mut)]
use crate::container_views::{MultiValueMap,OwnedKey,GSpan,GMutableSpan,registered_type,register_test_types};
use core::cell::Cell;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{$r.check(core::ptr::eq(($a) as *const u8,($b) as *const u8),stringify!($a pointer-equals $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
fn generic_span_suite_setup(){static SETUP:std::sync::Once=std::sync::Once::new();SETUP.call_once(register_test_types);}
'''
BODIES={
'LookupNotExistant':'''let mut map=MultiValueMap::<i32,i32>::new();
eq!(report,map.lookup(&5).len(),0);map.add(2,5);eq!(report,map.lookup(&5).len(),0);''',
'LookupExistant':'''let mut map=MultiValueMap::<i32,i32>::new();map.add(2,4);map.add(2,5);map.add(3,6);
eq!(report,map.lookup(&2).len(),2);eq!(report,map.lookup(&2)[0],4);eq!(report,map.lookup(&2)[1],5);
eq!(report,map.lookup(&3).len(),1);eq!(report,map.lookup(&3)[0],6);''',
'LookupMutable':'''let mut map=MultiValueMap::<i32,i32>::new();map.add(1,2);map.add(4,5);map.add(4,6);map.add(6,7);
{let span=map.lookup_mut(&4);eq!(report,span.len(),2);span[0]=10;span[1]=20;}
map.add(4,5);let new_span=map.lookup_mut(&4);eq!(report,new_span.len(),3);eq!(report,new_span[0],10);eq!(report,new_span[1],20);eq!(report,new_span[2],5);''',
'AddMultiple':'''let mut map=MultiValueMap::<i32,i32>::new();map.add_multiple(2,&[4,5,6]);map.add_multiple(2,&[1,2]);map.add_multiple(5,&[7,5,3]);
eq!(report,map.lookup(&2).len(),5);eq!(report,map.lookup(&2)[0],4);eq!(report,map.lookup(&2)[1],5);eq!(report,map.lookup(&2)[2],6);eq!(report,map.lookup(&2)[3],1);eq!(report,map.lookup(&2)[4],2);
eq!(report,map.lookup(&5).len(),3);eq!(report,map.lookup(&5)[0],7);eq!(report,map.lookup(&5)[1],5);eq!(report,map.lookup(&5)[2],3);''',
'Keys':'''let mut map=MultiValueMap::<i32,i32>::new();map.add(5,7);map.add(5,7);map.add_multiple(2,&[6,7,8]);let mut keys=Vec::new();for &key in map.keys(){keys.push(key);}
eq!(report,keys.len(),2);yes!(report,keys.contains(&5));yes!(report,keys.contains(&2));''',
'Values':'''let mut map=MultiValueMap::<i32,i32>::new();map.add(3,5);map.add_multiple(3,&[1,2]);map.add(6,1);
let mut values:Vec<&[i32]>=Vec::new();for value_span in map.values(){values.push(value_span);}eq!(report,values.len(),2);''',
'Items':'''let mut map=MultiValueMap::<i32,i32>::new();map.add_multiple(4,&[1,2,3]);for (&key,values) in map.items(){eq!(report,key,4);eq!(report,values.len(),3);eq!(report,values[0],1);eq!(report,values[1],2);eq!(report,values[2],3);}''',
'UniquePtr':'''let mut map=MultiValueMap::<OwnedKey<i32>,Box<i32>>::new();map.add(OwnedKey::new(4),Box::new(6));map.add(OwnedKey::new(4),Box::new(7));eq!(report,map.lookup(&OwnedKey::new(10)).len(),0);''',
'MutableItems':'''let mut map=MultiValueMap::<i32,i32>::new();map.add(1,3);map.add(1,4);for (_,span) in map.items_mut(){yes!(report,span.contains(&3));yes!(report,span.contains(&4));}''',
'TypeConstructor':'''generic_span_suite_setup();let span=GSpan::empty(registered_type::<f32>().unwrap());eq!(report,span.len(),0);eq!(report,span.typed::<f32>().unwrap().len(),0);yes!(report,span.is_empty());''',
'BufferAndSizeConstructor':'''generic_span_suite_setup();let values=[6_i32,7,3,2];let buffer=values.as_ptr().cast::<u8>();
// SAFETY: live initialized i32 array, correct registered descriptor, lifetime and extent.
let span=unsafe{GSpan::from_raw_parts(registered_type::<i32>().unwrap(),buffer,4)};
eq!(report,span.len(),4);no!(report,span.is_empty());eq!(report,span.typed::<i32>().unwrap().len(),4);
peq!(report,span.pointer_at(0),values.as_ptr().wrapping_add(0));peq!(report,span.pointer_at(1),values.as_ptr().wrapping_add(1));peq!(report,span.pointer_at(2),values.as_ptr().wrapping_add(2));peq!(report,span.pointer_at(3),values.as_ptr().wrapping_add(3));''',
'MutableTypeConstructor':'''generic_span_suite_setup();let span=GMutableSpan::empty(registered_type::<i32>().unwrap());eq!(report,span.len(),0);yes!(report,span.is_empty());''',
'MutableBufferAndSizeConstructor':'''generic_span_suite_setup();let values=[4_i32,7,3,5].map(Cell::new);let buffer=values.as_ptr().cast::<i32>().cast_mut().cast::<u8>();
// SAFETY: Cell<i32> has i32 layout and permits writes; no shared i32 reference escapes.
let span=unsafe{GMutableSpan::from_raw_parts(registered_type::<i32>().unwrap(),buffer,4)};
eq!(report,span.len(),4);no!(report,span.is_empty());eq!(report,span.typed::<i32>().unwrap().len(),4);eq!(report,values[2].get(),3);
unsafe{span.pointer_at(2).cast::<i32>().write(10)};eq!(report,values[2].get(),10);
span.typed::<i32>().unwrap().set(2,20);eq!(report,values[2].get(),20);'''
}
COUNTS=[2,5,5,10,3,1,5,1,2,3,7,2,6]
def extract(text):
 for m in re.finditer(r'\b(TEST(?:_F)?)\((\w+),\s*(\w+)\)\s*\{',text):
  start=m.end();i=start;depth=1
  while depth:
   if text[i]=='{':depth+=1
   elif text[i]=='}':depth-=1
   i+=1
  yield m[2]+'.'+m[3],text[start:i-1],text.count('\n',0,m.start())+1,m[1]
def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong reference')
 output=HEAD;cases=[]
 native='// SPDX-License-Identifier: Apache-2.0\n// Every runtime declaration in the two pinned original files; no stub passes.\nmacro_rules! original_case {($name:ident,$count:expr)=>{\n #[test] #[allow(non_snake_case)] fn $name(){\n  let r=blended_core::container_view_cases::$name();\n  assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,$count);\n }\n};}\n'
 for name,digest in FILES.items():
  path='source/blender/blenlib/tests/'+name;raw=(root/'.upstream/blender'/path).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Changed original source '+path)
  for identity,body,line,kind in extract(raw.decode()):
   code=BODIES[identity.split('.')[1]];count=COUNTS[len(cases)];fn=identity.replace('.','__')
   if len(re.findall(r'\b(?:EXPECT|ASSERT)_[A-Z_]+\(',body))!=count:raise ValueError('Original assertion count changed '+identity)
   if len(re.findall(r'\b(?:eq|peq|yes|no)!\(',code))!=count:raise ValueError('Lost translated assertion '+identity)
   output+=f'\n// {path}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();\n{code}\nreport\n}}\n'
   native+=f'original_case!({fn},{count});\n'
   cases.append(dict(id=identity,path=path,line=line,kind=kind,source_sha256=digest,source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=count,expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
  (root/'tests/upstream/blender'/name).write_bytes(raw)
 if len(cases)!=13 or sum(COUNTS)!=52:raise ValueError('Changed source universe')
 output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/container_view_cases.rs').write_text(output)
 (root/'crates/blended-core/tests/upstream_container_views.rs').write_text(native)
 (root/'compatibility/container-view-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,cases=cases,complete_blender_test_port=False,notes='Two complete source files. Mutable views borrow real storage. Owned pointer keys preserve allocation identity; distinct boxes with equal values do not merge. Original GenericSpanTest suite setup is once-only. Safe adapters use Copy values and checked descriptors; the complete CPPType lifecycle/registration API, ABI, all template instantiations and native iteration order are not certified.'),indent=2)+'\n')
 return cases
if __name__=='__main__':
 cases=generate();print(json.dumps(dict(cases=len(cases),assertions=sum(c['expected_runtime_assertions'] for c in cases))))
