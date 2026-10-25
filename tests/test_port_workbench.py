"""Acceptance-oracle checks, distinct from Blender feature tests."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from port_workbench import expected_cases,validate_result
class WorkbenchContractTests(unittest.TestCase):
    def setUp(self):
        self.expected=[{'id':'old.case','group':'legacy','expected_runtime_assertions':6},{'id':'new.case','group':'additional','expected_runtime_assertions':3},{'id':'bounds.case','group':'structures','expected_runtime_assertions':8}]
        self.data={'source_commit':'a'*40,'reference_commit':'b'*40,'complete_test_port':False,'wasm_sha256':'c'*64,'status':'passed','passed':3,'vector_assertions':6,'additional_assertions':3,'structure_assertions':8,'collection_assertions':0,'string_assertions':0,'bit_span_assertions':0,'numeric_type_assertions':0,'matrix_type_assertions':0,'geometry_math_assertions':0,'sampling_assertions':0,'curve_assertions':0,'heap_assertions':0,'data_assertions':0,'string_ops_assertions':0,'utf8_assertions':0,'pixel_format_assertions':0,'polyfill_assertions':0,'span_assertions':0,'invalid_index_rejected':True,'errors':[], 'cases':[dict(id=c['id'],group=c['group'],assertions=c['expected_runtime_assertions'],passed=True,code=1) for c in self.expected]}
    def check(self):validate_result(self.data,self.expected,'a'*40,'b'*40)
    def test_exact_valid_result(self):self.check()
    def test_missing_test_cannot_reduce_denominator(self):
        self.data['cases'].pop();self.data['passed']=2
        with self.assertRaises(ValueError):self.check()
    def test_success_flag_cannot_replace_assertions(self):
        self.data['cases'][2]['assertions']=1
        with self.assertRaises(ValueError):self.check()
    def test_wrong_test_identity_is_rejected(self):
        self.data['cases'][2]['id']='dummy'
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_identity_is_rejected(self):
        self.data['cases'][2]=copy.deepcopy(self.data['cases'][1])
        with self.assertRaises(ValueError):self.check()
    def test_wrong_reference_is_rejected(self):
        self.data['reference_commit']='f'*40
        with self.assertRaises(ValueError):self.check()
    def test_wrong_source_is_rejected(self):
        self.data['source_commit']='f'*40
        with self.assertRaises(ValueError):self.check()
    def test_failed_case_is_rejected(self):
        self.data['cases'][0]['code']=0
        with self.assertRaises(ValueError):self.check()
    def test_missing_wasm_digest_is_rejected(self):
        del self.data['wasm_sha256']
        with self.assertRaises(ValueError):self.check()
    def test_whole_suite_claim_is_rejected(self):
        self.data['complete_test_port']=True
        with self.assertRaises(ValueError):self.check()
    def test_changed_total_is_rejected(self):
        self.data['structure_assertions']=7
        with self.assertRaises(ValueError):self.check()
    def test_invalid_index_success_is_rejected(self):
        self.data['invalid_index_rejected']=False
        with self.assertRaises(ValueError):self.check()
    def test_current_universe_has_unique_upstream_identities(self):
        cases,commit=expected_cases();self.assertEqual(len(cases),581);self.assertEqual(len(commit),40)
        self.assertEqual(sum(c['expected_runtime_assertions'] or 0 for c in cases if c['group']=='structures'),235)
if __name__=='__main__':unittest.main()
