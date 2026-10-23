"""Never hide duplicate source declarations or present absent runtime data as zero."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from inventory import scan_cpp
from test_port_audit import evaluate,key,FAMILIES
class InventoryAccountingTests(unittest.TestCase):
 def setUp(self):
  self.inv={'commit':'a'*40,'fixture_completeness':'verified','files':[],'cases':[{'path':'a.cc','line':1,'identity':'A.B','kind':'TEST'}],'fixtures':[],'unreadable_files':[]}
  self.runtime={'commit':'a'*40,'complete':True,'unresolved':[],'families':{f:{'complete':True,'raw_evidence_sha256':'b'*64} for f in FAMILIES},'case_keys':['a.cc::A.B::1']}
 def test_same_line_static_assertions_remain_distinct(self):
  source='static_assert(true); static_assert(false);'
  cases=scan_cpp(source,'a.hh')
  self.assertEqual(len(cases),2);self.assertEqual(len({key(c) for c in cases}),2)
  self.assertEqual([c['column'] for c in cases],[1,22])
  self.assertTrue(all(c['source_identity_disambiguated'] for c in cases))
 def test_single_static_identity_stays_compatible(self):
  case=scan_cpp('\n  static_assert(true);','a.hh')[0]
  self.assertEqual(case['identity'],'static_assert@2');self.assertEqual(case['column'],3)
 def test_repeated_case_label_not_dropped(self):
  cases=scan_cpp('TEST(S,C){} TEST(S,C){}','a.cc')
  self.assertEqual(len(cases),2);self.assertEqual(len({key(c) for c in cases}),2)
  self.assertTrue(all(c['declared_identity']=='S.C' for c in cases))
 def test_no_runtime_inventory_means_unknown_not_zero(self):
  report=evaluate(self.inv,[])
  self.assertIsNone(report['unported_runtime_cases']);self.assertEqual(report['observed_unported_runtime_cases'],0)
 def test_partial_runtime_list_does_not_define_a_total(self):
  self.runtime['complete']=False
  report=evaluate(self.inv,[],self.runtime)
  self.assertIsNone(report['unported_runtime_cases']);self.assertEqual(report['observed_unported_runtime_cases'],1)
 def test_missing_runtime_family_means_unknown(self):
  del self.runtime['families']['ui']
  self.assertIsNone(evaluate(self.inv,[],self.runtime)['unported_runtime_cases'])
 def test_stale_runtime_count_is_not_current(self):
  self.runtime['commit']='f'*40
  self.assertIsNone(evaluate(self.inv,[],self.runtime)['unported_runtime_cases'])
 def test_complete_runtime_universe_has_an_exact_count(self):
  report=evaluate(self.inv,[],self.runtime)
  self.assertEqual(report['unported_runtime_cases'],1)
  self.assertEqual(report['observed_unported_runtime_cases'],1)
 def test_ambiguous_old_inventory_reports_rows_and_keys_separately(self):
  self.inv['cases']*=2
  report=evaluate(self.inv,[])
  self.assertEqual(report['unported_source_declarations'],2)
  self.assertEqual(report['unported_source_candidates'],1)
  self.assertIn('ambiguous_source_identities',report['blockers'])
if __name__=='__main__':unittest.main()
