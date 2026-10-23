import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools import hydrate_product_fixtures as hydration


class ProductFixtureHydrationTest(unittest.TestCase):
    def make_source(self, directory):
        commit = "a" * 40
        root = directory / ("blender-" + commit)
        root.mkdir()
        payload = b"exact original payload\0\xff"
        oid = hashlib.sha256(payload).hexdigest()
        pointer = ("version https://git-lfs.github.com/spec/v1\noid sha256:" + oid + "\nsize " + str(len(payload)) + "\n").encode()
        originals = {"tests/files/a.blend": pointer, "tests/files/copy.blend": pointer,
                     "tests/files/reference.txt": b"original reference\n"}
        rows = []
        archive_path = directory / "source.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            for relative, raw in originals.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                info = tarfile.TarInfo(root.name + "/" + relative)
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
                row = {"path": relative, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                       "status": "lfs_pointer" if raw == pointer else "present_unvalidated"}
                if raw == pointer:
                    row.update(lfs_oid_sha256=oid, lfs_declared_size=len(payload), lfs_pointer_valid=True)
                rows.append(row)
        inventory_path = directory / "source-inventory.json"
        inventory_path.write_text(json.dumps({"commit": commit, "upstream": "blender/blender",
                                              "fixture_roots": [{"path": "tests/files"}], "fixtures": rows}))
        archive_sha256 = hydration.file_identity(archive_path)["sha256"]
        return root, payload, oid, pointer, inventory_path, archive_path, commit, archive_sha256

    def test_archive_validation_preserves_every_pointer_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, payload, oid, pointer, inventory, archive, commit, digest = self.make_source(Path(temporary))
            result = hydration.freeze_inventory(inventory, archive, root, commit, digest)
            self.assertEqual((result["candidate_count"], result["lfs_path_count"], result["regular_path_count"]), (3, 2, 1))
            self.assertEqual((result["unique_lfs_object_count"], result["unique_lfs_bytes"]), (1, len(payload)))
            self.assertEqual(result["entries"][0]["original"]["text"].encode(), pointer)
            source = json.loads(inventory.read_text())
            source["fixtures"].pop()
            inventory.write_text(json.dumps(source))
            with self.assertRaisesRegex(hydration.HydrationError, "omitted candidate"):
                hydration.freeze_inventory(inventory, archive, root, commit, digest)

    def test_changed_regular_source_and_symlink_are_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, payload, oid, pointer, inventory, archive, commit, digest = self.make_source(Path(temporary))
            regular = root / "tests/files/reference.txt"
            regular.write_bytes(b"changed")
            with self.assertRaisesRegex(hydration.HydrationError, "changed source fixture"):
                hydration.freeze_inventory(inventory, archive, root, commit, digest)
            regular.unlink()
            regular.symlink_to(root / "tests/files/a.blend")
            with self.assertRaisesRegex(hydration.HydrationError, "symlink"):
                hydration.freeze_inventory(inventory, archive, root, commit, digest)

    def test_materialization_requires_exact_pointer_and_preserves_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root, payload, oid, pointer, inventory, archive, commit, digest = self.make_source(directory)
            result = hydration.freeze_inventory(inventory, archive, root, commit, digest)
            cached = directory / oid
            cached.write_bytes(payload)
            row = result["entries"][0]
            path = root / row["path"]
            path.write_bytes(b"unrelated content")
            with self.assertRaisesRegex(hydration.HydrationError, "changed before replacement"):
                hydration.materialize(row, root, cached)
            self.assertEqual(path.read_bytes(), b"unrelated content")
            path.write_bytes(pointer)
            self.assertEqual(hydration.materialize(row, root, cached), "hydrated_original_pointer")
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual((root / "tests/files/reference.txt").read_bytes(), b"original reference\n")

    def test_nonofficial_actions_and_redirects_are_rejected(self):
        for url in ["http://projects.blender.org/object", "https://example.org/object",
                    "https://projects.blender.org.evil.invalid/object", "https://u:p@projects.blender.org/object"]:
            with self.subTest(url=url), self.assertRaises(hydration.HydrationError):
                hydration.validate_action(url, {})
        hydration.validate_action("https://projects.blender.org/blender/blender.git/info/lfs/objects/abc", {})

    def test_one_cached_object_hydrates_duplicate_paths_without_network_or_pass_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            root, payload, oid, pointer, inventory, archive, commit, digest = self.make_source(directory)
            cache = directory / "objects"
            cache.mkdir()
            (cache / oid).write_bytes(payload)
            evidence = directory / "evidence"
            with patch.object(hydration, "actions_for", side_effect=AssertionError("unexpected network")):
                self.assertTrue(hydration.hydrate(inventory, archive, root, commit, digest, evidence, cache))
            result = json.loads((evidence / "report.json").read_text())
            self.assertEqual(result["counts"]["hydrated_paths"], 2)
            self.assertEqual(result["counts"]["verified_cache_objects"], 1)
            self.assertEqual(result["tests_executed"], 0)
            self.assertFalse(result["runtime_fixture_dependency_closure_complete"])
            self.assertEqual((root / "tests/files/copy.blend").read_bytes(), payload)

    def test_corrupt_download_is_retained_and_never_promoted_to_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            expected = b"correct"
            oid = hashlib.sha256(expected).hexdigest()
            class Opener:
                def open(self, *args, **kwargs):
                    return io.BytesIO(b"corrupt")
            with patch.object(hydration.urllib.request, "build_opener", return_value=Opener()):
                result = hydration.download_object(oid, len(expected), ("https://projects.blender.org/object", {}), directory, 1)
            self.assertEqual(result["status"], "download_failed")
            self.assertFalse((directory / oid).exists())
            self.assertEqual(Path(result["partial_path"]).read_bytes(), b"corrupt")


if __name__ == "__main__":
    unittest.main()
