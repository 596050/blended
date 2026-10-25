// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Non-owning callable references adapted from pinned BLI_function_ref.hh.
// The replacement stores a thin pointer to the referenced callable plus a
// monomorphized trampoline. It does not own or extend the callable lifetime.
use core::marker::PhantomData;

pub struct FunctionRef0<'a,R>{
 callback:Option<unsafe fn(*mut())->R>,data:*mut (),_life:PhantomData<&'a mut ()>
}
impl<'a,R> Copy for FunctionRef0<'a,R>{}
impl<'a,R> Clone for FunctionRef0<'a,R>{fn clone(&self)->Self{*self}}
impl<'a,R> FunctionRef0<'a,R>{
 pub const fn empty()->Self{Self{callback:None,data:core::ptr::null_mut(),_life:PhantomData}}
 pub fn new<F:FnMut()->R+'a>(f:&'a mut F)->Self{
  unsafe fn thunk<F:FnMut()->R,R>(p:*mut())->R{unsafe{(&mut *(p as *mut F))()}}
  Self{callback:Some(thunk::<F,R>),data:(f as *mut F).cast(),_life:PhantomData}
 }
 pub fn is_some(&self)->bool{self.callback.is_some()}
 pub fn call(&mut self)->R{unsafe{self.callback.expect("calling empty FunctionRef")(self.data)}}
}
impl<'a,R> Default for FunctionRef0<'a,R>{fn default()->Self{Self::empty()}}

pub struct FunctionRef1<'a,A,R>{
 callback:Option<unsafe fn(*mut(),A)->R>,data:*mut (),_life:PhantomData<&'a mut ()>
}
impl<'a,A,R> Copy for FunctionRef1<'a,A,R>{}
impl<'a,A,R> Clone for FunctionRef1<'a,A,R>{fn clone(&self)->Self{*self}}
impl<'a,A,R> FunctionRef1<'a,A,R>{
 pub const fn empty()->Self{Self{callback:None,data:core::ptr::null_mut(),_life:PhantomData}}
 pub fn new<F:FnMut(A)->R+'a>(f:&'a mut F)->Self{
  unsafe fn thunk<F:FnMut(A)->R,A,R>(p:*mut(),a:A)->R{unsafe{(&mut *(p as *mut F))(a)}}
  Self{callback:Some(thunk::<F,A,R>),data:(f as *mut F).cast(),_life:PhantomData}
 }
 pub fn is_some(&self)->bool{self.callback.is_some()}
 pub fn call(&mut self,a:A)->R{unsafe{self.callback.expect("calling empty FunctionRef")(self.data,a)}}
}
impl<'a,A,R> Default for FunctionRef1<'a,A,R>{fn default()->Self{Self::empty()}}

pub struct FunctionRef2<'a,A,B,R>{
 callback:Option<unsafe fn(*mut(),A,B)->R>,data:*mut (),_life:PhantomData<&'a mut ()>
}
impl<'a,A,B,R> Copy for FunctionRef2<'a,A,B,R>{}
impl<'a,A,B,R> Clone for FunctionRef2<'a,A,B,R>{fn clone(&self)->Self{*self}}
impl<'a,A,B,R> FunctionRef2<'a,A,B,R>{
 pub const fn empty()->Self{Self{callback:None,data:core::ptr::null_mut(),_life:PhantomData}}
 pub fn new<F:FnMut(A,B)->R+'a>(f:&'a mut F)->Self{
  unsafe fn thunk<F:FnMut(A,B)->R,A,B,R>(p:*mut(),a:A,b:B)->R{unsafe{(&mut *(p as *mut F))(a,b)}}
  Self{callback:Some(thunk::<F,A,B,R>),data:(f as *mut F).cast(),_life:PhantomData}
 }
 pub fn is_some(&self)->bool{self.callback.is_some()}
 pub fn call(&mut self,a:A,b:B)->R{unsafe{self.callback.expect("calling empty FunctionRef")(self.data,a,b)}}
}
impl<'a,A,B,R> Default for FunctionRef2<'a,A,B,R>{fn default()->Self{Self::empty()}}
