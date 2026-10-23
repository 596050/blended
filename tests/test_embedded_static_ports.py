"""Compile-time port accounting, distinct from executed Blender runtime tests."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from inventory import scan_cpp
class EmbeddedStaticPortsTests(unittest.TestCase):
 def test_six_explicit_static_assertions_accounted(self):
  m=json.loads((ROOT/'compatibility/compile-time-ports.json').read_text())
  self.assertEqual(len(m['cases']),6)
  for c in m['cases']:
   self.assertEqual(c['kind'],'static_assert');self.assertEqual(c['runtime_assertions'],0)
 def test_frozen_source_lines_and_conditions(self):
  m=json.loads((ROOT/'compatibility/compile-time-ports.json').read_text())
  for c in m['cases']:
   src=(ROOT/'tests/upstream/blender'/Path(c['path']).name).read_text()
   self.assertIn(c['id'],[x['identity'] for x in scan_cpp(src,c['path'])])
   self.assertEqual(hashlib.sha256(src.encode()).hexdigest(),c['source_sha256'])
   if c.get('embedded'):
    self.assertIn(c['source_condition'],src.splitlines()[c['line']-1])
    self.assertIn(c['target_assertion'],(ROOT/c['target_path']).read_text())
 def test_static_macro_discovery_does_not_ignore_alignment(self):
  cases=scan_cpp('BLI_STATIC_ASSERT(sizeof(T)==4, "");\nBLI_STATIC_ASSERT_ALIGN(T, 16);\nTEST(A,B){}','a.cc')
  self.assertEqual([c['identity'] for c in cases],['static_assert@1','static_assert@2','A.B'])
 def test_static_macros_in_comments_and_strings_are_not_tests(self):
  text='// BLI_STATIC_ASSERT_ALIGN(T,16);\nconst char *s="BLI_STATIC_ASSERT(x,y)";\nTEST(A,B){}'
  self.assertEqual([c['identity'] for c in scan_cpp(text,'a.cc')],['A.B'])
if __name__=='__main__':unittest.main()
