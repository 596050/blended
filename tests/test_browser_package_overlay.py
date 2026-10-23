"""Synthetic package integrity checks, not Blender feature evidence."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch

from tools import browser_package_overlay as overlay
from tools import probe_browser_port as probe


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class BrowserPackageOverlayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.payload = b"original synthetic resource, not a Blender asset"
        self.plan = {
            "schema": 1, "id": "synthetic-overlay", "upstream": {"commit": probe.UPSTREAM_SHA},
            "files": [{"upstream_path": "assets/brushes/example.blend",
                       "destination": "/bw/datafiles/assets/brushes/example.blend",
                       **identity(self.payload)}],
        }
        self.plan_identity = identity(json.dumps(self.plan, sort_keys=True).encode())
        self.plan_patch = patch.object(overlay, "load_plan", return_value=(self.plan, self.plan_identity))
        self.plan_patch.start()
        self.addCleanup(self.plan_patch.stop)
        self.base_data = b"startup"
        self.js = ('prefix;Module["FS_createPath"]("/bw","datafiles",true,true);'
                   'loadPackage({files:[{filename:"/bw/datafiles/startup.blend",start:0,end:7}],'
                   'remote_package_size:7});suffix;')
        self.members = {
            "bundle/bin/blender_browser.data": self.base_data,
            "bundle/bin/blender_browser.js": self.js.encode(),
            "bundle/bin/blender_browser.wasm": b"synthetic wasm identity",
            "bundle/shell/boot-windowed.js": b"synthetic shell identity",
            "bundle/LICENSE": b"synthetic license identity",
        }
        self.base = self.root / "base.tar.gz"
        self.write_archive(self.base, self.members)
        self.source = self.root / "source-build.json"
        self.source_data = {
            "schema": 1, "artifact_kind": "blender-source-development", "status": "built",
            "upstream_commit": probe.UPSTREAM_SHA, "port_commit": probe.DEVELOPMENT_PORT_SHA,
            "canonical_patch_sha256": probe.DEVELOPMENT_PATCH_SHA256,
            "build_mode": "OFF", "with_buildinfo": True,
            "artifact": {"path": str(self.base), **identity(self.base.read_bytes())},
            "engine_files": [{"path": name, **identity(data)} for name, data in self.members.items()
                             if "/bin/" in name],
        }
        self.source.write_text(json.dumps(self.source_data))
        self.asset_root = self.root / "assets"
        payload_file = self.asset_root / self.plan["files"][0]["upstream_path"]
        payload_file.parent.mkdir(parents=True)
        payload_file.write_bytes(self.payload)

    def write_archive(self, path, members):
        with tarfile.open(path, "w:gz") as archive:
            for name, data in members.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))

    def assemble(self):
        output = self.root / "result"
        return overlay.assemble_overlay(self.base, self.source, self.asset_root, output)

    def verify(self, receipt):
        return overlay.verify_overlay_receipt(receipt, self.source)

    def corrupt_output_and_rebind_digest(self, receipt_path, name, transform):
        receipt = json.loads(receipt_path.read_text())
        archive_path = Path(receipt["artifact"]["path"])
        with tarfile.open(archive_path) as archive:
            members = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
        members[name] = transform(members[name])
        self.write_archive(archive_path, members)
        receipt["artifact"].update(identity(archive_path.read_bytes()))
        receipt_path.write_text(json.dumps(receipt))

    def test_new_metadata_appends_asset_and_preserves_old_offsets(self):
        changed = overlay.append_preload(self.js, len(self.base_data), self.plan["files"])
        entries, size = overlay.parse_preload(changed)
        self.assertEqual(entries[0], {"filename": "/bw/datafiles/startup.blend", "start": 0, "end": 7})
        self.assertEqual(entries[-1]["filename"], self.plan["files"][0]["destination"])
        self.assertEqual(entries[-1]["start"], 7)
        self.assertEqual(size, 7 + len(self.payload))
        self.assertIn('Module["FS_createPath"]("/bw/datafiles/assets","brushes",true,true);', changed)
        self.assertTrue(changed.startswith("prefix;"))
        self.assertTrue(changed.endswith(";suffix;"))

    def test_malformed_or_duplicate_package_entries_are_rejected(self):
        for source in (self.js.replace("remote_package_size:7", "remote_package_size:8"),
                       self.js.replace("start:0", "start:1"),
                       self.js.replace("start:0", "start:evil()"),
                       self.js.replace("/bw/datafiles/startup.blend", "/bw/../outside"),
                       self.js + self.js):
            with self.subTest(source=source), self.assertRaises(ValueError):
                overlay.append_preload(source, 7, self.plan["files"])

    def test_existing_destination_cannot_be_overwritten(self):
        additions = copy.deepcopy(self.plan["files"])
        additions[0]["destination"] = "/bw/datafiles/startup.blend"
        with self.assertRaises(ValueError):
            overlay.append_preload(self.js, 7, additions)

    def test_minified_integer_exponents_keep_exact_offsets(self):
        source = self.js.replace("end:7", "end:39466e3").replace("remote_package_size:7", "remote_package_size:39466e3")
        changed = overlay.append_preload(source, 39466000, self.plan["files"])
        entries, size = overlay.parse_preload(changed)
        self.assertEqual(entries[0]["end"], 39466000)
        self.assertEqual(entries[-1]["start"], 39466000)
        self.assertEqual(size, 39466000 + len(self.payload))
        with self.assertRaises(ValueError):
            overlay.parse_preload(source.replace("39466e3", "1e400"))

    def test_assembly_is_distinct_and_base_is_unchanged(self):
        before = self.base.read_bytes()
        path = self.assemble()
        result = self.verify(path)
        self.assertEqual(self.base.read_bytes(), before)
        self.assertNotEqual(result["artifact"]["sha256"], identity(before)["sha256"])
        self.assertEqual(result["kind"], "blender-browser-package-overlay")
        self.assertEqual(result["verification"]["unchanged_files"], 3)
        self.assertFalse(result["full_parity"])
        self.assertEqual(result["tests_executed"], 0)

    def test_changed_asset_is_rejected(self):
        (self.asset_root / self.plan["files"][0]["upstream_path"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.assemble()

    def test_changed_base_archive_is_rejected(self):
        self.base.write_bytes(b"changed archive")
        with self.assertRaises(ValueError):
            self.assemble()

    def test_changed_source_receipt_is_rejected(self):
        receipt = self.assemble()
        self.source.write_text(self.source.read_text() + "\n")
        with self.assertRaises(ValueError):
            self.verify(receipt)

    def test_unrelated_js_change_is_rejected_even_if_archive_digest_is_rebound(self):
        receipt = self.assemble()
        self.corrupt_output_and_rebind_digest(receipt, "bundle/bin/blender_browser.js",
                                             lambda data: data.replace(b"suffix", b"changed"))
        with self.assertRaises(ValueError):
            self.verify(receipt)

    def test_existing_data_change_is_rejected_even_if_archive_digest_is_rebound(self):
        receipt = self.assemble()
        self.corrupt_output_and_rebind_digest(receipt, "bundle/bin/blender_browser.data",
                                             lambda data: b"X" + data[1:])
        with self.assertRaises(ValueError):
            self.verify(receipt)

    def test_overlay_data_change_is_rejected_even_if_archive_digest_is_rebound(self):
        receipt = self.assemble()
        self.corrupt_output_and_rebind_digest(receipt, "bundle/bin/blender_browser.data",
                                             lambda data: data[:-1] + b"X")
        with self.assertRaises(ValueError):
            self.verify(receipt)

    def test_wasm_change_is_rejected_even_if_archive_digest_is_rebound(self):
        receipt = self.assemble()
        self.corrupt_output_and_rebind_digest(receipt, "bundle/bin/blender_browser.wasm", lambda data: b"changed")
        with self.assertRaises(ValueError):
            self.verify(receipt)

    def test_other_archive_member_change_is_rejected(self):
        receipt = self.assemble()
        self.corrupt_output_and_rebind_digest(receipt, "bundle/LICENSE", lambda data: b"changed")
        with self.assertRaises(ValueError):
            self.verify(receipt)

    def test_unsafe_archive_member_is_rejected(self):
        self.members["../outside"] = b"outside"
        self.write_archive(self.base, self.members)
        self.source_data["artifact"].update(identity(self.base.read_bytes()))
        self.source.write_text(json.dumps(self.source_data))
        with self.assertRaises(ValueError):
            self.assemble()

    def test_probe_binds_overlay_separately_from_original_source_build(self):
        receipt = self.assemble()
        record = json.loads(receipt.read_text())
        report = {}
        args = types.SimpleNamespace(asset=Path(record["artifact"]["path"]), source_build_receipt=self.source,
                                     package_overlay_receipt=receipt, package_base_asset=self.base)
        contract = probe.select_artifact_contract(args, report)
        self.assertEqual(contract["sha256"], record["artifact"]["sha256"])
        self.assertEqual(report["package_overlay"]["base_artifact"]["sha256"], self.source_data["artifact"]["sha256"])
        self.assertEqual(report["source_build"]["receipt_sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(report["candidate"]["kind"], "blender-source-development-package-overlay")
        self.assertFalse(report["source_correspondence_verified"])

    def test_overlay_without_source_build_receipt_cannot_select_an_artifact(self):
        args = types.SimpleNamespace(asset=self.base, package_overlay_receipt=Path("missing.json"))
        with self.assertRaises(probe.Blocked):
            probe.select_artifact_contract(args, {})


if __name__ == "__main__":
    unittest.main()
