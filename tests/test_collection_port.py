"""Collection translation/accounting safeguards; these are not upstream feature tests."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_collection_tests import FILES,extract,translate
from assertion_fidelity import compare,contracts
from port_workbench import expected_cases
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
 def test_reviewed_hashes_match(self):self.assertEqual(len(contracts(ROOT)['contracts']),14)
 def test_full_runtime_registry(self):
  c,_=expected_cases();self.assertEqual(len(c),131);self.assertEqual(sum(x['expected_runtime_assertions'] for x in c),1049)
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
if __name__=='__main__':unittest.main()
