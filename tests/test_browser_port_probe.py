"""Probe infrastructure tests; synthetic tests are not Blender feature evidence."""
import contextlib
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


class BrowserPortProbeTests(unittest.TestCase):
    def run_payload(self, source, expected_hash=None):
        data = source.encode()
        row = {"upstream_path": "tests/python/synthetic.py",
               "sha256": expected_hash or hashlib.sha256(data).hexdigest()}
        fake_bpy = types.SimpleNamespace(app=types.SimpleNamespace(
            version=(5, 2, 0), version_string="5.2.0", build_hash=probe.UPSTREAM_SHA.encode(),
            build_branch=b"test", binary_path="/synthetic"))
        output = io.StringIO()
        with patch.dict(sys.modules, {"bpy": fake_bpy}), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            exec(probe.python_payload([(row, data)], "RESULT:"), {})
        payload = next(line.removeprefix("RESULT:") for line in output.getvalue().splitlines() if line.startswith("RESULT:"))
        return json.loads(payload), [row]

    def test_original_failures_survive_adapter_and_subtests_are_distinct(self):
        result, expected = self.run_payload('''
import unittest
class Example(unittest.TestCase):
    def test_failure(self):
        self.assertEqual(1, 2, "deliberate original assertion")
    def test_subtests(self):
        for value in [1, 2]:
            with self.subTest(value=value):
                self.assertGreater(value, 0)
''')
        row = result["suites"][0]
        self.assertEqual(row["testsRun"], 2)
        self.assertEqual(row["failures"], 1)
        self.assertEqual(sum(r.get("kind") == "subtest" for r in row["outcomes"]), 2)
        self.assertEqual(sum(r.get("kind") == "test" for r in row["outcomes"]), 2)
        with self.assertRaises(RuntimeError): probe.validate_suite_execution(result, expected)

    def test_zero_or_skipped_tests_cannot_qualify(self):
        for source in ("import unittest\n", '''
import unittest
class Example(unittest.TestCase):
    @unittest.skip("unsupported")
    def test_skipped(self):
        pass
'''):
            with self.subTest(source=source):
                result, expected = self.run_payload(source)
                with self.assertRaises(RuntimeError): probe.validate_suite_execution(result, expected)

    def test_unknown_or_wrong_build_identity_is_blocked(self):
        for build_hash in ("", "unknown", "none", "a" * 40):
            with self.subTest(build_hash=build_hash):
                with self.assertRaises(probe.Blocked):
                    probe.validate_build_identity({"version": [5, 2, 0], "build_hash": build_hash})
        for build_hash in (probe.UPSTREAM_SHA, probe.UPSTREAM_SHA[:12]):
            probe.validate_build_identity({"version": [5, 2, 0], "build_hash": build_hash})
        with self.assertRaises(probe.Blocked):
            probe.validate_build_identity({"version": [5, 3, 0], "build_hash": probe.UPSTREAM_SHA})

    def test_changed_source_or_asset_is_refused(self):
        result, _ = self.run_payload("raise AssertionError('must never execute')", expected_hash="0" * 64)
        self.assertIn("suite changed in transport", result["exception"])
        self.assertFalse(result["suites"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "corrupt.tar.gz"
            asset.write_bytes(b"not the pinned release")
            args = types.SimpleNamespace(output=root, asset=asset)
            report = {"artifact": {}}
            with self.assertRaisesRegex(probe.Blocked, "does not match the pinned release"):
                probe.probe(args, report)

    def test_software_profile_uses_observed_adapter(self):
        for adapter in ({"isFallbackAdapter": True}, {"description": "SwiftShader Device (Subzero)"},
                        {"description": "llvmpipe"}):
            with self.subTest(adapter=adapter):
                self.assertEqual(probe.adapter_profile(adapter), "chromium-software-webgpu")
        self.assertEqual(probe.adapter_profile({"vendor": "nvidia", "isFallbackAdapter": False}),
                         "chromium-webgpu-unverified")
        self.assertEqual(probe.adapter_profile(None), "chromium-webgpu-unavailable")


if __name__ == "__main__":
    unittest.main()
