"""Failure-oriented output-identity checks for explicit dependency-cache reuse."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from tools import verify_browser_dependency_cache as cache
from tools.verify_browser_dependency_cache import verify


class DependencyCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.prefix = self.root / "prefix"
        (self.prefix / "lib").mkdir(parents=True)
        self.file = self.prefix / "lib/output.a"
        self.file.write_bytes(b"synthetic original archive")
        self.manifest = self.root / "harvest.jsonl"
        self.manifest.write_text(json.dumps({"path": "lib/output.a", "bytes": self.file.stat().st_size,
            "sha256": hashlib.sha256(self.file.read_bytes()).hexdigest()}) + "\n")
        self.pin = hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def run_verification(self):
        return verify(self.prefix, self.manifest, self.pin)

    def make_alias_fixture(self):
        contract = cache.load_alias_contract(cache.ALIAS_CONTRACT, cache.ALIAS_CONTRACT_SHA256)
        self.aliases = {}
        for name, original in contract["aliases"].items():
            row = dict(original)
            target = self.prefix / row["target_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("synthetic fixture " + row["target_path"]).encode())
            row["target_identity"] = cache.identity(target)
            (self.prefix / name).symlink_to(row["link_text"])
            self.aliases[name] = row
        rows = [{"path": path.relative_to(self.prefix).as_posix(), **cache.identity(path)}
                for path in sorted(self.prefix.rglob("*")) if path.is_file() and not path.is_symlink()]
        self.manifest.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.pin = hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def verify_alias_fixture(self):
        return verify(self.prefix, self.manifest, self.pin, aliases=self.aliases)

    def invoke_main(self, receipt, *, aliases=None, extra=()):
        synthetic = {"aliases": aliases or {}, "scope": "Synthetic infrastructure fixture only"}
        with mock.patch.object(cache, "MANIFEST_SHA256", self.pin), \
                mock.patch.object(cache, "load_alias_contract", return_value=synthetic), \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            result = cache.main(["--prefix", str(self.prefix), "--manifest", str(self.manifest),
                                 "--receipt", str(receipt), *extra])
        return result, json.loads(receipt.read_text())

    def test_modified_missing_or_added_dependency_outputs_are_rejected(self):
        self.assertEqual(self.run_verification()["verified_files"], 1)
        original = self.file.read_bytes()
        self.file.write_bytes(b"different cached archive")
        with self.assertRaises(ValueError):
            self.run_verification()
        self.file.unlink()
        with self.assertRaises(ValueError):
            self.run_verification()
        self.file.write_bytes(original)
        (self.prefix / "lib/foreign.a").write_bytes(b"extra unbound archive")
        with self.assertRaises(ValueError):
            self.run_verification()

    def test_manifest_edit_cannot_qualify_a_changed_cache(self):
        self.manifest.write_text(self.manifest.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "manifest differs"):
            self.run_verification()

    def test_uninventoried_alias_is_rejected_even_to_a_verified_file(self):
        link = self.prefix / "lib/alias.a"
        link.symlink_to("output.a")
        with self.assertRaisesRegex(ValueError, "alias"):
            self.run_verification()
        link.unlink()
        external = self.root / "outside.a"
        external.write_bytes(self.file.read_bytes())
        link.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "alias"):
            self.run_verification()

    def test_directory_link_cannot_hide_uninventoried_dependency_files(self):
        link = self.prefix / "alias"
        link.symlink_to(self.prefix / "lib", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "alias"):
            self.run_verification()

    def test_symlink_cycle_produces_a_final_failed_receipt(self):
        (self.prefix / "cycle-a").symlink_to("cycle-b")
        (self.prefix / "cycle-b").symlink_to("cycle-a")
        receipt = self.root / "cycle-receipt.json"
        result, report = self.invoke_main(receipt)
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")

    def test_exact_source_derived_png_aliases_are_required_and_accepted(self):
        self.make_alias_fixture()
        report = self.verify_alias_fixture()
        self.assertEqual(report["verified_files"], 4)
        self.assertEqual(report["verified_aliases"], 3)
        self.assertEqual({row["path"] for row in report["links"]}, set(self.aliases))
        (self.prefix / "lib/libpng.a").unlink()
        with self.assertRaisesRegex(ValueError, "missing required.*aliases"):
            self.verify_alias_fixture()

    def test_redirected_alias_to_another_verified_file_is_rejected(self):
        self.make_alias_fixture()
        link = self.prefix / "lib/libpng.a"
        link.unlink()
        link.symlink_to("output.a")
        with self.assertRaisesRegex(ValueError, "alias text differs"):
            self.verify_alias_fixture()

    def test_equivalent_but_unselected_link_text_is_rejected(self):
        self.make_alias_fixture()
        link = self.prefix / "lib/libpng.a"
        link.unlink()
        link.symlink_to("./libpng16.a")
        with self.assertRaisesRegex(ValueError, "alias text differs"):
            self.verify_alias_fixture()

    def test_additional_alias_is_rejected_even_when_target_is_verified(self):
        self.make_alias_fixture()
        (self.prefix / "lib/additional.a").symlink_to("libpng16.a")
        with self.assertRaisesRegex(ValueError, "unrecognized cache alias"):
            self.verify_alias_fixture()

    def test_cyclic_required_alias_fails_without_a_running_receipt(self):
        self.make_alias_fixture()
        link = self.prefix / "lib/libpng.a"
        link.unlink()
        link.symlink_to("libpng.a")
        result, report = self.invoke_main(self.root / "required-cycle.json", aliases=self.aliases)
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")
        self.assertIn("alias text differs", report["reason"])

    def test_unexpected_runtime_resolution_error_has_final_failed_receipt(self):
        with mock.patch.object(cache, "verify", side_effect=RuntimeError("symlink resolution failed")):
            result, report = self.invoke_main(self.root / "runtime-error.json")
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["reason"], "symlink resolution failed")

    def test_prefix_matched_cache_key_cannot_qualify(self):
        result, report = self.invoke_main(self.root / "wrong-cache.json",
                                         extra=("--cache-key", cache.CACHE_KEY + "-different"))
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["cache_key"], cache.CACHE_KEY + "-different")
        self.assertEqual(report["expected_cache_key"], cache.CACHE_KEY)
        self.assertIn("cache key differs", report["reason"])

    def test_contract_and_original_installer_sources_have_fixed_identities(self):
        contract = cache.load_alias_contract(cache.ALIAS_CONTRACT, cache.ALIAS_CONTRACT_SHA256)
        self.assertEqual(len(contract["aliases"]), 3)
        self.assertEqual(len(contract["sources"]), 4)
        copied = self.root / "contract"
        shutil.copytree(cache.ALIAS_CONTRACT.parent, copied)
        source = copied / "sources/libpng-1.6.58/CMakeLists.txt"
        source.write_bytes(source.read_bytes() + b"# changed installer\n")
        with self.assertRaisesRegex(ValueError, "source differs"):
            cache.load_alias_contract(copied / "contract.json", cache.ALIAS_CONTRACT_SHA256)
        with self.assertRaisesRegex(ValueError, "selected digest"):
            cache.load_alias_contract(cache.ALIAS_CONTRACT, "0" * 64)


if __name__ == "__main__":
    unittest.main()
