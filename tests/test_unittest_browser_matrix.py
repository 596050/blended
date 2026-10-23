"""Frozen source-plan inputs remain usable after checkout relocation."""
from pathlib import Path
import tempfile
import unittest

from tools.run_unittest_browser_matrix import overlay_inputs, resolve_manifest_record


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

    def test_package_overlay_requires_its_original_archive(self):
        self.assertIsNone(overlay_inputs(None, None))
        for receipt, archive in ((Path("receipt.json"), None), (None, Path("base.tgz"))):
            with self.subTest(receipt=receipt, archive=archive):
                with self.assertRaisesRegex(ValueError, "both"):
                    overlay_inputs(receipt, archive)

    def test_package_overlay_rejects_missing_or_symlinked_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt, archive = root / "receipt.json", root / "base.tgz"
            receipt.write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "regular files"):
                overlay_inputs(receipt, archive)
            archive.write_bytes(b"test-only archive")
            self.assertEqual(overlay_inputs(receipt, archive), {"receipt": receipt, "base_asset": archive})
            alias = root / "alias.tgz"
            alias.symlink_to(archive)
            with self.assertRaisesRegex(ValueError, "regular files"):
                overlay_inputs(receipt, alias)


if __name__ == "__main__":
    unittest.main()
