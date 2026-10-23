"""Mapping-loader regression; not an additional Blender feature test."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from inventory import scan_cpp
from test_port_audit import load_ports,key
class PortTargetPathsTests(unittest.TestCase):
 def test_embedded_mappings_use_their_actual_target_modules(self):
  contracts=json.loads((ROOT/'compatibility/assertion-contracts.lock.json').read_text())
  inventory={'commit':contracts['reference_commit'],'files':[],'cases':[]};seen=set()
  for c in contracts['contracts']:
   if c['source_path'] in seen:continue
   seen.add(c['source_path'])
   raw=(ROOT/'tests/upstream/blender'/Path(c['source_path']).name).read_text()
   inventory['files'].append({'path':c['source_path'],'sha256':hashlib.sha256(raw.encode()).hexdigest()})
   inventory['cases'].extend(scan_cpp(raw,c['source_path']))
  ports=load_ports(inventory)
  self.assertEqual(len(ports),251)
  self.assertTrue(all(p['semantics_reviewed'] for p in ports),[p['id'] for p in ports if not p['semantics_reviewed']])
  self.assertTrue({key(p) for p in ports}<={key(c) for c in inventory['cases']})
  static=[p for p in ports if p.get('kind')=='static_assert'];self.assertEqual(len(static),6)
  self.assertEqual(len([p for p in static if p['target_path'].endswith('numerics_text_cases.rs')]),4)
  self.assertEqual(len([p for p in static if p['target_path'].endswith('structure_cases.rs')]),1)
  self.assertEqual(len([p for p in static if p['target_path'].endswith('compile_time_cases.rs')]),1)
if __name__=='__main__':unittest.main()
