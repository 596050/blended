"""Synthetic adapter checks, never Blender feature parity evidence."""
import base64
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from tools import font_image_oracle as oracle
from tools import probe_font_image_oracle as runner
from tools import unittest_cohort as cohort


PNG = b"\x89PNG\r\n\x1a\nsynthetic-image-content"
SOURCE = '''
import contextlib, os, pathlib, tempfile, unittest
IDIFF_BIN = ""
OUTPUT_DIR = ""
class Original(unittest.TestCase):
    def _compare_image(self, name, kind, idiff_fail, idiff_fail_percent):
        name_full = name
        ref_path = str(pathlib.Path(__file__).parents[1] / "files/blenfont/buffer_renders" / (name + ".png"))
        out_path = os.path.join(OUTPUT_DIR, "{:s}_{:s}_test.png".format(name_full, kind))
        pathlib.Path(out_path).write_bytes(pathlib.Path(ref_path).read_bytes())
        self.assertTrue(IDIFF_BIN, "idiff not found, set IDIFF_BIN or install OpenImageIO")
    def test_render(self):
        self._compare_image("synthetic", "buffer", 0.004, 0.0)
if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as OUTPUT_DIR:
        unittest.main(argv=[__file__], exit=False)
'''
COMPARISON_SOURCE = '''
class Original:
    def _compare_image(self):
        diff_path = os.path.join(OUTPUT_DIR, "{:s}_{:s}_diff.png".format(name_full, kind))
        result = subprocess.run(
            [IDIFF_BIN, "-fail", "{:.4f}".format(idiff_fail),
             "-failpercent", "{:.4f}".format(idiff_fail_percent),
             "-o", diff_path, "-abs", "-scale", "10", ref_path, out_path],
            capture_output=True, text=True)
'''.encode()


class FontImageObserverTests(unittest.TestCase):
    def test_capture_keeps_original_failure_and_precedes_temporary_cleanup(self):
        source = SOURCE.encode()
        fixture = {"relative_path": "blenfont/buffer_renders/synthetic.png",
                   "upstream_path": "tests/files/blenfont/buffer_renders/synthetic.png",
                   "bytes": len(PNG), "sha256": hashlib.sha256(PNG).hexdigest()}
        row = {"upstream_path": "tests/python/synthetic.py", "sha256": hashlib.sha256(source).hexdigest(),
               "bytes": len(source), "fixture_files": [fixture],
               "_fixture_payloads": [{**fixture, "source_b64": base64.b64encode(PNG).decode()}],
               "driver_execution": {"blender_args": [], "script_args": [], "host_tools": []}}
        fake_bpy = types.SimpleNamespace(app=types.SimpleNamespace(
            version=(5, 2, 0), version_string="5.2.0", build_hash=cohort.UPSTREAM_SHA.encode(),
            build_branch=b"test", binary_path="/synthetic", background=True))
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            code = oracle.instrument_payload(cohort.python_payload([(row, source)], "RESULT:", directory))
            with patch.dict(sys.modules, {"bpy": fake_bpy}), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                exec(code, {})
        result = json.loads(next(line[7:] for line in output.getvalue().splitlines() if line.startswith("RESULT:")))
        self.assertEqual(result["suites"][0]["failures"], 1)
        self.assertEqual(result["suites"][0]["outcomes"][0]["status"], "failed")
        capture = result["font_image_capture"]
        self.assertEqual(capture["errors"], [])
        self.assertEqual(len(capture["images"]), 1)
        record = capture["images"][0]
        self.assertFalse(Path(record["browser_output_path"]).exists())
        self.assertEqual(oracle.decode_image(record), PNG)
        self.assertEqual(record["idiff_fail_hex"], float(0.004).hex())
        self.assertEqual(record["reference"]["sha256"], fixture["sha256"])

    def test_instrumentation_rejects_incompatible_or_repeated_hook(self):
        with self.assertRaisesRegex(ValueError, "observer hook"):
            oracle.instrument_payload("unrelated runner")
        with self.assertRaisesRegex(ValueError, "observer hook"):
            oracle.instrument_payload(oracle.RESULT_ANCHOR * 2 + oracle.FAILURE_ANCHOR)

    def test_transported_image_rejects_changed_bytes_and_path_escape(self):
        record = {"filename": "synthetic_buffer_test.png", "name_full": "synthetic", "kind": "buffer", "bytes": len(PNG),
                  "sha256": hashlib.sha256(PNG).hexdigest(), "data_b64": base64.b64encode(PNG).decode()}
        self.assertEqual(oracle.decode_image(record), PNG)
        with self.assertRaisesRegex(ValueError, "checksum"):
            oracle.decode_image({**record, "sha256": "0" * 64})
        with self.assertRaisesRegex(ValueError, "filename"):
            oracle.decode_image({**record, "filename": "../../escaped.png"})
        with self.assertRaisesRegex(ValueError, "bound"):
            oracle.decode_image({**record, "bytes": oracle.MAX_IMAGE_BYTES + 1})
        with self.assertRaisesRegex(ValueError, "filename"):
            oracle.decode_image({**record, "name_full": "../../escaped"})
        with self.assertRaisesRegex(ValueError, "filename"):
            oracle.decode_image({**record, "kind": "../../escaped"})

    def test_command_expression_retains_original_argument_order_and_precision(self):
        expression = oracle.comparator_expression(COMPARISON_SOURCE)
        command = oracle.original_command(expression, {
            "name_full": "synthetic", "kind": "buffer", "filename": "synthetic_buffer_test.png", "idiff_fail": 0.012345,
            "idiff_fail_percent": 1.2, "reference_path": "/refs/ref.png", "output_path": "/out/image.png",
        }, "/tools/idiff", "/diffs")
        self.assertEqual(command, ["/tools/idiff", "-fail", "0.0123", "-failpercent", "1.2000",
                                   "-o", "/diffs/synthetic_buffer_diff.png", "-abs", "-scale", "10",
                                   "/refs/ref.png", "/out/image.png"])
        with self.assertRaisesRegex(ValueError, "filename"):
            oracle.original_command(expression, {"name_full": "../../escaped", "kind": "buffer",
                                    "filename": "synthetic_buffer_test.png"}, "/tools/idiff", "/diffs")


class HostComparatorTests(unittest.TestCase):
    def exercise(self, returncode=None, *, timeout=False):
        reference = {"upstream_path": "tests/files/blenfont/buffer_renders/synthetic.png",
                     "relative_path": "blenfont/buffer_renders/synthetic.png",
                     "sha256": hashlib.sha256(PNG).hexdigest(), "bytes": len(PNG)}
        image = {"case_id": "__main__.Original.test_render", "source_sha256": oracle.SOURCE_SHA256,
                 "filename": "synthetic_buffer_test.png", "name_full": "synthetic", "kind": "buffer",
                 "sha256": hashlib.sha256(PNG).hexdigest(), "bytes": len(PNG),
                 "data_b64": base64.b64encode(PNG).decode(), "reference": reference,
                 "idiff_fail": 0.004, "idiff_fail_hex": (0.004).hex(),
                 "idiff_fail_percent": 0.0, "idiff_fail_percent_hex": (0.0).hex()}
        ids = ["Original.test_render", *sorted(runner.NON_IMAGE_CASES)]
        suite = {"case_ids": ids, "fixture_files": [reference]}
        events = [{"id": image["case_id"], "kind": "test", "status": "failed",
                   "detail": "idiff not found, set IDIFF_BIN or install OpenImageIO"}]
        events += [{"id": "__main__." + identity, "kind": "test", "status": "passed"}
                   for identity in sorted(runner.NON_IMAGE_CASES)]
        qualification = {"status": "failed", "selected_suites_passed": False, "execution": {
            "font_image_capture": {"schema": 1, "original_failures_preserved": True,
                                   "images": [image], "total_bytes": len(PNG), "errors": []},
            "suites": [{"discovered_ids": ["__main__." + identity for identity in ids], "testsRun": 3,
                        "failures": 1, "errors": 0, "outcomes": events}]}}
        report = {"images": [], "status": "blocked"}
        behavior = {"side_effect": subprocess.TimeoutExpired("synthetic", 30, output=b"partial-out", stderr=b"partial-error")} if timeout else {
            "return_value": subprocess.CompletedProcess([], returncode, stdout="original idiff output", stderr="")}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "browser/fixtures" / reference["relative_path"]
            path.parent.mkdir(parents=True)
            path.write_bytes(PNG)
            with patch.object(runner.subprocess, "run", **behavior) as process:
                runner.compare_captured_images(report, {"suites": [suite]}, qualification, root, "/tools/idiff",
                                               oracle.comparator_expression(COMPARISON_SOURCE))
                self.assertEqual(process.call_count, 1)
            self.assertEqual((root / report["images"][0]["image"]["path"]).read_bytes(), PNG)
            self.assertEqual(qualification["status"], "failed")
            self.assertFalse(qualification["selected_suites_passed"])
            self.assertEqual(report["images"][0]["original_browser_test_status"], "failed")
        return report

    def test_original_warning_returncode_one_remains_accepted(self):
        report = self.exercise(1)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["counts"]["host_idiff_passed"], 1)
        self.assertEqual(report["images"][0]["process"]["returncode"], 1)

    def test_returncode_two_is_image_mismatch_without_browser_status_rewrite(self):
        report = self.exercise(2)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["counts"]["host_idiff_image_mismatch"], 1)
        self.assertEqual(report["images"][0]["status"], "image_mismatch")

    def test_timeout_retains_partial_output_and_never_reports_image_parity(self):
        report = self.exercise(timeout=True)
        process = report["images"][0]["process"]
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["counts"]["host_idiff_errors"], 1)
        self.assertTrue(process["timed_out"])
        self.assertIsNone(process["returncode"])
        self.assertEqual(process["stdout"]["sha256"], hashlib.sha256(b"partial-out").hexdigest())


if __name__ == "__main__":
    unittest.main()
