// SPDX-License-Identifier: GPL-3.0-or-later
//! Column-major numeric matrices and checked borrowed submatrix views.
//!
//! Owned matrices have value semantics. Mutable views use Cell-backed storage so
//! overlapping views remain live without unsound aliasing of mutable references.
use crate::numeric_vectors::{Scalar,V};
use std::cell::Cell;
use std::ops::*;

pub trait Real:Scalar+PartialEq+PartialOrd+Add<Output=Self>+Sub<Output=Self>+Mul<Output=Self>+Div<Output=Self>+Neg<Output=Self>{
    fn sqrt(self)->Self;
    fn threshold()->Self;
}
impl Real for f32{fn sqrt(self)->Self{self.sqrt()}fn threshold()->Self{1.0e-35}}
impl Real for f64{fn sqrt(self)->Self{self.sqrt()}fn threshold()->Self{1.0e-70}}
#[repr(transparent)]
#[derive(Debug,Clone,Copy,PartialEq)]
pub struct M<T,const C:usize,const R:usize>(pub [V<T,R>;C]);
impl<T:Real,const C:usize,const R:usize> M<T,C,R>{
    pub fn from_cols(columns:[V<T,R>;C])->Self{assert!(C>0&&R>0);Self(columns)}
    pub fn zero()->Self{Self::all(0.0)}
    pub fn all(value:f64)->Self{Self([V::splat(T::from_f64(value));C])}
    pub fn identity()->Self{Self::diagonal(1.0)}
    pub fn diagonal(value:f64)->Self{Self(core::array::from_fn(|c|V(core::array::from_fn(|r|T::from_f64(if c==r{value}else{0.0})))))}
    pub fn get(&self,column:usize,row:usize)->T{self.0[column].0[row]}
    pub fn from_matrix<U:Real,const C2:usize,const R2:usize>(other:&M<U,C2,R2>)->Self{
        Self(core::array::from_fn(|c|V(core::array::from_fn(|r|{
            if c<C2&&r<R2{T::from_f64(other.get(c,r).to_f64())}else{T::from_f64(if c==r{1.0}else{0.0})}
        }))))
    }
    pub fn from_flat<U:Real>(values:&[U])->Self{
        assert!(values.len()>=C.checked_mul(R).expect("Matrix size overflow"));
        Self(core::array::from_fn(|c|V(core::array::from_fn(|r|T::from_f64(values[c*R+r].to_f64())))))
    }
    pub fn from_array<U:Real>(values:&[[U;R];C])->Self{
        Self(core::array::from_fn(|c|V(core::array::from_fn(|r|T::from_f64(values[c][r].to_f64())))))
    }
}
impl<T:Real,const C:usize,const R:usize> Default for M<T,C,R>{fn default()->Self{Self::zero()}}
macro_rules! matrix_elementwise{
 ($trait:ident,$method:ident,$assign:ident,$assign_method:ident,$op:tt)=>{
  impl<T:Real,const C:usize,const R:usize> $trait for M<T,C,R>{type Output=Self;fn $method(self,b:Self)->Self{Self(core::array::from_fn(|c|V(core::array::from_fn(|r|self.get(c,r) $op b.get(c,r)))))} }
  impl<T:Real,const C:usize,const R:usize> $assign for M<T,C,R>{fn $assign_method(&mut self,b:Self){*self=*self $op b;}}
 };
}
matrix_elementwise!(Add,add,AddAssign,add_assign,+);
matrix_elementwise!(Sub,sub,SubAssign,sub_assign,-);
impl<T:Real,const C:usize,const R:usize> Neg for M<T,C,R>{type Output=Self;fn neg(self)->Self{Self(self.0.map(|v|-v))}}
macro_rules! scalar_op{
 ($s:ty,$trait:ident,$method:ident,$assign:ident,$assign_method:ident,$op:tt)=>{
  impl<T:Real,const C:usize,const R:usize> $trait<$s> for M<T,C,R>{type Output=Self;fn $method(self,b:$s)->Self{let b=T::from_f64(b as f64);Self(self.0.map(|v|V(v.0.map(|a|a $op b))))}}
  impl<T:Real,const C:usize,const R:usize> $assign<$s> for M<T,C,R>{fn $assign_method(&mut self,b:$s){*self=*self $op b;}}
  impl<T:Real,const C:usize,const R:usize> $trait<M<T,C,R>> for $s{type Output=M<T,C,R>;fn $method(self,b:M<T,C,R>)->Self::Output{let a=T::from_f64(self as f64);M(b.0.map(|v|V(v.0.map(|b|a $op b))))}}
 };
}
macro_rules! scalar_ops {($s:ty)=>{
 scalar_op!($s,Add,add,AddAssign,add_assign,+);
 scalar_op!($s,Sub,sub,SubAssign,sub_assign,-);
 scalar_op!($s,Mul,mul,MulAssign,mul_assign,*);
 scalar_op!($s,Div,div,DivAssign,div_assign,/);
};}
scalar_ops!(f32);scalar_ops!(f64);scalar_ops!(i32);
impl<T:Real,const C:usize,const R:usize,const K:usize> Mul<M<T,K,C>> for M<T,C,R>{
 type Output=M<T,K,R>;
 fn mul(self,b:M<T,K,C>)->Self::Output{
  assert!(C>0);
  M(core::array::from_fn(|c|V(core::array::from_fn(|r|{
   let mut value=self.get(0,r)*b.get(c,0);
   for i in 1..C{value=value+self.get(i,r)*b.get(c,i);}value
  }))))
 }
}
impl<T:Real,const N:usize> MulAssign for M<T,N,N>{fn mul_assign(&mut self,b:Self){*self=*self*b;}}
impl<T:Real,const C:usize,const R:usize> Mul<V<T,C>> for M<T,C,R>{type Output=V<T,R>;
 fn mul(self,b:V<T,C>)->Self::Output{assert!(C>0);V(core::array::from_fn(|r|{let mut v=self.get(0,r)*b[0];for c in 1..C{v=v+self.get(c,r)*b[c];}v}))}
}
impl<T:Real,const C:usize,const R:usize> Mul<M<T,C,R>> for V<T,R>{type Output=V<T,C>;
 fn mul(self,b:M<T,C,R>)->Self::Output{assert!(R>0);V(core::array::from_fn(|c|{let mut v=self[0]*b.get(c,0);for r in 1..R{v=v+self[r]*b.get(c,r);}v}))}
}

pub fn cell_storage<T:Copy,const C:usize,const R:usize>(values:[[T;R];C])->[[Cell<T>;R];C]{values.map(|v|v.map(Cell::new))}
#[derive(Debug)]
pub struct Shared<T:Copy,const C:usize,const R:usize>{data:[[Cell<T>;R];C]}
impl<T:Real,const C:usize,const R:usize> Shared<T,C,R>{
 pub fn new(matrix:M<T,C,R>)->Self{Self{data:cell_storage(matrix.0.map(|v|v.0))}}
 pub fn get(&self,c:usize,r:usize)->T{self.data[c][r].get()}
 pub fn view<const VC:usize,const VR:usize>(&self,c:usize,r:usize)->View<'_,T,VC,VR,C,R>{View::new(&self.data,c,r)}
}
#[derive(Debug,Clone,Copy)]
pub struct View<'a,T:Copy,const C:usize,const R:usize,const SC:usize,const SR:usize>{data:&'a[[Cell<T>;SR];SC],column:usize,row:usize}
impl<'a,T:Real,const C:usize,const R:usize,const SC:usize,const SR:usize> View<'a,T,C,R,SC,SR>{
 pub fn new(data:&'a[[Cell<T>;SR];SC],column:usize,row:usize)->Self{
  assert!(column<=SC&&C<=SC-column&&row<=SR&&R<=SR-row,"Submatrix view exceeds backing storage");
  Self{data,column,row}
 }
 pub fn get(&self,c:usize,r:usize)->T{assert!(c<C&&r<R);self.data[self.column+c][self.row+r].get()}
 pub fn read(&self)->M<T,C,R>{M(core::array::from_fn(|c|V(core::array::from_fn(|r|self.get(c,r)))))}
 pub fn assign(&self,rhs:M<T,C,R>){
  // rhs is an independent evaluated value, so self-overlap cannot change later reads.
  for c in 0..C{for r in 0..R{self.data[self.column+c][self.row+r].set(rhs.get(c,r));}}
 }
}
pub fn normalize<T:Real,const C:usize,const R:usize>(matrix:M<T,C,R>)->M<T,C,R>{
 assert!(R>0);
 M(matrix.0.map(|column|{
  let mut sum=column[0]*column[0];for i in 1..R{sum=sum+column[i]*column[i];}
  if sum>T::threshold(){let length=sum.sqrt();V(column.0.map(|v|v/length))}else{V::splat(T::from_f64(0.0))}
 }))
}

/// Read-only access to shared backing. Unlike View, this type exposes no write method.
#[derive(Debug,Clone,Copy)]
pub struct ReadView<'a,T:Copy,const C:usize,const R:usize,const SC:usize,const SR:usize>(View<'a,T,C,R,SC,SR>);
impl<'a,T:Real,const C:usize,const R:usize,const SC:usize,const SR:usize> ReadView<'a,T,C,R,SC,SR>{
 pub fn new(data:&'a[[Cell<T>;SR];SC],column:usize,row:usize)->Self{Self(View::new(data,column,row))}
 pub fn get(&self,c:usize,r:usize)->T{self.0.get(c,r)}
 pub fn read(&self)->M<T,C,R>{self.0.read()}
}
