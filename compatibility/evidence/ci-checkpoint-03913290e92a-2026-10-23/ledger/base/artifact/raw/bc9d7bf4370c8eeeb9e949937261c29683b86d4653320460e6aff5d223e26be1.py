#!/usr/bin/env python3
"""Run the selected unchanged Blender 5.2.0 suites on its official Linux build.

The archive and suite bytes are pinned independently of their download paths.
This qualifies the candidate's native reference only, not browser or Blender
5.4 product parity. Python 3.12 and a compatible Linux x64 host are required.
Every attempted run writes native_reference.json and native-reference.log.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
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
        python_payload, summarize_execution, load_suite_catalog, prepare_suites, suite_metadata, decode_qualification_event, preserve_suite_fixtures,
    )
except ImportError:
    from probe_browser_port import (
        Blocked, SUITES, SUITE_BYTES, UPSTREAM_SHA, digest, download, now,
        python_payload, summarize_execution, load_suite_catalog, prepare_suites, suite_metadata, decode_qualification_event, preserve_suite_fixtures,
    )


ASSET_URL = "https://download.blender.org/release/Blender5.2/blender-5.2.0-linux-x64.tar.xz"
ASSET_SHA256 = "96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48"
ASSET_BYTES = 384441228
ARCHIVE_ROOT = "blender-5.2.0-linux-x64"


class _VerifiedReference:
    """An extraction owned by one active, checksum-verified batch context."""
    def __init__(self, archive, binary, extraction):
        self.archive, self.binary, self.extraction = archive, binary, extraction
        self.executable = {"path": ARCHIVE_ROOT + "/blender", "sha256": digest(binary), "bytes": binary.stat().st_size}
        self.active = True


@contextmanager
def verified_reference(archive):
    """Reuse one verified official extraction; keep every test in a new process."""
    archive = Path(archive).resolve()
    if not archive.is_file() or archive.stat().st_size != ASSET_BYTES or digest(archive) != ASSET_SHA256:
        raise Blocked("native batch archive differs from the pinned official release")
    with tempfile.TemporaryDirectory(prefix="blended-native-batch-") as directory:
        root = Path(directory)
        extraction = extract_reference(archive, root)
        binary = (root / ARCHIVE_ROOT / "blender").resolve()
        if not binary.is_relative_to(root) or not binary.is_file():
            raise Blocked("native batch archive has no confined Blender executable")
        reference = _VerifiedReference(archive, binary, extraction)
        try:
            yield reference
        finally:
            reference.active = False


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


def load_suites(local_paths, work, cohort="numeric", fixture_root=None, catalog=None):
    return prepare_suites(local_paths, work, catalog or load_suite_catalog(cohort), require_complete=True, fixture_root=fixture_root)


def probe(args, report, reference=None):
    output = args.output.resolve()
    log_path = output / "native-reference.log"
    with tempfile.TemporaryDirectory(prefix="blended-native-reference-") as temporary:
        work = Path(temporary)
        archive = args.asset.resolve() if args.asset else work / "reference.tar.xz"
        if reference is not None:
            if not isinstance(reference, _VerifiedReference) or not reference.active or archive != reference.archive:
                raise Blocked("native batch reference is invalid or no longer active")
            if digest(reference.binary) != reference.executable["sha256"]:
                raise Blocked("native batch executable changed between isolated invocations")
        if args.asset is None:
            download(ASSET_URL, archive, ASSET_BYTES)
        if not archive.is_file():
            raise Blocked("native reference archive is missing")
        report["artifact"]["observed_bytes"] = archive.stat().st_size
        if archive.stat().st_size != ASSET_BYTES:
            raise Blocked("native artifact byte count differs from the pinned release")
        measured_digest = ASSET_SHA256 if reference is not None else digest(archive)
        report["artifact"]["observed_sha256"] = measured_digest
        if measured_digest != ASSET_SHA256:
            raise Blocked("native artifact checksum differs from the pinned official release")
        report["official_release_checksum_verified"] = True
        cohort = getattr(args, "cohort", "numeric")
        catalog = load_suite_catalog(cohort, getattr(args, "suite_manifest", None),
                                     getattr(args, "suite_manifest_sha256", None), allow_discovery=getattr(args, "discover", False))
        report["cohort"] = {key: value for key, value in catalog.items() if key != "suites"}
        report["cohort"]["complete_cohort_requested"] = True
        suites = load_suites(args.suite, work, cohort, fixture_root=getattr(args, "fixture_root", None), catalog=catalog)
        report["suite_sources"] = [suite_metadata(row) for row, _ in suites]
        report["input_fixture_transfer"] = preserve_suite_fixtures(suites, output / "fixtures")
        if reference is None:
            unpacked = work / "unpacked"
            unpacked.mkdir()
            report["extraction"] = extract_reference(archive, unpacked)
            binary = (unpacked / ARCHIVE_ROOT / "blender").resolve()
            if not binary.is_relative_to(unpacked.resolve()) or not binary.is_file():
                raise Blocked("native archive has no confined Blender executable")
            report["executable"] = {"path": str(binary.relative_to(unpacked)),
                                    "sha256": digest(binary), "bytes": binary.stat().st_size}
        else:
            binary = reference.binary
            report["extraction"] = {**reference.extraction, "shared_verified_extraction": True}
            report["executable"] = dict(reference.executable)
        marker = "BLENDED_NATIVE_REFERENCE_" + secrets.token_hex(12) + ":"
        io_root = str(work / "original-io") if catalog.get("suite_kind") == "original-script" else None
        if io_root:
            report["io_execution_root"] = io_root
        runner = work / "native-runner.py"
        runner.write_text(python_payload(suites, marker, io_root), encoding="utf-8")
        report["runner_sha256"] = digest(runner)
        flags = catalog.get("blender_args") or (["--background", "--factory-startup", "--threads", "1", "--python-exit-code", "1"] + catalog.get("extra_blender_args", []))
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
        transport_suffixes = []
        with log_path.open(encoding="utf-8", errors="replace") as log:
            for line in log:
                if line.startswith(marker):
                    result, suffix = decode_qualification_event(line, marker)
                    received.append(result)
                    transport_suffixes.append(suffix)
        if len(received) != 1:
            raise RuntimeError("native execution did not emit exactly one complete result marker")
        result = received[0]
        report["execution"] = result
        report["transport"] = {"protocol": "marker-prefixed-json-v1", "result_markers": 1,
            "recovered_json_prefix": bool(transport_suffixes[0]),
            "trailing_runtime_text": transport_suffixes[0] or None}
        report.update(summarize_execution(result, report["suite_sources"]))
        if transport_suffixes[0]:
            report["status"] = "failed"
            report["blockers"].append({"scope": "transport", "status": "failed",
                "reason": "runtime text followed complete qualification JSON", "trailing_runtime_text": transport_suffixes[0]})
        if io_root:
            try:
                try:
                    from .probe_io_files import native_reader, retrieve_files
                except ImportError:
                    from probe_io_files import native_reader, retrieve_files
                report["generated_file_transfer"] = retrieve_files(
                    result.get("generated_files"), io_root + "/files", output / "blendfiles",
                    native_reader(io_root + "/files"), "native-filesystem")
            except Exception as error:
                report["status"] = "failed"
                report["generated_file_transfer"] = {"status": "failed", "reason": str(error)}
                report["blockers"].append({"scope": "file_transport", "status": "failed", "reason": str(error)})
        if process.returncode != 0:
            report["status"] = "failed"
            report["blockers"].append({"scope": "native_runtime", "status": "failed",
                                       "reason": "native Blender exited with code " + str(process.returncode)})
        report["reason"] = (
            "All selected unchanged upstream test files passed on the checksum-verified official "
            "Blender 5.2.0 native release, with matching reported upstream build identity."
            if report["status"] == "passed" else
            "; ".join(row["scope"] + ": " + row["reason"] for row in report["blockers"]))


def main(argv=None, *, reference=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, help="Local exact official Blender 5.2.0 Linux x64 tar.xz")
    parser.add_argument("--suite", action="append", type=Path,
                        help="Local exact pinned suite file; supply all files in the selected cohort")
    parser.add_argument("--fixture-root", type=Path,
                        help="Local exact cohort fixtures under their original tests/files relative paths")
    parser.add_argument("--cohort", choices=("numeric", "data52", "blendio52", "liblink52"), default="numeric",
                        help="Selected fixed native suite inventory; default keeps the original 192 numerical tests")
    parser.add_argument("--suite-manifest", type=Path, help="Hash-bound external original unittest invocation")
    parser.add_argument("--suite-manifest-sha256", help="Expected SHA-256 of --suite-manifest")
    parser.add_argument("--discover", action="store_true", help="Run an unfrozen proposal to observe original native leaf IDs")
    parser.add_argument("--freeze-manifest", type=Path, help="Write a new browser-ready manifest bound to this native report")
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
        if args.discover and (not args.suite_manifest or not args.freeze_manifest):
            raise Blocked("native discovery requires --suite-manifest and --freeze-manifest")
        if args.freeze_manifest and not args.discover:
            raise Blocked("--freeze-manifest requires a fresh --discover invocation")
        if args.timeout <= 0 or args.timeout > 600:
            raise Blocked("timeout must be between 1 and 600 seconds")
        probe(args, report, reference=reference)
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
    if args.freeze_manifest:
        try:
            try:
                from .unittest_cohort import freeze_manifest
            except ImportError:
                from unittest_cohort import freeze_manifest
            frozen = freeze_manifest(args.suite_manifest, args.suite_manifest_sha256, evidence, args.freeze_manifest)
            print(json.dumps({"native_discovery": "frozen", **frozen}))
        except (OSError, ValueError, TypeError) as error:
            print(json.dumps({"native_discovery": "blocked", "reason": str(error)}))
            return 1
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
