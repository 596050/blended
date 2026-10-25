"""Span port/infrastructure regressions, not additional upstream Blender cases."""
from pathlib import Path
import copy,hashlib,json,shutil,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_span_tests import BLOB,BODIES,COUNTS,PATH,HEAD,extract
from port_workbench import expected_cases
from static_port_registry import load_static_cases,STATIC_MANIFESTS
from verify_span_static import MUTATIONS,diagnostics
from verify_span_sensitivity import MUTATIONS as RUNTIME_MUTATIONS,mutate
from verify_span_oracle import CPP,RUST,HEADER_SHA
class SpanPorts(unittest.TestCase):
 def setUp(self):
  self.raw=(ROOT/'tests/upstream/blender/BLI_span_test.cc').read_bytes();self.source=self.raw.decode()
  self.runtime=json.loads((ROOT/'compatibility/span-ports.json').read_text())['cases'];self.static=json.loads((ROOT/'compatibility/span-static-ports.json').read_text())['cases']
  self.target=(ROOT/'crates/blended-core/src/span_cases.rs').read_text()
 def test_complete_original_file_and_all_runtime_identities(self):
  self.assertEqual(hashlib.sha1(b'blob '+str(len(self.raw)).encode()+b'\0'+self.raw).hexdigest(),BLOB)
  originals=list(extract(self.source));self.assertEqual(len(originals),40)
  self.assertEqual([(i,l) for i,b,l in originals],[(c['id'],c['line']) for c in self.runtime])
  for (identity,body,line),c in zip(originals,self.runtime):self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),c['source_body_sha256'])
 def test_all_reviewed_translations_and_counts_are_reproduced(self):
  self.assertTrue(self.target.startswith(HEAD));self.assertEqual(sum(COUNTS),153)
  for c in self.runtime:
   key=c['id'] if c['id'].startswith('mutable_span.') else c['id'].split('.')[1]
   self.assertIn(BODIES[key],self.target);self.assertEqual(c['expected_runtime_assertions'],COUNTS[c['index']])
 def test_all_thirteen_original_compile_time_predicates_are_separate(self):
  self.assertEqual([c['line'] for c in self.static],[415,416,417,418,421,428,429,430,431,432,433,434,435])
  for c in self.static:
   self.assertEqual(self.source.splitlines()[c['line']-1].strip(),c['source_condition']);self.assertEqual(c['runtime_assertions'],0)
  self.assertEqual(len(load_static_cases(ROOT)),19)
 def test_zero_runtime_case_is_not_given_fabricated_assertions(self):
  case=next(c for c in self.runtime if c['id']=='span.ImplicitConversions')
  self.assertEqual(case['expected_runtime_assertions'],0);self.assertTrue(case['compile_time_only'])
  body=BODIES['ImplicitConversions'];self.assertEqual(body.count('require_into::<'),5);self.assertEqual(body.count('not_into!('),3)
 def test_every_compile_time_negative_targets_exactly_one_predicate(self):
  self.assertEqual(len(MUTATIONS),13)
  for old,new,code in MUTATIONS:
   self.assertEqual(self.target.count(old),1);self.assertNotEqual(old,new);self.assertIn(code,{'E0080','E0277','E0283'})
 def test_all_executable_cases_and_static_counts_are_independent(self):
  cases,_=expected_cases();self.assertEqual(len(cases),581);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196371)
  self.assertEqual([c['id'] for c in cases if c['expected_runtime_assertions']==0],['bit_span.SetEmpty','span.ImplicitConversions'])
 def test_cell_backing_and_actual_pointer_equality_not_snapshots(self):
  self.assertIn('array[1].set(10)',BODIES['IsReferencing']);self.assertIn('peq!(report,new_a_span.at(0)',BODIES['CastSameSize'])
  self.assertIn('cell.set(cell.get()+10)',BODIES['MutableReverseIterator'])
  self.assertIn('core::ptr::eq',HEAD)
 def test_runtime_mutations_keep_expected_case_counts(self):
  source=(ROOT/'crates/blended-core/src/spans.rs').read_text();ids={c['id'] for c in self.runtime}
  for _,_,kind,old,new,target,control in RUNTIME_MUTATIONS:
   self.assertEqual(source.count(old),1);self.assertNotEqual(mutate(source,kind,old,new),source)
   self.assertIn(target,ids);self.assertIn(control,ids);self.assertNotEqual(target,control)
 def test_oracle_does_not_hide_original_constructor_failure(self):
  script=(ROOT/'tools/verify_span_oracle.py').read_text()
  self.assertIn('original_conversion_limit',script);self.assertIn('not_compared_as_executable_parity',script)
  self.assertIn('for(int n=0;n<=32;++n)',CPP);self.assertIn('for n in 0..=32',RUST)
  self.assertIn('m.fill(7);view(s)',CPP);self.assertIn('m.fill(7);view(&mut out,s)',RUST)
 def test_diagnostics_require_real_coded_compiler_errors(self):
  text='not JSON\n'+json.dumps({'reason':'compiler-message','message':{'level':'warning','code':{'code':'E0080'}}})+'\n'+json.dumps({'reason':'compiler-message','message':{'level':'error','code':{'code':'E0080'},'spans':[{'file_name':'span_cases.rs'}]}})
  self.assertEqual(len(diagnostics(text)),1)

class RequiredStaticManifests(unittest.TestCase):
 def root(self):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);p=Path(d.name);(p/'compatibility').mkdir();shutil.copyfile(ROOT/'upstream.lock.json',p/'upstream.lock.json')
  for name in STATIC_MANIFESTS:shutil.copyfile(ROOT/'compatibility'/name,p/'compatibility'/name)
  return p
 def test_missing_manifest_cannot_reduce_static_universe(self):
  root=self.root();(root/'compatibility/span-static-ports.json').unlink()
  with self.assertRaises(FileNotFoundError):load_static_cases(root)
 def test_duplicate_or_stale_predicate_is_rejected(self):
  root=self.root();p=root/'compatibility/span-static-ports.json';data=json.loads(p.read_text());data['cases'].append(copy.deepcopy(data['cases'][0]));p.write_text(json.dumps(data))
  with self.assertRaises(ValueError):load_static_cases(root)
  data['cases'].pop();data['upstream_commit']='0'*40;p.write_text(json.dumps(data))
  with self.assertRaises(ValueError):load_static_cases(root)
if __name__=='__main__':unittest.main()
