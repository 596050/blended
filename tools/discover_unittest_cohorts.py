#!/usr/bin/env python3
"""Discover native leaf IDs for supported original Blender Python invocations.

This bounded source plan is not configured CTest discovery. Every unsupported,
conditional, UI, fixture, or non-unittest declaration remains explicitly blocked.
Eligible complete scripts run one per new native process with upstream flags.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil

try:
    from . import probe_native_reference as native
    from .unittest_cohort import CMAKE_SOURCES, CTEST_BLENDER_ARGS, UPSTREAM_SHA, validate_manifest
except ImportError:
    import probe_native_reference as native
    from unittest_cohort import CMAKE_SOURCES, CTEST_BLENDER_ARGS, UPSTREAM_SHA, validate_manifest


try:
    from .upstream_invocations import cmake_commands, registrations
except ImportError:
    from upstream_invocations import cmake_commands, registrations


def source_row(path, root):
    data = path.read_bytes()
    return {"upstream_path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def local_helpers(path, source_root):
    """Retain statically imported local helper modules; unresolved fixtures stay visible at runtime."""
    pending, visited, helpers = [path], {path.resolve()}, []
    while pending:
        current = pending.pop()
        tree = ast.parse(current.read_bytes(), filename=str(current))
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.level:
                    raise ValueError("relative helper imports require a reviewed package invocation")
                modules.append(node.module)
        for module in modules:
            relative = Path(*module.split("."))
            for directory in (current.parent, path.parent):
                candidates = [directory / relative.with_suffix(".py"), directory / relative / "__init__.py"]
                for candidate in candidates:
                    candidate = candidate.resolve()
                    if candidate.is_file() and candidate not in visited:
                        if not candidate.is_relative_to(source_root / "tests/python"):
                            raise ValueError("helper import escapes the pinned tests/python tree")
                        visited.add(candidate)
                        helpers.append(source_row(candidate, source_root))
                        pending.append(candidate)
    return helpers


def build_plan(source_root):
    root = Path(source_root).resolve()
    for pin in CMAKE_SOURCES:
        source = root / pin["upstream_path"]
        if not source.is_file() or source_row(source, root) != pin:
            raise ValueError("source root does not contain the pinned original CMake files")
    text = (root / "tests/python/CMakeLists.txt").read_text()
    plan = {"schema": 1, "upstream_commit": UPSTREAM_SHA, "scope": "bounded CMake source invocation plan",
            "configured_ctest_inventory": False, "complete_test_denominator": False,
            "cmake_sources": CMAKE_SOURCES, "registrations": []}
    for index, command in enumerate(registrations(text)):
        entry = {"source_declaration_index": index, "line": command["line"], "registration": command["text"],
                 "context": command["context"], "state": "blocked", "reason": None}
        plan["registrations"].append(entry)
        try:
            if command["name"] != "add_blender_test" or command["context"]:
                raise ValueError("conditional, generated, function, error-allowing, or UI invocation requires configured CTest evidence")
            tokens = shlex.split(command["arguments"], comments=True)
            if len(tokens) < 3 or tokens[1] != "--python":
                raise ValueError("non-Python or additional Blender arguments need a reviewed driver")
            match = re.fullmatch(r"\$\{(?:CMAKE_CURRENT_LIST_DIR|TEST_PYTHON_DIR)\}/([A-Za-z0-9_./-]+\.py)", tokens[2])
            if not match or ".." in Path(match.group(1)).parts:
                raise ValueError("original script path is not a literal pinned tests/python path")
            arguments = tokens[3:]
            if arguments and (arguments[0] != "--" or any("$" in value or ";" in value for value in arguments[1:])):
                raise ValueError("fixture, output, or computed arguments require an explicit resource manifest")
            path = root / "tests/python" / match.group(1)
            entry["ctest_name"], entry["upstream_path"] = tokens[0], path.relative_to(root).as_posix()
            if not path.is_file():
                raise ValueError("original upstream script is missing")
            tree = ast.parse(path.read_bytes(), filename=str(path))
            if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                       isinstance(node.func.value, ast.Name) and node.func.value.id == "unittest" and
                       node.func.attr in ("main", "TextTestRunner") for node in ast.walk(tree)):
                raise ValueError("original driver is not a supported unittest entrypoint")
            row = source_row(path, root)
            row.update(support_files=local_helpers(path, root), fixture_files=[])
            proposal = {"schema": 2, "stage": "native-discovery", "cohort_id": tokens[0] + "-5.2",
                        "suite_kind": "unittest-main", "upstream": {"repository": "blender/blender", "commit": UPSTREAM_SHA},
                        "execution": {"entrypoint": "original __main__", "process_isolation": "one-upstream-script",
                                      "background": True, "blender_args": list(CTEST_BLENDER_ARGS),
                                      "script_args": arguments[1:] if arguments else [], "ctest_name": tokens[0],
                                      "cmake_sources": copy.deepcopy(CMAKE_SOURCES), "registration": command["text"]},
                        "suites": [row]}
            validate_manifest(proposal, allow_discovery=True)
            entry.update(state="pending_native_discovery", proposal=proposal)
        except (ValueError, OSError, SyntaxError) as error:
            entry["reason"] = str(error)
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-asset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 600:
        parser.error("timeout must be between 1 and 600")
    if not args.plan_only and not args.native_asset:
        parser.error("native discovery requires --native-asset")
    args.output.mkdir(parents=True, exist_ok=True)
    args.manifest_output.mkdir(parents=True, exist_ok=True)
    inventory_path = args.output / "discovery-inventory.json"
    if inventory_path.exists():
        parser.error("choose a new output directory; discovery evidence cannot be overwritten")
    plan = build_plan(args.source_root)
    def save():
        counts = {}
        for entry in plan["registrations"]:
            counts[entry["state"]] = counts.get(entry["state"], 0) + 1
        plan["declaration_counts"] = counts
        inventory_path.write_text(json.dumps(plan, indent=2) + "\n")
    save()
    if args.plan_only:
        print(json.dumps({"inventory": str(inventory_path), "counts": plan["declaration_counts"]}))
        return 0
    with native.verified_reference(args.native_asset) as reference:
        for entry in plan["registrations"]:
            if entry["state"] != "pending_native_discovery":
                continue
            name = entry["ctest_name"]
            directory = args.output / name
            directory.mkdir()
            proposal_path = directory / "discovery-proposal.json"
            proposal_path.write_text(json.dumps(entry.pop("proposal"), indent=2) + "\n")
            frozen = args.manifest_output / (name + ".json")
            value = json.loads(proposal_path.read_text())
            suite_args = []
            for row in [value["suites"][0], *value["suites"][0]["support_files"]]:
                source = args.source_root / row["upstream_path"]
                preserved = directory / "sources" / row["upstream_path"]
                preserved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, preserved)
                suite_args.extend(["--suite", str(preserved)])
            entry["native_exit_code"] = native.main([
                "--asset", str(args.native_asset), "--suite-manifest", str(proposal_path),
                "--suite-manifest-sha256", native.digest(proposal_path), "--discover", "--freeze-manifest", str(frozen),
                "--output", str(directory), "--timeout", str(args.timeout), *suite_args], reference=reference)
            report_path = directory / "native_reference.json"
            report = json.loads(report_path.read_text())
            entry["native_receipt"] = {"path": str(report_path), "sha256": native.digest(report_path), "bytes": report_path.stat().st_size}
            entry["native_status"] = report["status"]
            if frozen.is_file():
                entry.update(state="native_inventory_frozen", manifest={"path": str(frozen), "sha256": native.digest(frozen),
                             "bytes": frozen.stat().st_size}, expected_cases=json.loads(frozen.read_text())["expected_total_cases"])
            else:
                entry.update(state="native_discovery_blocked", reason=report.get("reason"))
            save()
            print(json.dumps({"ctest_name": name, "state": entry["state"], "native_status": entry["native_status"],
                              "expected_cases": entry.get("expected_cases"), "manifest": entry.get("manifest")}), flush=True)
    print(json.dumps({"inventory": str(inventory_path), "counts": plan["declaration_counts"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
