"""Retrieve bounded, hash-verified outputs from an executed Blender IO suite."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_FILES = 32
# Emscripten 6.0.5 musl bits/fcntl.h: O_WRONLY=1, O_CREAT=64, O_EXCL=128.
# Its WasmFS mode-string helper has no 'wx'; numeric flags pass through.
ACK_OPEN_FLAGS = 193

BROWSER_ACK_SCRIPT = r"""({path, text, flags}) => {
    const fs = window.__bwModule?.FS;
    if (!fs || ['open', 'write', 'close', 'rename'].some(name => typeof fs[name] !== 'function')) {
        throw new Error('atomic output transfer acknowledgement API unavailable');
    }
    const bytes = new TextEncoder().encode(text);
    if (bytes.length > 16384) throw new Error('output transfer acknowledgement exceeds its bound');
    if (flags !== 193) throw new Error('output transfer acknowledgement requires exclusive create');
    const temporary = path + '.tmp';
    const stream = fs.open(temporary, flags);
    try {
        let offset = 0;
        while (offset < bytes.length) {
            const remaining = bytes.length - offset;
            const count = fs.write(stream, bytes, offset, remaining, offset);
            if (!Number.isInteger(count) || count <= 0 || count > remaining) {
                throw new Error('output transfer acknowledgement write was incomplete');
            }
            offset += count;
        }
    } finally {
        fs.close(stream);
    }
    fs.rename(temporary, path);
    return bytes.length;
}"""

BROWSER_READ_SCRIPT = r"""({path, expectedBytes}) => {
    const fs = window.__bwModule?.FS;
    if (!fs || ['lstat', 'open', 'read', 'close'].some(name => typeof fs[name] !== 'function')) {
        throw new Error('bounded engine filesystem API unavailable');
    }
    if (!Number.isSafeInteger(expectedBytes) || expectedBytes <= 0 || expectedBytes > MAX_FILE_BOUND) {
        throw new Error('generated file byte bound is invalid');
    }
    const info = fs.lstat(path);
    if ((info.mode & 0xF000) !== 0x8000 || info.size !== expectedBytes) {
        throw new Error('generated file type or byte count changed before reading');
    }
    const data = new Uint8Array(expectedBytes);
    const stream = fs.open(path, 'r');
    try {
        let offset = 0;
        while (offset < expectedBytes) {
            const remaining = expectedBytes - offset;
            const count = fs.read(stream, data, offset, remaining, offset);
            if (!Number.isInteger(count) || count <= 0 || count > remaining) {
                throw new Error('generated file ended before its declared byte count');
            }
            offset += count;
        }
        if (fs.read(stream, new Uint8Array(1), 0, 1, expectedBytes) !== 0) {
            throw new Error('generated file grew beyond its declared byte count');
        }
    } finally {
        fs.close(stream);
    }
    let binary = '';
    for (let offset = 0; offset < data.length; offset += 32768) {
        binary += String.fromCharCode(...data.subarray(offset, offset + 32768));
    }
    return btoa(binary);
}""".replace("MAX_FILE_BOUND", str(MAX_FILE_BYTES))


def validate_inventory(inventory, expected_root):
    if not isinstance(inventory, dict) or inventory.get("root") != expected_root:
        raise ValueError("generated file root differs from this execution's output directory")
    files = inventory.get("files")
    if not isinstance(files, list) or not 0 < len(files) <= MAX_FILES:
        raise ValueError("generated file inventory is missing or exceeds its file bound")
    names, total = set(), 0
    for row in files:
        if not isinstance(row, dict):
            raise ValueError("generated file inventory row is malformed")
        name, size, digest = row.get("path"), row.get("bytes"), row.get("sha256")
        if (not isinstance(name, str) or PurePosixPath(name).name != name or
                not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.blend[0-9]*", name) or name in names):
            raise ValueError("generated file name escapes, duplicates or differs from the blend-file contract")
        if type(size) is not int or not 0 < size <= MAX_FILE_BYTES:
            raise ValueError("generated file exceeds its byte bound")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("generated file has no valid SHA256")
        names.add(name)
        total += size
    if total > MAX_TOTAL_BYTES:
        raise ValueError("generated file inventory exceeds its total byte bound")
    return files


def retrieve_files(inventory, expected_root, destination, read, origin):
    """Read bytes via an engine-specific seam, then verify before preserving them."""
    rows = validate_inventory(inventory, expected_root)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    result = {"status": "verified", "origin": origin, "root": expected_root,
              "files": [], "bytes": 0, "semantic_equivalence_verified": False}
    for row in rows:
        remote_path = str(PurePosixPath(expected_root) / row["path"])
        data = read(remote_path, row["bytes"])
        if not isinstance(data, bytes):
            raise ValueError("generated file transport did not return bytes")
        observed = hashlib.sha256(data).hexdigest()
        if len(data) != row["bytes"] or observed != row["sha256"]:
            raise ValueError("generated file byte count or digest changed during transfer: " + row["path"])
        target = destination / row["path"]
        if target.exists() or target.is_symlink():
            raise ValueError("generated file destination already exists: " + row["path"])
        target.write_bytes(data)
        result["files"].append({"path": row["path"], "bytes": len(data), "sha256": observed})
        result["bytes"] += len(data)
    return result


def native_reader(root):
    root = Path(root).resolve()
    def read(path, expected_bytes):
        candidate = Path(path)
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(root) or not candidate.is_file():
            raise ValueError("native generated output is not a confined regular file")
        with candidate.open("rb") as stream:
            return stream.read(expected_bytes + 1)
    return read


def browser_reader(page):
    def read(path, expected_bytes):
        encoded = page.evaluate(BROWSER_READ_SCRIPT, {"path": path, "expectedBytes": expected_bytes})
        if not isinstance(encoded, str) or len(encoded) > ((expected_bytes + 2) // 3) * 4:
            raise ValueError("browser generated file transport exceeded its byte bound")
        return base64.b64decode(encoded, validate=True)
    return read


def acknowledge_browser_transfer(page, handshake, execution_root, token, transfer):
    """Release the background worker only after bounded output retrieval ends."""
    expected_path = str(PurePosixPath(execution_root) / "transfer-ack.json")
    if (not isinstance(handshake, dict) or handshake.get("required") is not True or
            handshake.get("protocol") != "blended-output-transfer-v1" or
            handshake.get("ack_path") != expected_path or handshake.get("token") != token or
            handshake.get("timeout_seconds") != 60 or
            type(handshake.get("exclusive_create_flags")) is not int or
            handshake.get("exclusive_create_flags") != ACK_OPEN_FLAGS):
        raise ValueError("output transfer acknowledgement is not bound to this execution")
    verified = isinstance(transfer, dict) and transfer.get("status") == "verified"
    files = validate_inventory(transfer, execution_root + "/files") if verified else []
    payload = {"protocol": handshake["protocol"], "token": token,
               "status": "verified" if verified else "failed", "files": files}
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    encoded = text.encode("utf-8")
    if len(encoded) > 16384:
        raise ValueError("output transfer acknowledgement exceeds its byte bound")
    written = page.evaluate(BROWSER_ACK_SCRIPT, {"path": expected_path, "text": text, "flags": ACK_OPEN_FLAGS})
    if written != len(encoded):
        raise ValueError("output transfer acknowledgement byte count changed")
    return {"status": "sent", "transfer_status": payload["status"],
            "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}
