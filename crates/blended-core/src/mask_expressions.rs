// SPDX-FileCopyrightText: 2026 Blended contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Selected-index sets and expressions for pinned Blender semantics.
//! Serial Rust interval storage is not native arena, segment-layout or TBB parity.
use crate::data_structures::IndexRange;
use std::sync::Arc;

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct IndexMask { ranges: Arc<[[i64; 2]]> }
impl IndexMask {
    pub fn from_range(range: IndexRange) -> Self { Self::from_ranges([range]) }
    pub fn from_ranges(ranges: impl IntoIterator<Item=IndexRange>) -> Self {
        let mut runs: Vec<[i64; 2]> = ranges.into_iter().filter(|r| !r.is_empty())
            .map(|r| [r.start(), r.one_after_last()]).collect();
        runs.sort_unstable();
        let mut merged = Vec::with_capacity(runs.len());
        for run in runs { append_run(&mut merged, run); }
        Self { ranges: merged.into() }
    }
    pub fn from_indices(indices: impl IntoIterator<Item=i64>) -> Self {
        Self::from_ranges(indices.into_iter().map(IndexRange::from_single))
    }
    pub fn from_bools(values: &[bool]) -> Self {
        Self::from_predicate(IndexRange::from_size(i64::try_from(values.len()).expect("Mask length overflow")), |i| values[i as usize])
    }
    /// Every index in the supplied universe is evaluated exactly once.
    pub fn from_predicate(universe: IndexRange, mut predicate: impl FnMut(i64)->bool) -> Self {
        let mut ranges=Vec::new();let mut start=None;
        for i in universe.iter() {
            if predicate(i) { if start.is_none(){start=Some(i);} }
            else if let Some(first)=start.take(){ranges.push([first,i]);}
        }
        if let Some(first)=start {ranges.push([first,universe.one_after_last()]);}
        Self { ranges: ranges.into() }
    }
    /// Count is the number of selected indices, not an end position.
    pub fn from_every_nth(step: i64, count: i64, start: i64) -> Self {
        assert!(step>0 && count>=0 && start>=0,"Invalid strided mask");
        if count==0 {return Self::default();}
        let last=start.checked_add((count-1).checked_mul(step).expect("Strided mask overflow")).expect("Strided mask overflow");
        assert!(last<i64::MAX,"Final selected index has no representable exclusive bound");
        if step==1 {return Self::from_range(IndexRange::new(start,count));}
        Self::from_indices((0..count).map(|i|start+i*step))
    }
    pub fn is_empty(&self)->bool {self.ranges.is_empty()}
    pub fn len(&self)->i64 {self.ranges.iter().map(|r|r[1]-r[0]).sum()}
    pub fn canonical_ranges(&self)->&[[i64;2]] {&self.ranges}
    pub fn contains(&self,index:i64)->bool {
        if index<0{return false;}
        let i=self.ranges.partition_point(|r|r[1]<=index);
        i<self.ranges.len() && self.ranges[i][0]<=index
    }
    pub fn to_range(&self)->Option<IndexRange> {
        match self.ranges.as_ref() {
            []=>Some(IndexRange::empty()),
            [[start,end]]=>Some(IndexRange::from_begin_end(*start,*end)),
            _=>None,
        }
    }
    pub fn iter(&self)->impl Iterator<Item=i64>+'_ {self.ranges.iter().flat_map(|r|r[0]..r[1])}
    /// Virtual bounded-span segmentation. Original expression tests require one
    /// segment for their small masks. Arbitrary native allocation choices are
    /// not promised for larger masks with several canonical runs.
    pub fn segments_num(&self)->usize {
        const WIDTH:i64=16384;
        let mut segments=0_usize;let mut covered_end=0_i64;
        for &[mut start,end] in self.ranges.iter() {
            if start<covered_end {start=covered_end.min(end);}
            if start==end {continue;}
            let count=(end-start-1)/WIDTH+1;
            segments=segments.checked_add(usize::try_from(count).expect("Segment count overflow")).expect("Segment count overflow");
            covered_end=start.saturating_add(count.saturating_mul(WIDTH));
        }
        segments
    }
    pub fn union(&self,other:&Self)->Self {
        let mut out=Vec::with_capacity(self.ranges.len()+other.ranges.len());let(mut a,mut b)=(0,0);
        while a<self.ranges.len() || b<other.ranges.len() {
            let take_a=b==other.ranges.len() || (a<self.ranges.len() && self.ranges[a]<=other.ranges[b]);
            let next=if take_a {let r=self.ranges[a];a+=1;r}else{let r=other.ranges[b];b+=1;r};
            append_run(&mut out,next);
        }
        Self {ranges:out.into()}
    }
    pub fn intersection(&self,other:&Self)->Self {
        let mut out=Vec::new();let(mut a,mut b)=(0,0);
        while a<self.ranges.len() && b<other.ranges.len(){
            let x=self.ranges[a];let y=other.ranges[b];let start=x[0].max(y[0]);let end=x[1].min(y[1]);
            if start<end {append_run(&mut out,[start,end]);}
            if x[1]<y[1]{a+=1;}else{b+=1;}
        }
        Self {ranges:out.into()}
    }
    pub fn difference(&self,other:&Self)->Self {
        let mut out=Vec::new();let mut b=0;
        for &[start,end] in self.ranges.iter(){
            let mut cursor=start;
            while b<other.ranges.len() && other.ranges[b][1]<=cursor{b+=1;}
            let mut j=b;
            while j<other.ranges.len() && other.ranges[j][0]<end{
                let [cut_start,cut_end]=other.ranges[j];
                if cut_start>cursor{append_run(&mut out,[cursor,cut_start.min(end)]);}
                cursor=cursor.max(cut_end);
                if cursor>=end{break;}
                j+=1;
            }
            if cursor<end{append_run(&mut out,[cursor,end]);}
            b=j;
        }
        Self {ranges:out.into()}
    }
    pub fn complement(&self,universe:&Self)->Self {universe.difference(self)}
    pub fn complement_range(&self,universe:IndexRange)->Self {Self::from_range(universe).difference(self)}
}
fn append_run(out:&mut Vec<[i64;2]>,run:[i64;2]) {
    debug_assert!(0<=run[0] && run[0]<run[1]);
    if let Some(last)=out.last_mut(){
        if run[0]<=last[1]{last[1]=last[1].max(run[1]);return;}
    }
    out.push(run);
}

/// Leaves borrow masks; composite nodes own expressions instead of a native arena.
pub enum Expr<'a> {
    Mask(&'a IndexMask), Range(IndexRange),
    Union(Vec<Expr<'a>>), Intersection(Vec<Expr<'a>>),
    Difference(Box<Expr<'a>>,Vec<Expr<'a>>),
}
impl<'a> From<&'a IndexMask> for Expr<'a>{fn from(v:&'a IndexMask)->Self{Self::Mask(v)}}
impl From<IndexRange> for Expr<'_>{fn from(v:IndexRange)->Self{Self::Range(v)}}
#[derive(Default)]pub struct ExprBuilder;
impl ExprBuilder {
    pub fn new()->Self{Self}
    pub fn merge<'a>(&self,terms:impl IntoIterator<Item=Expr<'a>>)->Expr<'a>{Expr::Union(terms.into_iter().collect())}
    pub fn intersect<'a>(&self,terms:impl IntoIterator<Item=Expr<'a>>)->Expr<'a>{
        let terms:Vec<_>=terms.into_iter().collect();assert!(!terms.is_empty(),"Intersection needs a bounded first term");Expr::Intersection(terms)
    }
    pub fn subtract<'a>(&self,main:Expr<'a>,others:impl IntoIterator<Item=Expr<'a>>)->Expr<'a>{Expr::Difference(Box::new(main),others.into_iter().collect())}
}
impl Expr<'_> {
    /// Explicit post-order evaluation avoids recursive evaluation call depth.
    pub fn evaluate(&self)->IndexMask {
        let mut work=vec![(self,false)];let mut values:Vec<IndexMask>=Vec::new();
        while let Some((expr,visited))=work.pop(){
            if !visited{
                match expr{
                    Self::Mask(mask)=>values.push((*mask).clone()),
                    Self::Range(range)=>values.push(IndexMask::from_range(*range)),
                    Self::Union(terms)|Self::Intersection(terms)=>{
                        work.push((expr,true));for term in terms.iter().rev(){work.push((term,false));}
                    }
                    Self::Difference(main,terms)=>{
                        work.push((expr,true));for term in terms.iter().rev(){work.push((term,false));}work.push((main,false));
                    }
                }
                continue;
            }
            let count=match expr{Self::Union(t)|Self::Intersection(t)=>t.len(),Self::Difference(_,t)=>t.len()+1,_=>unreachable!()};
            let base=values.len().checked_sub(count).expect("Expression evaluation stack mismatch");
            let result=match expr{
                Self::Union(_)=>values[base..].iter().fold(IndexMask::default(),|a,b|a.union(b)),
                Self::Intersection(_)=>{
                    assert!(count>0,"Unbounded empty intersection");values[base+1..].iter().fold(values[base].clone(),|a,b|a.intersection(b))
                }
                Self::Difference(_,_)=>values[base+1..].iter().fold(values[base].clone(),|a,b|a.difference(b)),
                _=>unreachable!(),
            };
            values.truncate(base);values.push(result);
        }
        assert_eq!(values.len(),1,"Expression evaluation result mismatch");values.pop().unwrap()
    }
}
