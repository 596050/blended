#!/usr/bin/env python3
"""One-time source registration. Fixed reviewed hashes are never auto-approved by CI."""
from pathlib import Path
import hashlib,json
from port_mask_expression_tests import generate,PATH,PIN
ROOT=Path(__file__).resolve().parents[1]
REVIEWED='84f8039f2797880492b283ab58f9f455cd30ef9b7e97d18b0275813d8a596a23'
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Registration baseline changed: '+path)
 p.write_text(s.replace(old,new))
def main():
 lib=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod mask_expression_cases;' in lib.read_text():raise ValueError('Already registered; do not refresh hashes')
 cases=generate();target='crates/blended-core/src/mask_expression_cases.rs'
 if hashlib.sha256((ROOT/target).read_bytes()).hexdigest()!=REVIEWED:raise ValueError('Reviewed generated test changed')
 shard=dict(schema=1,reference_commit=PIN,contracts=[dict(source_path=PATH,source_sha256=cases[0]['source_sha256'],target_path=target,target_sha256=REVIEWED,case_ids=[c['id'] for c in cases])])
 (ROOT/'compatibility/mask-expression-assertion-contract.lock.json').write_text(json.dumps(shard,indent=2)+'\n')
 with lib.open('a') as f:f.write('''
pub mod mask_expressions;
pub mod mask_expression_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_expressions_case_count()->u32{mask_expression_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_expressions_run_case(index:u32)->i32{mask_expression_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_expressions_assertion_count(index:u32)->u32{mask_expression_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('mask_expressions','mask-expression-ports.json','mask_expression_cases','upstream_mask_expressions','port_mask_expression_tests.py','mask_expression_assertions',('blended_mask_expressions_case_count','blended_mask_expressions_run_case','blended_mask_expressions_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/contract_registry.py','"compatibility/span-assertion-contract.lock.json")','"compatibility/span-assertion-contract.lock.json","compatibility/mask-expression-assertion-contract.lock.json")')
 replace('tools/assertion_fidelity.py',"'BLI_span_test.cc':'span.hh'", "'BLI_span_test.cc':'span.hh','BLI_index_mask_expression_test.cc':'mask_expression.hh'")
 replace('tools/assertion_fidelity.py',"'polyfill_cases.rs','span_cases.rs']:","'polyfill_cases.rs','span_cases.rs','mask_expression_cases.rs']:")
 replace('tools/assertion_fidelity.py',"'bit_span_cases.rs','data_cases.rs','string_ops_cases.rs'):","'bit_span_cases.rs','data_cases.rs','string_ops_cases.rs','mask_expression_cases.rs'):")
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))',' for (id,run,n) in crate::mask_expression_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))')
 with (ROOT/'tools/fidelity/trace.rs').open('a') as f:f.write('''
// Reversible canonical run encoding, not a cardinality or hash surrogate.
impl Value for crate::mask_expressions::IndexMask {
 fn encode(&self)->String {
  fn varint(out:&mut Vec<u8>,mut v:u64){loop{let b=(v&127) as u8;v>>=7;out.push(b|if v==0{0}else{128});if v==0{break;}}}
  let mut bytes=Vec::new();let mut previous_end=0_i64;
  for &[start,end] in self.canonical_ranges(){varint(&mut bytes,(start-previous_end) as u64);varint(&mut bytes,(end-start) as u64);previous_end=end;}
  format!("{{\\\"mask_runs\\\":{}}}",bytes_value(&bytes))
 }
}
''')
 from port_workbench import expected_cases
 current,_=expected_cases();assert len(current)==596 and sum(c['expected_runtime_assertions'] for c in current)==3196692
 changed=[]
 for path in sorted((ROOT/'tests').glob('test_*.py')):
  before=path.read_text();after=before.replace(',581)',',596)').replace(',3196371)',',3196692)').replace("['contracts']),40)","['contracts']),41)")
  if path.name=='test_port_workbench.py':after=after.replace("'span_assertions':0,","'span_assertions':0,'mask_expression_assertions':0,")
  if after!=before:path.write_text(after);changed.append(path.name)
 print(json.dumps(dict(registered_cases=len(cases),new_assertion_events=321,total_runtime=len(current),infrastructure_only_updates=changed)))
if __name__=='__main__':main()
