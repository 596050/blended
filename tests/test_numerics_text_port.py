"""Source-translation integrity checks; these are not additional Blender feature cases."""
import copy,hashlib,json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_numerics_text_tests import FILES,extract,vectors,strings,colors,comments
from assertion_fidelity import compare,contracts
from port_workbench import expected_cases
from inventory import scan_cpp
class NumericTextPortTests(unittest.TestCase):
 def test_all_original_runtime_cases_are_present(self):
  manifest=json.loads((ROOT/'compatibility/numerics-text-ports.json').read_text());expected=[]
  counts={}
  for name,sha in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
   found=list(extract(raw.decode()));counts[name]=len(found)
   expected.extend((i,l) for i,b,l in found)
  self.assertEqual(counts,{'BLI_math_vector_types_test.cc':29,'BLI_string_ref_test.cc':53,'BLI_color_test.cc':11})
  self.assertEqual(expected,[(c['id'],c['line']) for c in manifest['cases']])
  self.assertEqual(sum(c['assertion_count'] for c in manifest['cases']),450)
  self.assertFalse(manifest['complete_blender_test_port'])
 def test_all_sources_reproduce_exact_runtime_assertions(self):
  combined=(ROOT/'crates/blended-core/src/numerics_text_cases.rs').read_text()
  for name in FILES:
   for identity,body,line in extract((ROOT/'tests/upstream/blender'/name).read_text()):
    translated=vectors(body) if 'vector_types' in name else colors(body) if name=='BLI_color_test.cc' else strings(body,identity)
    self.assertIn(translated,combined)
    self.assertEqual(len(re.findall(r'\bEXPECT_(?:EQ|FLOAT_EQ|NEAR|TRUE|FALSE)\s*\(',comments(body))),len(re.findall(r'\b(?:eq|numeq|feq|near|yes|no)!',translated)))
 def test_reviewed_target_hashes_and_full_case_registry(self):
  self.assertEqual(len(contracts(ROOT)['contracts']),17)
  cases,_=expected_cases();self.assertEqual(len(cases),224)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),1499)
 def test_named_std_string_preserves_length_and_borrow(self):
  code=(ROOT/'crates/blended-core/src/numerics_text_cases.rs').read_text()
  self.assertIn('s::StringRef::with_length(str.as_bytes(),str.len())',code)
  self.assertIn('eq!(r, value.data(), str.as_ptr())',code)
 def test_utf8_and_bytes_are_not_interchanged(self):
  code=(ROOT/'crates/blended-core/src/numerics_text_cases.rs').read_text()
  self.assertIn('copy_utf8_truncated(&mut dst)',code);self.assertIn('copy_bytes_truncated(&mut dst)',code)
  self.assertIn('dst.fill(0xFF)',code);self.assertIn('"²²"',code);self.assertIn('"ž"',code)
 def test_four_original_constexpr_checks_are_retained(self):
  code=(ROOT/'crates/blended-core/src/numerics_text_cases.rs').read_text()
  self.assertEqual(code.count("const _:()=assert!(SREF.byte(2)==b'r');"),2)
  self.assertEqual(code.count('const _:()=assert!(SREF.size()==5);'),2)
  self.assertEqual(code.count("let compiles:[i32;SREF.find_first_of(b'o') as usize]=[1];"),2)
 def test_vector_static_assertions_not_counted_as_runtime_ports(self):
  source=ROOT/'tests/upstream/blender/BLI_math_vector_types_test.cc'
  found=[c for c in scan_cpp(source.read_text(),source.name) if c['kind']=='static_assert']
  self.assertEqual(len(found),9)
  self.assertEqual(len([c for c in expected_cases()[0] if c['id'].startswith('math_vec_types.')]),29)
 def test_changed_text_byte_rejected_by_fidelity_comparator(self):
  r=[{'case':'x','kind':'EQ','passed':True,'values':['s:74657374','s:74657374']}]
  p=copy.deepcopy(r);p[0]['values']=['s:74657375','s:74657375']
  with self.assertRaises(ValueError):compare(r,p,[{'id':'x','expected_runtime_assertions':1}])
 def test_changed_pointer_alias_rejected_by_fidelity_comparator(self):
  r=[{'case':'x','kind':'EQ','passed':True,'values':['p8:0','p8:0']}]
  p=copy.deepcopy(r);p[0]['values'][0]='p8:1'
  with self.assertRaises(ValueError):compare(r,p,[{'id':'x','expected_runtime_assertions':1}])
 def test_swizzle_alias_writeback_is_not_removed(self):
  code=(ROOT/'crates/blended-core/src/numerics_text_cases.rs').read_text()
  self.assertIn('.set_swizzle(',code)
  self.assertIn('.swizzle([',code)
  self.assertIn('v::construct::<u32,2>',code)
if __name__=='__main__':unittest.main()
