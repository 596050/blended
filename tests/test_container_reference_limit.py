"""A broken declared upstream API must not become a silent parity claim."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from verify_container_view_oracle import LIMIT,RUST,expected_words
class OriginalApiLimit(unittest.TestCase):
 def test_failed_reference_instantiation_is_preserved(self):
  evidence=json.loads((ROOT/'evidence/container-oracle-reference-limit.json').read_text())
  self.assertEqual(evidence['failed_run'],40207913645)
  self.assertFalse(evidence['original_reference_tests_executed_in_failed_job'])
  self.assertTrue(evidence['publication_blocked']);self.assertFalse(evidence['original_test_bodies_or_expectations_changed'])
  self.assertIn("no member named 'clear_and_shrink'",evidence['diagnostic'])
 def test_same_supported_clear_operation_on_both_targets(self):
  cpp=(ROOT/'tools/fidelity/container_view_oracle.hh').read_text()
  self.assertIn('if(step==31||step==63)map.clear()',cpp)
  self.assertIn('if step==31||step==63{map.clear();}',RUST)
  self.assertNotIn('map.clear_and_shrink()',cpp);self.assertNotIn('map.clear_and_shrink()',RUST)
  self.assertFalse(LIMIT['equivalence_certified']);self.assertEqual(len(expected_words()),107101)
if __name__=='__main__':unittest.main()
