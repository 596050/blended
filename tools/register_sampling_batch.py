#!/usr/bin/env python3
"""Register precisely reviewed generated cases. Execution evidence is separate."""
from pathlib import Path
import hashlib,json
from port_sampling_tests import generate,FILES,PIN
ROOT=Path(__file__).resolve().parents[1]
REVIEWED={'sampling_cases':'d9ece2c730c3bc7915a8100db556ff155d3130a1725bbec5253222710c056e16','curve_cases':'e9e98b4818d3ccd4e2f3dd6f700a18151816ef0bcdaca55c24f33d9d7fea98aa'}
BATCH=[('sampling','sampling-ports.json','sampling_cases','upstream_sampling','sampling_assertions','image_sampling'),('curves','curve-ports.json','curve_cases','upstream_curves','curve_assertions','curve_sampling')]
def edit(name,before,after):
 p=ROOT/name;s=p.read_text()
 if after in s:return
 if s.count(before)!=1:raise ValueError('Unexpected integration preimage: '+name)
 p.write_text(s.replace(before,after,1))
def register():
 cases=generate(ROOT)
 if len(cases)!=36 or sum(c['expected_runtime_assertions'] for c in cases)!=402:raise ValueError('New runtime universe changed')
 contract_path=ROOT/'compatibility/assertion-contracts.lock.json';contracts=json.loads(contract_path.read_text())
 for name,manifest,module,suite,total,implementation in BATCH:
  target='crates/blended-core/src/'+module+'.rs';digest=hashlib.sha256((ROOT/target).read_bytes()).hexdigest()
  if digest!=REVIEWED[module]:raise ValueError('Unreviewed translation: '+module)
  data=json.loads((ROOT/'compatibility'/manifest).read_text());filename=next(iter(data['source_files']))
  contract={'source_path':'source/blender/blenlib/tests/'+filename,'source_sha256':FILES[filename],'target_path':target,'target_sha256':digest,'case_ids':[c['id'] for c in data['cases']]}
  existing=[c for c in contracts['contracts'] if c['target_path']==target]
  if existing and existing!=[contract]:raise ValueError('Conflicting assertion contract')
  if not existing:contracts['contracts'].append(contract)
  p=ROOT/'crates/blended-core/src/lib.rs';s=p.read_text()
  block=f'''
pub mod {implementation};
pub mod {module};
#[unsafe(no_mangle)]pub extern "C" fn blended_{name}_case_count()->u32{{{module}::CASES.len() as u32}}
#[unsafe(no_mangle)]pub extern "C" fn blended_{name}_run_case(index:u32)->i32{{{module}::CASES.get(index as usize).map(|(_,run,n)|{{let r=run();i32::from(r.passed()&&r.assertions==*n)}}).unwrap_or(-1)}}
#[unsafe(no_mangle)]pub extern "C" fn blended_{name}_assertion_count(index:u32)->u32{{{module}::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}}
'''
  if 'pub mod '+module+';' not in s:p.write_text(s+block)
  group=f"    Group('{name}','{manifest}','{module}','{suite}','port_sampling_tests.py','{total}',('blended_{name}_case_count','blended_{name}_run_case','blended_{name}_assertion_count')),\n"
  edit('tools/port_registry.py',')\nTOTAL_KEYS',group+')\nTOTAL_KEYS')
  edit('tools/assertion_fidelity.py',"'geometry_math_cases.rs']",f"'{module}.rs','geometry_math_cases.rs']")
  run=f' for (id,run,count) in crate::{module}::CASES{{start(id);let r=run();end(r.passed()&&r.assertions==*count);}}\n'
  edit('tools/fidelity/trace.rs',' TAPE.with(|t|t.borrow().1.clone())',run+' TAPE.with(|t|t.borrow().1.clone())')
 contract_path.write_text(json.dumps(contracts,indent=2)+'\n')
 # These are infrastructure universe tests, never upstream expectations.
 for name in ['test_extended_port.py','test_geometry_math_port.py','test_port_workbench.py','test_collection_port.py','test_numeric_types.py']:
  p=ROOT/'tests'/name;s=p.read_text().replace(',302)',',338)').replace(',16402)',',16804)').replace("len(contracts(ROOT)['contracts']),23)","len(contracts(ROOT)['contracts']),25)");p.write_text(s)
 edit('tests/test_port_workbench.py',"'geometry_math_assertions':0,", "'geometry_math_assertions':0,'sampling_assertions':0,'curve_assertions':0,")
 if json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong pin')
if __name__=='__main__':register()
