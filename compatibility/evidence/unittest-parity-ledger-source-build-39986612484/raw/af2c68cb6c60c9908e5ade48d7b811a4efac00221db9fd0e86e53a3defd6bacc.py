#!/usr/bin/env python3
"""Assemble and verify an explicit original-resource overlay for a browser package.

Only the generated Emscripten preload data and its metadata may change. The
verifier compares the augmented archive against the actual original archive,
including every unchanged member and the byte prefix of the preload data.
No Blender test runs here and no source-build receipt is rewritten.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile

PLAN_PATH = Path(__file__).resolve().parents[1] / "compatibility/package-overlays/essentials-brushes-5.2.json"
PLAN_SHA256 = "3face96d93404046a15b0a22d77f25711997039a374d14d6458d547fd57483dd"
UPSTREAM_COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"
MAX_ARCHIVE_BYTES = 2_000_000_000
MAX_MEMBER_BYTES = 512_000_000
JS_INTEGER = r"(?:0|[1-9][0-9]*)(?:e(?:0|[1-9][0-9]*))?"
METADATA = re.compile(r"loadPackage\(\{files:\[(.*?)\],remote_package_size:(" + JS_INTEGER + r")\}\)", re.DOTALL)
ENTRY = re.compile(r'\{filename:("(?:[^"\\]|\\.)*"),start:(' + JS_INTEGER + r'),end:(' + JS_INTEGER + r')\}')
DIRECTORY_ANCHOR = 'Module["FS_createPath"]("/bw","datafiles",true,true);'


def identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def file_identity(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("required regular file is missing: " + str(path))
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return {"bytes": path.stat().st_size, "sha256": value.hexdigest()}


def _same_identity(actual, expected):
    return (isinstance(expected, dict) and type(expected.get("bytes")) is int and
            actual == {key: expected.get(key) for key in ("bytes", "sha256")})


def _require_identity(path, expected, label):
    actual = file_identity(path)
    if not _same_identity(actual, expected):
        raise ValueError(label + " identity differs from the required bytes")
    return actual


def _read_json(path, maximum=2_000_000):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > maximum:
        raise ValueError("JSON receipt is missing or exceeds its bound: " + str(path))
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON receipt is not an object")
    return value


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def load_plan():
    observation = file_identity(PLAN_PATH)
    if observation["sha256"] != PLAN_SHA256:
        raise ValueError("reviewed package overlay manifest is missing or changed")
    return _read_json(PLAN_PATH), observation


def _safe_path(name, *, absolute=False):
    path = PurePosixPath(name)
    if (not isinstance(name, str) or not name or "\\" in name or
            path.is_absolute() != absolute or ".." in path.parts or
            path.as_posix() != name or any(ord(char) < 32 for char in name)):
        raise ValueError("unsafe or noncanonical package path: " + str(name))
    return path


def _preload_match(source):
    matches = list(METADATA.finditer(source))
    if len(matches) != 1:
        raise ValueError("expected one supported generated preload metadata block")
    return matches[0]


def _integer_token(value):
    parts = value.split("e")
    if len(parts[0]) > 10 or (len(parts) == 2 and (len(parts[1]) > 2 or int(parts[1]) > 10)):
        raise ValueError("preload integer exceeds the supported byte bound")
    number = int(parts[0]) * (10 ** int(parts[1]) if len(parts) == 2 else 1)
    if number > MAX_ARCHIVE_BYTES:
        raise ValueError("preload integer exceeds the supported byte bound")
    return number


def parse_preload(source):
    """Read one supported generated metadata literal without executing JavaScript."""
    match = _preload_match(source)
    body = match[1]
    entries, seen, position, end = [], set(), 0, 0
    while position < len(body):
        row = ENTRY.match(body, position)
        if row is None:
            raise ValueError("preload metadata contains unsupported syntax")
        name = json.loads(row[1])
        _safe_path(name, absolute=True)
        start, following = _integer_token(row[2]), _integer_token(row[3])
        if name in seen or start != end or following < start:
            raise ValueError("preload entries are duplicate, overlapping, or not contiguous")
        entries.append({"filename": name, "start": start, "end": following})
        seen.add(name)
        end = following
        position = row.end()
        if position < len(body):
            if body[position] != "," or position + 1 == len(body):
                raise ValueError("preload metadata separator is malformed")
            position += 1
    size = _integer_token(match[2])
    if not entries or end != size:
        raise ValueError("preload entry range does not match package size")
    return entries, size


def append_preload(source, base_bytes, additions):
    entries, size = parse_preload(source)
    if size != base_bytes or source.count(DIRECTORY_ANCHOR) != 1:
        raise ValueError("preload data length or directory creation anchor differs")
    known = {row["filename"] for row in entries}
    directories, suffix, cursor = set(), [], size
    for row in additions:
        path = _safe_path(row["destination"], absolute=True)
        if (not path.is_relative_to("/bw/datafiles") or str(path) in known or
                type(row.get("bytes")) is not int or not 0 < row["bytes"] <= MAX_MEMBER_BYTES):
            raise ValueError("overlay must add a unique bounded original datafile")
        known.add(str(path))
        for parent in path.parents:
            if parent == PurePosixPath("/bw/datafiles"):
                break
            directories.add(parent)
        suffix.append('{filename:' + json.dumps(str(path)) + ',start:' + str(cursor) +
                      ',end:' + str(cursor + row["bytes"]) + '}')
        cursor += row["bytes"]
    if not suffix:
        raise ValueError("overlay has no added files")
    match = _preload_match(source)
    replacement = 'loadPackage({files:[' + match[1] + ',' + ','.join(suffix) + '],remote_package_size:' + str(cursor) + '})'
    result = source[:match.start()] + replacement + source[match.end():]
    creation = ''.join('Module["FS_createPath"](' + json.dumps(str(path.parent)) + ',' +
                       json.dumps(path.name) + ',true,true);'
                       for path in sorted(directories, key=lambda value: (len(value.parts), str(value))))
    return result.replace(DIRECTORY_ANCHOR, DIRECTORY_ANCHOR + creation, 1)


def _members(archive):
    members, seen, total = {}, set(), 0
    for index, member in enumerate(archive):
        name = member.name.rstrip("/") if member.isdir() else member.name
        _safe_path(name)
        if name in seen or index >= 20_000 or not (member.isfile() or member.isdir()):
            raise ValueError("archive has duplicate, excessive, or unsupported members")
        seen.add(name)
        total += member.size
        if not 0 <= member.size <= MAX_MEMBER_BYTES or total > MAX_ARCHIVE_BYTES:
            raise ValueError("archive contents exceed their byte bound")
        if member.isfile():
            members[name] = member
    return members


def _read(archive, member):
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError("archive member cannot be read")
    with stream:
        data = stream.read()
    if len(data) != member.size:
        raise ValueError("archive member is truncated")
    return data


def _member_identity(archive, member):
    value, count = hashlib.sha256(), 0
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError("archive member cannot be read")
    with stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(block)
            value.update(block)
    if count != member.size:
        raise ValueError("archive member is truncated")
    return {"bytes": count, "sha256": value.hexdigest()}


def _layout(members):
    js = [name for name in members if name.endswith("/bin/blender_browser.js")]
    if len(js) != 1:
        raise ValueError("archive has no unambiguous supported engine layout")
    root = js[0].removesuffix("/bin/blender_browser.js")
    paths = {ext: root + "/bin/blender_browser." + ext for ext in ("js", "data", "wasm")}
    if any(path not in members for path in paths.values()):
        raise ValueError("archive is missing an engine component")
    return root, paths


def _source_contract(source_path):
    source = _read_json(source_path, maximum=5_000_000)
    if (source.get("schema") != 1 or source.get("artifact_kind") != "blender-source-development" or
            source.get("status") != "built" or source.get("upstream_commit") != UPSTREAM_COMMIT):
        raise ValueError("base source-build receipt is not the selected candidate")
    return source


def _verify_base_engines(archive, members, paths, source):
    declared = source.get("engine_files", [])
    for path in paths.values():
        rows = [row for row in declared if PurePosixPath(row.get("path", "")).name == PurePosixPath(path).name]
        if len(rows) != 1 or not _same_identity(_member_identity(archive, members[path]), rows[0]):
            raise ValueError("base engine member differs from source-build receipt: " + path)


def _inputs(plan, plan_identity, source_identity, base_identity):
    return {"schema": 1, "kind": "original-resource-preload-overlay-inputs", "overlay_id": plan["id"],
            "upstream_commit": UPSTREAM_COMMIT, "manifest": plan_identity,
            "base_source_build_receipt": source_identity, "base_artifact": base_identity,
            "additions": plan["files"], "algorithm": "append-preload-resources-v1",
            "engine_recompiled": False, "tests_modified": False}


def assemble_overlay(base_archive, source_path, asset_root, output):
    base_archive, source_path, asset_root, output = map(Path, (base_archive, source_path, asset_root, output))
    plan, plan_identity = load_plan()
    source = _source_contract(source_path)
    base_identity = _require_identity(base_archive, source.get("artifact"), "base archive")
    source_identity = file_identity(source_path)
    if base_identity["bytes"] > MAX_ARCHIVE_BYTES:
        raise ValueError("base archive exceeds its byte bound")
    payloads = []
    for row in plan["files"]:
        relative = _safe_path(row["upstream_path"])
        path = asset_root / relative
        if not path.resolve().is_relative_to(asset_root.resolve()):
            raise ValueError("original resource path escapes its root")
        _require_identity(path, row, "original resource")
        payloads.append(path.read_bytes())
    inputs = _inputs(plan, plan_identity, source_identity, base_identity)
    with tarfile.open(base_archive, "r:gz") as original:
        members = _members(original)
        root, paths = _layout(members)
        _verify_base_engines(original, members, paths, source)
        data = _read(original, members[paths["data"]])
        js = _read(original, members[paths["js"]]).decode("utf-8")
        changed_js = append_preload(js, len(data), plan["files"]).encode("utf-8")
        replacements = {paths["js"]: changed_js, paths["data"]: data + b"".join(payloads)}
        proof_path = root + "/PACKAGE-OVERLAY.json"
        if proof_path in members:
            raise ValueError("base package already contains an overlay declaration")
        replacements[proof_path] = _json_bytes(inputs)
        output.mkdir(parents=True, exist_ok=False)
        archive_path = output / "blender-source-development-essentials.tar.gz"
        with archive_path.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as assembled:
                for name in sorted(set(members) | {proof_path}):
                    info = tarfile.TarInfo(name)
                    info.mode = members[name].mode if name in members else 0o644
                    info.mtime = 0
                    if name in replacements:
                        payload = replacements[name]
                        info.size = len(payload)
                        assembled.addfile(info, io.BytesIO(payload))
                    else:
                        info.size = members[name].size
                        stream = original.extractfile(members[name])
                        if stream is None:
                            raise ValueError("original package member cannot be copied")
                        with stream:
                            assembled.addfile(info, stream)
    shutil.copyfile(source_path, output / "base-source-build.json")
    (output / "overlay-manifest.json").write_bytes(PLAN_PATH.read_bytes() if plan_identity["sha256"] == PLAN_SHA256 else _json_bytes(plan))
    receipt = {"schema": 1, "kind": "blender-browser-package-overlay", "status": "assembled",
               "overlay_id": plan["id"], "upstream_commit": UPSTREAM_COMMIT,
               "manifest": plan_identity, "additions": plan["files"],
               "source_build_receipt": {"path": str(source_path.resolve()), **source_identity},
               "base_artifact": {"path": str(base_archive.resolve()), **base_identity},
               "artifact": {"path": str(archive_path.resolve()), **file_identity(archive_path)},
               "assembly_tool": {"path": str(Path(__file__).resolve()), **file_identity(__file__)},
               "full_parity": False, "tests_executed": 0, "engine_recompiled": False,
               "scope": "Original resource package augmentation only; browser qualification is a separate execution."}
    receipt_path = output / "package-overlay.json"
    receipt_path.write_bytes(_json_bytes(receipt))
    verified = verify_overlay_receipt(receipt_path, source_path)
    receipt["verification"] = verified["verification"]
    receipt_path.write_bytes(_json_bytes(receipt))
    return receipt_path


def verify_overlay_receipt(receipt_path, source_path, *, base_archive=None, augmented_archive=None):
    """Verify actual base/output bytes, not just a receipt's asserted identities."""
    receipt_path, source_path = Path(receipt_path), Path(source_path)
    receipt = _read_json(receipt_path)
    plan, plan_identity = load_plan()
    if (receipt.get("schema") != 1 or receipt.get("kind") != "blender-browser-package-overlay" or
            receipt.get("status") != "assembled" or receipt.get("overlay_id") != plan["id"] or
            receipt.get("upstream_commit") != UPSTREAM_COMMIT or receipt.get("manifest") != plan_identity or
            receipt.get("additions") != plan["files"] or receipt.get("engine_recompiled") is not False or
            receipt.get("tests_executed") != 0 or receipt.get("full_parity") is not False):
        raise ValueError("overlay receipt differs from the reviewed package contract")
    source = _source_contract(source_path)
    source_identity = _require_identity(source_path, receipt.get("source_build_receipt"), "base source receipt")
    base_archive = Path(base_archive or receipt.get("base_artifact", {}).get("path", ""))
    augmented_archive = Path(augmented_archive or receipt.get("artifact", {}).get("path", ""))
    base_identity = _require_identity(base_archive, receipt.get("base_artifact"), "base archive")
    if not _same_identity(base_identity, source.get("artifact")):
        raise ValueError("overlay base does not match the original source build")
    output_identity = _require_identity(augmented_archive, receipt.get("artifact"), "augmented archive")
    if max(base_identity["bytes"], output_identity["bytes"]) > MAX_ARCHIVE_BYTES:
        raise ValueError("package archive exceeds its byte bound")
    inputs = _inputs(plan, plan_identity, source_identity, base_identity)
    with tarfile.open(base_archive, "r:gz") as original, tarfile.open(augmented_archive, "r:gz") as changed:
        before, after = _members(original), _members(changed)
        root, paths = _layout(before)
        _verify_base_engines(original, before, paths, source)
        proof_path = root + "/PACKAGE-OVERLAY.json"
        if set(after) != set(before) | {proof_path} or proof_path in before:
            raise ValueError("augmented archive added or removed unexpected files")
        if _read(changed, after[proof_path]) != _json_bytes(inputs):
            raise ValueError("embedded overlay declaration differs from verified inputs")
        base_data = _read(original, before[paths["data"]])
        new_data = _read(changed, after[paths["data"]])
        if not new_data.startswith(base_data):
            raise ValueError("existing preload bytes changed")
        cursor = len(base_data)
        for row in plan["files"]:
            end = cursor + row["bytes"]
            if not _same_identity(identity(memoryview(new_data)[cursor:end]), row):
                raise ValueError("added preload resource differs from its exact upstream identity")
            cursor = end
        if cursor != len(new_data):
            raise ValueError("augmented preload data contains unaccounted bytes")
        base_js = _read(original, before[paths["js"]]).decode("utf-8")
        expected_js = append_preload(base_js, len(base_data), plan["files"]).encode("utf-8")
        if _read(changed, after[paths["js"]]) != expected_js:
            raise ValueError("JavaScript changed outside the supported preload metadata overlay")
        unchanged = set(before) - {paths["js"], paths["data"]}
        for name in sorted(unchanged):
            if _member_identity(original, before[name]) != _member_identity(changed, after[name]):
                raise ValueError("unrelated package member changed: " + name)
        verification = {"base_archive_verified": True, "added_resource_bytes_verified": True,
                        "existing_preload_bytes_unchanged": True, "wasm_unchanged": True,
                        "unchanged_files": len(unchanged), "added_files": 1,
                        "modified_files": [paths["data"], paths["js"]],
                        "mount_timing": "Emscripten preload before application main",
                        "scope": "Actual archive members compared with actual original package and pinned asset hashes."}
    return {**receipt, "verification": verification, "receipt_sha256": file_identity(receipt_path)["sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-archive", type=Path, required=True)
    parser.add_argument("--source-build-receipt", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True,
                        help="Original source tree or native datafiles tree containing assets/brushes")
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing evidence is never overwritten")
    args = parser.parse_args(argv)
    receipt = assemble_overlay(args.base_archive, args.source_build_receipt, args.asset_root, args.output)
    print(json.dumps({"status": "assembled", "receipt": str(receipt), "tests_executed": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
