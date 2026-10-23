#!/usr/bin/env python3
"""Source-locked translation of both geometric-maths test families.

All expectations and loop bounds originate in the pinned Blender sources.
Uninitialised output arrays become zeroed Rust arrays and are overwritten before
inspection. Legacy output parameters stay output parameters; typed calls return
values. Fatal ASSERT_TRUE returns from the case on failure, unlike EXPECT_TRUE.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract,split_args,rewrite_calls
from port_numeric_type_tests import numbers,comments
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={'BLI_math_geom_test.cc': 'SOURCE_LEGACY_SHA', 'BLI_math_geom_hh_test.cc': 'SOURCE_MODERN_SHA'}
HEAD='''// SPDX-FileCopyrightText: 2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from unmodified, hash-locked original test bodies.
#![allow(non_snake_case,unused_mut,unused_parens,unused_assignments)]
use crate::geometry_math::*;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! numeq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a as f64)==($b as f64),stringify!($a == $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b within $e),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! fatal_yes {($r:expr,$a:expr)=>{{let p=$a;$r.check(p,stringify!($a),line!());if !p{return $r;}}};}
'''
LOOP_COUNTS={'math_geom_hh.AxisDominantToM3':9,'math_geom_hh.InterpWeightsPoly':8}

def expr(s):
 s=s.strip().replace('std::sqrt','sqrtf').replace('::blender::poly_to_tri_count','legacy_poly_to_tri_count')
 s=s.replace('blender::map_to_sphere','map_to_sphere_out')
 s=re.sub(r'reinterpret_cast<const float \*>\(&([a-zA-Z0-9_]+)\)',r'\1',s)
 s=re.sub(r'reinterpret_cast<(?:const )?float \(\*\)\[2\]>\((\w+)\.data\(\)\)',r'&\1',s)
 s=re.sub(r'&([a-zA-Z0-9_]+)\.x\b',r'\1',s)
 s=s.replace('MutableSpan(w, 4)','&mut w').replace('hit.has_value()','hit.is_some()').replace('.has_value()', '.is_some()')
 s=re.sub(r'hit->([xyz])',lambda m:'hit.as_ref().unwrap()['+str('xyz'.index(m[1]))+']',s)
 s=re.sub(r'\b(\w+)\.([xyzw])\b',lambda m:m[1]+'['+str('xyzw'.index(m[2]))+']',s)
 s=re.sub(r'\b(?:uint|int)\((\w+)\.size\(\)\)',r'\1.len()',s)
 s=s.replace('std::','')
 for dim in (2,3,4):
  def constructor(a,dim=dim):
   args=split_args(a)
   if len(args)!=dim:raise ValueError('Unexpected vector constructor '+a)
   return '['+', '.join('('+expr(x)+') as f32' for x in args)+']'
  s=rewrite_calls(s,f'float{dim}(',constructor)
 s=rewrite_calls(s,'UNPACK3(',lambda x:', '.join(x+'['+str(i)+']' for i in range(3)))
 s=numbers(s)
 s=re.sub(r'(?<!\w)\+(\d)',r'\1',s)
 output_first={'normal_quad_v3','plane_from_point_normal_v3','closest_to_line_segment_v3','closest_to_plane_normalized_v3','closest_to_plane_v3','axis_dominant_v3_to_m3','interp_weights_poly_v2','cross_tri_v3','cross_poly_v3'}
 for fun in output_first:
  s=rewrite_calls(s,fun+'(',lambda a: fun+'('+', '.join((['&mut '+split_args(a)[0].strip().lstrip('&')] + split_args(a)[1:]))+')')
 s=rewrite_calls(s,'barycentric_weights_v2(',lambda a:'barycentric_weights_v2('+', '.join(split_args(a)[:-1]+['&mut '+split_args(a)[-1]])+')')
 s=rewrite_calls(s,'interp_bilinear_quad_v3(',lambda a:'interp_bilinear_quad_v3('+', '.join(split_args(a)[:-1]+['&mut '+split_args(a)[-1]])+')')
 s=rewrite_calls(s,'isect_line_line(',lambda a:'isect_line_line('+', '.join(split_args(a)[:4]+['&mut '+x for x in split_args(a)[4:]])+')')
 s=rewrite_calls(s,'map_to_sphere_out(',lambda a:'map_to_sphere_out('+', '.join(['&mut '+x.strip().lstrip('&') for x in split_args(a)[:2]]+split_args(a)[2:])+')')
 for fun in ('isect_point_poly','area_poly','interp_weights_poly'):
  s=rewrite_calls(s,fun+'(',lambda a,fun=fun:fun+'('+', '.join('&'+x if x in ('verts','tri') else x for x in split_args(a))+')')
 for fun in ('cross_poly_v2','cross_poly_v3'):
  s=rewrite_calls(s,fun+'(',lambda a,fun=fun:fun+'('+', '.join('&'+x if re.fullmatch(r'(?:tri_\w+|poly)',x) else x for x in split_args(a))+')')
 return s

def array_init(raw,shape):
 raw=raw.strip()
 if not shape:return '('+expr(raw)+') as f32'
 if not(raw.startswith('{') and raw.endswith('}')):raise ValueError('Unknown array initialiser '+raw)
 parts=split_args(raw[1:-1]) if raw[1:-1].strip() else []
 if len(parts)>shape[0]:raise ValueError('Too many array elements')
 zero='0.0_f32'
 for n in reversed(shape[1:]):zero='['+zero+';'+str(n)+']'
 return '['+', '.join([array_init(p,shape[1:]) for p in parts]+[zero]*(shape[0]-len(parts)))+']'

def translate(body,identity):
 s=comments(body).replace('_as_float3','_as_vec3')
 s=re.sub(r'auto (cross_(?:tri|poly)_v3_as_vec3) = \[\]\(const float \(\*poly\)\[3\]\) -> float3 \{(.*?)\};',lambda m:'let '+m[1]+' = |poly:[[f32;3];3]| -> [f32;3] {'+m[2]+'};',s,flags=re.S)
 s=re.sub(r'for \(int (\w+) = 0; \1 < (\d+); \1\+\+\)',r'for \1 in 0..\2',s)
 s=re.sub(r'Vector<float2> (\w+) = (\{.*?\});',lambda m:'let '+m[1]+':Vec<[f32;2]> = '+array_init(m[2],[len(split_args(m[2][1:-1])),2])+'.to_vec();',s,flags=re.S)
 def declaration(m):
  typ,declarations=m.groups();output=[]
  if typ=='std::optional<float3>':typ='optional'
  for decl in split_args(declarations):
   h=re.fullmatch(r'(\w+)((?:\[\d+\])*)\s*(.*)',decl,re.S)
   if not h:raise ValueError('Unknown declaration '+decl)
   name,dims,init=h.groups();shape=[int(n) for n in re.findall(r'\[(\d+)\]',dims)]
   tdim={'float2':2,'float3':3,'float4':4}.get(typ)
   if tdim:shape+=[tdim]
   elif typ=='float3x3':shape+=[3,3]
   init=init.strip()
   if init.startswith('='):
    init=init[1:].strip()
    value=array_init(init,shape) if shape and init.startswith('{') else expr(init)
   elif init.startswith('('):value=expr(typ+init)
   elif init.startswith('{'):
    if not tdim:raise ValueError('Unexpected braces '+decl)
    value=array_init(init,shape)
   elif not init:
    value='0.0_f32' if typ.startswith('float') else '0_i32'
    for n in reversed(shape):value='['+value+';'+str(n)+']'
   else:raise ValueError('Untranslated initialiser '+decl)
   annotation=''
   if typ=='float' and not dims:annotation=':f32'
   elif typ=='int':annotation=':i32'
   output.append('let mut '+name+annotation+' = '+value+';')
  return '\n'.join(output)
 s=re.sub(r'(?m)^\s*(?:const\s+)?(std::optional<float3>|float3x3|float[234]|float|int)\s+([^;]+);',declaration,s)
 for kind,macro in [('EQ','numeq'),('NEAR','near'),('TRUE','yes'),('FALSE','no')]:
  def assertion(a,kind=kind,macro=macro):
   parts=[expr(x) for x in split_args(a)]
   if kind=='EQ' and (parts[0] in ('v0','v1','v2','v3') or 'isect_point_poly' in a):macro='eq'
   return macro+'!(r, '+', '.join(parts)+')'
  s=rewrite_calls(s,'EXPECT_'+kind+'(',assertion)
 s=rewrite_calls(s,'ASSERT_TRUE(',lambda a:'fatal_yes!(r, '+expr(a)+')')
 s=re.sub(r'(?m)^\s*(?:normal_quad_v3|plane_from_point_normal_v3|closest_to_line_segment_v3|closest_to_plane_normalized_v3|closest_to_plane_v3|axis_dominant_v3_to_m3|barycentric_weights_v2|interp_weights_poly|interp_weights_poly_v2|interp_bilinear_quad_v3|blender::map_to_sphere|cross_tri_v3|cross_poly_v3)\([^;]+;',lambda m:expr(m[0]),s)
 s=re.sub(r'return float3\([^;]+;',lambda m:expr(m[0]),s)
 s=s.replace('reinterpret_cast<float (*)[2]>(verts.data())','&verts').replace('int(verts.size())','verts.len()').replace('float2(0.5f, 0.5f)','[0.5_f32,0.5_f32]')
 if re.search(r'\bEXPECT_|\bASSERT_|\bfloat[234]?\b|reinterpret_cast|std::|\bauto\b|\bint\b|-> float',s):raise ValueError('Untranslated C++ in '+identity+'\n'+s)
 return s

def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong reference')
 out=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
 for name,digest in FILES.items():
  source='source/blender/blenlib/tests/'+name;raw=(root/'.upstream/blender'/source).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Changed original source '+name)
  for identity,body,line in extract(raw.decode()):
   translated=translate(body,identity);sites=len(re.findall(r'\b(?:EXPECT|ASSERT)_(?:EQ|NEAR|TRUE|FALSE)\s*\(',comments(body)))
   if sites!=len(re.findall(r'\b(?:eq|numeq|near|yes|no|fatal_yes)!',translated)):raise ValueError('Dropped or duplicated assertion '+identity)
   count=LOOP_COUNTS.get(identity,sites);fn=identity.replace('.','__')
   out+=f'\n// {source}:{line}\npub fn {fn}()->Report{{let mut r=Report::default();\n{translated}\nr\n}}\n'
   native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::geometry_math_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
   cases.append(dict(id=identity,path=source,line=line,source_sha256=digest,rust_function=fn,assertion_count=sites,expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
  (root/'tests/upstream/blender'/name).write_bytes(raw)
 out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/geometry_math_cases.rs').write_text(out)
 (root/'crates/blended-core/tests/upstream_geometry_math.rs').write_text(native)
 (root/'compatibility/geometry-math-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files=FILES,cases=cases,complete_blender_test_port=False,notes='Complete legacy and modern geometric maths test files. Assertions, finite inputs and loop bounds preserved. Safe Rust zero-initialises output buffers; upstream writes all inspected elements. Fatal ASSERT_TRUE exits the case on failure. Original API layers may share implementation, independently checked against C++ traces.'),indent=2)+'\n')
 return cases
if __name__=='__main__':
 cases=generate();print(json.dumps(dict(cases=len(cases),assertion_sites=sum(c['assertion_count'] for c in cases),runtime_assertions=sum(c['expected_runtime_assertions'] for c in cases))))
