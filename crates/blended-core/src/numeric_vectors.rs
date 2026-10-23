// SPDX-License-Identifier: GPL-3.0-or-later
//! Fixed-size numeric vectors and explicitly evaluated swizzle reads/write-backs.
//! Values are stored contiguously. Writes read their RHS before changing storage.
use core::ops::*;

#[repr(transparent)]
#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub struct V<T,const N:usize>(pub [T;N]);
pub trait Scalar:Copy {fn from_f64(x:f64)->Self;fn to_f64(self)->f64;}
macro_rules! scalar {($($t:ty),*)=>{$(impl Scalar for $t{fn from_f64(x:f64)->Self{x as $t}fn to_f64(self)->f64{self as f64}})*};}
scalar!(f32,f64,i32,u32);
pub trait Components {fn components(&self,out:&mut Vec<f64>);}
macro_rules! components {($($t:ty),*)=>{$(impl Components for $t{fn components(&self,out:&mut Vec<f64>){out.push(*self as f64)}})*};}
components!(f32,f64,i32,u32);
impl<T:Scalar,const N:usize> Components for V<T,N>{fn components(&self,out:&mut Vec<f64>){out.extend(self.0.iter().map(|v|v.to_f64()));}}
impl<T:Scalar,const N:usize> Components for [T;N]{fn components(&self,out:&mut Vec<f64>){out.extend(self.iter().map(|v|v.to_f64()));}}
impl<T:Components+?Sized> Components for &T{fn components(&self,out:&mut Vec<f64>){(*self).components(out)}}
/// Broadcasting and component conversion. Supported scalar types are at most 32-bit
/// integers, so the f64 interchange retains every integer exactly.
pub fn construct<T:Scalar,const N:usize>(parts:&[&dyn Components])->V<T,N>{
    assert!(N>0);let mut scalars=Vec::with_capacity(N);
    for part in parts {part.components(&mut scalars);}
    assert!(scalars.len()==1||scalars.len()>=N,"Too few vector components");
    V(core::array::from_fn(|i|T::from_f64(scalars[if scalars.len()==1{0}else{i}])))
}
impl<T:Copy,const N:usize> V<T,N>{
    pub const fn splat(value:T)->Self{Self([value;N])}
    pub fn swizzle<const M:usize>(&self,indices:[usize;M])->V<T,M>{V(indices.map(|i|self.0[i]))}
    pub fn set_swizzle<const M:usize>(&mut self,indices:[usize;M],value:V<T,M>){
        // Evaluate the RHS before mutation, including overlapping components.
        for (i,v) in indices.into_iter().zip(value.0) {self.0[i]=v;}
    }
    pub const fn component(&self,index:usize)->T{self.0[index]}
}
impl<T,const N:usize> Index<usize> for V<T,N>{type Output=T;fn index(&self,i:usize)->&T{&self.0[i]}}
impl<T,const N:usize> IndexMut<usize> for V<T,N>{fn index_mut(&mut self,i:usize)->&mut T{&mut self.0[i]}}
macro_rules! operator {
 ($trait:ident,$method:ident,$assign:ident,$assign_method:ident,$op:tt)=>{
  impl<T:Copy+$trait<Output=T>,const N:usize> $trait for V<T,N>{type Output=Self;fn $method(self,rhs:Self)->Self{V(core::array::from_fn(|i|self.0[i] $op rhs.0[i]))}}
  impl<T:Copy+$trait<Output=T>,const N:usize> $trait<T> for V<T,N>{type Output=Self;fn $method(self,rhs:T)->Self{V(self.0.map(|v|v $op rhs))}}
  impl<T:Copy+$trait<Output=T>,const N:usize> $assign for V<T,N>{fn $assign_method(&mut self,rhs:Self){*self=*self $op rhs;}}
  impl<T:Copy+$trait<Output=T>,const N:usize> $assign<T> for V<T,N>{fn $assign_method(&mut self,rhs:T){*self=*self $op rhs;}}
 };
}
operator!(Add,add,AddAssign,add_assign,+);operator!(Sub,sub,SubAssign,sub_assign,-);
operator!(Mul,mul,MulAssign,mul_assign,*);operator!(Div,div,DivAssign,div_assign,/);
operator!(BitAnd,bitand,BitAndAssign,bitand_assign,&);operator!(BitOr,bitor,BitOrAssign,bitor_assign,|);
operator!(BitXor,bitxor,BitXorAssign,bitxor_assign,^);operator!(Shl,shl,ShlAssign,shl_assign,<<);operator!(Shr,shr,ShrAssign,shr_assign,>>);
impl<T:Copy+Neg<Output=T>,const N:usize> Neg for V<T,N>{type Output=Self;fn neg(self)->Self{V(self.0.map(|v|-v))}}
impl<T:Copy+Not<Output=T>,const N:usize> Not for V<T,N>{type Output=Self;fn not(self)->Self{V(self.0.map(|v|!v))}}
macro_rules! scalar_left {($($t:ty),*)=>{$(
 impl<const N:usize> Add<V<$t,N>> for $t{type Output=V<$t,N>;fn add(self,r:V<$t,N>)->Self::Output{V(r.0.map(|x|self+x))}}
 impl<const N:usize> Sub<V<$t,N>> for $t{type Output=V<$t,N>;fn sub(self,r:V<$t,N>)->Self::Output{V(r.0.map(|x|self-x))}}
 impl<const N:usize> Mul<V<$t,N>> for $t{type Output=V<$t,N>;fn mul(self,r:V<$t,N>)->Self::Output{V(r.0.map(|x|self*x))}}
 impl<const N:usize> Div<V<$t,N>> for $t{type Output=V<$t,N>;fn div(self,r:V<$t,N>)->Self::Output{V(r.0.map(|x|self/x))}}
 )*};}
scalar_left!(f32,f64,i32,u32);
