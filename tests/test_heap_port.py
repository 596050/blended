"""Source translation and audit regressions, not additional Blender runtime cases."""
from pathlib import Path
import copy,hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_heap_tests import FILES,extract,translate,original_helper
from port_workbench import expected_cases
from assertion_fidelity import compare
class HeapPorts(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads((ROOT/'compatibility/heap-ports.json').read_text())
  self.target=(ROOT/'crates/blended-core/src/heap_cases.rs').read_text()
 def test_all_original_files_and_case_identities(self):
  actual=[]
  for name,digest in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
   actual.extend((i,l) for i,_,l in extract(raw.decode()))
  self.assertEqual(actual,[(c['id'],c['line']) for c in self.manifest['cases']]);self.assertEqual(len(actual),29)
 def test_each_test_body_reproduces(self):
  for name in FILES:
   for identity,body,_ in extract((ROOT/'tests/upstream/blender'/name).read_text()):
    self.assertIn(translate(body,queue='priority_queue' in name),self.target,identity)
 def test_original_helper_bodies_reproduce(self):
  for h in self.manifest['helpers']:
   text=(ROOT/'tests/upstream/blender'/Path(h['path']).name).read_text();body,line=original_helper(text,h['name'])
   self.assertEqual(line,h['line']);self.assertIn(translate(body),self.target)
 def test_all_assertion_sites_and_execution_counts(self):
  original=sum(len(re.findall(r'\bEXPECT_\w+\(', (ROOT/'tests/upstream/blender'/n).read_text())) for n in FILES)
  self.assertEqual(original,66)
  self.assertEqual(len(re.findall(r'\b(?:eq|le|yes|no)!\(',self.target)),66)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in self.manifest['cases']),16300)
 def test_independent_registered_universe(self):
  cases,_=expected_cases();self.assertEqual(len(cases),596);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196692)
  self.assertEqual([c['id'] for c in cases if c['group']=='heaps'],[c['id'] for c in self.manifest['cases']])
 def test_actual_pointer_payload_and_live_priority_storage(self):
  self.assertEqual(self.target.count('b"test\\0".as_ptr()'),2)
  self.assertIn('Vec<Cell<i32>>',self.target);self.assertIn('values[(2) as usize].set(0);',self.target)
  self.assertIn('heap.pop_min()',self.target)
 def test_original_large_iteration_and_seed_inputs(self):
  self.assertIn('const SIZE:i32=1024;',self.target)
  for amount,seed in ((1,1234),(2,1234),(100,4321),(1024,9876),(2048,5321)):
   self.assertIn(f'random_heap_reinsert_helper(&mut report, {amount}, {seed})',self.target)
  self.assertEqual(self.target.count('let mut amount:i32=1000;'),2)
  self.assertEqual(self.target.count('BlenderRng::new(0)'),2)
 def test_unknown_upstream_call_is_rejected(self):
  with self.assertRaises(ValueError):translate('BLI_heap_future_operation(heap);')
 def test_less_equal_operand_order_is_not_symmetric(self):
  expected=[{'id':'queue.order','expected_runtime_assertions':1}]
  trace=[{'case':'queue.order','kind':'LE','passed':True,'values':['i:2','i:5']}]
  self.assertEqual(compare(trace,copy.deepcopy(trace),expected)['assertions_compared'],1)
  changed=copy.deepcopy(trace);changed[0]['values'].reverse()
  with self.assertRaises(ValueError):compare(trace,changed,expected)
 def test_wrong_comparison_kind_is_rejected(self):
  expected=[{'id':'queue.order','expected_runtime_assertions':1}]
  trace=[{'case':'queue.order','kind':'LE','passed':True,'values':['i:2','i:5']}]
  changed=copy.deepcopy(trace);changed[0]['kind']='EQ'
  with self.assertRaises(ValueError):compare(trace,changed,expected)
if __name__=='__main__':unittest.main()
