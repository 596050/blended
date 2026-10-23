// SPDX-FileCopyrightText: 2023-2026 Blender Authors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Borrowed, checked bit spans and packed group/bitmap adapters.
//! Cells retain Blender's non-atomic shared-reference behaviour without unsafe aliases.
use core::cell::Cell;
pub use crate::collections::{BitRef,MutableBitRef,BitVector,IndexRange,IndexRangesBuilder};

#[derive(Clone,Copy,Debug)]
pub struct BitSpan<'a>{words:&'a [Cell<u64>],range:IndexRange}
impl<'a> BitSpan<'a>{
    pub fn empty()->Self{Self{words:&[],range:IndexRange::empty()}}
    pub fn new(words:&'a [Cell<u64>],range:IndexRange)->Self{
        let available=i64::try_from(words.len()).expect("Bit storage length overflow").checked_mul(64).expect("Bit length overflow");
        assert!(range.one_after_last()<=available,"Bit span outside backing storage");
        Self{words,range}
    }
    pub fn from_vector(v:&'a BitVector)->Self{Self::new(v.words(),IndexRange::from_size(v.size()))}
    pub fn size(self)->i64{self.range.size()}
    pub fn is_empty(self)->bool{self.range.is_empty()}
    pub fn bit_range(self)->IndexRange{self.range}
    pub fn data(self)->*const Cell<u64>{self.words.as_ptr()}
    pub fn bit(self,index:i64)->BitRef<'a>{
        assert!(index>=0 && index<self.size(),"Bit index outside span");
        let bit=self.range.start()+index;
        BitRef::new(&self.words[(bit/64) as usize],(bit%64) as u32)
    }
    pub fn iter(self)->impl Iterator<Item=BitRef<'a>>{(0..self.size()).map(move|i|self.bit(i))}
    pub fn slice(self,range:IndexRange)->Self{
        assert!(range.one_after_last()<=self.size(),"Bit slice outside span");
        Self::new(self.words,IndexRange::new(self.range.start()+range.start(),range.size()))
    }
    pub fn drop_front(self,n:i64)->Self{assert!(n>=0);let n=n.min(self.size());self.slice(IndexRange::new(n,self.size()-n))}
    pub fn take_back(self,n:i64)->Self{assert!(n>=0);let n=n.min(self.size());self.slice(IndexRange::new(self.size()-n,n))}
    /// Word of up to 64 relative bits; unused high bits are zero.
    fn chunk(self,start:i64)->u64{
        assert!(start>=0 && start<=self.size());
        let remaining=(self.size()-start).min(64);
        if remaining==0{return 0;}
        let absolute=self.range.start()+start;let word=(absolute/64) as usize;let offset=(absolute%64) as u32;
        let mut value=self.words[word].get()>>offset;
        if offset!=0 && remaining>i64::from(64-offset){value|=self.words[word+1].get()<<(64-offset);}
        value & crate::collections::mask_first_n_bits(remaining as u32)
    }
}
#[derive(Clone,Copy,Debug)]
pub struct MutableBitSpan<'a>(BitSpan<'a>);
impl<'a> MutableBitSpan<'a>{
    pub fn empty()->Self{Self(BitSpan::empty())}
    pub fn new(words:&'a[Cell<u64>],range:IndexRange)->Self{Self(BitSpan::new(words,range))}
    pub fn from_vector(v:&'a BitVector)->Self{Self(BitSpan::from_vector(v))}
    pub fn as_read(self)->BitSpan<'a>{self.0}
    pub fn size(self)->i64{self.0.size()}
    pub fn is_empty(self)->bool{self.0.is_empty()}
    pub fn data(self)->*const Cell<u64>{self.0.data()}
    pub fn bit_range(self)->IndexRange{self.0.bit_range()}
    pub fn slice(self,r:IndexRange)->Self{Self(self.0.slice(r))}
    pub fn bit(self,index:i64)->MutableBitRef<'a>{
        assert!(index>=0 && index<self.size(),"Bit index outside span");
        let bit=self.0.range.start()+index;
        MutableBitRef::new(&self.0.words[(bit/64) as usize],(bit%64) as u32)
    }
    pub fn iter(self)->impl Iterator<Item=MutableBitRef<'a>>{(0..self.size()).map(move|i|self.bit(i))}
    pub fn set_all(self,value:bool){
        // The empty case deliberately does not touch any backing word.
        for bit in self.iter(){bit.set(value);}
    }
    pub fn copy_from(self,source:BitSpan<'_>){
        assert_eq!(self.size(),source.size());
        for i in 0..self.size(){self.bit(i).set(source.bit(i).test());}
    }
    pub fn or_assign(self,source:impl AsBitSpan){
        let source=source.as_bit_span();assert_eq!(self.size(),source.size());
        for i in 0..self.size(){self.bit(i).set(self.bit(i).test()|source.bit(i).test());}
    }
    pub fn and_assign(self,source:impl AsBitSpan){
        let source=source.as_bit_span();assert_eq!(self.size(),source.size());
        for i in 0..self.size(){self.bit(i).set(self.bit(i).test()&source.bit(i).test());}
    }
}
pub trait AsBitSpan{fn as_bit_span(&self)->BitSpan<'_>;}
impl AsBitSpan for BitSpan<'_>{fn as_bit_span(&self)->BitSpan<'_>{*self}}
impl AsBitSpan for MutableBitSpan<'_>{fn as_bit_span(&self)->BitSpan<'_>{self.0}}
impl AsBitSpan for BitVector{fn as_bit_span(&self)->BitSpan<'_>{BitSpan::from_vector(self)}}
pub trait AsMutableBitSpan:AsBitSpan{fn as_mutable_bit_span(&self)->MutableBitSpan<'_>;}
impl AsMutableBitSpan for MutableBitSpan<'_>{fn as_mutable_bit_span(&self)->MutableBitSpan<'_>{*self}}
impl AsMutableBitSpan for BitVector{fn as_mutable_bit_span(&self)->MutableBitSpan<'_>{MutableBitSpan::from_vector(self)}}
pub fn is_bounded_span(span:&impl AsBitSpan)->bool{
    let s=span.as_bit_span();let start=s.bit_range().start();let len=s.size();
    start<64 && (if len<64{start+len<=64}else{start==0})
}
pub fn iter_1_indices(mut word:u64)->impl Iterator<Item=i32>{
    core::iter::from_fn(move||{if word==0{return None;}let bit=word.trailing_zeros();word&=word-1;Some(bit as i32)})
}
pub fn foreach_1_index(span:&impl AsBitSpan,mut visit:impl FnMut(i32)->bool){
    let s=span.as_bit_span();assert!(s.size()<=i64::from(i32::MAX),"Callback index outside i32 range");
    for start in (0..s.size()).step_by(64){
        for relative in iter_1_indices(s.chunk(start)){
            if !visit((start+i64::from(relative)) as i32){return;}
        }
    }
}
pub fn find_first_1_index(span:&impl AsBitSpan)->Option<i64>{
    let s=span.as_bit_span();for start in (0..s.size()).step_by(64){let word=s.chunk(start);if word!=0{return Some(start+i64::from(word.trailing_zeros()));}}None
}
pub fn find_first_0_index(span:&impl AsBitSpan)->Option<i64>{
    let s=span.as_bit_span();for start in (0..s.size()).step_by(64){let word=!s.chunk(start)&crate::collections::mask_first_n_bits((s.size()-start).min(64) as u32);if word!=0{return Some(start+i64::from(word.trailing_zeros()));}}None
}
pub fn find_first_1_index_expr(a:&impl AsBitSpan,b:&impl AsBitSpan,mut expr:impl FnMut(u64,u64)->u64)->Option<i64>{
    let(a,b)=(a.as_bit_span(),b.as_bit_span());assert_eq!(a.size(),b.size());
    for start in (0..a.size()).step_by(64){
        let bits=expr(a.chunk(start),b.chunk(start))&crate::collections::mask_first_n_bits((a.size()-start).min(64) as u32);
        if bits!=0{return Some(start+i64::from(bits.trailing_zeros()));}
    }None
}
pub fn or_bools_into_bits(values:&[bool],destination:&impl AsMutableBitSpan){
    let d=destination.as_mutable_bit_span();assert!((values.len() as u64)<=d.size() as u64);
    for (i,&value) in values.iter().enumerate(){if value{d.bit(i as i64).set(true);}}
}
pub fn bits_to_index_ranges<const N:usize>(span:&impl AsBitSpan,builder:&mut IndexRangesBuilder<N>){
    let s=span.as_bit_span();let mut i=0;
    while i<s.size(){if !s.bit(i).test(){i+=1;continue;}let start=i;while i<s.size()&&s.bit(i).test(){i+=1;}builder.add_range(start,i);}
}
#[derive(Clone,Debug,Default)]
pub struct BitGroupVector{bits:BitVector,groups:i64,group_len:i64,stride:i64}
impl BitGroupVector{
    pub fn new(groups:i64,group_len:i64)->Self{
        assert!(groups>=0 && group_len>=0);
        let stride=if group_len<64{(group_len.max(1) as u64).next_power_of_two() as i64}else{group_len.checked_add(63).expect("Group width overflow")/64*64};
        let len=groups.checked_mul(stride).expect("Group allocation overflow");
        Self{bits:BitVector::with_fill(len,false),groups,group_len,stride}
    }
    pub fn size(&self)->i64{self.groups}
    pub fn group_size(&self)->i64{self.group_len}
    pub fn group(&self,index:i64)->MutableBitSpan<'_>{
        assert!(index>=0 && index<self.groups);let bit=index*self.stride;
        MutableBitSpan::new(&self.bits.words()[(bit/64) as usize..],IndexRange::new(bit%64,self.group_len))
    }
    pub fn all_bits(&self)->MutableBitSpan<'_>{MutableBitSpan::from_vector(&self.bits)}
    pub fn foreach_and(&self,mask:&impl AsBitSpan){let m=mask.as_bit_span();assert_eq!(m.size(),self.group_len);for i in 0..self.groups{self.group(i).and_assign(m);}}
}
#[derive(Debug)]
pub struct Bitmap{words:Vec<u32>,len:usize}
impl Bitmap{
    pub fn new(len:usize)->Self{Self{words:vec![0;len.checked_add(31).expect("Bitmap length overflow")/32],len}}
    pub fn get(&self,bit:usize)->bool{assert!(bit<self.len);self.words[bit/32]&(1_u32<<(bit%32))!=0}
    pub fn set(&mut self,bit:usize,value:bool){assert!(bit<self.len);let mask=1_u32<<(bit%32);if value{self.words[bit/32]|=mask;}else{self.words[bit/32]&=!mask;}}
    pub fn flip_all(&mut self,length:usize){assert!(length<=self.len);for w in &mut self.words[..length.div_ceil(32)]{*w=!*w;}}
    pub fn find_first_unset(&self,length:usize)->i32{assert!(length<=self.len && length<=i32::MAX as usize);(0..length).find(|&i|!self.get(i)).map_or(-1,|i|i as i32)}
}
