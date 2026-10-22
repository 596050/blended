// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Range and bounding-box contracts corresponding to the pinned Blender BLI sources.
//! Rust allocation/iteration APIs replace C++ containers, not their observable values.
use core::fmt::Debug;
use core::ops::{Add, Div, Mul, Neg, Sub};

#[derive(Clone, Copy, Debug, Default)]
pub struct IndexRange { start: i64, size: i64 }
impl PartialEq for IndexRange {
    fn eq(&self, other: &Self) -> bool {
        self.size == other.size && (self.size == 0 || self.start == other.start)
    }
}
impl Eq for IndexRange {}
impl IndexRange {
    pub const fn new(start: i64, size: i64) -> Self {
        assert!(start >= 0 && size >= 0, "Negative index range");
        assert!(start <= i64::MAX - size, "Index range overflows");
        Self { start, size }
    }
    pub const fn empty() -> Self { Self::new(0, 0) }
    pub const fn from_size(size: i64) -> Self { Self::new(0, size) }
    pub const fn from_begin_size(begin: i64, size: i64) -> Self { Self::new(begin, size) }
    pub const fn from_begin_end(begin: i64, end: i64) -> Self {
        assert!(begin >= 0 && end >= begin); Self::new(begin, end - begin)
    }
    pub const fn from_begin_end_inclusive(begin: i64, last: i64) -> Self {
        assert!(begin >= 0 && last >= begin && last < i64::MAX);
        Self::new(begin, last - begin + 1)
    }
    pub const fn from_end_size(end: i64, size: i64) -> Self {
        assert!(size >= 0 && end >= size); Self::new(end - size, size)
    }
    pub const fn from_single(index: i64) -> Self { Self::new(index, 1) }
    pub const fn start(self) -> i64 { self.start }
    pub const fn size(self) -> i64 { self.size }
    pub const fn is_empty(self) -> bool { self.size == 0 }
    pub const fn get(self, index: i64) -> i64 {
        assert!(index >= 0 && index < self.size, "Index outside range"); self.start + index
    }
    pub const fn first(self) -> i64 { self.get(0) }
    pub const fn last(self) -> i64 { self.get(self.size - 1) }
    pub const fn one_after_last(self) -> i64 { self.start + self.size }
    pub const fn one_before_start(self) -> i64 { assert!(self.start > 0); self.start - 1 }
    pub fn iter(self) -> core::ops::Range<i64> { self.start..self.one_after_last() }
    pub const fn contains(self, value: i64) -> bool { value >= self.start && value < self.one_after_last() }
    pub const fn before(self, size: i64) -> Self { assert!(size >= 0 && size <= self.start); Self::new(self.start-size, size) }
    pub const fn after(self, size: i64) -> Self { Self::new(self.one_after_last(), size) }
    pub const fn slice(self, start: i64, size: i64) -> Self {
        assert!(start >= 0 && size >= 0);
        assert!(size == 0 || (start <= self.size && size <= self.size-start));
        assert!(start <= i64::MAX-self.start);
        Self::new(self.start+start, size)
    }
    pub const fn slice_range(self, range: Self) -> Self { self.slice(range.start, range.size) }
    pub const fn intersect(self, other: Self) -> Self {
        let old_end=self.one_after_last();
        let lower=if self.start > other.start {self.start} else {other.start};
        let start=if old_end < lower {old_end} else {lower};
        let upper=if old_end < other.one_after_last() {old_end} else {other.one_after_last()};
        let end=if start > upper {start} else {upper};
        Self::new(start,end-start)
    }
    pub const fn drop_front(self, n: i64) -> Self {
        assert!(n >= 0 && n <= i64::MAX-self.start);
        Self::new(self.start+n, if n > self.size {0} else {self.size-n})
    }
    pub const fn drop_back(self, n: i64) -> Self {
        assert!(n >= 0); Self::new(self.start, if n > self.size {0} else {self.size-n})
    }
    pub const fn take_front(self, n: i64) -> Self {
        assert!(n >= 0); Self::new(self.start, if n < self.size {n} else {self.size})
    }
    pub const fn take_back(self, n: i64) -> Self {
        assert!(n >= 0); let size=if n < self.size {n} else {self.size};
        Self::new(self.one_after_last()-size,size)
    }
}
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct AlignedIndexRanges { pub prefix: IndexRange, pub aligned: IndexRange, pub suffix: IndexRange }
pub fn split_index_range_by_alignment(range: IndexRange, alignment: i64) -> AlignedIndexRanges {
    assert!(alignment > 0 && alignment & (alignment-1) == 0, "Alignment must be a positive power of two");
    let mask=alignment-1;
    let start_chunk=range.start() & !mask;
    let end_chunk=range.one_after_last() & !mask;
    if start_chunk==end_chunk { return AlignedIndexRanges { prefix:range,..Default::default() }; }
    let prefix_size=if range.start()!=start_chunk {alignment-(range.start() & mask)} else {0};
    let suffix_size=range.one_after_last()-end_chunk;
    AlignedIndexRanges {
        prefix:IndexRange::new(range.start(),prefix_size),
        aligned:IndexRange::new(range.start()+prefix_size,range.size()-prefix_size-suffix_size),
        suffix:IndexRange::new(end_chunk,suffix_size),
    }
}
/// Predicate must be false then true. Returns length when it is never true.
pub fn first_if<T>(values:&[T],mut predicate:impl FnMut(&T)->bool)->i64 {
    values.partition_point(|v|!predicate(v)) as i64
}
/// Predicate must be true then false. Returns -1 when it is never true.
pub fn last_if<T>(values:&[T],mut predicate:impl FnMut(&T)->bool)->i64 {
    values.partition_point(|v|predicate(v)) as i64-1
}

pub trait Scalar: Copy+Debug+PartialOrd+Add<Output=Self>+Sub<Output=Self>+Mul<Output=Self>+Div<Output=Self>+Neg<Output=Self> {
    const ZERO:Self; const ONE:Self; const TWO:Self;
    fn absolute(self)->Self;
    fn midpoint(a:Self,b:Self)->Self;
    fn cross_greater(a:Self,b:Self,c:Self,d:Self)->bool;
}
impl Scalar for f32 {
    const ZERO:Self=0.0;const ONE:Self=1.0;const TWO:Self=2.0;
    fn absolute(self)->Self {self.abs()}
    fn midpoint(a:Self,b:Self)->Self {(a+b)*0.5}
    fn cross_greater(a:Self,b:Self,c:Self,d:Self)->bool {a*b>c*d}
}
impl Scalar for i32 {
    const ZERO:Self=0;const ONE:Self=1;const TWO:Self=2;
    fn absolute(self)->Self {self.checked_abs().expect("Integer bounds size overflows")}
    fn midpoint(a:Self,b:Self)->Self {(a as i64+(b as i64-a as i64)/2) as i32}
    // Widen integer products so valid rational comparisons do not overflow.
    fn cross_greater(a:Self,b:Self,c:Self,d:Self)->bool {(a as i64)*(b as i64)>(c as i64)*(d as i64)}
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct VecN<T,const N:usize>(pub [T;N]);
impl<T:Copy,const N:usize> From<T> for VecN<T,N> {fn from(value:T)->Self {Self([value;N])}}
impl<T:Scalar,const N:usize> Mul for VecN<T,N> {
    type Output=Self;
    fn mul(self,rhs:Self)->Self {Self(core::array::from_fn(|i|self.0[i]*rhs.0[i]))}
}
pub trait BoundValue: Copy+Debug+PartialEq {
    type S:Scalar;
    const DIMENSIONS:usize;
    fn component(self,index:usize)->Self::S;
    fn from_fn(f:impl FnMut(usize)->Self::S)->Self;
    fn map(self,mut f:impl FnMut(Self::S)->Self::S)->Self {Self::from_fn(|i|f(self.component(i)))}
    fn zip(self,other:Self,mut f:impl FnMut(Self::S,Self::S)->Self::S)->Self {Self::from_fn(|i|f(self.component(i),other.component(i)))}
}
macro_rules! scalar_bounds {
    ($t:ty)=>{impl BoundValue for $t {
        type S=$t;const DIMENSIONS:usize=1;
        fn component(self,index:usize)->Self::S {assert_eq!(index,0);self}
        fn from_fn(mut f:impl FnMut(usize)->Self::S)->Self {f(0)}
    }};
}
scalar_bounds!(f32);scalar_bounds!(i32);
impl<T:Scalar,const N:usize> BoundValue for VecN<T,N> {
    type S=T;const DIMENSIONS:usize=N;
    fn component(self,index:usize)->T {self.0[index]}
    fn from_fn(f:impl FnMut(usize)->T)->Self {assert!(N>0);Self(core::array::from_fn(f))}
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Bounds<T> {pub min:T,pub max:T}
impl<T:BoundValue> Bounds<T> {
    pub fn new(min:T,max:T)->Self {assert!(T::DIMENSIONS>0);Self{min,max}}
    pub fn point(value:T)->Self {Self::new(value,value)}
    pub fn is_empty(self)->bool {(0..T::DIMENSIONS).any(|i|self.max.component(i)<=self.min.component(i))}
    pub fn center(self)->T {self.min.zip(self.max,T::S::midpoint)}
    pub fn size(self)->T {self.max.zip(self.min,|a,b|(a-b).absolute())}
    pub fn translate(&mut self,offset:T) {self.min=self.min.zip(offset,|a,b|a+b);self.max=self.max.zip(offset,|a,b|a+b);}
    pub fn scale_from_center(&mut self,scale:T) {
        let center=self.center();let half=self.size().zip(scale,|a,b|a/T::S::TWO*b);
        self.min=center.zip(half,|a,b|a-b);self.max=center.zip(half,|a,b|a+b);
    }
    pub fn resize(&mut self,size:T) {
        self.min=self.center().zip(size,|a,b|a-b/T::S::TWO);
        self.max=self.min.zip(size,|a,b|a+b);
    }
    pub fn recenter(&mut self,center:T) {self.translate(center.zip(self.center(),|a,b|a-b));}
    pub fn pad<P:Into<T>>(&mut self,padding:P) {
        let p=padding.into();self.min=self.min.zip(p,|a,b|a-b);self.max=self.max.zip(p,|a,b|a+b);
    }
    pub fn contains(self,point:T)->bool {
        !(0..T::DIMENSIONS).any(|i|point.component(i)<self.min.component(i)||point.component(i)>self.max.component(i))
    }
    /// Liang-Barsky clipping with rational comparisons, including parallel and point segments.
    pub fn intersects_segment(self,start:T,end:T)->bool {
        if self.contains(start)||self.contains(end) {return true;}
        let (mut p_enter,mut q_enter,mut p_exit,mut q_exit)=(T::S::ZERO,T::S::ONE,T::S::ONE,T::S::ONE);
        for i in 0..T::DIMENSIONS {
            let s=start.component(i);let d=end.component(i)-s;
            let lo=self.min.component(i);let hi=self.max.component(i);
            if d==T::S::ZERO {if s<lo||s>hi {return false;} continue;}
            let (low,high,den)=if d>T::S::ZERO {(lo-s,hi-s,d)} else {(-(hi-s),-(lo-s),-d)};
            if T::S::cross_greater(low,q_enter,p_enter,den) {p_enter=low;q_enter=den;}
            if T::S::cross_greater(p_exit,den,high,q_exit) {p_exit=high;q_exit=den;}
            if T::S::cross_greater(p_enter,q_exit,p_exit,q_enter) {return false;}
        }
        p_exit>=T::S::ZERO&&p_enter<=q_enter
    }
    pub fn merge(self,other:Self)->Self {
        Self::new(self.min.zip(other.min,|a,b|if b<a {b} else {a}),self.max.zip(other.max,|a,b|if a<b {b} else {a}))
    }
}
pub fn min_max<T:BoundValue>(values:&[T])->Option<Bounds<T>> {
    let (&first,rest)=values.split_first()?;
    Some(rest.iter().fold(Bounds::point(first),|b,&v|b.merge(Bounds::point(v))))
}
pub fn min_max_with_radii<T:BoundValue>(values:&[T],radii:&[T::S])->Option<Bounds<T>> {
    assert_eq!(values.len(),radii.len(),"Every value needs exactly one radius");
    let (&first,rest)=values.split_first()?;
    let expanded=|v:T,r:T::S|Bounds::new(v.map(|a|a-r),v.map(|a|a+r));
    Some(rest.iter().zip(&radii[1..]).fold(expanded(first,radii[0]),|b,(&v,&r)|b.merge(expanded(v,r))))
}
