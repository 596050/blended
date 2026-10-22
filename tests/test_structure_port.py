"""Checks the new test-port translator's frozen inputs and outputs, not feature parity."""
import hashlib,json,re,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from port_structure_tests import FILES,extract,transform
ROOT=Path(__file__).resolve().parents[1]
class StructureTranslationTests(unittest.TestCase):
    def setUp(self):self.manifest=json.loads((ROOT/'compatibility/structure-ports.json').read_text())
    def test_all_three_frozen_source_files_match_pinned_hashes(self):
        for f,h in FILES.items():self.assertEqual(hashlib.sha256((ROOT/'tests/upstream/blender'/f).read_bytes()).hexdigest(),h)
    def test_every_source_case_has_exactly_one_translation(self):
        expected=[]
        for filename in FILES:
            text=(ROOT/'tests/upstream/blender'/filename).read_text()
            expected.extend(identity for identity,_,_,_ in extract(text))
        self.assertEqual([c['id'] for c in self.manifest['cases']],expected)
        self.assertEqual(len(expected),54)
    def test_assertion_sites_preserved(self):
        for filename in FILES:
            for identity,_,body,_ in extract((ROOT/'tests/upstream/blender'/filename).read_text()):
                code=transform(body,identity)
                self.assertEqual(len(re.findall(r'\bEXPECT_\w+\s*\(',body)),len(re.findall(r'\b(?:eq|gt|yes|no)!',code)),identity)
    def test_loops_have_explicit_execution_counts(self):
        counts={c['id']:c['expected_runtime_assertions'] for c in self.manifest['cases']}
        self.assertEqual(counts['bounds.Contains'],8)
        self.assertEqual(sum(counts.values()),235)
        self.assertEqual(sum(c['assertion_count'] for c in self.manifest['cases']),226)
    def test_constexpr_array_and_static_assert_retained(self):
        source=(ROOT/'crates/blended-core/src/structure_cases.rs').read_text()
        self.assertIn('RANGE.get(0) as usize',source)
        self.assertIn('const _: () = assert!(RANGE.size() == 1)',source)
    def test_original_asymmetric_3d_case_not_normalised(self):
        body=next(b for i,_,b,_ in extract((ROOT/'tests/upstream/blender/BLI_bounds_test.cc').read_text()) if i=='bounds.IntersectSegment3D')
        code=transform(body,'bounds.IntersectSegment3D')
        self.assertIn('no!(r, int_bounds.intersects_segment(m::VecN([(-10) as i32, (-10) as i32, (-10) as i32]), m::VecN([(-10) as i32, (-10) as i32, (-10) as i32])))',code)
    def test_legacy_vector_assertion_sites_and_hash(self):
        d=json.loads((ROOT/'compatibility/vector-assertions.json').read_text())
        source=(ROOT/'tests/upstream/blender/BLI_math_vector_test.cc').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),d['source_sha256'])
        self.assertEqual([(i,len(re.findall(r'\bEXPECT_',b))) for i,_,b,_ in extract(source.decode())],[(c['id'],c['assertion_count']) for c in d['cases']])
        self.assertEqual(sum(c['assertion_count'] for c in d['cases']),68)
    def test_manifest_never_claims_whole_suite_complete(self):self.assertFalse(self.manifest['complete_blender_test_port'])
if __name__=='__main__':unittest.main()
