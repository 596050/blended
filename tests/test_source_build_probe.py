"""Source-build provenance gates; these are not Blender feature tests."""
import hashlib
import json
from pathlib import Path
import tempfile
import types
import unittest

from tools import probe_browser_port as probe


class SourceBuildProbeTests(unittest.TestCase):
    def receipt(self, asset):
        return {
            "schema": 1,
            "artifact_kind": "blender-source-development",
            "status": "built",
            "upstream_commit": probe.UPSTREAM_SHA,
            "port_commit": "0e02e84b2bc5d9b27a6dc6e275443292f781fbad",
            "canonical_patch_sha256": "04ba2e6ba8a04ef37bdaf879b10a135736f07114597a908bbbdea8bba244193c",
            "build_mode": "OFF",
            "with_buildinfo": True,
            "artifact": {"path": asset.name, "bytes": asset.stat().st_size,
                         "sha256": hashlib.sha256(asset.read_bytes()).hexdigest()},
        }

    def test_source_receipt_cannot_be_labelled_as_the_published_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic artifact, contract test only")
            receipt = root / "build.json"
            receipt.write_text(json.dumps(self.receipt(asset)))
            args = types.SimpleNamespace(asset=asset, source_build_receipt=receipt)
            report = {"candidate": {"tag": "v0.1.1"}, "artifact": {}}
            contract = probe.select_artifact_contract(args, report)
            self.assertEqual(contract["sha256"], self.receipt(asset)["artifact"]["sha256"])
            self.assertEqual(report["candidate"]["source_commit"], self.receipt(asset)["port_commit"])
            self.assertNotIn("tag", report["candidate"])
            self.assertEqual(report["candidate"]["kind"], "blender-source-development")
            self.assertFalse(report["source_correspondence_verified"])
            self.assertTrue(report["source_build_receipt_verified"])

    def test_incomplete_or_foreign_build_receipts_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic")
            receipt = root / "build.json"
            invalid = {"status": "building", "upstream_commit": "a" * 40,
                       "port_commit": probe.PORT_SOURCE_SHA,
                       "canonical_patch_sha256": "a" * 64,
                       "build_mode": "APPLY", "with_buildinfo": False,
                       "artifact_kind": "release", "schema": 2}
            for field, value in invalid.items():
                with self.subTest(field=field):
                    data = self.receipt(asset)
                    data[field] = value
                    receipt.write_text(json.dumps(data))
                    with self.assertRaises(probe.Blocked):
                        probe.select_artifact_contract(
                            types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})
            for value in (0, -1, True, 2_000_000_001):
                data = self.receipt(asset)
                data["artifact"]["bytes"] = value
                receipt.write_text(json.dumps(data))
                with self.assertRaises(probe.Blocked):
                    probe.select_artifact_contract(
                        types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})

    def test_source_mode_requires_an_explicit_local_artifact(self):
        with self.assertRaises(probe.Blocked):
            probe.select_artifact_contract(
                types.SimpleNamespace(asset=None, source_build_receipt=Path("build.json")), {})

    def test_changed_source_artifact_is_refused_before_unpacking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"original bytes")
            receipt = root / "build.json"
            receipt.write_text(json.dumps(self.receipt(asset)))
            asset.write_bytes(b"modified bytes")
            args = types.SimpleNamespace(output=root, asset=asset, source_build_receipt=receipt)
            with self.assertRaisesRegex(probe.Blocked, "artifact does not match"):
                probe.probe(args, {"artifact": {}})


if __name__ == "__main__":
    unittest.main()
