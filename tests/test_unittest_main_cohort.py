"""Contract tests for original unittest entrypoints and native frozen discovery.

Synthetic fixtures here qualify the adapter only, never Blender functionality.
"""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from tools import probe_browser_port as probe
from tools import unittest_cohort as cohort


def proposal(source):
    data = source.encode()
    return {
        "schema": 2, "stage": "native-discovery", "cohort_id": "synthetic-original-main",
        "suite_kind": "unittest-main",
        "upstream": {"repository": "blender/blender", "commit": probe.UPSTREAM_SHA},
        "execution": {
            "entrypoint": "original __main__", "process_isolation": "one-upstream-script",
            "background": True, "blender_args": list(cohort.CTEST_BLENDER_ARGS), "script_args": [],
            "ctest_name": "synthetic", "cmake_sources": copy.deepcopy(cohort.CMAKE_SOURCES),
            "registration": "add_blender_test(\n  synthetic\n  --python ${CMAKE_CURRENT_LIST_DIR}/synthetic.py\n)",
        },
        "suites": [{"upstream_path": "tests/python/synthetic.py", "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data), "support_files": [], "fixture_files": []}],
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return probe.digest(path)


def execute(source, *, script_args=(), support=()):
    value = proposal(source)
    value["execution"]["script_args"] = list(script_args)
    row = {**value["suites"][0], "driver": "unittest-main", "required_background": True,
           "driver_execution": value["execution"], "_support_payloads": list(support)}
    fake_bpy = types.SimpleNamespace(app=types.SimpleNamespace(
        version=(5, 2, 0), version_string="5.2.0", build_hash=probe.UPSTREAM_SHA.encode(),
        build_branch=b"test", binary_path="/synthetic", background=True))
    output, caught_exit = io.StringIO(), None
    with tempfile.TemporaryDirectory() as directory:
        with patch.dict(sys.modules, {"bpy": fake_bpy}), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            try:
                exec(cohort.python_payload([(row, source.encode())], "ORIGINAL_RESULT:", directory), {})
            except SystemExit as error:
                caught_exit = error.code
    text = next(line[len("ORIGINAL_RESULT:"):] for line in output.getvalue().splitlines()
                if line.startswith("ORIGINAL_RESULT:"))
    return json.loads(text), row, caught_exit


def native_report(value, result, source):
    return {
        "profile": "native-reference", "official_release_checksum_verified": True,
        "upstream": value["upstream"], "cohort": {"manifest_sha256": "1" * 64},
        "artifact": {"observed_sha256": cohort.NATIVE_ARCHIVE_SHA256, "observed_bytes": cohort.NATIVE_ARCHIVE_BYTES},
        "process": {"returncode": 0, "flags": value["execution"]["blender_args"]},
        "execution": result, "suite_sources": [source],
        "transport": {"result_markers": 1, "trailing_runtime_text": None},
    }


MAIN_SOURCE = '''
import unittest
class Original(unittest.TestCase):
    def test_main_setup(self):
        self.assertEqual(ORIGINAL_MAIN_VALUE, 42)
if __name__ == "__main__":
    ORIGINAL_MAIN_VALUE = 42
    unittest.main(argv=[__file__])
'''


class OriginalEntrypointTests(unittest.TestCase):
    def test_nonassertion_subtest_errors_keep_original_error_category(self):
        result, _, exit_code = execute('''
import unittest
class Original(unittest.TestCase):
    def test_subtests(self):
        with self.subTest(kind="assertion"):
            self.assertTrue(False)
        with self.subTest(kind="exception"):
            raise ValueError("original error")
if __name__ == "__main__":
    unittest.main(argv=[__file__])
''')
        row = result["suites"][0]
        self.assertEqual(exit_code, 1)
        self.assertEqual((row["failures"], row["errors"]), (1, 1))
        self.assertEqual([event["status"] for event in row["outcomes"]], ["failed", "error"])

    def test_original_main_setup_and_process_exit_are_preserved(self):
        result, row, exit_code = execute(MAIN_SOURCE)
        self.assertEqual(exit_code, 0)
        self.assertIsNone(result["exception"])
        self.assertEqual(result["suites"][0]["discovered_ids"], ["__main__.Original.test_main_setup"])
        self.assertTrue(result["execution_context"]["background"])
        self.assertEqual(result["driver_observation"]["runner_invocations"], 1)
        probe.validate_suite_execution(result, [row])

    def test_load_tests_controls_actual_discovery_instead_of_method_name_regex(self):
        result, _, _ = execute('''
import unittest
class Original(unittest.TestCase):
    def test_selected(self):
        self.assertTrue(True)
    def test_not_in_original_suite(self):
        self.fail("the original load_tests excludes this method")
def load_tests(loader, tests, pattern):
    return unittest.TestSuite([Original("test_selected")])
if __name__ == "__main__":
    unittest.main(argv=[__file__])
''')
        self.assertEqual(result["suites"][0]["discovered_ids"], ["__main__.Original.test_selected"])
        self.assertEqual(result["suites"][0]["failures"], 0)

    def test_original_skip_expected_failure_and_unexpected_success_are_distinct(self):
        result, row, exit_code = execute('''
import unittest
class Original(unittest.TestCase):
    @unittest.skip("upstream conditional skip")
    def test_skip(self):
        self.fail()
    @unittest.expectedFailure
    def test_expected_failure(self):
        self.assertEqual(1, 2)
    @unittest.expectedFailure
    def test_unexpected_success(self):
        self.assertTrue(True)
if __name__ == "__main__":
    unittest.main(argv=[__file__])
''')
        self.assertEqual(exit_code, 1)
        observed = result["suites"][0]
        self.assertEqual(observed["testsRun"], 3)
        self.assertEqual({r["status"] for r in observed["outcomes"]},
                         {"skipped", "expected_failure", "unexpected_success"})
        self.assertFalse(probe.summarize_execution(result, [row])["selected_suites_passed"])

    def test_original_cli_and_support_module_bytes_are_preserved(self):
        import base64
        helper = b"VALUE = 42\n"
        support = {"upstream_path": "tests/python/original_helper.py", "bytes": len(helper),
                   "sha256": hashlib.sha256(helper).hexdigest(), "source_b64": base64.b64encode(helper).decode()}
        result, _, _ = execute('''
import sys, unittest
from original_helper import VALUE
class Original(unittest.TestCase):
    def test_cli(self):
        self.assertEqual(PARSED, "original-value")
        self.assertEqual(VALUE, 42)
if __name__ == "__main__":
    PARSED = sys.argv[sys.argv.index("--") + 1]
    unittest.main(argv=[__file__])
''', script_args=["original-value"], support=[support])
        self.assertEqual(result["suites"][0]["failures"], 0)
        self.assertIsNone(result["exception"])
        self.assertEqual(result["driver_observation"]["support_files"][0]["sha256"], support["sha256"])


class FrozenManifestTests(unittest.TestCase):
    def setUp(self):
        # These are deliberately synthetic adapter fixtures. Declaration
        # authenticity has separate tests against the complete pinned CMake.
        self.registration_check = patch.object(cohort, "validate_original_invocation", return_value={})
        self.registration_check.start()
        self.addCleanup(self.registration_check.stop)

    def test_discovery_input_cannot_run_as_a_frozen_browser_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proposal.json"
            digest = write_json(path, proposal(MAIN_SOURCE))
            with self.assertRaisesRegex(cohort.ManifestError, "native discovery"):
                cohort.load_manifest(path, digest)
            catalog = cohort.load_manifest(path, digest, allow_discovery=True)
            self.assertIsNone(catalog["expected_cases"])
            with self.assertRaisesRegex(cohort.ManifestError, "checksum"):
                cohort.load_manifest(path, "0" * 64, allow_discovery=True)

    def test_native_receipt_freezes_exact_ids_and_omission_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = proposal(MAIN_SOURCE)
            proposal_path, receipt_path, frozen_path = root / "proposal.json", root / "native.json", root / "frozen.json"
            proposal_digest = write_json(proposal_path, value)
            result, row, _ = execute(MAIN_SOURCE)
            receipt = native_report(value, result, row)
            receipt["cohort"]["manifest_sha256"] = proposal_digest
            write_json(receipt_path, receipt)
            cohort.freeze_manifest(proposal_path, proposal_digest, receipt_path, frozen_path)
            catalog = cohort.load_manifest(frozen_path, probe.digest(frozen_path))
            self.assertEqual(catalog["suites"][0]["case_ids"], ["Original.test_main_setup"])
            self.assertEqual(catalog["expected_cases"], 1)
            frozen = json.loads(frozen_path.read_text())
            frozen["suites"][0]["case_ids"] = ["Original.invented_case"]
            frozen["suites"][0]["mandatory_case_ids"] = ["Original.invented_case"]
            write_json(frozen_path, frozen)
            with self.assertRaisesRegex(cohort.ManifestError, "native.*inventory"):
                cohort.load_manifest(frozen_path, probe.digest(frozen_path))

    def test_changed_native_receipt_and_wrong_context_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = proposal(MAIN_SOURCE)
            proposal_path, receipt_path, frozen_path = root / "proposal.json", root / "native.json", root / "frozen.json"
            proposal_digest = write_json(proposal_path, value)
            result, row, _ = execute(MAIN_SOURCE)
            receipt = native_report(value, result, row)
            receipt["cohort"]["manifest_sha256"] = proposal_digest
            receipt["execution"]["execution_context"]["background"] = False
            write_json(receipt_path, receipt)
            with self.assertRaisesRegex(cohort.ManifestError, "background"):
                cohort.freeze_manifest(proposal_path, proposal_digest, receipt_path, frozen_path)
            receipt["execution"]["execution_context"]["background"] = True
            write_json(receipt_path, receipt)
            cohort.freeze_manifest(proposal_path, proposal_digest, receipt_path, frozen_path)
            receipt_path.write_text("{}\n")
            with self.assertRaisesRegex(cohort.ManifestError, "native.*checksum"):
                cohort.load_manifest(frozen_path, probe.digest(frozen_path))

    def test_new_contract_requires_one_script_and_complete_ctest_flags(self):
        for change in (lambda v: v["suites"].append(copy.deepcopy(v["suites"][0])),
                       lambda v: v["execution"]["blender_args"].remove("--debug-memory"),
                       lambda v: v["execution"].update(script_args=["--keyword", "only_this_case"]),
                       lambda v: v["execution"].update(background=False)):
            with tempfile.TemporaryDirectory() as directory:
                value = proposal(MAIN_SOURCE)
                change(value)
                path = Path(directory) / "proposal.json"
                digest = write_json(path, value)
                with self.assertRaises(cohort.ManifestError):
                    cohort.load_manifest(path, digest, allow_discovery=True)


if __name__ == "__main__":
    unittest.main()
