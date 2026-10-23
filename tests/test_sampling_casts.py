"""Cast-token regressions for the translator, not additional Blender cases."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from port_sampling_tests import image_expr
class SamplingCastTests(unittest.TestCase):
 def test_unsigned_constructor_is_not_parsed_as_signed_suffix(self):
  self.assertEqual(image_expr('uint4(res)'),'(res).map(|v|v as u32)')
 def test_signed_constructor_retains_signed_type(self):
  self.assertEqual(image_expr('int4(res)'),'(res).map(|v|v as i32)')
if __name__=='__main__':unittest.main()
