"""UTF8 source and stress-universe regressions, not additional Blender cases."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_utf8_tests import HASH,extract_cases,definitions,fixture,translate
from port_workbench import expected_cases
from verify_utf8_oracle import corpus,SIZES
from verify_utf8_sensitivity import MUTATIONS
class Utf8PortTests(unittest.TestCase):
 def setUp(self):
  self.original=(ROOT/'tests/upstream/blender/BLI_string_utf8_test.cc').read_bytes();self.text=self.original.decode()
  self.manifest=json.loads((ROOT/'compatibility/utf8-ports.json').read_text());self.target=(ROOT/'crates/blended-core/src/utf8_cases.rs').read_text()
 def test_all_original_identities_and_lines(self):
  self.assertEqual(hashlib.sha256(self.original).hexdigest(),HASH)
  self.assertEqual([(i,l,k) for i,b,l,k in extract_cases(self.text)],[(c['id'],c['line'],c['test_kind']) for c in self.manifest['cases']]);self.assertEqual(len(self.manifest['cases']),39)
 def test_each_original_body_reproduces(self):
  defs=definitions(self.text);rows=fixture(self.text)
  for (identity,body,line,kind),case in zip(extract_cases(self.text),self.manifest['cases']):
   code,count=translate(identity,body,defs,rows);self.assertIn(code,self.target);self.assertEqual(count,case['expected_runtime_assertions']);self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),case['source_body_sha256'])
 def test_original_invalid_fixture_bytes_and_count_preserved(self):
  self.assertEqual(len(fixture(self.text)),78);self.assertEqual(self.manifest['invalid_fixture_count'],78)
  self.assertIn('buff.copy_from_slice(src)',self.target)
 def test_complete_stress_loops_and_counts_not_sampled(self):
  self.assertEqual(self.manifest['stress_buffer_sizes'],list(range(1,13)))
  self.assertEqual(self.manifest['stress_assertions'],1626112)
  self.assertIn('0..=255_i32',self.target);self.assertIn('mul<256',self.target)
  self.assertIn('src.len()+7',self.target);self.assertIn('u32::MAX',self.target)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in self.manifest['cases']),1627163)
 def test_full_registry_remains_bijective(self):
  cases,_=expected_cases();self.assertEqual(len(cases),541);self.assertEqual(len({c['id'] for c in cases}),541);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196218)
 def test_supplemental_corpus_has_every_single_and_two_byte_input(self):
  c=corpus();self.assertEqual(len(c),68273);self.assertEqual(c[0],b'');self.assertEqual(set(c[1:257]),{bytes([b]) for b in range(256)})
  self.assertEqual(len(set(c[257:65793])),65536);self.assertTrue(all(len(v)==2 for v in c[257:65793]));self.assertIn(6,SIZES);self.assertIn(7,SIZES)
 def test_negative_controls_modify_only_implementation(self):
  code=(ROOT/'crates/blended-core/src/utf8_compat.rs').read_text()
  for name,signature,replacement,target,control in MUTATIONS:
   self.assertEqual(code.count(signature),1);self.assertNotEqual(target,control);self.assertIn(target,{c['id'] for c in self.manifest['cases']})
 def test_pinned_width_table_is_not_host_unicode(self):
  table=(ROOT/'crates/blended-core/src/utf8_combining.rs').read_text()
  self.assertIn('1d337ec47f24e04f427937deeedcd773cc3ea474',table)
  self.assertTrue((ROOT/'LICENSES/wcwidth-original-notice.txt').exists())
 def test_unknown_source_case_is_rejected(self):
  with self.assertRaises(ValueError):translate('unknown.case','',{},[])
if __name__=='__main__':unittest.main()
