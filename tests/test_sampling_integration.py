"""The registered production cases must agree with their independently locked inputs."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_workbench import expected_cases
from assertion_fidelity import contracts
class SamplingIntegrationTests(unittest.TestCase):
 def test_case_groups_are_unique_and_complete(self):
  cases,_=expected_cases();self.assertEqual(len(cases),338)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),16804)
  self.assertEqual(len([c for c in cases if c['group']=='sampling']),27)
  self.assertEqual(len([c for c in cases if c['group']=='curves']),9)
 def test_reviewed_unsigned_cast_target_hash(self):
  actual=hashlib.sha256((ROOT/'crates/blended-core/src/sampling_cases.rs').read_bytes()).hexdigest()
  self.assertEqual(actual,'f8f7332a4310354a5c8ae5b66b87b1a885bf7794f87080aac0d7383bd37722c5')
  self.assertEqual(len(contracts(ROOT)['contracts']),25)
if __name__=='__main__':unittest.main()
