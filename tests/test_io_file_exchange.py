"""Require exact bytes when retrieving files made by the original IO suite."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools import probe_io_files as exchange


class IOFileExchangeTests(unittest.TestCase):
    def inventory(self, data=b"synthetic blend bytes"):
        return {"root": "/tmp/blended-test/files", "files": [
            {"path": "scene.blend", "bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest()}]}

    def test_saved_file_must_match_the_bytes_observed_inside_blender(self):
        data = b"synthetic blend bytes"
        calls = []
        def read(path, size):
            calls.append((path, size))
            return data
        with tempfile.TemporaryDirectory() as directory:
            result = exchange.retrieve_files(self.inventory(data), "/tmp/blended-test/files",
                                            Path(directory), read, "synthetic")
            self.assertEqual((Path(directory) / "scene.blend").read_bytes(), data)
            self.assertEqual(calls, [("/tmp/blended-test/files/scene.blend", len(data))])
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["files"][0]["sha256"], hashlib.sha256(data).hexdigest())

    def test_wrong_root_or_escaping_name_is_refused_before_file_access(self):
        for field, value in (("root", "/tmp/another-run"), ("path", "../scene.blend"),
                             ("path", "/scene.blend"), ("path", "sub/scene.blend")):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                inventory = self.inventory()
                if field == "root":
                    inventory[field] = value
                else:
                    inventory["files"][0][field] = value
                with self.assertRaises(ValueError):
                    exchange.retrieve_files(inventory, "/tmp/blended-test/files", Path(directory),
                                            lambda *_: self.fail("must not read an unbound path"), "synthetic")

    def test_changed_bytes_cannot_be_saved_as_verified_blender_output(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "digest"):
                exchange.retrieve_files(self.inventory(), "/tmp/blended-test/files", Path(directory),
                                        lambda *_: b"changed Blender bytes", "synthetic")
            self.assertFalse((Path(directory) / "scene.blend").exists())

    def test_missing_duplicate_and_oversized_inventory_is_rejected(self):
        for defect in ("empty", "duplicate", "oversized"):
            with self.subTest(defect=defect):
                inventory = self.inventory()
                if defect == "empty":
                    inventory["files"] = []
                elif defect == "duplicate":
                    inventory["files"] *= 2
                else:
                    inventory["files"][0]["bytes"] = 100_000_000
                with self.assertRaises(ValueError):
                    exchange.validate_inventory(inventory, "/tmp/blended-test/files")

    def test_browser_reads_are_bounded_even_if_file_grows_after_stat(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required to execute the actual browser transport function")
        script = "const read = " + exchange.BROWSER_READ_SCRIPT + ";\n" + r'''
const results = [];
for (const scenario of ['valid', 'already-large', 'grew']) {
    const data = new Uint8Array(scenario === 'valid' ? [1, 2, 3] : [1, 2, 3, 4]);
    let opens = 0, closed = 0;
    const requests = [];
    global.window = {__bwModule: {FS: {
        lstat: () => ({size: scenario === 'already-large' ? 4 : 3, mode: 0x8000}),
        open: () => {opens++; return {fd: 1};},
        read: (stream, target, offset, length, position) => {
            requests.push({length, position});
            const chunk = data.subarray(position, position + length);
            target.set(chunk, offset);
            return chunk.length;
        },
        close: () => {closed++;}
    }}};
    let value = null, error = null;
    try { value = read({path: '/tmp/fixed/scene.blend', expectedBytes: 3}); }
    catch (caught) { error = String(caught); }
    results.push({scenario, opens, closed, requests, value, error});
}
console.log(JSON.stringify(results));
'''
        completed = subprocess.run([node], input=script, text=True, capture_output=True, check=True, timeout=10)
        valid, oversized, grew = json.loads(completed.stdout)
        self.assertEqual(valid["value"], "AQID")
        self.assertEqual(valid["closed"], 1)
        self.assertEqual((oversized["opens"], oversized["requests"]), (0, []))
        self.assertIsNotNone(oversized["error"])
        self.assertIsNotNone(grew["error"])
        self.assertEqual(grew["closed"], 1)
        self.assertEqual(grew["requests"], [{"length": 3, "position": 0}, {"length": 1, "position": 3}])


if __name__ == "__main__":
    unittest.main()
