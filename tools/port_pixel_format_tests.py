#!/usr/bin/env python3
"""Source-locked half-float/normalised-format cases, not a general translator.

Eight enabled half tests and one normalised-int test. Five explicitly disabled
DO_PERF_TESTS cases remain inventoried but unported; never count them as passes.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract,split_args,rewrite_calls
from port_numeric_type_tests import comments
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={
 'BLI_math_half_test.cc':'508ccd5a21a2dd191154b07e7a273fa5b04239be30c1c149737c5dd7f1e5fac9',
 'BLI_normalized_int_test.cc':'06537f28199781c45d94ddadf080f386e0c54bec7c907b9413f22d867d1e35c0',
}
HEAD='''// SPDX-FileCopyrightText: 2024-2026 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked tests; see compatibility/pixel-format-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::pixel_formats as m;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$v:expr)=>{{$r.check($v,stringify!($v),line!());}};}
fn array_eq<T:PartialEq+Copy>(report:&mut Report,a:&[T],b:&[T],n:usize){for i in 0..n{eq!(report,a[i],b[i]);}}
'''

def expr(s):
 s=s.strip().replace('math::','m::')
 mapping={'min()':'f32::MIN_POSITIVE','max()':'f32::MAX','infinity()':'f32::INFINITY','quiet_NaN()':'f32::from_bits(0x7fc00000)','signaling_NaN()':'f32::from_bits(0x7fa00000)'}
 for old,new in mapping.items():s=s.replace('std::numeric_limits<float>::'+old,new)
 s=re.sub(r'(\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)f\b',r'\1_f32',s)
 s=rewrite_calls(s,'std::isnan(',lambda a:expr(a)+'.is_nan()')
 return s

def translate(body,name):
 s=comments(body);macro=re.search(r'^#define HFUN\(v\) math::(\w+)\(v\)\s*$',s,re.M)
 if macro:
  s=re.sub(r'^#(?:define HFUN[^\n]*|undef HFUN)\s*$', '',s,flags=re.M)
  s=s.replace('HFUN(', 'math::'+macro[1]+'(')
 count=len(re.findall(r'\bEXPECT_(?:EQ|TRUE)\(',s))
 for n in re.findall(r'EXPECT_EQ_ARRAY\([^;]*?,\s*(\d+)\)',s):count+=int(n)
 for kind,macro in [('EQ','eq'),('TRUE','yes')]:s=rewrite_calls(s,'EXPECT_'+kind+'(',lambda a,macro=macro:macro+'!(report, '+', '.join(expr(x) for x in split_args(a))+')')
 s=rewrite_calls(s,'EXPECT_EQ_ARRAY(',lambda a:'array_eq(&mut report, '+', '.join('&'+x if i<2 else x for i,x in enumerate(split_args(a)))+')')
 if name=='BLI_math_half_test.cc':
  def array(m):
   const,typ,var,n,values=m.groups();t={'float':'f32','uint16_t':'u16'}[typ]
   value='['+expr(values)+']' if values.strip() else ('[0.0_f32;'+n+']' if t=='f32' else '[0_u16;'+n+']')
   return f'let mut {var}:[{t};{n}]={value};'
  s=re.sub(r'(const )?(float|uint16_t) (\w+)\[(\d+)\]\s*=\s*\{(.*?)\};',array,s,flags=re.S)
  s=s.replace('const ScopedFlushToZero flush_to_zero;', 'let _flush_to_zero=m::ScopedFlushToZero::new();')
  for method in ['half_to_float_array','float_to_half_array','float_to_half_make_finite_array','float_to_half_clamp_array']:
   s=rewrite_calls(s,'math::'+method+'(',lambda a,method=method:'m::'+method+'(&'+split_args(a)[0]+', &mut '+split_args(a)[1]+', '+', '.join(expr(x) for x in split_args(a)[2:])+')')
  s=expr(s)
 else:
  s=re.sub(r'const float([24]) a\((.*?)\);',lambda m:'let a:[f32;'+m[1]+']=['+expr(m[2])+'];',s)
  s=re.sub(r'float[24]\((\w+_norm)\(a\)\)',r'm::\1(a).to_float()',s)
 if re.search(r'EXPECT_|math::|std::|#|ScopedFlushToZero flush|\b(?:float|uint16_t)\b',s):raise ValueError('Untranslated syntax '+s)
 return s,count

def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong pinned Blender commit')
 out=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[];conditional=[]
 for name,digest in FILES.items():
  path='source/blender/blenlib/tests/'+name;raw=(root/'.upstream/blender'/path).read_bytes();text=raw.decode()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Original source changed: '+path)
  active=text
  if name=='BLI_math_half_test.cc':
   if text.count('#ifdef DO_PERF_TESTS')!=2:raise ValueError('Conditional region changed')
   active,disabled=text.split('#ifdef DO_PERF_TESTS',1)
   for identity,body,line in extract(disabled):conditional.append(dict(id=identity,path=path,kind='TEST',status='unported_conditional_performance_case',condition='DO_PERF_TESTS',enabled_in_reference_config=False))
   if len(conditional)!=5:raise ValueError('Conditional case universe changed')
  for identity,body,line in extract(active):
   translated,count=translate(body,name);fn=identity.replace('.','__')
   out+=f'\n// {path}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();\n{translated}\nreport\n}}\n'
   native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::pixel_format_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
   cases.append(dict(id=identity,path=path,line=line,source_sha256=digest,source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=len(re.findall(r'\bEXPECT_\w+\(',body)),expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
  (root/'tests/upstream/blender'/name).write_bytes(raw)
 if len(cases)!=9:raise ValueError('Active case universe changed')
 out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/pixel_format_cases.rs').write_text(out)
 (root/'crates/blended-core/tests/upstream_pixel_formats.rs').write_text(native)
 (root/'compatibility/pixel-format-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files=FILES,cases=cases,conditional_unported_cases=conditional,complete_blender_test_port=False,notes='Preserve all 8 enabled half tests and the normalised-int case. Original EXPECT_EQ_ARRAY expands to n scalar comparisons; vector equality is one array-valued assertion. Native x86_64 scoped FTZ/DAZ changes MXCSR and restores it. Like the pinned C++ fallback, the browser has no accessible FP control register, so it checks values but not a hardware mode perturbation. Five opt-in performance cases are unported, not passed.'),indent=2)+'\n')
 return cases
if __name__=='__main__':
 c=generate();print(json.dumps(dict(cases=len(c),assertion_events=sum(x['expected_runtime_assertions'] for x in c))))
