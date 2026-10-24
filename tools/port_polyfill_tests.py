#!/usr/bin/env python3
"""Source-locked original polyfill cases and helper assertions.

Preserve the pinned helper's observable bug: it rotates poly_copy but passes poly.
Real rotations/reversals belong to a separate oracle, not silently altered tests.
"""
from pathlib import Path
import hashlib,json,re,struct
from port_collection_tests import extract
from port_numeric_type_tests import comments
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
SOURCE='source/blender/blenlib/tests/BLI_polyfill_2d_test.cc'
SHA='10bbd9b39d4cf465f4df070e517b2d41d5b55c8cfba5a380f23dfa23f468652b'
HEADER='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Original helper assertions and source-locked input polygons.
// See compatibility/polyfill-ports.json for observable combination-loop behaviour.
#![allow(non_snake_case,unused_mut)]
use crate::polyfill as p;
use std::collections::BTreeMap;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,passed:bool,expression:&str,line:u32){self.assertions+=1;if !passed{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! ne {($r:expr,$a:expr,$b:expr)=>{{$r.check($a!=$b,stringify!($a != $b),line!());}};}
macro_rules! yes {($r:expr,$v:expr)=>{{$r.check($v,stringify!($v),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b),line!());}};}

// Original test helper maths remain separate from the production implementation.
fn cross(a:[f32;2],b:[f32;2],c:[f32;2])->f32{(a[0]-b[0])*(b[1]-c[1])+(a[1]-b[1])*(c[0]-b[0])}
fn triangle_area(a:[f32;2],b:[f32;2],c:[f32;2])->f32{(0.5_f32*cross(a,b,c)).abs()}
fn polygon_area(poly:&[[f32;2]])->f32{
 let mut last=poly[poly.len()-1];let mut value=0.0_f32;
 for &co in poly{value+=(last[0]-co[0])*(co[1]+last[1]);last=co;}
 (0.5_f32*value).abs()
}
fn simple(report:&mut Report,poly_num:usize,tris:&[[u32;3]]){
 let mut used=vec![0_i32;poly_num];
 for tri in tris{
  for j in 0..3{ne!(report,u32::MAX,tri[j]);used[tri[j] as usize]+=1;}
  ne!(report,tri[0],tri[1]);ne!(report,tri[1],tri[2]);ne!(report,tri[2],tri[0]);
 }
 for i in 0..poly_num{ne!(report,0_i32,used[i]);}
}
fn edge(a:u32,b:u32)->(u32,u32){if a<b{(a,b)}else{(b,a)}}
fn topology(report:&mut Report,poly_num:usize,tris:&[[u32;3]]){
 let mut edges:BTreeMap<(u32,u32),i32>=BTreeMap::new();
 for tri in tris{for j in 0..3{*edges.entry(edge(tri[j],tri[(j+1)%3])).or_insert(0)+=1;}}
 eq!(report,edges.len() as u32,(poly_num+poly_num-3) as u32);
 for i in 0..poly_num{let key=edge(i as u32,((i+1)%poly_num) as u32);yes!(report,edges.contains_key(&key));eq!(report,*edges.get(&key).expect("Original topology lookup precondition"),1_i32);}
 // Original Map iteration order is unspecified here. Only its Boolean predicate
 // is asserted, so sorted-map iteration preserves every observable assertion.
 for &value in edges.values(){yes!(report,value==1||value==2);}
}
fn winding(report:&mut Report,poly:&[[f32;2]],tris:&[[u32;3]]){
 let mut count=[0_u32;2];
 for t in tris{let w=cross(poly[t[0] as usize],poly[t[1] as usize],poly[t[2] as usize]);if w.abs()>f32::EPSILON{count[usize::from(w<0.0)]+=1;}}
 yes!(report,count[0]==0||count[1]==0);
}
fn area(report:&mut Report,poly:&[[f32;2]],tris:&[[u32;3]]){
 let expected=polygon_area(poly);let mut actual=0.0_f32;let eps_abs=0.00001_f32;let eps=if expected>1.0{expected*eps_abs}else{eps_abs};
 for t in tris{actual+=triangle_area(poly[t[0] as usize],poly[t[1] as usize],poly[t[2] as usize]);}
 near!(report,expected,actual,eps);
}
fn nonzero(report:&mut Report,poly:&[[f32;2]],tris:&[[u32;3]]){
 let mut total=0_u32;
 for t in tris{if triangle_area(poly[t[0] as usize],poly[t[1] as usize],poly[t[2] as usize])<1e-6_f32{total+=1;}}
 eq!(report,total,0_u32);
}
fn check(report:&mut Report,flag:u32,poly:&[[f32;2]],tris:&[[u32;3]]){
 simple(report,poly.len(),tris);topology(report,poly.len(),tris);
 if flag&1==0{winding(report,poly,tris);area(report,poly,tris);if flag&2!=0{nonzero(report,poly,tris);}}
 // USE_OBJ_PREVIEW is disabled in the pinned source: its helper is a no-op.
}
fn template(report:&mut Report,flag:u32,poly:&[[f32;2]],tris:&mut [[u32;3]]){
 for tri in tris.iter_mut(){*tri=[u32::MAX;3];}
 p::triangulate_into(poly,0,tris);
 check(report,flag,poly,tris);
 p::beautify(poly,tris);
 check(report,flag,poly,tris);
}
fn flip_sign(report:&mut Report,flag:u32,poly:&[[f32;2]],tris:&mut [[u32;3]]){
 let mut copy=vec![[0.0_f32;2];poly.len()];
 for flip_x in 0..2{for flip_y in 0..2{
  let sx=if flip_x!=0{-1.0_f32}else{1.0_f32};let sy=if flip_y!=0{-1.0_f32}else{1.0_f32};
  for i in 0..poly.len(){copy[i]=[poly[i][0]*sx,poly[i][1]*sy];}
  template(report,flag,&copy,tris);
 }}
}
fn run_original(report:&mut Report,flag:u32,poly:&[[f32;2]]){
 let mut copy=poly.to_vec();let mut tris=vec![[u32::MAX;3];poly.len()-2];
 for reversed in 0..2{
  if reversed!=0{copy.reverse();}
  for _cycle in 0..poly.len(){
   // Deliberately passes poly, not copy, exactly like the pinned original helper.
   flip_sign(report,flag,poly,&mut tris);
   copy.rotate_left(1);
  }
 }
}
'''

def parse(body):
 cleaned=comments(body)
 match=re.fullmatch(r'\s*const float poly\[\]\[2\]\s*=\s*\{(.*?)\};\s*TEST_POLYFILL_TEMPLATE_STATIC\(poly,\s*(POLYFILL2D_TEST_\w+)\);\s*',cleaned,re.S)
 if not match:raise ValueError('Unreviewed source body syntax')
 points=re.findall(r'\{([^{}]+)\}',match[1]);rest=re.sub(r'\{[^{}]+\}|[\s,]','',match[1])
 if rest or len(points)<3:raise ValueError('Malformed polygon source')
 parsed=[];bits=[]
 for point in points:
  values=[v.strip() for v in point.split(',')]
  if len(values)!=2 or any(not re.fullmatch(r'-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?f?',v) for v in values):raise ValueError('Unreviewed coordinate expression')
  parsed.append([v.rstrip('f')+'_f32' if '.' in v or 'e' in v.lower() else v.rstrip('f')+'.0_f32' for v in values])
  bits.append([struct.unpack('<I',struct.pack('<f',float(v.rstrip('f'))))[0] for v in values])
 flag={'POLYFILL2D_TEST_NOP':0,'POLYFILL2D_TEST_IS_DEGENERATE':1,'POLYFILL2D_TEST_NO_ZERO_AREA_TRIS':2}[match[2]]
 n=len(parsed);count=16*n*(11*n-14+(0 if flag&1 else 2+bool(flag&2)))
 return parsed,bits,flag,count

def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong reference commit')
 raw=(root/'.upstream/blender'/SOURCE).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Source changed; review all helper semantics')
 text=raw.decode();cases=[];out=HEADER;native='// SPDX-License-Identifier: Apache-2.0\n'
 for identity,body,line in extract(text):
  coords,bits,flag,count=parse(body);fn=identity.replace('.','__');values=','.join('['+','.join(v)+']' for v in coords)
  out+=f'\n// {SOURCE}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();let poly=[{values}];run_original(&mut report,{flag},&poly);report}}\n'
  native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::polyfill_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
  cases.append(dict(id=identity,path=SOURCE,line=line,source_sha256=SHA,source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,polygon_bits=bits,polygon_size=len(coords),flag=flag,expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
 if len(cases)!=29 or sum(c['expected_runtime_assertions'] for c in cases)!=1534672:raise ValueError('Source case universe changed')
 out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/polyfill_cases.rs').write_text(out)
 (root/'crates/blended-core/tests/upstream_polyfill.rs').write_text(native)
 (root/'tests/upstream/blender/BLI_polyfill_2d_test.cc').write_bytes(raw)
 (root/'compatibility/polyfill-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_sha256=SHA,cases=cases,complete_blender_test_port=False,helper_scope='All original assertion helpers, both plain and beautified output, 2*n*4 calls per input. Original rotation/reversal helper mutates a copy but passes original poly; preserve this and cover actual transformed inputs in a separate oracle.',configurations={'USE_COMBINATIONS_ALL':True,'USE_BEAUTIFY':True,'USE_OBJ_PREVIEW':False}),indent=2)+'\n')
 return cases
if __name__=='__main__':
 c=generate();print(json.dumps({'cases':len(c),'assertions':sum(x['expected_runtime_assertions'] for x in c)}))
