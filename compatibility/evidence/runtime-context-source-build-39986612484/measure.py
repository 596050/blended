#!/usr/bin/env python3
"""Independently bind the new CI package and the exact official Chrome binary."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUNTIME = ROOT.parent / "runtime/source-build-39986612484"
BUILD = RUNTIME / "browser-source-development-39986612484"
RAW = ROOT / "compatibility/evidence/source-rebuild-unittest-39986612484"
CI = ROOT / "compatibility/evidence/source-rebuild-codecs-sqlite-5.2-2026-10-23"
OFFICIAL = RUNTIME / "chrome-official-inspection"
sys.path.insert(0, str(ROOT))
from tools.browser_package_overlay import verify_overlay_receipt
from tools.reconcile_unittest_matrix import CI_CWD_BASIS, CI_PRODUCER_COMMIT, CI_PRODUCER_FILES, CI_PRODUCER_RULE, CI_SOURCE_MODE


def record(path, relative=False):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    name = path.relative_to(OUT).as_posix() if relative else str(path.resolve())
    return {"path": name, "bytes": path.stat().st_size, "sha256": digest}


def write(name, value):
    with (OUT / name).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def copy(source, relative):
    destination = OUT / relative
    assert source.is_file() and not source.is_symlink() and not destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(source.read_bytes())
    assert record(source)["sha256"] == record(destination)["sha256"]
    return destination


started = datetime.now(timezone.utc).isoformat()
assert not (OUT / "browser-context.json").exists()
copied = []
for name in ("Packages", "Packages.gz", "metadata-receipt.json", "exact-package-head.json", "package-download.json",
             "package-control.txt", "measurement.json", "version.stdout.log", "version.stderr.log",
             "measure-official-package.py", "measure-official-package-v2.py", "attempt-01-failure.json"):
    copied.append(copy(OFFICIAL / name, "chrome/" + name))
official = json.loads((OUT / "chrome/measurement.json").read_bytes())
assert official["exact_ci_binary_match"] is True and official["version_exit_code"] == 0
measured_binary = record(OFFICIAL / "chrome")
assert (measured_binary["bytes"], measured_binary["sha256"]) == (
    297798984, "9bfb381296dffe75f3419d07b6cc64525105ed117d1453a4ef3b291cb97d2b58")
assert {key: official["binary"][key] for key in ("bytes", "sha256")} == {
    key: measured_binary[key] for key in ("bytes", "sha256")}
version_raw = (OUT / "chrome/version.stdout.log").read_text()
version_match = re.fullmatch(r"Google Chrome ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) unknown\n", version_raw)
assert version_match and version_raw == official["version_stdout"]
version = version_match.group(1)
source = copy(BUILD / "source-build.json", "source-build.json")
cache = copy(BUILD / "CMakeCache.txt", "CMakeCache.txt")
receipt = copy(BUILD / "essentials/package-overlay.json", "package-overlay.json")
verifier = copy(ROOT / "tools/browser_package_overlay.py", "browser_package_overlay.py")
run = copy(CI / "public-run-completed.json", "ci-run.json")
workflow_bytes = subprocess.check_output(["git", "show", CI_PRODUCER_COMMIT + ":.github/workflows/browser-source-build.yml"], cwd=ROOT)
assert (len(workflow_bytes), hashlib.sha256(workflow_bytes).hexdigest()) == CI_PRODUCER_FILES["workflow"][1:]
with (OUT / "browser-source-build.yml").open("xb") as stream:
    stream.write(workflow_bytes)
producer = {"schema": 1, "kind": "source-derived-frozen-producer-context", "rule": CI_PRODUCER_RULE,
    "source_commit": CI_PRODUCER_COMMIT, "run_id": 39986612484, "ci_run": record(run, True),
    "checkout_root": "/home/runner/work/blended/blended",
    "original_entrypoint": "/home/runner/work/blended/blended/tools/run_unittest_browser_matrix.py",
    "cwd_basis": CI_CWD_BASIS, "os_cwd_observed": False, "source_mode": CI_SOURCE_MODE,
    "workflow": {**record(OUT / "browser-source-build.yml", True), "upstream_path": CI_PRODUCER_FILES["workflow"][0]},
    "matrices": [{"plan": name, "matrix": record(RAW / name / "matrix.json")} for name in ("main", "resources")],
    "limitations": ["The actual OS cwd was not recorded in the host receipt.",
                    "The cwd and source acquisition mode are derived only for these exact immutable producer and workflow bytes."]}
for field in ("matrix_driver", "probe"):
    path, size, digest = CI_PRODUCER_FILES[field]
    file = RAW / "main/harness" / path
    pin = record(file)
    assert (pin["bytes"], pin["sha256"]) == (size, digest)
    producer[field] = {**pin, "upstream_path": path}
write("producer-context.json", producer)
base_archive = BUILD / "blender-source-development.tar.gz"
augmented_archive = BUILD / "essentials/blender-source-development-essentials.tar.gz"
verified = verify_overlay_receipt(receipt, source, base_archive=base_archive, augmented_archive=augmented_archive)
engine_files = []
with tarfile.open(augmented_archive, "r:gz") as archive:
    for member in archive:
        if member.name in {"blender-source-development/bin/blender_browser." + suffix for suffix in ("data", "js", "wasm")}:
            assert member.isfile()
            with archive.extractfile(member) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            engine_files.append({"path": member.name, "bytes": member.size, "sha256": digest})
assert len(engine_files) == 3
engine_files.sort(key=lambda row: row["path"])
flags = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-watchdog", "--enable-unsafe-webgpu",
         "--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
for name in ("main", "resources"):
    matrix = json.loads((RAW / name / "matrix.json").read_bytes())
    assert all(matrix["browser_executable"][field] == measured_binary[field] for field in ("bytes", "sha256"))
    for qualification in sorted((RAW / name).glob("*/qualification.json")):
        observed = json.loads(qualification.read_bytes())
        assert observed["browser"]["version"] == version and observed["browser"]["flags"] == flags
context = {"schema": 1, "kind": "artifact-bound-browser-context",
    "upstream": {"repository": "blender/blender", "commit": "fbe6228777e7d9afefcd61a413844e790ae75db7", "version": "5.2.0"},
    "browser": {**measured_binary, "version": "Google Chrome " + version, "numeric_version": version,
        "version_raw_stdout": version_raw,
        "version_field_basis": "Normalized product name plus the four-component numeric token parsed from the preserved independent --version stdout; the trailing unknown build label is retained above.",
        "archive": {**official["package"], "url": json.loads((OUT / "chrome/package-download.json").read_bytes())["url"]}},
    "engine_archive": record(base_archive), "source_build_receipt": record(source, True),
    "build_configuration": record(cache, True), "requested_flags": flags,
    "raw_evidence": [record(path, True) for path in copied],
    "profile_scope": "GitHub-hosted headless Chrome with software GPU requested. The engine-selected GPU is not instrumented.",
    "limitations": ["The independently downloaded official package's exact ELF matches the producer-reported CI browser digest; CI process behavior is not independently re-executed.",
        "Source receipt, CMake cache and measured archives are bound, but no independent source-to-binary rebuild correspondence is claimed.",
        "Original background Python observations do not qualify editor UI, hardware profiles, deployed sessions or Blender5.4.",
        CI_CWD_BASIS]}
write("base-browser-context.json", context)
measurement = {"schema": 1, "kind": "verified-browser-package-measurement", "started_utc": started,
    "finished_utc": datetime.now(timezone.utc).isoformat(), "measurement_tool": record(Path(__file__)),
    "verification_tool": record(verifier), "base_context": record(OUT / "base-browser-context.json"),
    "source_build_receipt": record(source), "package_overlay_receipt": record(receipt),
    "base_artifact": record(base_archive), "artifact": record(augmented_archive), "engine_files": engine_files,
    "package_overlay": verified, "tests_executed": 0,
    "scope": "Actual archive content and engine-member verification plus separate official Chrome ELF measurement; no Blender execution or test result inferred."}
write("package-measurement.json", measurement)
context.update(engine_archive=record(augmented_archive), package_overlay_receipt=record(receipt, True),
               package_base_asset=record(base_archive), package_overlay_measurement=record(OUT / "package-measurement.json", True),
               source_derived_producer_context=record(OUT / "producer-context.json", True))
context["limitations"].append("This package and browser identity form a distinct candidate profile; no old package passes are transferred.")
write("browser-context.json", context)
write("preservation.json", {"schema": 1, "measurement_script": record(Path(__file__)),
    "context": record(OUT / "browser-context.json"), "measurement": record(OUT / "package-measurement.json"),
    "preserved_files": [record(path, True) for path in sorted(OUT.rglob("*")) if path.is_file()],
    "tests_executed": 0, "full_feature_parity": False})
print(json.dumps({"context": record(OUT / "browser-context.json"), "measurement": record(OUT / "package-measurement.json"),
                  "exact_chrome_binary_match": True, "tests_executed": 0}))
