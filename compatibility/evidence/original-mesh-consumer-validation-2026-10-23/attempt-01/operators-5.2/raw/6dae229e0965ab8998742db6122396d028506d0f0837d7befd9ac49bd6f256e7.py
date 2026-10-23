#!/usr/bin/env python3
"""Measure the augmented package independently of any Blender test outcome."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT.parent / "runtime"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.browser_package_overlay import verify_overlay_receipt


def record(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest}


def write(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


started = datetime.now(timezone.utc).isoformat()
base_context_path = ROOT / "compatibility/evidence/runtime-context-2026-10-23/browser-context.json"
context = json.loads(base_context_path.read_bytes())
source = base_context_path.parent / "source-build.json"
receipt = ROOT / "compatibility/evidence/brush-package-overlay-5.2-2026-10-23/package-overlay.json"
base_archive = RUNTIME / "source/blender-source-development.tar.gz"
augmented_archive = RUNTIME / "brush-package-overlay-5.2/blender-source-development-essentials.tar.gz"
verified = verify_overlay_receipt(receipt, source, base_archive=base_archive, augmented_archive=augmented_archive)
engine_files = []
with tarfile.open(augmented_archive, "r:gz") as archive:
    for member in archive:
        if member.name in {
            "blender-source-development/bin/blender_browser.data",
            "blender-source-development/bin/blender_browser.js",
            "blender-source-development/bin/blender_browser.wasm",
        }:
            assert member.isfile()
            with archive.extractfile(member) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            engine_files.append({"path": member.name, "bytes": member.size, "sha256": digest})
assert len(engine_files) == 3
engine_files.sort(key=lambda row: row["path"])
measurement = {
    "schema": 1,
    "kind": "verified-browser-package-measurement",
    "started_utc": started,
    "finished_utc": datetime.now(timezone.utc).isoformat(),
    "measurement_tool": record(Path(__file__)),
    "verification_tool": record(ROOT / "tools/browser_package_overlay.py"),
    "base_context": record(base_context_path),
    "source_build_receipt": record(source),
    "package_overlay_receipt": record(receipt),
    "base_artifact": record(base_archive),
    "artifact": record(augmented_archive),
    "engine_files": engine_files,
    "package_overlay": verified,
    "tests_executed": 0,
    "scope": "Archive content verification and engine member identities only; no test outcomes or runtime behavior inferred.",
}
write(OUT / "package-measurement.json", measurement)
context["engine_archive"] = record(augmented_archive)
context["source_build_receipt"] = {
    **record(source), "path": "../runtime-context-2026-10-23/source-build.json"}
cache = base_context_path.parent / "CMakeCache.txt"
context["build_configuration"] = {
    **record(cache), "path": "../runtime-context-2026-10-23/CMakeCache.txt"}
context["package_overlay_receipt"] = {
    **record(receipt), "path": "../brush-package-overlay-5.2-2026-10-23/package-overlay.json"}
context["package_base_asset"] = record(base_archive)
context["package_overlay_measurement"] = {
    **record(OUT / "package-measurement.json"), "path": "package-measurement.json"}
context["limitations"].append(
    "Augmented package is a distinct artifact with independent test obligations; original artifact passes are not transferred.")
write(OUT / "browser-context.json", context)
print(json.dumps({"context": record(OUT / "browser-context.json"),
                  "measurement": record(OUT / "package-measurement.json"), "tests_executed": 0}))
