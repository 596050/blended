#!/usr/bin/env python3
"""Source-locked port of Blender's matrix type runtime tests.

Matrix views retain shared backing, including overlapping write-back.
Every scalar comparison in matrix macros is preserved.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract,split_args,rewrite_calls
from port_numerics_text_tests import numbers,comments,vector_expr
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
SOURCE='source/blender/blenlib/tests/BLI_math_matrix_types_test.cc'
SHA='faaef43e1af1b54f8034dc083825edb9cc9c5f49b644b83681b91ccf9e12a345'
HEADER='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from pinned original matrix test bodies, not replacement expectations.
#![allow(non_snake_case,unused_mut,unused_parens,unused_variables,unused_assignments)]
use crate::numeric_vectors as v;
use crate::matrix_types as m;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! numeq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a as f64)==($b as f64),stringify!($a == $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b within $e),line!());}};}
'''

def expression(s):
 s=numbers(s.strip());pos=0
 while (hit:=re.search(r'\b(float|double)([234])x([234])(?:::([a-z]+))?\(',s[pos:])):
  start=pos+hit.start();a=pos+hit.end();end=a;depth=1
  while depth:
   if s[end]=='(':depth+=1
   elif s[end]==')':depth-=1
   end+=1
  ty={'float':'f32','double':'f64'}[hit[1]];cols=int(hit[2]);rows=int(hit[3]);method=hit[4]
  args=split_args(s[a:end-1]) if s[a:end-1].strip() else []
  prefix=f'm::M::<{ty},{cols},{rows}>'
  if method:
   assert method in ('identity','zero','all','diagonal','default')
   value=prefix+'::'+method+'('+', '.join('('+expression(x)+') as f64' for x in args)+')'
  elif len(args)==cols:
   col=[]
   for arg in args:
    arg=arg.strip()
    if arg.startswith('{') and arg.endswith('}'):arg=hit[1]+str(rows)+'('+arg[1:-1]+')'
    col.append('v::construct::<'+ty+','+str(rows)+'>(&[&('+expression(arg)+') as &dyn v::Components])')
   value=prefix+'::from_cols(['+', '.join(col)+'])'
  elif len(args)==1:
   arg=args[0].strip()
   if arg=='array':value=prefix+'::from_flat(&array)'
   elif arg=='ptr':value=prefix+'::from_array(ptr)'
   elif arg=='view':value=prefix+'::from_matrix(&view.read())'
   else:value=prefix+'::from_matrix(&('+expression(arg)+'))'
  else:raise ValueError('Unreviewed matrix constructor '+s[start:end])
  s=s[:start]+value+s[end:];pos=start+len(value)
 s=vector_expr(s)
 s=re.sub(r'\b(\w+)\[([0-9]+)\]\[([0-9]+)\]',r'\1.get(\2,\3)',s)
 s=re.sub(r'\b(\w+)\.([xyzw])\.([xyzw])\b',lambda h:h[1]+'.get('+str('xyzw'.index(h[2]))+','+str('xyzw'.index(h[3]))+')',s)
 s=re.sub(r'\b(\w+)\[([0-3])\]\.([xyzw])\b',lambda h:h[1]+'.get('+h[2]+','+str('xyzw'.index(h[3]))+')',s)
 return s

def translate(body,identity):
 code=comments(body)
 code=code.replace('float2x2 m{};','float2x2 m = float2x2::default();')
 code=code.replace('float array[4] = {1.0f, 2.0f, 3.0f, 4.0f};','let array=[1.0_f32,2.0_f32,3.0_f32,4.0_f32];')
 code=code.replace('float array[2][2] = {{1.0f, 2.0f}, {3.0f, 4.0f}};','let array=[[1.0_f32,2.0_f32],[3.0_f32,4.0_f32]];')
 code=code.replace('float (*ptr)[2] = array;','let ptr=&array;')
 code=code.replace('float c_style_mat[4][4] = {{1, 2, 3, 4}, {5, 6, 7, 8}, {9, 10, 11, 12}, {13, 14, 15, 16}};','let c_style_mat=m::cell_storage([[1.0_f32,2.0,3.0,4.0],[5.0,6.0,7.0,8.0],[9.0,10.0,11.0,12.0],[13.0,14.0,15.0,16.0]]);')
 code=code.replace('float4x4_view c_mat_view = float4x4_view(c_style_mat);','let c_mat_view=m::View::<f32,4,4,4,4>::new(&c_style_mat,0,0);')
 code=code.replace('float4x4_mutableview c_mat_mutable_view = float4x4_mutableview(c_style_mat);','let c_mat_mutable_view=m::View::<f32,4,4,4,4>::new(&c_style_mat,0,0);')
 def declaration(h):
  typename,name,value=h.groups();value=value.strip()
  init=typename+value if value.startswith('(') else value[1:].strip()
  expr=expression(init)
  if init=='view':
   kind,c,rr=re.fullmatch(r'(float|double)([234])x([234])',typename).groups()
   ty={'float':'f32','double':'f64'}[kind]
   expr=f'm::M::<{ty},{c},{rr}>::from_matrix(&view.read())'
  if name=='mat' and '.view<' in body:expr='m::Shared::new('+expr+')'
  return f'let mut {name} = {expr};'
 code=re.sub(r'\b((?:float|double)[234]x[234])\s+(\w+)\s*(\([^;]*\)|=\s*[^;]+);',declaration,code)
 code=re.sub(r'\b(float[234])\s+(\w+)\s*=\s*([^;]+);',lambda h:'let '+h[2]+'='+expression(h[3])+';',code)
 code=re.sub(r'\.view<([0-9, ]+)>\(\)',lambda h:'.view::<'+','.join(split_args(h[1])[:2])+'>('+','.join((split_args(h[1])+['0','0'])[2:4])+')',code)
 code=code.replace('auto view =','let view =')
 def view_assignment(h):
  lhs,op,rhs=h.groups();rhs=expression(rhs)
  if rhs.startswith('normalize('):rhs='m::normalize('+rhs[len('normalize('):-1]+'.read())'
  elif rhs.startswith('mat.view::<'):rhs=rhs+'.read()'
  elif rhs=='-view':rhs='-view.read()'
  elif rhs=='view':rhs='view.read()'
  if op!='=':rhs=lhs+'.read() '+op[:-1]+' ('+rhs+')'
  return lhs+'.assign('+rhs+');'
 code=re.sub(r'(?m)^\s*(mat\.view::<[0-9,]+>\([0-9,]+\)|view|c_mat_mutable_view)\s*(\+=|-=|\*=|=)(?!=)\s*([^;]+);',view_assignment,code)
 code=re.sub(r'\b(view|c_mat_view)\s*\*',r'\1.read() *',code)
 code=re.sub(r'\*\s*(view|c_mat_view)\b(?!\.read)',r'* \1.read()',code)
 for old,new in [('EXPECT_EQ(','EQ'),('EXPECT_M4_NEAR(','M4')]:
  def assertion(args,new=new):
   parts=[expression(x) for x in split_args(args)]
   if new=='M4':
    assert len(parts)==3
    return '{'+''.join(f'near!(r, {parts[0]}.get({i},{j}),{parts[1]}.get({i},{j}),{parts[2]});' for i in range(4) for j in range(4))+'}'
   assert len(parts)==2
   scalar=bool(re.search(r'(\.get\(\d,\d\)|\[[0-9]+\])$',parts[0]))
   return ('numeq' if scalar else 'eq')+'!(r, '+', '.join(parts)+')'
  code=rewrite_calls(code,old,assertion)
 code=expression(code)
 if re.search(r'\bEXPECT_|\bfloat[234]x|\bdouble[234]x|\bauto\b',code):raise ValueError('Untranslated '+identity+'\n'+code)
 return code

def generate(root=ROOT):
 raw=(root/'.upstream/blender'/SOURCE).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==SHA,'Changed upstream matrix source'
 assert json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']==PIN
 out=HEADER;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
 for identity,body,line in extract(raw.decode()):
  text=translate(body,identity);fn=identity.replace('.','__')
  sites=len(re.findall(r'\bEXPECT_(?:EQ|M4_NEAR)\s*\(',comments(body)))
  count=len(re.findall(r'\bEXPECT_EQ\s*\(',comments(body)))+16*len(re.findall(r'\bEXPECT_M4_NEAR\s*\(',comments(body)))
  assert count==len(re.findall(r'\b(?:eq|numeq|near)!',text)),identity
  out+=f'\n// {SOURCE}:{line}\npub fn {fn}()->Report{{let mut r=Report::default();\n{text}\nr\n}}\n'
  cases.append({'id':identity,'path':SOURCE,'line':line,'source_sha256':SHA,'rust_function':fn,'assertion_count':sites,'expected_runtime_assertions':count,'index':len(cases),'status':'ported_unexecuted'})
  native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::matrix_type_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
 out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/matrix_type_cases.rs').write_text(out)
 (root/'crates/blended-core/tests/upstream_matrix_types.rs').write_text(native)
 (root/'tests/upstream/blender'/Path(SOURCE).name).write_bytes(raw)
 (root/'compatibility/matrix-type-ports.json').write_text(json.dumps({'schema':1,'upstream_commit':PIN,'source_files':{Path(SOURCE).name:SHA},'cases':cases,'complete_blender_test_port':False,'notes':'Complete runtime family. Matrix macro checks retain all scalar NEAR assertions. Shared views observe and mutate original storage; no SIMD/performance equivalence claim.'},indent=2)+'\n')
 return cases
if __name__=='__main__':
 c=generate();print(len(c),sum(x['expected_runtime_assertions'] for x in c))
