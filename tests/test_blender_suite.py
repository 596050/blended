"""Completeness-gate tests, not Blender feature tests."""
import copy
import hashlib
import unittest
from tools.blender_suite import lfs_pointer, verify_fixture, parse_gtest_list, parse_ctest_json, assess
PIN='a'*40
APP='b'*40
HASH='c'*64
URL='https://example.org/blended/index.html'
def fixture():
    contract={'schema':1,'upstream_commit':PIN,'required_profiles':['cpu'],'source_obligations':[{'path':'tests/a.py','sha256':HASH}],'fixtures':[],'source_audit_errors':[],'external_dependencies':[]}
    registries=[{'profile':'cpu','upstream_commit':PIN,'complete':True,'build_config_sha256':HASH,'cases':[{'id':'unit.a','source_paths':['tests/a.py'],'disabled':False}]}]
    ports=[{'source_path':'tests/a.py','source_sha256':HASH,'assertions':'upstream_verbatim','adapter':'python','adapter_sha256':HASH,'review':'reviewed','cases':[{'profile':'cpu','id':'unit.a'}]}]
    results=[{'profile':'cpu','id':'unit.a','upstream_commit':PIN,'realm':realm,'status':'passed','executed':True,'skipped':0,'log_sha256':HASH,'application_commit':APP,'url':URL} for realm in ('native','browser')]
    return contract,registries,ports,results
class FixtureTests(unittest.TestCase):
    def test_pointer_recognises_non_blend_files(self):
        raw=b'version https://git-lfs.github.com/spec/v1\noid sha256:'+b'1'*64+b'\nsize 17\n'
        self.assertEqual(lfs_pointer(raw),{'oid':'1'*64,'size':17})
    def test_non_pointer_is_not_lfs(self): self.assertIsNone(lfs_pointer(b'BLENDER-v501'))
    def test_malformed_pointer_is_rejected(self):
        with self.assertRaises(ValueError): lfs_pointer(b'version https://git-lfs.github.com/spec/v1\nsize 2\n')
    def test_fixture_requires_hash_not_just_filename(self):
        expected={'oid':hashlib.sha256(b'abc').hexdigest(),'size':3}
        self.assertEqual(verify_fixture(b'abc',expected),'verified')
        self.assertEqual(verify_fixture(b'abd',expected),'hash_mismatch')
        self.assertEqual(verify_fixture(b'ab',expected),'size_mismatch')
    def test_pointer_never_counts_as_payload(self):
        raw=b'version https://git-lfs.github.com/spec/v1\noid sha256:'+b'1'*64+b'\nsize 17\n'
        self.assertEqual(verify_fixture(raw,{'oid':'1'*64,'size':17}),'lfs_pointer')
class EnumerationTests(unittest.TestCase):
    def test_gtest_expands_actual_runtime_parameter_names(self):
        text='Running main() from gtest_main.cc\nVector/0.  # TypeParam = float\n  Works\nCases/Modifier.\n  Evaluate/0  # GetParam() = 1\n  Evaluate/1  # GetParam() = 2\n'
        self.assertEqual([x['id'] for x in parse_gtest_list(text)],['Vector/0.Works','Cases/Modifier.Evaluate/0','Cases/Modifier.Evaluate/1'])
    def test_gtest_disabled_is_retained(self): self.assertTrue(all(x['disabled'] for x in parse_gtest_list('DISABLED_Suite.\n  A\nSuite.\n  DISABLED_B\n')))
    def test_gtest_duplicate_is_rejected(self):
        with self.assertRaises(ValueError): parse_gtest_list('Suite.\n  A\n  A\n')
    def test_gtest_empty_is_rejected(self):
        with self.assertRaises(ValueError): parse_gtest_list('')
    def test_ctest_preserves_commands_properties_and_disabled(self):
        raw={'kind':'ctestInfo','version':{'major':1,'minor':0},'tests':[{'name':'render','command':['blender','--background'],'properties':[{'name':'DISABLED','value':True}]}]}
        case=parse_ctest_json(raw)[0]
        self.assertEqual(case['command'],['blender','--background']);self.assertTrue(case['disabled'])
    def test_ctest_duplicate_is_rejected(self):
        with self.assertRaises(ValueError): parse_ctest_json({'tests':[{'name':'a'},{'name':'a'}]})
    def test_ctest_empty_is_rejected(self):
        with self.assertRaises(ValueError): parse_ctest_json({'tests':[]})
class CompletenessTests(unittest.TestCase):
    def report(self,d): return assess(*d,expected_application_commit=APP,expected_url=URL)
    def test_synthetic_complete_contract(self):
        r=self.report(fixture());self.assertTrue(r['test_port_complete']);self.assertTrue(r['conformance_passed']);self.assertFalse(r['feature_parity_proven'])
    def test_assertion_failure_is_executed_port_but_not_conformance(self):
        d=fixture();d[3][1]['status']='failed';r=self.report(d)
        self.assertTrue(r['test_port_complete']);self.assertFalse(r['conformance_passed'])
    def test_skipped_not_run_unsupported_blocked_never_pass(self):
        for state in ('skipped','not_run','unsupported','blocked'):
            with self.subTest(state=state):
                d=fixture();d[3][1]['status']=state;self.assertFalse(self.report(d)['test_port_complete'])
# Each generated method is an independently named regression, not an aggregate feature count.
def rejecting(name,mutate):
    def test(self):
        d=fixture();mutate(d);self.assertFalse(self.report(d)['test_port_complete'])
    test.__name__='test_'+name;setattr(CompletenessTests,test.__name__,test)
rejecting('empty_suite_cannot_pass',lambda d:d[1][0].update(cases=[]))
rejecting('discovery_is_not_execution',lambda d:d[3].clear())
rejecting('missing_profile_blocks',lambda d:d[0]['required_profiles'].append('gpu'))
rejecting('unexpanded_runtime_inventory_blocks',lambda d:d[1][0].update(complete=False))
rejecting('fixture_pointer_blocks',lambda d:d[0].update(fixtures=[{'path':'test.exr','status':'lfs_pointer'}]))
rejecting('source_audit_failure_blocks',lambda d:d[0].update(source_audit_errors=['missing tracked source']))
rejecting('external_dependency_unpinned_blocks',lambda d:d[0].update(external_dependencies=[{'name':'benchmarks','status':'unpinned'}]))
rejecting('unmapped_source_file_blocks',lambda d:d[0]['source_obligations'].append({'path':'tests/b.py','sha256':HASH}))
rejecting('source_hash_mismatch_blocks',lambda d:d[2][0].update(source_sha256='d'*64))
rejecting('unreviewed_translation_blocks',lambda d:d[2][0].update(assertions='translated',review='unreviewed'))
rejecting('changed_assertions_block',lambda d:d[2][0].update(assertions='weakened'))
rejecting('missing_adapter_blocks',lambda d:d[2][0].update(adapter=''))
rejecting('missing_browser_case_mapping_blocks',lambda d:d[2][0].update(cases=[]))
rejecting('native_only_does_not_prove_browser_port',lambda d:d[3].pop())
rejecting('missing_native_baseline_blocks',lambda d:d[3].pop(0))
rejecting('nested_skipped_tests_block',lambda d:d[3][1].update(skipped=1))
rejecting('wrong_upstream_commit_blocks',lambda d:d[3][1].update(upstream_commit='f'*40))
rejecting('wrong_deployed_commit_blocks',lambda d:d[3][1].update(application_commit='f'*40))
rejecting('local_surrogate_not_public_evidence',lambda d:d[3][1].update(url='http://localhost:8000/'))
rejecting('duplicate_result_does_not_raise_count',lambda d:d[3].append(copy.deepcopy(d[3][1])))
rejecting('unknown_result_blocks',lambda d:d[3].append(dict(d[3][1],id='invented')))
rejecting('disabled_case_not_silently_removed',lambda d:d[1][0]['cases'][0].update(disabled=True))
rejecting('missing_log_evidence_blocks',lambda d:d[3][1].update(log_sha256=''))
rejecting('fake_pass_without_execution_blocks',lambda d:d[3][1].update(executed=False))
rejecting('unregistered_port_case_blocks',lambda d:d[2][0]['cases'].append({'profile':'cpu','id':'invented'}))
rejecting('missing_build_configuration_blocks',lambda d:d[1][0].update(build_config_sha256=''))
rejecting('utility_tests_cannot_cover_other_sources',lambda d:d[0]['source_obligations'].append({'path':'tests/modifiers.py','sha256':HASH}))
if __name__=='__main__': unittest.main()
