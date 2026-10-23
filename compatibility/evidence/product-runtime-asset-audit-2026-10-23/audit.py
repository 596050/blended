#!/usr/bin/env python3
"""Read-only audit of original LFS assets outside the verified fixture paths."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile
import time


COMMIT = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
ARCHIVE_IDENTITY = {"bytes": 80900636, "sha256": "e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7"}
POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"
POINTER = re.compile(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n")
MAX_POINTER_BYTES = 1024
MAX_ARCHIVE_ENTRIES = 100000
MAX_ARCHIVE_CONTENT_BYTES = 2 * 1024 ** 3
MAX_LIVE_FILE_BYTES = 128 * 1024 ** 2
MAX_LIVE_HASH_BYTES = 1024 ** 3


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_members(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "duplicate JSON member: " + key)
        value[key] = item
    return value


def read_json(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_members,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def byte_identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def file_identity(path):
    with Path(path).open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        value = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": size, "sha256": value}


def pinned(value):
    require(isinstance(value, dict) and type(value.get("bytes")) is int
            and value["bytes"] >= 0 and re.fullmatch(r"[0-9a-f]{64}", value.get("sha256", "")),
            "invalid pinned byte identity")
    return {key: value[key] for key in ("bytes", "sha256")}


def safe_relative(value):
    path = PurePosixPath(value)
    require(value and "\\" not in value and not path.is_absolute()
            and value == path.as_posix() and all(part not in {"", ".", ".."} for part in value.split("/"))
            and not any(ord(char) < 32 for char in value), "unsafe source member path: " + value)
    return path


def live_state(root, relative, expected, original, budget):
    path = root
    for part in safe_relative(relative).parts:
        path /= part
        if path.is_symlink():
            return {"state": "symlink_not_followed"}
    if not path.exists():
        return {"state": "missing"}
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        return {"state": "nonregular_file"}
    if before.st_size > MAX_LIVE_FILE_BYTES or budget[0] + before.st_size > MAX_LIVE_HASH_BYTES:
        return {"state": "not_hashed_byte_bound", "observed_bytes": before.st_size}
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode), "live asset changed file type while opening")
        value = hashlib.sha256()
        count = 0
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(block)
            require(count <= MAX_LIVE_FILE_BYTES and budget[0] + count <= MAX_LIVE_HASH_BYTES,
                    "live file grew beyond the read bound")
            value.update(block)
        finished = os.fstat(stream.fileno())
    budget[0] += count
    observed = {"bytes": count, "sha256": value.hexdigest()}
    stable = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) == (
        finished.st_dev, finished.st_ino, finished.st_size, finished.st_mtime_ns)
    if not stable:
        state = "changed_during_read"
    elif observed == expected:
        state = "materialized_verified"
    elif observed == original:
        state = "unmaterialized_original_pointer"
    else:
        state = "unexpected_live_bytes"
    return {"state": state, "observed": observed}


def aggregate(rows):
    objects = {}
    for row in rows:
        oid, size = row["oid_sha256"], row["declared_payload_bytes"]
        require(oid not in objects or objects[oid] == size, "one LFS OID declares inconsistent sizes")
        objects[oid] = size
    states = Counter(row["live"]["state"] for row in rows)
    return {"pointer_paths": len(rows), "declared_bytes_by_path": sum(row["declared_payload_bytes"] for row in rows),
            "unique_lfs_objects": len(objects), "unique_declared_bytes": sum(objects.values()),
            "live_states": dict(sorted(states.items())),
            "verified_materialized_bytes_by_path": sum(row["declared_payload_bytes"] for row in rows
                if row["live"]["state"] == "materialized_verified"),
            "unmaterialized_original_pointer_bytes_by_path": sum(row["declared_payload_bytes"] for row in rows
                if row["live"]["state"] == "unmaterialized_original_pointer")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("source-archive", "source-root", "fixture-inventory", "fixture-report", "preserved-source-receipt", "output"):
        parser.add_argument("--" + field, required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "previous audit evidence is immutable")
    started, tick = datetime.now(timezone.utc).isoformat(), time.monotonic()
    require(not any(path.is_symlink() for path in (args.source_root, *args.source_root.parents)),
            "live source root contains a symlink")
    source_root = args.source_root.resolve(strict=True)
    inventory, report, preserved = (read_json(path) for path in
        (args.fixture_inventory, args.fixture_report, args.preserved_source_receipt))
    for value in (inventory, report, preserved):
        require(value.get("source_commit") == COMMIT and pinned(value.get("source_archive")) == ARCHIVE_IDENTITY,
                "prior receipt disagrees with the pinned source archive")
    require(file_identity(args.source_archive) == ARCHIVE_IDENTITY, "source archive differs from prior receipts")
    require(file_identity(args.fixture_inventory) == pinned(report.get("inventory"))
            == pinned(preserved.get("fixture_inventory")), "fixture exclusion inventory is not bound to prior verification")
    require(report.get("candidate_closure_complete") is True and report.get("status") == "verified_candidate_closure"
            and report.get("failures") == [] and preserved.get("status") == "unchanged" and preserved.get("failures") == [],
            "the prior fixture and source verification did not complete")
    entries = inventory.get("entries")
    require(isinstance(entries, list) and len(entries) == inventory.get("candidate_count") == 7353,
            "unexpected exact fixture exclusion denominator")
    excluded = {row["path"]: row for row in entries}
    verified = {row["path"]: row for row in report.get("files", [])}
    require(len(excluded) == len(entries) == len(verified) == len(report.get("files", []))
            and set(excluded) == set(verified), "fixture receipt drops or duplicates a candidate path")
    for path, row in excluded.items():
        safe_relative(path)
        observed = verified[path]
        require(observed.get("status") == "verified" and pinned(observed.get("observed"))
                == pinned(observed.get("expected")) == pinned(row.get("expected")),
                "excluded fixture lacks its original verified identity: " + path)
    prefix = "blender-" + COMMIT + "/"
    seen, excluded_seen, rows, unparsed = set(), set(), [], []
    total_bytes = regular_files = original_pointers = nonregular_files = 0
    budget = [0]
    with tarfile.open(args.source_archive, "r|gz") as archive:
        for member in archive:
            require(len(seen) < MAX_ARCHIVE_ENTRIES, "source archive exceeds entry bound")
            require(member.name not in seen, "duplicate source archive member")
            seen.add(member.name)
            if member.name == prefix.rstrip("/") and member.isdir():
                continue
            require(member.name.startswith(prefix), "source archive contains another root")
            relative = member.name[len(prefix):]
            safe_relative(relative)
            total_bytes += member.size
            require(0 <= member.size and total_bytes <= MAX_ARCHIVE_CONTENT_BYTES,
                    "source archive exceeds uncompressed byte bound")
            if member.isdir():
                continue
            if not member.isfile():
                require(relative not in excluded, "excluded fixture is not a regular original file")
                nonregular_files += 1
                continue
            regular_files += 1
            with archive.extractfile(member) as stream:
                if relative in excluded:
                    value = hashlib.sha256()
                    count = 0
                    prefix_bytes = b""
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        if not count:
                            prefix_bytes = block[:MAX_POINTER_BYTES + 1]
                        count += len(block)
                        value.update(block)
                    original = {"bytes": count, "sha256": value.hexdigest()}
                    require(original == pinned(excluded[relative]["original"]), "excluded fixture changed in the archive")
                    excluded_seen.add(relative)
                    match = POINTER.fullmatch(prefix_bytes) if count <= MAX_POINTER_BYTES else None
                    if match:
                        original_pointers += 1
                        require(excluded[relative]["kind"] == "lfs"
                                and {"bytes": int(match.group(2)), "sha256": match.group(1).decode()}
                                == pinned(excluded[relative]["expected"]), "excluded pointer identity changed")
                    else:
                        require(excluded[relative]["kind"] == "regular", "excluded LFS pointer could not be parsed")
                    continue
                raw = stream.read(min(member.size, MAX_POINTER_BYTES + 1))
            if not raw.startswith(POINTER_PREFIX):
                continue
            match = POINTER.fullmatch(raw) if member.size <= MAX_POINTER_BYTES else None
            if not match:
                unparsed.append({"path": relative, "archive_bytes": member.size,
                                 "reason": "pointer-like prefix does not match the bounded canonical original pointer form"})
                continue
            original_pointers += 1
            oid, size = match.group(1).decode(), int(match.group(2))
            original = byte_identity(raw)
            expected = {"bytes": size, "sha256": oid}
            rows.append({"path": relative, "directory": str(PurePosixPath(relative).parent),
                         "oid_sha256": oid, "declared_payload_bytes": size,
                         "original_pointer": {**original, "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()},
                         "live": live_state(source_root, relative, expected, original, budget)})
    require(excluded_seen == set(excluded), "the archive did not contain every excluded fixture")
    require(file_identity(args.source_archive) == ARCHIVE_IDENTITY, "source archive changed during audit")
    rows.sort(key=lambda row: row["path"])
    groups = {directory: aggregate([row for row in rows if row["directory"] == directory])
              for directory in sorted({row["directory"] for row in rows})}
    summary = aggregate(rows)
    result = {"schema": 1, "kind": "original-lfs-runtime-asset-audit", "status": "completed",
              "source_commit": COMMIT, "source_archive": {"path": str(args.source_archive.resolve()), **ARCHIVE_IDENTITY},
              "source_root": str(source_root), "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
              "duration_seconds": time.monotonic() - tick, "command": [sys.executable, *sys.argv],
              "auditor": {"path": Path(__file__).name, **file_identity(__file__)},
              "input_receipts": [{"path": str(path.resolve()), **file_identity(path)} for path in
                  (args.fixture_inventory, args.fixture_report, args.preserved_source_receipt)],
              "original_archive_identity_verified": True,
              "archive_scan": {"entries": len(seen), "regular_files": regular_files, "nonregular_files": nonregular_files,
                               "declared_content_bytes": total_bytes, "original_lfs_pointer_paths": original_pointers},
              "excluded_verified_fixture_paths": len(excluded_seen), "excluded_fixture_lfs_paths": inventory["lfs_path_count"],
              "exclusion_scope": "Only exact fixture paths from the independently byte-bound successful hydration inventory; original bytes for every excluded path were checked again against this archive.",
              "summary": summary, "by_directory": groups, "files": rows,
              "unparsed_pointer_like_members": unparsed, "all_pointer_like_members_parsed": not unparsed,
              "live_bytes_hashed": budget[0],
              "bounds": {"archive_entries": MAX_ARCHIVE_ENTRIES, "archive_content_bytes": MAX_ARCHIVE_CONTENT_BYTES,
                         "pointer_bytes": MAX_POINTER_BYTES, "live_file_bytes": MAX_LIVE_FILE_BYTES, "total_live_hash_bytes": MAX_LIVE_HASH_BYTES},
              "downloads_attempted": 0, "source_files_modified": False, "tests_executed": 0, "test_passes": 0,
              "whole_application_resource_closure_complete": False, "full_feature_parity": False,
              "limitations": ["This enumerates original pointer assets outside the prior exact fixture candidate set; runtime services and dependencies not expressed as these pointers remain outside this audit.",
                              "The 7,353 excluded live fixture payloads were not rehashed; their prior successful receipt was verified and their original archive bytes were reconciled.",
                              "Declared bytes by path include duplicate references; unique OID bytes are separately counted, and per-directory unique totals may overlap.",
                              "No source files were written, no resources were fetched, and no test execution or pass is inferred."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "summary": summary, "by_directory": groups,
                      "unparsed_pointer_like_members": unparsed, "receipt": {"path": str(args.output), **file_identity(args.output)}}, indent=2))


if __name__ == "__main__":
    main()
