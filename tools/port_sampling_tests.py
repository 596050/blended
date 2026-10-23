#!/usr/bin/env python3
"""Source-locked image interpolation and curve sampling test translations.

This is not a general translator. Original data, expectations, macro expansions,
helper assertions, loop sizes and infinity smoke operations are retained. Changed
or unsupported input is an error, never a silently omitted case.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract,split_args,rewrite_calls
from port_numeric_type_tests import comments,numbers
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={'BLI_math_interp_test.cc': '1057f15ff1a473a157e4fbf81fdaed258b1105a0f54e860c4b6df43d228be28e', 'BLI_length_parameterize_test.cc': '4c7aa638696fccf0e794e0a5d0d949796ee57f6863d7444774ea18ad926cf0a3'}
HEAD='''// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from hash-locked Blender test sources; do not edit expected values.
#![allow(non_snake_case,non_upper_case_globals,unused_mut,unused_assignments,unused_parens,unused_macros)]
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b within $e),line!());}};}
macro_rules! near4 {($r:expr,$a:expr,$b:expr,$e:expr)=>{{let a=$a;let b=$b;for i in 0..4 {near!($r,a[i],b[i],$e);}}};}
'''
CURVE_COUNTS={'FloatSimple':7,'Float':39,'Float2':24,'Float2Cyclic':24,'LineMany':20,'CyclicMany':40,'InterpolateColor':40,'ArbitraryFloatSimple':4,'ArbitraryFloat2':24}

def init(raw,ty):
 raw=raw.strip()
 if raw.startswith('{'):
  if not raw.endswith('}'):raise ValueError('Invalid initializer')
  return '['+', '.join(init(x,ty) for x in split_args(raw[1:-1]) if x.strip())+']'
 return '('+numbers(raw)+') as '+ty

def image_header(text):
 out='use crate::image_sampling::*;\n'
 for cpp,rust in [('float','f32'),('int','usize')]:
  for name,value in re.findall(r'static constexpr '+cpp+r' (\w+) = ([^;]+);',text):out+=f'const {name}:{rust}=({numbers(value)}) as {rust};\n'
 for name,ty in [('image_char','u8'),('image_fl','f32')]:
  m=re.search(name+r'\[image_height\]\[image_width\]\[4\] = (\{.*?\});',text,re.S)
  if not m:raise ValueError('Missing original image data')
  vals=re.findall(r'[-+]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?f?',m[1])
  if len(vals)!=36:raise ValueError('Image shape changed')
  out+=f'const {name}:[{ty};36]=['+', '.join('('+numbers(v)+') as '+ty for v in vals)+'];\n'
 return out

def image_expr(s):
 s=numbers(s.strip()).replace('image_char[0][0]','&image_char').replace('image_fl[0][0]','&image_fl').replace('INFINITY','f32::INFINITY')
 for name,ty in [('int4','i32'),('uint4','u32')]:s=rewrite_calls(s,name+'(',lambda a,ty=ty:'('+a+').map(|v|v as '+ty+')')
 return s

def image_translate(body):
 s=comments(body)
 def declaration(m):
  typ,name,value=m.groups();ty={'uchar4':'u8','uint4':'u32','float4':'f32'}[typ]
  return f'let mut {name}:[{ty};4] = '+(init(value,ty) if value else '['+('0.0' if ty=='f32' else '0')+';4]')+';'
 s=re.sub(r'\b(uchar4|uint4|float4)\s+(\w+)\s*(?:=\s*(\{[^;]*\}))?;',declaration,s)
 functions=set(re.findall(r'\b(interpolate_\w+)\(',s))
 for name in functions:
  def call(a,name=name):
   args=[image_expr(x) for x in split_args(a)]
   if 'wrapmode' in name:
    if len(args)!=9:raise ValueError('Unsupported wrapmode call')
    args[1]='&mut '+args[1];coord=(5,6)
   else:
    if len(args)!=5:raise ValueError('Unsupported sample call')
    coord=(3,4)
   for i in coord:args[i]='('+args[i]+') as f32'
   return name+'('+', '.join(args)+')'
  s=rewrite_calls(s,name+'(',call)
 for source,macro in [('EXPECT_EQ','eq'),('EXPECT_V4_NEAR','near4')]:
  s=rewrite_calls(s,source+'(',lambda a,macro=macro:macro+'!(report, '+', '.join(image_expr(x) for x in split_args(a))+')')
 if re.search(r'\bEXPECT_|\b(?:uchar4|float4|uint4)\b',s):raise ValueError('Untranslated image syntax')
 return s

def curve_translate(body):
 s=comments(body)
 def array(m):
  ty,name,rhs=m.groups();scalar={'int':'i32','float':'f32','float2':'f32','ColorGeometry4f':'f32'}[ty]
  rust={'int':'i32','float':'f32','float2':'[f32;2]','ColorGeometry4f':'[f32;4]'}[ty];rhs=rhs.strip()
  if rhs.startswith('='):
   value=rhs[1:].strip().replace('.as_span()','')
   value=rewrite_calls(value,'calculate_lengths(',lambda a:'calculate_lengths(&'+a+')')
  elif rhs.startswith('('):
   args=rhs[1:-1].strip()
   if args.startswith('{'):value='vec!'+init(args,scalar)
   else:value='vec!['+{'int':'0_i32','float':'0.0_f32','float2':'[0.0_f32;2]','ColorGeometry4f':'[0.0_f32;4]'}[ty]+';'+args+']'
  elif rhs.startswith('{') and rhs.endswith('}') and rhs[1:-1].strip().startswith('{'):value='vec!'+init(rhs[1:-1].strip(),scalar)
  else:raise ValueError('Untranslated array '+m[0])
  return f'let mut {name}:Vec<{rust}> = {value};'
 s=re.sub(r'Array<(float2|float|int|ColorGeometry4f)>\s+(\w+)\s*([^;]*);',array,s,flags=re.S)
 s=re.sub(r'for \(const int (\w+) : (\w+)\.index_range\(\)\)',r'for \1 in 0..\2.len()',s)
 s=s.replace('results.as_span().take_back(20)','results[results.len()-20..]')
 s=re.sub(r'\.(x|y|r|g|b|a)\b',lambda m:'['+str({'x':0,'y':1,'r':0,'g':1,'b':2,'a':3}[m[1]])+']',s)
 s=re.sub(r'interpolate<(float2|float|ColorGeometry4f)>', 'interpolate',s)
 for name in ('sample_uniform','sample_at_lengths','interpolate'):
  def call(a,name=name):
   args=split_args(a)
   if len(args)!=4:raise ValueError('Unexpected curve call')
   args[0]='&'+args[0]
   if name!='sample_uniform':args[1]='&'+args[1]
   args[2]=('&' if name=='interpolate' else '&mut ')+args[2]
   args[3]='&mut '+args[3]
   return name+'('+', '.join(args)+')'
  s=rewrite_calls(s,name+'(',call)
 s=rewrite_calls(s,'test_uniform_lengths(',lambda a:'test_uniform_lengths(&mut report, &'+a.replace('.as_span()','')+')')
 s=rewrite_calls(s,'EXPECT_NEAR(',lambda a:'near!(report, '+numbers(a)+')')
 if re.search(r'\bEXPECT_|\bArray<|\.as_span\(|\.index_range\(',s):raise ValueError('Untranslated curve syntax')
 return s

CURVE_HELPERS='''use crate::curve_sampling::*;
// Translated upstream helpers, including every EXPECT_NEAR in test_uniform_lengths.
fn calculate_lengths<T:CurveValue>(values:&[T],cyclic:bool)->Vec<f32>{
 let mut lengths=vec![0.0;segments_num(values.len(),cyclic)];
 accumulate_lengths(values,cyclic,&mut lengths);lengths
}
fn test_uniform_lengths<T:CurveValue>(report:&mut Report,values:&[T]){
 let segment_length=values[0].distance(*values.last().unwrap())/((values.len()-1) as f32);
 for i in 0..values.len()-1{near!(report,values[i].distance(values[i+1]),segment_length,1e-5);}
}
'''

def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong pin')
 total=[]
 for filename,digest in FILES.items():
  path='source/blender/blenlib/tests/'+filename;raw=(root/'.upstream/blender'/path).read_bytes();text=raw.decode()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Original source changed: '+path)
  image=filename=='BLI_math_interp_test.cc';module='sampling_cases' if image else 'curve_cases';manifest='sampling-ports.json' if image else 'curve-ports.json';native_suite='upstream_sampling' if image else 'upstream_curves'
  output=HEAD+(image_header(text) if image else CURVE_HELPERS);native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
  for identity,body,line in extract(text):
   translated=image_translate(body) if image else curve_translate(body)
   clean=comments(body);sites=len(re.findall(r'\bEXPECT_(?:EQ|V4_NEAR|NEAR)\(',clean));fn=identity.replace('.','__')
   if sites!=len(re.findall(r'\b(?:eq|near4|near)!',translated)):raise ValueError('Lost assertion site '+identity)
   count=sites+3*clean.count('EXPECT_V4_NEAR(') if image else CURVE_COUNTS[identity.split('.')[1]]
   output+=f'\n// {path}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();\n{translated}\nreport\n}}\n'
   native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::{module}::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
   cases.append(dict(id=identity,path=path,line=line,source_sha256=digest,rust_function=fn,assertion_count=sites,expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
  output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
  (root/'crates/blended-core/src'/f'{module}.rs').write_text(output)
  (root/'crates/blended-core/tests'/f'{native_suite}.rs').write_text(native)
  (root/'tests/upstream/blender'/filename).write_bytes(raw)
  (root/'compatibility'/manifest).write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files={filename:digest},cases=cases,complete_blender_test_port=False,helper_assertion_sites=0 if image else 1,notes='All original runtime cases. Original expectations, sample images, loop sizes, helper assertions and wrap/infinity smoke operation retained. EXPECT_V4_NEAR expands to four original nonfatal scalar comparisons. Curve loops retain 5007 samples. Array/colour storage uses safe Rust slices; no thread-performance equivalence asserted.'),indent=2)+'\n')
  total.extend(cases)
 return total
if __name__=='__main__':
 cases=generate();print(json.dumps(dict(cases=len(cases),runtime_assertions=sum(c['expected_runtime_assertions'] for c in cases))))
