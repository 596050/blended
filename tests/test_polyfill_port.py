"""Polygon source, review-shard and discovery regressions, not upstream features."""
from pathlib import Path
import copy,hashlib,json,re,shutil,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_polyfill_tests import SOURCE,SHA,HEADER,parse,extract
from port_registry import verify_runtime_contract_bijection
from port_workbench import expected_cases
from contract_registry import load_contracts,EXTENSIONS
from inventory import scan_cpp
from assertion_fidelity import compare
class PolygonPorts(unittest.TestCase):
 def setUp(self):
  self.text=(ROOT/'tests/upstream/blender/BLI_polyfill_2d_test.cc').read_text();self.cases=json.loads((ROOT/'compatibility/polyfill-ports.json').read_text())['cases'];self.target=(ROOT/'crates/blended-core/src/polyfill_cases.rs').read_text()
 def test_original_snapshot_in_crate_and_test_tree_match(self):
  for p in [ROOT/'tests/upstream/blender/BLI_polyfill_2d_test.cc',ROOT/'crates/blended-core/src/polyfill_fixture.cc']:self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),SHA)
 def test_all_original_cases_and_input_body_hashes(self):
  source=list(extract(self.text));self.assertEqual(len(source),29)
  self.assertEqual([(i,l) for i,_,l in source],[(c['id'],c['line']) for c in self.cases])
  for (i,b,l),c in zip(source,self.cases):
   pts,bits,flag,n=parse(b);self.assertEqual(len(pts),c['polygon_size']);self.assertEqual(flag,c['flag']);self.assertEqual(n,c['expected_runtime_assertions']);self.assertEqual(hashlib.sha256(b.encode()).hexdigest(),c['source_body_sha256'])
 def test_helpers_and_original_bug_are_not_silently_changed(self):
  self.assertTrue(self.target.startswith(HEADER));self.assertIn('flip_sign(report,flag,poly,&mut tris);',self.target);self.assertNotIn('flip_sign(report,flag,&copy',self.target)
  self.assertIn('copy.rotate_left(1);',self.target);self.assertIn('if reversed!=0{copy.reverse();}',self.target)
  self.assertEqual(len(re.findall(r'\b(?:eq|ne|yes|near)!\(',HEADER)),12)
 def test_both_plain_and_beautified_checks_remain(self):
  self.assertEqual(self.target.count('check(report,flag,poly,tris);'),2);self.assertIn('p::beautify(poly,tris);',self.target)
 def test_counts_are_execution_counts_not_features(self):
  cases,_=expected_cases();self.assertEqual(len(cases),609);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196744)
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in self.cases),1534672);self.assertEqual(sum(c['polygon_size'] for c in self.cases)*8,3064)
 def test_digit_prefixed_test_arguments_are_discovered(self):
  found={(c['identity'],c['line']) for c in scan_cpp(self.text,SOURCE)}
  self.assertTrue({(c['id'],c['line']) for c in self.cases}<=found)
  self.assertIn(('polyfill2d.3Colinear',438),found);self.assertIn(('polyfill2d.4Colinear',445),found)
 def test_numbers_do_not_invent_tests_or_hide_quoted_text(self):
  text='auto n=1\'000; auto z=0.TEST(fake,No); const char*s=R"x(TEST(fake,1Bad))x"; TEST(real,3Good){}'
  self.assertEqual([c['identity'] for c in scan_cpp(text,'x.cc')],['real.3Good'])
 def test_ne_values_are_checked_not_just_result(self):
  expected=[dict(id='x',expected_runtime_assertions=1)];r=[dict(case='x',kind='NE',passed=True,values=['i:0','i:1'])]
  self.assertEqual(compare(r,copy.deepcopy(r),expected)['assertions_compared'],1)
  changed=copy.deepcopy(r);changed[0]['values'][1]='i:2'
  with self.assertRaises(ValueError):compare(r,changed,expected)
class RequiredContractShards(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  for name in ('compatibility/assertion-contracts.lock.json',*EXTENSIONS):
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
 def test_current_union_is_exact(self):self.assertEqual(len(load_contracts(self.root)['contracts']),43)
 def test_missing_shard_is_an_error_not_reduced_scope(self):
  (self.root/EXTENSIONS[0]).unlink()
  with self.assertRaises(FileNotFoundError):load_contracts(self.root)
 def test_wrong_reference_is_rejected(self):
  p=self.root/EXTENSIONS[0];d=json.loads(p.read_text());d['reference_commit']='0'*40;p.write_text(json.dumps(d))
  with self.assertRaises(ValueError):load_contracts(self.root)
 def test_duplicate_identity_is_rejected(self):
  p=self.root/EXTENSIONS[0];d=json.loads(p.read_text());d['contracts']*=2;p.write_text(json.dumps(d))
  with self.assertRaises(ValueError):load_contracts(self.root)
 def test_removing_polygon_registry_cannot_pass_contract(self):
  cases,_=expected_cases()
  with self.assertRaises(ValueError):verify_runtime_contract_bijection(ROOT,[c for c in cases if c['group']!='polyfill'])
if __name__=='__main__':unittest.main()
