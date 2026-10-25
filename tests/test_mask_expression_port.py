"""Source, value-encoding and audit checks, not additional Blender runtime cases."""
from pathlib import Path
import copy,hashlib,json,struct,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_mask_expression_tests import BLOB,PATH,BODIES,HEAD,extract,COUNTS
from port_workbench import expected_cases
from contract_registry import load_contracts
from assertion_fidelity import compare
from verify_mask_expression_oracle import equal_bytes,REVIEWED_CASES
from verify_mask_expression_sensitivity import MUTATIONS

def runs(indices):
 result=[]
 for i in sorted(set(indices)):
  if i<0:raise ValueError('Negative index')
  if result and result[-1][1]==i:result[-1][1]+=1
  else:result.append([i,i+1])
 return result

def encode(indices):
 output=bytearray();previous=0
 for start,end in runs(indices):
  for value in (start-previous,end-start):
   while True:
    byte=value&127;value>>=7;output.append(byte|(128 if value else 0))
    if not value:break
  previous=end
 return output.hex()

def decode(text):
 values=[];value=0;shift=0
 for byte in bytes.fromhex(text):
  value|=(byte&127)<<shift
  if byte&128:shift+=7
  else:values.append(value);value=0;shift=0
 if shift or len(values)%2:raise ValueError('Truncated run encoding')
 result=[];end=0
 for gap,size in zip(values[::2],values[1::2]):
  if size==0:raise ValueError('Empty run')
  start=end+gap
  if result and start==end:raise ValueError('Noncanonical adjacent runs')
  end=start+size;result.append([start,end])
 return result

class MaskExpressionTests(unittest.TestCase):
 def setUp(self):
  self.original=(ROOT/'tests/upstream/blender'/Path(PATH).name).read_bytes()
  self.manifest=json.loads((ROOT/'compatibility/mask-expression-ports.json').read_text())
  self.target=(ROOT/'crates/blended-core/src/mask_expression_cases.rs').read_text()
 def test_original_source_and_active_identities(self):
  self.assertEqual(hashlib.sha1(b'blob '+str(len(self.original)).encode()+b'\0'+self.original).hexdigest(),BLOB)
  original=list(extract(self.original.decode().split('/* Disable benchmark by default. */')[0]))
  self.assertEqual([(i,l) for i,b,l in original],[(c['id'],c['line']) for c in self.manifest['cases']]);self.assertEqual(len(original),15)
  for (identity,body,line),case in zip(original,self.manifest['cases']):self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),case['source_body_sha256'])
 def test_all_reviewed_bodies_and_original_helper_are_retained(self):
  self.assertEqual(hashlib.sha256(self.target.encode()).hexdigest(),REVIEWED_CASES)
  for name,body in BODIES.items():self.assertIn(body,self.target,name)
  self.assertTrue(self.target.startswith(HEAD));text=self.original.decode()
  helper=text[text.index('static Array<bool> random_bools'):text.index('TEST(index_mask_expression, Fuzzy)')]
  self.assertEqual(hashlib.sha256(helper.encode()).hexdigest(),self.manifest['random_helper_source_sha256'])
 def test_original_random_workload_is_not_reduced(self):
  self.assertIn('0..50',self.target);self.assertIn('%200_000+1',self.target);self.assertIn('%5000+1',self.target)
  self.assertIn('2147483648.0_f32',self.target);self.assertIn('BlenderRng::new(0)',self.target)
  self.assertEqual([c['expected_runtime_assertions'] for c in self.manifest['cases']],COUNTS)
  self.assertEqual(sum(COUNTS),321)
 def test_disabled_benchmark_stays_unported(self):
  self.assertEqual(len(self.manifest['conditional_unported_cases']),1);case=self.manifest['conditional_unported_cases'][0]
  self.assertEqual(case['id'],'index_mask_expression.Benchmark');self.assertEqual(case['condition'],'#if 0')
  self.assertEqual(case['status'],'unported_disabled_benchmark');self.assertFalse(self.manifest['complete_blender_test_port'])
 def test_current_registry_and_required_contract(self):
  cases,_=expected_cases();self.assertEqual(len(cases),596);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196692)
  contracts=load_contracts(ROOT)['contracts'];self.assertEqual(len(contracts),41)
  self.assertEqual(next(c for c in contracts if c['source_path']==PATH)['target_sha256'],REVIEWED_CASES)
 def test_lossless_codec_distinguishes_equal_cardinality_sets(self):
  self.assertEqual(encode([0,1,2,5,6]),'00030202');self.assertEqual(decode('00030202'),[[0,3],[5,7]])
  keys=set()
  for bits in range(256):
   indices=[i for i in range(8) if bits&(1<<i)];code=encode(indices);self.assertEqual(decode(code),runs(indices));keys.add(code)
  self.assertEqual(len(keys),256);self.assertNotEqual(encode([1,3]),encode([1,4]))
 def test_codec_retains_large_64_bit_offsets(self):
  indices=[(1<<40)+1,(1<<40)+2,(1<<40)+100];self.assertEqual(decode(encode(indices)),runs(indices))
  with self.assertRaises(ValueError):decode('80')
  with self.assertRaises(ValueError):decode('0100')
 def test_trace_comparison_cannot_accept_different_membership(self):
  value=lambda selected:{'mask_runs':'s:'+encode(selected)}
  expected=[dict(id='mask.check',expected_runtime_assertions=1)]
  reference=[dict(case='mask.check',kind='EQ',passed=True,values=[value([1,3]),value([1,3])])]
  self.assertEqual(compare(reference,copy.deepcopy(reference),expected)['assertions_compared'],1)
  wrong=copy.deepcopy(reference);wrong[0]['values']=[value([1,4]),value([1,4])]
  with self.assertRaises(ValueError):compare(reference,wrong,expected)
 def test_binary_oracle_does_not_ignore_last_byte(self):
  with tempfile.TemporaryDirectory() as directory:
   a=Path(directory)/'a';b=Path(directory)/'b';a.write_bytes(b'\x00\x01\x00');b.write_bytes(a.read_bytes());self.assertEqual(equal_bytes(a,b),3)
   b.write_bytes(b'\x00\x01\x01')
   with self.assertRaisesRegex(ValueError,'byte 2'):equal_bytes(a,b)
   b.write_bytes(b'\x00\x01')
   with self.assertRaises(ValueError):equal_bytes(a,b)
 def test_original_cpp_oracle_calls_unedited_original_helper(self):
  text=(ROOT/'tools/fidelity/mask_expression.hh').read_text()
  self.assertIn('blender::index_mask::tests::random_bools(rng,size)',text)
  self.assertIn('iteration<50',text);self.assertIn('rng.get_int32(200000)+1',text)
  self.assertIn('1)<<40',text);self.assertNotIn('sha256',text)
 def test_mutation_targets_are_unique_and_independent(self):
  code=(ROOT/'crates/blended-core/src/mask_expressions.rs').read_text();ids={c['id'] for c in self.manifest['cases']}
  for name,signature,replacement,target,control in MUTATIONS:
   self.assertEqual(code.count(signature),1);self.assertIn(target,ids);self.assertIn(control,ids);self.assertNotEqual(target,control)
 def test_missing_new_contract_is_not_reduced_success(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'compatibility').mkdir()
   for path in (ROOT/'compatibility').glob('*contract*.json'):
    if path.name!='mask-expression-assertion-contract.lock.json':(root/'compatibility'/path.name).write_bytes(path.read_bytes())
   with self.assertRaises(FileNotFoundError):load_contracts(root)
if __name__=='__main__':unittest.main()
