#!/usr/bin/env python3
"""Application regressions using the real pinned port preimages and reviewed diff."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[1]
SOURCE = REPO / "compatibility/evidence/browser-codecs-5.2-2026-10-23/sources/port"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CodecPatchApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="blended-codec-patch-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / "package"
        shutil.copytree(PACKAGE, self.package, ignore=shutil.ignore_patterns("__pycache__"))
        self.manifest_path = self.package / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text())
        self.port = self.root / "port"
        self.port.mkdir()
        for row in self.manifest["files"]:
            if row["before_sha256"] is not None:
                source = SOURCE / row["path"]
                self.assertEqual(sha(source), row["before_sha256"])
                target = self.port / row["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        self.sequence = 0

    def execute(self, expected_sha=None):
        self.sequence += 1
        receipt = self.root / ("receipt-" + str(self.sequence) + ".json")
        result = subprocess.run([sys.executable, str(self.package / "apply.py"),
                                 "--port-root", str(self.port), "--receipt", str(receipt),
                                 "--expected-manifest-sha256", expected_sha or sha(self.manifest_path)],
                                capture_output=True, text=True, timeout=30)
        return result, json.loads(receipt.read_text()) if receipt.exists() else None

    def assert_no_new_files(self):
        for row in self.manifest["files"]:
            if row["before_sha256"] is None:
                self.assertFalse((self.port / row["path"]).exists(), row["path"])

    def test_real_patch_applies_and_exact_reapplication_is_recorded(self):
        result, receipt = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["application"], "applied")
        self.assertFalse(receipt["dependency_build_verified"])
        self.assertFalse(receipt["blender_tests_executed"])
        for row in self.manifest["files"]:
            self.assertEqual(sha(self.port / row["path"]), row["after_sha256"])
        result, second = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(second["application"], "already_applied_exact_bytes")
        self.assertEqual(second["commands"], [])

    def test_changed_original_source_fails_before_mutation(self):
        target = self.port / "scripts/deps/openimageio.sh"
        target.write_text(target.read_text() + "# unreviewed source\n")
        result, receipt = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")
        self.assertIn("pinned inputs", receipt["reason"])
        self.assert_no_new_files()

    def test_wrong_selected_manifest_digest_rejected(self):
        result, _ = self.execute("0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicitly selected digest", result.stderr)
        self.assert_no_new_files()

    def test_tampered_patch_rejected_even_when_paths_are_unchanged(self):
        target = self.package / self.manifest["patch"]["file"]
        target.write_text(target.read_text().replace("WITH_IMAGE_WEBP", "WITH_IMAGE_XYZP", 1))
        result, _ = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patch identity mismatch", result.stderr)
        self.assert_no_new_files()

    def test_changed_application_helper_rejected(self):
        target = self.package / "apply.py"
        target.write_text(target.read_text() + "\n# modified consumer\n")
        result, _ = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("application helper identity mismatch", result.stderr)
        self.assert_no_new_files()

    def test_partial_application_does_not_qualify_or_resume(self):
        result, _ = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        name = "patches/blender_web.cmake"
        shutil.copyfile(SOURCE / name, self.port / name)
        result, receipt = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("partially applied", receipt["reason"])

    def test_symlinked_target_parent_cannot_modify_another_tree(self):
        target = self.port / "scripts/deps"
        moved = self.root / "elsewhere"
        target.rename(moved)
        before = sha(moved / "openimageio.sh")
        target.symlink_to(moved, target_is_directory=True)
        result, receipt = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", receipt["reason"])
        self.assertEqual(sha(moved / "openimageio.sh"), before)
        self.assertFalse((moved / "webp.sh").exists())

    def test_incomplete_file_inventory_cannot_hide_patch_writes(self):
        self.manifest["files"] = [row for row in self.manifest["files"]
                                  if row["path"] != "scripts/deps/webp.sh"]
        self.manifest_path.write_text(json.dumps(self.manifest))
        result, receipt = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patch paths differ", receipt["reason"])
        self.assert_no_new_files()

    def test_corrupted_applied_output_is_not_accepted_as_cached_success(self):
        result, _ = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.port / "patches/image_codecs.cmake"
        target.write_text(target.read_text().replace("REQUIRED", "QUIET", 1))
        result, receipt = self.execute()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt["status"], "failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
