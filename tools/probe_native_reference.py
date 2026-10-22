#!/usr/bin/env python3
"""Run the selected unchanged Blender 5.2.0 suites on its official Linux build.

The archive and suite bytes are pinned independently of their download paths.
This qualifies the candidate's native reference only, not browser or Blender
5.4 product parity. Python 3.12 and a compatible Linux x64 host are required.
Every attempted run writes native_reference.json and native-reference.log.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import secrets
import subprocess
import tarfile
import tempfile
import traceback

try:
    from .probe_browser_port import (
        Blocked, SUITES, SUITE_BYTES, UPSTREAM_SHA, digest, download, now,
        python_payload, summarize_execution,
    )
except ImportError:
    from probe_browser_port import (
        Blocked, SUITES, SUITE_BYTES, UPSTREAM_SHA, digest, download, now,
        python_payload, summarize_execution,
    )


ASSET_URL = "https://download.blender.org/release/Blender5.2/blender-5.2.0-linux-x64.tar.xz"
ASSET_SHA256 = "96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48"
ASSET_BYTES = 384441228
ARCHIVE_ROOT = "blender-5.2.0-linux-x64"


def extract_reference(archive, directory):
    """Retain confined internal links while rejecting special files and escapes."""
    with tarfile.open(archive, "r:xz") as package:
        members = package.getmembers()
        total = 0
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name or
                    not path.parts or path.parts[0] != ARCHIVE_ROOT):
                raise Blocked("unsafe or unexpected native archive path: " + member.name)
            if not (member.isdir() or member.isfile() or member.issym() or member.islnk()):
                raise Blocked("unsupported native archive special file: " + member.name)
            total += member.size
            if total > 4_000_000_000 or len(members) > 100_000:
                raise Blocked("native archive exceeds its extraction bound")
        # Python's data filter also checks link destinations during extraction,
        # including paths affected by links created by preceding members.
        package.extractall(directory, members=members, filter="data")
    return {"members": len(members), "unpacked_bytes": total, "filter": "data"}


def load_suites(local_paths, work):
    supplied = {}
    for path in local_paths or []:
        if path.name not in SUITES or path.name in supplied:
            raise Blocked("unknown or duplicate pinned suite: " + path.name)
        supplied[path.name] = path.resolve()
    if local_paths and set(supplied) != set(SUITES):
        raise Blocked("both pinned mathutils and BMesh suite files are required")
    suites = []
    for name, expected_hash in SUITES.items():
        upstream_path = "tests/python/" + name
        url = "https://raw.githubusercontent.com/blender/blender/" + UPSTREAM_SHA + "/" + upstream_path
        path = supplied.get(name, work / name)
        if not local_paths:
            download(url, path, SUITE_BYTES[name])
        if not path.is_file() or path.stat().st_size != SUITE_BYTES[name]:
            raise Blocked("suite is missing or its byte count changed: " + name)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected_hash:
            raise Blocked("suite bytes differ from the immutable upstream source: " + name)
        suites.append(({"upstream_path": upstream_path, "sha256": expected_hash,
                        "bytes": len(data), "url": url}, data))
    return suites


def probe(args, report):
    output = args.output.resolve()
    log_path = output / "native-reference.log"
    with tempfile.TemporaryDirectory(prefix="blended-native-reference-") as temporary:
        work = Path(temporary)
        archive = args.asset.resolve() if args.asset else work / "reference.tar.xz"
        if args.asset is None:
            download(ASSET_URL, archive, ASSET_BYTES)
        if not archive.is_file():
            raise Blocked("native reference archive is missing")
        report["artifact"]["observed_bytes"] = archive.stat().st_size
        if archive.stat().st_size != ASSET_BYTES:
            raise Blocked("native artifact byte count differs from the pinned release")
        measured_digest = digest(archive)
        report["artifact"]["observed_sha256"] = measured_digest
        if measured_digest != ASSET_SHA256:
            raise Blocked("native artifact checksum differs from the pinned official release")
        report["official_release_checksum_verified"] = True
        suites = load_suites(args.suite, work)
        report["suite_sources"] = [row for row, _ in suites]
        unpacked = work / "unpacked"
        unpacked.mkdir()
        report["extraction"] = extract_reference(archive, unpacked)
        binary = (unpacked / ARCHIVE_ROOT / "blender").resolve()
        if not binary.is_relative_to(unpacked.resolve()) or not binary.is_file():
            raise Blocked("native archive has no confined Blender executable")
        report["executable"] = {"path": str(binary.relative_to(unpacked)),
                                "sha256": digest(binary), "bytes": binary.stat().st_size}
        marker = "BLENDED_NATIVE_REFERENCE_" + secrets.token_hex(12) + ":"
        runner = work / "native-runner.py"
        runner.write_text(python_payload(suites, marker), encoding="utf-8")
        report["runner_sha256"] = digest(runner)
        flags = ["--background", "--factory-startup", "--threads", "1", "--python-exit-code", "1"]
        report["process"] = {"flags": flags, "timeout_seconds": args.timeout, "returncode": None}
        with log_path.open("w", encoding="utf-8") as log:
            try:
                process = subprocess.run([str(binary), *flags, "--python", str(runner)],
                                         cwd=work, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=args.timeout, check=False)
            except subprocess.TimeoutExpired as error:
                raise Blocked("native reference exceeded the execution timeout; no pass inferred") from error
        report["process"]["returncode"] = process.returncode
        received = []
        with log_path.open(encoding="utf-8", errors="replace") as log:
            for line in log:
                if line.startswith(marker):
                    received.append(json.loads(line[len(marker):]))
        if len(received) != 1:
            raise RuntimeError("native execution did not emit exactly one complete result marker")
        result = received[0]
        report["execution"] = result
        report.update(summarize_execution(result, report["suite_sources"]))
        if process.returncode != 0:
            report["status"] = "failed"
            report["blockers"].append({"scope": "native_runtime", "status": "failed",
                                       "reason": "native Blender exited with code " + str(process.returncode)})
        report["reason"] = (
            "Both unchanged upstream unittest files passed on the checksum-verified official "
            "Blender 5.2.0 native release, with matching reported upstream build identity."
            if report["status"] == "passed" else
            "; ".join(row["scope"] + ": " + row["reason"] for row in report["blockers"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, help="Local exact official Blender 5.2.0 Linux x64 tar.xz")
    parser.add_argument("--suite", action="append", type=Path,
                        help="Local exact pinned suite file; supply both mathutils and BMesh")
    parser.add_argument("--output", type=Path, required=True, help="Directory for native report and native log")
    parser.add_argument("--timeout", type=int, default=240, help="Native execution bound in seconds (1 to 600)")
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    log_path = args.output / "native-reference.log"
    log_path.write_text("", encoding="utf-8")
    report = {
        "schema": 1, "status": "blocked", "started_utc": now(), "finished_utc": None,
        "scope": "selected Blender 5.2.0 candidate native reference qualification only",
        "profile": "native-reference", "full_parity": False, "browser_parity": False,
        "product_target_parity": False, "selected_suites_passed": False,
        "official_release_checksum_verified": False, "upstream_build_hash_verified": False,
        "source_correspondence_verified": False,
        "upstream": {"repository": "blender/blender", "commit": UPSTREAM_SHA, "version": "5.2.0"},
        "artifact": {"url": ASSET_URL, "expected_sha256": ASSET_SHA256, "expected_bytes": ASSET_BYTES},
        "suite_sources": [], "summary": None, "execution": None, "blockers": [],
    }
    try:
        if args.timeout <= 0 or args.timeout > 600:
            raise Blocked("timeout must be between 1 and 600 seconds")
        probe(args, report)
    except Blocked as error:
        report["status"], report["reason"] = "blocked", str(error)
        report["blockers"].append({"scope": "infrastructure", "status": "blocked", "reason": str(error)})
    except Exception as error:
        report["status"], report["reason"] = "failed", str(error)
        report["blockers"].append({"scope": "infrastructure", "status": "failed", "reason": str(error)})
        report["traceback"] = traceback.format_exc()
    finally:
        report["finished_utc"] = now()
        report["log"] = {"path": log_path.name, "sha256": digest(log_path), "bytes": log_path.stat().st_size}
        evidence = args.output / "native_reference.json"
        evidence.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "reason": report.get("reason"), "evidence": str(evidence)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
