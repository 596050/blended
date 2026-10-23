"""Frozen source-plan inputs remain usable after checkout relocation."""
from pathlib import Path
import tempfile
import unittest

from tools.run_unittest_browser_matrix import resolve_manifest_record


class MatrixInputTests(unittest.TestCase):
    def test_repository_relative_record_does_not_depend_on_caller_cwd(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "relocated-checkout"
            manifest = repository / "compatibility/candidate-suites/example.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_bytes(b"{}\n")
            record = {"path": "compatibility/candidate-suites/example.json", "bytes": 3}
            self.assertEqual(resolve_manifest_record(record, repository), manifest)

    def test_changed_byte_count_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "byte count"):
                resolve_manifest_record({"path": "manifest.json", "bytes": 4}, temporary)


if __name__ == "__main__":
    unittest.main()
