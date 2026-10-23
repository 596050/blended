#!/usr/bin/env python3
"""One-time registration of the reviewed geometry family. Not a coverage waiver."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
def change(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Unexpected integration input '+path+': '+old)
 p.write_text(s.replace(old,new))
def main():
 expected={'crates/blended-core/src/geometry_math_cases.rs':'2333ef82a58d7efd859a9499f4d5be113ea48c1e0e9fe436799a0acbbad96afd','crates/blended-core/tests/upstream_geometry_math.rs':'39da2d7a11320e8f25dee572822810aedbab99bd19bcfb9927891fe14d4def86','compatibility/geometry-math-ports.json':'efa128614bf7d63883a9985aa77018fbaa22fd001854952f78ea87a1d7b1e45f'}
 for path,want in expected.items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=want:raise ValueError('Reviewed test changed: '+path)
 p=ROOT/'crates/blended-core/src/lib.rs';s=p.read_text()
 if 'pub mod geometry_math;' in s:raise ValueError('Batch already integrated')
 p.write_text(s+'''\npub mod geometry_math;
pub mod geometry_math_cases;
#[unsafe(no_mangle)]
pub extern "C" fn blended_geometry_math_case_count()->u32 {geometry_math_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_geometry_math_run_case(index:u32)->i32 {
    geometry_math_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_geometry_math_assertion_count(index:u32)->u32 {
    geometry_math_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}
''')
 change('tools/port_registry.py','\n)\nTOTAL_KEYS',"\n    Group('geometry_math','geometry-math-ports.json','geometry_math_cases','upstream_geometry_math','port_geometry_math_tests.py','geometry_math_assertions',('blended_geometry_math_case_count','blended_geometry_math_run_case','blended_geometry_math_assertion_count')),\n)\nTOTAL_KEYS")
 manifest=json.loads((ROOT/'compatibility/geometry-math-ports.json').read_text());p=ROOT/'compatibility/assertion-contracts.lock.json';lock=json.loads(p.read_text())
 if lock['reference_commit']!=PIN or manifest['upstream_commit']!=PIN:raise ValueError('Reference drift')
 for name,digest in manifest['source_files'].items():
  path='source/blender/blenlib/tests/'+name
  lock['contracts'].append(dict(source_path=path,source_sha256=digest,target_path='crates/blended-core/src/geometry_math_cases.rs',target_sha256=expected['crates/blended-core/src/geometry_math_cases.rs'],case_ids=[c['id'] for c in manifest['cases'] if c['path']==path]))
 p.write_text(json.dumps(lock,indent=2)+'\n')
 change('tools/assertion_fidelity.py',"'numeric_type_cases.rs','matrix_type_cases.rs']:","'numeric_type_cases.rs','matrix_type_cases.rs','geometry_math_cases.rs']:")
 change('tools/assertion_fidelity.py','        changes={\n','        changes={\n'+'''          'macro_rules! fatal_yes ': 'macro_rules! fatal_yes {($r:expr,$a:expr)=>{{let p=crate::fidelity_trace::boolean("ASSERT_TRUE",$a);$r.check(p,stringify!($a),line!());if !p{return $r;}}};}',
''')
 change('tools/assertion_fidelity.py',"'TRUE':1,'FALSE':1","'TRUE':1,'FALSE':1,'ASSERT_TRUE':1")
 change('tools/fidelity/trace.rs',' TAPE.with(|t|t.borrow().1.clone())',' for (id,run,count) in crate::geometry_math_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}\n TAPE.with(|t|t.borrow().1.clone())')
 p=ROOT/'tools/fidelity/trace.hh';s=p.read_text();anchor='inline void no(bool v){record("FALSE",!v,nullptr,nullptr,v);EXPECT_FALSE(v);}'
 if s.count(anchor)!=1:raise ValueError('Unexpected C++ overlay')
 s=s.replace(anchor,anchor+'\ninline bool fatal_true(bool v){record("ASSERT_TRUE",v,nullptr,nullptr,v);return v;}')
 s+='\n// Keep the fatal assertion at the test call site, not inside a returning wrapper.\n#undef ASSERT_TRUE\n#define ASSERT_TRUE(v) GTEST_ASSERT_TRUE(::blended_fidelity::fatal_true(bool(v)))\n';p.write_text(s)
 for path in ('tests/test_collection_port.py','tests/test_extended_port.py','tests/test_numeric_types.py','tests/test_port_workbench.py'):
  p=ROOT/path;s=p.read_text().replace('272','302').replace('16248','16402')
  if 'test_collection_port' in path or 'test_numeric_types' in path:s=s.replace("['contracts']),21)","['contracts']),23)")
  if 'test_port_workbench' in path:s=s.replace("'matrix_type_assertions':0,","'matrix_type_assertions':0,'geometry_math_assertions':0,")
  p.write_text(s)
 print('Registered 30 source-locked cases; original C++ and public-URL verification still required.')
if __name__=='__main__':main()
