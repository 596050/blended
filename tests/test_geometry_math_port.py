"""Translation completeness and assertion semantics, not extra Blender features."""
import hashlib,json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_geometry_math_tests import FILES,extract,translate
from port_workbench import expected_cases
from assertion_fidelity import contracts,compare
class GeometryMathPortTests(unittest.TestCase):
 def test_complete_original_files_and_identities(self):
  manifest=json.loads((ROOT/'compatibility/geometry-math-ports.json').read_text());original=[]
  for name,digest in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
   original.extend((identity,'source/blender/blenlib/tests/'+name,line) for identity,body,line in extract(raw.decode()))
  self.assertEqual(original,[(c['id'],c['path'],c['line']) for c in manifest['cases']]);self.assertEqual(len(original),30)
 def test_every_original_body_reproduces(self):
  target=(ROOT/'crates/blended-core/src/geometry_math_cases.rs').read_text()
  for name in FILES:
   for identity,body,line in extract((ROOT/'tests/upstream/blender'/name).read_text()):self.assertIn(translate(body,identity),target)
 def test_assertion_sites_and_loop_execution(self):
  cases=json.loads((ROOT/'compatibility/geometry-math-ports.json').read_text())['cases']
  self.assertEqual(sum(c['assertion_count'] for c in cases),140)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),154)
  lookup={c['id']:c for c in cases}
  self.assertEqual(lookup['math_geom_hh.AxisDominantToM3']['expected_runtime_assertions'],9)
  self.assertEqual(lookup['math_geom_hh.InterpWeightsPoly']['expected_runtime_assertions'],8)
 def test_fatal_assertion_not_converted_to_nonfatal(self):
  target=(ROOT/'crates/blended-core/src/geometry_math_cases.rs').read_text()
  self.assertIn('fatal_yes!(report, hit.is_some())',target)
  self.assertIn('if !p{return $r;}',target)
  self.assertIn('GTEST_ASSERT_TRUE(::blended_fidelity::fatal_true', (ROOT/'tools/fidelity/trace.hh').read_text())
 def test_original_local_result_does_not_shadow_harness(self):
  target=(ROOT/'crates/blended-core/src/geometry_math_cases.rs').read_text()
  self.assertIn('let mut r = ',target)
  self.assertIn('let mut report=Report::default();',target)
  self.assertNotIn('let mut r=Report::default();',target)
 def test_all_current_cases_are_reviewed(self):
  cases,_=expected_cases();self.assertEqual(len(cases),512)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),1661546)
  self.assertEqual(len(contracts(ROOT)['contracts']),38)
 def test_empty_geometric_test_cannot_replace_original(self):
  for c in json.loads((ROOT/'compatibility/geometry-math-ports.json').read_text())['cases']:
   self.assertGreater(c['assertion_count'],0);self.assertFalse(c.get('assertion_free_smoke',False))
if __name__=='__main__':unittest.main()
