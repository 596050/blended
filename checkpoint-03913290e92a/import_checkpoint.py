#!/usr/bin/env python3
"""Verify and optionally publish one previously reviewed Git bundle checkpoint."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

EXPECTED = {
    "repository": "596050/blended",
    "target_branch": "checkpoint/verified-03913290e92a",
    "base_commit": "9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c",
    "target_commit": "03913290e92a98cd9c45fdecf679072587c4dbe7",
    "target_tree": "a3fbe996e97c8e872ca4d94a1c0f7283e9cb86ad"
}
BUNDLE_SHA256 = "a4a7b7dd8347aa3196e63fda820db641661f88749a44db1b9c60d239b7d5be1a"
BUNDLE_BYTES = 5045057
LEDGER_PATH = "compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/report.json"
LEDGER_SHA256 = "d1b6df970fd0be756b374eba9ca2c662372106c9e3ec1fe6df9ea80bff553e81"
LFS_OID = "1335899143c7e77bcb0f6e3680fd99078c0af481a1238e4ed7d4eb1ddd7dd353"
LFS_BYTES = 121384
LFS_PATH = "checkpoint-03913290e92a/lfs/startup.blend"
LFS_POINTER = "compatibility/evidence/product-configure-2026-10-23/startup.blend.pointer"
GIT_LFS_OBJECTS = []


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--chunks-root", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    commands = work / "commands"
    commands.mkdir()
    receipt = {
        "schema": 1, "started_utc": utc(), "status": "running",
        "entry_point_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "expected": EXPECTED, "push_requested": args.push, "published": False,
        "publication_outcome": "not_attempted",
        "all_upstream_test_parity": False, "full_feature_parity": False,
        "blender_tests_executed": 0, "commands": [], "chunks": [],
    }

    def save():
        (work / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")

    def run(name, argv, *, timeout=180, input_data=None):
        record = {"name": name, "argv": [str(x) for x in argv], "started_utc": utc()}
        if input_data is not None:
            record["stdin"] = {"bytes": len(input_data), "sha256": hashlib.sha256(input_data).hexdigest()}
        receipt["commands"].append(record)
        save()
        try:
            result = subprocess.run(record["argv"], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, input=input_data,
                                    timeout=timeout, check=False)
            stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
            timed_out = False
        except subprocess.TimeoutExpired as error:
            stdout, stderr, returncode = error.stdout or b"", error.stderr or b"", None
            timed_out = True
        for label, data in (("stdout", stdout), ("stderr", stderr)):
            path = commands / f"{len(receipt['commands']):02d}-{name}.{label}.log"
            path.write_bytes(data)
            record[label] = {"path": str(path.relative_to(work)), "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()}
        record.update(returncode=returncode, timed_out=timed_out,
                      timeout_seconds=timeout, finished_utc=utc())
        save()
        require(not timed_out, f"{name} exceeded {timeout} seconds; inspect preserved partial logs")
        require(returncode == 0, f"{name} exited {returncode}; inspect preserved logs")
        return stdout

    try:
        raw_manifest = args.manifest.read_bytes()
        manifest = json.loads(raw_manifest)
        receipt["manifest_sha256"] = hashlib.sha256(raw_manifest).hexdigest()
        require(manifest.get("schema") == 1, "Unexpected manifest schema")
        for key, value in EXPECTED.items():
            require(manifest.get(key) == value, f"Unexpected {key}")
        require(manifest["bundle"] == {
            "bytes": BUNDLE_BYTES, "sha256": BUNDLE_SHA256,
            "ref": "refs/heads/" + EXPECTED["target_branch"],
        }, "Unexpected bundle contract")
        root = args.chunks_root.resolve()
        expected_lfs = {"path": LFS_PATH, "bytes": LFS_BYTES, "sha256": LFS_OID}
        require(manifest.get("lfs_objects") == [expected_lfs], "Unexpected referenced LFS object contract")
        lfs_path = root / LFS_PATH
        require(not lfs_path.is_symlink() and lfs_path.resolve().is_relative_to(root),
                "LFS payload is not an ordinary in-root file")
        lfs_payload = lfs_path.read_bytes()
        require(len(lfs_payload) == LFS_BYTES and hashlib.sha256(lfs_payload).hexdigest() == LFS_OID,
                "Original LFS payload does not match its source pointer")
        receipt["lfs_objects"] = [expected_lfs]
        require(manifest.get("git_lfs_objects") == GIT_LFS_OBJECTS,
                "Unexpected in-tree original fixture LFS contract")
        receipt["git_lfs_objects"] = []
        receipt["lfs_upload_outcome"] = "not_attempted"
        chunks = manifest["chunks"]
        require(len(chunks) == 10, "Unexpected chunk count")
        bundle = work / "verified.bundle"
        with bundle.open("xb") as stream:
            for index, chunk in enumerate(chunks):
                expected_path = f"checkpoint-03913290e92a/bundle-{index:03d}.bin"
                require(chunk["index"] == index and chunk["path"] == expected_path,
                        "Chunk order or path mismatch")
                path = root / expected_path
                require(not path.is_symlink() and path.resolve().is_relative_to(root),
                        "Chunk path is not an ordinary in-root file")
                data = path.read_bytes()
                actual = {"index": index, "path": expected_path, "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest(),
                          "git_blob_sha1": hashlib.sha1(
                              f"blob {len(data)}\0".encode() + data).hexdigest()}
                require(actual == chunk, f"Chunk {index} failed its byte/hash contract")
                stream.write(data)
                receipt["chunks"].append(actual)
        bundle_data = bundle.read_bytes()
        require(len(bundle_data) == BUNDLE_BYTES, "Bundle byte count mismatch")
        require(hashlib.sha256(bundle_data).hexdigest() == BUNDLE_SHA256, "Bundle SHA256 mismatch")
        receipt["bundle"] = {"bytes": len(bundle_data), "sha256": BUNDLE_SHA256}
        del bundle_data

        bare = work / "repository.git"
        run("init", ["git", "init", "--bare", bare])
        git = ["git", "--git-dir", str(bare)]
        run("remote", git + ["remote", "add", "origin", "https://github.com/596050/blended.git"])
        run("fetch-base", git + ["fetch", "--no-tags", "origin", EXPECTED["base_commit"]], timeout=300)
        run("verify-bundle", git + ["bundle", "verify", str(bundle)])
        run("import-bundle", git + ["fetch", str(bundle), manifest["bundle"]["ref"] + ":refs/heads/imported"], timeout=300)
        target = EXPECTED["target_commit"]
        require(run("commit", git + ["rev-parse", "refs/heads/imported"]).decode().strip() == target,
                "Imported commit identity mismatch")
        require(run("tree", git + ["rev-parse", target + "^{tree}"]).decode().strip() == EXPECTED["target_tree"],
                "Imported tree identity mismatch")
        parents = run("parents", git + ["rev-list", "--parents", "-n", "1", target]).decode().split()
        require(parents == [target, EXPECTED["base_commit"]],
                "Target must have exactly the selected base as its sole parent")
        run("ancestry", git + ["merge-base", "--is-ancestor", EXPECTED["base_commit"], target])
        run("fsck", git + ["fsck", "--full", "--strict"], timeout=300)
        ledger_data = run("ledger", git + ["show", target + ":" + LEDGER_PATH])
        require(hashlib.sha256(ledger_data).hexdigest() == LEDGER_SHA256, "Ledger digest mismatch")
        receipt["verified_ledger_sha256"] = LEDGER_SHA256
        run("lfs-version", git + ["lfs", "version"])
        generated_pointer = run("lfs-clean", git + ["lfs", "clean"], input_data=lfs_payload)
        original_pointer = run("original-lfs-pointer", git + ["show", target + ":" + LFS_POINTER])
        require(generated_pointer == original_pointer, "Git LFS did not reproduce the committed evidence pointer")

        for index, item in enumerate(GIT_LFS_OBJECTS):
            payload = run(f"fixture-{index}-payload", git + [
                "show", target + ":" + item["payload_git_path"]])
            require(len(payload) == item["bytes"] and
                    hashlib.sha256(payload).hexdigest() == item["sha256"],
                    f"Original in-tree fixture {index} failed its byte/hash contract")
            pointer = run(f"fixture-{index}-pointer", git + [
                "show", target + ":" + item["pointer_git_path"]])
            expected_pointer = (
                "version https://git-lfs.github.com/spec/v1\n"
                f"oid sha256:{item['sha256']}\nsize {item['bytes']}\n"
            ).encode("ascii")
            require(pointer == expected_pointer,
                    f"Original in-tree fixture {index} pointer mismatch")
            cleaned = run(f"fixture-{index}-lfs-clean", git + ["lfs", "clean"],
                          input_data=payload)
            require(cleaned == pointer,
                    f"Git LFS did not reproduce original fixture {index} pointer")
            receipt["git_lfs_objects"].append(item)
            save()

        branch_ref = "refs/heads/" + EXPECTED["target_branch"]
        def read_head(name):
            output = run(name, git + ["ls-remote", "--exit-code", "--heads", "origin", branch_ref]).decode().strip()
            rows = [line.split() for line in output.splitlines()]
            require(len(rows) == 1 and len(rows[0]) == 2 and rows[0][1] == branch_ref,
                    "Remote branch query was ambiguous")
            return rows[0][0]

        before = read_head("remote-before")
        receipt["remote_before"] = before
        require(before in (EXPECTED["base_commit"], target), "Remote branch changed; refusing to overwrite other work")
        receipt["status"] = "verified"
        if args.push:
            if before != target:
                # Upload only the fixed, verified original payload identities.
                # The target commit, tree, tests and pointer bytes remain unchanged.
                receipt["lfs_upload_outcome"] = "unknown"
                save()
                object_ids = list(dict.fromkeys([LFS_OID] + [item["sha256"] for item in GIT_LFS_OBJECTS]))
                run("lfs-push", git + ["lfs", "push", "--object-id", "origin"] +
                    object_ids, timeout=180)
                receipt["lfs_upload_outcome"] = "completed"
                # The ancestry check above proves this is a fast-forward.
                # The explicit lease adds an atomic check against a concurrent change.
                receipt.update(publication_outcome="unknown", published=None)
                save()
                run("push", git + ["push", "--porcelain",
                    "--force-with-lease=" + branch_ref + ":" + EXPECTED["base_commit"],
                    "origin", target + ":" + branch_ref], timeout=300)
            after = read_head("remote-after")
            require(after == target, "Remote verification did not match the reviewed checkpoint")
            receipt.update(remote_after=after, status="published", published=True,
                           publication_outcome="verified")
        return 0
    except BaseException as error:
        receipt.update(status="failed", error=f"{type(error).__name__}: {error}")
        (work / "error.log").write_text(traceback.format_exc())
        if receipt["publication_outcome"] == "unknown":
            try:
                after = read_head("remote-after-command-error")
                receipt["remote_after"] = after
                if after == EXPECTED["target_commit"]:
                    receipt.update(published=True, publication_outcome="verified_after_command_error")
                else:
                    receipt.update(published=False, publication_outcome="target_not_current_remote_head")
            except BaseException as verification_error:
                receipt["remote_verification_error"] = f"{type(verification_error).__name__}: {verification_error}"
        print(receipt["error"], file=sys.stderr)
        return 1
    finally:
        receipt["finished_utc"] = utc()
        save()
        print(json.dumps({key: receipt[key] for key in ("status", "published", "full_feature_parity")}))


if __name__ == "__main__":
    raise SystemExit(main())
