// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Behavioural Rust adaptation of pinned BLI_multi_value_map.hh and
// BLI_generic_span.hh, 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Native hash-table layout/order and the full CPPType lifecycle API are not
// reproduced. Mutable views retain real storage, never detached snapshots.
use core::{any::{TypeId,type_name},borrow::Borrow,cell::Cell,hash::{Hash,Hasher},marker::PhantomData,mem::{align_of,size_of}};
use std::{collections::HashMap,sync::OnceLock};

#[derive(Debug,Clone)]
pub struct MultiValueMap<K,V>{buckets:HashMap<K,Vec<V>>}
impl<K:Eq+Hash,V> Default for MultiValueMap<K,V>{fn default()->Self{Self::new()}}
impl<K:Eq+Hash,V> MultiValueMap<K,V>{
 pub fn new()->Self{Self{buckets:HashMap::new()}}
 pub fn len(&self)->usize{self.buckets.len()}
 pub fn is_empty(&self)->bool{self.buckets.is_empty()}
 pub fn add(&mut self,key:K,value:V){self.buckets.entry(key).or_default().push(value);}
 pub fn add_multiple(&mut self,key:K,values:&[V]) where V:Clone{
  // Even an empty input creates a key, as the original header specifies.
  self.buckets.entry(key).or_default().extend_from_slice(values);
 }
 pub fn add_non_duplicates(&mut self,key:K,value:V) where V:PartialEq{
  let bucket=self.buckets.entry(key).or_default();if !bucket.contains(&value){bucket.push(value);}
 }
 pub fn lookup<Q:Eq+Hash+?Sized>(&self,key:&Q)->&[V] where K:Borrow<Q>{
  self.buckets.get(key).map(Vec::as_slice).unwrap_or(&[])
 }
 pub fn lookup_mut<Q:Eq+Hash+?Sized>(&mut self,key:&Q)->&mut[V] where K:Borrow<Q>{
  self.buckets.get_mut(key).map(Vec::as_mut_slice).unwrap_or(&mut[])
 }
 pub fn keys(&self)->impl Iterator<Item=&K>{self.buckets.keys()}
 pub fn values(&self)->impl Iterator<Item=&[V]>{self.buckets.values().map(Vec::as_slice)}
 pub fn values_mut(&mut self)->impl Iterator<Item=&mut[V]>{self.buckets.values_mut().map(Vec::as_mut_slice)}
 pub fn items(&self)->impl Iterator<Item=(&K,&[V])>{self.buckets.iter().map(|(k,v)|(k,v.as_slice()))}
 pub fn items_mut(&mut self)->impl Iterator<Item=(&K,&mut[V])>{self.buckets.iter_mut().map(|(k,v)|(k,v.as_mut_slice()))}
 pub fn clear(&mut self){self.buckets.clear();}
 pub fn clear_and_shrink(&mut self){self.buckets=HashMap::new();}
}
impl<K:Eq+Hash,V:PartialEq> PartialEq for MultiValueMap<K,V>{fn eq(&self,other:&Self)->bool{self.buckets==other.buckets}}
impl<K:Eq+Hash,V:Eq> Eq for MultiValueMap<K,V>{}

/// An owning pointer key with unique_ptr-style address identity. Rust Box alone
/// compares pointee values, which would incorrectly merge two equal allocations.
#[derive(Debug)]
pub struct OwnedKey<T>{value:Option<Box<T>>}
impl<T> OwnedKey<T>{
 pub fn new(value:T)->Self{Self{value:Some(Box::new(value))}}
 pub fn from_box(value:Box<T>)->Self{Self{value:Some(value)}}
 pub fn null()->Self{Self{value:None}}
 pub fn as_ptr(&self)->*const T{self.value.as_deref().map_or(core::ptr::null(),|v|v as *const T)}
 pub fn value(&self)->Option<&T>{self.value.as_deref()}
}
impl<T> PartialEq for OwnedKey<T>{fn eq(&self,other:&Self)->bool{core::ptr::eq(self.as_ptr(),other.as_ptr())}}
impl<T> Eq for OwnedKey<T>{}
impl<T> Hash for OwnedKey<T>{fn hash<H:Hasher>(&self,state:&mut H){self.as_ptr().hash(state);}}

#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub struct TypeDescriptor{id:TypeId,size:usize,alignment:usize,name:&'static str}
impl TypeDescriptor{
 pub fn of<T:Copy+'static>()->Self{Self{id:TypeId::of::<T>(),size:size_of::<T>(),alignment:align_of::<T>(),name:type_name::<T>()}}
 pub fn size(self)->usize{self.size}
 pub fn alignment(self)->usize{self.alignment}
 pub fn name(self)->&'static str{self.name}
 fn matches<T:'static>(self)->bool{self.id==TypeId::of::<T>()}
}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub enum TypeError{NotRegistered,TypeMismatch}
static TYPES:OnceLock<HashMap<TypeId,TypeDescriptor>>=OnceLock::new();
/// Idempotent fixture-visible registration of the exact primitive types used by
/// the original tests. Not a substitute for Blender's complete CPPType registry.
pub fn register_test_types(){TYPES.get_or_init(||{
 [TypeDescriptor::of::<i32>(),TypeDescriptor::of::<f32>()].into_iter().map(|d|(d.id,d)).collect()
});}
pub fn registered_type<T:'static>()->Result<TypeDescriptor,TypeError>{
 TYPES.get().and_then(|types|types.get(&TypeId::of::<T>())).copied().ok_or(TypeError::NotRegistered)
}
fn validate_extent(descriptor:TypeDescriptor,ptr:*const u8,len:usize){
 let bytes=len.checked_mul(descriptor.size).expect("Generic span byte length overflow");
 assert!(bytes<=isize::MAX as usize,"Generic span allocation exceeds addressable extent");
 assert!(len==0||!ptr.is_null(),"Nonempty generic span has null storage");
 assert!(ptr.is_null()||(ptr as usize)%descriptor.alignment==0,"Misaligned generic span");
}
#[derive(Clone,Copy,Debug)]
pub struct GSpan<'a>{descriptor:TypeDescriptor,ptr:*const u8,len:usize,_borrow:PhantomData<&'a Cell<u8>>}
impl<'a> GSpan<'a>{
 pub fn empty(descriptor:TypeDescriptor)->Self{Self{descriptor,ptr:core::ptr::null(),len:0,_borrow:PhantomData}}
 pub fn from_slice<T:Copy+'static>(values:&'a[T])->Self{
  Self{descriptor:TypeDescriptor::of::<T>(),ptr:values.as_ptr().cast(),len:values.len(),_borrow:PhantomData}
 }
 /// # Safety
 /// `ptr` must describe `len` initialized values of exactly `descriptor`'s type,
 /// live for 'a. Any mutation during 'a must obey Rust's aliasing rules; no shared
 /// reference to an externally mutable plain T may coexist with those writes.
 pub unsafe fn from_raw_parts(descriptor:TypeDescriptor,ptr:*const u8,len:usize)->Self{
  validate_extent(descriptor,ptr,len);Self{descriptor,ptr,len,_borrow:PhantomData}
 }
 pub fn len(self)->usize{self.len}
 pub fn is_empty(self)->bool{self.len==0}
 pub fn descriptor(self)->TypeDescriptor{self.descriptor}
 pub fn pointer_at(self,index:usize)->*const u8{
  assert!(index<self.len,"Generic span index out of bounds");
  // SAFETY: constructors promise a live extent; bounds and checked extent above.
  unsafe{self.ptr.add(index*self.descriptor.size)}
 }
 pub fn typed<T:Copy+'static>(self)->Result<TypedSpan<'a,T>,TypeError>{
  if !self.descriptor.matches::<T>(){return Err(TypeError::TypeMismatch);}
  Ok(TypedSpan{ptr:self.ptr.cast(),len:self.len,_borrow:PhantomData})
 }
}
#[derive(Clone,Copy,Debug)]
pub struct TypedSpan<'a,T:Copy>{ptr:*const T,len:usize,_borrow:PhantomData<&'a Cell<T>>}
impl<T:Copy> TypedSpan<'_,T>{
 pub fn len(self)->usize{self.len}
 pub fn is_empty(self)->bool{self.len==0}
 pub fn get(self,index:usize)->T{assert!(index<self.len);unsafe{self.ptr.add(index).read()}}
 pub fn data(self)->*const T{self.ptr}
}
#[derive(Clone,Copy,Debug)]
pub struct GMutableSpan<'a>{view:GSpan<'a>}
impl<'a> GMutableSpan<'a>{
 pub fn empty(descriptor:TypeDescriptor)->Self{Self{view:GSpan::empty(descriptor)}}
 pub fn from_cells<T:Copy+'static>(values:&'a[Cell<T>])->Self{
  // Cell has T's layout and supports these copy accesses without exposing &T.
  Self{view:GSpan{descriptor:TypeDescriptor::of::<T>(),ptr:values.as_ptr().cast(),len:values.len(),_borrow:PhantomData}}
 }
 pub fn from_mut_slice<T:Copy+'static>(values:&'a mut[T])->Self{Self::from_cells(Cell::from_mut(values).as_slice_of_cells())}
 /// # Safety
 /// As for GSpan::from_raw_parts, plus the entire extent must permit writes for
 /// 'a (exclusive borrow or Cell-compatible storage). No incompatible references
 /// may escape. Checked size/alignment do not prove the pointer's allocation.
 pub unsafe fn from_raw_parts(descriptor:TypeDescriptor,ptr:*mut u8,len:usize)->Self{
  Self{view:unsafe{GSpan::from_raw_parts(descriptor,ptr,len)}}
 }
 pub fn len(self)->usize{self.view.len}
 pub fn is_empty(self)->bool{self.view.is_empty()}
 pub fn as_readonly(self)->GSpan<'a>{self.view}
 pub fn pointer_at(self,index:usize)->*mut u8{self.view.pointer_at(index).cast_mut()}
 pub fn typed<T:Copy+'static>(self)->Result<TypedMutableSpan<'a,T>,TypeError>{
  Ok(TypedMutableSpan{view:self.view.typed()?})
 }
}
#[derive(Clone,Copy,Debug)]
pub struct TypedMutableSpan<'a,T:Copy>{view:TypedSpan<'a,T>}
impl<T:Copy> TypedMutableSpan<'_,T>{
 pub fn len(self)->usize{self.view.len}
 pub fn is_empty(self)->bool{self.view.is_empty()}
 pub fn get(self,index:usize)->T{self.view.get(index)}
 pub fn set(self,index:usize,value:T){assert!(index<self.view.len);unsafe{self.view.ptr.cast_mut().add(index).write(value)}}
}
