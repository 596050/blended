#!/usr/bin/env python3
"""Convert immutable original-unittest observations into a paired test ledger.

This program consumes evidence; it does not execute Blender or certify a full
upstream test denominator. It preserves the source plan, fixes the case inventory
from native discovery, and binds every normalized receipt to its original bytes.
Reported producer observations remain a trust boundary, not an independent
re-execution. Artifact context measurements are required, never fabricated.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

try:
    from .test_parity_ledger import assess, canonical_sha256, digest, load_json, require, strings
    from .unittest_cohort import (CMAKE_SOURCES, NATIVE_ARCHIVE_BYTES, NATIVE_ARCHIVE_SHA256,
                                  UPSTREAM_SHA, case_id, validate_manifest, validate_native_discovery)
    from .upstream_invocations import load_catalog, validate_declaration
    from .browser_package_overlay import PLAN_PATH as OVERLAY_PLAN_PATH, load_plan as load_overlay_plan
except ImportError:
    from test_parity_ledger import assess, canonical_sha256, digest, load_json, require, strings
    from unittest_cohort import (CMAKE_SOURCES, NATIVE_ARCHIVE_BYTES, NATIVE_ARCHIVE_SHA256,
                                 UPSTREAM_SHA, case_id, validate_manifest, validate_native_discovery)
    from upstream_invocations import load_catalog, validate_declaration
    from browser_package_overlay import PLAN_PATH as OVERLAY_PLAN_PATH, load_plan as load_overlay_plan

ROOT = Path(__file__).resolve().parents[1]
TARGET = {"repository": "blender/blender", "commit": UPSTREAM_SHA}
CONFIGURATION = "blender-5.2-original-main-artifact-pair"
NATIVE = "native-reference"
BROWSER = "chromium-software-webgpu"
SOURCE_FIELDS = ("upstream_path", "sha256", "bytes")
EVENT_OUTCOMES = {"passed", "failed", "error", "skipped", "expected_failure", "unexpected_success"}
POLICY = {
    "schema": 1, "name": "unchanged-upstream-unittest-outcomes-v1",
    "acceptance": "Original source assertions, thresholds and complete script arguments are unchanged.",
    "case_identity": "upstream_path::unittest_id; remove only the __main__. module prefix",
    "subtest_identity": "Preserve the complete original parent ID and unittest sub-description.",
    "failure_detail": "Replace only the observed temporary source_root prefix with {source_root}; preserve all other text.",
    "expected_failure": "May establish outcome agreement; never a successful functional test.",
    "completion": "An original test callback is distinct from an independently observed whole-process exit.",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


@dataclass
class Captured:
    path: Path
    data: bytes
    ref: dict

    def json(self) -> dict:
        value = load_json(self.data)
        require(isinstance(value, dict), "evidence JSON must be an object: " + self.path.name)
        return value


class Evidence:
    """Read confined, hash-bound input bytes once and retain reproducible copies."""

    def __init__(self, root: Path, output: Path):
        require(not root.is_symlink() and root.is_dir(), "repository root must be a real directory")
        self.root, self.output = root.resolve(), output.absolute()
        require(not self.output.exists(), "choose a new output directory; previous evidence is immutable")
        require(not any(parent.is_symlink() for parent in [self.output, *self.output.parents]),
                "output path contains a symlink")
        self.output.mkdir(parents=True)
        self.origins: dict[str, dict] = {}

    def resolve(self, name: str | Path, base: Path | None = None) -> Path:
        name = str(name)
        require(name and "\\" not in name, "invalid evidence path")
        path = Path(name)
        if path.is_absolute() and not path.is_relative_to(self.root):
            # Archived receipts name their historical checkout. Only versioned
            # compatibility paths may be relocated; external runtime binaries
            # are described by context measurements and are never followed.
            parts = PurePosixPath(name).parts
            require(parts.count("compatibility") == 1, "external evidence path is not relocatable: " + name)
            path = self.root.joinpath(*parts[parts.index("compatibility"):])
        elif not path.is_absolute():
            path = (base or self.root) / path
        # Check lexical components before resolving '..', including symlinks
        # that could otherwise leave and re-enter the repository.
        require(path.is_relative_to(self.root), "evidence path escapes repository")
        current = self.root
        for part in path.relative_to(self.root).parts:
            current /= part
            require(not current.is_symlink(), "symlink evidence is forbidden")
        resolved = path.resolve(strict=True)
        require(resolved.is_relative_to(self.root) and resolved.is_file(), "evidence must be a confined regular file")
        return resolved

    def write(self, name: str, data: bytes) -> dict:
        require(not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts,
                "unsafe output path")
        path = self.output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            require(path.read_bytes() == data, "refusing to replace different evidence: " + name)
        else:
            with path.open("xb") as stream:
                stream.write(data)
        return {"path": name, "sha256": sha(data), "bytes": len(data)}

    def json(self, name: str, value: Any) -> dict:
        return self.write(name, encoded(value))

    def capture(self, path: str | Path, pin: dict | None = None, base: Path | None = None) -> Captured:
        resolved = self.resolve(path, base)
        data = resolved.read_bytes()
        if pin is not None:
            require(sha(data) == digest(pin.get("sha256"), "input sha256"),
                    "input hash mismatch: " + resolved.name)
            require("bytes" not in pin or type(pin["bytes"]) is int and pin["bytes"] == len(data),
                    "input byte count mismatch: " + resolved.name)
        suffix = resolved.suffix if resolved.suffix in {".json", ".log", ".txt", ".py", ".png", ".ttf", ".otf"} else ".bin"
        ref = self.write("raw/" + sha(data) + suffix, data)
        origin = resolved.relative_to(self.root).as_posix()
        self.origins[origin] = ref
        return Captured(resolved, data, ref)

    def reference(self, pin: dict, base: Path | None = None) -> Captured:
        require(isinstance(pin, dict) and isinstance(pin.get("path"), str), "bound input reference is missing")
        return self.capture(pin["path"], pin, base)


def unique_refs(refs: list[dict]) -> list[dict]:
    return sorted({row["path"]: row for row in refs}.values(), key=lambda row: row["path"])


def identity(value: dict, label: str) -> tuple[str, int]:
    require(isinstance(value, dict), label + " identity is missing")
    require(type(value.get("bytes")) is int and value["bytes"] > 0, label + " byte count is invalid")
    return digest(value.get("sha256"), label + " sha256"), value["bytes"]


def check_target(value: dict, label: str) -> None:
    require(isinstance(value, dict) and value.get("repository") == TARGET["repository"]
            and value.get("commit") == TARGET["commit"], label + " targets another Blender revision")


def timestamp(value: Any, label: str) -> datetime:
    require(isinstance(value, str) and bool(value), label + " timestamp is missing")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, label + " timestamp must identify its time zone")
    return result


def check_execution_log(captured: Captured, raw: dict, native: bool) -> None:
    prefix = "BLENDED_NATIVE_REFERENCE_" if native else "BLENDED_QUALIFICATION_"
    expression = re.compile(r"^(?:log )?" + prefix + r"[0-9a-f]+:")
    observations = []
    for line in captured.data.decode("utf-8", errors="replace").splitlines():
        match = expression.match(line)
        if match:
            observations.append(load_json(line[match.end():]))
    require(len(observations) == 1 and observations[0] == raw.get("execution"),
            "raw execution differs from the single original log observation")


def engine_files(entries: Any) -> dict:
    require(isinstance(entries, list) and bool(entries), "engine file identity list is missing")
    pairs = []
    for row in entries:
        require(isinstance(row, dict) and isinstance(row.get("path"), str) and row["path"],
                "engine file path is missing")
        pairs.append((PurePosixPath(row["path"]).name, identity(row, "engine file")))
    require(len({name for name, _ in pairs}) == len(pairs), "ambiguous engine file identity")
    require({name for name, _ in pairs} == {"blender_browser." + suffix for suffix in ("data", "js", "wasm")},
            "engine identity must retain data, JavaScript and Wasm")
    return dict(pairs)


def package_context(evidence: Evidence, context_file: Captured, browser: dict,
                    source: Captured, cache: Captured) -> tuple[dict | None, dict, list]:
    """Bind a separately measured resource package without relabeling its build.

    Archive paths are historical runtime identities, not replay dependencies.
    The independent measurement and the original verifier bytes are preserved;
    this consumer does not claim to re-read or re-verify the external archives.
    """
    markers = {"package_overlay_receipt", "package_base_asset", "package_overlay_measurement"}
    present = markers & browser.keys()
    build = source.json()
    base_engine = identity(build.get("artifact"), "source build artifact")
    selected_engine = identity(browser.get("engine_archive"), "browser engine archive")
    original_members = engine_files(build.get("engine_files"))
    if not present:
        require(base_engine == selected_engine,
                "browser context, source build and observed CMake cache do not agree")
        return None, original_members, []
    require(present == markers, "package overlay context requires receipt, base asset and independent measurement")
    receipt_file = evidence.reference(browser["package_overlay_receipt"], context_file.path.parent)
    measured_file = evidence.reference(browser["package_overlay_measurement"], context_file.path.parent)
    receipt, measured = receipt_file.json(), measured_file.json()
    plan, plan_pin = load_overlay_plan()
    require(type(receipt.get("schema")) is int and receipt["schema"] == 1
            and receipt.get("kind") == "blender-browser-package-overlay" and receipt.get("status") == "assembled"
            and receipt.get("upstream_commit") == UPSTREAM_SHA and receipt.get("overlay_id") == plan["id"]
            and identity(receipt.get("manifest"), "overlay plan") == identity(plan_pin, "reviewed overlay plan")
            and receipt.get("additions") == plan["files"]
            and receipt.get("engine_recompiled") is False and receipt.get("full_parity") is False
            and type(receipt.get("tests_executed")) is int and receipt["tests_executed"] == 0,
            "package overlay receipt differs from the independently reviewed resource plan")
    require(identity(receipt.get("source_build_receipt"), "overlay base source receipt") == identity(source.ref, "source receipt")
            and identity(receipt.get("base_artifact"), "overlay base archive") == base_engine
            and identity(browser["package_base_asset"], "context base archive") == base_engine
            and identity(receipt.get("artifact"), "overlay artifact") == selected_engine
            and selected_engine != base_engine,
            "package overlay must preserve its base source identity and select a distinct artifact")
    require(type(measured.get("schema")) is int and measured["schema"] == 1
            and measured.get("kind") == "verified-browser-package-measurement"
            and type(measured.get("tests_executed")) is int and measured["tests_executed"] == 0,
            "independent package measurement is missing or claims test execution")
    require(timestamp(measured.get("started_utc"), "package measurement start")
            <= timestamp(measured.get("finished_utc"), "package measurement finish"),
            "package measurement did not complete in order")
    require(identity(measured.get("artifact"), "measured overlay archive") == selected_engine
            and identity(measured.get("base_artifact"), "measured base archive") == base_engine,
            "independent package measurement identifies another archive")
    raw = [receipt_file.ref, measured_file.ref]
    for field, expected in (("source_build_receipt", source), ("package_overlay_receipt", receipt_file)):
        captured = evidence.reference(measured.get(field), measured_file.path.parent)
        require(identity(captured.ref, "measured " + field) == identity(expected.ref, field),
                "independent package measurement substituted its " + field)
        raw.append(captured.ref)
    original_context_file = evidence.reference(measured.get("base_context"), measured_file.path.parent)
    original_context = original_context_file.json()
    check_target(original_context.get("upstream"), "package base context")
    require(original_context.get("schema") == 1 and original_context.get("kind") == "artifact-bound-browser-context"
            and not (markers & original_context.keys())
            and identity(original_context.get("engine_archive"), "original context engine") == base_engine
            and identity(original_context.get("browser"), "original browser") == identity(browser.get("browser"), "selected browser")
            and original_context["browser"].get("version") == browser["browser"].get("version")
            and original_context.get("requested_flags") == browser.get("requested_flags"),
            "package overlay changed its independently bound base browser context")
    raw.append(original_context_file.ref)
    for field, expected in (("source_build_receipt", source), ("build_configuration", cache)):
        captured = evidence.reference(original_context.get(field), original_context_file.path.parent)
        require(identity(captured.ref, "base context " + field) == identity(expected.ref, field),
                "package base context differs from the selected original build")
        raw.append(captured.ref)
    measurement_tool = evidence.reference(measured.get("measurement_tool"), measured_file.path.parent)
    # The receipt records the original tools/ path. An adjacent exact snapshot
    # preserves those bytes after checkout relocation or later tool changes.
    identity(measured.get("verification_tool"), "package verification tool")
    verifier = evidence.capture(measured_file.path.parent / "browser_package_overlay.py", measured.get("verification_tool"))
    require(verifier.data == Path(__file__).with_name("browser_package_overlay.py").read_bytes(),
            "package measurement used an unreviewed verifier")
    raw.extend([measurement_tool.ref, verifier.ref])
    verified = measured.get("package_overlay")
    require(isinstance(verified, dict) and verified == {**receipt, "receipt_sha256": receipt_file.ref["sha256"]},
            "independent package verification differs from its bound overlay receipt")
    verification = verified.get("verification", {})
    require(isinstance(verification, dict) and all(verification.get(field) is True for field in
            ("base_archive_verified", "added_resource_bytes_verified", "existing_preload_bytes_unchanged", "wasm_unchanged"))
            and type(verification.get("unchanged_files")) is int and verification["unchanged_files"] >= 1
            and type(verification.get("added_files")) is int and verification["added_files"] == 1
            and verification.get("mount_timing") == "Emscripten preload before application main",
            "package measurement did not verify the unchanged engine and original resources")
    members = engine_files(measured.get("engine_files"))
    member_paths = [PurePosixPath(row["path"]) for row in measured["engine_files"]]
    require(all(not path.is_absolute() and ".." not in path.parts for path in member_paths)
            and len({path.parent for path in member_paths}) == 1,
            "measured package engine members have unsafe or inconsistent paths")
    require(verification.get("modified_files") == sorted(str(path) for path in member_paths if path.suffix in {".data", ".js"}),
            "package verification changed unexpected engine members")
    require(members["blender_browser.wasm"] == original_members["blender_browser.wasm"]
            and members["blender_browser.js"] != original_members["blender_browser.js"]
            and members["blender_browser.data"][0] != original_members["blender_browser.data"][0]
            and members["blender_browser.data"][1] == original_members["blender_browser.data"][1]
                + sum(row["bytes"] for row in plan["files"]),
            "measured package must retain Wasm and account for changed JavaScript and preload data")
    return {"receipt": receipt_file, "measurement": measured_file, "verified": verified,
            "base_asset": browser["package_base_asset"], "verifier": verifier,
            "plan_identity": plan_pin}, members, raw


def read_contexts(evidence: Evidence, native_path: Path, browser_path: Path, adapter_sha: str) -> dict:
    nc, bc = evidence.capture(native_path), evidence.capture(browser_path)
    native, browser = nc.json(), bc.json()
    check_target(native.get("upstream"), "native context")
    check_target(browser.get("upstream"), "browser context")
    require(native.get("schema") == 1 and native.get("kind") == "artifact-bound-native-context"
            and type(native.get("measurement_exit_code")) is int and native["measurement_exit_code"] == 0,
            "independent native context measurement did not complete")
    require(browser.get("schema") == 1 and browser.get("kind") == "artifact-bound-browser-context",
            "independent browser context is missing")
    require(identity(native.get("archive"), "native archive") == (NATIVE_ARCHIVE_SHA256, NATIVE_ARCHIVE_BYTES)
            and native["archive"].get("expected_sha256_verified") is True,
            "native context is not bound to the verified official archive")
    native_executable = identity(native.get("executable"), "native executable")
    native_raw = [evidence.reference(row, nc.path.parent) for row in native.get("raw_evidence", [])]
    measurements = [row for row in native_raw if row.path.name == "native-measurement.json"]
    require(len(measurements) == 1 and measurements[0].json() == native.get("build_configuration"),
            "native configuration is not independently bound to its raw measurement")
    measured = measurements[0].json()
    require(measured.get("identity", {}).get("build_hash") in {UPSTREAM_SHA, UPSTREAM_SHA[:12]}
            and measured.get("identity", {}).get("version") == [5, 2, 0]
            and isinstance(measured.get("build_options"), dict)
            and measured.get("runtime", {}).get("background") is True,
            "native measured configuration differs from the selected runtime")
    browser_executable = identity(browser.get("browser"), "browser executable")
    engine = identity(browser.get("engine_archive"), "browser engine archive")
    source = evidence.reference(browser.get("source_build_receipt"), bc.path.parent)
    cache = evidence.reference(browser.get("build_configuration"), bc.path.parent)
    build = source.json()
    require(build.get("schema") == 1 and build.get("artifact_kind") == "blender-source-development"
            and build.get("status") == "built" and build.get("upstream_commit") == UPSTREAM_SHA,
            "browser source build does not identify the selected artifact")
    require(identity(build.get("configuration"), "source build configuration") == identity(cache.ref, "CMake cache"),
            "browser context, source build and observed CMake cache do not agree")
    overlay, members, package_raw = package_context(evidence, bc, browser, source, cache)
    require(isinstance(browser.get("requested_flags"), list) and browser["requested_flags"],
            "browser flags are not independently recorded")
    contexts = {
        NATIVE: {"artifact_sha256": NATIVE_ARCHIVE_SHA256, "build_config_sha256": measurements[0].ref["sha256"],
                 "runtime_sha256": native_executable[0], "adapter_sha256": adapter_sha},
        BROWSER: {"artifact_sha256": engine[0], "build_config_sha256": cache.ref["sha256"],
                  "runtime_sha256": browser_executable[0], "adapter_sha256": adapter_sha},
    }
    return {"native": native, "browser": browser, "contexts": contexts, "build": build,
            "source": source, "overlay": overlay, "engine_files": members,
            "raw": unique_refs([nc.ref, bc.ref, source.ref, cache.ref, *package_raw, *[row.ref for row in native_raw]])}


def declaration_rows(plan: dict) -> dict[int, dict]:
    require(plan.get("schema") == 1 and plan.get("upstream_commit") == UPSTREAM_SHA,
            "source plan targets another upstream revision")
    require(plan.get("configured_ctest_inventory") is False and plan.get("complete_test_denominator") is False,
            "this converter accepts explicitly bounded source plans, not a claimed full CTest denominator")
    require(isinstance(plan.get("registrations"), list) and plan["registrations"], "source declarations are missing")
    rows, names = {}, set()
    for row in plan["registrations"]:
        index = row.get("source_declaration_index")
        require(type(index) is int and index >= 0 and index not in rows, "duplicate or invalid source declaration index")
        require(row.get("state") in {"blocked", "native_inventory_frozen", "native_discovery_blocked"},
                "unknown source declaration state")
        require(isinstance(row.get("registration"), str) and row["registration"] and isinstance(row.get("context"), list),
                "source declaration text or CMake context is missing")
        validate_declaration(row)
        if row.get("ctest_name") is not None:
            require(re.fullmatch(r"[A-Za-z0-9_]+", row["ctest_name"]) and row["ctest_name"] not in names,
                    "duplicate or invalid original CTest name")
            names.add(row["ctest_name"])
        rows[index] = row
    return rows


def source_identity(row: dict) -> dict:
    return {key: row.get(key) for key in ("source_declaration_index", "line", "registration", "context", "ctest_name", "upstream_path")}


def original_rows(evidence: Evidence, source_path: Path, retry_paths: list[Path]) -> tuple[dict, dict, list, list]:
    base = evidence.capture(source_path)
    plan = base.json()
    require(plan.get("cmake_sources") == CMAKE_SOURCES, "source plan does not bind the original CMake files")
    rows = declaration_rows(plan)
    require(set(rows) == {row["source_declaration_index"] for row in load_catalog()["declarations"]},
            "base source plan must retain the complete pinned declaration set")
    plans = {base.ref["sha256"]: (base, plan)}
    superseded = []
    for path in retry_paths:
        captured = evidence.capture(path)
        retry = captured.json()
        parent = evidence.reference(retry.get("base_inventory"))
        require(parent.ref["sha256"] in plans, "retry does not bind a previously supplied source plan")
        updates = declaration_rows(retry)
        for index, update in updates.items():
            require(index in rows and source_identity(update) == source_identity(rows[index]),
                    "retry changes the original source declaration identity")
            old = rows[index]
            previous = update.get("supersedes", {})
            require(previous.get("original_state") == old["state"]
                    and previous.get("original_native_receipt") == old.get("native_receipt")
                    and previous.get("original_manifest") == old.get("manifest"),
                    "retry does not explicitly supersede the current original attempt")
            old_refs = [evidence.reference(old[field]).ref for field in ("native_receipt", "manifest") if old.get(field)]
            superseded.append({"source_declaration_index": index, "ctest_name": old.get("ctest_name"),
                               "previous": old_refs, "retry_plan": captured.ref})
            rows[index] = update
        plans[captured.ref["sha256"]] = (captured, retry)
    return rows, plans, superseded, [entry[0].ref for entry in plans.values()]


def read_matrices(evidence: Evidence, paths: list[Path], plans: dict, context: dict) -> tuple[dict, list]:
    observations, references = {}, []
    for path in paths:
        captured = evidence.capture(path)
        matrix = captured.json()
        require(matrix.get("schema") == 1 and matrix.get("upstream_commit") == UPSTREAM_SHA,
                "browser matrix targets another upstream revision")
        native_plan = evidence.reference(matrix.get("native_inventory"))
        require(native_plan.ref["sha256"] in plans, "browser matrix binds an unselected native source plan")
        plan_rows = declaration_rows(native_plan.json())
        require(identity(matrix.get("asset"), "matrix engine") == identity(context["browser"]["engine_archive"], "context engine")
                and identity(matrix.get("browser_executable"), "matrix browser") == identity(context["browser"]["browser"], "context browser"),
                "matrix executable or engine differs from independently measured context")
        build = evidence.reference(matrix.get("source_build_receipt"))
        require(build.ref["sha256"] == context["source"].ref["sha256"], "matrix source build receipt differs from context")
        package_refs = []
        overlay = context["overlay"]
        if overlay:
            selected_overlay = evidence.reference(matrix.get("package_overlay_receipt"))
            require(identity(selected_overlay.ref, "matrix overlay") == identity(overlay["receipt"].ref, "context overlay")
                    and identity(matrix.get("package_base_asset"), "matrix base asset") == identity(overlay["base_asset"], "context base asset"),
                    "matrix package overlay or base archive differs from independent context")
            package_refs.append(selected_overlay.ref)
        else:
            require(not {"package_overlay_receipt", "package_base_asset"} & matrix.keys(),
                    "matrix package overlay lacks an independent package context")
        harness = evidence.reference(matrix.get("harness_manifest"))
        files, names, harness_refs, harness_by_name = harness.json().get("files"), set(), [], {}
        require(isinstance(files, list) and files, "browser harness snapshot is missing")
        for row in files:
            require(row["path"] not in names and not Path(row["path"]).is_absolute()
                    and ".." not in PurePosixPath(row["path"]).parts, "duplicate or unsafe harness path")
            names.add(row["path"])
            captured_tool = evidence.reference(row, harness.path.parent / "harness")
            harness_refs.append(captured_tool.ref)
            harness_by_name[row["path"]] = captured_tool
        require({"tools/probe_browser_port.py", "tools/unittest_cohort.py"} <= names,
                "browser harness omits the actual original-main producer")
        if overlay:
            required_package_files = {"tools/browser_package_overlay.py", "compatibility/package-overlays/essentials-brushes-5.2.json"}
            require(required_package_files <= names, "browser harness omits the reviewed package verifier or plan")
            require(harness_by_name["tools/browser_package_overlay.py"].data == overlay["verifier"].data
                    and identity(harness_by_name["compatibility/package-overlays/essentials-brushes-5.2.json"].ref, "harness plan")
                        == identity(overlay["plan_identity"], "reviewed plan"),
                    "browser harness substituted its package verifier or resource plan")
        rows = matrix.get("registrations")
        require(isinstance(rows, list), "matrix registration list is missing")
        seen = set()
        raw = unique_refs([captured.ref, native_plan.ref, build.ref, harness.ref, *harness_refs, *package_refs])
        for row in rows:
            index = row.get("source_declaration_index")
            require(index in plan_rows and index not in seen, "duplicate or unknown matrix source declaration")
            seen.add(index)
            expected = plan_rows[index]
            require(row.get("ctest_name") == expected.get("ctest_name") and row.get("state") == expected["state"],
                    "matrix declaration identity differs from its plan")
            if expected["state"] == "native_inventory_frozen":
                pin = row.get("manifest", {})
                require(pin.get("sha256") == expected["manifest"]["sha256"], "matrix selected another frozen manifest")
                key = (index, pin["sha256"])
                require(key not in observations, "multiple executions for the same selected invocation need an explicit selection")
                observations[key] = {"row": row, "matrix": matrix, "raw": raw, "path": captured.path,
                                     "harness": harness.ref, "harness_names": names}
        require(seen == set(plan_rows), "browser matrix dropped source declarations from its native plan")
        references.append(captured.ref)
    return observations, references


def metadata(row: dict) -> dict:
    return {key: row.get(key) for key in SOURCE_FIELDS}


def normalized_id(path: str, value: str) -> str:
    return path + "::" + case_id(value)


def normalized_detail(value: Any, source_root: str | None) -> str | None:
    require(value is None or isinstance(value, str), "outcome detail must be text or null")
    if value is None:
        return None
    if source_root:
        value = value.replace(source_root.rstrip("/") + "/", "{source_root}/")
    return sha(value.encode())


def normalize_outcomes(result: dict, manifest: dict, policy_sha: str) -> tuple[list, dict, list]:
    """Preserve terminal observations, including subtest-only parent failures."""
    suite = manifest["suites"][0]
    path, expected = suite["upstream_path"], set(suite["case_ids"])
    observed = result.get("suites", [])
    blockers, cases = [], []
    counts = {"fixed_native_cases": len(expected), "discovered": 0, "executed": 0,
              "observed_terminal_cases": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0,
              "expected_failure": 0, "unexpected_success": 0, "subtest_events": 0,
              "missing_outcomes": len(expected), "unexpected_discovered_ids": [], "unassigned_events": []}
    require(isinstance(observed, list), "observed suite list is invalid")
    if not observed:
        return cases, counts, ["original_suite_did_not_reach_unittest_runner"]
    require(len(observed) == 1, "original invocation produced more than one suite")
    row = observed[0]
    require(row.get("upstream_path") == path and row.get("sha256") == suite["sha256"], "executed source differs from frozen source")
    original_ids = strings(row.get("discovered_ids"), "observed discovered IDs")
    ids = [case_id(value) for value in original_ids]
    require(len(ids) == len(set(ids)) and type(row.get("discovered")) is int and row["discovered"] == len(ids),
            "observed discovery is duplicated or has an inconsistent count")
    require(type(row.get("testsRun")) is int and 0 <= row["testsRun"] <= len(ids), "observed executed count is invalid")
    counts.update(discovered=len(ids), executed=row["testsRun"],
                  unexpected_discovered_ids=sorted(set(ids) - expected))
    if set(ids) != expected:
        blockers.append("observed_discovery_differs_from_fixed_native_inventory")
    if row["testsRun"] != len(expected):
        blockers.append("original_unittest_did_not_execute_every_frozen_case")
    outcomes = row.get("outcomes")
    require(isinstance(outcomes, list), "original outcome observations are missing")
    for field in ("failures", "errors", "skipped", "expected_failures", "unexpected_successes"):
        require(type(row.get(field)) is int and row[field] >= 0, "original unittest counter is invalid: " + field)
    grouped, subevents = defaultdict(list), defaultdict(list)
    source_root = result.get("execution_context", {}).get("source_root")
    for event in outcomes:
        require(isinstance(event, dict) and event.get("kind") in {"test", "subtest"}
                and event.get("status") in EVENT_OUTCOMES and isinstance(event.get("id"), str),
                "invalid original unittest outcome event")
        parent = event.get("parent_id") if event["kind"] == "subtest" else event["id"]
        require(isinstance(parent, str), "subtest parent identity is missing")
        cid = case_id(parent)
        if cid not in expected or cid not in ids:
            counts["unassigned_events"].append(event)
            blockers.append("outcome_event_has_no_frozen_parent")
            continue
        detail = normalized_detail(event.get("detail"), source_root)
        converted = {"id": normalized_id(path, event["id"]), "outcome": event["status"]}
        if detail is not None:
            converted["detail_sha256"] = detail
        if event["kind"] == "subtest":
            require(event["id"].startswith(parent + " "), "subtest ID is not bound to its exact parent ID")
            subevents[cid].append(converted)
            counts["subtest_events"] += 1
        else:
            require(event.get("parent_id") is None, "top-level test event has a parent")
            grouped[cid].append(converted)
    event_counts = Counter(event["status"] for event in outcomes)
    # Old producer versions labeled non-AssertionError subtests as failed while
    # unittest correctly counted them as errors. Retain that historical label;
    # compare the combined failure/error counter and preserve its original split.
    if (row["failures"] + row["errors"] != event_counts["failed"] + event_counts["error"]
            or row["skipped"] != event_counts["skipped"]
            or row["expected_failures"] != event_counts["expected_failure"]
            or row["unexpected_successes"] != event_counts["unexpected_success"]):
        blockers.append("original_unittest_counters_disagree_with_outcome_events")
    for cid in suite["case_ids"]:
        events, subtests = grouped[cid], subevents[cid]
        require(len({event["id"] for event in subtests}) == len(subtests),
                "duplicate subtest identity cannot be matched one to one")
        require(len(events) <= 1, "multiple terminal parent callbacks require an explicit reviewed aggregation")
        derived = False
        if events:
            status = events[0]["outcome"]
            detail = events[0].get("detail_sha256")
            require(status != "passed" or all(event["outcome"] == "passed" for event in subtests),
                    "passing parent contradicts a nonpassing subtest")
        elif any(event["outcome"] in {"failed", "error", "skipped"} for event in subtests):
            # unittest suppresses addSuccess after a nonpassing subTest. The
            # failure event itself, not absence of a parent, establishes this
            # derived nonpassing result. Never infer a pass from subtests alone.
            status = "error" if any(event["outcome"] == "error" for event in subtests) else (
                "failed" if any(event["outcome"] == "failed" for event in subtests) else "skipped")
            detail = canonical_sha256(sorted(subtests, key=lambda event: event["id"]))
            derived = True
        else:
            continue
        comparison = "passed" if status == "passed" else (
            "not_applicable" if status in {"skipped", "expected_failure"} else "failed")
        item = {"id": normalized_id(path, cid), "outcome": status, "started": True, "completed": True,
                "comparison": {"status": comparison, "policy_sha256": policy_sha},
                "subtests": sorted(subtests, key=lambda event: event["id"])}
        if detail is not None:
            item["detail_sha256"] = detail
        if derived:
            item["outcome_basis"] = "Observed nonpassing subtest; upstream unittest emits no successful parent callback."
        cases.append(item)
        counts[status] += 1
    counts["observed_terminal_cases"] = len(cases)
    counts["missing_outcomes"] = len(expected) - len(cases)
    counts["original_unittest_counters"] = {key: row.get(key) for key in
        ("testsRun", "failures", "errors", "skipped", "expected_failures", "unexpected_successes")}
    return cases, counts, sorted(set(blockers))


def check_sources(raw: dict, manifest: dict, native: bool) -> None:
    sources = raw.get("suite_sources")
    require(isinstance(sources, list) and len(sources) == 1, "receipt does not identify exactly one original source")
    actual, expected = sources[0], manifest["suites"][0]
    require(metadata(actual) == metadata(expected), "receipt source identity differs from frozen manifest")
    for field in ("support_files", "fixture_files", "resource_files"):
        require(actual.get(field, []) == expected.get(field, []), "receipt source closure differs: " + field)
    require(actual.get("driver") == "unittest-main" and actual.get("required_background") is True
            and actual.get("driver_execution") == manifest["execution"]
            and actual.get("case_id_normalization") == "original-main", "receipt original driver contract differs")
    if not native:
        for field in ("case_ids", "mandatory_case_ids", "expected_cases"):
            require(actual.get(field) == expected[field], "browser receipt changed its frozen case inventory")


def driver_blockers(result: dict, manifest: dict) -> list[str]:
    blockers = []
    observed = result.get("driver_observation", {})
    context = result.get("execution_context", {})
    if result.get("exception") is not None:
        blockers.append("original_script_raised_outside_unittest")
    if observed.get("entrypoint") != "original __main__" or observed.get("runner_invocations") != 1:
        blockers.append("one_original_unittest_entrypoint_not_observed")
    if observed.get("failfast") is not False:
        blockers.append("unfiltered_non_failfast_runner_not_observed")
    # Original scripts legitimately use sys.exit(not result.wasSuccessful()).
    # A boolean SystemExit payload is not the OS process return code; the latter
    # is independently required to be an actual integer by process_observation.
    if observed.get("original_exit_code") is not None and type(observed["original_exit_code"]) not in {int, bool}:
        blockers.append("original_unittest_exit_has_no_numeric_status")
    if context.get("background") is not True or context.get("entrypoint") != "original __main__":
        blockers.append("original_background_context_not_observed")
    source_root = context.get("source_root")
    require(isinstance(source_root, str) and source_root.startswith("/") and len(source_root) > 1,
            "observed original source root is missing")
    execution, source = manifest["execution"], manifest["suites"][0]
    identity_row = result.get("identity", {})
    require(identity_row.get("version") == [5, 2, 0] and identity_row.get("build_hash") in {UPSTREAM_SHA, UPSTREAM_SHA[:12]},
            "observed Blender identity differs from the bound runtime")
    expected_argv = [identity_row.get("binary_path"), *execution["blender_args"], "--python", source_root + "/" + source["upstream_path"]]
    arguments = [value.replace("{fixture_root}", source_root + "/tests/files") for value in execution["script_args"]]
    if arguments:
        expected_argv += ["--", *arguments]
    require(context.get("script_argv") == expected_argv, "observed original script argv differs from its CMake invocation")
    for field in ("support_files", "resource_files"):
        if observed.get(field, []) != [metadata(row) for row in source.get(field, [])]:
            blockers.append("original_" + field + "_not_observed")
    io = result.get("io_observation", {})
    fixtures = [{key: row[key] for key in ("relative_path", "upstream_path", "bytes", "sha256")}
                for row in source.get("fixture_files", [])]
    if io.get("fixture_bytes_preserved") is not True or io.get("fixture_files", []) != fixtures:
        blockers.append("original_fixture_bytes_not_observed")
    tools = observed.get("host_tools", [])
    require(isinstance(tools, list) and len({row.get("environment") for row in tools}) == len(tools),
            "duplicate host-tool observation")
    by_name = {row.get("environment"): row for row in tools}
    for tool in execution.get("host_tools", []):
        actual = by_name.get(tool["environment"], {})
        if (actual.get("available") is not True or actual.get("sha256") != tool["sha256"]
                or actual.get("bytes") != tool["bytes"]):
            blockers.append("original_host_tool_identity_not_observed:" + tool["environment"])
    return sorted(set(blockers))


def process_observation(raw: dict, host: dict | None = None) -> dict:
    if host is None:
        code = raw.get("process", {}).get("returncode")
        require(code is None or type(code) is int, "native process exit must be an integer or null")
        started = isinstance(raw.get("started_utc"), str) and bool(raw["started_utc"])
        completed = started and isinstance(raw.get("finished_utc"), str) and bool(raw["finished_utc"]) and code is not None
        timed_out = raw.get("process", {}).get("timed_out", False)
        require(type(timed_out) is bool, "native timeout metadata is invalid")
    else:
        code = raw.get("execution_mode", {}).get("runtime_exit_code")
        require(code is None or type(code) is int, "browser runtime exit must be an integer or null")
        require(type(host.get("timed_out")) is bool and
                (host.get("returncode") is None or type(host["returncode"]) is int), "host process metadata is invalid")
        timed_out = host["timed_out"]
        started = isinstance(host.get("started_utc"), str) and bool(host["started_utc"])
        completed = (started and isinstance(host.get("finished_utc"), str) and bool(host["finished_utc"])
                     and host.get("returncode") is not None and host["returncode"] >= 0 and code is not None)
    bounds = raw if host is None else host
    if completed:
        require(timestamp(bounds["started_utc"], "process start") <= timestamp(bounds["finished_utc"], "process end"),
                "process completion precedes its start")
    crashed = bool(code is not None and code < 0)
    if host is not None:
        crashed = crashed or bool(host.get("returncode") is not None and host["returncode"] < 0)
        crashed = crashed or "browser page crashed" in raw.get("browser_errors", [])
    return {"started": started, "completed": completed, "exit_code": code, "timed_out": timed_out, "crashed": crashed}


def raw_blockers(raw: dict) -> list[str]:
    transport = raw.get("transport", {})
    blockers = []
    if (transport.get("protocol") != "marker-prefixed-json-v1" or transport.get("result_markers") != 1
            or transport.get("trailing_runtime_text") or transport.get("recovered_json_prefix") is not False):
        blockers.append("incomplete_or_ambiguous_result_transport")
    code = raw.get("execution_mode", {}).get("runtime_exit_code")
    for error in raw.get("browser_errors", []):
        if type(code) is int and error == "browser background runtime exited with code " + str(code):
            continue
        blockers.append("browser_runtime_error:" + str(error))
    return blockers


def check_cohort(raw: dict, manifest: dict, manifest_sha: str, native: bool) -> None:
    check_target(raw.get("upstream"), "raw receipt")
    require(raw.get("profile") == (NATIVE if native else BROWSER), "raw receipt belongs to another runtime profile")
    cohort = raw.get("cohort", {})
    require(cohort.get("id") == manifest["cohort_id"] and cohort.get("suite_kind") == "unittest-main"
            and cohort.get("complete_cohort_requested") is True
            and cohort.get("original_invocation") == manifest["execution"]
            and cohort.get("blender_args") == manifest["execution"]["blender_args"],
            "raw receipt is not the complete original invocation")
    expected_sha = manifest["discovery_manifest_sha256"] if native else manifest_sha
    require(cohort.get("manifest_sha256") == expected_sha and
            cohort.get("stage") == ("native-discovery" if native else "frozen"), "raw receipt manifest binding differs")
    if not native:
        require(cohort.get("native_discovery") == manifest["native_discovery"]
                and cohort.get("expected_cases") == manifest["expected_total_cases"],
                "browser receipt changed the native discovery binding")
    digest(raw.get("runner_sha256"), "actual producer runner sha256")
    check_sources(raw, manifest, native)


def check_browser(raw: dict, host: dict, observation: dict, manifest_file: Captured, context: dict) -> None:
    manifest = manifest_file.json()
    check_cohort(raw, manifest, manifest_file.ref["sha256"], False)
    expected = identity(context["browser"]["engine_archive"], "browser engine")
    artifact = raw.get("artifact", {})
    require((artifact.get("observed_sha256"), artifact.get("observed_bytes")) == expected
            and (artifact.get("expected_sha256"), artifact.get("expected_bytes")) == expected,
            "browser receipt executed another engine artifact")
    require(raw.get("source_build_receipt_verified") is True
            and raw.get("source_build", {}).get("receipt_sha256") == context["source"].ref["sha256"],
            "browser receipt does not bind the independently supplied source build")
    require(engine_files(raw.get("engine_files")) == context["engine_files"],
            "browser extracted engine files differ from independently bound build artifact")
    overlay = context["overlay"]
    if overlay:
        require(raw.get("package_overlay") == overlay["verified"]
                and raw.get("candidate", {}).get("kind") == "blender-source-development-package-overlay"
                and raw["candidate"].get("package_overlay_id") == overlay["verified"]["overlay_id"]
                and identity(raw.get("source_build", {}).get("base_artifact"), "observed base archive")
                    == identity(overlay["base_asset"], "context base archive"),
                "browser receipt did not independently verify the selected package overlay")
    else:
        require(raw.get("package_overlay") is None
                and raw.get("candidate", {}).get("kind") != "blender-source-development-package-overlay"
                and "base_artifact" not in raw.get("source_build", {}),
                "browser receipt package overlay lacks an independent package context")
    browser = raw.get("browser", {})
    require(browser.get("flags") == context["browser"]["requested_flags"] and
            str(context["browser"]["browser"].get("version", "")).endswith(" " + str(browser.get("version"))),
            "observed browser version or flags differ from measured context")
    mode = raw.get("execution_mode", {})
    require(mode.get("requested") == "background" and mode.get("extra_argv") == manifest["execution"]["blender_args"],
            "browser shell did not request the original Blender flags")
    command = host.get("command")
    require(isinstance(command, list) and len(command) >= 2 and all(isinstance(item, str) for item in command),
            "browser host command is missing")
    matrix = observation["matrix"]
    require(command[0] == matrix.get("python_executable", {}).get("path")
            and command[1] == str(PurePosixPath(matrix["harness_manifest"]["path"]).parent / "harness/tools/probe_browser_port.py"),
            "browser host command is not the bound harness")
    permitted = {"--asset", "--source-build-receipt", "--suite-manifest", "--suite-manifest-sha256",
                 "--browser-executable", "--output", "--timeout", "--suite", "--fixture-root", "--resource-root"}
    if overlay:
        permitted.update({"--package-overlay-receipt", "--package-base-asset"})
    require(len(command[2:]) % 2 == 0 and all(command[index] in permitted for index in range(2, len(command), 2)),
            "browser host command has an unreviewed argument or selection filter")
    require(all(command[2::2].count(name) <= 1 for name in permitted - {"--suite"}),
            "browser host command repeats a configuration flag")
    def flag(name):
        require(command.count(name) == 1 and command.index(name) + 1 < len(command), "missing or repeated host flag: " + name)
        return command[command.index(name) + 1]
    require(flag("--suite-manifest-sha256") == manifest_file.ref["sha256"]
            and flag("--suite-manifest") == observation["row"]["manifest"]["path"]
            and flag("--asset") == matrix["asset"]["path"]
            and flag("--browser-executable") == matrix["browser_executable"]["path"]
            and flag("--source-build-receipt") == matrix["source_build_receipt"]["path"],
            "browser host command does not bind the selected manifest and artifact context")
    if overlay:
        require(flag("--package-overlay-receipt") == matrix["package_overlay_receipt"]["path"]
                and flag("--package-base-asset") == matrix["package_base_asset"]["path"],
                "browser host command substituted the package overlay or base archive")
    expected_sources = [manifest["suites"][0], *manifest["suites"][0].get("support_files", [])]
    supplied_sources = [command[index + 1] for index in range(2, len(command), 2) if command[index] == "--suite"]
    require(len(supplied_sources) == len(expected_sources) and all(
        actual.endswith("/" + expected["upstream_path"]) for actual, expected in zip(supplied_sources, expected_sources)),
        "browser host command omits or substitutes an original source file")
    require(flag("--output") == str(PurePosixPath(observation["row"]["browser_receipt"]["path"]).parent),
            "browser receipt was substituted from another output directory")
    require(timestamp(host.get("started_utc"), "host start") <= timestamp(raw.get("started_utc"), "browser receipt start")
            <= timestamp(raw.get("finished_utc"), "browser receipt end") <= timestamp(host.get("finished_utc"), "host end"),
            "browser receipt is stale or outside the recorded host process interval")
    require(timestamp(matrix.get("started_utc"), "matrix start") <= timestamp(host.get("started_utc"), "host start"),
            "host execution predates its matrix")
    if matrix.get("finished_utc") is not None:
        require(timestamp(host.get("finished_utc"), "host end") <= timestamp(matrix["finished_utc"], "matrix end"),
                "host execution follows its completed matrix")
    argv = raw.get("execution", {}).get("execution_context", {}).get("runtime_argv", [])
    runner_pins = [item.get("injected_runner_sha256") for item in argv if isinstance(item, dict) and "injected_runner_sha256" in item]
    require(runner_pins == [raw["runner_sha256"]], "browser observed argv does not bind its actual injected producer")


def main_contract(rows: dict, manifests: dict, context: dict, program: list, inputs: list) -> dict:
    registrations = []
    policy_sha = canonical_sha256(POLICY)
    for index, row in sorted(rows.items()):
        manifest = manifests.get(index)
        if manifest:
            source = manifest["suites"][0]
            invocation = {"execution": manifest["execution"], "source": metadata(source),
                          "support_files": source.get("support_files", [])}
            fixtures = {"fixture_files": source.get("fixture_files", []), "resource_files": source.get("resource_files", []),
                        "host_tools": manifest["execution"].get("host_tools", [])}
        else:
            # This hashes the supplied unresolved declaration, not invented
            # execution/configuration evidence. It is permanently blocked until
            # an actual manifest and native discovery supply concrete criteria.
            invocation = {"unresolved_source_declaration": source_identity(row)}
            fixtures = {"unresolved_inputs_for_source_declaration": index}
        registrations.append({"id": "source-declaration:" + str(index), "source_declaration": source_identity(row),
                              "criteria_kind": "original-invocation" if manifest else "unresolved-source-obligation",
                              "invocation_sha256": canonical_sha256(invocation),
                              "fixture_manifest_sha256": canonical_sha256(fixtures),
                              "comparison_policy_sha256": policy_sha})
    limitations = ["Source declarations are not a configured CTest inventory or an all-Blender leaf denominator.",
                  "Only this artifact pair and selected original background unittest invocations are measured.",
                  "The native release has measured build options, not a recovered full CMake configuration matrix.",
                  "Fixture and host-service closure remains unproved for unresolved declarations.",
                  "A local software Chromium profile does not qualify hardware browsers, deployment, UI, or Blender 5.4."]
    return {"schema": 1, "target": TARGET, "scope": "bounded-source-plan-and-native-frozen-original-unittest-invocations",
            "configurations": [{"id": CONFIGURATION, "registrations": registrations}],
            "profiles": [{"id": pid, "role": role, "runtime_kind": kind, "contexts": {CONFIGURATION: context["contexts"][pid]}}
                         for pid, role, kind in [(NATIVE, "reference", "native"), (BROWSER, "candidate", "browser")]],
            "coverage": {"source_registration_reconciliation_complete": False, "configuration_matrix_complete": False,
                         "fixture_closure_complete": False, "blockers": limitations},
            "normalization_adapter": {"meaning": "Versioned evidence normalization program; not an independent execution-adapter verification.",
                                      "files": program, "policy": POLICY},
            "input_evidence": inputs, "context_evidence": context["raw"]}


def reconcile(repo_root: Path, source_plan: Path, browser_matrices: list[Path], native_context: Path,
              browser_context: Path, output: Path, retry_plans: list[Path] = ()) -> dict:
    evidence = Evidence(repo_root, output)
    program = []
    for name in ("reconcile_unittest_matrix.py", "test_parity_ledger.py", "unittest_cohort.py", "upstream_resources.py",
                 "probe_blender_fixtures.py", "upstream_invocations.py", "upstream_invocations_5_2.json",
                 "browser_package_overlay.py"):
        path = Path(__file__).with_name(name)
        program.append(evidence.write("normalizer/" + name, path.read_bytes()))
    program.append(evidence.write("compatibility/package-overlays/essentials-brushes-5.2.json", OVERLAY_PLAN_PATH.read_bytes()))
    context = read_contexts(evidence, native_context, browser_context, program[0]["sha256"])
    rows, plans, superseded, plan_refs = original_rows(evidence, source_plan, list(retry_plans))
    browser_rows, matrix_refs = read_matrices(evidence, browser_matrices, plans, context)
    manifests, frozen, natives, raw_by_index = {}, {}, {}, {}
    for index, row in sorted(rows.items()):
        if row["state"] != "native_inventory_frozen":
            if row.get("native_receipt"):
                evidence.reference(row["native_receipt"])
            continue
        captured = evidence.reference(row.get("manifest"))
        manifest = validate_manifest(captured.json())
        require(manifest["execution"]["ctest_name"] == row["ctest_name"]
                and manifest["execution"]["registration"] == row["registration"]
                and manifest["suites"][0]["upstream_path"] == row["upstream_path"],
                "frozen manifest changed its source declaration")
        native = evidence.reference(manifest.get("native_discovery"), captured.path.parent)
        selected = evidence.reference(row.get("native_receipt"))
        require(selected.ref["sha256"] == native.ref["sha256"], "source plan and frozen manifest choose different native receipts")
        value = native.json()
        ids = validate_native_discovery(manifest, value, manifest.get("discovery_manifest_sha256"))
        require(ids == manifest["suites"][0]["case_ids"] and len(ids) == row.get("expected_cases"),
                "frozen denominator differs from native discovery")
        check_cohort(value, manifest, captured.ref["sha256"], True)
        require(identity(value.get("executable"), "native run executable") == identity(context["native"]["executable"], "context executable"),
                "native run executable differs from independently measured context")
        require(value.get("artifact", {}).get("expected_sha256") == NATIVE_ARCHIVE_SHA256,
                "native expected artifact identity changed")
        native_log = evidence.reference(value.get("log"), native.path.parent)
        check_execution_log(native_log, value, True)
        raw = [captured.ref, native.ref, native_log.ref]
        proposal = native.path.parent / "discovery-proposal.json"
        if not proposal.exists():
            proposal = evidence.root / "compatibility/candidate-suites/resource-discovery-5.2" / (row["ctest_name"] + ".json")
        original = evidence.capture(proposal, {"sha256": manifest["discovery_manifest_sha256"]})
        proposal_value = validate_manifest(original.json(), allow_discovery=True)
        require(proposal_value["stage"] == "native-discovery" and proposal_value["execution"] == manifest["execution"],
                "native discovery proposal changed the original invocation")
        require({key: item for key, item in manifest["suites"][0].items()
                 if key not in {"case_ids", "mandatory_case_ids", "expected_cases"}} == proposal_value["suites"][0],
                "frozen manifest changed source or input closure after native discovery")
        raw.append(original.ref)
        for source in [manifest["suites"][0], *manifest["suites"][0].get("support_files", [])]:
            path = native.path.parent / "sources" / source["upstream_path"]
            if path.exists():
                raw.append(evidence.capture(path, source).ref)
        for field, directory, key in (("fixture_files", "fixtures", "relative_path"), ("resource_files", "resources", "upstream_path")):
            for source in manifest["suites"][0].get(field, []):
                raw.append(evidence.capture(native.path.parent / directory / source[key], source).ref)
        manifests[index], frozen[index], natives[index], raw_by_index[index] = manifest, captured, value, raw
    contract = main_contract(rows, manifests, context, program, unique_refs(plan_refs + matrix_refs))
    evidence.json("contract.json", contract)
    contract_sha = canonical_sha256(contract)
    required = {int(row["id"].split(":")[1]): row for row in contract["configurations"][0]["registrations"]}
    inventory = {"schema": 1, "target": TARGET, "contract_sha256": contract_sha, "registrations": []}
    receipts, diagnostics = [], []
    def base_receipt(index, profile):
        return {"schema": 1, "target": TARGET, "contract_sha256": contract_sha, "configuration": CONFIGURATION,
                "registration_id": required[index]["id"], "profile": profile,
                "runtime_kind": "native" if profile == NATIVE else "browser", "context": context["contexts"][profile],
                **{key: required[index][key] for key in ("invocation_sha256", "fixture_manifest_sha256", "comparison_policy_sha256")},
                "selection": {"filters": [], "shard": None}}
    for index, row in sorted(rows.items()):
        item = {"id": required[index]["id"], "configuration": CONFIGURATION, "status": "blocked",
                "case_ids": [], "disabled_case_ids": [], "source_state": row["state"], "reason": row.get("reason")}
        inventory["registrations"].append(item)
        if index not in manifests:
            continue
        manifest, native, raw = manifests[index], natives[index], raw_by_index[index]
        cases = [normalized_id(manifest["suites"][0]["upstream_path"], value) for value in manifest["suites"][0]["case_ids"]]
        process = process_observation(native)
        discovery = {**base_receipt(index, NATIVE), "kind": "blender-test-discovery", "process": process,
                     "case_ids": cases, "disabled_case_ids": [], "raw_evidence": unique_refs(raw + context["raw"]),
                     "discovery_basis": "Observed original unittest loader before the complete original invocation; process exit is preserved."}
        item.update(status="expanded", case_ids=cases, discovery=evidence.json("receipts/" + str(index) + "/discovery.json", discovery))
        pair_cases = {}
        diag = {"source_declaration_index": index, "ctest_name": row["ctest_name"], "fixed_native_cases": len(cases),
                "manifest": frozen[index].ref, "native": None, "browser": None}
        diagnostics.append(diag)
        for profile in (NATIVE, BROWSER):
            refs, host, observation = list(raw), None, None
            value = native
            if profile == BROWSER:
                observation = browser_rows.get((index, frozen[index].ref["sha256"]))
                if not observation or not observation["row"].get("browser_receipt"):
                    diag["browser"] = {"state": "missing_receipt", "missing_outcomes": len(cases)}
                    continue
                reported = evidence.reference(observation["row"]["browser_receipt"])
                host_file = evidence.reference(observation["row"].get("host_process"))
                host, value = host_file.json(), reported.json()
                check_browser(value, host, observation, frozen[index], context)
                refs += [reported.ref, host_file.ref, evidence.reference(host.get("log")).ref, *observation["raw"]]
                # Logs without producer checksums are attachments captured now;
                # they cannot replace a semantic receipt or prove completion.
                for name in ("browser.log", "http.log"):
                    log = reported.path.parent / name
                    if log.exists():
                        log_file = evidence.capture(log)
                        if name == "browser.log":
                            check_execution_log(log_file, value, False)
                        refs.append(log_file.ref)
                    elif name == "browser.log":
                        raise ValueError("original browser execution log is missing")
                raw_receipt = reported.ref
            else:
                raw_receipt = raw[1]
            result = value.get("execution")
            require(isinstance(result, dict), "original driver execution observation is missing")
            normalized, counts, blockers = normalize_outcomes(result, manifest, required[index]["comparison_policy_sha256"])
            blockers += driver_blockers(result, manifest) + raw_blockers(value)
            process = process_observation(value, host)
            if not process["completed"]:
                blockers.append("actual_runtime_process_completion_not_observed")
            pair_cases[profile] = normalized
            diag["native" if profile == NATIVE else "browser"] = {"state": "observed", "counts": counts,
                "process": process, "validation_blockers": sorted(set(blockers)), "raw_receipt": raw_receipt,
                "original_exception": result.get("exception")}
            receipt = {**base_receipt(index, profile), "kind": "blender-test-execution", "process": process,
                       "run_id": profile + ":" + raw_receipt["sha256"], "cases": normalized,
                       "validation_blockers": sorted(set(blockers)), "raw_evidence": unique_refs(refs + context["raw"]),
                       "producer": {"runner_sha256": value["runner_sha256"], "raw_receipt": raw_receipt,
                                    "harness_manifest": observation["harness"] if observation else None},
                       "case_started_meaning": "Original unittest lifecycle has a terminal callback; a skip does not imply its test body ran."}
            receipts.append((index, profile, receipt))
        native_subtests = {event["id"] for case in pair_cases.get(NATIVE, []) for event in case["subtests"]}
        browser_subtests = {event["id"] for case in pair_cases.get(BROWSER, []) for event in case["subtests"]}
        diag["missing_browser_subtest_ids"] = sorted(native_subtests - browser_subtests)
        diag["unexpected_browser_subtest_ids"] = sorted(browser_subtests - native_subtests)
    evidence.json("inventory.json", inventory)
    inventory_sha = canonical_sha256(inventory)
    executions = {"schema": 1, "target": TARGET, "contract_sha256": contract_sha, "inventory_sha256": inventory_sha, "runs": []}
    for index, profile, receipt in receipts:
        receipt["inventory_sha256"] = inventory_sha
        executions["runs"].append({"profile": profile, "configuration": CONFIGURATION, "registration_id": required[index]["id"],
                                   "run_id": receipt["run_id"], "receipt": evidence.json("receipts/" + str(index) + "/" + profile + ".json", receipt)})
    evidence.json("executions.json", executions)
    report = assess(contract, inventory, executions, evidence.output)
    totals = {}
    for label in ("native", "browser"):
        total = Counter()
        for row in diagnostics:
            record = row[label]
            if record and record.get("state") == "observed":
                total.update({key: value for key, value in record["counts"].items() if type(value) is int})
            else:
                total.update(fixed_native_cases=row["fixed_native_cases"], missing_outcomes=row["fixed_native_cases"])
        totals[label] = dict(sorted(total.items()))
    report["observation_totals"] = totals
    report["missing_browser_subtest_count"] = sum(len(row["missing_browser_subtest_ids"]) for row in diagnostics)
    report["unexpected_browser_subtest_count"] = sum(len(row["unexpected_browser_subtest_ids"]) for row in diagnostics)
    report["observation_count_limit"] = "Original callback counts are diagnostic; they do not imply one-to-one outcome agreement or successful process execution."
    evidence.json("report.json", report)
    evidence.json("conversion.json", {"schema": 1, "normalization_program": program, "inputs": unique_refs(plan_refs + matrix_refs),
                                       "context_evidence": context["raw"], "superseded_attempts": superseded,
                                       "registrations": diagnostics, "raw_origins": evidence.origins,
                                       "all_upstream_test_parity": False, "full_feature_parity": False})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--source-plan", required=True, type=Path)
    parser.add_argument("--native-retry-plan", action="append", type=Path, default=[])
    parser.add_argument("--browser-matrix", action="append", type=Path, required=True)
    parser.add_argument("--native-context", required=True, type=Path)
    parser.add_argument("--browser-context", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = reconcile(args.repo_root, args.source_plan, args.browser_matrix, args.native_context,
                           args.browser_context, args.output, args.native_retry_plan)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"gate": "invalid", "declared_scope_test_parity": False, "all_upstream_test_parity": False,
                          "full_feature_parity": False, "error": str(exc)}))
        return 2
    print(json.dumps({key: value for key, value in report.items() if key not in {"pairs", "registrations", "coverage_review"}}))
    return 0 if args.report_only or report["declared_scope_test_parity"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
