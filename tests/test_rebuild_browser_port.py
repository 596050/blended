"""Real pinned recipe integration and failure gates; no Blender feature claims."""
from pathlib import Path
import shutil
import tempfile
import types
import unittest

from tools import rebuild_browser_port as build


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_PORT = ROOT / "compatibility/evidence/browser-codecs-5.2-2026-10-23/sources/port"


class DependencyIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.args = types.SimpleNamespace(
            work_dir=self.root / "work", output=self.root / "evidence", jobs=1,
            stage_timeout=60, build_timeout=60, numeric_patchset=None,
            sqlite_patchset=ROOT / "patches/browser-sqlite/manifest.json",
            codec_patchset=ROOT / "patches/browser-codecs/manifest.json",
        )
        self.driver = build.Build(self.args)
        for relative in ("scripts/deps/python.sh", "scripts/deps/openimageio.sh",
                         "patches/blender_web.cmake", "patches/platform_wasm.cmake"):
            target = self.driver.port / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ORIGINAL_PORT / relative, target)

    def test_both_real_patchsets_apply_before_recipe_snapshot_without_losing_dependencies(self):
        self.driver.load_dependency_patchsets()
        self.driver.apply_dependency_patchsets()
        order = self.driver.dependency_order
        self.assertEqual([item for item in order if item in build.DEPENDENCIES], build.DEPENDENCIES)
        index = order.index("openimageio")
        self.assertEqual(order[index - 4:index], ["webp", "openjpeg", "aom", "libheif"])
        self.assertEqual(order[order.index("python") - 1], "sqlite")
        self.assertEqual(len(order), len(set(order)))
        for key in ("PYTHON_CPU_COUNT", "EMCC_CORES", "BLENDED_BUILD_JOBS"):
            self.assertEqual(self.driver.env[key], "1")
        for name in ("sqlite", "codec"):
            receipt = self.driver.data[name + "_patchset"]
            self.assertTrue(receipt["applied"])
            self.assertEqual(receipt["status"], "applied_and_verified")
            for output in receipt["outputs"]:
                actual = build.digest(self.driver.port / output["path"])
                self.assertEqual((actual["sha256"], actual["bytes"]),
                                 (output["sha256"], output["bytes"]))
        self.assertFalse(self.driver.data["tests_executed"])
        self.assertFalse(self.driver.data["full_feature_parity"])

    def test_baseline_does_not_silently_enable_optional_dependencies(self):
        self.args.sqlite_patchset = self.args.codec_patchset = None
        before = build.digest(self.driver.port / "scripts/deps/python.sh")
        self.driver.load_dependency_patchsets()
        self.driver.apply_dependency_patchsets()
        self.assertEqual(self.driver.dependency_order, build.DEPENDENCIES)
        self.assertEqual(build.digest(self.driver.port / "scripts/deps/python.sh"), before)
        self.assertNotIn("sqlite_patchset", self.driver.data)
        self.assertNotIn("codec_patchset", self.driver.data)

    def test_foreign_manifest_is_rejected_before_any_recipe_mutation(self):
        original = (self.driver.port / "scripts/deps/python.sh").read_bytes()
        foreign = self.root / "manifest.json"
        foreign.write_bytes(self.args.sqlite_patchset.read_bytes() + b" ")
        self.args.sqlite_patchset = foreign
        with self.assertRaisesRegex(build.Blocked, "manifest digest"):
            self.driver.load_dependency_patchsets()
        self.assertEqual((self.driver.port / "scripts/deps/python.sh").read_bytes(), original)
        self.assertEqual(self.driver.data["stages"], [])

    def test_patch_preimage_failure_keeps_actual_failed_stage_and_no_applied_claim(self):
        self.driver.load_dependency_patchsets()
        path = self.driver.port / "scripts/deps/python.sh"
        path.write_bytes(path.read_bytes() + b"# foreign recipe edit\n")
        with self.assertRaisesRegex(RuntimeError, "failed with exit code"):
            self.driver.apply_dependency_patchsets()
        stage = self.driver.data["stages"][-1]
        self.assertEqual(stage["status"], "failed")
        self.assertNotEqual(stage["exit_code"], 0)
        self.assertFalse(self.driver.data["sqlite_patchset"]["applied"])
        self.assertFalse(self.driver.data["codec_patchset"]["applied"])

    def test_missing_or_trimmed_oiio_configuration_cannot_satisfy_codec_profile(self):
        self.driver.load_dependency_patchsets()
        manifest = self.driver.codec_manifest
        with self.assertRaisesRegex(build.Blocked, "preserve"):
            self.driver.verify_dependency_features("openimageio")
        path = self.driver.port / manifest["installed_oiio_configuration"]
        path.parent.mkdir(parents=True)
        values = dict(manifest["required_oiio_cache"], USE_LIBHEIF="OFF")
        path.write_text("".join(key + ":BOOL=" + value + "\n" for key, value in values.items()))
        with self.assertRaisesRegex(build.Blocked, "required static codec profile"):
            self.driver.verify_dependency_features("openimageio")
        self.assertNotIn("configured_oiio_features", self.driver.data["codec_patchset"])

    def test_verified_oiio_configuration_is_retained_with_its_actual_hash(self):
        self.driver.load_dependency_patchsets()
        manifest = self.driver.codec_manifest
        path = self.driver.port / manifest["installed_oiio_configuration"]
        path.parent.mkdir(parents=True)
        path.write_text("".join(key + ":BOOL=" + value + "\n"
                                for key, value in manifest["required_oiio_cache"].items()))
        self.driver.verify_dependency_features("openimageio")
        saved = self.driver.data["codec_patchset"]["oiio_configuration"]
        self.assertEqual(saved["sha256"], build.digest(path)["sha256"])
        self.assertEqual(self.driver.data["codec_patchset"]["configured_oiio_features"],
                         manifest["required_oiio_cache"])

    def test_duplicate_or_missing_dependency_anchors_are_rejected(self):
        for order, names, before in ((["python"], ["python"], "python"),
                                     (["python", "python"], ["sqlite"], "python"),
                                     (["python"], ["sqlite", "sqlite"], "python"),
                                     (["python"], ["sqlite"], "missing")):
            with self.subTest(order=order, names=names, before=before):
                with self.assertRaises(build.Blocked):
                    build.insert_dependencies(order, names, before)


if __name__ == "__main__":
    unittest.main()
