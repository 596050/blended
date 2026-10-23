#!/usr/bin/env python3
"""Ingest CTest registrations and concrete GoogleTest runtime names.

This is a bounded inventory adapter, not a test runner or a completeness oracle.
CTest registrations are driver commands, not necessarily individual test cases.
All discovered entries remain not_run. Source/configuration reconciliation, asset
closure and successful unfiltered capture need independent evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any


def load_json_strict(text: str) -> Any:
    """Reject duplicate JSON keys and non-finite numbers before ingestion."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"Non-finite JSON number: {value}")
        return parsed

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(f"Expected finite JSON data: {exc}") from exc


def _clone(value: Any) -> Any:
    return load_json_strict(_canonical(value).decode("utf-8"))


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _identifier(kind: str, scope: dict, identity: Any) -> str:
    return f"{kind}:" + _hash(_canonical({"scope": scope, "identity": identity}))


def _hex(value: Any, length: int, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(f"[0-9a-f]{{{length}}}", value):
        raise ValueError(f"{name} must be a full lowercase {length}-character hexadecimal hash")
    return value


def _string(value: Any, name: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value) or "\0" in value:
        raise ValueError(f"{name} must be a {'possibly empty' if empty else 'nonempty'} string without NUL")
    return value


def _strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array of strings")
    for item in value:
        _string(item, name, empty=True)
    return value


def _scope(source_commit: str, build_config_sha256: str) -> dict:
    return {
        "source_commit": _hex(source_commit, 40, "source_commit"),
        "build_config_sha256": _hex(build_config_sha256, 64, "build_config_sha256"),
    }


def _provenance(provenance: dict) -> tuple[dict, list[str]]:
    if not isinstance(provenance, dict):
        raise ValueError("provenance must be an object")
    provenance = _clone(provenance)
    code = provenance.get("returncode")
    if code is not None and type(code) is not int:
        raise ValueError("provenance.returncode must be an integer")
    if "argv" in provenance:
        _strings(provenance["argv"], "provenance.argv")
    blockers = ["capture_scope_requires_attestation"]
    if code is None:
        blockers.append("capture_exit_status_unknown")
    elif code != 0:
        blockers.append("capture_failed")
    return provenance, blockers


def _index(value: Any, size: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < size:
        raise ValueError(f"Invalid backtrace {name} index: {value!r}")
    return value


def _backtrace_graph(document: dict) -> dict | None:
    graph = document.get("backtraceGraph")
    if graph is None:
        return None
    if not isinstance(graph, dict):
        raise ValueError("backtraceGraph must be an object")
    _strings(graph.get("commands"), "backtrace commands")
    _strings(graph.get("files"), "backtrace files")
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("backtrace nodes must be an array")
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("backtrace node must be an object")
        _index(node.get("file"), len(graph["files"]), "file")
        if "command" in node:
            _index(node["command"], len(graph["commands"]), "command")
        if "parent" in node:
            _index(node["parent"], len(nodes), "parent")
        if "line" in node and (type(node["line"]) is not int or node["line"] < 1):
            raise ValueError("backtrace line must be a positive integer")
    checked = set()
    for start in range(len(nodes)):
        current, active = start, set()
        while current is not None and current not in checked:
            if current in active:
                raise ValueError("Cycle in backtrace graph")
            active.add(current)
            current = nodes[current].get("parent")
        checked.update(active)
    return graph


def _backtrace(graph: dict | None, entry: dict) -> list[dict]:
    if "backtrace" not in entry:
        return []
    if graph is None:
        raise ValueError("Test backtrace has no backtraceGraph")
    index = _index(entry["backtrace"], len(graph["nodes"]), "test")
    frames = []
    while index is not None:
        node = graph["nodes"][index]
        frame = {"file": graph["files"][node["file"]]}
        if "line" in node:
            frame["line"] = node["line"]
        if "command" in node:
            frame["command"] = graph["commands"][node["command"]]
        frames.append(frame)
        index = node.get("parent")
    return frames


def _properties(entry: dict) -> tuple[list, dict]:
    values, by_name = entry.get("properties", []), {}
    if not isinstance(values, list):
        raise ValueError("CTest properties must be an array")
    for prop in values:
        if not isinstance(prop, dict) or "value" not in prop:
            raise ValueError("CTest property requires name and value")
        name = _string(prop.get("name"), "CTest property name")
        if name in by_name:
            raise ValueError(f"Duplicate CTest property: {name}")
        by_name[name] = prop["value"]
    return values, by_name


def inventory_ctest(document: dict | str, *, source_commit: str,
                    build_config_sha256: str, configuration: str | None,
                    provenance: dict) -> dict:
    """Preserve a configured JSON-v1 listing without upgrading it to leaf tests.

    IDs bind the source commit, declared build configuration hash, selected CTest
    configuration and exact registration name. Paths, ordering and backtrace line
    numbers do not define identity. Hash values are identifiers supplied by the
    caller; this parser does not attest that files/builds match those identifiers.
    """
    input_hash_encoding = "raw_utf8" if isinstance(document, str) else "canonical_json_utf8"
    raw = document.encode("utf-8") if isinstance(document, str) else _canonical(document)
    document = load_json_strict(raw.decode("utf-8"))
    if not isinstance(document, dict) or document.get("kind") != "ctestInfo":
        raise ValueError("Expected CTest JSON-v1 ctestInfo object")
    version = document.get("version")
    if not isinstance(version, dict) or type(version.get("major")) is not int or version["major"] != 1:
        raise ValueError("Unsupported CTest JSON major version")
    if type(version.get("minor")) is not int or version["minor"] < 0:
        raise ValueError("Invalid CTest JSON minor version")
    tests = document.get("tests")
    if not isinstance(tests, list):
        raise ValueError("CTest tests must be an array")
    scope = _scope(source_commit, build_config_sha256)
    if configuration is not None:
        _string(configuration, "configuration")
    scope["configuration"] = configuration
    provenance, blockers = _provenance(provenance)
    blockers += ["source_and_configuration_reconciliation_required", "runtime_expansion_required",
                 "fixture_closure_unverified"]
    graph = _backtrace_graph(document)
    registrations, names = [], set()
    for entry in tests:
        if not isinstance(entry, dict):
            raise ValueError("CTest test must be an object")
        name = _string(entry.get("name"), "CTest name")
        if name in names:
            raise ValueError(f"Duplicate CTest registration: {name}")
        names.add(name)
        config = entry.get("config")
        if "config" in entry:
            _string(config, "CTest configuration")
            if config != configuration:
                raise ValueError(f"CTest configuration {config!r} differs from capture configuration {configuration!r}")
        command = entry.get("command")
        if "command" in entry:
            _strings(command, "CTest command")
        command_status = "present_unvalidated" if command and command != ["NOT_AVAILABLE"] else "unavailable"
        properties, by_name = _properties(entry)
        diagnostics = []
        disabled = by_name.get("DISABLED", False)
        if type(disabled) is not bool:
            disabled = None
            diagnostics.append("unrecognized_disabled_property")

        def list_property(key):
            value = by_name.get(key, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                diagnostics.append(f"unrecognized_{key.lower()}_property")
                return None
            return value

        labels = list_property("LABELS")
        fixtures = {kind: list_property("FIXTURES_" + kind.upper()) for kind in ("setup", "required", "cleanup")}
        frames = _backtrace(graph, entry)
        unresolved = command_status == "unavailable" or bool(diagnostics)
        registrations.append({
            "id": _identifier("ctest", scope, name),
            "identity": name,
            "kind": "ctest_registration",
            "command": command,
            "command_status": command_status,
            "config": config,
            "configuration_status": "captured" if config is not None else "unspecified_in_listing",
            "properties": properties,
            "labels": labels,
            "fixtures": fixtures,
            "disabled": disabled,
            "backtrace": frames,
            "raw_registration": entry,
            "diagnostics": diagnostics,
            "execution": "not_run",
            "expansion_obligation": {
                "status": "unresolved" if unresolved else "required",
                "reason": "CTest commands require runtime leaf discovery and source reconciliation.",
                "children": [],
            },
        })
    if not registrations:
        blockers.append("empty_registration_listing")
    if any(case["expansion_obligation"]["status"] == "unresolved" for case in registrations):
        blockers.append("unresolved_registrations")
    return {
        "schema": 1,
        "inventory_kind": "ctest_registrations",
        "scope": scope,
        "provenance": provenance,
        "input_sha256": _hash(raw),
        "input_hash_encoding": input_hash_encoding,
        "ctest_version": version,
        "backtrace_graph": graph,
        "registration_enumeration_complete": False,
        "runtime_enumeration_complete": False,
        "fixture_completeness": "unknown",
        "registrations": registrations,
        "counts": {"registrations": len(registrations), "not_run": len(registrations)},
        "blockers": blockers,
    }


# The pinned Blender GoogleTest printer emits these two line forms. Any other
# nonblank line is retained as unresolved unless it is the gtest_main banner.
_SUITE = re.compile(r"([^\s#]+)\.(?:[ \t]+#[ \t]+TypeParam = (.*))?[ \t]*")
_CASE = re.compile(r"  ([^\s#]+)(?:[ \t]+#[ \t]+GetParam\(\) = (.*))?[ \t]*")


def _gtest_disabled(name: str) -> bool:
    # Exact semantics of DISABLED_*:*/DISABLED_*, applied to suite and test.
    return name.startswith("DISABLED_") or "/DISABLED_" in name


def gtest_source_case_id(identity: str, *, source_commit: str, source_path: str,
                         source_sha256: str, source_line: int) -> str:
    """Identify a runtime registration using independently verified source data.

    GoogleTest permits equal suite/test names from different C++ namespaces.
    Its original XML includes declaration file and line, while list output does
    not. A caller must verify the file against the pinned source, match the name
    multiplicities, and reject any remaining equal source-qualified identities.
    This function validates identity fields; it does not attest those bindings.
    Ordering, report timestamps and runtime artifact hashes are not identifiers
    of the original source case.
    """
    _string(identity, "GoogleTest case name")
    _hex(source_commit, 40, "source_commit")
    _hex(source_sha256, 64, "source_sha256")
    _string(source_path, "source_path")
    path = PurePosixPath(source_path)
    if path.is_absolute() or ".." in path.parts or "\\" in source_path or ":" in source_path:
        raise ValueError("source_path must be a confined repository-relative POSIX path")
    if path.as_posix() != source_path or source_path == ".":
        raise ValueError("source_path must be normalized and nonempty")
    if type(source_line) is not int or source_line < 1:
        raise ValueError("source_line must be a positive integer")
    return _identifier("gtest-source", {"source_commit": source_commit}, {
        "name": identity, "source_path": source_path, "source_sha256": source_sha256,
        "source_line": source_line,
    })


def inventory_gtest(text: str, *, source_commit: str, build_config_sha256: str,
                    artifact_sha256: str, registration_id: str,
                    provenance: dict) -> dict:
    """Ingest concrete --gtest_list_tests names, preserving every parameter suffix.

    GoogleTest applies its filter to listing. A parsed listing alone does not
    prove an unfiltered/successful capture, nor inclusion of other executables or
    configurations. Displayed type/value annotations can be truncated upstream
    and are not canonical parameter values. Execution IDs deliberately exclude
    the parent registration so overlapping CTest filters cannot double-count a
    single unambiguous case in the same artifact/build/source scope. Equal names
    are retained as unresolved observations, never silently deduplicated. Their
    capture-local IDs cannot become canonical case identities without separate
    source-location metadata from the runtime framework.
    """
    _string(text, "GoogleTest listing", empty=True)
    _string(registration_id, "registration_id")
    scope = _scope(source_commit, build_config_sha256)
    scope["artifact_sha256"] = _hex(artifact_sha256, 64, "artifact_sha256")
    provenance, blockers = _provenance(provenance)
    blockers += ["source_and_configuration_reconciliation_required", "fixture_closure_unverified"]
    cases, unparsed, preamble = [], [], []
    suites, name_groups, current = {}, {}, None
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith("Running main() from ") and not suites:
            preamble.append({"line": number, "text": line})
            continue
        suite_match = _SUITE.fullmatch(line)
        if suite_match:
            suite, type_parameter = suite_match.groups()
            if suite in suites:
                raise ValueError(f"Duplicate GoogleTest suite: {suite}")
            suites[suite] = {"type_parameter": type_parameter, "line": number, "count": 0}
            current = suite
            continue
        case_match = _CASE.fullmatch(line)
        if case_match and current is not None:
            name, value_parameter = case_match.groups()
            identity = f"{current}.{name}"
            suites[current]["count"] += 1
            case = {
                "id": _identifier("gtest", scope, {"suite": current, "name": name}),
                "identity": identity,
                "identity_status": "unique_name_in_listing",
                "kind": "gtest_runtime_case",
                "suite": current,
                "name": name,
                "type_parameter": suites[current]["type_parameter"],
                "value_parameter": value_parameter,
                "parameter_metadata_fidelity": "display_only_may_be_truncated",
                "disabled": _gtest_disabled(current) or _gtest_disabled(name),
                "registration_ids": [registration_id],
                "listing_line": number,
                "execution": "not_run",
                "expansion_obligation": {
                    "status": "expanded",
                    "reason": "Concrete runtime case identity; listing scope still requires attestation.",
                    "children": [],
                },
            }
            cases.append(case)
            name_groups.setdefault(identity, []).append(case)
            continue
        unparsed.append({"line": number, "text": line})
        # A malformed/new header must never assign following cases to an old suite.
        if not line.startswith("  "):
            current = None
    empty_suites = [name for name, suite in suites.items() if not suite["count"]]
    if unparsed:
        blockers.append("unparsed_listing_lines")
    if empty_suites:
        blockers.append("empty_suites")
    if not cases:
        blockers.append("empty_runtime_listing")
    input_sha256 = _hash(text.encode("utf-8"))
    duplicates = []
    for identity, group in name_groups.items():
        if len(group) < 2:
            continue
        for case in group:
            case.update(
                id=_identifier("gtest-observation", scope, {
                    "input_sha256": input_sha256, "listing_line": case["listing_line"],
                }),
                kind="gtest_runtime_observation",
                identity_status="ambiguous_duplicate_name",
                expansion_obligation={
                    "status": "unresolved",
                    "reason": "Equal runtime names require independently verified source-location metadata; listing order is not a case identity.",
                    "children": [],
                },
            )
        duplicates.append({"identity": identity, "listing_lines": [case["listing_line"] for case in group],
                           "observation_ids": [case["id"] for case in group]})
    if duplicates:
        blockers.append("ambiguous_duplicate_case_names")
    return {
        "schema": 1,
        "inventory_kind": "gtest_runtime_cases",
        "scope": scope,
        "registration_id": registration_id,
        "provenance": provenance,
        "input_sha256": input_sha256,
        "input_hash_encoding": "raw_utf8",
        "listing_parse_complete": not unparsed and not empty_suites,
        "runtime_identities_unambiguous": not duplicates,
        "runtime_enumeration_complete": False,
        "fixture_completeness": "unknown",
        "cases": cases,
        "preamble": preamble,
        "unparsed_lines": unparsed,
        "empty_suites": empty_suites,
        "duplicate_identities": duplicates,
        "counts": {"cases": len(cases), "disabled": sum(case["disabled"] for case in cases), "not_run": len(cases)},
        "blockers": blockers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("ctest", "gtest"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--build-config-sha256", required=True)
    parser.add_argument("--configuration")
    parser.add_argument("--artifact-sha256")
    parser.add_argument("--registration-id")
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must not overwrite the raw input listing")
    try:
        provenance = load_json_strict(args.provenance.read_text()) if args.provenance else {}
        common = {"source_commit": args.source_commit, "build_config_sha256": args.build_config_sha256,
                  "provenance": provenance}
        text = args.input.read_bytes().decode("utf-8")
        if args.kind == "ctest":
            result = inventory_ctest(text, configuration=args.configuration, **common)
        else:
            result = inventory_gtest(text, artifact_sha256=args.artifact_sha256,
                                     registration_id=args.registration_id, **common)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        print(json.dumps({"inventory_kind": result["inventory_kind"], "counts": result["counts"],
                          "runtime_enumeration_complete": False}))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
