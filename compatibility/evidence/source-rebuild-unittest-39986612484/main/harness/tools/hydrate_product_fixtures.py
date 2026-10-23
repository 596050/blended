#!/usr/bin/env python3
"""Hydrate every original candidate fixture with bounded, verified official LFS bytes.

The frozen input inventory and source archive define the complete allowed path set.
This is resource preparation, not test execution or runtime dependency discovery.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


LFS_BATCH_URL = "https://projects.blender.org/blender/blender.git/info/lfs/objects/batch"
MAX_OBJECT_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_CANDIDATES = 20000
MAX_BATCH = 64
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
EXCLUDED = {".git", "node_modules", "target", "dist", "__pycache__", ".venv"}
POINTER = re.compile(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n")


class HydrationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise HydrationError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def file_identity(path):
    with Path(path).open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": Path(path).stat().st_size, "sha256": digest}


def receipt_identity(path):
    return {"path": str(Path(path).resolve()), **file_identity(path)}


def confined(root, relative):
    rel = PurePosixPath(relative)
    require(isinstance(relative, str) and relative and "\\" not in relative and "\0" not in relative and
            not rel.is_absolute() and ".." not in rel.parts and relative == rel.as_posix(), "unsafe fixture path")
    root = Path(root).absolute()
    require(not any(p.is_symlink() for p in (root, *root.parents)), "fixture root contains a symlink")
    path = root
    for part in rel.parts:
        path = path / part
        require(not path.is_symlink(), "fixture path contains a symlink: " + relative)
    return path


def write_json(path, document):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2)
        stream.write("\n")


def freeze_inventory(inventory_path, archive_path, source_root, commit, expected_archive_sha256):
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "full source commit required")
    archive_identity = file_identity(archive_path)
    require(archive_identity["sha256"] == expected_archive_sha256, "pinned source archive hash changed")
    source = json.loads(Path(inventory_path).read_text())
    require(source.get("commit") == commit and source.get("upstream") == "blender/blender", "source inventory pin changed")
    candidates = source.get("fixtures")
    require(isinstance(candidates, list) and 0 < len(candidates) <= MAX_CANDIDATES, "candidate count invalid")
    indexed = {}
    for row in candidates:
        confined(source_root, row["path"])
        require(row["path"] not in indexed, "duplicate candidate path")
        require(row.get("status") in {"lfs_pointer", "present_unvalidated"}, "unsupported original candidate status")
        indexed[row["path"]] = row
    roots = [r["path"] for r in source.get("fixture_roots", [])]
    require(roots == ["tests/files"], "unexpected source inventory fixture roots")
    frozen, seen, archive_candidates = [], set(), set()
    prefix = "blender-" + commit + "/"
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            if not member.name.startswith(prefix):
                continue
            relative = member.name[len(prefix):]
            rel = PurePosixPath(relative)
            if any(part in EXCLUDED for part in rel.parts):
                continue
            selected = relative.startswith("tests/files/") or rel.suffix.lower() == ".blend"
            if not selected or member.isdir():
                continue
            require(member.isfile(), "candidate source archive entry is not a regular file: " + relative)
            archive_candidates.add(relative)
            require(relative in indexed, "source archive has an omitted candidate fixture: " + relative)
            require(relative not in seen, "duplicate source archive candidate")
            seen.add(relative)
            row = indexed[relative]
            require(0 <= member.size <= MAX_OBJECT_BYTES, "original candidate byte bound exceeded")
            raw = archive.extractfile(member).read()
            require(len(raw) == row["size"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "candidate differs from pinned archive: " + relative)
            original = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()}
            match = POINTER.fullmatch(raw)
            if row["status"] == "lfs_pointer":
                require(match is not None and row.get("lfs_pointer_valid") is True, "invalid pinned LFS pointer")
                oid, size = match.group(1).decode(), int(match.group(2))
                require(oid == row["lfs_oid_sha256"] and size == row["lfs_declared_size"], "pointer identity changed")
                require(0 <= size <= MAX_OBJECT_BYTES, "LFS object byte bound exceeded")
                expected = {"bytes": size, "sha256": oid}
                original["text"] = raw.decode("ascii")
                kind = "lfs"
            else:
                require(match is None, "regular candidate contains an undeclared LFS pointer")
                expected = {"bytes": len(raw), "sha256": original["sha256"]}
                kind = "regular"
            live = confined(source_root, relative)
            require(live.is_file() and stat.S_ISREG(live.stat().st_mode), "candidate missing or not regular: " + relative)
            observed = file_identity(live)
            original_identity = {key: original[key] for key in ("bytes", "sha256")}
            require(observed in (original_identity, expected), "refusing changed source fixture: " + relative)
            frozen.append({"path": relative, "kind": kind, "original_inventory_row": row,
                           "archive_member": member.name, "original": original, "expected": expected,
                           "initial": observed, "initial_state": "payload" if observed == expected else "pointer"})
    require(seen == set(indexed) == archive_candidates, "candidate inventory and pinned archive differ")
    frozen.sort(key=lambda row: row["path"])
    unique = {}
    for row in frozen:
        if row["kind"] == "lfs":
            oid, size = row["expected"]["sha256"], row["expected"]["bytes"]
            require(oid not in unique or unique[oid] == size, "duplicate OID declares inconsistent sizes")
            unique[oid] = size
    require(sum(unique.values()) <= MAX_TOTAL_BYTES, "unique LFS inventory exceeds byte bound")
    return {"schema": 1, "source_commit": commit, "source_inventory": receipt_identity(inventory_path),
            "source_archive": {"path": str(Path(archive_path).resolve()), **archive_identity},
            "source_root": str(Path(source_root).resolve()), "candidate_count": len(frozen),
            "lfs_path_count": sum(row["kind"] == "lfs" for row in frozen),
            "regular_path_count": sum(row["kind"] == "regular" for row in frozen),
            "unique_lfs_object_count": len(unique), "unique_lfs_bytes": sum(unique.values()),
            "selection": "Every original non-excluded regular file under tests/files and every .blend file in the pinned source archive.",
            "entries": frozen}


def validate_action(href, headers):
    require(isinstance(href, str) and len(href) <= 16384, "invalid LFS action URL")
    parsed = urllib.parse.urlsplit(href)
    require(parsed.scheme == "https" and parsed.hostname == "projects.blender.org" and
            parsed.port in (None, 443) and parsed.username is None and parsed.password is None and not parsed.fragment,
            "LFS action is outside the official Blender HTTPS host")
    require(isinstance(headers, dict) and len(headers) <= 32 and
            all(isinstance(k, str) and re.fullmatch(r"[A-Za-z0-9-]+", k) and isinstance(v, str) and
                len(v) <= 16384 and "\r" not in v and "\n" not in v for k, v in headers.items()), "invalid LFS action headers")


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        validate_action(newurl, {})
        return super().redirect_request(request, response, code, message, headers, newurl)


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate LFS JSON field")
        result[key] = value
    return result


def actions_for(objects):
    require(0 < len(objects) <= MAX_BATCH, "invalid LFS batch count")
    body = {"operation": "download", "transfers": ["basic"],
            "objects": [{"oid": oid, "size": size} for oid, size in objects.items()]}
    request = urllib.request.Request(LFS_BATCH_URL, data=json.dumps(body).encode(), method="POST",
                                     headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json"})
    with urllib.request.build_opener(OfficialRedirect()).open(request, timeout=45) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    require(len(raw) <= MAX_RESPONSE_BYTES, "LFS response exceeds byte bound")
    document = json.loads(raw, object_pairs_hook=unique_json)
    require(document.get("transfer", "basic") == "basic", "unsupported LFS transfer")
    returned = document.get("objects")
    require(isinstance(returned, list) and len(returned) == len(objects), "LFS response omitted or added objects")
    actions, errors = {}, {}
    for row in returned:
        oid = row.get("oid")
        require(oid in objects and oid not in actions and oid not in errors and row.get("size") == objects[oid], "LFS response identity mismatch")
        if "error" in row:
            errors[oid] = {"type": "server_object_error", "code": row["error"].get("code") if isinstance(row["error"], dict) else None}
            continue
        action = row.get("actions", {}).get("download", {})
        href, headers = action.get("href"), action.get("header", {})
        validate_action(href, headers)
        actions[oid] = (href, headers)
    return actions, errors


def error_record(error):
    record = {"type": type(error).__name__}
    if isinstance(error, HydrationError):
        record["detail"] = str(error)
    if isinstance(error, urllib.error.HTTPError):
        record["http_status"] = error.code
    if isinstance(getattr(error, "errno", None), int):
        record["errno"] = error.errno
    return record


def download_object(oid, size, action, cache, attempt):
    started = now()
    destination = confined(cache, oid)
    descriptor, temporary = tempfile.mkstemp(prefix=oid + ".partial-" + str(attempt) + "-", dir=cache)
    os.close(descriptor)
    part = Path(temporary)
    received, digest = 0, hashlib.sha256()
    try:
        require(not destination.exists(), "unexpected existing download path")
        href, headers = action
        validate_action(href, headers)
        request = urllib.request.Request(href, headers=headers)
        with urllib.request.build_opener(OfficialRedirect()).open(request, timeout=45) as response, part.open("wb") as stream:
            while True:
                chunk = response.read(min(1024 * 1024, size + 1 - received))
                if not chunk:
                    break
                received += len(chunk)
                digest.update(chunk)
                stream.write(chunk)
                require(received <= size, "download exceeds original LFS size")
        require(received == size and digest.hexdigest() == oid, "download differs from original LFS hash or size")
        os.replace(part, destination)
        return {"oid": oid, "expected_bytes": size, "attempt": attempt, "started_utc": started,
                "finished_utc": now(), "status": "verified_download", "observed_bytes": received, "observed_sha256": digest.hexdigest()}
    except Exception as error:
        # Keep incomplete or incorrect bytes under a distinct attempt filename.
        return {"oid": oid, "expected_bytes": size, "attempt": attempt, "started_utc": started,
                "finished_utc": now(), "status": "download_failed", "observed_bytes": received,
                "observed_sha256": digest.hexdigest(), "error": error_record(error),
                "partial_path": str(part) if part.exists() else None}


def materialize(row, source_root, cached):
    require(file_identity(cached) == row["expected"], "cache differs from expected payload")
    path = confined(source_root, row["path"])
    current = file_identity(path)
    if current == row["expected"]:
        return "already_verified_payload"
    require(current == {key: row["original"][key] for key in ("bytes", "sha256")}, "fixture changed before replacement")
    temporary = path.with_name(path.name + ".blended-lfs-hydration-partial")
    require(not temporary.exists() and not temporary.is_symlink(), "materialization temporary path already exists")
    with cached.open("rb") as source, temporary.open("xb") as destination:
        shutil.copyfileobj(source, destination, 1024 * 1024)
    require(file_identity(temporary) == row["expected"], "materialization copy changed bytes")
    os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
    require(file_identity(path) == current, "fixture changed during replacement")
    os.replace(temporary, path)
    require(file_identity(path) == row["expected"], "materialized fixture did not verify")
    return "hydrated_original_pointer"


def hydrate(inventory_path, archive_path, source_root, commit, archive_sha256, evidence, cache, workers=8):
    require(1 <= workers <= 16, "worker count exceeds bound")
    evidence, cache, source_root = Path(evidence), Path(cache), Path(source_root)
    evidence.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=True)
    started = now()
    try:
        frozen = freeze_inventory(inventory_path, archive_path, source_root, commit, archive_sha256)
    except Exception as error:
        write_json(evidence / "preflight-failure.json", {"source_commit": commit, "started_utc": started,
                   "finished_utc": now(), "status": "preflight_failed", "error": error_record(error),
                   "tests_executed": 0, "downloads_attempted": 0})
        raise
    write_json(evidence / "inventory.json", frozen)
    shutil.copyfile(__file__, evidence / "hydrate_product_fixtures.py")
    object_rows = {}
    for row in frozen["entries"]:
        if row["kind"] == "lfs":
            object_rows.setdefault(row["expected"]["sha256"], []).append(row)
    events = evidence / "attempts.jsonl"
    counts = {"verified_download_objects": 0, "verified_cache_objects": 0, "verified_existing_payload_objects": 0,
              "download_failed_attempts": 0, "batch_failed_attempts": 0, "hydrated_paths": 0, "already_verified_payload_paths": 0}
    pending, failures = {}, []

    def event(record):
        with events.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    def place(oid):
        for row in object_rows[oid]:
            try:
                result = materialize(row, source_root, confined(cache, oid))
                counts["hydrated_paths" if result == "hydrated_original_pointer" else "already_verified_payload_paths"] += 1
            except Exception as error:
                failure = {"stage": "materialize", "path": row["path"], "oid": oid, "error": error_record(error)}
                failures.append(failure)
                event(failure)

    for oid, rows in object_rows.items():
        expected = rows[0]["expected"]
        cached = confined(cache, oid)
        existing = next((r for r in rows if r["initial_state"] == "payload"), None)
        if cached.exists():
            require(file_identity(cached) == expected, "existing object cache has incorrect bytes")
            counts["verified_cache_objects"] += 1
            event({"stage": "cache", "oid": oid, "status": "verified_existing_cache", **expected})
            place(oid)
        elif existing is not None:
            path = confined(source_root, existing["path"])
            require(file_identity(path) == expected, "existing source payload changed")
            with path.open("rb") as source, cached.open("xb") as destination:
                shutil.copyfileobj(source, destination, 1024 * 1024)
            require(file_identity(cached) == expected, "existing source payload copy changed")
            counts["verified_existing_payload_objects"] += 1
            event({"stage": "cache", "oid": oid, "status": "verified_existing_source_payload", "path": existing["path"], **expected})
            place(oid)
        else:
            pending[oid] = expected["bytes"]

    all_pending = list(pending.items())
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for offset in range(0, len(all_pending), MAX_BATCH):
            chunk = dict(all_pending[offset:offset + MAX_BATCH])
            for attempt in range(1, 4):
                if not chunk:
                    break
                batch_started = now()
                try:
                    actions, server_errors = actions_for(chunk)
                    event({"stage": "batch", "attempt": attempt, "objects": list(chunk), "started_utc": batch_started,
                           "finished_utc": now(), "status": "verified_batch_identities", "server_object_errors": server_errors})
                except Exception as error:
                    counts["batch_failed_attempts"] += 1
                    event({"stage": "batch", "attempt": attempt, "objects": list(chunk), "started_utc": batch_started,
                           "finished_utc": now(), "status": "batch_failed", "error": error_record(error)})
                    if attempt < 3:
                        time.sleep(attempt)
                    continue
                futures = {pool.submit(download_object, oid, chunk[oid], action, cache, attempt): oid for oid, action in actions.items()}
                for future in as_completed(futures):
                    try:
                        record = future.result()
                    except Exception as error:
                        record = {"oid": futures[future], "attempt": attempt, "status": "download_failed",
                                  "error": error_record(error), "finished_utc": now()}
                    event({"stage": "object", **record})
                    if record["status"] == "verified_download":
                        oid = record["oid"]
                        counts["verified_download_objects"] += 1
                        del chunk[oid]
                        place(oid)
                    else:
                        counts["download_failed_attempts"] += 1
                if chunk and attempt < 3:
                    time.sleep(attempt)
            for oid, size in chunk.items():
                failures.append({"stage": "download_exhausted", "oid": oid, "expected_bytes": size,
                                 "paths": [row["path"] for row in object_rows[oid]]})
            print(json.dumps({"objects_processed": min(offset + MAX_BATCH, len(all_pending)), "objects_to_download": len(all_pending),
                              **counts, "unresolved": len(failures)}), flush=True)

    final = []
    for row in frozen["entries"]:
        try:
            observed = file_identity(confined(source_root, row["path"]))
            verified = observed == row["expected"]
            final.append({"path": row["path"], "kind": row["kind"], "expected": row["expected"],
                          "observed": observed, "status": "verified" if verified else "unresolved"})
        except Exception as error:
            final.append({"path": row["path"], "kind": row["kind"], "expected": row["expected"],
                          "status": "unresolved", "error": error_record(error)})
    complete = all(row["status"] == "verified" for row in final) and not failures
    report = {"schema": 1, "source_commit": commit, "started_utc": started, "finished_utc": now(),
              "source_root": str(source_root.resolve()), "official_lfs_batch_url": LFS_BATCH_URL,
              "inventory": receipt_identity(evidence / "inventory.json"),
              "verifier": receipt_identity(evidence / "hydrate_product_fixtures.py"),
              "attempts": receipt_identity(events), "source_archive": frozen["source_archive"],
              "counts": {**counts, "candidate_paths": len(final), "verified_paths": sum(r["status"] == "verified" for r in final),
                         "regular_paths": frozen["regular_path_count"], "lfs_paths": frozen["lfs_path_count"],
                         "unique_lfs_objects": frozen["unique_lfs_object_count"], "unique_lfs_bytes": frozen["unique_lfs_bytes"]},
              "status": "verified_candidate_closure" if complete else "incomplete_candidate_closure",
              "candidate_closure_complete": complete, "runtime_fixture_dependency_closure_complete": False,
              "tests_executed": 0, "test_passes": 0, "original_assertions_modified": False,
              "failures": failures, "files": final,
              "limitations": ["Covers every path in the original candidate inventory, independently reconciled to the pinned source archive.",
                              "Runtime tests may reveal additional dependencies outside this candidate selection.",
                              "Hydration is resource availability evidence and does not establish a test pass or feature parity."]}
    write_json(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "counts": report["counts"], "report": receipt_identity(evidence / "report.json")}))
    return complete


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inventory", "source-archive", "source-root", "evidence", "object-cache"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    success = hydrate(args.inventory, args.source_archive, args.source_root, args.source_commit, args.archive_sha256,
                      args.evidence, args.object_cache, args.workers)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
