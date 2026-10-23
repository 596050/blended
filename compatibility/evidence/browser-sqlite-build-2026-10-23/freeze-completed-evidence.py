#!/usr/bin/env python3
"""Preserve completed component receipts without changing any original attempt."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO.parent / "runtime/browser-sqlite-work"


def identity(path):
    data = path.read_bytes()
    try:
        location = path.relative_to(REPO).as_posix()
    except ValueError:
        location = str(path)
    return {"path": location, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_attempt(name):
    path = HERE / name / "execution.json"
    return json.loads(path.read_text()), identity(path)


def main():
    if (HERE / "summary.json").exists():
        raise FileExistsError("completed summary is immutable")
    copies = []
    profiles = [
        ("python-component-artifact-1", "python-component-build", ["build.json", "build.log", "cache-verification.log", "stdlib-files.json"]),
        ("python-diagnostic-artifact-1", "python-diagnostic-build-1", ["build.json", "build.log", "diagnostic-pre.js"]),
    ]
    archive_entries = []
    for source_name, destination_name, names in profiles:
        source = WORK / source_name
        destination = HERE / destination_name
        destination.mkdir(exist_ok=False)
        report = json.loads((source / "build.json").read_text())
        assert report["completed_successfully"] and report["returncode"] == 0
        for item in report["artifacts"]:
            actual = identity(Path(item["path"]))
            assert all(actual[key] == item[key] for key in ("bytes", "sha256"))
        for name in names:
            target = destination / name
            shutil.copyfile(source / name, target)
            assert target.read_bytes() == (source / name).read_bytes()
            copies.append({"source": identity(source / name), "preserved": identity(target)})
        archive_entries.append((f"profiles/{source_name}/python-sqlite.js", source / "python-sqlite.js"))
    original_artifact = WORK / profiles[0][0]
    diagnostic_artifact = WORK / profiles[1][0]
    for suffix in ("wasm", "data"):
        filename = f"python-sqlite.{suffix}"
        assert (original_artifact / filename).read_bytes() == (diagnostic_artifact / filename).read_bytes()
        archive_entries.append((f"common/{filename}", original_artifact / filename))
    source_inputs = json.loads((HERE / "original-disk-hash-inputs.json").read_text())
    for source in source_inputs["files"]:
        path = WORK / "component-original" / source["upstream_path"]
        actual = identity(path)
        assert all(actual[key] == source[key] for key in ("bytes", "sha256"))
        archive_entries.append((f"original/{source['upstream_path']}", path))
    archive_entries.sort()
    archive_path = HERE / "python-component-artifacts.tar.gz"
    with archive_path.open("xb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for member_name, source in archive_entries:
                    member = tarfile.TarInfo(member_name)
                    member.size = source.stat().st_size
                    member.mode = 0o644
                    member.mtime = 0
                    with source.open("rb") as data:
                        archive.addfile(member, data)
    archived = []
    with tarfile.open(archive_path, "r:gz") as archive:
        for member_name, source in archive_entries:
            data = archive.extractfile(member_name).read()
            actual = identity(source)
            assert len(data) == actual["bytes"] and hashlib.sha256(data).hexdigest() == actual["sha256"]
            archived.append({"member": member_name, "source": actual})
    preservation = {"schema": 1, "kind": "exact-completed-component-preservation", "copies": copies,
                    "archive": identity(archive_path), "members": archived,
                    "original_receipts_rewritten": False, "shared_wasm_and_preload_are_byte_identical": True}
    (HERE / "preservation.json").write_text(json.dumps(preservation, indent=2) + "\n")
    attempts = []
    notes = {
        "sqlite-attempt-1": "Source extraction failed when restoring archive ownership in the sandbox; no successful build claimed.",
        "sqlite-attempt-2": "SQLite compiled, but the cache recorder rejected the SDK's legitimate confined clang symlink; no successful harvest claimed.",
        "sqlite-attempt-3": "Real SQLite 3.51.3 archive compiled and its cache receipt was recorded successfully.",
        "python-attempt-1": "Real CPython 3.13.13 configured and compiled its original _sqlite3 extension against the pinned SQLite archive; symbol and cache verification passed.",
        "sqlite-component-node": "Separate real SQLite C diagnostic completed in Node; it is not an original Blender test.",
        "sqlite-component-browser": "The same SQLite C diagnostic completed in Chrome; it is not an original Blender test.",
        "original-disk-hash-node-attempt-1": "The exact original test and package bytes were loaded, but the package initializer requires bpy. The standalone interpreter exited before discovering any of the 12 expected cases.",
        "original-disk-hash-browser-attempt-1": "The exact original test and package bytes were loaded in Chrome, but the package initializer requires bpy. The standalone interpreter exited before discovering any of the 12 expected cases.",
        "native-python-diagnostic-1": "The separately authored binding diagnostic failed at its WAL-derived serialization round-trip assumption with sqlite3.OperationalError: unable to open database file.",
        "python-sqlite-browser-diagnostic-1": "The same separately authored binding diagnostic failed at the same line and exception as native Blender's bundled Python. This is not evidence of a browser-only defect or a completed binding diagnostic pass.",
    }
    for name, note in notes.items():
        report, binding = read_attempt(name)
        row = {"attempt": name, "receipt": binding, "interpretation": note}
        for key in ("returncode", "runtime_exit", "completed_successfully", "elapsed_seconds"):
            if key in report:
                row[key] = report[key]
        if "commands" in report:
            row["command_results"] = [{key: command[key] for key in ("returncode", "elapsed_seconds")} for command in report["commands"]]
        if "case_reconciliation" in report:
            cases = report["case_reconciliation"]
            assert len(cases["expected_case_ids"]) == 12
            assert not cases["observed_cases"] and len(cases["missing_case_ids"]) == 12
            assert not cases["complete_original_module_pass_in_component"]
            row.update(expected_cases=12, observed_cases=0, case_passes=0, blocked_cases=12,
                       missing_case_ids=cases["missing_case_ids"], blocker="ModuleNotFoundError: No module named 'bpy'")
        attempts.append(row)
    manifest = REPO / "patches/browser-sqlite/manifest.json"
    assert identity(manifest)["sha256"] == "4c3d9fe421f461854a77abc36fa1580dba3e11abbeb39f3d7bf409bf36e8a57d"
    summary = {
        "schema": 1,
        "kind": "browser-sqlite-component-implementation-summary",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "summary_driver": identity(Path(__file__).resolve()),
        "patchset": identity(manifest),
        "preparation_helper": identity(REPO / "tools/prepare_browser_sqlite.py"),
        "source_commit": "fbe6228777e7d9afefcd61a413844e790ae75db7",
        "port_commit": "0e02e84b2bc5d9b27a6dc6e275443292f781fbad",
        "sqlite_version": "3.51.3", "python_version": "3.13.13", "emscripten_version": "6.0.5",
        "sqlite_archive_build_completed": True, "cpython_sqlite_extension_build_completed": True,
        "separate_c_component_completed_in_node_and_chrome": True,
        "separate_python_binding_diagnostic_v1_completed_successfully": False,
        "original_blender_tests_modified": False, "original_blender_assertions_modified": False,
        "original_blender_driver_executed": False, "strict_blender_browser_test_passes": 0,
        "full_feature_parity": False,
        "original_disk_hash_expected_cases": 12, "original_disk_hash_observed_cases": 0,
        "original_disk_hash_remaining_gate": "Rebuild the actual Blender browser artifact with this patchset and execute the original invocation with real bpy and the unchanged native case identities.",
        "attempts": attempts, "preservation": identity(HERE / "preservation.json"),
        "copied_component_builds": [identity(HERE / item[1] / "build.json") for item in profiles],
        "independent_out_of_scope_followup_directory": "compatibility/evidence/browser-sqlite-python-validation-2026-10-23/",
        "not_established": ["complete Blender feature parity", "the 12 original disk hash case outcomes on a rebuilt Blender artifact",
                            "browser reload durability", "cross-tab or cross-process locking", "arbitrary dynamic native extensions"],
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"summary": identity(HERE / "summary.json"), "archive": identity(archive_path),
                      "preservation": identity(HERE / "preservation.json")}, indent=2))


if __name__ == "__main__":
    main()
