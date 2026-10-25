"""Corresponding-source completeness guards; not Blender runtime cases."""
from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
class CorrespondingSourceInputs(unittest.TestCase):
 def test_workflow_sources_are_part_of_the_archive_manifest(self):
  code=(ROOT/'tools/port_workbench.py').read_text()
  self.assertIn("('.github','crates','tools','tests'",code)
  for name in ('test-port-conformance.yml','port-inventory-integrity.yml'):
   self.assertTrue((ROOT/'.github/workflows'/name).is_file())
 def test_reference_limit_fixtures_are_included_not_only_on_the_ci_checkout(self):
  code=(ROOT/'tools/port_workbench.py').read_text()
  for name in ('evidence/mask-oracle-domain-failure.json','evidence/container-oracle-reference-limit.json'):
   self.assertIn(repr(name),code);self.assertIsInstance(json.loads((ROOT/name).read_text()),dict)
 def test_bundle_does_not_add_large_ephemeral_trace_directories(self):
  code=(ROOT/'tools/port_workbench.py').read_text()
  line=next(line for line in code.splitlines() if "for name in ('.github','crates'" in line)
  self.assertNotIn("'evidence',",line);self.assertNotIn("'.upstream'",line)
if __name__=='__main__':unittest.main()
