#!/usr/bin/env python3
"""Transport exact pinned Blender test fixtures without changing their bytes.

Returned payloads retain the supplied metadata and add only ``source_b64``.
Downloaded LFS action URLs and headers are used in memory and never persisted.
This module establishes fixture transport integrity, not Blender test coverage.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import urllib.parse
import urllib.request


LFS_BATCH_URL = "https://projects.blender.org/blender/blender.git/info/lfs/objects/batch"
MAX_FIXTURES = 256
MAX_FIXTURE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_POINTER_BYTES = 1024
MAX_BATCH_BYTES = 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 45
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_RELATIVE = re.compile(r"[A-Za-z0-9_.+\-/]+")
_POINTER = re.compile(
    r"version https://git-lfs.github.com/spec/v1\n"
    r"oid sha256:([0-9a-f]{64})\nsize ([1-9][0-9]*)\n"
)


class FixtureError(ValueError):
    """The supplied fixture metadata, transport, or destination is invalid."""


def _require(condition, reason):
    if not condition:
        raise FixtureError(reason)


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "LFS response contains a duplicate JSON field")
        result[key] = value
    return result


def _validate_rows(rows, upstream_sha=None, *, payloads=False):
    _require(isinstance(rows, (list, tuple)) and 0 < len(rows) <= MAX_FIXTURES,
             "fixture inventory is empty or exceeds its count bound")
    if upstream_sha is not None:
        _require(isinstance(upstream_sha, str) and _COMMIT.fullmatch(upstream_sha),
                 "fixture upstream commit must be a full lowercase Git commit")
    paths, objects, pins, total = set(), {}, set(), 0
    validated = []
    for row in rows:
        _require(isinstance(row, dict), "fixture metadata must be an object")
        relative = row.get("relative_path")
        _require(isinstance(relative, str) and _RELATIVE.fullmatch(relative),
                 "fixture relative path contains invalid characters")
        parts = relative.split("/")
        _require(not PurePosixPath(relative).is_absolute() and all(part not in ("", ".", "..") for part in parts),
                 "fixture relative path is not canonical or escapes its root")
        _require(relative not in paths, "duplicate fixture relative path")
        paths.add(relative)
        source_path = "tests/files/" + relative
        _require(row.get("upstream_path") == source_path, "fixture path differs from its tests/files source")
        source_url = row.get("upstream_url")
        match = re.fullmatch(r"https://github\.com/blender/blender/blob/([0-9a-f]{40})/" + re.escape(source_path),
                             source_url) if isinstance(source_url, str) else None
        _require(match is not None, "fixture source URL does not identify its exact upstream path and commit")
        pin = match.group(1)
        _require(upstream_sha is None or pin == upstream_sha, "fixture source commit differs from the requested upstream pin")
        pins.add(pin)
        _require(row.get("lfs_batch_url") == LFS_BATCH_URL, "fixture LFS endpoint differs from the pinned Blender endpoint")
        size, digest = row.get("bytes"), row.get("sha256")
        _require(type(size) is int and 0 < size <= MAX_FIXTURE_BYTES, "fixture byte count exceeds its bound or is invalid")
        _require(isinstance(digest, str) and _SHA256.fullmatch(digest), "fixture SHA-256 is invalid")
        # Different upstream paths may legitimately contain the same LFS object.
        # The path is the fixture identity; its content identity may be shared.
        _require(digest not in objects or objects[digest] == size,
                 "shared fixture object has inconsistent byte counts")
        objects[digest] = size
        total += size
        _require(total <= MAX_TOTAL_BYTES, "fixture inventory exceeds its total byte bound")
        pointer = row.get("lfs_pointer")
        _require(isinstance(pointer, dict), "fixture has no pinned LFS pointer")
        text = pointer.get("text")
        _require(isinstance(text, str) and len(text) <= MAX_POINTER_BYTES, "fixture pointer text exceeds its bound or is invalid")
        try:
            raw = text.encode("ascii")
        except UnicodeEncodeError as error:
            raise FixtureError("fixture pointer is not ASCII") from error
        _require(type(pointer.get("bytes")) is int and pointer["bytes"] == len(raw), "fixture pointer byte count changed")
        _require(pointer.get("sha256") == hashlib.sha256(raw).hexdigest(), "fixture pointer digest changed")
        parsed = _POINTER.fullmatch(text)
        _require(parsed is not None, "fixture pointer is not canonical Git LFS pointer text")
        _require(parsed.group(1) == digest and int(parsed.group(2)) == size, "fixture pointer object identity differs from fixture metadata")
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        _require(row.get("git_blob_sha1") == git_blob and pointer.get("git_blob_sha1") == git_blob,
                 "fixture pointer Git blob identity changed")
        obj = row.get("lfs_object")
        _require(isinstance(obj, dict) and obj.get("oid") == "sha256:" + digest and
                 obj.get("sha256") == digest and type(obj.get("bytes")) is int and obj["bytes"] == size,
                 "fixture LFS object metadata differs from its pointer")
        if payloads:
            encoded = row.get("source_b64")
            _require(isinstance(encoded, str) and len(encoded) == 4 * ((size + 2) // 3),
                     "fixture base64 payload length differs from the pinned size")
        else:
            _require("source_b64" not in row, "fixture metadata already contains a payload")
        validated.append(row)
    _require(len(pins) == 1, "fixture inventory mixes upstream source commits")
    return validated


def _directory_root(value, *, create):
    root = Path(value)
    _require(".." not in root.parts, "fixture root contains parent traversal")
    root = Path(os.path.abspath(root))
    for part in reversed((root, *root.parents)):
        _require(not part.is_symlink(), "fixture directory path contains a symlink")
        if part.exists():
            _require(part.is_dir(), "fixture directory path contains a non-directory")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    _require(root.is_dir(), "fixture directory is missing")
    return root


def _confined_path(root, relative):
    path = root
    parts = relative.split("/")
    for index, name in enumerate(parts):
        path = path / name
        _require(not path.is_symlink(), "fixture path contains a symlink: " + relative)
        if index < len(parts) - 1 and path.exists():
            _require(path.is_dir(), "fixture parent is not a directory: " + relative)
    _require(path.is_relative_to(root), "fixture path escapes its root")
    return path


def _bounded_read(stream, limit, label):
    result = bytearray()
    while len(result) <= limit:
        chunk = stream.read(min(64 * 1024, limit + 1 - len(result)))
        if not chunk:
            return bytes(result)
        _require(isinstance(chunk, bytes), label + " returned non-byte data")
        result.extend(chunk)
    raise FixtureError(label + " exceeds its byte bound")


def _verify_bytes(data, row):
    _require(len(data) == row["bytes"], "fixture object byte count changed: " + row["relative_path"])
    _require(hashlib.sha256(data).hexdigest() == row["sha256"], "fixture object digest changed: " + row["relative_path"])
    return data


def _read_local(root, row):
    path = _confined_path(root, row["relative_path"])
    _require(path.is_file(), "local fixture is missing or not a regular file: " + row["relative_path"])
    _require(path.stat().st_size == row["bytes"], "local fixture object byte count changed: " + row["relative_path"])
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise FixtureError("cannot open confined local fixture: " + row["relative_path"]) from error
    with os.fdopen(descriptor, "rb") as stream:
        _require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "local fixture is not a regular file")
        return _verify_bytes(_bounded_read(stream, row["bytes"], "local fixture"), row)


def _download_rows(rows):
    expected = {row["sha256"]: row for row in rows}
    body = {"operation": "download", "transfers": ["basic"],
            "objects": [{"oid": row["sha256"], "size": row["bytes"]} for row in expected.values()]}
    request = urllib.request.Request(LFS_BATCH_URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json"})
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            raw = _bounded_read(response, MAX_BATCH_BYTES, "LFS batch response")
    except FixtureError:
        raise
    except Exception:
        raise FixtureError("official Blender LFS batch request failed") from None
    try:
        batch = json.loads(raw, object_pairs_hook=_unique_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FixtureError("LFS batch response is not complete valid JSON") from error
    _require(isinstance(batch, dict) and batch.get("transfer", "basic") == "basic", "LFS response has an unsupported transfer")
    returned = batch.get("objects")
    _require(isinstance(returned, list) and len(returned) == len(expected), "LFS batch returned a missing or extra fixture object")
    actions = {}
    for obj in returned:
        _require(isinstance(obj, dict), "LFS returned a malformed object")
        oid = obj.get("oid")
        _require(isinstance(oid, str) and oid in expected and oid not in actions,
                 "LFS returned a duplicate or unexpected fixture object")
        _require(type(obj.get("size")) is int and obj["size"] == expected[oid]["bytes"], "LFS returned a changed fixture object size")
        _require("error" not in obj, "LFS server reported a fixture object error")
        action_group = obj.get("actions")
        action = action_group.get("download") if isinstance(action_group, dict) else None
        _require(isinstance(action, dict), "LFS fixture has no download action")
        href, headers = action.get("href"), action.get("header", {})
        _require(isinstance(href, str) and len(href) <= 16384, "LFS download URL is missing or exceeds its bound")
        try:
            url = urllib.parse.urlsplit(href)
            valid_url = url.scheme == "https" and bool(url.hostname) and url.username is None and url.password is None and not url.fragment
        except ValueError:
            valid_url = False
        _require(valid_url, "LFS download action is not a valid HTTPS URL")
        _require(isinstance(headers, dict) and len(headers) <= 32 and
                 all(isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9-]+", key) and isinstance(value, str) and
                     len(value) <= 16384 and "\r" not in value and "\n" not in value for key, value in headers.items()),
                 "LFS download headers are malformed or exceed their bound")
        actions[oid] = (href, headers)
    downloaded = {}
    for row in expected.values():
        href, headers = actions[row["sha256"]]
        try:
            request = urllib.request.Request(href, headers=headers)
            with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                data = _bounded_read(response, row["bytes"], "LFS fixture object")
        except FixtureError:
            raise
        except Exception:
            # Exception text can contain signed action URLs or authorization headers.
            raise FixtureError("LFS fixture download failed: " + row["relative_path"]) from None
        downloaded[row["sha256"]] = _verify_bytes(data, row)
    return [downloaded[row["sha256"]] for row in rows]


def _write_tree(rows, contents, destination):
    root = _directory_root(destination, create=True)
    for row in rows:
        path = _confined_path(root, row["relative_path"])
        _require(not path.exists(), "fixture destination already exists; refusing to clobber: " + row["relative_path"])
    for row, data in zip(rows, contents, strict=True):
        path = _confined_path(root, row["relative_path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path = _confined_path(root, row["relative_path"])
        try:
            with path.open("xb") as stream:
                stream.write(data)
        except FileExistsError as error:
            raise FixtureError("fixture destination already exists; refusing to clobber") from error
        _read_local(root, row)
    return root


def prepare_fixture_payloads(rows, upstream_sha, work_root, local_root=None):
    """Verify and materialize pinned object bytes, returning metadata plus base64.

    ``local_root`` selects a strictly local mode with no network requests. Both
    modes refuse existing destination files and all observed symlink components.
    """
    validated = _validate_rows(rows, upstream_sha)
    if local_root is not None:
        local = _directory_root(local_root, create=False)
        contents = [_read_local(local, row) for row in validated]
    else:
        contents = _download_rows(validated)
    _write_tree(validated, contents, work_root)
    return [{**copy.deepcopy(row), "source_b64": base64.b64encode(data).decode("ascii")}
            for row, data in zip(validated, contents, strict=True)]


def preserve_fixture_payloads(payloads, destination):
    """Save the same verified input tree without clobbering any existing file."""
    rows = _validate_rows(payloads, payloads=True)
    contents = []
    for row in rows:
        try:
            data = base64.b64decode(row["source_b64"], validate=True)
        except (ValueError, UnicodeEncodeError) as error:
            raise FixtureError("fixture payload is not valid base64") from error
        contents.append(_verify_bytes(data, row))
    root = _write_tree(rows, contents, destination)
    return {"status": "verified", "origin": "pinned-upstream-fixtures", "root": str(root),
            "files": [{"path": row["relative_path"], "bytes": row["bytes"], "sha256": row["sha256"],
                       "upstream_path": row["upstream_path"]} for row in rows],
            "bytes": sum(row["bytes"] for row in rows)}
