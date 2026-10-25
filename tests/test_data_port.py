"""Source/provenance and audit regressions, not additional Blender runtime cases."""
import collections,copy,hashlib,json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_data_tests import FILES,ARRAY,translate_csv,translate_hash,translate_disjoint
from port_string_ref_tests import extract,code_mask
from port_workbench import expected_cases
from assertion_fidelity import compare
from verify_data_sensitivity import MUTATIONS,mutate
from verify_hash_streaming import corpus
class DataPorts(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads((ROOT/'compatibility/data-ports.json').read_text());self.target=(ROOT/'crates/blended-core/src/data_cases.rs').read_text()
 def test_all_original_file_hashes_and_runtime_identities(self):
  ids=[]
  for name,sha in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
   ids.extend((identity,line) for identity,_,line in extract(raw.decode()))
  self.assertEqual(ids,[(c['id'],c['line']) for c in self.manifest['cases']]);self.assertEqual(len(ids),49)
 def test_every_case_body_retains_original_provenance(self):
  by_id={c['id']:c for c in self.manifest['cases']}
  for name in FILES:
   for identity,body,_ in extract((ROOT/'tests/upstream/blender'/name).read_text()):
    self.assertEqual(by_id[identity]['body_sha256'],hashlib.sha256(body.encode()).hexdigest())
    if identity.startswith('array_utils.'):translation=ARRAY[identity.split('.')[1]][0]
    else:translation=(translate_csv if identity.startswith('csv_parse.') else translate_hash if identity.startswith('hash_mm2a.') else translate_disjoint)(body)
    self.assertIn(translation,self.target,identity)
 def test_expanded_helper_counts_are_not_case_counts(self):
  totals=collections.Counter();counts=collections.Counter()
  for case in self.manifest['cases']:
   family=case['id'].split('.')[0];counts[family]+=1;totals[family]+=case['expected_runtime_assertions']
  self.assertEqual(dict(counts),{'array_utils':35,'csv_parse':10,'hash_mm2a':3,'disjoint_set':1})
  self.assertEqual(dict(totals),{'array_utils':133,'csv_parse':114,'hash_mm2a':5,'disjoint_set':12})
 def test_registered_runtime_and_source_contracts_are_bijective(self):
  cases,_=expected_cases();self.assertEqual(len(cases),624);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196774)
  self.assertEqual([c['id'] for c in cases if c['group']=='data'],[c['id'] for c in self.manifest['cases']])
 def test_large_original_input_and_mask_are_not_subsampled(self):
  self.assertIn('vec![0_i32;100000]',self.target);self.assertEqual(self.target.count('vec![0_i32;100000]'),2)
  self.assertIn('(x*7919)%20011',self.target);self.assertIn('((x*7919)%1009)*1000003',self.target);self.assertIn('i%3!=0',self.target)
  self.assertIn('array_utils__GroupIdsToIndicesLarge,20',self.target)
 def test_original_helpers_and_nonfatal_array_expansion_remain(self):
  self.assertIn('for i in 0..$n{eq!($r,expected[i],actual[i]);}',self.target)
  self.assertIn('a::deduplicate_ordered(data,new_len)',self.target)
  self.assertIn('BTreeMap::new()',self.target);self.assertIn('expected_ids.insert(ids[i],index)',self.target)
  self.assertIn('a::VirtualInts::from_fn(10,|x|',self.target)
 def test_unknown_csv_syntax_is_rejected(self):
  with self.assertRaises(ValueError):translate_csv('EXPECT_NEW_RULE(a,b);')
 def test_string_content_assertion_cannot_be_replaced_with_pointer_equality(self):
  case=[{'id':'s.content','expected_runtime_assertions':1}]
  ref=[{'case':'s.content','kind':'STREQ','passed':True,'values':['s:303132','s:303132']}]
  self.assertEqual(compare(ref,copy.deepcopy(ref),case)['assertions_compared'],1)
  altered=copy.deepcopy(ref);altered[0]['kind']='EQ'
  with self.assertRaises(ValueError):compare(ref,altered,case)
 def test_string_content_mutation_is_rejected(self):
  case=[{'id':'s.content','expected_runtime_assertions':1}]
  ref=[{'case':'s.content','kind':'STREQ','passed':True,'values':['s:303132','s:303132']}]
  altered=copy.deepcopy(ref);altered[0]['values'][1]='s:303133'
  with self.assertRaises(ValueError):compare(ref,altered,case)
 def test_each_negative_probe_changes_only_a_unique_implementation_target(self):
  for _,name,kind,old,new,_,_ in MUTATIONS:
   source=(ROOT/'crates/blended-core/src'/name).read_text();changed=mutate(source,kind,old,new)
   self.assertNotEqual(source,changed)
  with self.assertRaises(ValueError):mutate('no such target','replace','missing','replacement')
 def test_hash_corpus_preserves_every_two_part_boundary(self):
  text,records=corpus();self.assertEqual(len(records),10592);self.assertEqual(len(text.splitlines()),len(records))
  grouped=collections.defaultdict(set)
  for record in records:
   n=len(bytes.fromhex(record['bytes_hex']));self.assertEqual(sum(record['chunks']),n)
   grouped[(record['seed'],n)].add(tuple(record['chunks']))
  self.assertEqual(len(grouped),4*65)
  for (_,n),plans in grouped.items():
   self.assertTrue({(i,n-i) for i in range(n+1)}<=plans)
if __name__=='__main__':unittest.main()
