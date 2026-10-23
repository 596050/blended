"""Stage a hash-bound original source resource tree without editing its files."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path, PurePosixPath
import re
import urllib.request

try:
    from .probe_blender_fixtures import _download_rows
except ImportError:
    from probe_blender_fixtures import _download_rows

MAX_FILES = 512
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PATH = re.compile(r"[A-Za-z0-9_.+/-]+")


def validate_resources(rows):
    if not isinstance(rows, list) or len(rows) > MAX_FILES:
        raise ValueError("original resource inventory exceeds its count bound")
    paths, total = set(), 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("original resource metadata must be an object")
        path = row.get("upstream_path")
        if (not isinstance(path, str) or not _PATH.fullmatch(path) or PurePosixPath(path).is_absolute() or
                any(part in ("", ".", "..") for part in path.split("/")) or path in paths or
                not path.startswith(("doc/python_api/", "scripts/templates_py/", "source/blender/"))):
            raise ValueError("original resource path escapes its source tree or is duplicated")
        paths.add(path)
        if type(row.get("bytes")) is not int or not 0 <= row["bytes"] <= MAX_FILE_BYTES:
            raise ValueError("original resource byte count exceeds its bound")
        if not isinstance(row.get("sha256"), str) or not _SHA256.fullmatch(row["sha256"]):
            raise ValueError("original resource checksum is missing")
        total += row["bytes"]
        if total > MAX_TOTAL_BYTES:
            raise ValueError("original resource tree exceeds its total byte bound")
        if "lfs_pointer" in row:
            pointer = row["lfs_pointer"]
            text = pointer.get("text") if isinstance(pointer, dict) else None
            expected = "version https://git-lfs.github.com/spec/v1\noid sha256:" + row["sha256"] + "\nsize " + str(row["bytes"]) + "\n"
            if text != expected or pointer.get("bytes") != len(expected) or pointer.get("sha256") != hashlib.sha256(expected.encode()).hexdigest():
                raise ValueError("original resource LFS pointer changed")
            blob = hashlib.sha1(b"blob " + str(len(expected)).encode() + b"\0" + expected.encode()).hexdigest()
            if row.get("git_blob_sha1") != blob:
                raise ValueError("original resource LFS Git blob identity changed")
        elif not isinstance(row.get("git_blob_sha1"), str) or not re.fullmatch(r"[0-9a-f]{40}", row["git_blob_sha1"]):
            raise ValueError("original resource Git blob identity is missing")
    return rows


def _checked_path(root, relative):
    root = Path(root).resolve()
    target = root / relative
    if not target.resolve().is_relative_to(root) or any(p.is_symlink() for p in (target, *target.parents) if p.is_relative_to(root)):
        raise ValueError("original resource path follows a symlink outside its fixed tree")
    return target


def prepare_resources(rows, upstream_sha, work_root, local_root=None):
    validate_resources(rows)
    payloads = []
    for row in rows:
        if local_root is not None:
            source = _checked_path(local_root, row["upstream_path"])
            if not source.is_file() or source.stat().st_size != row["bytes"]:
                raise ValueError("original resource is missing or changed: " + row["upstream_path"])
            data = source.read_bytes()
        elif "lfs_pointer" in row:
            data = _download_rows([{**row, "relative_path": row["upstream_path"]}])[0]
        else:
            url = "https://raw.githubusercontent.com/blender/blender/" + upstream_sha + "/" + row["upstream_path"]
            with urllib.request.urlopen(url, timeout=45) as response:
                data = response.read(row["bytes"] + 1)
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("original resource bytes differ from the pinned source: " + row["upstream_path"])
        if "lfs_pointer" not in row and hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != row["git_blob_sha1"]:
            raise ValueError("original resource Git blob identity differs: " + row["upstream_path"])
        destination = _checked_path(work_root, row["upstream_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        payloads.append({**row, "source_b64": base64.b64encode(data).decode("ascii")})
    return payloads


def preserve_resources(payloads, destination):
    rows = [{key: value for key, value in payload.items() if key != "source_b64"} for payload in payloads]
    validate_resources(rows)
    for row, payload in zip(rows, payloads, strict=True):
        data = base64.b64decode(payload["source_b64"], validate=True)
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("original resource changed after transport")
        target = _checked_path(destination, row["upstream_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {"status": "passed", "files": rows, "total_bytes": sum(row["bytes"] for row in rows)}
