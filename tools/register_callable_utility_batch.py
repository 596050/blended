#!/usr/bin/env python3
"""One-time reviewed registration for callable/iterator/session runtime cases.

This writes the explicit registry/contract/fidelity wiring and updates only
known subset-accounting guards. It must not be used to auto-approve changed
translated test bodies.
"""
from pathlib import Path
import hashlib,json
from port_callable_utility_tests import generate,FILES,CASES
ROOT=Path(__file__).resolve().parents[1]

def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError("Reviewed registration target changed: "+path)
 p.write_text(s.replace(old,new))

def main():
 cases=generate(ROOT)
 if len(cases)!=15 or sum(c["expected_runtime_assertions"] for c in cases)!=30:
  raise ValueError("Callable utility universe changed")
 target="crates/blended-core/src/callable_utility_cases.rs"
 target_hash=hashlib.sha256((ROOT/target).read_bytes()).hexdigest()

 # Explicit executable group.
 replace("tools/port_registry.py","\n)\nTOTAL_KEYS=",
 """\n    Group('callable_utils','callable-utility-ports.json','callable_utility_cases','upstream_callable_utils','port_callable_utility_tests.py','callable_utility_assertions',('blended_callable_utils_case_count','blended_callable_utils_run_case','blended_callable_utils_assertion_count')),\n)\nTOTAL_KEYS=""")

 # Explicit reviewed contract shard, one entry per complete source file.
 contracts=[]
 for name,(path,digest) in FILES.items():
  contracts.append(dict(source_path=path,source_sha256=digest,target_path=target,target_sha256=target_hash,
                        case_ids=[c["id"] for c in cases if c["path"]==path]))
 shard=dict(schema=1,reference_commit="94363991e7dcf39e2d70614aa002ab6f67764a5d",contracts=contracts)
 (ROOT/"compatibility/callable-utility-assertion-contract.lock.json").write_text(json.dumps(shard,indent=2)+"\n")
 replace("tools/contract_registry.py",'"compatibility/container-view-assertion-contract.lock.json")',
         '"compatibility/container-view-assertion-contract.lock.json","compatibility/callable-utility-assertion-contract.lock.json")')

 # Build-only assertion recorder. Production tests remain unchanged.
 replace("tools/assertion_fidelity.py","'mask_expression_cases.rs','container_view_cases.rs']",
         "'mask_expression_cases.rs','container_view_cases.rs','callable_utility_cases.rs']")
 replace("tools/fidelity/trace.rs",
         " for (id,run,n) in crate::container_view_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with",
         " for (id,run,n) in crate::container_view_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n for (id,run,n) in crate::callable_utility_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with")

 # Exact subset totals and reviewed-contract totals. Do not touch snapshots.
 guard_files=[
  "test_collection_port.py","test_container_view_port.py","test_data_port.py","test_extended_port.py",
  "test_geometry_math_port.py","test_heap_port.py","test_mask_expression_port.py","test_pixel_format_port.py",
  "test_polyfill_port.py","test_sampling_port.py","test_span_port.py","test_string_ops_port.py",
  "test_utf8_port.py","test_sampling_integration.py",
 ]
 for name in guard_files:
  p=ROOT/"tests"/name;s=p.read_text()
  changed=s.replace(",609)",",624)").replace(",3196744)",",3196774)").replace("),43)", "),46)")
  if name=="test_port_workbench.py":
   changed=changed.replace("'container_view_assertions':0,","'container_view_assertions':0,'callable_utility_assertions':0,")
  if changed==s:raise ValueError("Expected subset guard absent: "+name)
  p.write_text(changed)
 # test_port_workbench is not in the list above because its formatting differs.
 p=ROOT/"tests/test_port_workbench.py";s=p.read_text()
 changed=s.replace(",609)",",624)").replace(",3196744)",",3196774)").replace("'container_view_assertions':0,","'container_view_assertions':0,'callable_utility_assertions':0,")
 if changed==s:raise ValueError("Expected workbench guard absent")
 p.write_text(changed)

 # Contract-count guards may be formatted independently.
 for name in ["test_collection_port.py","test_geometry_math_port.py","test_mask_expression_port.py","test_sampling_integration.py"]:
  p=ROOT/"tests"/name;s=p.read_text();s2=s.replace("['contracts']),43)","['contracts']),46)")
  if s2!=s:p.write_text(s2)

if __name__=="__main__":main()
