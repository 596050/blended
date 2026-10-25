"""Source-lock and semantic-registry regressions, not extra Blender cases."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_callable_utility_tests import FILES,CASES
from port_workbench import expected_cases
from contract_registry import load_contracts

class CallableUtilityPorts(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads((ROOT/'compatibility/callable-utility-ports.json').read_text())
  self.target=(ROOT/'crates/blended-core/src/callable_utility_cases.rs').read_text()
 def test_complete_original_identity_set(self):
  self.assertEqual(len(self.manifest['cases']),15)
  self.assertEqual([c['id'] for c in self.manifest['cases']],[c[0] for c in CASES])
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in self.manifest['cases']),30)
 def test_snapshots_match_locked_source_hashes(self):
  for name,(path,digest) in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes()
   self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
 def test_executable_registry_matches_manifest(self):
  registry=[(m.group(1),int(m.group(2))) for m in re.finditer(r'\("([^"]+)",\s*[A-Za-z0-9_]+,\s*(\d+)\)',self.target)]
  self.assertEqual(registry,[(c['id'],c['expected_runtime_assertions']) for c in self.manifest['cases']])
 def test_current_global_union(self):
  cases,_=expected_cases();self.assertEqual(len(cases),624);self.assertEqual(len({c['id'] for c in cases}),624)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196774)
 def test_reviewed_contracts_include_all_three_sources(self):
  contracts=load_contracts(ROOT)['contracts'];self.assertEqual(len(contracts),46)
  target=[c for c in contracts if c['target_path'].endswith('callable_utility_cases.rs')]
  self.assertEqual(len(target),3)
  self.assertEqual({i for c in target for i in c['case_ids']},{c['id'] for c in self.manifest['cases']})
 def test_function_ref_is_non_owning_and_copyable(self):
  code=(ROOT/'crates/blended-core/src/function_ref_compat.rs').read_text()
  self.assertIn('*mut ()',code);self.assertIn('impl<\'a,R> Copy for FunctionRef0',code)
  self.assertIn('PhantomData',code)
 def test_session_uid_is_session_counter_not_uuid(self):
  code=(ROOT/'crates/blended-core/src/session_uid_compat.rs').read_text()
  self.assertIn('AtomicU64',code);self.assertIn('is_generated',code)
 def test_iterator_test_uses_original_four_inputs(self):
  self.assertIn('let array=[3,6,1,2]',self.target)
if __name__=='__main__':unittest.main()
