"""Mutation tests for assertion-fidelity accounting, not Blender features."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from assertion_fidelity import compare
class FidelityTests(unittest.TestCase):
 def setUp(self):
  self.expected=[{'id':'suite.case','expected_runtime_assertions':2}]
  self.ref=[{'case':'suite.case','kind':'EQ','passed':True,'values':['i:4','i:4']},{'case':'suite.case','kind':'NEAR','passed':True,'values':['f:3ff0000000000000','f:3ff0000000000000','f:3eb0c6f7a0b5ed8d']}]
  self.port=copy.deepcopy(self.ref)
 def result(self):return compare(self.ref,self.port,self.expected)
 def test_equal(self):self.assertEqual(self.result()['assertions_compared'],2)
 def test_no_full_suite_claim(self):self.assertFalse(self.result()['complete_blender_test_port'])
 def test_missing_case(self):
  self.port=[]
  with self.assertRaises(ValueError):self.result()
 def test_duplicate_assertion(self):
  self.port.append(self.port[0])
  with self.assertRaises(ValueError):self.result()
 def test_removed_assertion(self):
  self.port.pop()
  with self.assertRaises(ValueError):self.result()
 def test_changed_kind(self):
  self.port[0]['kind']='FLOAT_EQ'
  with self.assertRaises(ValueError):self.result()
 def test_changed_expected_value(self):
  self.port[0]['values'][1]='i:5'
  with self.assertRaises(ValueError):self.result()
 def test_changed_actual_value(self):
  self.port[0]['values'][0]='i:5'
  with self.assertRaises(ValueError):self.result()
 def test_loosened_tolerance(self):
  self.port[1]['values'][2]='f:3ff0000000000000'
  with self.assertRaises(ValueError):self.result()
 def test_failure_not_passed(self):
  self.port[0]['passed']=False
  with self.assertRaises(ValueError):self.result()
 def test_reordered_assertions(self):
  self.port.reverse()
  with self.assertRaises(ValueError):self.result()
 def test_wrong_identity(self):
  self.port[0]['case']='suite.other'
  with self.assertRaises(ValueError):self.result()
 def test_truthy_string_not_pass(self):
  self.port[0]['passed']='true'
  with self.assertRaises(ValueError):self.result()
 def test_count_only_stub(self):
  self.port[0]={'case':'suite.case','kind':'EQ','passed':True,'values':['b:1','b:1']}
  with self.assertRaises(ValueError):self.result()
if __name__=='__main__':unittest.main()
