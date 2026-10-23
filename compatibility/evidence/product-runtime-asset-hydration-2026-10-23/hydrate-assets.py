"""Materialize only the exact original LFS assets in the frozen independent audit."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
import time

from hydration_transport import (
    LFS_BATCH_URL, POINTER, actions_for, confined, download_object, error_record,
    file_identity, materialize, receipt_identity, require, write_json,
)


directory = Path(__file__).resolve().parent
repo = directory.parents[2]
workspace = repo.parent
audit_path = repo / "compatibility/evidence/product-runtime-asset-audit-2026-10-23/report.json"
audit_identity = receipt_identity(audit_path)
require(audit_identity["sha256"] == "afa1183fd17b9b21e07e0da7eba18a8c41508ba33c5704ae2ab86f57d6e2901f",
        "independent asset audit changed")
audit = json.loads(audit_path.read_text())
commit = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
require(audit["source_commit"] == commit and audit["status"] == "completed", "audit source or status differs")
source_root = Path(audit["source_root"])
archive_path = Path(audit["source_archive"]["path"])
cache = workspace / "runtime/product-runtime-asset-objects-94363991"
require(not cache.exists(), "use a fresh bounded object cache for this attempt")
require(not (directory / "inventory.json").exists(), "preserve the original hydration attempt")
now = lambda: datetime.now(timezone.utc).isoformat()
started = now()
require(receipt_identity(archive_path) == audit["source_archive"], "pinned source archive changed")
selected = {row["path"]: row for row in audit["files"]}
require(len(selected) == len(audit["files"]) == 338, "audited path count differs")
frozen, non_lfs, symlinks, all_lfs = [], [], [], []
prefix = "blender-" + commit + "/"

# Read original archive bytes before any network or source mutation. The frozen
# audit is selection authority; archive pointers independently bind its OIDs.
with tarfile.open(archive_path, "r:gz") as archive:
    for member in archive:
        if member.isdir() and member.name == prefix.removesuffix("/"):
            continue
        require(member.name.startswith(prefix), "archive entry is outside pinned source root")
        if member.isdir():
            continue
        relative = member.name[len(prefix):]
        if member.issym():
            rel = PurePosixPath(relative)
            require(relative == rel.as_posix() and not rel.is_absolute() and ".." not in rel.parts,
                    "unsafe original symlink path")
            path = source_root / relative
            require(not any(parent.is_symlink() for parent in path.parents), "symlink parent changed")
            require(path.is_symlink() and os.readlink(path) == member.linkname, "original symlink changed")
            symlinks.append({"path": relative, "target": member.linkname})
            continue
        require(member.isfile() and member.size <= 64 * 1024 * 1024, "unsupported or oversized original archive entry")
        raw = archive.extractfile(member).read()
        require(len(raw) == member.size, "short original archive entry")
        original = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        match = POINTER.fullmatch(raw)
        if match is None:
            require(not raw.startswith(b"version https://git-lfs.github.com/spec/"), "unparsed original pointer")
            require(relative not in selected, "audited LFS asset is not an original pointer")
            observed = file_identity(confined(source_root, relative))
            require(observed == original, "original non-LFS source bytes changed: " + relative)
            non_lfs.append({"path": relative, "expected": original})
            continue
        oid, size = match.group(1).decode(), int(match.group(2))
        require(0 <= size <= 64 * 1024 * 1024, "original LFS payload exceeds bound")
        all_lfs.append({"path": relative, "expected": {"bytes": size, "sha256": oid}})
        if relative not in selected:
            continue
        audited = selected[relative]
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(audited["original_pointer"] == {**original, "git_blob_sha1": blob}, "audited pointer differs from original")
        require(audited["oid_sha256"] == oid and audited["declared_payload_bytes"] == size,
                "audited payload differs from original pointer")
        observed = file_identity(confined(source_root, relative))
        require(observed == original == audited["live"]["observed"], "original asset changed since audit")
        frozen.append({"path": relative, "kind": "lfs", "original": {**original, "git_blob_sha1": blob,
                       "text": raw.decode("ascii")}, "initial": observed, "initial_state": "pointer",
                       "expected": {"bytes": size, "sha256": oid}, "audited_row": audited})

require({row["path"] for row in frozen} == set(selected), "original archive and audit selection differ")
frozen.sort(key=lambda row: row["path"])
objects = {}
for row in frozen:
    oid, size = row["expected"]["sha256"], row["expected"]["bytes"]
    require(oid not in objects or objects[oid] == size, "original OID has conflicting declared sizes")
    objects[oid] = size
require(len(objects) == 297 and sum(objects.values()) == 8710555, "audited unique object totals differ")
require(sum(row["expected"]["bytes"] for row in frozen) == 8791719, "audited path byte total differs")
inventory = {"schema": 1, "source_commit": commit, "source_root": str(source_root),
             "source_archive": audit["source_archive"], "independent_audit": audit_identity,
             "entries": frozen, "unique_objects": objects, "unique_object_bytes": sum(objects.values()),
             "candidate_paths": len(frozen), "selection": "Exactly the 338 original pointer paths in the frozen independent audit."}
write_json(directory / "inventory.json", inventory)
preservation = {"schema": 1, "source_commit": commit, "source_archive": audit["source_archive"],
                "non_lfs_files": non_lfs, "symlinks": symlinks, "all_original_lfs_paths": all_lfs}
write_json(directory / "source-preservation-manifest.json", preservation)
cache.mkdir(parents=True, exist_ok=False)
events = directory / "attempts.jsonl"
events.touch(exist_ok=False)
counts = {"verified_download_objects": 0, "download_failed_attempts": 0, "batch_failed_attempts": 0,
          "hydrated_paths": 0, "materialization_failed_paths": 0}
failures = []
paths_by_oid = {}
for row in frozen:
    paths_by_oid.setdefault(row["expected"]["sha256"], []).append(row)


def event(record):
    with events.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def place(oid):
    for row in paths_by_oid[oid]:
        record = {"stage": "materialize", "path": row["path"], "oid": oid, "started_utc": now(),
                  "expected": row["expected"]}
        try:
            path = confined(source_root, row["path"])
            record["before"] = file_identity(path)
            record["before_mode"] = stat.S_IMODE(path.stat().st_mode)
            result = materialize(row, source_root, confined(cache, oid))
            record["after"] = file_identity(path)
            record["after_mode"] = stat.S_IMODE(path.stat().st_mode)
            require(result == "hydrated_original_pointer", "unexpected already materialized source asset")
            require(record["before"] == row["initial"] and record["after"] == row["expected"] and
                    record["before_mode"] == record["after_mode"], "asset replacement identity or mode differs")
            record["status"] = result
            counts["hydrated_paths"] += 1
        except Exception as error:
            record.update(status="materialization_failed", error=error_record(error))
            counts["materialization_failed_paths"] += 1
            failures.append(record)
        record["finished_utc"] = now()
        event(record)


pending = list(objects.items())
with ThreadPoolExecutor(max_workers=8) as pool:
    for offset in range(0, len(pending), 64):
        chunk = dict(pending[offset:offset + 64])
        for attempt in range(1, 4):
            if not chunk:
                break
            batch_started = now()
            try:
                actions, errors = actions_for(chunk)
                event({"stage": "batch", "attempt": attempt, "objects": chunk, "started_utc": batch_started,
                       "finished_utc": now(), "status": "verified_batch_identities", "server_object_errors": errors,
                       "official_lfs_batch_url": LFS_BATCH_URL})
            except Exception as error:
                counts["batch_failed_attempts"] += 1
                event({"stage": "batch", "attempt": attempt, "objects": chunk, "started_utc": batch_started,
                       "finished_utc": now(), "status": "batch_failed", "error": error_record(error)})
                if attempt < 3:
                    time.sleep(attempt)
                continue
            tasks = {pool.submit(download_object, oid, chunk[oid], action, cache, attempt): oid
                     for oid, action in actions.items()}
            for task in as_completed(tasks):
                record = task.result()
                event({"stage": "object", **record})
                if record["status"] == "verified_download":
                    counts["verified_download_objects"] += 1
                    del chunk[record["oid"]]
                    place(record["oid"])
                else:
                    counts["download_failed_attempts"] += 1
            if chunk and attempt < 3:
                time.sleep(attempt)
        failures.extend({"stage": "download_exhausted", "oid": oid, "expected_bytes": size}
                        for oid, size in chunk.items())
        print(json.dumps({"objects_considered": min(offset + 64, len(pending)), **counts,
                          "unresolved": len(failures)}), flush=True)

final_assets = []
for row in frozen:
    observed = file_identity(confined(source_root, row["path"]))
    final_assets.append({"path": row["path"], "before": row["initial"], "expected": row["expected"],
                         "after": observed, "verified": observed == row["expected"]})
    if observed != row["expected"]:
        failures.append({"stage": "final_asset_rehash", "path": row["path"], "observed": observed})

# Re-read every original non-LFS file and symlink after the only allowed pointer
# substitutions. Also verify all original LFS paths, including prior fixtures,
# without changing any path outside the selected 338 assets.
preservation_failures = []
verified_non_lfs, verified_lfs, verified_symlinks = 0, 0, 0
for kind, rows in (("non_lfs", non_lfs), ("lfs", all_lfs)):
    for row in rows:
        try:
            observed = file_identity(confined(source_root, row["path"]))
            require(observed == row["expected"], "original source payload differs")
            if kind == "non_lfs":
                verified_non_lfs += 1
            else:
                verified_lfs += 1
        except Exception as error:
            preservation_failures.append({"kind": kind, "path": row["path"], "error": error_record(error)})
for row in symlinks:
    path = source_root / row["path"]
    if path.is_symlink() and os.readlink(path) == row["target"]:
        verified_symlinks += 1
    else:
        preservation_failures.append({"kind": "symlink", "path": row["path"]})
require(receipt_identity(audit_path) == audit_identity, "independent audit changed during hydration")
complete = not failures and not preservation_failures and all(row["verified"] for row in final_assets)
report = {
    "schema": 1, "kind": "original-lfs-runtime-asset-hydration", "source_commit": commit,
    "started_utc": started, "finished_utc": now(), "source_root": str(source_root),
    "source_archive": audit["source_archive"], "independent_audit": audit_identity,
    "official_lfs_batch_url": LFS_BATCH_URL, "object_cache": str(cache),
    "inventory": receipt_identity(directory / "inventory.json"),
    "source_preservation_manifest": receipt_identity(directory / "source-preservation-manifest.json"),
    "attempts": receipt_identity(events), "hydrator": receipt_identity(Path(__file__)),
    "transport_snapshot": receipt_identity(directory / "hydration_transport.py"),
    "counts": {**counts, "candidate_paths": len(frozen), "verified_paths": sum(row["verified"] for row in final_assets),
               "unique_objects": len(objects), "unique_object_bytes": sum(objects.values()),
               "payload_bytes_by_path": sum(row["expected"]["bytes"] for row in frozen),
               "original_non_lfs_files_unchanged": verified_non_lfs, "original_non_lfs_total": len(non_lfs),
               "original_lfs_paths_verified": verified_lfs, "original_lfs_paths_total": len(all_lfs),
               "original_symlinks_unchanged": verified_symlinks, "original_symlinks_total": len(symlinks)},
    "status": "verified_audited_assets" if complete else "incomplete_audited_assets",
    "audited_asset_selection_complete": complete, "files": final_assets,
    "failures": failures, "source_preservation_failures": preservation_failures,
    "original_non_lfs_source_modified": False if not preservation_failures else None,
    "original_assertions_modified": False if not preservation_failures else None,
    "tests_executed": 0, "test_passes": 0, "builds_started": 0,
    "whole_application_resource_closure_complete": False, "full_feature_parity": False,
    "limitations": [
        "The allowed mutations are only the 338 exact original pointer paths selected by the independent audit.",
        "All original archive payloads were rehashed, but dependencies not represented by original source archive entries remain outside this evidence.",
        "Resource materialization does not demonstrate a compiler success, test pass, application runtime closure, or browser feature parity.",
    ],
}
write_json(directory / "report.json", report)
print(json.dumps({"status": report["status"], "counts": report["counts"],
                  "report": receipt_identity(directory / "report.json")}))
raise SystemExit(0 if complete else 1)
