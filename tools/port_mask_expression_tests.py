#!/usr/bin/env python3
"""Finite source-locked port. The original randomized workload is not reduced.
The #if 0 benchmark remains explicitly unported, never counted passing.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
PATH='source/blender/blenlib/tests/BLI_index_mask_expression_test.cc'
BLOB='2d266c4d5312e4c9ddc28cddec657e0253134af3'
HEAD='''// SPDX-FileCopyrightText: 2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked adapter; original identities, bodies and helper hashes are in mask-expression-ports.json.
#![allow(non_snake_case,unused_mut)]
use crate::mask_expressions::{IndexMask,ExprBuilder,Expr};
use crate::data_structures::IndexRange;
use crate::priority_heaps::BlenderRng;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
// Tuples are (start, size), exactly like the original IndexRange initializers.
fn mask(ranges:&[(i64,i64)])->IndexMask{IndexMask::from_ranges(ranges.iter().map(|&(start,size)|IndexRange::new(start,size)))}
fn random_bools(rng:&mut BlenderRng,size:usize)->Vec<bool>{
 let mut bools=vec![false;size];let mut i=0;
 while i<size{
  let chunk_size=(size-i).min((rng.get_int32()%5000+1) as usize);
  let chunk_type=rng.get_int32()%4;
  let density=rng.get_int32() as f32/2147483648.0_f32;
  for value in &mut bools[i..i+chunk_size]{
   *value=if chunk_type==0{true}else if chunk_type==1{false}else{rng.get_int32() as f32/2147483648.0_f32<density};
  }
  i+=chunk_size;
 }
 bools
}
'''
BODIES={
'Union':'''let mask_a=mask(&[(5,1),(50,100),(100_000,1)]);let mask_b=mask(&[(10,10),(60,1),(200,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_a).into(),(&mask_b).into()]);let union_mask=expr.evaluate();
eq!(report,union_mask,mask(&[(5,1),(10,10),(50,100),(200,1),(100_000,1)]));''',
'UnionMulti':'''let mask_a=mask(&[(3,1),(5,1),(6,1),(8,1),(9,1)]);let mask_b=mask(&[(4,1),(6,1),(7,1),(12,1)]);let mask_c=mask(&[(0,1),(5,1)]);let mask_d=mask(&[(6,1),(7,1),(10,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_a).into(),(&mask_b).into(),(&mask_c).into(),(&mask_d).into()]);let union_mask=expr.evaluate();
eq!(report,union_mask,mask(&[(0,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),(10,1),(12,1)]));''',
'IntersectMulti':'''let mask_a=mask(&[(3,1),(5,1),(6,1),(8,1),(9,1)]);let mask_b=mask(&[(2,1),(5,1),(6,1),(10,1)]);let mask_c=mask(&[(4,1),(5,1),(6,1)]);let mask_d=mask(&[(1,1),(5,1),(10,1)]);
let builder=ExprBuilder::new();let expr=builder.intersect([(&mask_a).into(),(&mask_b).into(),(&mask_c).into(),(&mask_d).into()]);let intersect_mask=expr.evaluate();
eq!(report,intersect_mask,mask(&[(5,1)]));''',
'DifferenceMulti':'''let mask_a=mask(&[(1,1),(2,1),(3,1),(5,1),(6,1),(7,1),(9,1),(10,1)]);let mask_b=mask(&[(2,1),(5,1),(6,1),(10,1)]);let mask_c=mask(&[(4,1),(5,1),(6,1)]);let mask_d=mask(&[(1,1),(5,1),(10,1)]);
let builder=ExprBuilder::new();let expr=builder.subtract((&mask_a).into(),[(&mask_b).into(),(&mask_c).into(),(&mask_d).into()]);let difference_mask=expr.evaluate();
eq!(report,difference_mask,mask(&[(3,1),(7,1),(9,1)]));''',
'Intersection':'''let mask_a=mask(&[(5,1),(50,100),(100_000,1)]);let mask_b=mask(&[(5,1),(6,1),(100,100),(80000,1),(100_000,1)]);
let builder=ExprBuilder::new();let expr=builder.intersect([(&mask_a).into(),(&mask_b).into()]);let intersection_mask=expr.evaluate();
eq!(report,intersection_mask,mask(&[(5,1),(100,50),(100_000,1)]));''',
'Difference':'''let mask_a=mask(&[(5,1),(50,100),(100_000,1)]);let mask_b=mask(&[(5,1),(60,1),(100,20)]);
let builder=ExprBuilder::new();let expr=builder.subtract((&mask_a).into(),[(&mask_b).into()]);let difference_mask=expr.evaluate();
eq!(report,difference_mask,mask(&[(50,10),(61,39),(120,30),(100_000,1)]));''',
'FizzBuzz':'''let mask_3=IndexMask::from_every_nth(3,11,0);let mask_5=IndexMask::from_every_nth(5,11,0);
{let builder=ExprBuilder::new();let expr=builder.merge([(&mask_3).into(),(&mask_5).into()]);let result=expr.evaluate();
eq!(report,result,mask(&[(0,1),(3,1),(5,1),(6,1),(9,1),(10,1),(12,1),(15,1),(18,1),(20,1),(21,1),(24,1),(25,1),(27,1),(30,1),(35,1),(40,1),(45,1),(50,1)]));}
{let builder=ExprBuilder::new();let expr=builder.intersect([(&mask_3).into(),(&mask_5).into()]);let result=expr.evaluate();eq!(report,result,mask(&[(0,1),(15,1),(30,1)]));}
{let builder=ExprBuilder::new();let expr=builder.subtract((&mask_3).into(),[(&mask_5).into()]);let result=expr.evaluate();eq!(report,result,mask(&[(3,1),(6,1),(9,1),(12,1),(18,1),(21,1),(24,1),(27,1)]));}
{let builder=ExprBuilder::new();let expr=builder.merge([builder.intersect([(&mask_3).into(),(&mask_5).into()]),builder.subtract((&mask_3).into(),[(&mask_5).into()])]);let result=expr.evaluate();eq!(report,result,mask(&[(0,1),(3,1),(6,1),(9,1),(12,1),(15,1),(18,1),(21,1),(24,1),(27,1),(30,1)]));}''',
'UnionToFullRange':'''let mask_1=mask(&[(2,1),(4,1),(5,1),(7,1)]);let mask_2=mask(&[(6,1),(8,1)]);let mask_3=mask(&[(1,1),(3,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_1).into(),(&mask_2).into(),(&mask_3).into()]);let result=expr.evaluate();
yes!(report,result.to_range().is_some());eq!(report,result.to_range().unwrap(),IndexRange::from_begin_end_inclusive(1,8));eq!(report,result.segments_num(),1);''',
'UnionIndividualIndices':'''let mask_1=mask(&[(3,1)]);let mask_2=mask(&[(6,1)]);let mask_3=mask(&[(5,1)]);
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_1).into(),(&mask_2).into(),(&mask_3).into()]);let result=expr.evaluate();
eq!(report,result,mask(&[(3,1),(5,1),(6,1)]));eq!(report,result.segments_num(),1);''',
'UnionLargeRanges':'''let mask_a=IndexMask::from_range(IndexRange::new(0,1_000_000));let mask_b=IndexMask::from_range(IndexRange::new(900_000,1_100_000));
let builder=ExprBuilder::new();let expr=builder.merge([(&mask_a).into(),(&mask_b).into()]);let result_mask=expr.evaluate();
eq!(report,result_mask,IndexMask::from_range(IndexRange::new(0,2_000_000)));''',
'SubtractSmall':'''let mask_a=mask(&[(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1)]);let mask_b=mask(&[(5,1),(7,1)]);let mask_c=mask(&[(8,1)]);
let builder=ExprBuilder::new();let expr=builder.subtract((&mask_a).into(),[(&mask_b).into(),(&mask_c).into()]);let result=expr.evaluate();
eq!(report,result,mask(&[(3,1),(4,1),(6,1),(9,1)]));eq!(report,result.segments_num(),1);''',
'RangeTerms':'''let builder=ExprBuilder::new();let range_a=IndexRange::from_begin_end(30_000,50_000);let range_b=IndexRange::from_begin_end(40_000,100_000);let range_c=IndexRange::from_begin_end(45_000,48_000);
let expr=builder.subtract(builder.merge([range_a.into(),range_b.into()]),[range_c.into()]);let result_mask=expr.evaluate();
eq!(report,result_mask,IndexMask::from_ranges([IndexRange::from_begin_end(30_000,45_000),IndexRange::from_begin_end(48_000,100_000)]));''',
'SingleMask':'''let mask=mask(&[(5,1),(6,1),(8,1),(9,1)]);let builder=ExprBuilder::new();let expr=builder.merge([(&mask).into()]);let result=expr.evaluate();eq!(report,result,mask);''',
'SubtractSelf':'''let mask=mask(&[(6,1),(8,1),(10,1),(100,1)]);let builder=ExprBuilder::new();let expr=builder.subtract((&mask).into(),[(&mask).into()]);let result=expr.evaluate();yes!(report,result.is_empty());''',
'Fuzzy':'''let mut rng=BlenderRng::new(0);
for _iteration in 0..50{
 let size=(rng.get_int32()%200_000+1) as usize;
 let a_bools=random_bools(&mut rng,size);let b_bools=random_bools(&mut rng,size);let c_bools=random_bools(&mut rng,size);
 let a=IndexMask::from_bools(&a_bools);let b=IndexMask::from_bools(&b_bools);let c=IndexMask::from_bools(&c_bools);let universe=IndexRange::from_size(size as i64);
 let expected=|predicate:&dyn Fn(usize)->bool|IndexMask::from_predicate(universe,|i|predicate(i as usize));
 eq!(report,a.complement_range(universe),expected(&|i|!a_bools[i]));
 eq!(report,a.complement(&b),expected(&|i|b_bools[i]&&!a_bools[i]));
 {let builder=ExprBuilder::new();eq!(report,builder.merge([(&a).into(),(&b).into(),(&c).into()]).evaluate(),expected(&|i|a_bools[i]||b_bools[i]||c_bools[i]));}
 {let builder=ExprBuilder::new();eq!(report,builder.intersect([(&a).into(),(&b).into()]).evaluate(),expected(&|i|a_bools[i]&&b_bools[i]));}
 {let builder=ExprBuilder::new();eq!(report,builder.subtract((&a).into(),[(&b).into(),(&c).into()]).evaluate(),expected(&|i|a_bools[i]&&!b_bools[i]&&!c_bools[i]));}
 {let builder=ExprBuilder::new();eq!(report,builder.subtract(builder.merge([(&a).into(),(&b).into()]),[builder.intersect([(&b).into(),(&c).into()])]).evaluate(),expected(&|i|(a_bools[i]||b_bools[i])&&!(b_bools[i]&&c_bools[i])));}
}''',
}
COUNTS=[1,1,1,1,1,1,4,3,2,1,2,1,1,1,300]
def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong reference')
 raw=(root/'.upstream/blender'/PATH).read_bytes()
 if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:raise ValueError('Pinned test source changed')
 text=raw.decode();active,disabled=text.split('/* Disable benchmark by default. */',1)
 original=list(extract(active));remaining=list(extract(disabled))
 if len(original)!=15 or len(remaining)!=1 or remaining[0][0]!='index_mask_expression.Benchmark':raise ValueError('Changed complete source universe')
 out=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
 for i,((identity,body,line),count) in enumerate(zip(original,COUNTS)):
  code=BODIES[identity.split('.')[1]];fn=identity.replace('.','__')
  out+=f'\n// {PATH}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();\n{code}\nreport\n}}\n'
  native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::mask_expression_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
  cases.append(dict(id=identity,path=PATH,line=line,source_sha256=hashlib.sha256(raw).hexdigest(),source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=len(re.findall(r'\bEXPECT_\w+\(',body)),expected_runtime_assertions=count,index=i,status='ported_unexecuted'))
 out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/mask_expression_cases.rs').write_text(out)
 (root/'crates/blended-core/tests/upstream_mask_expressions.rs').write_text(native)
 (root/'tests/upstream/blender/BLI_index_mask_expression_test.cc').write_bytes(raw)
 helper=active[active.index('static Array<bool> random_bools'):active.index('TEST(index_mask_expression, Fuzzy)')]
 (root/'compatibility/mask-expression-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,cases=cases,random_helper_source_sha256=hashlib.sha256(helper.encode()).hexdigest(),conditional_unported_cases=[dict(id=remaining[0][0],path=PATH,condition='#if 0',status='unported_disabled_benchmark')],complete_blender_test_port=False,notes='All 15 enabled original cases, original 50 randomized iterations and up-to-200000 input sizes. IndexMaskMemory uses Rust ownership rather than native arena. Mask assertions encode every selected index losslessly using canonical maximal ranges, never just counts or hashes. Disabled benchmark remains unported. Segment-count observations are preserved for small original cases, not claimed as all representation parity.'),indent=2)+'\n')
 return cases
if __name__=='__main__':
 c=generate();print(json.dumps(dict(cases=len(c),assertions=sum(v['expected_runtime_assertions'] for v in c))))
