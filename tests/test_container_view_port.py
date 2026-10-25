"""Source and supplementary-observer regressions, not extra Blender cases."""
from pathlib import Path
import copy,hashlib,json,shutil,struct,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_container_view_tests import FILES,BODIES,HEAD,COUNTS,extract
from port_workbench import expected_cases
from contract_registry import EXTENSIONS,load_contracts
from verify_container_view_oracle import expected_words,check
from verify_container_view_sensitivity import MUTATIONS

class ContainerViewPorts(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads((ROOT/'compatibility/container-view-ports.json').read_text())
  self.target=(ROOT/'crates/blended-core/src/container_view_cases.rs').read_text()
 def test_all_original_files_identities_and_body_hashes(self):
  original=[]
  for name,digest in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
   original.extend(extract(raw.decode()))
  self.assertEqual(len(original),13)
  self.assertEqual([(i,l,k) for i,b,l,k in original],[(c['id'],c['line'],c['kind']) for c in self.manifest['cases']])
  for (_,body,_,_),c in zip(original,self.manifest['cases']):self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),c['source_body_sha256'])
 def test_reviewed_bodies_and_original_counts_are_preserved(self):
  self.assertTrue(self.target.startswith(HEAD));self.assertEqual(sum(COUNTS),52)
  for c in self.manifest['cases']:
   self.assertIn(BODIES[c['id'].split('.')[1]],self.target)
   self.assertEqual(c['expected_runtime_assertions'],COUNTS[c['index']])
 def test_fixture_setup_is_once_per_suite_not_an_assertion(self):
  self.assertIn('static SETUP:std::sync::Once',HEAD)
  self.assertEqual(self.target.count('generic_span_suite_setup();'),4)
  self.assertEqual(sum(c['kind']=='TEST_F' for c in self.manifest['cases']),4)
 def test_exact_runtime_universe(self):
  cases,_=expected_cases();self.assertEqual(len(cases),624)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196774)
  self.assertEqual([c['id'] for c in cases if c['group']=='container_views'],[c['id'] for c in self.manifest['cases']])
 def test_pointer_identity_and_live_cells_are_not_value_snapshots(self):
  self.assertIn('core::ptr::eq',HEAD)
  body=BODIES['BufferAndSizeConstructor'];self.assertEqual(body.count('peq!('),4)
  self.assertIn('OwnedKey::new(4)',BODIES['UniquePtr'])
  self.assertIn('values[2].get()',BODIES['MutableBufferAndSizeConstructor'])
  self.assertIn('span.pointer_at(2).cast::<i32>().write(10)',BODIES['MutableBufferAndSizeConstructor'])
 def test_all_negative_controls_have_unique_implementation_targets(self):
  code=(ROOT/'crates/blended-core/src/container_views.rs').read_text();ids={c['id'] for c in self.manifest['cases']}
  self.assertEqual(len(MUTATIONS),4)
  for name,old,new,target,control in MUTATIONS:
   self.assertEqual(code.count(old),1);self.assertNotEqual(old,new);self.assertIn(target,ids);self.assertIn(control,ids);self.assertNotEqual(target,control)
 def test_original_header_observer_is_actually_included(self):
  header=(ROOT/'tools/fidelity/generic_span.hh').read_text();self.assertIn('#include "container_view_oracle.hh"',header)
  code=(ROOT/'tools/fidelity/container_view_oracle.hh').read_text()
  self.assertIn('OnTestProgramEnd',code);self.assertIn('tests.failed_test_count()',code)
  self.assertIn('name!="reference.jsonl"',code)
 def test_independent_model_and_binary_comparison_cover_the_last_word(self):
  words=expected_words();self.assertEqual(words[:3],[0x43564f31,16,64]);self.assertEqual(words[-11:],[2,4,1,4,1,6,7,3,2,3,4])
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'observations.bin';data=b''.join(struct.pack('<I',v) for v in words);path.write_bytes(data)
   self.assertEqual(check(path),len(words))
   path.write_bytes(data[:-4]+struct.pack('<I',0))
   with self.assertRaises(ValueError):check(path)
   path.write_bytes(data[:-1])
   with self.assertRaises(ValueError):check(path)
 def test_membership_and_order_corruption_is_not_hidden_by_same_count(self):
  words=expected_words();words[10],words[11]=words[11],words[10]
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'wrong.bin';path.write_bytes(b''.join(struct.pack('<I',v) for v in words))
   with self.assertRaises(ValueError):check(path)

class RequiredContainerContracts(unittest.TestCase):
 def root(self):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);p=Path(d.name)
  for name in ('compatibility/assertion-contracts.lock.json',*EXTENSIONS):
   target=p/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
  return p
 def test_missing_shard_cannot_reduce_coverage(self):
  root=self.root();(root/'compatibility/container-view-assertion-contract.lock.json').unlink()
  with self.assertRaises(FileNotFoundError):load_contracts(root)
 def test_stale_reference_cannot_be_approved(self):
  root=self.root();p=root/'compatibility/container-view-assertion-contract.lock.json';data=json.loads(p.read_text());data['reference_commit']='0'*40;p.write_text(json.dumps(data))
  with self.assertRaises(ValueError):load_contracts(root)
 def test_duplicate_mapping_is_rejected(self):
  root=self.root();p=root/'compatibility/container-view-assertion-contract.lock.json';data=json.loads(p.read_text());data['contracts'].append(copy.deepcopy(data['contracts'][0]));p.write_text(json.dumps(data))
  with self.assertRaises(ValueError):load_contracts(root)
if __name__=='__main__':unittest.main()
