"""Regression tests for the recorder, not additional upstream geometry cases."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from assertion_fidelity import compare
class FatalAssertionContractTests(unittest.TestCase):
 def setUp(self):
  self.expected=[{'id':'geometry.Fatal','expected_runtime_assertions':1}]
  self.trace=[{'case':'geometry.Fatal','kind':'CASE_BEGIN','passed':True,'values':[]},{'case':'geometry.Fatal','kind':'ASSERT_TRUE','passed':True,'values':['b:1']},{'case':'geometry.Fatal','kind':'CASE_END','passed':True,'values':[]}]
 def test_matching_fatal_assertion_is_checked(self):
  report=compare(self.trace,copy.deepcopy(self.trace),self.expected,require_boundaries=True)
  self.assertEqual(report['assertions_compared'],1)
 def test_nonfatal_substitution_is_rejected(self):
  port=copy.deepcopy(self.trace);port[1]['kind']='TRUE'
  with self.assertRaises(ValueError):compare(self.trace,port,self.expected,require_boundaries=True)
 def test_failed_fatal_is_not_a_passing_test(self):
  port=copy.deepcopy(self.trace);port[1]['passed']=False;port[1]['values']=['b:0'];port[-1]['passed']=False
  with self.assertRaises(ValueError):compare(self.trace,port,self.expected,require_boundaries=True)
 def test_post_fatal_assertion_cannot_be_hidden(self):
  port=copy.deepcopy(self.trace);port.insert(-1,copy.deepcopy(port[1]))
  with self.assertRaises(ValueError):compare(self.trace,port,self.expected,require_boundaries=True)
if __name__=='__main__':unittest.main()
