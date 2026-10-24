#!/usr/bin/env python3
"""Generate compact case wrappers; original fixture bytes are compiled into WASM."""
from pathlib import Path
import hashlib,json
from port_polyfill_tests import ROOT,PIN,SOURCE,SHA,HEADER,parse,extract
FIXTURE='''
/// Source-locked input data, not expectations produced by the triangulator.
pub fn fixture(name:&str)->Vec<[f32;2]>{
 const SOURCE:&str=include_str!("../../../tests/upstream/blender/BLI_polyfill_2d_test.cc");
 let marker=format!("TEST(polyfill2d, {name})");
 let body=SOURCE.split_once(&marker).expect("Unknown original case").1;
 let values=body.split_once("const float poly[][2] = {").expect("Original fixture declaration").1.split_once("};").expect("Original fixture terminator").0;
 let numbers=values.split(|c:char|c==','||c=='{'||c=='}'||c.is_ascii_whitespace()).filter(|s|!s.is_empty()).map(|s|s.strip_suffix('f').unwrap_or(s).parse::<f32>().expect("Source-locked numeric literal")).collect::<Vec<_>>();
 assert_eq!(numbers.len()%2,0);numbers.chunks_exact(2).map(|v|[v[0],v[1]]).collect()
}
'''
def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Reference changed')
 raw=(root/'.upstream/blender'/SOURCE).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Source changed; re-review all helper semantics')
 out=HEADER+FIXTURE+'\nmacro_rules! original_case {($f:ident,$name:literal,$flag:expr)=>{pub fn $f()->Report{let mut r=Report::default();let poly=fixture($name);run_original(&mut r,$flag,&poly);r}};}\n';cases=[];native='// SPDX-License-Identifier: Apache-2.0\nmacro_rules! original {($name:ident,$n:expr)=>{#[test] #[allow(non_snake_case)] fn $name(){let r=blended_core::polyfill_cases::$name();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,$n);}};}\n'
 for identity,body,line in extract(raw.decode()):
  points,bits,flag,count=parse(body);fn=identity.replace('.','__');name=identity.split('.')[1]
  out+=f'original_case!({fn},"{name}",{flag});\n'
  native+=f'original!({fn},{count});\n'
  cases.append(dict(id=identity,path=SOURCE,line=line,source_sha256=SHA,source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,polygon_size=len(points),flag=flag,assertion_count=12,expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
 assert len(cases)==29 and sum(c['expected_runtime_assertions'] for c in cases)==1534672
 out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/polyfill_cases.rs').write_text(out)
 (root/'crates/blended-core/tests/upstream_polyfill.rs').write_text(native)
 (root/'tests/upstream/blender/BLI_polyfill_2d_test.cc').write_bytes(raw)
 data=dict(schema=1,upstream_commit=PIN,source_sha256=SHA,cases=cases,complete_blender_test_port=False,helper_scope='Original 12 shared EXPECT sites and full loops; both plain and beautified output. Original reversal/cycling modifies a copy but tests the unmodified poly; genuine permutations are supplemental.',configurations={'USE_COMBINATIONS_ALL':True,'USE_BEAUTIFY':True,'USE_OBJ_PREVIEW':False})
 (root/'compatibility/polyfill-ports.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
 return cases
if __name__=='__main__':
 c=generate();print(len(c),sum(x['expected_runtime_assertions'] for x in c))
