#!/usr/bin/env python3
"""One-time reviewed source registration, never automatic CI re-approval."""
from pathlib import Path
import hashlib,json
from port_pixel_format_tests import generate,FILES
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Reviewed registration baseline changed: '+path)
 p.write_text(s.replace(old,new))
def main():
 cases=generate();path=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod pixel_formats;' in path.read_text():raise ValueError('Already registered; no target-hash auto-refresh')
 with path.open('a') as f:f.write('''
pub mod pixel_formats;
pub mod pixel_format_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_pixel_formats_case_count()->u32{pixel_format_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_pixel_formats_run_case(index:u32)->i32{pixel_format_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_pixel_formats_assertion_count(index:u32)->u32{pixel_format_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
#[unsafe(no_mangle)]pub extern "C" fn blended_pixel_formats_hardware_fp_control()->u32{u32::from(pixel_formats::ScopedFlushToZero::hardware_supported())}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('pixel_formats','pixel-format-ports.json','pixel_format_cases','upstream_pixel_formats','port_pixel_format_tests.py','pixel_format_assertions',('blended_pixel_formats_case_count','blended_pixel_formats_run_case','blended_pixel_formats_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/assertion_fidelity.py',"'string_ops_cases.rs','utf8_cases.rs']:","'string_ops_cases.rs','utf8_cases.rs','pixel_format_cases.rs']:")
 replace('tools/assertion_fidelity.py',"        changes={", "        if name=='pixel_format_cases.rs':\n            after=after.replace('fn array_eq<T:PartialEq+Copy>', 'fn array_eq<T:PartialEq+Copy+crate::fidelity_trace::Value>')\n        changes={")
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))',' for (id,run,n) in crate::pixel_format_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))')
 p=ROOT/'compatibility/assertion-contracts.lock.json';data=json.loads(p.read_text());target='crates/blended-core/src/pixel_format_cases.rs'
 for name,digest in FILES.items():
  source='source/blender/blenlib/tests/'+name
  data['contracts'].append(dict(source_path=source,source_sha256=digest,target_path=target,target_sha256=hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),case_ids=[c['id'] for c in cases if c['path']==source]))
 p.write_text(json.dumps(data,indent=2)+'\n')
 from port_workbench import expected_cases
 current,_=expected_cases();assert len(current)==512 and sum(c['expected_runtime_assertions'] for c in current)==1661546
 # Only infrastructure totals change; generated upstream assertion bodies do not.
 names=('test_collection_port.py','test_data_port.py','test_extended_port.py','test_geometry_math_port.py','test_heap_port.py','test_numeric_types.py','test_port_workbench.py','test_sampling_integration.py','test_sampling_port.py','test_string_ops_port.py','test_utf8_port.py')
 for name in names:
  p=ROOT/'tests'/name;s=p.read_text();updated=s.replace(',503)',',512)').replace(',1661377)',',1661546)').replace("['contracts']),36)","['contracts']),38)")
  if name=='test_port_workbench.py':updated=updated.replace("'utf8_assertions':0,","'utf8_assertions':0,'pixel_format_assertions':0,")
  if s==updated:raise ValueError('Expected subset-accounting update missing: '+name)
  p.write_text(updated)
if __name__=='__main__':main()
