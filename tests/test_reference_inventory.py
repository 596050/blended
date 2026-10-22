"""Parser regression tests, not ported Blender cases."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from reference_inventory import parse_gtest_listing,parse_results,reconcile
class ReferenceInventoryTests(unittest.TestCase):
    def test_regular_listing(self):self.assertEqual(parse_gtest_listing('bounds.\n  Empty\n  Center\n')['case_ids'],['bounds.Empty','bounds.Center'])
    def test_typed_and_parameterised_names_preserved(self):
        data=parse_gtest_listing('Vec/0.  # TypeParam = int\n  Construct\nValues/Fixture.\n  Case/0  # GetParam() = 3\n')
        self.assertEqual(data['case_ids'],['Vec/0.Construct','Values/Fixture.Case/0'])
    def test_disabled_case_is_not_lost(self):
        data=parse_gtest_listing('DISABLED_Feature.\n  Case\nOther.\n  DISABLED_Case\n')
        self.assertEqual(len(data['disabled']),2)
    def test_duplicate_listing_is_error(self):
        with self.assertRaises(ValueError):parse_gtest_listing('A.\n  B\n  B\n')
    def test_case_without_suite_is_error(self):
        with self.assertRaises(ValueError):parse_gtest_listing('  B\n')
    def test_empty_listing_is_error(self):
        with self.assertRaises(ValueError):parse_gtest_listing('')
    def test_successful_xml(self):
        x=parse_results('<testsuites tests="1"><testsuite><testcase classname="A" name="B" status="run" result="completed"/></testsuite></testsuites>')
        self.assertEqual(x,{'A.B':'passed'})
    def test_skipped_and_failed_are_distinct(self):
        x=parse_results('<testsuites tests="2"><testsuite><testcase classname="A" name="B" status="run" result="completed"><failure/></testcase><testcase classname="A" name="C" status="notrun" result="suppressed"/></testsuite></testsuites>')
        self.assertEqual(x,{'A.B':'failed','A.C':'not_run'})
    def test_duplicate_xml_is_error(self):
        with self.assertRaises(ValueError):parse_results('<testsuites tests="2"><testcase classname="A" name="B"/><testcase classname="A" name="B"/></testsuites>')
    def test_xml_count_mismatch_is_error(self):
        with self.assertRaises(ValueError):parse_results('<testsuites tests="2"><testcase classname="A" name="B"/></testsuites>')
    def test_runtime_case_not_in_source_map_is_retained(self):
        r=reconcile(['A.B','A.C'],['A.B'],{'A.B':'passed'},['A.'])
        self.assertFalse(r['selected_families_complete']);self.assertEqual(r['unmapped_selected_cases'],['A.C'])
    def test_failed_reference_is_not_conformance(self):
        r=reconcile(['A.B'],['A.B'],{'A.B':'failed'},['A.']);self.assertFalse(r['selected_reference_tests_passed'])
    def test_partial_scope_never_complete_application(self):
        r=reconcile(['A.B','Z.C'],['A.B'],{'A.B':'passed'},['A.'])
        self.assertTrue(r['selected_families_complete']);self.assertTrue(r['selected_reference_tests_passed']);self.assertFalse(r['complete_blender_runtime_enumeration'])
if __name__=='__main__':unittest.main()
