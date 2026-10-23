#!/usr/bin/env python3
"""Apply the explicitly selected, hash-bound codec patch to the pinned port.

The main source-build driver owns Git commit/toolchain verification. This helper
verifies every affected source byte, the reviewed patch, and its complete result.
It does not qualify dependency builds or claim any Blender test result.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if not name or "\\" in name or relative.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("invalid patch path")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("patch path crosses a symlink: " + name)
    if current.exists() and not current.is_file():
        raise ValueError("patch target is not a regular file: " + name)
    return current


def apply(port_root: Path, receipt_path: Path, expected_manifest_sha256: str) -> dict:
    package = Path(__file__).resolve().parent
    manifest_path = package / "manifest.json"
    if receipt_path.exists():
        raise ValueError("refusing to overwrite an existing patch receipt")
    root = port_root.resolve(strict=True)
    manifest_bytes = manifest_path.read_bytes()
    actual_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    if actual_manifest_sha != expected_manifest_sha256:
        raise ValueError("codec manifest does not match the explicitly selected digest")
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != 1 or manifest.get("id") != "blender-5.2.0-web-codecs-v1":
        raise ValueError("unrecognized codec patchset contract")
    helper = manifest["application_helper"]
    if helper.get("file") != "apply.py" or helper.get("sha256") != sha256(Path(__file__).resolve()) or helper.get("bytes") != Path(__file__).stat().st_size:
        raise ValueError("codec application helper identity mismatch")
    patch = safe_path(package, manifest["patch"]["file"])
    if sha256(patch) != manifest["patch"]["sha256"] or patch.stat().st_size != manifest["patch"]["bytes"]:
        raise ValueError("codec patch identity mismatch")
    entries = manifest["files"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("empty codec patch file inventory")
    if len({entry["path"] for entry in entries}) != len(entries):
        raise ValueError("duplicate patch target")
    for entry in entries:
        if not isinstance(entry["after_sha256"], str) or not re.fullmatch("[0-9a-f]{64}", entry["after_sha256"]):
            raise ValueError("invalid codec postimage digest")
        if entry["before_sha256"] is not None and not re.fullmatch("[0-9a-f]{64}", entry["before_sha256"]):
            raise ValueError("invalid codec preimage digest")
    record = {"schema": 1, "kind": "browser-codec-patch-application", "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(), "port_root": str(root),
              "id": manifest["id"], "manifest_sha256": actual_manifest_sha,
              "patch_sha256": manifest["patch"]["sha256"], "files": [], "commands": [],
              "dependency_build_verified": False, "blender_tests_executed": False,
              "full_feature_parity": False,
              "limit": "Affected source-file identities and patch application only; source checkout commits and toolchain identity are verified separately by the build driver."}

    def save():
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(record, indent=2) + "\n")

    def command(args: list[str]):
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=60)
        row = {"argv": args, "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(),
               "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        record["commands"].append(row)
        save()
        if result.returncode:
            raise ValueError("codec patch command failed: " + result.stderr)
        return result.stdout

    try:
        before, after = [], []
        for entry in entries:
            target = safe_path(root, entry["path"])
            observed = sha256(target) if target.exists() else None
            before.append(observed == entry["before_sha256"])
            after.append(observed == entry["after_sha256"])
            record["files"].append({**entry, "observed_before_sha256": observed})
        if all(after):
            record["application"] = "already_applied_exact_bytes"
        elif all(before):
            numstat = command(["git", "apply", "--numstat", str(patch)])
            changed = [line.split("\t", 2)[2] for line in numstat.splitlines()]
            if sorted(changed) != sorted(entry["path"] for entry in entries):
                raise ValueError("patch paths differ from the reviewed manifest")
            command(["git", "apply", "--check", "--whitespace=error-all", str(patch)])
            for entry in entries:
                target = safe_path(root, entry["path"])
                if (sha256(target) if target.exists() else None) != entry["before_sha256"]:
                    raise ValueError("source changed after patch preflight: " + entry["path"])
            command(["git", "apply", "--whitespace=error-all", str(patch)])
            record["application"] = "applied"
        else:
            raise ValueError("codec source bytes differ from the pinned inputs or are partially applied")
        for entry, row in zip(entries, record["files"]):
            target = safe_path(root, entry["path"])
            observed = sha256(target) if target.exists() else None
            row["observed_after_sha256"] = observed
            if observed != entry["after_sha256"]:
                raise ValueError("codec patch output mismatch: " + entry["path"])
        record["status"] = "applied_and_verified"
    except Exception as exc:
        record.update(status="failed", reason=str(exc))
        raise
    finally:
        record["completed_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    args = parser.parse_args()
    report = apply(args.port_root, args.receipt, args.expected_manifest_sha256)
    print(json.dumps({"id": report["id"], "status": report["status"], "application": report["application"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
