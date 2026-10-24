"""Full-event streaming regressions, not additional upstream cases."""
import copy,gzip,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import fidelity_stream as fs
from assertion_fidelity import compare

def begin(k):return dict(case=k,kind='CASE_BEGIN',passed=True,values=[])
def end(k):return dict(case=k,kind='CASE_END',passed=True,values=[])
def event(k,n):return dict(case=k,kind='EQ',passed=True,values=[f'i:{n}',f'i:{n}'])
class StreamTests(unittest.TestCase):
 def setUp(self):
  self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
  self.root=Path(self.directory.name);self.r=self.root/'reference.jsonl';self.p=self.root/'port.jsonl'
  self.expected=[dict(id='case.long',expected_runtime_assertions=513),dict(id='case.empty',expected_runtime_assertions=0)]
  self.rows=[begin('case.long')]+[event('case.long',i) for i in range(513)]+[end('case.long'),begin('case.empty'),end('case.empty')]
 def write(self,port=None,reference=None):
  for path,rows in [(self.r,self.rows if reference is None else reference),(self.p,self.rows if port is None else port)]:path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
 def result(self):return fs.compare_files(self.r,self.p,self.expected)
 def test_all_chunks_equal_list_comparator(self):
  self.write();a=self.result();b=compare(self.rows,self.rows,self.expected,require_boundaries=True)
  for k in ('case_count','assertions_compared','case_boundaries_verified','assertion_free_cases','floating_differences_within_original_rule','complete_blender_test_port'):self.assertEqual(a[k],b[k])
 def test_case_order_may_differ(self):
  self.write(port=self.rows[-2:]+self.rows[:-2]);self.assertEqual(self.result()['assertions_compared'],513)
 def test_last_event_not_sampled(self):
  rows=copy.deepcopy(self.rows);rows[513]['values']=['i:99','i:99'];self.write(rows)
  with self.assertRaises(ValueError):self.result()
 def test_dropped_event_detected(self):
  rows=copy.deepcopy(self.rows);rows.pop(256);self.write(rows)
  with self.assertRaises(ValueError):self.result()
 def test_extra_event_detected(self):
  rows=copy.deepcopy(self.rows);rows.insert(256,event('case.long',255));self.write(rows)
  with self.assertRaises(ValueError):self.result()
 def test_chunk_boundary_reorder_detected(self):
  rows=copy.deepcopy(self.rows);rows[256],rows[257]=rows[257],rows[256];self.write(rows)
  with self.assertRaises(ValueError):self.result()
 def test_missing_end_detected(self):
  self.write(self.rows[:-1])
  with self.assertRaises(ValueError):self.result()
 def test_failed_end_detected(self):
  rows=copy.deepcopy(self.rows);rows[-1]['passed']=False;self.write(rows)
  with self.assertRaises(ValueError):self.result()
 def test_duplicate_empty_case_detected(self):
  self.write(self.rows+self.rows[-2:])
  with self.assertRaises(ValueError):self.result()
 def test_wrong_identity_detected(self):
  rows=copy.deepcopy(self.rows);rows[400]['case']='unknown';self.write(rows)
  with self.assertRaises(ValueError):self.result()
 def test_no_events_outside_boundaries(self):
  self.write([event('case.long',0)]+self.rows)
  with self.assertRaises(ValueError):self.result()
 def test_floating_difference_ordinal_remains_global_within_case(self):
  r=copy.deepcopy(self.rows);p=copy.deepcopy(self.rows)
  r[300]=dict(case='case.long',kind='NEAR',passed=True,values=['f:3ff0000000000000','f:3ff0000000000000','f:3eb0c6f7a0b5ed8d'])
  p[300]=copy.deepcopy(r[300]);p[300]['values'][1]='f:3ff0000000000001'
  self.write(p,r);self.assertEqual(self.result()['floating_differences_within_original_rule'][0]['ordinal'],299)
 def test_compression_preserves_all_raw_bytes(self):
  self.write();raw=self.r.read_bytes();records=fs.pack(self.root)
  self.assertEqual(len(records),2);self.assertFalse(self.r.exists());self.assertEqual(gzip.decompress((self.root/'reference.jsonl.gz').read_bytes()),raw)
  self.assertTrue(json.loads((self.root/'TRACE-STORAGE.json').read_text())['all_events_preserved'])
 def test_compression_refuses_overwrite(self):
  self.write();(self.root/'port.jsonl.gz').write_bytes(b'old')
  with self.assertRaises(ValueError):fs.pack(self.root)
if __name__=='__main__':unittest.main()
