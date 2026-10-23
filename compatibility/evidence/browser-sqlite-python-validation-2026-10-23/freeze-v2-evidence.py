#!/usr/bin/env python3
"""Preserve and reconcile the separately authored Python binding diagnostic."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREVIOUS = REPO / "compatibility/evidence/browser-sqlite-build-2026-10-23"
ARTIFACT = REPO.parent / "runtime/browser-sqlite-work/python-diagnostic-artifact-2"


def identity(path):
    data = path.read_bytes()
    try:
        name = path.relative_to(REPO).as_posix()
    except ValueError:
        name = str(path)
    return {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    if (HERE / "summary.json").exists():
        raise FileExistsError("v2 evidence summary is immutable")
    native_path, browser_path = HERE / "native-v2/execution.json", HERE / "browser-v2/execution.json"
    native, browser = (json.loads(path.read_text()) for path in (native_path, browser_path))
    build_path = ARTIFACT / "build.json"
    build = json.loads(build_path.read_text())
    assert native["completed_successfully"] and native["returncode"] == 0
    assert browser["completed_successfully"] and browser["runtime_exit"] == 0
    assert browser["runtime_abort"] is None and not browser["page_errors"]
    assert build["completed_successfully"] and build["returncode"] == 0
    assert len(native["observations"]) == len(browser["component_observations"]) == 1
    left, right = native["observations"][0], browser["component_observations"][0]
    assert left.keys() == right.keys()
    differences = {key: {"native": left[key], "browser": right[key]} for key in left if left[key] != right[key]}
    assert differences == {"actual_builtin_extension": {"native": False, "browser": True}}
    source = identity(HERE / "probe_python_sqlite_v2.py")
    assert source["sha256"] == build["diagnostic_source"]["sha256"] == native["inputs"][1]["sha256"]
    assert source["bytes"] == build["diagnostic_source"]["bytes"] == native["inputs"][1]["bytes"]
    for item in browser["artifact_inputs"]:
        actual = identity(Path(item["path"]))
        assert all(actual[key] == item[key] for key in ("sha256", "bytes"))
    assert identity(build_path)["sha256"] == browser["build_receipt"]["sha256"]
    destination = HERE / "component-build-v2"
    destination.mkdir(exist_ok=False)
    copies = []
    for name in ("build.json", "build.log", "diagnostic-pre.js", "python-sqlite.js"):
        target = destination / name
        shutil.copyfile(ARTIFACT / name, target)
        assert target.read_bytes() == (ARTIFACT / name).read_bytes()
        copies.append({"source": identity(ARTIFACT / name), "preserved": identity(target)})
    common_archive = PREVIOUS / "python-component-artifacts.tar.gz"
    preservation = json.loads((PREVIOUS / "preservation.json").read_text())
    assert identity(common_archive) == preservation["archive"]
    shared = []
    with tarfile.open(common_archive, "r:gz") as archive:
        for suffix in ("wasm", "data"):
            filename = f"python-sqlite.{suffix}"
            member = "common/" + filename
            data = archive.extractfile(member).read()
            actual = identity(ARTIFACT / filename)
            assert len(data) == actual["bytes"] and hashlib.sha256(data).hexdigest() == actual["sha256"]
            shared.append({"member": member, "identity": actual})
    previous_diagnostic = [identity(PREVIOUS / name / "execution.json") for name in
                           ("native-python-diagnostic-1", "python-sqlite-browser-diagnostic-1")]
    previous_original_attempts = [identity(PREVIOUS / name / "execution.json") for name in
                                 ("original-disk-hash-node-attempt-1", "original-disk-hash-browser-attempt-1")]
    report = {
        "schema": 1, "kind": "independent-cpython-sqlite-binding-diagnostic-v2-summary",
        "created_utc": datetime.now(timezone.utc).isoformat(), "summary_driver": identity(Path(__file__).resolve()),
        "diagnostic_source": source, "documented_precondition": identity(HERE / "precondition-reference.json"),
        "native_execution": identity(native_path), "browser_execution": identity(browser_path),
        "native_sqlite_configuration": identity(PREVIOUS / "native-sqlite-configuration.json"),
        "patchset": identity(REPO / "patches/browser-sqlite/manifest.json"),
        "native_returncode": 0, "browser_runtime_exit": 0,
        "native_and_browser_diagnostic_completed_successfully": True,
        "native_and_browser_behavioral_observations_equal": True,
        "observed_metadata_differences": differences,
        "native_observations": left, "browser_observations": right,
        "v1_failed_native_and_browser_diagnostic_receipts_preserved": previous_diagnostic,
        "original_module_missing_bpy_receipts_preserved": previous_original_attempts,
        "preserved_build_files": copies, "shared_artifact_archive": identity(common_archive),
        "byte_identical_shared_artifacts": shared,
        "original_blender_tests_modified": False, "original_blender_tests_executed": False,
        "strict_blender_browser_test_passes": 0, "original_disk_hash_cases_still_unobserved": 12,
        "full_feature_parity": False,
        "remaining_gate": "Execute all original disk hash cases with real bpy in the rebuilt Blender browser application.",
    }
    (HERE / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(identity(HERE / "summary.json"), indent=2))


if __name__ == "__main__":
    main()
