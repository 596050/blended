#!/usr/bin/env python3
"""Qualify a pinned Blender browser artifact using unchanged upstream tests.

This is a local browser qualification requesting a software GPU, not native-oracle,
hardware, deployed, or full Blender parity evidence. The observed adapter is
recorded separately. All failures still produce qualification.json.
Requires Playwright and a Chromium installation. No paid service is used.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.server
import json
from pathlib import Path, PurePosixPath
import secrets
import shutil
import socketserver
import tarfile
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request

UPSTREAM_SHA = "fbe6228777e7d9afefcd61a413844e790ae75db7"
PORT_SOURCE_SHA = "cc22090b88da63cc617d48b218f4945175928844"
DEVELOPMENT_PORT_SHA = "0e02e84b2bc5d9b27a6dc6e275443292f781fbad"
DEVELOPMENT_PATCH_SHA256 = "04ba2e6ba8a04ef37bdaf879b10a135736f07114597a908bbbdea8bba244193c"
NUMERIC_PATCHSET_ID = "blender-5.2.0-web-numerics-v1"
NUMERIC_PATCH_MANIFEST = Path(__file__).resolve().parents[1] / "patches/browser-numerics/manifest.json"
ASSET_URL = "https://github.com/gessa-ai/blender-web/releases/download/v0.1.1/blender-web-local-v0.1.1.tar.gz"
ASSET_SHA256 = "1af405cd00d3471e105a39dad24a628aeb988f77b372c4c21bbf85ccbdca2ee0"
ASSET_BYTES = 108802132
SUITES = {
    "bl_pyapi_mathutils.py": "c5e252adc5fc80590faca2c667ba81d0ff732f682e1d866f1d4a0050b21a99af",
    "bl_pyapi_bmesh.py": "7dd9b28372ca371420c98e11bed49aff07f4fbe008c0fc1685cb9b5bc6721329",
}
SUITE_BYTES = {"bl_pyapi_mathutils.py": 41853, "bl_pyapi_bmesh.py": 32918}
DATA_SUITE_MANIFEST = Path(__file__).resolve().parents[1] / "compatibility/candidate-suites/data-5.2.json"
DATA_SUITE_MANIFEST_SHA256 = "3a1d1a942978461f655ab127faad4bc0c2c3b32210029af9117f5ded03e55085"
IO_SUITE_MANIFEST = Path(__file__).resolve().parents[1] / "compatibility/candidate-suites/blendio-5.2.json"
IO_SUITE_MANIFEST_SHA256 = "2cccdb42ff82628b34abb6838ce4a77758bfd442d17328f301b1ef1b80fbf497"
LIBLINK_SUITE_MANIFEST = Path(__file__).resolve().parents[1] / "compatibility/candidate-suites/liblink-5.2.json"
LIBLINK_SUITE_MANIFEST_SHA256 = "027da2aee878fbd44f7cc66c21b084241646aae3da4eab5d9bad2ad466f11537"


class Blocked(RuntimeError):
    """Required execution infrastructure or provenance is unavailable."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def load_suite_catalog(cohort="numeric", manifest_path=None, manifest_sha256=None, *, allow_discovery=False):
    """Select an independently frozen native denominator, never browser discovery."""
    if manifest_path is not None or manifest_sha256 is not None:
        if cohort != "numeric" or manifest_path is None or manifest_sha256 is None:
            raise Blocked("an external suite manifest requires its checksum and cannot be combined with a named cohort")
        try:
            try:
                from .unittest_cohort import load_manifest
            except ImportError:
                from unittest_cohort import load_manifest
            return load_manifest(manifest_path, manifest_sha256, allow_discovery=allow_discovery)
        except ValueError as error:
            raise Blocked(str(error)) from error
    if cohort == "numeric":
        counts = {"bl_pyapi_mathutils.py": 180, "bl_pyapi_bmesh.py": 12}
        return {"id": "numeric-5.2", "manifest_sha256": None, "expected_cases": 192, "suite_kind": "unittest",
                "suites": [{"upstream_path": "tests/python/" + name, "sha256": value,
                            "bytes": SUITE_BYTES[name], "expected_cases": counts[name]}
                           for name, value in SUITES.items()]}
    specifications = {
        "data52": (DATA_SUITE_MANIFEST, DATA_SUITE_MANIFEST_SHA256, "data-5.2", "unittest", 3, 48),
        "blendio52": (IO_SUITE_MANIFEST, IO_SUITE_MANIFEST_SHA256, "blendio-5.2", "original-script", 1, 4),
        "liblink52": (LIBLINK_SUITE_MANIFEST, LIBLINK_SUITE_MANIFEST_SHA256, "liblink-5.2", "original-script", 1, 17),
    }
    if cohort not in specifications:
        raise Blocked("unknown candidate suite cohort: " + str(cohort))
    path, manifest_digest, cohort_id, suite_kind, module_count, case_count = specifications[cohort]
    if not path.is_file() or digest(path) != manifest_digest:
        raise Blocked("candidate suite manifest is missing or changed: " + cohort_id)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != 1 or manifest.get("cohort_id") != cohort_id or
            manifest.get("suite_kind") != suite_kind or
            manifest.get("upstream", {}).get("commit") != UPSTREAM_SHA):
        raise Blocked("candidate suite manifest differs from the selected reference")
    suites = manifest.get("suites", [])
    if len(suites) != module_count:
        raise Blocked("candidate cohort must retain every original module")
    for row in suites:
        ids = row.get("case_ids", [])
        if (not ids or len(ids) != len(set(ids)) or row.get("expected_cases") != len(ids) or
                set(row.get("mandatory_case_ids", [])) != set(ids)):
            raise Blocked("candidate cohort lost its fixed mandatory cases")
    count = sum(len(row["case_ids"]) for row in suites)
    if count != case_count or manifest.get("expected_total_cases") != count:
        raise Blocked("candidate cohort denominator changed")
    selected = []
    for row in suites:
        entry = {key: row[key] for key in ("upstream_path", "sha256", "bytes", "expected_cases", "case_ids")}
        if suite_kind == "original-script":
            support = row.get("support_files", [])
            if len(support) != 1 or support[0].get("upstream_path") != "tests/python/bl_blendfile_utils.py":
                raise Blocked("original blend-file driver requires its pinned upstream helper")
            entry["support_files"] = [{key: source[key] for key in ("upstream_path", "sha256", "bytes")}
                                      for source in support]
            entry["driver"] = suite_kind
            # tests/CMakeLists.txt supplies --background to add_blender_test.
            # Windowed file loading deliberately clears CTX_wm_window.
            entry["required_background"] = True
            if cohort == "liblink52":
                fixtures = row.get("fixture_files", [])
                if len(fixtures) != 3 or sum(value.get("bytes", 0) for value in fixtures) != 213000:
                    raise Blocked("library cohort lost its fixed fixture inventory")
                entry["fixture_files"] = fixtures
                entry["fixture_directory_argument"] = "--src-test-dir"
        selected.append(entry)
    return {"id": cohort_id, "manifest_sha256": manifest_digest,
            "expected_cases": count, "suite_kind": suite_kind, "suites": selected,
            "extra_blender_args": ["--disable-autoexec"] if cohort == "liblink52" else []}


def prepare_suites(local_paths, work, catalog, require_complete=False, fixture_root=None):
    all_sources = [source for row in catalog["suites"] for source in (row, *row.get("support_files", []))]
    by_name = {PurePosixPath(row["upstream_path"]).name: row for row in all_sources}
    if len(by_name) != len(all_sources):
        raise Blocked("candidate suite and helper names must be unambiguous")
    supplied = {}
    for path in local_paths or []:
        if path.name not in by_name or path.name in supplied:
            raise Blocked("unknown or duplicate pinned suite: " + path.name)
        supplied[path.name] = path.resolve()
    if local_paths and (require_complete or catalog["id"] != "numeric-5.2") and set(supplied) != set(by_name):
        raise Blocked("every original module and helper in the selected cohort is required")
    def load_source(source):
        name = PurePosixPath(source["upstream_path"]).name
        row = dict(source)
        row["url"] = "https://raw.githubusercontent.com/blender/blender/" + UPSTREAM_SHA + "/" + row["upstream_path"]
        path = supplied.get(name, work / name)
        if not local_paths:
            download(row["url"], path, row["bytes"])
        if not path.is_file() or path.stat().st_size != row["bytes"]:
            raise Blocked("suite is missing or its byte count changed: " + name)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise Blocked("suite bytes differ from the immutable upstream source: " + name)
        return row, data
    suites = []
    for source in catalog["suites"]:
        if local_paths and PurePosixPath(source["upstream_path"]).name not in supplied:
            continue
        row, data = load_source(source)
        if source.get("support_files"):
            row["_support_payloads"] = []
            row["support_files"] = []
            for support_source in source["support_files"]:
                helper_row, helper_data = load_source(support_source)
                row["support_files"].append(helper_row)
                row["_support_payloads"].append({**helper_row, "source_b64": base64.b64encode(helper_data).decode("ascii")})
        if source.get("fixture_files"):
            try:
                from .probe_blender_fixtures import prepare_fixture_payloads
            except ImportError:
                from probe_blender_fixtures import prepare_fixture_payloads
            row["_fixture_payloads"] = prepare_fixture_payloads(
                source["fixture_files"], UPSTREAM_SHA, work / "fixtures", local_root=fixture_root)
        suites.append((row, data))
    return suites


def suite_metadata(row):
    """Keep transported helper bytes out of the public source identity rows."""
    return {key: value for key, value in row.items() if key not in ("_support_payloads", "_fixture_payloads")}


def preserve_suite_fixtures(suites, destination):
    payloads = [value for row, _ in suites for value in row.get("_fixture_payloads", [])]
    if not payloads:
        return None
    try:
        from .probe_blender_fixtures import preserve_fixture_payloads
    except ImportError:
        from probe_blender_fixtures import preserve_fixture_payloads
    return preserve_fixture_payloads(payloads, destination)


def canonical_case_id(value, source=None):
    """Normalize only the injected module prefix, preserving class and method."""
    if not isinstance(value, str) or "." not in value:
        raise RuntimeError("case ID has no runtime module prefix")
    if source and source.get("case_id_normalization") == "original-main":
        return value.removeprefix("__main__.")
    return value.split(".", 1)[1]


def validate_numeric_patchset(receipt):
    """Bind additional engine/toolchain changes to this checkout's manifest.

    Historical unpatched development receipts remain distinguishable. A new
    patch declaration must never silently inherit that baseline's identity.
    """
    if "numeric_patchset" not in receipt:
        return None
    observed = receipt["numeric_patchset"]
    if not isinstance(observed, dict) or observed.get("applied") is not True:
        raise Blocked("numeric patchset receipt is incomplete or was not applied")
    if not NUMERIC_PATCH_MANIFEST.is_file() or NUMERIC_PATCH_MANIFEST.stat().st_size > 1_000_000:
        raise Blocked("independent numeric patchset manifest is unavailable")
    try:
        manifest = json.loads(NUMERIC_PATCH_MANIFEST.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as error:
        raise Blocked("independent numeric patchset manifest is invalid") from error
    if (not isinstance(manifest, dict) or type(manifest.get("schema")) is not int or
            manifest["schema"] != 1 or manifest.get("id") != NUMERIC_PATCHSET_ID or
            manifest.get("upstream_commit") != UPSTREAM_SHA or
            manifest.get("port_commit") != DEVELOPMENT_PORT_SHA):
        raise Blocked("numeric patchset manifest identity differs from this probe")
    patches = manifest.get("patches")
    keys = ("id", "component", "path", "before_sha256", "after_sha256", "patch_sha256")
    if not isinstance(patches, list) or len(patches) != 2 or any(
            not isinstance(p, dict) or any(not isinstance(p.get(k), str) or not p[k] for k in keys)
            for p in patches):
        raise Blocked("numeric patchset manifest does not identify both reviewed source changes")
    expected = {"id": manifest["id"], "manifest_sha256": digest(NUMERIC_PATCH_MANIFEST),
                "applied": True, "patches": [{k: patch[k] for k in keys} for patch in patches]}
    if any(observed.get(key) != expected[key] for key in ("id", "manifest_sha256", "applied")):
        raise Blocked("numeric patchset receipt differs from the reviewed manifest")
    declared = observed.get("patches")
    if (not isinstance(declared, list) or len(declared) != len(patches) or
            any(not isinstance(patch, dict) for patch in declared) or
            [{key: patch.get(key) for key in keys} for patch in declared] != expected["patches"]):
        raise Blocked("numeric source patch identities are missing or changed")
    compiler = receipt.get("compiler", {})
    toolchain = manifest.get("toolchain", {})
    compiler_keys = {"version": "emscripten_version", "commit": "emscripten_commit",
                     "emsdk_commit": "emsdk_repo_commit", "release": "emsdk_release_commit"}
    if (not isinstance(compiler, dict) or not isinstance(toolchain, dict) or any(
            not toolchain.get(expected_key) or compiler.get(key) != toolchain[expected_key]
            for key, expected_key in compiler_keys.items())):
        raise Blocked("numeric fixes were declared for a different or unknown compiler")
    return expected


def select_artifact_contract(args, report):
    """Select the immutable release or an explicitly identified new source build.

    A build receipt supplies the expected digest for its new artifact. Checking
    that declaration does not independently reproduce the compilation or prove
    the published release was built from the same source.
    """
    receipt_path = getattr(args, "source_build_receipt", None)
    if receipt_path is None:
        return {"url": ASSET_URL, "sha256": ASSET_SHA256, "bytes": ASSET_BYTES,
                "label": "pinned release asset"}
    if args.asset is None:
        raise Blocked("source-build qualification requires an explicit --asset archive")
    if not receipt_path.is_file() or receipt_path.stat().st_size > 5_000_000:
        raise Blocked("source-build receipt is missing or exceeds its byte bound")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as error:
        raise Blocked("source-build receipt is not valid UTF-8 JSON") from error
    if not isinstance(receipt, dict) or type(receipt.get("schema")) is not int:
        raise Blocked("source-build receipt has no supported schema")
    expected = {
        "schema": 1, "artifact_kind": "blender-source-development", "status": "built",
        "upstream_commit": UPSTREAM_SHA, "port_commit": DEVELOPMENT_PORT_SHA,
        "canonical_patch_sha256": DEVELOPMENT_PATCH_SHA256, "build_mode": "OFF",
        "with_buildinfo": True,
    }
    for key, value in expected.items():
        if receipt.get(key) != value or type(receipt.get(key)) is not type(value):
            raise Blocked("source-build receipt differs from the required contract: " + key)
    numeric_patchset = validate_numeric_patchset(receipt)
    artifact = receipt.get("artifact")
    if not isinstance(artifact, dict):
        raise Blocked("source-build receipt has no artifact digest and byte count")
    value, size = artifact.get("sha256"), artifact.get("bytes")
    if (not isinstance(value, str) or len(value) != 64 or
            any(c not in "0123456789abcdef" for c in value) or
            type(size) is not int or not 0 < size <= 2_000_000_000):
        raise Blocked("source-build artifact identity is malformed or exceeds its byte bound")
    report["candidate"] = {"repository": "gessa-ai/blender-web",
                           "source_commit": DEVELOPMENT_PORT_SHA,
                           "kind": "blender-source-development",
                           "numeric_patchset_id": numeric_patchset["id"] if numeric_patchset else None}
    report["artifact"] = {"url": None, "expected_sha256": value, "expected_bytes": size}
    report["scope"] = "selected upstream Python suite qualification of a new development source build"
    report["source_correspondence_verified"] = False
    report["source_build_receipt_verified"] = True
    report["source_build"] = {
        **expected,
        "numeric_patchset": numeric_patchset,
        "numeric_fixes_declared": numeric_patchset is not None,
        "receipt_sha256": digest(receipt_path),
        "validation_scope": "Declared source pins and artifact digest only; no independent recompile or release correspondence claimed.",
    }
    return {"url": None, "sha256": value, "bytes": size,
            "label": "selected source-build receipt"}


def adapter_profile(adapter):
    """Classify observed fallback/software evidence without certifying hardware."""
    if not adapter:
        return "chromium-webgpu-unavailable"
    description = " ".join(str(adapter.get(key, "")) for key in
                           ("vendor", "architecture", "device", "description")).lower()
    if adapter.get("isFallbackAdapter") is True or any(
            name in description for name in ("swiftshader", "llvmpipe", "lavapipe", "software")):
        return "chromium-software-webgpu"
    return "chromium-webgpu-unverified"


def validate_build_identity(identity):
    """Unknown native reference identity cannot qualify an artifact as passing."""
    if identity.get("version") != [5, 2, 0]:
        raise Blocked("engine version differs from the pinned Blender 5.2.0 candidate")
    observed = str(identity.get("build_hash", "")).strip().lower()
    if observed in ("", "unknown", "none"):
        raise Blocked("engine build hash unavailable; executed suites do not establish reference provenance")
    if observed not in (UPSTREAM_SHA, UPSTREAM_SHA[:12]):
        raise Blocked("engine build hash differs from the candidate's pinned upstream reference: " + observed)


def decode_qualification_event(text, marker):
    """Retain one complete result prefix, with trailing runtime text kept separate."""
    if not text.startswith(marker):
        raise RuntimeError("qualification event has no matching marker")
    payload = text[len(marker):].lstrip()
    decoder = json.JSONDecoder()
    try:
        result, end = decoder.raw_decode(payload)
        json.dumps(result, allow_nan=False)
    except (ValueError, TypeError) as error:
        raise RuntimeError("qualification marker contains invalid or incomplete JSON") from error
    if not isinstance(result, dict):
        raise RuntimeError("qualification result is not an object")
    suffix = payload[end:]
    if marker in suffix:
        raise RuntimeError("duplicate qualification result marker in one event")
    if suffix.strip():
        try:
            decoder.raw_decode(suffix.lstrip())
        except ValueError:
            pass
        else:
            raise RuntimeError("extra JSON value after qualification result")
    else:
        suffix = ""
    return result, suffix


def validate_suite_execution(result, expected_sources):
    """Require complete top-level outcomes; subtests never inflate testsRun."""
    if result.get("exception"):
        raise RuntimeError("Python runner raised: " + result["exception"])
    rows = result.get("suites", [])
    if not expected_sources or len(rows) != len(expected_sources):
        raise RuntimeError("not every requested suite executed")
    for row, expected in zip(rows, expected_sources):
        if row["upstream_path"] != expected["upstream_path"] or row["sha256"] != expected["sha256"]:
            raise RuntimeError("suite identity changed during browser execution")
        ids = row["discovered_ids"]
        if (row["testsRun"] <= 0 or row["testsRun"] != row["discovered"] or
                row["discovered"] != len(ids) or len(set(ids)) != len(ids)):
            raise RuntimeError("suite ran zero tests or omitted/duplicated discovered tests")
        if "expected_cases" in expected and len(ids) != expected["expected_cases"]:
            raise RuntimeError("suite case count differs from the fixed native denominator: " + row["upstream_path"])
        if "case_ids" in expected and {canonical_case_id(value, expected) for value in ids} != set(expected["case_ids"]):
            raise RuntimeError("suite cases differ from the fixed native case IDs: " + row["upstream_path"])
        if any(row[key] for key in ("failures", "errors", "skipped", "expected_failures", "unexpected_successes")):
            raise RuntimeError("upstream suite is not completely passing: " + row["upstream_path"])
        top_level = [outcome for outcome in row["outcomes"] if outcome.get("kind") == "test"]
        if (len(top_level) != len(ids) or {outcome["id"] for outcome in top_level} != set(ids) or
                any(outcome["status"] != "passed" for outcome in row["outcomes"])):
            raise RuntimeError("complete passing outcomes were not recorded for every discovered test")


def summarize_execution(result, expected_sources, browser_errors=()):
    """Collect every suite failure and provenance blocker without double counts.

    A failing subtest and a later failure in its enclosing test are separate
    failure events but exactly one failed discovered test. A successful parent
    outcome is required to count a test as passed.
    """
    keys = ("discovered", "executed", "passed", "failed", "skipped",
            "expected_failures", "missing_outcomes", "failure_events", "subtest_events")
    totals = {key: 0 for key in keys}
    blockers, summaries = [], []
    rows = result.get("suites", [])
    expected_by_path = {entry["upstream_path"]: entry for entry in expected_sources}
    observed_paths = [row.get("upstream_path") for row in rows]
    if (not expected_sources or len(rows) != len(expected_sources) or
            len(set(observed_paths)) != len(observed_paths) or
            set(observed_paths) != set(expected_by_path)):
        blockers.append({"scope": "suite_inventory", "status": "failed",
                         "reason": "not every requested suite executed exactly once"})
    if result.get("exception"):
        blockers.append({"scope": "runner", "status": "failed", "reason": result["exception"]})
    if (any(source.get("required_background") is True for source in expected_sources) and
            result.get("execution_context", {}).get("background") is not True):
        blockers.append({"scope": "execution_context", "status": "failed",
                         "reason": "original CTest driver requires observed bpy.app.background=True"})
    if any(source.get("driver") == "unittest-main" for source in expected_sources):
        observation = result.get("driver_observation", {})
        if (observation.get("entrypoint") != "original __main__" or observation.get("runner_invocations") != 1 or
                observation.get("failfast") is not False or observation.get("original_exit_code") not in (None, 0)):
            blockers.append({"scope": "original_driver", "status": "failed",
                             "reason": "one complete original unittest entrypoint and its successful exit were not observed"})
    expected_fixtures = [value for source in expected_sources for value in source.get("fixture_files", [])]
    if expected_fixtures:
        observation = result.get("io_observation")
        observation = observation if isinstance(observation, dict) else {}
        observed_fixtures = observation.get("fixture_files")
        fields = ("relative_path", "upstream_path", "bytes", "sha256")
        inventory_matches = (isinstance(observed_fixtures, list) and
            all(isinstance(value, dict) and type(value.get("bytes")) is int for value in observed_fixtures) and
            [{key: value.get(key) for key in fields} for value in observed_fixtures] ==
            [{key: value[key] for key in fields} for value in expected_fixtures])
        if observation.get("fixture_bytes_preserved") is not True or not inventory_matches:
            blockers.append({"scope": "fixture_inputs", "status": "failed",
                             "reason": "complete unchanged fixture bytes and pinned identities were not observed"})
    for row in rows:
        path = row.get("upstream_path")
        counts = {key: 0 for key in keys}
        ids = list(dict.fromkeys(row.get("discovered_ids", [])))
        outcomes = row.get("outcomes", [])
        counts["discovered"], counts["executed"] = len(ids), row.get("testsRun", 0)
        counts["subtest_events"] = sum(item.get("kind") == "subtest" for item in outcomes)
        failure_events = [item for item in outcomes if item.get("status") in {"failed", "error", "unexpected_success"}]
        counts["failure_events"] = len(failure_events)
        for case_id in ids:
            related = [item for item in outcomes if item.get("id") == case_id or
                       (item.get("kind") == "subtest" and item.get("parent_id") == case_id)]
            statuses = {item.get("status") for item in related}
            if statuses & {"failed", "error", "unexpected_success"}:
                counts["failed"] += 1
            elif "skipped" in statuses:
                counts["skipped"] += 1
            elif "expected_failure" in statuses:
                counts["expected_failures"] += 1
            elif statuses == {"passed"} and any(item.get("kind") == "test" and
                                               item.get("id") == case_id for item in related):
                counts["passed"] += 1
            else:
                counts["missing_outcomes"] += 1
        suite_status = "passed"
        try:
            validate_suite_execution({"suites": [row], "exception": None},
                                     [expected_by_path[path]] if path in expected_by_path else [])
        except (RuntimeError, KeyError, TypeError, ValueError) as error:
            suite_status = "failed"
            blockers.append({"scope": "suite", "suite": path, "status": "failed", "reason": str(error)})
        summaries.append({"upstream_path": path, "status": suite_status, "counts": counts,
                          "failure_events": [{key: item.get(key) for key in ("id", "parent_id", "kind", "status")}
                                             for item in failure_events]})
        for key in keys:
            totals[key] += counts[key]
    suites_passed = not blockers
    identity = result.get("identity", {})
    hash_verified = str(identity.get("build_hash", "")).strip().lower() in (UPSTREAM_SHA, UPSTREAM_SHA[:12])
    try:
        validate_build_identity(identity)
    except Blocked as error:
        blockers.append({"scope": "provenance", "status": "blocked", "reason": str(error)})
    for error in browser_errors:
        blockers.append({"scope": "browser_runtime", "status": "failed", "reason": str(error)})
    inventory_rows = []
    observed_by_path = {row.get("upstream_path"): row for row in rows}
    for expected in expected_sources:
        if "expected_cases" not in expected:
            continue
        observed = observed_by_path.get(expected["upstream_path"], {})
        ids = observed.get("discovered_ids", [])
        canonical_ids = {canonical_case_id(value, expected) for value in ids if isinstance(value, str) and "." in value}
        missing_ids = sorted(set(expected.get("case_ids", [])) - canonical_ids)
        extra_ids = sorted(canonical_ids - set(expected["case_ids"])) if "case_ids" in expected else []
        missing = len(missing_ids) if "case_ids" in expected else max(expected["expected_cases"] - len(ids), 0)
        inventory_rows.append({"upstream_path": expected["upstream_path"],
                               "expected_cases": expected["expected_cases"], "missing_cases": missing,
                               "missing_case_ids": missing_ids, "unexpected_case_ids": extra_ids})
    inventory = {"fixed_for_all_requested_suites": len(inventory_rows) == len(expected_sources),
                 "expected_cases": sum(row["expected_cases"] for row in inventory_rows),
                 "missing_cases": sum(row["missing_cases"] for row in inventory_rows),
                 "suites": inventory_rows}
    status = ("failed" if any(b["status"] == "failed" for b in blockers) else
              "blocked" if blockers else "passed")
    return {"status": status, "selected_suites_passed": suites_passed,
            "upstream_build_hash_verified": hash_verified,
            "summary": {"expected_suites": len(expected_sources), "observed_suites": len(rows),
                        "totals": totals, "suites": summaries, "required_case_inventory": inventory}, "blockers": blockers}


def download(url, destination, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "Blended-port-qualification/1"})
    size = 0
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as output:
        while data := response.read(1024 * 1024):
            size += len(data)
            if size > limit:
                raise Blocked("download exceeds declared byte bound: " + url)
            output.write(data)


def extract_asset(archive, directory):
    """Extract only confined regular files/directories from the verified archive."""
    with tarfile.open(archive, "r:gz") as package:
        members = package.getmembers()
        total = 0
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or "\\" in member.name:
                raise Blocked("unsafe archive path: " + member.name)
            if not (member.isdir() or member.isfile()):
                raise Blocked("unsupported archive link/special file: " + member.name)
            total += member.size
            if total > 2_000_000_000:
                raise Blocked("unpacked archive exceeds 2 GB qualification limit")
        package.extractall(directory, members=members, filter="data")


def python_payload(suites, marker, output_root=None, wait_for_output_transfer=False):
    """Transport and execute whole source files without changing assertions."""
    if any(row.get("driver") == "unittest-main" for row, _ in suites):
        if len(suites) != 1:
            raise Blocked("original unittest scripts require separate processes")
        try:
            from .unittest_cohort import python_payload as original_unittest_payload
        except ImportError:
            from unittest_cohort import python_payload as original_unittest_payload
        return original_unittest_payload(suites, marker)
    if any(row.get("driver") == "original-script" for row, _ in suites):
        if len(suites) != 1 or output_root is None:
            raise Blocked("the original blend-file script requires an isolated output directory and complete cohort")
        try:
            from .blender_io_cohort import python_payload as original_script_payload
        except ImportError:
            from blender_io_cohort import python_payload as original_script_payload
        return original_script_payload(suites, marker, str(output_root), wait_for_output_transfer)
    encoded = [{**row, "source_b64": base64.b64encode(data).decode("ascii")}
               for row, data in suites]
    # The adapter loads the upstream module and uses its unittest loader. Only
    # the entry point is adapted; every discovered test and subtest is retained.
    return r'''
import base64, hashlib, json, sys, traceback, types, unittest
_blended_suites = json.loads(PAYLOAD_JSON)
_blended_marker = MARKER_JSON
_blended_report = {"suites": [], "identity": {}, "exception": None}
try:
    import bpy
    def _blended_text(value):
        return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
    _blended_report["identity"] = {
        "version": list(bpy.app.version),
        "version_string": bpy.app.version_string,
        "build_hash": _blended_text(bpy.app.build_hash),
        "build_branch": _blended_text(bpy.app.build_branch),
        "binary_path": bpy.app.binary_path,
    }
    _blended_report["execution_context"] = {"background": getattr(bpy.app, "background", None)}
    def _blended_case_id(test):
        # Upstream ID-property helpers use an `id` property for a Blender ID.
        # Call unittest's base implementation without evaluating that property.
        if isinstance(test, unittest.TestCase):
            return unittest.TestCase.id(test)
        return test.id()  # unittest's non-TestCase setup/module error holders.
    class _BlendedResult(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.case_outcomes = []
        def _record(self, test, status, detail=None, kind="test", parent_id=None):
            case_id = parent_id + " " + test._subDescription() if kind == "subtest" else _blended_case_id(test)
            self.case_outcomes.append({"id": case_id, "kind": kind, "parent_id": parent_id,
                                       "status": status, "detail": detail})
        def addSuccess(self, test):
            super().addSuccess(test); self._record(test, "passed")
        def addFailure(self, test, err):
            super().addFailure(test, err); self._record(test, "failed", self._exc_info_to_string(err, test))
        def addError(self, test, err):
            super().addError(test, err); self._record(test, "error", self._exc_info_to_string(err, test))
        def addSkip(self, test, reason):
            super().addSkip(test, reason); self._record(test, "skipped", reason)
        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err); self._record(test, "expected_failure", self._exc_info_to_string(err, test))
        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test); self._record(test, "unexpected_success")
        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            self._record(subtest, "passed" if err is None else "failed",
                         None if err is None else self._exc_info_to_string(err, test),
                         kind="subtest", parent_id=_blended_case_id(test))
    def _blended_ids(suite):
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                yield from _blended_ids(test)
            else:
                yield _blended_case_id(test)
    for _blended_index, _blended_row in enumerate(_blended_suites):
        _blended_data = base64.b64decode(_blended_row["source_b64"])
        if hashlib.sha256(_blended_data).hexdigest() != _blended_row["sha256"]:
            raise RuntimeError("suite changed in transport")
        _blended_name = "blended_upstream_" + str(_blended_index)
        _blended_module = types.ModuleType(_blended_name)
        _blended_module.__file__ = "/" + _blended_row["upstream_path"]
        sys.modules[_blended_name] = _blended_module
        sys.argv = [_blended_module.__file__]
        exec(compile(_blended_data, _blended_module.__file__, "exec"), _blended_module.__dict__)
        _blended_suite = unittest.defaultTestLoader.loadTestsFromModule(_blended_module)
        _blended_expected = list(_blended_ids(_blended_suite))
        _blended_result = unittest.TextTestRunner(verbosity=2, resultclass=_BlendedResult).run(_blended_suite)
        _blended_report["suites"].append({
            "upstream_path": _blended_row["upstream_path"], "sha256": _blended_row["sha256"],
            "discovered_ids": _blended_expected, "discovered": len(_blended_expected),
            "testsRun": _blended_result.testsRun,
            "failures": len(_blended_result.failures), "errors": len(_blended_result.errors),
            "skipped": len(_blended_result.skipped),
            "expected_failures": len(_blended_result.expectedFailures),
            "unexpected_successes": len(_blended_result.unexpectedSuccesses),
            "outcomes": _blended_result.case_outcomes,
        })
except BaseException:
    _blended_report["exception"] = traceback.format_exc()
finally:
    print(_blended_marker + json.dumps(_blended_report, sort_keys=True), flush=True)
'''.replace("PAYLOAD_JSON", repr(json.dumps(encoded))).replace("MARKER_JSON", repr(marker))


def serve(shell, binary, entry, output):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          ".wasm": "application/wasm", ".js": "text/javascript",
                          ".data": "application/octet-stream"}

        def translate_path(self, path):
            rel = urllib.parse.unquote(urllib.parse.urlsplit(path).path)
            root = binary if rel.startswith("/bin/") else shell
            rel = rel[5:] if rel.startswith("/bin/") else rel.lstrip("/")
            if not rel:
                rel = entry
            resolved = (root / rel).resolve()
            if not resolved.is_relative_to(root.resolve()):
                return str(shell / "__blocked_path__")
            return str(resolved)

        def end_headers(self):
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, fmt, *args):
            with (output / "http.log").open("a", encoding="utf-8") as log:
                log.write((fmt % args) + "\n")

    class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    server = Server(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def probe(args, report):
    output = args.output.resolve()
    artifact_contract = select_artifact_contract(args, report)
    with tempfile.TemporaryDirectory(prefix="blended-port-probe-") as temporary:
        work = Path(temporary)
        archive = args.asset.resolve() if args.asset else work / "candidate.tar.gz"
        if args.asset is None:
            download(artifact_contract["url"], archive, artifact_contract["bytes"])
        if not archive.is_file():
            raise Blocked("candidate archive is missing")
        measured_digest = digest(archive)
        report["artifact"]["observed_sha256"] = measured_digest
        report["artifact"]["observed_bytes"] = archive.stat().st_size
        if measured_digest != artifact_contract["sha256"] or archive.stat().st_size != artifact_contract["bytes"]:
            raise Blocked("candidate artifact does not match the " + artifact_contract["label"])

        catalog = load_suite_catalog(getattr(args, "cohort", "numeric"),
                                     getattr(args, "suite_manifest", None), getattr(args, "suite_manifest_sha256", None))
        report["cohort"] = {key: value for key, value in catalog.items() if key != "suites"}
        suites = prepare_suites(args.suite, work, catalog, fixture_root=getattr(args, "fixture_root", None))
        report["cohort"]["complete_cohort_requested"] = len(suites) == len(catalog["suites"])
        report["suite_sources"] = [suite_metadata(row) for row, _ in suites]
        report["input_fixture_transfer"] = preserve_suite_fixtures(suites, output / "fixtures")

        unpacked = work / "unpacked"
        unpacked.mkdir()
        extract_asset(archive, unpacked)
        boots = list(unpacked.rglob("boot-windowed.js"))
        engines = list(unpacked.rglob("blender_browser.js"))
        if len(boots) != 1 or len(engines) != 1:
            raise Blocked("release layout has no unambiguous windowed shell and Blender engine")
        shell, binary = boots[0].parent, engines[0].parent
        entry = "windowed.html" if (shell / "windowed.html").is_file() else "index.html"
        if not (shell / entry).is_file():
            raise Blocked("release contains no windowed entry page")
        report["engine_files"] = [{"path": str(p.relative_to(unpacked)), "sha256": digest(p),
                                    "bytes": p.stat().st_size}
                                   for p in sorted(binary.iterdir()) if p.is_file()]
        report["shell"] = {"entry": entry, "boot_sha256": digest(boots[0]), "modified": False}
        server = serve(shell, binary, entry, output)
        report["url"] = "http://127.0.0.1:" + str(server.server_port) + "/"
        marker = "BLENDED_QUALIFICATION_" + secrets.token_hex(12) + ":"
        io_root = "/tmp/blended-original-io-" + secrets.token_hex(12) if catalog.get("suite_kind") == "original-script" else None
        if io_root:
            report["io_execution_root"] = io_root
        received = []
        transport_suffixes = []
        browser_errors = []
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            server.shutdown()
            raise Blocked("Playwright is not installed") from error
        try:
            with sync_playwright() as playwright:
                flags = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu-watchdog",
                         "--enable-unsafe-webgpu", "--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
                executable = args.browser_executable or shutil.which("google-chrome")
                launch = {"headless": True, "args": flags}
                if executable:
                    launch["executable_path"] = executable
                try:
                    browser = playwright.chromium.launch(**launch)
                except Exception as error:
                    raise Blocked("Chromium could not start: " + str(error)) from error
                report["browser"] = {"version": browser.version, "flags": flags}
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()

                def console(message):
                    text = message.text
                    with (output / "browser.log").open("a", encoding="utf-8") as log:
                        log.write(message.type + " " + text + "\n")
                    if text.startswith(marker):
                        try:
                            result, suffix = decode_qualification_event(text, marker)
                            received.append(result)
                            transport_suffixes.append(suffix)
                            if suffix:
                                browser_errors.append("runtime text followed complete qualification JSON: " + suffix)
                        except RuntimeError as error:
                            browser_errors.append(str(error))

                page.on("console", console)
                page.on("pageerror", lambda error: browser_errors.append(str(error)))
                page.on("crash", lambda: browser_errors.append("browser page crashed"))
                code = python_payload(suites, marker, io_root, wait_for_output_transfer=bool(io_root))
                report["runner_sha256"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
                background = any(row.get("required_background") is True for row, _ in suites)
                extra_args = catalog.get("blender_args") or (["--background", "--factory-startup", "--threads", "1", "--python-exit-code", "1"] +
                              catalog.get("extra_blender_args", [])
                              if background else [])
                report["execution_mode"] = {"requested": "background" if background else "windowed",
                    "extra_argv": extra_args, "hook": "unchanged shell __BW_ARGS before __BW_PYEXPR"}
                if extra_args:
                    page.add_init_script("window.__BW_ARGS = " + json.dumps(extra_args) + ";")
                page.add_init_script("window.__BW_PYEXPR = " + json.dumps(code) + ";")
                response = page.goto(report["url"], wait_until="domcontentloaded", timeout=60000)
                if response is None or response.status != 200:
                    raise Blocked("local candidate page did not return HTTP 200")
                capability = page.evaluate("""async () => {
                    const adapter = navigator.gpu ? await navigator.gpu.requestAdapter() : null;
                    return {crossOriginIsolated, sharedArrayBuffer: typeof SharedArrayBuffer !== 'undefined',
                        webgpu: !!navigator.gpu, adapter: adapter ? {
                            vendor: adapter.info?.vendor ?? null,
                            architecture: adapter.info?.architecture ?? null,
                            device: adapter.info?.device ?? null,
                            description: adapter.info?.description ?? null,
                            isFallbackAdapter: adapter.info?.isFallbackAdapter ?? adapter.isFallbackAdapter ?? null,
                            features: Array.from(adapter.features)
                        } : null};
                }""")
                report["capabilities"] = capability
                report["profile"] = adapter_profile(capability["adapter"])
                report["adapter_measurement_scope"] = (
                    "Independent navigator.gpu.requestAdapter probe; engine-selected adapter is not instrumented.")
                if not capability["crossOriginIsolated"] or not capability["sharedArrayBuffer"]:
                    raise Blocked("cross-origin isolation or SharedArrayBuffer unavailable")
                if not capability["adapter"]:
                    raise Blocked("WebGPU adapter unavailable")
                deadline = time.monotonic() + args.timeout
                while not received and time.monotonic() < deadline:
                    if browser_errors:
                        raise RuntimeError("browser runtime error: " + browser_errors[0])
                    if page.evaluate("window.__bwDevHooksAllowed === false"):
                        raise Blocked("artifact disables the Python test hook; unchanged release was preserved")
                    page.wait_for_timeout(250)
                report["browser_errors"] = browser_errors
                try:
                    page.screenshot(path=str(output / "candidate.png"))
                except Exception as error:
                    report["screenshot_error"] = str(error)
                if not received:
                    raise Blocked("timed out waiting for executed upstream tests; no pass inferred from boot")
                if len(received) != 1:
                    raise RuntimeError("duplicate qualification result markers")
                report["transport"] = {"protocol": "marker-prefixed-json-v1", "result_markers": len(received),
                    "recovered_json_prefix": bool(transport_suffixes[0]),
                    "trailing_runtime_text": transport_suffixes[0] or None}
                result = received[0]
                report["execution"] = result
                transfer_error = None
                if io_root:
                    try:
                        try:
                            from .probe_io_files import browser_reader, retrieve_files
                        except ImportError:
                            from probe_io_files import browser_reader, retrieve_files
                        page.wait_for_function("() => typeof window.__bwModule?.FS?.open === 'function'", timeout=30000)
                        report["generated_file_transfer"] = retrieve_files(
                            result.get("generated_files"), io_root + "/files", output / "blendfiles",
                            browser_reader(page), "browser-wasm-filesystem")
                    except Exception as error:
                        transfer_error = str(error)
                        report["generated_file_transfer"] = {"status": "failed", "reason": transfer_error}
                    try:
                        try:
                            from .probe_io_files import acknowledge_browser_transfer
                        except ImportError:
                            from probe_io_files import acknowledge_browser_transfer
                        report["output_transfer_acknowledgement"] = acknowledge_browser_transfer(
                            page, result.get("output_transfer_handshake"), io_root,
                            hashlib.sha256(marker.encode("utf-8")).hexdigest(),
                            report.get("generated_file_transfer"))
                    except Exception as error:
                        report["output_transfer_acknowledgement"] = {"status": "failed", "reason": str(error)}
                        browser_errors.append("output transfer acknowledgement failed: " + str(error))
                if background:
                    try:
                        # The unmodified shell's onExit writes the real Emscripten
                        # exit code. A Python result alone does not prove shutdown.
                        page.wait_for_function("() => /^-?\\d+$/.test(document.getElementById('exit')?.textContent?.trim() ?? '')",
                                               timeout=30000)
                        exit_code = int(page.locator("#exit").text_content().strip())
                        report["execution_mode"]["runtime_exit_code"] = exit_code
                        if exit_code != 0:
                            browser_errors.append("browser background runtime exited with code " + str(exit_code))
                    except Exception as error:
                        report["execution_mode"]["runtime_exit_code"] = None
                        browser_errors.append("browser background runtime exit was not verified: " + str(error))
                if len(received) != 1:
                    browser_errors.append("duplicate qualification result markers after output retrieval")
                    report["transport"]["result_markers"] = len(received)
                report.update(summarize_execution(result, report["suite_sources"], browser_errors))
                if transfer_error:
                    report["status"] = "failed"
                    report["blockers"].append({"scope": "file_transport", "status": "failed", "reason": transfer_error})
                report["identity_limit"] = next((b["reason"] for b in report["blockers"]
                                                 if b["scope"] == "provenance"), None)
                report["reason"] = (
                    "Whole selected unchanged upstream test files passed on the pinned artifact in a local browser; "
                    "reported upstream build identity matched. Observed probe profile: " + report["profile"] + "."
                    if report["status"] == "passed" else
                    "; ".join(b["scope"] + ": " + b["reason"] for b in report["blockers"]))
                browser.close()
        finally:
            report["browser_errors"] = browser_errors
            server.shutdown()
            server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path,
                        help="Local pinned release archive, or new archive identified by --source-build-receipt")
    parser.add_argument("--source-build-receipt", type=Path,
                        help="Exact development build receipt; requires --asset and preserves all runtime/test gates")
    parser.add_argument("--suite", action="append", type=Path,
                        help="Exact pinned source file from the selected cohort; repeatable")
    parser.add_argument("--fixture-root", type=Path,
                        help="Local exact cohort fixtures under their original tests/files relative paths")
    parser.add_argument("--cohort", choices=("numeric", "data52", "blendio52", "liblink52"), default="numeric",
                        help="Selected fixed native suite inventory; default keeps the original 192 numerical tests")
    parser.add_argument("--suite-manifest", type=Path, help="Hash-bound external frozen original unittest invocation")
    parser.add_argument("--suite-manifest-sha256", help="Expected SHA-256 of --suite-manifest; native discovery is mandatory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser-executable")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": 1, "status": "blocked", "started_utc": now(), "finished_utc": None,
        "scope": "selected upstream Python suite qualification only",
        "profile": "chromium-webgpu-unclassified", "deployed": False,
        "hardware_verified": False, "native_oracle_compared": False, "full_parity": False,
        "selected_suites_passed": False,
        "summary": None, "blockers": [],
        "source_correspondence_verified": False,
        "candidate": {"repository": "gessa-ai/blender-web", "tag": "v0.1.1", "source_commit": PORT_SOURCE_SHA},
        "upstream": {"repository": "blender/blender", "commit": UPSTREAM_SHA},
        "artifact": {"url": ASSET_URL, "expected_sha256": ASSET_SHA256, "expected_bytes": ASSET_BYTES},
        "suite_sources": [], "browser_errors": [], "execution": None,
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
        (args.output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "reason": report.get("reason"),
                          "evidence": str(args.output / "qualification.json")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
