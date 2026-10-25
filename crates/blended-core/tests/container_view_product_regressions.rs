// SPDX-License-Identifier: GPL-3.0-or-later
// Supplemental product/safety tests, not original Blender case counts.
use blended_core::container_views::*;
use core::cell::Cell;
use std::rc::Rc;
#[test]
fn empty_bucket_is_a_real_key_and_missing_lookup_is_not(){
 let mut m=MultiValueMap::<i32,i32>::new();assert!(m.lookup(&1).is_empty());assert!(m.lookup_mut(&1).is_empty());assert!(m.is_empty());
 m.add_multiple(1,&[]);assert_eq!(m.len(),1);assert!(!m.is_empty());assert!(m.lookup(&1).is_empty());
}
#[test]
fn insertion_order_duplicates_and_live_bucket_changes_are_preserved(){
 let mut m=MultiValueMap::new();m.add_multiple(3,&[2,2,1]);m.lookup_mut(&3)[1]=8;m.add(3,2);m.add_non_duplicates(3,2);assert_eq!(m.lookup(&3),[2,8,1,2]);
 for(_,v)in m.items_mut(){v[0]=7;}assert_eq!(m.lookup(&3),[7,8,1,2]);
}
#[test]
fn equal_pointees_do_not_merge_distinct_owned_pointer_keys(){
 let a=OwnedKey::new(4);let b=OwnedKey::new(4);assert_ne!(a.as_ptr(),b.as_ptr());assert_ne!(a,b);
 let mut m=MultiValueMap::new();m.add(a,6);m.add(b,7);assert_eq!(m.len(),2);
 let mut values:Vec<i32>=m.values().flatten().copied().collect();values.sort();assert_eq!(values,[6,7]);
 m.add(OwnedKey::null(),3);m.add(OwnedKey::null(),4);assert_eq!(m.lookup(&OwnedKey::null()),[3,4]);
}
#[test]
fn owning_keys_and_values_are_dropped_exactly_once(){
 struct Dropper(Rc<Cell<i32>>);impl Drop for Dropper{fn drop(&mut self){self.0.set(self.0.get()+1);}}
 let keys=Rc::new(Cell::new(0));let values=Rc::new(Cell::new(0));
 {let mut m=MultiValueMap::new();for _ in 0..2{m.add(OwnedKey::new(Dropper(keys.clone())),Box::new(Dropper(values.clone())));}assert_eq!((keys.get(),values.get()),(0,0));m.clear();assert_eq!((keys.get(),values.get()),(2,2));}
 assert_eq!((keys.get(),values.get()),(2,2));
}
#[test]
fn same_size_different_type_is_rejected_even_for_empty_views(){
 let ints=[1_i32,2];let s=GSpan::from_slice(&ints);assert!(matches!(s.typed::<f32>(),Err(TypeError::TypeMismatch)));
 let e=GSpan::empty(TypeDescriptor::of::<i32>());assert!(matches!(e.typed::<f32>(),Err(TypeError::TypeMismatch)));assert!(e.typed::<i32>().unwrap().is_empty());
}
#[test]
fn readonly_alias_sees_typed_and_external_cell_mutation(){
 let values=[1_i32,2,3].map(Cell::new);let m=GMutableSpan::from_cells(&values);let read=m.as_readonly().typed::<i32>().unwrap();m.typed::<i32>().unwrap().set(1,19);assert_eq!(read.get(1),19);values[1].set(27);assert_eq!(read.get(1),27);
 assert_eq!(m.pointer_at(2),values.as_ptr().wrapping_add(2).cast_mut().cast::<u8>());
}
#[test]
fn type_erasure_retains_alignment_and_copy_values(){
 #[repr(align(64))]#[derive(Clone,Copy,Debug,PartialEq)]struct Aligned(u64);
 let values=[Aligned(91),Aligned(37)];let s=GSpan::from_slice(&values);assert_eq!(s.descriptor().alignment(),64);assert_eq!(s.typed::<Aligned>().unwrap().get(1),Aligned(37));assert!(s.typed::<u64>().is_err());
 assert_eq!(s.pointer_at(1) as usize-s.pointer_at(0) as usize,64);
}
#[test]
fn cloned_buckets_are_independent(){
 let mut original=MultiValueMap::new();original.add_multiple(4,&[1,2,3]);let mut copy=original.clone();copy.lookup_mut(&4)[0]=9;copy.add(4,8);assert_eq!(original.lookup(&4),[1,2,3]);assert_eq!(copy.lookup(&4),[9,2,3,8]);
}
#[test]
fn borrowed_key_lookup_and_clear_work_without_inserting(){
 let mut map=MultiValueMap::<String,i32>::new();map.add("word".into(),3);assert_eq!(map.lookup("word"),[3]);assert!(map.lookup("absent").is_empty());assert_eq!(map.len(),1);map.clear_and_shrink();assert!(map.is_empty());map.add("word".into(),7);assert_eq!(map.lookup("word"),[7]);
}
#[test]
fn registry_setup_is_idempotent_and_descriptors_are_exact(){
 register_test_types();let a=registered_type::<i32>().unwrap();register_test_types();assert_eq!(a,registered_type::<i32>().unwrap());assert_ne!(a,registered_type::<f32>().unwrap());assert_eq!(a.size(),4);assert_eq!(registered_type::<u64>(),Err(TypeError::NotRegistered));
}
