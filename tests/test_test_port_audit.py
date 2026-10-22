"""Coverage-accounting tests. These are not Blender feature tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from test_port_audit import evaluate
class TestPortAuditTests(unittest.TestCase):
    def setUp(self):
        self.inventory={'commit':'a'*40,'runtime_enumeration_complete':False,'fixture_completeness':'unknown','files':[{'path':'a.cc','sha256':'b'*64}], 'cases':[{'path':'a.cc','identity':'A.B','kind':'TEST','line':1}], 'fixtures':[], 'unreadable_files':[]}
        self.port={'path':'a.cc','id':'A.B','line':1,'source_sha256':'b'*64,'assertion_count':2,'semantics_reviewed':True,'target_test':'A__B','target_sha256':'c'*64}
        self.runtime={'commit':'a'*40,'complete':True,'families':{x:{'complete':True,'raw_evidence_sha256':'d'*64} for x in ['ctest','gtest','python','render','ui','compile_time']},'case_keys':['a.cc::A.B::1'],'unresolved':[]}
        self.execution={'source_commit':'a'*40,'case_results':{'a.cc::A.B::1':{'native':'passed','wasm':'passed','deployed':'passed'}}}
    def result(self,ports=None,runtime=None,execution=None):
        return evaluate(self.inventory,[self.port] if ports is None else ports,self.runtime if runtime is None else runtime,self.execution if execution is None else execution)
    def test_source_scan_alone_never_complete(self):self.assertFalse(self.result(runtime={})['complete_test_port'])
    def test_missing_case_never_passes(self):self.assertEqual(self.result(ports=[])['unported_source_candidates'],1)
    def test_unknown_fixtures_block_completion(self):self.assertFalse(self.result()['complete_test_port'])
    def test_lfs_pointer_is_not_fixture(self):
        self.inventory['fixture_completeness']='verified';self.inventory['fixtures']=[{'path':'a.blend','status':'lfs_pointer'}]
        self.assertFalse(self.result()['complete_test_port'])
    def test_duplicate_port_is_invalid(self):self.assertIn('duplicate_port:a.cc::A.B::1',self.result([self.port,self.port])['blockers'])
    def test_unknown_port_is_invalid(self):
        self.port['id']='Wrong';self.assertTrue(any(x.startswith('unknown_port:') for x in self.result()['blockers']))
    def test_source_hash_drift_invalidates_port(self):
        self.port['source_sha256']='e'*64;self.assertEqual(self.result()['mapped_source_candidates'],0)
    def test_missing_assertion_review_invalidates_port(self):
        self.port['semantics_reviewed']=False;self.assertEqual(self.result()['mapped_source_candidates'],0)
    def test_unexpanded_runtime_blocks_completion(self):
        self.runtime['unresolved']=['parameter values'];self.assertFalse(self.result()['complete_test_port'])
    def test_new_source_test_cannot_disappear(self):
        self.inventory['cases'].append({'path':'a.cc','identity':'A.C','kind':'TEST','line':2});self.assertEqual(self.result()['unported_source_candidates'],1)
    def test_ignored_is_not_execution_pass(self):
        self.inventory['fixture_completeness']='verified';self.execution['case_results']['a.cc::A.B::1']['wasm']='ignored';self.assertFalse(self.result()['test_conformance_complete'])
    def test_stale_commit_never_complete(self):
        self.runtime['commit']='f'*40;self.assertFalse(self.result()['complete_test_port'])
    def test_missing_runtime_family_is_blocked(self):
        del self.runtime['families']['ui'];self.assertFalse(self.result()['complete_test_port'])
    def test_runtime_extra_case_must_be_mapped(self):
        self.runtime['case_keys'].append('generated::Case/1');self.assertEqual(self.result()['unported_runtime_cases'],1)
    def test_unreadable_source_is_blocked(self):
        self.inventory['unreadable_files']=[{'path':'broken.py'}];self.assertFalse(self.result()['complete_test_port'])
    def test_empty_universe_never_complete(self):
        self.inventory['cases']=[];self.runtime['case_keys']=[];self.assertFalse(self.result(ports=[])['complete_test_port'])
    def test_verified_port_is_distinct_from_test_conformance(self):
        self.inventory['fixture_completeness']='verified';self.execution['case_results']['a.cc::A.B::1']['wasm']='failed'
        r=self.result();self.assertTrue(r['complete_test_port']);self.assertFalse(r['test_conformance_complete'])
    def test_fully_accounted_synthetic_fixture_passes(self):
        self.inventory['fixture_completeness']='verified';self.assertTrue(self.result()['test_conformance_complete'])
    def test_test_conformance_never_proves_all_features(self):
        self.inventory['fixture_completeness']='verified';self.assertFalse(self.result()['feature_parity'])
if __name__=='__main__':unittest.main()
