"""Source-bundle and supplemental-corpus guards, not extra upstream cases."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_utf8_oracle import SIZES
class Utf8SourceNotices(unittest.TestCase):
 def test_all_original_stress_lengths_are_in_exact_input_oracle(self):
  self.assertEqual(SIZES,tuple(range(1,13))+(16,31,32,33))
  self.assertEqual(len(SIZES)*256,4096)
  self.assertEqual(sum(SIZES)*256,48640)
 def test_corresponding_source_archive_includes_full_notices(self):
  source=(ROOT/'tools/port_workbench.py').read_text()
  self.assertIn("'docs','LICENSES','Cargo.toml'",source)
  notice=(ROOT/'LICENSES/wcwidth-original-notice.txt').read_text()
  self.assertIn('Markus Kuhn',notice);self.assertIn('Permission to use, copy, modify',notice)
if __name__=='__main__':unittest.main()
