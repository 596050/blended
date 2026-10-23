#!/usr/bin/env python3
"""Application regressions using the real pinned port preimages and reviewed diff."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
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


class DPXSignedBufferTests(unittest.TestCase):
    """Execute the exact upstream helper with both relevant unsigned widths.

    These are component arithmetic and recipe regressions. They do not execute
    Blender or establish image decoding or original-suite conformance.
    """

    BEFORE = "793e53edfac8dc79b8cea7bf0cc15c29a23b947e5559cf65cbe4bafd7227ebf1"
    AFTER = "28dd63ce548ee759f09bd23c2a90040408e3f91ffdfc7be3888fb357ad11d9b3"
    SOURCE_NAME = "src/dpx.imageio/libdpx/DPXColorConverter.cpp"
    PATCH_NAME = "scripts/deps/openimageio-dpx-signed-buffer.patch"

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="blended-dpx-width-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.port = cls.root / "port"
        cls.port.mkdir()
        manifest = json.loads((PACKAGE / "manifest.json").read_text())
        for row in manifest["files"]:
            if row["before_sha256"] is not None:
                target = cls.port / row["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE / row["path"], target)
        applied = subprocess.run(
            [sys.executable, str(PACKAGE / "apply.py"), "--port-root", str(cls.port),
             "--receipt", str(cls.root / "application.json"),
             "--expected-manifest-sha256", sha(PACKAGE / "manifest.json")],
            capture_output=True, text=True, timeout=30)
        if applied.returncode:
            raise RuntimeError(applied.stderr)
        cls.original = (PACKAGE / "test-data/DPXColorConverter.cpp").read_bytes()
        if hashlib.sha256(cls.original).hexdigest() != cls.BEFORE:
            raise RuntimeError("DPX upstream preimage identity mismatch")
        for row in manifest["dpx_signed_buffer"]["test_preimages"]:
            payload = (PACKAGE / row["file"]).read_bytes()
            if len(payload) != row["bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise RuntimeError("DPX test preimage identity mismatch")
        if (cls.port / cls.PATCH_NAME).read_bytes() != (
                PACKAGE / manifest["dpx_signed_buffer"]["patch"]["file"]).read_bytes():
            raise RuntimeError("Embedded and reviewed DPX dependency patches differ")
        recipe = (cls.port / "scripts/deps/openimageio.sh").read_text()
        start = recipe.index("# DPX uses a negative byte count")
        end_marker = 'bc_check_sha256 "$BC_DPX_SOURCE" ' + cls.AFTER + "\n"
        end = recipe.index(end_marker, start) + len(end_marker)
        cls.recipe_block = recipe[start:end]
        cls.source_tree = cls.root / "upstream"
        original_path = cls.source_tree / cls.SOURCE_NAME
        original_path.parent.mkdir(parents=True)
        original_path.write_bytes(cls.original)
        result = cls.apply_recipe(cls.port, cls.source_tree)
        if result.returncode:
            raise RuntimeError(result.stderr)
        cls.patched = original_path.read_bytes()
        if hashlib.sha256(cls.patched).hexdigest() != cls.AFTER:
            raise RuntimeError("DPX recipe did not produce the exact reviewed source")

        header = (PACKAGE / "test-data/DPXHeader.h").read_text()
        enum = re.search(r"\benum Descriptor\s*\{.*?\n\s*\};", header, flags=re.S)
        if enum is None:
            raise RuntimeError("Pinned upstream Descriptor enum is absent")

        def helper(payload):
            text = payload.decode()
            begin = text.index("\tstatic inline int64_t QueryRGBBufferSizeInternal(")
            end = text.index("\n\tint64_t QueryRGBBufferSize(", begin)
            return text[begin:end]

        program = "#include <cstdint>\n#include <iostream>\n"
        program += "static_assert(sizeof(std::uint32_t) == 4);\n"
        program += "static_assert(sizeof(std::uint64_t) == 8);\n"
        variants = (("before32", 32, cls.original), ("after32", 32, cls.patched),
                    ("before64", 64, cls.original), ("after64", 64, cls.patched))
        for name, width, payload in variants:
            program += ("namespace " + name + " {\nusing size_t = std::uint" + str(width)
                        + "_t;\nusing int64_t = std::int64_t;\n" + enum[0] + "\n"
                        + helper(payload) + "\n}\n")
        program += "int main() { unsigned d; std::uint64_t p, b;\n"
        program += "while (std::cin >> d >> p >> b) {\n"
        for index, (name, _, _) in enumerate(variants):
            program += ("std::cout << " + name + "::QueryRGBBufferSizeInternal(static_cast<"
                        + name + "::Descriptor>(d), static_cast<" + name
                        + "::size_t>(p), static_cast<" + name + "::size_t>(b))"
                        + (" << ' ';\n" if index < 3 else " << '\\n';\n"))
        program += "} return std::cin.eof() ? 0 : 2; }\n"
        source = cls.root / "actual-helpers.cpp"
        source.write_text(program)
        cls.executable = cls.root / "actual-helpers"
        compiler = shutil.which("c++")
        if not compiler:
            raise RuntimeError("A C++ compiler is required for DPX numeric regression coverage")
        compiled = subprocess.run(
            [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic",
             "-fsanitize=undefined", "-fno-sanitize-recover=undefined",
             str(source), "-o", str(cls.executable)], capture_output=True, text=True, timeout=30)
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)

    @classmethod
    def apply_recipe(cls, port, source_tree):
        script = ('set -euo pipefail\nROOT="$1"\nSRC="$2"\n'
                  'source "$ROOT/scripts/deps/codec-common.sh"\n' + cls.recipe_block)
        return subprocess.run(["bash", "-s", "--", str(port), str(source_tree)],
                              input=script, capture_output=True, text=True, timeout=30)

    def evaluate(self, cases):
        result = subprocess.run([str(self.executable)],
                                input="".join("%d %d %d\n" % row for row in cases),
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
        self.assertEqual(len(values), len(cases))
        self.assertTrue(all(len(row) == 4 for row in values))
        return values

    def test_actual_32_by_32_rgba_reproduces_unsigned_failure_and_signed_sentinel(self):
        self.assertEqual(self.evaluate([(51, 32 * 32, 1)]),
                         [(4294963200, -4096, -4096, -4096)])

    def test_all_original_negative_descriptor_branches_keep_the_signed_size(self):
        channels = {50: 3, 102: 3, 51: 4, 52: 4, 103: 4}
        cases = [(desc, pixels, width) for desc in channels
                 for pixels in (0, 1, 31, 1024, 65537, 2**32 - 1)
                 for width in (1, 2, 4, 8)]
        for case, values in zip(cases, self.evaluate(cases)):
            desc, pixels, width = case
            expected = -(pixels * channels[desc] * width)
            with self.subTest(descriptor=desc, pixels=pixels, component_bytes=width):
                self.assertEqual(values[1:], (expected, expected, expected))
                self.assertEqual(values[0], expected % (2**32))

    def test_positive_and_unsupported_descriptors_preserve_existing_results(self):
        channels = {100: 3, 101: 4, 1: 1, 2: 1, 3: 1, 4: 1, 6: 1, 8: 1,
                    0: 0, 7: 0, 9: 0, 150: 0, 151: 0, 152: 0, 153: 0,
                    154: 0, 155: 0, 156: 0, 255: 0}
        cases = [(desc, pixels, width) for desc in channels
                 for pixels in (0, 1, 31, 1024, 65537) for width in (1, 2, 4, 8)]
        for case, values in zip(cases, self.evaluate(cases)):
            desc, pixels, width = case
            expected = pixels * channels[desc] * width
            with self.subTest(descriptor=desc, pixels=pixels, component_bytes=width):
                self.assertEqual(values, (expected,) * 4)

    def test_inactive_source_and_every_other_source_byte_are_unchanged(self):
        expected = self.original
        for count in (3, 4):
            expected = expected.replace(f"return pixels * -{count} * bytes;".encode(),
                                        f"return -int64_t(pixels) * {count} * int64_t(bytes);".encode(), 1)
        self.assertEqual(self.patched, expected)
        for count in (3, 4):
            self.assertEqual(self.patched.count(f"return pixels * -{count} * bytes;".encode()), 1)

    def test_recipe_rejects_changed_upstream_source_before_patching(self):
        with tempfile.TemporaryDirectory(prefix="blended-dpx-bad-source-") as directory:
            tree = Path(directory)
            source = tree / self.SOURCE_NAME
            source.parent.mkdir(parents=True)
            modified = self.original + b"\n// altered source\n"
            source.write_bytes(modified)
            result = self.apply_recipe(self.port, tree)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA256 mismatch", result.stderr)
            self.assertEqual(source.read_bytes(), modified)

    def test_recipe_rejects_changed_dependency_patch_before_source_mutation(self):
        with tempfile.TemporaryDirectory(prefix="blended-dpx-bad-patch-") as directory:
            root = Path(directory)
            port, tree = root / "port", root / "source"
            shutil.copytree(self.port, port)
            patch = port / self.PATCH_NAME
            patch.write_bytes(patch.read_bytes() + b"\n# altered patch\n")
            source = tree / self.SOURCE_NAME
            source.parent.mkdir(parents=True)
            source.write_bytes(self.original)
            result = self.apply_recipe(port, tree)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA256 mismatch", result.stderr)
            self.assertEqual(source.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
