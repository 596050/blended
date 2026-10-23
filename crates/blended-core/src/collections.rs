// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Safe Rust adapters for the observable BLI bit/range collection contracts.
//! Cell preserves shared bit-reference aliasing; these are not atomic references.
use core::cell::Cell;
pub use crate::data_structures::IndexRange;

pub const fn mask_first_n_bits(n:u32)->u64 {
    assert!(n<=64); if n==64 {u64::MAX} else {(1_u64<<n)-1}
}
pub const fn mask_last_n_bits(n:u32)->u64 {
    assert!(n<=64); if n==0 {0} else {u64::MAX<<(64-n)}
}
pub const fn mask_single_bit(n:u32)->u64 {assert!(n<64);1_u64<<n}
pub const fn mask_range_bits(start:u32,size:u32)->u64 {
    assert!(start<=64 && size<=64-start);
    if size==0 {0} else {mask_first_n_bits(size)<<start}
}
pub fn word_ptr(words:&[Cell<u64>],bit:i64)->*const Cell<u64> {
    assert!(bit>=0); let index=usize::try_from(bit/64).expect("Bit address overflow");
    &words[index] as *const Cell<u64>
}
#[derive(Clone,Copy,Debug)]
pub struct BitRef<'a> {word:&'a Cell<u64>,mask:u64}
impl<'a> BitRef<'a> {
    pub fn new(word:&'a Cell<u64>,bit:u32)->Self {Self{word,mask:mask_single_bit(bit)}}
    pub fn test(self)->bool {self.word.get()&self.mask!=0}
}
#[derive(Clone,Copy,Debug)]
pub struct MutableBitRef<'a>(BitRef<'a>);
impl<'a> MutableBitRef<'a> {
    pub fn new(word:&'a Cell<u64>,bit:u32)->Self {Self(BitRef::new(word,bit))}
    pub fn test(self)->bool {self.0.test()}
    pub fn as_read(self)->BitRef<'a> {self.0}
    pub fn set(self,value:bool) {
        let old=self.0.word.get();
        self.0.word.set(if value {old|self.0.mask}else{old&!self.0.mask});
    }
    pub fn reset(self) {self.set(false);}
    pub fn set_branchless(self,value:bool) {
        let old=self.0.word.get();let fill=0_u64.wrapping_sub(value as u64);
        self.0.word.set(old^((fill^old)&self.0.mask));
    }
}
pub trait BitValue {fn to_bool(self)->bool;}
impl BitValue for bool {fn to_bool(self)->bool {self}}
impl BitValue for i64 {fn to_bool(self)->bool {self!=0}}
#[derive(Clone,Debug,Default)]
pub struct BitVector {words:Vec<Cell<u64>>,len:i64}
impl BitVector {
    pub fn with_fill(len:i64,value:bool)->Self {
        assert!(len>=0 && len<=i64::MAX-63);
        let count=usize::try_from((len+63)/64).expect("Bit allocation overflow");
        Self{words:(0..count).map(|_|Cell::new(if value{u64::MAX}else{0})).collect(),len}
    }
    pub fn from_values(values:&[bool])->Self {
        let v=Self::with_fill(i64::try_from(values.len()).expect("Too many bits"),false);
        for (i,b) in values.iter().copied().enumerate(){v.bit_mut(i as i64).set(b);}v
    }
    pub fn size(&self)->i64 {self.len}
    pub fn get(&self,index:i64)->bool {self.bit_mut(index).test()}
    pub fn bit_mut(&self,index:i64)->MutableBitRef<'_> {
        assert!(index>=0 && index<self.len,"Bit index out of bounds");
        MutableBitRef::new(&self.words[(index/64) as usize],(index%64) as u32)
    }
    pub fn append(&mut self,value:impl BitValue) {
        let index=self.len;assert!(index<i64::MAX,"Bit count overflow");
        if index%64==0{self.words.push(Cell::new(0));}self.len+=1;
        self.bit_mut(index).set(value.to_bool());
    }
    pub fn iter(&self)->impl Iterator<Item=BitRef<'_>>+'_ {(0..self.len).map(|i|self.bit_mut(i).as_read())}
    pub fn iter_mut(&self)->impl Iterator<Item=MutableBitRef<'_>>+'_ {(0..self.len).map(|i|self.bit_mut(i))}
}
#[derive(Debug)]
pub struct IndexRangesBuilder<const N:usize> {ranges:[IndexRange;N],len:usize}
impl<const N:usize> Default for IndexRangesBuilder<N> {fn default()->Self{Self::new()}}
impl<const N:usize> IndexRangesBuilder<N> {
    pub fn new()->Self{Self{ranges:[IndexRange::empty();N],len:0}}
    pub fn size(&self)->i64{self.len as i64}
    pub fn is_empty(&self)->bool{self.len==0}
    pub fn get(&self,index:usize)->IndexRange{assert!(index<self.len);self.ranges[index]}
    pub fn add(&mut self,index:i64)->bool{self.add_range(index,index.checked_add(1).expect("Index overflow"))}
    pub fn add_range(&mut self,start:i64,end:i64)->bool{
        assert!(start>=0 && start<end);
        let previous=if self.len==0{-1}else{self.ranges[self.len-1].one_after_last()};
        assert!(start>=previous,"Indices must be ascending and non-overlapping");
        if start==previous {
            let first=self.ranges[self.len-1].start();
            self.ranges[self.len-1]=IndexRange::from_begin_end(first,end);false
        }else{
            assert!(self.len<N,"Range buffer is full");
            self.ranges[self.len]=IndexRange::from_begin_end(start,end);self.len+=1;true
        }
    }
}
/// Inputs to the following algorithms must be sorted, unique nonnegative indices.
pub fn non_empty_is_range(values:&[i32])->bool {
    assert!(!values.is_empty());
    i64::from(*values.last().unwrap())-i64::from(values[0])==values.len() as i64-1
}
pub fn non_empty_as_range(values:&[i32])->IndexRange {
    assert!(non_empty_is_range(values));IndexRange::new(i64::from(values[0]),values.len() as i64)
}
pub fn find_size_of_next_range(values:&[i32])->i64 {
    assert!(!values.is_empty());let mut lo=0;let mut hi=values.len();
    while lo<hi {let mid=lo+(hi-lo)/2;if i64::from(values[mid])-i64::from(values[0])>mid as i64 {hi=mid}else{lo=mid+1}}
    lo as i64
}
pub fn find_size_until_next_range(values:&[i32],minimum:i64)->i64 {
    assert!(!values.is_empty() && minimum>=1);let mut length=1_i64;let mut last=i64::from(values[0]);
    for (i,&value) in values.iter().enumerate().skip(1){
        let value=i64::from(value);
        if value==last+1 {length+=1;if length>=minimum{return i as i64-minimum+1;}}
        else{length=1;}last=value;
    }values.len() as i64
}
pub fn find_content_range(values:&[i32],range:IndexRange)->IndexRange {
    if values.is_empty()||range.is_empty(){return IndexRange::empty();}
    let first=values.partition_point(|&v|i64::from(v)<range.first());
    let end=first+values[first..].partition_point(|&v|i64::from(v)<=range.last());
    IndexRange::from_begin_end(first as i64,end as i64)
}
#[derive(Clone,Copy,Debug)]
pub enum IndexPart<'a>{Range(IndexRange),Span(&'a [i32])}
impl<'a> IndexPart<'a>{
    pub fn as_range(self)->IndexRange{match self{Self::Range(r)=>r,_=>panic!("Expected range variant")}}
    pub fn as_slice(self)->&'a [i32]{match self{Self::Span(s)=>s,_=>panic!("Expected span variant")}}
}
pub fn split_to_ranges_and_spans<'a>(values:&'a [i32],threshold:usize,parts:&mut Vec<IndexPart<'a>>)->i64{
    assert!(threshold>=1 && threshold<=i64::MAX as usize);let old=parts.len();let mut remaining=values;
    while !remaining.is_empty(){
        if non_empty_is_range(remaining){parts.push(IndexPart::Range(non_empty_as_range(remaining)));break;}
        let prefix=&remaining[..threshold.min(remaining.len())];
        if non_empty_is_range(prefix){
            let size=find_size_of_next_range(remaining) as usize;
            parts.push(IndexPart::Range(IndexRange::new(i64::from(remaining[0]),size as i64)));remaining=&remaining[size..];
        }else{
            let size=find_size_until_next_range(remaining,threshold as i64) as usize;
            assert!(size>0,"Expected nonempty span segment");let segment=&remaining[..size];
            parts.push(if non_empty_is_range(segment){IndexPart::Range(non_empty_as_range(segment))}else{IndexPart::Span(segment)});
            remaining=&remaining[size..];
        }
    }(parts.len()-old) as i64
}
