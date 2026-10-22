"""Protect fixed native case inventories and original-suite invocation boundaries."""
import contextlib
import hashlib
import io
import json
import sys
import types
import unittest
from unittest.mock import patch

from tools import probe_browser_port as probe


def run_payload(source):
    data = source.encode()
    row = {"upstream_path": "tests/python/synthetic.py", "sha256": hashlib.sha256(data).hexdigest()}
    fake_bpy = types.SimpleNamespace(app=types.SimpleNamespace(
        version=(5, 2, 0), version_string="5.2.0", build_hash=probe.UPSTREAM_SHA.encode(),
        build_branch=b"test", binary_path="/synthetic"))
    output = io.StringIO()
    with patch.dict(sys.modules, {"bpy": fake_bpy}), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
        exec(probe.python_payload([(row, data)], "COHORT_RESULT:"), {})
    result = next(line[len("COHORT_RESULT:"):] for line in output.getvalue().splitlines()
                  if line.startswith("COHORT_RESULT:"))
    return json.loads(result), [row]


class CandidateCohortTests(unittest.TestCase):
    def test_upstream_id_property_does_not_break_discovery_or_subtest_recording(self):
        result, expected = run_payload('''
import unittest
class DataCase(unittest.TestCase):
    @property
    def id(self):
        return self._id
    def setUp(self):
        self._id = object()
    def test_data(self):
        for value in (1, 2):
            with self.subTest(value=value):
                self.assertGreater(value, 0)
''')
        self.assertIsNone(result["exception"])
        probe.validate_suite_execution(result, expected)
        events = result["suites"][0]["outcomes"]
        subtests = [item for item in events if item["kind"] == "subtest"]
        self.assertEqual(len(subtests), 2)
        self.assertEqual(len({item["id"] for item in subtests}), 2)
        self.assertTrue(all(item["parent_id"].endswith(".DataCase.test_data") for item in subtests))

    def test_class_setup_errors_remain_visible_without_testcase_id_methods(self):
        result, expected = run_payload('''
import unittest
class BrokenSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raise RuntimeError("original setup failure")
    def test_never_reached(self):
        self.fail("must not execute")
''')
        self.assertIsNone(result["exception"])
        self.assertEqual(result["suites"][0]["errors"], 1)
        self.assertIn("original setup failure", result["suites"][0]["outcomes"][0]["detail"])
        with self.assertRaises(RuntimeError):
            probe.validate_suite_execution(result, expected)

    def test_missing_conditional_cases_cannot_reduce_the_native_denominator(self):
        result, expected = run_payload('''
import unittest
class Feature(unittest.TestCase):
    def test_core(self):
        self.assertTrue(True)
''')
        expected[0]["expected_cases"] = 2
        expected[0]["case_ids"] = ["Feature.test_core", "Feature.test_numpy"]
        assessment = probe.summarize_execution(result, expected)
        self.assertEqual(assessment["status"], "failed")
        self.assertFalse(assessment["selected_suites_passed"])
        inventory = assessment["summary"]["required_case_inventory"]
        self.assertEqual((inventory["expected_cases"], inventory["missing_cases"]), (2, 1))

    def test_data_cohort_keeps_all_48_native_cases_and_default_numeric_scope(self):
        data = probe.load_suite_catalog("data52")
        self.assertEqual(data["expected_cases"], 48)
        self.assertEqual([row["expected_cases"] for row in data["suites"]], [8, 1, 39])
        self.assertEqual(sum(len(row["case_ids"]) for row in data["suites"]), 48)
        numeric = probe.load_suite_catalog("numeric")
        self.assertEqual([row["upstream_path"] for row in numeric["suites"]],
                         ["tests/python/bl_pyapi_mathutils.py", "tests/python/bl_pyapi_bmesh.py"])
        self.assertEqual(numeric["expected_cases"], 192)
        with self.assertRaises(probe.Blocked):
            probe.load_suite_catalog("unknown")


if __name__ == "__main__":
    unittest.main()
