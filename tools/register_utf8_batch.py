#!/usr/bin/env python3
"""One-time registration of reviewed source cases. Never auto-refresh hashes in CI."""
from pathlib import Path
import hashlib,json
from port_utf8_tests import generate,PATH,HASH
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Changed registration baseline: '+path)
 p.write_text(s.replace(old,new))
def install():
 p=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod utf8_cases;' in p.read_text():raise ValueError('Already registered')
 cases=generate()
 with p.open('a') as f:f.write('''
pub mod utf8_compat;
pub mod utf8_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_utf8_case_count()->u32{utf8_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_utf8_run_case(index:u32)->i32{utf8_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_utf8_assertion_count(index:u32)->u32{utf8_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('utf8','utf8-ports.json','utf8_cases','upstream_utf8','port_utf8_tests.py','utf8_assertions',('blended_utf8_case_count','blended_utf8_run_case','blended_utf8_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/assertion_fidelity.py',"'data_cases.rs','string_ops_cases.rs']:","'data_cases.rs','string_ops_cases.rs','utf8_cases.rs']:")
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|t.borrow().1.clone())',' for (id,run,n) in crate::utf8_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|t.borrow().1.clone())')
 p=ROOT/'compatibility/assertion-contracts.lock.json';data=json.loads(p.read_text());target='crates/blended-core/src/utf8_cases.rs'
 data['contracts'].append(dict(source_path=PATH,source_sha256=HASH,target_path=target,target_sha256=hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),case_ids=[c['id'] for c in cases]))
 p.write_text(json.dumps(data,indent=2)+'\n')
 from port_workbench import expected_cases
 all_cases,_=expected_cases();assert len(all_cases)==503 and sum(c['expected_runtime_assertions'] for c in all_cases)==1661377
 changed=[]
 for p in (ROOT/'tests').glob('test_*.py'):
  before=p.read_text();after=before.replace(',464)',',503)').replace(',34214)',',1661377)').replace("['contracts']),35)","['contracts']),36)")
  if p.name=='test_port_workbench.py':after=after.replace("'string_ops_assertions':0,","'string_ops_assertions':0,'utf8_assertions':0,")
  if after!=before:p.write_text(after);changed.append(p.name)
 if len(changed)<8:raise ValueError('Subset guard baseline changed')
if __name__=='__main__':install()
