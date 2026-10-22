"""Infrastructure tests, not Blender feature tests."""
import json
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ManifestTests(unittest.TestCase):
    def test_exact_upstream_pins(self):
        data=json.loads((ROOT/'upstream.lock.json').read_text())
        self.assertEqual(set(data['upstreams']),{'blender','cycles','solarxy'})
        for entry in data['upstreams'].values():self.assertRegex(entry['commit'],r'^[0-9a-f]{40}$')
    def test_case_names_and_indices(self):
        source=(ROOT/'crates/blended-core/src/compat_cases.rs').read_text()
        names=re.findall(r'\("(math_vector\.[^"]+)",',source)
        self.assertEqual(len(names),17);self.assertEqual(len(set(names)),17)
        manifest=json.loads((ROOT/'site/compat/ports.json').read_text())
        self.assertEqual([c['id'] for c in manifest['cases']],names)
        self.assertEqual([c['wasm_index'] for c in manifest['cases']],list(range(17)))
    def test_no_manufactured_execution(self):
        manifest=json.loads((ROOT/'site/compat/ports.json').read_text())
        self.assertFalse(manifest['full_feature_parity'])
        for c in manifest['cases']:self.assertEqual(c['execution'],'not_run')
    def test_same_cases_on_native_and_wasm(self):
        source=(ROOT/'crates/blended-core/src/lib.rs').read_text()
        self.assertIn('compat_cases::CASES.get',source)
        source=(ROOT/'crates/blended-core/tests/upstream_math_vector.rs').read_text()
        self.assertEqual(len(re.findall(r'case!\(',source)),17)
if __name__=='__main__':unittest.main()
