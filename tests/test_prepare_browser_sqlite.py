"""Byte integrity and stale-cache regressions for the optional SQLite build."""
import contextlib
import difflib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import prepare_browser_sqlite as prepare


REPO = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.port = self.root / "port"
        self.recipe = self.port / "scripts/deps/python.sh"
        self.recipe.parent.mkdir(parents=True)
        self.original = b"#!/bin/sh\n# fixture recipe\nSQLITE=disabled\n"
        self.result = b"#!/bin/sh\n# fixture recipe\nSQLITE=real\n"
        self.recipe.write_bytes(self.original)
        self.patchroot = self.root / "patchset"
        self.patchroot.mkdir()
        delta = "".join(difflib.unified_diff(self.original.decode().splitlines(True), self.result.decode().splitlines(True),
                                           fromfile="a/scripts/deps/python.sh", tofile="b/scripts/deps/python.sh")).encode()
        self.files = {"sqlite.sh": b"#!/bin/sh\nexit 0\n", "sqlite-cache.py": b"# synthetic cache fixture only\n", "sqlite.patch": delta}
        for name, content in self.files.items():
            (self.patchroot / name).write_bytes(content)
        self.document = {"schema": 1, "id": "synthetic-build-contract",
                         "install_files": [{"file": name, "destination": "scripts/deps/" + name,
                                            "bytes": len(self.files[name]), "sha256": digest(self.files[name])}
                                           for name in ("sqlite.sh", "sqlite-cache.py")],
                         "patches": [{"file": "sqlite.patch", "destination": "scripts/deps/python.sh",
                                      "bytes": len(delta), "sha256": digest(delta),
                                      "before_bytes": len(self.original), "before_sha256": digest(self.original),
                                      "after_bytes": len(self.result), "after_sha256": digest(self.result)}],
                         "sqlite": {"archive": "sqlite-fixture.tar.gz", "bytes": 3, "sha256": digest(b"sql")},
                         "python": {"archive": "python-fixture.tar.xz", "bytes": 2, "sha256": digest(b"py")}}
        self.manifest = self.patchroot / "manifest.json"
        self.select()

    def select(self):
        self.manifest.write_text(json.dumps(self.document))
        self.pin = digest(self.manifest.read_bytes())

    def apply(self):
        return prepare.apply_patchset(self.port, self.manifest, self.pin)

    def test_exact_preparation_is_idempotent_and_retains_explicit_scope(self):
        first = self.apply()
        self.assertEqual(self.recipe.read_bytes(), self.result)
        self.assertEqual(first, self.apply())
        self.assertEqual(first["dependency_insertion"], {"name": "sqlite", "before": "python"})
        self.assertEqual(first["environment"]["BLENDED_SQLITE_PATCHSET_SHA256"], self.pin)
        self.assertFalse(first["source_tests_modified"])
        self.assertFalse(first["browser_tests_executed"])

    def test_manifest_and_patch_tampering_are_rejected_before_preparation(self):
        self.manifest.write_text(self.manifest.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "manifest hash mismatch"):
            self.apply()
        self.select()
        (self.patchroot / "sqlite.patch").write_text("forged patch\n")
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual(self.recipe.read_bytes(), self.original)

    def test_foreign_original_or_already_patched_recipe_is_rejected(self):
        for content in (b"unrelated original\n", self.result + b"# foreign edit\n"):
            with self.subTest(content=content):
                self.recipe.write_bytes(content)
                with self.assertRaisesRegex(ValueError, "neither the pinned original"):
                    self.apply()
                self.assertEqual(self.recipe.read_bytes(), content)

    def test_changed_diff_context_cannot_be_accepted_with_fresh_patch_hash(self):
        delta = self.files["sqlite.patch"].replace(b"# fixture recipe", b"# wrong context")
        (self.patchroot / "sqlite.patch").write_bytes(delta)
        self.document["patches"][0].update(bytes=len(delta), sha256=digest(delta))
        self.select()
        with self.assertRaisesRegex(ValueError, "patch context differs"):
            self.apply()
        self.assertEqual(self.recipe.read_bytes(), self.original)

    def test_conflicting_helper_is_detected_before_mutating_original_recipe(self):
        (self.recipe.parent / "sqlite.sh").write_bytes(b"unrelated existing helper\n")
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self.apply()
        self.assertEqual(self.recipe.read_bytes(), self.original)
        self.assertFalse((self.recipe.parent / "sqlite-patchset.json").exists())

    def test_existing_different_receipt_is_preserved_before_recipe_mutation(self):
        receipt = self.root / "existing-receipt.json"
        receipt.write_bytes(b"original immutable observation\n")
        with self.assertRaisesRegex(ValueError, "different SQLite preparation receipt"):
            prepare.apply_patchset(self.port, self.manifest, self.pin, receipt)
        self.assertEqual(receipt.read_bytes(), b"original immutable observation\n")
        self.assertEqual(self.recipe.read_bytes(), self.original)

    def test_destination_parent_symlink_and_source_traversal_are_rejected(self):
        actual = self.port / "actual-scripts"
        (self.port / "scripts").rename(actual)
        (self.port / "scripts").symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.apply()
        (self.port / "scripts").unlink()
        actual.rename(self.port / "scripts")
        self.document["install_files"][0]["file"] = "../escape"
        self.select()
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.apply()

    def test_patch_cannot_append_a_second_file_or_use_fuzzy_hunk_positions(self):
        for delta in (self.files["sqlite.patch"] + b"--- a/other\n+++ b/other\n",
                      self.files["sqlite.patch"].replace(b"@@ -1,3 +1,3 @@", b"@@ -2,3 +2,3 @@")):
            with self.subTest(delta=delta):
                with self.assertRaises(ValueError):
                    prepare.apply_exact_patch(self.original, delta, "scripts/deps/python.sh")

    def test_repository_manifest_inputs_are_all_bound(self):
        manifest = REPO / "patches/browser-sqlite/manifest.json"
        selected = prepare.load_patchset(manifest, digest(manifest.read_bytes()))
        self.assertEqual(len(selected["inputs"]), 3)
        self.assertEqual(selected["manifest"]["sqlite"]["version"], "3.51.3")
        self.assertFalse(selected["manifest"]["scope"]["original_tests_modified"])


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = REPO / "patches/browser-sqlite/sqlite-cache.py"
        spec = importlib.util.spec_from_file_location("sqlite_cache_under_test", source)
        self.cache = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.cache)
        contents = {
            "scripts/deps/sqlite.sh": b"# fixture recipe", "scripts/deps/sqlite-cache.py": source.read_bytes(),
            "scripts/deps/python.sh": b"# patched fixture python recipe",
            "tools/emsdk/upstream/emscripten/emcc": b"fixture compiler wrapper",
            "tools/emsdk/upstream/bin/clang": b"fixture compiler",
            "build-deps/_cache/sqlite.tar.gz": b"sqlite source fixture", "build-deps/_cache/python.tar.xz": b"python source fixture",
        }
        for name in ("lib/wasm/lib/libsqlite3.a", "lib/wasm/include/sqlite3.h", "lib/wasm/include/sqlite3ext.h",
                     "lib/wasm/lib/libpython3.13.a", "lib/wasm/include/python3.13/Python.h",
                     "lib/wasm/include/python3.13/pyconfig.h", "lib/wasm/lib/python3.13/sqlite3/__init__.py",
                     "lib/wasm/lib/python3.13/sqlite3/dbapi2.py", "lib/wasm/lib/python3.13/sqlite3/dump.py"):
            contents[name] = ("synthetic output " + name).encode()
        for name, content in contents.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        manifest = {"install_files": [{"destination": name, "bytes": len(contents[name]), "sha256": digest(contents[name])}
                                      for name in ("scripts/deps/sqlite.sh", "scripts/deps/sqlite-cache.py")],
                    "patches": [{"destination": "scripts/deps/python.sh", "after_bytes": len(contents["scripts/deps/python.sh"]),
                                 "after_sha256": digest(contents["scripts/deps/python.sh"])}]}
        for key, name in (("sqlite", "sqlite.tar.gz"), ("python", "python.tar.xz")):
            data = contents["build-deps/_cache/" + name]
            manifest[key] = {"archive": name, "bytes": len(data), "sha256": digest(data)}
        lock = self.root / "scripts/deps/sqlite-patchset.json"
        lock.write_text(json.dumps(manifest))
        environment = patch.dict(os.environ, {"BLENDED_SQLITE_PATCHSET_SHA256": digest(lock.read_bytes()), "EM_CACHE": "fixture-private-cache"})
        environment.start()
        self.addCleanup(environment.stop)

    def invoke(self, action, target="python"):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return self.cache.main([action, target, str(self.root)])

    def test_missing_or_changed_python_output_cannot_reuse_stale_cache(self):
        self.assertEqual(self.invoke("verify"), 1)
        self.assertEqual(self.invoke("record"), 0)
        self.assertEqual(self.invoke("verify"), 0)
        (self.root / "lib/wasm/lib/libpython3.13.a").write_bytes(b"older disabled-SQLite library")
        self.assertEqual(self.invoke("verify"), 1)

    def test_changed_sqlite_library_invalidates_python_receipt(self):
        self.assertEqual(self.invoke("record"), 0)
        (self.root / "lib/wasm/lib/libsqlite3.a").write_bytes(b"different SQLite library")
        self.assertEqual(self.invoke("verify"), 1)

    def test_changed_source_or_recipe_cannot_be_recorded_as_verified(self):
        for name in ("scripts/deps/python.sh", "scripts/deps/sqlite.sh", "build-deps/_cache/sqlite.tar.gz"):
            with self.subTest(name=name):
                path = self.root / name
                previous = path.read_bytes()
                path.write_bytes(b"different input")
                self.assertEqual(self.invoke("record"), 1)
                path.write_bytes(previous)

    def test_output_symlink_is_not_accepted_as_a_cache_artifact(self):
        path = self.root / "lib/wasm/lib/libsqlite3.a"
        outside = self.root / "outside.a"
        path.rename(outside)
        path.symlink_to(outside)
        self.assertEqual(self.invoke("record"), 1)

    def test_sdk_compiler_link_is_bound_to_a_confined_actual_binary(self):
        clang = self.root / "tools/emsdk/upstream/bin/clang"
        real = clang.with_name("clang-fixture-version")
        clang.rename(real)
        clang.symlink_to(real.name)
        self.assertEqual(self.invoke("record"), 0)
        self.assertEqual(self.invoke("verify"), 0)
        real.write_bytes(b"changed compiler payload")
        self.assertEqual(self.invoke("verify"), 1)
        clang.unlink()
        outside = self.root / "foreign-compiler"
        outside.write_bytes(b"foreign payload")
        clang.symlink_to(outside)
        self.assertEqual(self.invoke("record"), 1)


if __name__ == "__main__":
    unittest.main()
