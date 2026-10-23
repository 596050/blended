"""Integration safety checks, not additional upstream feature tests."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from verify_embedded_static_ports import scoped_mutation
from port_registry import verify_runtime_contract_bijection
from port_workbench import expected_cases
class IntegrationGuardTests(unittest.TestCase):
 def test_all_embedded_mutations_hit_only_the_intended_input(self):
  entries=json.loads((ROOT/'compatibility/compile-time-ports.json').read_text())['cases']
  for c in entries:
   if not c.get('embedded'):continue
   original=(ROOT/c['target_path']).read_text();mutated=scoped_mutation(original,c)
   self.assertNotEqual(original,mutated)
   self.assertEqual(original.count(c['target_assertion']),mutated.count(c['target_assertion']))
   self.assertEqual(original.count(c['negative_fixture_before'])-1,mutated.count(c['negative_fixture_before']))
 def test_audit_registry_cannot_be_reduced(self):
  expected,_=expected_cases()
  with self.assertRaises(ValueError):verify_runtime_contract_bijection(ROOT,expected[:-1])
 def test_wrong_enclosing_function_rejected(self):
  c=next(c for c in json.loads((ROOT/'compatibility/compile-time-ports.json').read_text())['cases'] if c.get('embedded'))
  original=(ROOT/c['target_path']).read_text();c=dict(c,rust_function='missing_implementation')
  with self.assertRaises(ValueError):scoped_mutation(original,c)
 def test_workflow_keeps_real_full_suite_failure(self):
  text=(ROOT/'.github/workflows/test-port-conformance.yml').read_text()
  self.assertIn('--require-complete',text)
  self.assertNotIn('continue-on-error',text)
  self.assertIn('needs: [native-and-wasm, assertion-fidelity]',text)
  self.assertIn('python3 tools/verify_embedded_static_ports.py',text)
  self.assertIn("{(p['path'],p['id']) for p in static_ports}",text)
 def test_inventory_integrity_tracks_source_keys_not_an_old_total(self):
  text=(ROOT/'.github/workflows/port-inventory-integrity.yml').read_text()
  self.assertNotIn('==132',text)
  self.assertIn('len(expected)+len(static)',text)
  self.assertIn('set(port_keys)<=set(source_keys)',text)
  self.assertIn("{(p['path'],p['id']) for p in static_ports}",text)
if __name__=='__main__':unittest.main()
