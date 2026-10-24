#!/usr/bin/env python3
"""One-time reviewed registration; CI never automatically approves target hashes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Registration baseline changed: '+path)
 p.write_text(s.replace(old,new))
def main():
 # Record the twelve shared original EXPECT sites separately from loop executions.
 replace('tools/port_polyfill_tests.py','flag=flag,expected_runtime_assertions=count,index=', 'flag=flag,assertion_count=12,expected_runtime_assertions=count,index=')
 from port_polyfill_tests import generate,SOURCE,SHA
 cases=generate();p=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod polyfill;' in p.read_text():raise ValueError('Already registered; no hash refresh')
 with p.open('a') as f:f.write('''
pub mod polyfill;
pub mod polyfill_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_polyfill_case_count()->u32{polyfill_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_polyfill_run_case(index:u32)->i32{polyfill_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_polyfill_assertion_count(index:u32)->u32{polyfill_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('polyfill','polyfill-ports.json','polyfill_cases','upstream_polyfill','port_polyfill_tests.py','polyfill_assertions',('blended_polyfill_case_count','blended_polyfill_run_case','blended_polyfill_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/assertion_fidelity.py',"'pixel_format_cases.rs']:","'pixel_format_cases.rs','polyfill_cases.rs']:")
 replace('tools/assertion_fidelity.py','        changes={', '        changes={\n          \'macro_rules! ne \': \'macro_rules! ne {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::ne($a,$b),stringify!($a != $b),line!());}};}\',')
 replace('tools/assertion_fidelity.py',"arity={'EQ':2,", "arity={'EQ':2,'NE':2,")
 replace('tools/fidelity/trace.rs','pub fn eq<T:PartialEq+Value>', 'pub fn ne<T:PartialEq+Value>(a:T,b:T)->bool{let p=a!=b;record("NE",p,&[a.encode(),b.encode()]);p}\npub fn eq<T:PartialEq+Value>')
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))',' for (id,run,n) in crate::polyfill_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))')
 replace('tools/fidelity/trace.hh','template<class A,class B> void gt(', 'template<class A,class B> void ne(const A&a,const B&b){record("NE",a!=b,nullptr,nullptr,a,b);EXPECT_NE(a,b);}\ntemplate<class A,class B> void gt(')
 with (ROOT/'tools/fidelity/trace.hh').open('a') as f:f.write('\n#undef EXPECT_NE\n#define EXPECT_NE(a,b) ::blended_fidelity::ne((a),(b))\n')
 target='crates/blended-core/src/polyfill_cases.rs';p=ROOT/'compatibility/assertion-contracts.lock.json';data=json.loads(p.read_text())
 data['contracts'].append(dict(source_path=SOURCE,source_sha256=SHA,target_path=target,target_sha256=hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),case_ids=[c['id'] for c in cases]))
 p.write_text(json.dumps(data,indent=2)+'\n')
 from port_workbench import expected_cases
 current,_=expected_cases();assert len(current)==541 and sum(c['expected_runtime_assertions'] for c in current)==3196218
 # Infrastructure totals only, never original expected values or tolerances.
 names=('test_collection_port.py','test_data_port.py','test_extended_port.py','test_geometry_math_port.py','test_heap_port.py','test_numeric_types.py','test_port_workbench.py','test_sampling_integration.py','test_sampling_port.py','test_string_ops_port.py','test_utf8_port.py','test_pixel_format_port.py')
 for name in names:
  p=ROOT/'tests'/name;s=p.read_text();new=s.replace(',512)',',541)').replace(',1661546)',',3196218)').replace("['contracts']),38)","['contracts']),39)")
  if name=='test_port_workbench.py':new=new.replace("'pixel_format_assertions':0,","'pixel_format_assertions':0,'polyfill_assertions':0,")
  if new==s:raise ValueError('Expected infrastructure update missing: '+name)
  p.write_text(new)
if __name__=='__main__':main()
