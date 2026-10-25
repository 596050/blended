"""Source fidelity for integrated numeric/vector/colour families, not feature counts."""
import copy,hashlib,json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_numeric_type_tests import FILES,extract,vectors,colors,comments
from assertion_fidelity import contracts
from port_workbench import expected_cases
from inventory import scan_cpp
class NumericTypesTests(unittest.TestCase):
 def test_source_universe_is_exact(self):
  manifest=json.loads((ROOT/'compatibility/numeric-type-ports.json').read_text());expected=[];counts={}
  for name,sha in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
   cases=list(extract(raw.decode()));counts[name]=len(cases);expected.extend((i,line) for i,body,line in cases)
  self.assertEqual(counts,{'BLI_math_vector_types_test.cc':29,'BLI_color_test.cc':11})
  self.assertEqual(expected,[(c['id'],c['line']) for c in manifest['cases']])
 def test_original_test_bodies_reproduce(self):
  target=(ROOT/'crates/blended-core/src/numeric_type_cases.rs').read_text()
  for name in FILES:
   for identity,body,line in extract((ROOT/'tests/upstream/blender'/name).read_text()):
    translated=vectors(body) if 'vector_types' in name else colors(body)
    self.assertIn(translated,target)
    self.assertEqual(len(re.findall(r'\bEXPECT_(?:EQ|FLOAT_EQ|NEAR|TRUE|FALSE)\s*\(',comments(body))),len(re.findall(r'\b(?:eq|numeq|feq|near|yes|no)!',translated)))
 def test_unique_case_registry(self):
  cases,_=expected_cases();self.assertEqual(len(cases),609);self.assertEqual(len({c['id'] for c in cases}),609)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196744)
  self.assertEqual(sum(c['group']=='strings' for c in cases),53)
 def test_vector_static_layout_assertions_are_not_hidden(self):
  src=ROOT/'tests/upstream/blender/BLI_math_vector_types_test.cc'
  static=[c for c in scan_cpp(src.read_text(),src.name) if c['kind']=='static_assert']
  self.assertEqual(len(static),9)
  cases,_=expected_cases();self.assertEqual(sum(c['id'].startswith('math_vec_types.') for c in cases),29)
 def test_swizzles_remain_operations(self):
  text=(ROOT/'crates/blended-core/src/numeric_type_cases.rs').read_text()
  self.assertIn('.set_swizzle(',text);self.assertIn('.swizzle([',text);self.assertIn('v::construct::<u32,2>',text)
 def test_reviewed_targets(self):
  self.assertEqual(len(contracts(ROOT)['contracts']),43)
if __name__=='__main__':unittest.main()
