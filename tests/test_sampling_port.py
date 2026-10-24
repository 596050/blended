"""Source translation regressions. Not extra upstream runtime cases."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_sampling_tests import FILES,extract,image_translate,curve_translate,image_header,CURVE_HELPERS
class SamplingPorts(unittest.TestCase):
 def test_all_original_identities_are_retained(self):
  for filename,manifest in [('BLI_math_interp_test.cc','sampling-ports.json'),('BLI_length_parameterize_test.cc','curve-ports.json')]:
   text=(ROOT/'tests/upstream/blender'/filename).read_text();cases=json.loads((ROOT/'compatibility'/manifest).read_text())['cases']
   self.assertEqual([(i,l) for i,_,l in extract(text)],[(c['id'],c['line']) for c in cases])
 def test_complete_original_file_hashes(self):
  for filename,digest in FILES.items():self.assertEqual(hashlib.sha256((ROOT/'tests/upstream/blender'/filename).read_bytes()).hexdigest(),digest)
 def test_each_body_reproduces_without_expected_result_edits(self):
  for filename,module,translate in [('BLI_math_interp_test.cc','sampling_cases',image_translate),('BLI_length_parameterize_test.cc','curve_cases',curve_translate)]:
   target=(ROOT/'crates/blended-core/src'/f'{module}.rs').read_text()
   for identity,body,_ in extract((ROOT/'tests/upstream/blender'/filename).read_text()):self.assertIn(translate(body),target,identity)
 def test_vector_near_expands_to_four_assertions(self):
  target=(ROOT/'crates/blended-core/src/sampling_cases.rs').read_text()
  self.assertIn('for i in 0..4 {near!',target)
  cases=json.loads((ROOT/'compatibility/sampling-ports.json').read_text())['cases']
  self.assertEqual((len(cases),sum(c['expected_runtime_assertions'] for c in cases)),(27,180))
 def test_curve_helper_checks_and_original_sizes(self):
  target=(ROOT/'crates/blended-core/src/curve_cases.rs').read_text()
  self.assertIn(CURVE_HELPERS,target);self.assertEqual(target.count('vec![0_i32;5007]'),2)
  cases=json.loads((ROOT/'compatibility/curve-ports.json').read_text())['cases'];self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),222)
  self.assertEqual(next(c for c in cases if c['id']=='length_parameterize.Float')['expected_runtime_assertions'],39)
 def test_infinity_call_is_not_removed_or_replaced_by_a_value(self):
  target=(ROOT/'crates/blended-core/src/sampling_cases.rs').read_text()
  self.assertIn('interpolate_bilinear_wrap_byte(&image_char, image_width, image_height, (f32::INFINITY) as f32, (-f32::INFINITY) as f32)',target)
 def test_original_image_and_tolerance(self):
  source=(ROOT/'tests/upstream/blender/BLI_math_interp_test.cc').read_text()
  target=(ROOT/'crates/blended-core/src/sampling_cases.rs').read_text()
  self.assertIn(image_header(source),target);self.assertIn('0.00005_f32',target)
 def test_unknown_calls_are_rejected(self):
  with self.assertRaises(ValueError):image_translate('res = interpolate_nearest_border_fl(data);')
 def test_exact_integrated_registry_and_assertion_counts(self):
  from port_workbench import expected_cases
  cases,_=expected_cases();self.assertEqual(len(cases),503);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),1661377)
if __name__=='__main__':unittest.main()
