// SPDX-FileCopyrightText: 2023 Blender Authors
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

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:11
pub fn multi_value_map__LookupNotExistant()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();
eq!(report,map.lookup(&5).len(),0);map.add(2,5);eq!(report,map.lookup(&5).len(),0);
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:19
pub fn multi_value_map__LookupExistant()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add(2,4);map.add(2,5);map.add(3,6);
eq!(report,map.lookup(&2).len(),2);eq!(report,map.lookup(&2)[0],4);eq!(report,map.lookup(&2)[1],5);
eq!(report,map.lookup(&3).len(),1);eq!(report,map.lookup(&3)[0],6);
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:34
pub fn multi_value_map__LookupMutable()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add(1,2);map.add(4,5);map.add(4,6);map.add(6,7);
{let span=map.lookup_mut(&4);eq!(report,span.len(),2);span[0]=10;span[1]=20;}
map.add(4,5);let new_span=map.lookup_mut(&4);eq!(report,new_span.len(),3);eq!(report,new_span[0],10);eq!(report,new_span[1],20);eq!(report,new_span[2],5);
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:55
pub fn multi_value_map__AddMultiple()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add_multiple(2,&[4,5,6]);map.add_multiple(2,&[1,2]);map.add_multiple(5,&[7,5,3]);
eq!(report,map.lookup(&2).len(),5);eq!(report,map.lookup(&2)[0],4);eq!(report,map.lookup(&2)[1],5);eq!(report,map.lookup(&2)[2],6);eq!(report,map.lookup(&2)[3],1);eq!(report,map.lookup(&2)[4],2);
eq!(report,map.lookup(&5).len(),3);eq!(report,map.lookup(&5)[0],7);eq!(report,map.lookup(&5)[1],5);eq!(report,map.lookup(&5)[2],3);
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:75
pub fn multi_value_map__Keys()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add(5,7);map.add(5,7);map.add_multiple(2,&[6,7,8]);let mut keys=Vec::new();for &key in map.keys(){keys.push(key);}
eq!(report,keys.len(),2);yes!(report,keys.contains(&5));yes!(report,keys.contains(&2));
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:92
pub fn multi_value_map__Values()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add(3,5);map.add_multiple(3,&[1,2]);map.add(6,1);
let mut values:Vec<&[i32]>=Vec::new();for value_span in map.values(){values.push(value_span);}eq!(report,values.len(),2);
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:107
pub fn multi_value_map__Items()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add_multiple(4,&[1,2,3]);for (&key,values) in map.items(){eq!(report,key,4);eq!(report,values.len(),3);eq!(report,values[0],1);eq!(report,values[1],2);eq!(report,values[2],3);}
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:123
pub fn multi_value_map__UniquePtr()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<OwnedKey<i32>,Box<i32>>::new();map.add(OwnedKey::new(4),Box::new(6));map.add(OwnedKey::new(4),Box::new(7));eq!(report,map.lookup(&OwnedKey::new(10)).len(),0);
report
}

// source/blender/blenlib/tests/BLI_multi_value_map_test.cc:132
pub fn multi_value_map__MutableItems()->Report{let mut report=Report::default();
let mut map=MultiValueMap::<i32,i32>::new();map.add(1,3);map.add(1,4);for (_,span) in map.items_mut(){yes!(report,span.contains(&3));yes!(report,span.contains(&4));}
report
}

// source/blender/blenlib/tests/BLI_generic_span_test.cc:19
pub fn GenericSpanTest__TypeConstructor()->Report{let mut report=Report::default();
generic_span_suite_setup();let span=GSpan::empty(registered_type::<f32>().unwrap());eq!(report,span.len(),0);eq!(report,span.typed::<f32>().unwrap().len(),0);yes!(report,span.is_empty());
report
}

// source/blender/blenlib/tests/BLI_generic_span_test.cc:27
pub fn GenericSpanTest__BufferAndSizeConstructor()->Report{let mut report=Report::default();
generic_span_suite_setup();let values=[6_i32,7,3,2];let buffer=values.as_ptr().cast::<u8>();
// SAFETY: live initialized i32 array, correct registered descriptor, lifetime and extent.
let span=unsafe{GSpan::from_raw_parts(registered_type::<i32>().unwrap(),buffer,4)};
eq!(report,span.len(),4);no!(report,span.is_empty());eq!(report,span.typed::<i32>().unwrap().len(),4);
peq!(report,span.pointer_at(0),values.as_ptr().wrapping_add(0));peq!(report,span.pointer_at(1),values.as_ptr().wrapping_add(1));peq!(report,span.pointer_at(2),values.as_ptr().wrapping_add(2));peq!(report,span.pointer_at(3),values.as_ptr().wrapping_add(3));
report
}

// source/blender/blenlib/tests/BLI_generic_span_test.cc:41
pub fn GenericSpanTest__MutableTypeConstructor()->Report{let mut report=Report::default();
generic_span_suite_setup();let span=GMutableSpan::empty(registered_type::<i32>().unwrap());eq!(report,span.len(),0);yes!(report,span.is_empty());
report
}

// source/blender/blenlib/tests/BLI_generic_span_test.cc:48
pub fn GenericSpanTest__MutableBufferAndSizeConstructor()->Report{let mut report=Report::default();
generic_span_suite_setup();let values=[4_i32,7,3,5].map(Cell::new);let buffer=values.as_ptr().cast::<i32>().cast_mut().cast::<u8>();
// SAFETY: Cell<i32> has i32 layout and permits writes; no shared i32 reference escapes.
let span=unsafe{GMutableSpan::from_raw_parts(registered_type::<i32>().unwrap(),buffer,4)};
eq!(report,span.len(),4);no!(report,span.is_empty());eq!(report,span.typed::<i32>().unwrap().len(),4);eq!(report,values[2].get(),3);
unsafe{span.pointer_at(2).cast::<i32>().write(10)};eq!(report,values[2].get(),10);
span.typed::<i32>().unwrap().set(2,20);eq!(report,values[2].get(),20);
report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("multi_value_map.LookupNotExistant",multi_value_map__LookupNotExistant,2),
("multi_value_map.LookupExistant",multi_value_map__LookupExistant,5),
("multi_value_map.LookupMutable",multi_value_map__LookupMutable,5),
("multi_value_map.AddMultiple",multi_value_map__AddMultiple,10),
("multi_value_map.Keys",multi_value_map__Keys,3),
("multi_value_map.Values",multi_value_map__Values,1),
("multi_value_map.Items",multi_value_map__Items,5),
("multi_value_map.UniquePtr",multi_value_map__UniquePtr,1),
("multi_value_map.MutableItems",multi_value_map__MutableItems,2),
("GenericSpanTest.TypeConstructor",GenericSpanTest__TypeConstructor,3),
("GenericSpanTest.BufferAndSizeConstructor",GenericSpanTest__BufferAndSizeConstructor,7),
("GenericSpanTest.MutableTypeConstructor",GenericSpanTest__MutableTypeConstructor,2),
("GenericSpanTest.MutableBufferAndSizeConstructor",GenericSpanTest__MutableBufferAndSizeConstructor,6),
];
