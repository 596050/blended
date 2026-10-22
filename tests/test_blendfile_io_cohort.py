"""Custom-driver transport checks, not Blender feature-parity evidence."""
import base64
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import textwrap
import types
import unittest
from unittest.mock import patch

from tools import blender_io_cohort as adapter
from tools import probe_browser_port as shared


HELPER = b'''import unittest
class TestHelper(unittest.TestCase):
    def __init__(self, args):
        super().__init__()
        self.args = args
    def run_all_tests(self):
        for inst_attr_id in dir(self):
            if not inst_attr_id.startswith("test_"):
                continue
            inst_attr = getattr(self, inst_attr_id)
            if not callable(inst_attr):
                continue
            self.setUp()
            try:
                inst_attr()
            finally:
                self.tearDown()
'''


def original_script(methods):
    return ('''import argparse
from pathlib import Path
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from bl_blendfile_utils import TestHelper

class OriginalCase(TestHelper):
''' + textwrap.indent(textwrap.dedent(methods), "    ") + '''
TESTS = (OriginalCase,)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    Path(args.output_dir, "original-entrypoint.txt").write_text(__name__)
    for Test in TESTS:
        Test(args).run_all_tests()

if __name__ == "__main__":
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    main()
''').encode()


@unittest.skipUnless(hasattr(sys, "monitoring"), "requires CPython 3.12+ monitoring")
class BlendFileIOAdapterTests(unittest.TestCase):
    def execute(self, methods, case_names=("test_a", "test_b"), build_hash=shared.UPSTREAM_SHA,
                corrupt_helper=False, background=True, transfer_ack=None):
        source = original_script(methods)
        support = {"upstream_path": "tests/python/bl_blendfile_utils.py",
                   "sha256": hashlib.sha256(HELPER).hexdigest(), "bytes": len(HELPER)}
        payload_support = {**support, "source_b64": base64.b64encode(HELPER).decode()}
        if corrupt_helper:
            payload_support["source_b64"] = base64.b64encode(HELPER + b"\nraise AssertionError('changed source executed')\n").decode()
        row = {"upstream_path": "tests/python/bl_blendfile_io.py",
               "sha256": hashlib.sha256(source).hexdigest(), "bytes": len(source),
               "case_ids": ["OriginalCase." + value for value in case_names],
               "expected_cases": len(case_names), "support_files": [support], "required_background": True,
               "_support_payloads": [payload_support]}
        fake_bpy = types.SimpleNamespace(app=types.SimpleNamespace(
            version=(5, 2, 0), version_string="5.2.0", build_hash=build_hash.encode(),
            build_branch=b"synthetic", binary_path="/synthetic", background=background))
        class CapturedOutput(io.StringIO):
            def flush(self):
                if transfer_ack is None:
                    return
                lines = [line[len("IO_RESULT:"):] for line in self.getvalue().splitlines()
                         if line.startswith("IO_RESULT:")]
                if not lines:
                    return
                emitted = json.loads(lines[-1])
                handshake = emitted["output_transfer_handshake"]
                payload = {"protocol": handshake["protocol"], "token": handshake["token"],
                           "status": "verified", "files": emitted["generated_files"]["files"]}
                if transfer_ack == "changed":
                    payload["files"] = []
                elif transfer_ack == "failed":
                    payload["status"] = "failed"
                Path(handshake["ack_path"]).write_text(json.dumps(payload))
        stdout = CapturedOutput()
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory) / "isolated-io"
            original_argv, original_path = sys.argv[:], sys.path[:]
            with patch.dict(sys.modules, {"bpy": fake_bpy}), contextlib.redirect_stdout(stdout):
                exec(adapter.python_payload([(row, source)], "IO_RESULT:", output_root,
                                            wait_for_output_transfer=transfer_ack is not None), {})
            self.assertEqual(sys.argv, original_argv)
            self.assertEqual(sys.path, original_path)
            found = [line[len("IO_RESULT:"):] for line in stdout.getvalue().splitlines()
                     if line.startswith("IO_RESULT:")]
            self.assertEqual(len(found), 1)
            result = json.loads(found[0])
            if not corrupt_helper:
                self.assertEqual((output_root / "sources/bl_blendfile_io.py").read_bytes(), source)
                self.assertEqual((output_root / "sources/bl_blendfile_utils.py").read_bytes(), HELPER)
                self.assertTrue(result["io_observation"]["source_bytes_preserved"])
            output_files = {path.name: path.read_bytes() for path in (output_root / "files").glob("*")
                            if path.is_file()}
            for file in result["generated_files"]["files"]:
                self.assertEqual(file["bytes"], len(output_files[file["path"]]))
                self.assertEqual(file["sha256"], hashlib.sha256(output_files[file["path"]]).hexdigest())
            return result, row, output_files

    def test_original_main_and_four_complete_lifecycles_pass(self):
        methods = "\n".join(
            "def test_" + value + "(self):\n    Path(self.args.output_dir, '" + value + ".txt').write_text('original')\n"
            for value in ("a", "b", "c", "d"))
        result, row, files = self.execute(methods, ("test_a", "test_b", "test_c", "test_d"))
        self.assertIsNone(result["exception"])
        self.assertEqual(files["original-entrypoint.txt"], b"__main__")
        self.assertEqual(set(files), {"original-entrypoint.txt", "a.txt", "b.txt", "c.txt", "d.txt"})
        self.assertEqual(result["suites"][0]["testsRun"], 4)
        self.assertTrue(result["io_observation"]["driver_completed_as_expected"])
        self.assertIs(result["execution_context"]["background"], True)

        self.assertTrue(result["io_observation"]["helper_import_verified"])
        for case in result["io_observation"]["cases"]:
            self.assertEqual(case["status"], "passed")
            self.assertEqual([(event["phase"], event["event"]) for event in case["events"]],
                             [(phase, event) for phase in ("setup", "body", "teardown")
                              for event in ("start", "return")])
        shared.validate_suite_execution(result, [row])

    def test_wrong_execution_mode_retains_outcomes_but_fails_qualification(self):
        result, row, _ = self.execute("def test_a(self):\n    self.assertTrue(True)\n", ("test_a",), background=False)
        self.assertEqual(result["suites"][0]["outcomes"][0]["status"], "passed")
        assessment = shared.summarize_execution(result, [row])
        self.assertEqual(assessment["status"], "failed")
        self.assertFalse(assessment["selected_suites_passed"])
        self.assertEqual(assessment["blockers"][0]["scope"], "execution_context")

    def test_post_test_transfer_ack_must_match_the_actual_file_inventory(self):
        methods = "def test_a(self):\n    self.assertTrue(True)\n"
        result, row, _ = self.execute(methods, ("test_a",), transfer_ack="verified")
        self.assertIsNone(result["exception"])
        self.assertTrue(result["output_transfer_handshake"]["required"])
        self.assertEqual(result["output_transfer_handshake"]["timeout_seconds"], 60)
        decoded, suffix = shared.decode_qualification_event("IO_RESULT:" + json.dumps(result), "IO_RESULT:")
        self.assertEqual(decoded, result)
        self.assertEqual(suffix, "")
        self.assertEqual(shared.summarize_execution(result, [row])["status"], "passed")
        for bad in ("changed", "failed"):
            with self.subTest(bad=bad), self.assertRaisesRegex(RuntimeError, "output transfer"):
                self.execute(methods, ("test_a",), transfer_ack=bad)

    def test_original_body_assertion_aborts_later_methods_and_runs_teardown(self):
        result, row, files = self.execute('''
            def tearDown(self):
                Path(self.args.output_dir, "teardown.txt").write_text("original")
            def test_a(self):
                self.assertEqual(1, 2, "original failing assertion")
            def test_b(self):
                Path(self.args.output_dir, "must-not-run.txt").write_text("bad")
        ''')
        self.assertIn("original failing assertion", result["exception"])
        self.assertNotIn("must-not-run.txt", files)
        self.assertIn("teardown.txt", files)
        self.assertEqual(result["suites"][0]["testsRun"], 1)
        self.assertEqual(result["suites"][0]["failures"], 1)
        self.assertEqual(result["suites"][0]["outcomes"][0]["status"], "failed")
        assessment = shared.summarize_execution(result, [row])
        self.assertEqual(assessment["status"], "failed")
        self.assertEqual(assessment["summary"]["required_case_inventory"]["missing_cases"], 1)

    def test_setup_error_never_calls_body_or_teardown(self):
        result, row, files = self.execute('''
            def setUp(self):
                raise RuntimeError("original setup failure")
            def tearDown(self):
                Path(self.args.output_dir, "must-not-teardown.txt").write_text("bad")
            def test_a(self):
                Path(self.args.output_dir, "must-not-run.txt").write_text("bad")
            def test_b(self):
                self.fail("later method must not execute")
        ''')
        self.assertIn("original setup failure", result["exception"])
        self.assertNotIn("must-not-run.txt", files)
        self.assertNotIn("must-not-teardown.txt", files)
        self.assertEqual(result["suites"][0]["errors"], 1)
        self.assertEqual([(event["phase"], event["event"])
                          for event in result["io_observation"]["cases"][0]["events"]],
                         [("setup", "start"), ("setup", "unwind")])
        self.assertEqual(shared.summarize_execution(result, [row])["status"], "failed")

    def test_teardown_error_invalidates_a_normally_returning_body(self):
        result, row, files = self.execute('''
            def tearDown(self):
                raise RuntimeError("original teardown failure")
            def test_a(self):
                Path(self.args.output_dir, "body.txt").write_text("original")
            def test_b(self):
                Path(self.args.output_dir, "must-not-run.txt").write_text("bad")
        ''')
        self.assertIn("original teardown failure", result["exception"])
        self.assertIn("body.txt", files)
        self.assertNotIn("must-not-run.txt", files)
        case = result["io_observation"]["cases"][0]
        self.assertEqual(case["status"], "error")
        self.assertIn({"phase": "body", "event": "return"}, case["events"])
        self.assertEqual(case["events"][-1]["event"], "unwind")
        self.assertEqual(shared.summarize_execution(result, [row])["status"], "failed")

    def test_unknown_engine_identity_is_a_shared_provenance_blocker(self):
        result, row, _ = self.execute('''
            def test_a(self):
                self.assertTrue(True)
            def test_b(self):
                self.assertTrue(True)
        ''', build_hash="Unknown")
        self.assertIsNone(result["exception"])
        self.assertTrue(all(case["status"] == "passed" for case in result["suites"][0]["outcomes"]))
        assessment = shared.summarize_execution(result, [row])
        self.assertEqual(assessment["status"], "blocked")
        self.assertTrue(assessment["selected_suites_passed"])

    def test_changed_helper_is_rejected_before_original_code_executes(self):
        result, row, files = self.execute('''
            def test_a(self):
                self.fail("must not execute")
            def test_b(self):
                self.fail("must not execute")
        ''', corrupt_helper=True)
        self.assertIn("source changed in transport", result["exception"])
        self.assertFalse(files)
        self.assertFalse(result["io_observation"]["cases"])
        self.assertEqual(shared.summarize_execution(result, [row])["status"], "failed")


if __name__ == "__main__":
    unittest.main()
