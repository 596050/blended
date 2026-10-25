"""Reference-domain and absolute-index guards, not extra upstream test cases."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from verify_mask_expression_oracle import ORIGINS,STRIDES,read_mask_observation,PROBE
class MaskOracleDomainTests(unittest.TestCase):
 def test_all_input_indices_fit_pinned_original_static_constructor_domain(self):
  self.assertEqual(ORIGINS,(0,16380,(1<<31)-128));self.assertEqual(STRIDES,(1,17))
  for origin in ORIGINS:
   for stride in STRIDES:self.assertLess(origin+5*stride,1<<31)
 def test_failed_out_of_domain_attempt_is_not_relabelled_as_passing(self):
  evidence=json.loads((ROOT/'evidence/mask-oracle-domain-failure.json').read_text())
  self.assertEqual(evidence['run'],40148762471);self.assertIn('failed',evidence['status'])
  self.assertEqual(evidence['supplemental_offset_that_exceeded_original_domain'],1<<40)
  self.assertFalse(evidence['original_case_bodies_or_expected_values_changed'])
 def test_exact_absolute_values_are_checked(self):
  values=iter([2,0b100001,ORIGINS[-1],ORIGINS[-1]+5*17])
  self.assertEqual(read_mask_observation(lambda:next(values),ORIGINS[-1],17,0b100001),2)
 def test_relative_membership_cannot_hide_wrong_absolute_offset(self):
  values=iter([2,0b100001,0,85])
  with self.assertRaisesRegex(ValueError,'Absolute selected indices'):read_mask_observation(lambda:next(values),ORIGINS[-1],17,0b100001)
 def test_equal_cardinality_cannot_hide_wrong_membership(self):
  values=iter([2,0b11,0,17])
  with self.assertRaisesRegex(ValueError,'truth-table'):read_mask_observation(lambda:next(values),0,17,0b100001)
 def test_diagnostic_tape_contains_both_input_configuration_and_actual_indices(self):
  cpp=(ROOT/'tools/fidelity/mask_expression.hh').read_text()
  self.assertIn('MASKORC2',cpp);self.assertIn('MASKORC2',PROBE)
  self.assertIn('u64(origin);u64(stride);u64(abits);u64(bbits);u64(cbits)',cpp)
  self.assertIn('m.foreach_index',cpp);self.assertIn('for index in mask.iter()',PROBE)
if __name__=='__main__':unittest.main()
