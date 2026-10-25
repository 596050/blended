"""Fixture/source/recorder regressions; not additional upstream runtime ports."""
from pathlib import Path
import collections,copy,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_string_ops_tests import FILES,c_bytes,lit,extract_cases,main_case,search_case,utils_case
from port_workbench import expected_cases
from assertion_fidelity import compare
from verify_string_ops_sensitivity import MUTATIONS,mutate
from verify_string_ops_oracle import corpus,LIMITS
class StringOperationsPort(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads((ROOT/'compatibility/string-ops-ports.json').read_text());self.target=(ROOT/'crates/blended-core/src/string_ops_cases.rs').read_text()
 def test_every_original_TEST_and_TEST_F_identity(self):
  ids=[]
  for name,sha in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
   ids.extend((i,l,k) for i,_,l,k in extract_cases(raw.decode()))
  self.assertEqual(ids,[(c['id'],c['line'],c['kind']) for c in self.manifest['cases']]);self.assertEqual(len(ids),48)
  self.assertEqual(sum(k=='TEST_F' for _,_,k in ids),19)
 def test_each_body_reproduces_and_has_source_provenance(self):
  by_id={c['id']:c for c in self.manifest['cases']}
  for name in FILES:
   translator=search_case if name=='BLI_string_search_test.cc' else utils_case if name=='BLI_string_utils_test.cc' else main_case
   for identity,body,_,_ in extract_cases((ROOT/'tests/upstream/blender'/name).read_text()):
    code,n=translator(identity,body);self.assertIn(code,self.target);self.assertEqual(n,by_id[identity]['expected_runtime_assertions']);self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),by_id[identity]['body_sha256'])
 def test_runtime_registry_bijection(self):
  cases,_=expected_cases();self.assertEqual(len(cases),609);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196744)
  self.assertEqual([c['id'] for c in cases if c['group']=='string_ops'],[c['id'] for c in self.manifest['cases']])
 def test_counts_include_conditional_vector_helper_and_original_loops(self):
  by_id={c['id']:c for c in self.manifest['cases']};self.assertEqual(sum(c['expected_runtime_assertions'] for c in by_id.values()),846)
  self.assertEqual(by_id['string.StrJoin_Truncate']['expected_runtime_assertions'],166)
  self.assertEqual(by_id['StringEscape.Control']['expected_runtime_assertions'],55)
  self.assertIn('if actual.len()==expected.len(){for i in 0..actual.len()',self.target)
  self.assertIn('(1..=len+1).rev()',self.target)
 def test_C_literals_preserve_bytes_not_double_UTF8_encoding(self):
  self.assertEqual(c_bytes(r'"\xe2\x96\xb8"'),bytes.fromhex('e296b8'))
  self.assertEqual(c_bytes('"☯"'),bytes.fromhex('e298af'))
  self.assertEqual(c_bytes(r'"\303\261"'),bytes.fromhex('c3b1'))
  self.assertEqual(c_bytes(r'"a\0b"'),b'a\0b')
  self.assertEqual(c_bytes('"hello" UI_MENU_ARROW_SEP "world"'),b'hello'+bytes.fromhex('e296b8')+b'world')
  self.assertEqual(lit(r'"\a\b\f\n\r\t\v"'),r'b"\x07\x08\x0c\x0a\x0d\x09\x0b"')
 def test_unknown_literal_or_out_of_byte_escape_is_rejected(self):
  for text in ['L"wide"',r'"\u1234"',r'"\x123"',r'"\x"','SOME_MACRO']:
   with self.assertRaises(ValueError):c_bytes(text)
 def test_pointer_alias_mismatch_is_not_value_or_null_equality(self):
  expected=[{'id':'p.address','expected_runtime_assertions':1}]
  source=[{'case':'p.address','kind':'EQ','passed':True,'values':['palias:a','palias:a']}]
  self.assertEqual(compare(source,copy.deepcopy(source),expected)['assertions_compared'],1)
  for replacement in ['palias:b','palias:null','s:61']:
   altered=copy.deepcopy(source);altered[0]['values'][1]=replacement
   with self.assertRaises(ValueError):compare(source,altered,expected)
 def test_strict_less_order_cannot_reverse_operands_or_change_kind(self):
  expected=[{'id':'s.order','expected_runtime_assertions':1}];source=[{'case':'s.order','kind':'LT','passed':True,'values':['i:-32','i:0']}]
  self.assertEqual(compare(source,copy.deepcopy(source),expected)['assertions_compared'],1)
  for k,v in [('kind','LE'),('values',['i:0','i:-32'])]:
   changed=copy.deepcopy(source);changed[0][k]=v
   with self.assertRaises(ValueError):compare(source,changed,expected)
 def test_each_negative_probe_has_one_unique_implementation_target(self):
  for _,filename,kind,old,new,_,_ in MUTATIONS:
   before=(ROOT/'crates/blended-core/src'/filename).read_text();self.assertNotEqual(mutate(before,kind,old,new),before)
 def test_supplemental_corpus_is_explicit_unique_and_covers_zero_length_search(self):
  text,words=corpus();self.assertEqual(len(words),56);self.assertEqual(len(set(words)),56);self.assertEqual(len(text.splitlines()),56)
  self.assertIn(b'',words);self.assertIn(b'01',words);self.assertIn(b'001',words);self.assertIn(0,LIMITS);self.assertIn(32,LIMITS)
if __name__=='__main__':unittest.main()
