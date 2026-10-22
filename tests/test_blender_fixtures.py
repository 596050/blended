"""Transport contracts; synthetic object bytes are not Blender feature evidence."""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import probe_blender_fixtures as fixtures


PIN = "fbe6228777e7d9afefcd61a413844e790ae75db7"


def metadata(relative, data):
    digest = hashlib.sha256(data).hexdigest()
    text = f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {len(data)}\n"
    pointer = text.encode("ascii")
    blob = hashlib.sha1(b"blob " + str(len(pointer)).encode("ascii") + b"\0" + pointer).hexdigest()
    path = "tests/files/" + relative
    return {"upstream_path": path, "relative_path": relative, "sha256": digest, "bytes": len(data),
            "git_blob_sha1": blob, "upstream_url": f"https://github.com/blender/blender/blob/{PIN}/{path}",
            "lfs_pointer": {"text": text, "bytes": len(pointer), "sha256": hashlib.sha256(pointer).hexdigest(),
                            "git_blob_sha1": blob},
            "lfs_object": {"oid": "sha256:" + digest, "sha256": digest, "bytes": len(data)},
            "lfs_batch_url": fixtures.LFS_BATCH_URL}


class ObservedStream(io.BytesIO):
    def __init__(self, value):
        super().__init__(value)
        self.bytes_read = 0
        self.requested_sizes = []

    def read(self, size=-1):
        self.requested_sizes.append(size)
        value = super().read(size)
        self.bytes_read += len(value)
        return value


class BlenderFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = [b"first pinned synthetic fixture", b"second pinned synthetic fixture"]
        self.rows = [metadata("images/test.jpg", self.data[0]), metadata("libraries/test.blend", self.data[1])]
        self.local = self.root / "local"
        for row, value in zip(self.rows, self.data, strict=True):
            path = self.local / row["relative_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)

    def batch(self, rows=None):
        return {"transfer": "basic", "objects": [
            {"oid": row["sha256"], "size": row["bytes"], "actions": {"download": {
                "href": "https://objects.example.invalid/" + row["sha256"] + "?signed=ephemeral-secret",
                "header": {"Authorization": "ephemeral-download-header"}}}}
            for row in (self.rows if rows is None else rows)]}

    def response(self, batch):
        return ObservedStream(json.dumps(batch).encode())

    def test_local_objects_are_verified_materialized_and_payloads_leave_metadata_unchanged(self):
        before = copy.deepcopy(self.rows)
        with mock.patch.object(fixtures.urllib.request, "urlopen") as network:
            payloads = fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)
        network.assert_not_called()
        self.assertEqual(self.rows, before)
        for row, payload, data in zip(self.rows, payloads, self.data, strict=True):
            self.assertEqual({key: value for key, value in payload.items() if key != "source_b64"}, row)
            self.assertEqual(base64.b64decode(payload["source_b64"], validate=True), data)
            self.assertEqual((self.root / "work" / row["relative_path"]).read_bytes(), data)
        payloads[0]["lfs_pointer"]["text"] = "changed copy"
        self.assertEqual(self.rows, before)

    def test_changed_and_missing_local_objects_fail_without_network_or_output(self):
        path = self.local / self.rows[0]["relative_path"]
        path.write_bytes(b"x" * self.rows[0]["bytes"])
        with mock.patch.object(fixtures.urllib.request, "urlopen") as network:
            with self.assertRaisesRegex(fixtures.FixtureError, "digest"):
                fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)
            path.unlink()
            with self.assertRaisesRegex(fixtures.FixtureError, "missing"):
                fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)
        network.assert_not_called()
        self.assertFalse((self.root / "work").exists())

    def test_pointer_text_hash_size_blob_and_object_identity_are_independently_bound(self):
        edits = [
            lambda row: row["lfs_pointer"].update(sha256="0" * 64),
            lambda row: row["lfs_pointer"].update(bytes=row["lfs_pointer"]["bytes"] + 1),
            lambda row: row.update(git_blob_sha1="0" * 40),
            lambda row: row["lfs_object"].update(bytes=row["bytes"] + 1),
            lambda row: row.update(bytes=row["bytes"] + 1),
        ]
        for edit in edits:
            with self.subTest(edit=edit):
                rows = copy.deepcopy(self.rows)
                edit(rows[0])
                with self.assertRaisesRegex(fixtures.FixtureError, "pointer|object"):
                    fixtures.prepare_fixture_payloads(rows, PIN, self.root / "work", self.local)
        rows = copy.deepcopy(self.rows)
        rows[0]["lfs_pointer"]["text"] = "version https://git-lfs.github.com/spec/v1\noid sha256:" + "a" * 64 + f"\nsize {rows[0]['bytes']}\n"
        pointer = rows[0]["lfs_pointer"]["text"].encode()
        rows[0]["lfs_pointer"]["sha256"] = hashlib.sha256(pointer).hexdigest()
        with self.assertRaisesRegex(fixtures.FixtureError, "object identity"):
            fixtures.prepare_fixture_payloads(rows, PIN, self.root / "work", self.local)

    def test_path_escape_noncanonical_paths_duplicate_inventory_and_wrong_pin_are_rejected(self):
        for name in ("../outside.blend", "/outside.blend", "a/../outside.blend", "a//file.blend", "a\\file.blend"):
            with self.subTest(path=name):
                rows = [metadata(name, self.data[0])]
                with self.assertRaisesRegex(fixtures.FixtureError, "path"):
                    fixtures.prepare_fixture_payloads(rows, PIN, self.root / "work", self.local)
        with self.assertRaisesRegex(fixtures.FixtureError, "duplicate"):
            fixtures.prepare_fixture_payloads([self.rows[0], self.rows[0]], PIN, self.root / "work", self.local)
        with self.assertRaisesRegex(fixtures.FixtureError, "commit"):
            fixtures.prepare_fixture_payloads(self.rows, "a" * 40, self.root / "work", self.local)

    def test_local_and_destination_symlink_components_are_rejected(self):
        alias = self.root / "alias"
        alias.symlink_to(self.local, target_is_directory=True)
        with self.assertRaisesRegex(fixtures.FixtureError, "symlink"):
            fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", alias)
        path = self.local / self.rows[0]["relative_path"]
        path.unlink()
        target = self.root / "outside.jpg"
        target.write_bytes(self.data[0])
        path.symlink_to(target)
        with self.assertRaisesRegex(fixtures.FixtureError, "symlink"):
            fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)
        path.unlink()
        path.write_bytes(self.data[0])
        work = self.root / "work"
        work.mkdir()
        (work / "images").symlink_to(self.local / "images", target_is_directory=True)
        with self.assertRaisesRegex(fixtures.FixtureError, "symlink"):
            fixtures.prepare_fixture_payloads(self.rows, PIN, work, self.local)
        self.assertEqual((self.local / self.rows[0]["relative_path"]).read_bytes(), self.data[0])

    def test_real_lfs_batch_shape_downloads_exact_objects_without_persisting_actions(self):
        batch = self.batch()
        # The batch response order is not the fixture path order.
        batch["objects"].reverse()
        responses = [self.response(batch), *[ObservedStream(value) for value in self.data]]
        with mock.patch.object(fixtures.urllib.request, "urlopen", side_effect=responses) as network:
            payloads = fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work")
        self.assertEqual(network.call_count, 3)
        request = network.call_args_list[0].args[0]
        self.assertEqual(request.full_url, fixtures.LFS_BATCH_URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data), {"operation": "download", "transfers": ["basic"],
            "objects": [{"oid": row["sha256"], "size": row["bytes"]} for row in self.rows]})
        for call in network.call_args_list[1:]:
            self.assertEqual(call.args[0].get_header("Authorization"), "ephemeral-download-header")
        rendered = json.dumps(payloads)
        self.assertNotIn("ephemeral-secret", rendered)
        self.assertNotIn("ephemeral-download-header", rendered)
        self.assertEqual({path.relative_to(self.root / "work").as_posix() for path in (self.root / "work").rglob("*") if path.is_file()},
                         {row["relative_path"] for row in self.rows})

    def test_missing_duplicate_changed_and_unknown_batch_objects_prevent_any_download(self):
        batches = []
        missing = self.batch(); missing["objects"].pop(); batches.append(missing)
        duplicate = self.batch(); duplicate["objects"][1] = duplicate["objects"][0]; batches.append(duplicate)
        changed = self.batch(); changed["objects"][0]["size"] += 1; batches.append(changed)
        unknown = self.batch(); unknown["objects"][0]["oid"] = "0" * 64; batches.append(unknown)
        for batch in batches:
            with self.subTest(batch=batch), mock.patch.object(fixtures.urllib.request, "urlopen", return_value=self.response(batch)) as network:
                with self.assertRaisesRegex(fixtures.FixtureError, "object"):
                    fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work")
                self.assertEqual(network.call_count, 1)
                self.assertFalse((self.root / "work").exists())

    def test_download_tampering_and_oversize_fail_with_bounded_reads(self):
        for data, message in ((b"x" * self.rows[0]["bytes"], "digest"), (self.data[0] + b"extra" * 1000, "bound")):
            download = ObservedStream(data)
            with self.subTest(message=message), mock.patch.object(fixtures.urllib.request, "urlopen",
                    side_effect=[self.response(self.batch()), download]):
                with self.assertRaisesRegex(fixtures.FixtureError, message):
                    fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work")
            self.assertLessEqual(download.bytes_read, self.rows[0]["bytes"] + 1)
            self.assertTrue(all(size >= 0 for size in download.requested_sizes))
            self.assertFalse((self.root / "work").exists())

    def test_batch_response_is_bounded_and_duplicate_json_fields_fail(self):
        oversized = ObservedStream(b" " * (fixtures.MAX_BATCH_BYTES + 100))
        with mock.patch.object(fixtures.urllib.request, "urlopen", return_value=oversized):
            with self.assertRaisesRegex(fixtures.FixtureError, "bound"):
                fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work")
        self.assertEqual(oversized.bytes_read, fixtures.MAX_BATCH_BYTES + 1)
        duplicate = ObservedStream(b'{"objects":[],"objects":[]}')
        with mock.patch.object(fixtures.urllib.request, "urlopen", return_value=duplicate):
            with self.assertRaisesRegex(fixtures.FixtureError, "duplicate JSON"):
                fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work")

    def test_preservation_rechecks_exact_payload_tree_and_refuses_clobbering(self):
        payloads = fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)
        saved = fixtures.preserve_fixture_payloads(payloads, self.root / "output" / "fixtures")
        self.assertEqual(saved["status"], "verified")
        self.assertEqual(saved["bytes"], sum(len(value) for value in self.data))
        self.assertEqual({row["path"] for row in saved["files"]}, {row["relative_path"] for row in self.rows})
        for row, value in zip(self.rows, self.data, strict=True):
            self.assertEqual((Path(saved["root"]) / row["relative_path"]).read_bytes(), value)
        with self.assertRaisesRegex(fixtures.FixtureError, "clobber"):
            fixtures.preserve_fixture_payloads(payloads, Path(saved["root"]))
        with self.assertRaisesRegex(fixtures.FixtureError, "clobber"):
            fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)

    def test_preservation_rejects_changed_payload_and_destination_symlink(self):
        payloads = fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work", self.local)
        changed = copy.deepcopy(payloads)
        changed[0]["source_b64"] = base64.b64encode(b"x" * changed[0]["bytes"]).decode()
        with self.assertRaisesRegex(fixtures.FixtureError, "digest"):
            fixtures.preserve_fixture_payloads(changed, self.root / "changed")
        self.assertFalse((self.root / "changed").exists())
        (self.root / "linked").symlink_to(self.local, target_is_directory=True)
        with self.assertRaisesRegex(fixtures.FixtureError, "symlink"):
            fixtures.preserve_fixture_payloads(payloads, self.root / "linked")

    def test_network_errors_do_not_expose_signed_action_urls_or_headers(self):
        secret_error = RuntimeError("https://objects.invalid/?signed=ephemeral-secret Authorization=ephemeral-download-header")
        with mock.patch.object(fixtures.urllib.request, "urlopen", side_effect=[self.response(self.batch()), secret_error]):
            with self.assertRaises(fixtures.FixtureError) as caught:
                fixtures.prepare_fixture_payloads(self.rows, PIN, self.root / "work")
        self.assertNotIn("ephemeral", str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)


if __name__ == "__main__":
    unittest.main()
