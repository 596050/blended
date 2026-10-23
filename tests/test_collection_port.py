"""Collection translation/accounting safeguards; these are not upstream feature tests."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_collection_tests import FILES,extract,translate
from assertion_fidelity import compare,contracts
from port_workbench import expected_cases
from inventory import scan_cpp
class CollectionPortTests(unittest.TestCase):
 def test_every_case_and_assertion_accounted(self):
  m=json.loads((ROOT/'compatibility/collection-ports.json').read_text());self.assertEqual(len(m['cases']),32)
  self.assertEqual(sum(c['assertion_count'] for c in m['cases']),170)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in m['cases']),521)
  ids=[]
  for name,sha in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
   ids.extend(i for i,b,l in extract(raw.decode()))
  self.assertEqual(ids,[c['id'] for c in m['cases']])
 def test_reviewed_hashes_match(self):self.assertEqual(len(contracts(ROOT)['contracts']),25)
 def test_full_runtime_registry(self):
  c,_=expected_cases();self.assertEqual(len(c),338);self.assertEqual(sum(x['expected_runtime_assertions'] for x in c),16804)
 def test_shared_reference_not_boolean_snapshot(self):
  s=(ROOT/'crates/blended-core/src/collection_cases.rs').read_text();self.assertIn('let read_ref = mutable_ref.as_read();',s);self.assertIn('yes!(r, read_ref.test());',s)
 def test_move_keeps_observable_source_empty(self):
  s=(ROOT/'crates/blended-core/src/collection_cases.rs').read_text();self.assertEqual(s.count('core::mem::take(&mut vec)'),2)
 def test_original_iteration_sizes_not_shrunk(self):
  s=(ROOT/'crates/blended-core/src/collection_cases.rs').read_text();self.assertIn('0_i64..1000',s);self.assertIn('with_fill(123, true)',s)
 def test_wrong_word_offset_is_rejected(self):
  r=[{'case':'x','kind':'EQ','passed':True,'values':['p64:1','p64:1']}];p=copy.deepcopy(r);p[0]['values']=['p64:2','p64:2']
  with self.assertRaises(ValueError):compare(r,p,[{'id':'x','expected_runtime_assertions':1}])
 def test_compile_time_case_is_not_runtime_case(self):
  m=json.loads((ROOT/'compatibility/compile-time-ports.json').read_text());self.assertEqual(m['cases'][0]['id'],'static_assert@219');self.assertNotIn('static_assert@219',[c['id'] for c in expected_cases()[0]])
class CppNumericInventoryTests(unittest.TestCase):
 def test_binary_separator_does_not_hide_next_case(self):
  text="TEST(bits, First) {auto x=0b0000'0001;}\nTEST(bits, Second) {auto y=0b0010'0000;}"
  self.assertEqual([c['identity'] for c in scan_cpp(text,'bits.cc')],['bits.First','bits.Second'])
 def test_hexadecimal_decimal_and_suffixes_preserve_lines(self):
  text="auto a=0xFA'CEULL;\nauto b=1'000'000;\nTEST(Foo, Next) {}\nchar c='x';"
  found=scan_cpp(text,'bits.cc');self.assertEqual([(c['identity'],c['line']) for c in found],[('Foo.Next',3)])
 def test_strings_comments_and_raw_strings_still_masked(self):
  text='// 0b00\'01 TEST(fake,One)\nconst char *s="123\'456 TEST(fake,Two)";\nconst char *r=R"tag(0xA\'BC TEST(fake,Three))tag";\nTEST(real,Case){}'
  self.assertEqual([c['identity'] for c in scan_cpp(text,'bits.cc')],['real.Case'])
 def test_character_literals_still_masked(self):
  text="char a='1'; char b='\\\''; char c='A'; TEST(real,Case){}"
  self.assertEqual([c['identity'] for c in scan_cpp(text,'bits.cc')],['real.Case'])
 def test_every_bit_ref_declaration_is_retained(self):
  source=ROOT/'tests/upstream/blender/BLI_bit_ref_test.cc'
  found=scan_cpp(source.read_text(),'source/blender/blenlib/tests/BLI_bit_ref_test.cc')
  self.assertEqual(len(found),10)
  self.assertIn(('bit_ref.MaskSingleBit',40),[(c['identity'],c['line']) for c in found])
 def test_all_frozen_runtime_and_static_mappings_are_discovered(self):
  for name in ['additional-ports.json','structure-ports.json','collection-ports.json','compile-time-ports.json']:
   manifest=json.loads((ROOT/'compatibility'/name).read_text())
   for case in manifest['cases']:
    text=(ROOT/'tests/upstream/blender'/Path(case['path']).name).read_text()
    found={(c['identity'],c['line']) for c in scan_cpp(text,case['path'])}
    self.assertIn((case['id'],case['line']),found)
if __name__=='__main__':unittest.main()
