"""Source resource integrity checks; these are not Blender feature tests."""
import base64
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools import upstream_resources as resources


def metadata(path, data):
    return {"upstream_path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "git_blob_sha1": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}


class SourceResourceTests(unittest.TestCase):
    def test_original_resource_tree_is_preserved_and_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b"original documentation helper\n"
            row = metadata("doc/python_api/helper.py", data)
            path = root / "input" / row["upstream_path"]
            path.parent.mkdir(parents=True)
            path.write_bytes(data)
            payloads = resources.prepare_resources([row], "a" * 40, root / "work", root / "input")
            self.assertEqual(base64.b64decode(payloads[0]["source_b64"]), data)
            saved = resources.preserve_resources(payloads, root / "saved")
            self.assertEqual(saved["files"], [row])
            self.assertEqual((root / "saved" / row["upstream_path"]).read_bytes(), data)
            path.write_bytes(b"changed documentation helper!\n")
            with self.assertRaises(ValueError):
                resources.prepare_resources([row], "a" * 40, root / "other", root / "input")

    def test_escapes_duplicates_and_oversized_resources_are_rejected(self):
        row = metadata("doc/python_api/helper.py", b"original")
        for rows in ([{**row, "upstream_path": "doc/python_api/../../outside.py"}], [row, row],
                     [{**row, "bytes": resources.MAX_FILE_BYTES + 1}]):
            with self.assertRaises(ValueError):
                resources.validate_resources(rows)

    def test_empty_original_git_blob_is_supported_without_weakening_hash_identity(self):
        row = metadata("doc/python_api/empty.txt", b"")
        self.assertEqual(resources.validate_resources([row]), [row])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resources.preserve_resources([{**row, "source_b64": ""}], root)
            self.assertEqual((root / row["upstream_path"]).read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
