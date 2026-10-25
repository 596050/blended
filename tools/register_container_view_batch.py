#!/usr/bin/env python3
"""One-time registration for reviewed finite translations; not CI hash refreshing."""
from pathlib import Path
import hashlib,json
from port_container_view_tests import generate,FILES,PIN
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Registration baseline changed: '+path)
 p.write_text(s.replace(old,new))
def main():
 lib=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod container_view_cases;' in lib.read_text():raise ValueError('Already registered; no auto-refresh of reviewed targets')
 native=ROOT/'crates/blended-core/tests/upstream_container_views.rs';before=native.read_bytes()
 cases=generate()
 if native.read_bytes()!=before:raise ValueError('Test-first native declarations changed')
 target='crates/blended-core/src/container_view_cases.rs';target_hash=hashlib.sha256((ROOT/target).read_bytes()).hexdigest()
 contract=[]
 for filename,source_hash in FILES.items():
  path='source/blender/blenlib/tests/'+filename
  contract.append(dict(source_path=path,source_sha256=source_hash,target_path=target,target_sha256=target_hash,case_ids=[c['id'] for c in cases if c['path']==path]))
 (ROOT/'compatibility/container-view-assertion-contract.lock.json').write_text(json.dumps(dict(schema=1,reference_commit=PIN,contracts=contract),indent=2)+'\n')
 with lib.open('a') as f:f.write('''
pub mod container_views;
pub mod container_view_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_container_views_case_count()->u32{container_view_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_container_views_run_case(index:u32)->i32{container_view_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_container_views_assertion_count(index:u32)->u32{container_view_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('container_views','container-view-ports.json','container_view_cases','upstream_container_views','port_container_view_tests.py','container_view_assertions',('blended_container_views_case_count','blended_container_views_run_case','blended_container_views_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/contract_registry.py','"compatibility/mask-expression-assertion-contract.lock.json")','"compatibility/mask-expression-assertion-contract.lock.json","compatibility/container-view-assertion-contract.lock.json")')
 replace('tools/assertion_fidelity.py',"'BLI_index_mask_expression_test.cc':'mask_expression.hh'", "'BLI_index_mask_expression_test.cc':'mask_expression.hh','BLI_generic_span_test.cc':'generic_span.hh'")
 replace('tools/assertion_fidelity.py',"'span_cases.rs','mask_expression_cases.rs']:","'span_cases.rs','mask_expression_cases.rs','container_view_cases.rs']:")
 replace('tools/assertion_fidelity.py',"        if name=='span_cases.rs':","        if name=='container_view_cases.rs':\n            changes['macro_rules! peq ']='macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::eq(($a) as *const u8,($b) as *const u8),stringify!($a pointer-equals $b),line!());}};}'\n        if name=='span_cases.rs':")
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))',' for (id,run,n) in crate::container_view_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))')
 from port_workbench import expected_cases
 current,_=expected_cases();assert len(current)==609 and sum(c['expected_runtime_assertions'] for c in current)==3196744
 updates=[]
 for p in sorted((ROOT/'tests').glob('test_*.py')):
  before=p.read_text();after=before.replace(',596)',',609)').replace(',3196692)',',3196744)').replace("['contracts']),41)","['contracts']),43)").replace('len(contracts),41)','len(contracts),43)')
  if p.name=='test_port_workbench.py':after=after.replace("'mask_expression_assertions':0,","'mask_expression_assertions':0,'container_view_assertions':0,")
  if after!=before:p.write_text(after);updates.append(p.name)
 print(json.dumps(dict(registered_cases=len(cases),total_cases=len(current),reviewed_target_sha256=target_hash,infrastructure_only_updates=updates)))
if __name__=='__main__':main()
