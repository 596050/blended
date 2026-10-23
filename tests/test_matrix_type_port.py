"""Matrix translation regressions, separate from upstream feature tests."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from port_matrix_type_tests import SHA,SOURCE,extract,translate,comments
from assertion_fidelity import contracts
class MatrixPortTests(unittest.TestCase):
 def setUp(self):
  self.source=(ROOT/'tests/upstream/blender'/Path(SOURCE).name).read_text()
  self.target=(ROOT/'crates/blended-core/src/matrix_type_cases.rs').read_text()
  self.manifest=json.loads((ROOT/'compatibility/matrix-type-ports.json').read_text())
 def test_complete_runtime_case_identity_and_lines(self):
  self.assertEqual(hashlib.sha256(self.source.encode()).hexdigest(),SHA)
  cases=list(extract(self.source));self.assertEqual(len(cases),21)
  self.assertEqual([(i,l) for i,b,l in cases],[(c['id'],c['line']) for c in self.manifest['cases']])
 def test_original_macros_expand_all_scalar_checks(self):
  sites=events=0
  for identity,body,line in extract(self.source):
   t=translate(body,identity);self.assertIn(t,self.target)
   n=len(re.findall(r'\bEXPECT_EQ\s*\(',comments(body)));mat=len(re.findall(r'\bEXPECT_M4_NEAR\s*\(',comments(body)))
   self.assertEqual(len(re.findall(r'\b(?:eq|numeq|near)!',t)),n+16*mat)
   sites+=n+mat;events+=n+16*mat
  self.assertEqual(sites,184);self.assertEqual(events,289)
 def test_zero_initialisation_uses_default_constructor(self):
  self.assertIn('m::M::<f32,2,2>::default()',self.target)
 def test_const_external_view_has_no_write_interface(self):
  self.assertIn('m::ReadView::<f32,4,4,4,4>::new(&c_style_mat,0,0)',self.target)
  self.assertIn('m::View::<f32,4,4,4,4>::new(&c_style_mat,0,0)',self.target)
 def test_original_normalisation_tolerance_not_relaxed(self):
  body=next(b for i,b,l in extract(self.source) if i.endswith('.ViewMatrixNormalize'))
  t=translate(body,'math_matrix_types.ViewMatrixNormalize')
  self.assertEqual(t.count('1e-8_f32'),16)
  self.assertIn('0.267261236',t)
 def test_shared_writeback_and_copy_conversion_retained(self):
  self.assertIn('m::Shared::new(',self.target)
  self.assertIn('view.assign(view.read()',self.target)
  self.assertIn('::from_matrix(&view.read())',self.target)
 def test_reviewed_hash_and_completion_status(self):
  self.assertTrue(any(c['source_path']==SOURCE for c in contracts(ROOT)['contracts']))
  self.assertFalse(self.manifest['complete_blender_test_port'])
if __name__=='__main__':unittest.main()
