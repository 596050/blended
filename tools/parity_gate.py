#!/usr/bin/env python3
"""Gate a declared Blender parity contract using current, hash-bound evidence.

This validates coverage and evidence identity. It does not execute Blender,
independently judge comparison outputs, or establish that an author's declared
inventory covers every Blender feature. Test producers and inventory reviewers
remain responsible for those claims. Native and browser profiles are distinct.

The strict command exits 1 for an incomplete or non-passing contract, 2 for a
malformed input, and 0 only for a satisfied contract. --report-only exits 0 for
a valid report, including a blocked report, without changing its parity status.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


STATUSES = {
    "passed", "failed", "blocked", "unsupported", "skipped", "not_run",
    "missing_fixture", "crashed", "timed_out", "disabled", "stale", "missing",
}
KINDS = {"upstream", "feature", "workflow"}
CONTEXT_FIELDS = {
    "artifact_sha256": 64,
    "native_artifact_sha256": 64,
    "port_commit": 40,
    "build_config_sha256": 64,
    "fixture_manifest_sha256": 64,
    "comparison_policy_sha256": 64,
    "suite_manifest_sha256": 64,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _object(value: Any, label: str) -> dict:
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    return value


def _strings(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    _require(isinstance(value, list), f"{label} must be a list")
    for item in value:
        _text(item, label)
    _require(len(value) == len(set(value)), f"{label} contains duplicates")
    _require(not nonempty or bool(value), f"{label} must not be empty")
    return value


def _hash(value: Any, length: int, label: str) -> str:
    _require(isinstance(value, str) and bool(re.fullmatch(f"[0-9a-f]{{{length}}}", value)),
             f"{label} requires {length} lowercase hexadecimal characters")
    return value


def _schema(value: Any, label: str) -> dict:
    obj = _object(value, label)
    _require(type(obj.get("schema")) is int and obj["schema"] == 1, f"Unsupported {label} schema")
    return obj


def _target(value: Any, label: str) -> dict:
    obj = _object(value, label)
    _text(obj.get("repository"), f"{label}.repository")
    _hash(obj.get("commit"), 40, f"{label}.commit")
    return {"repository": obj["repository"], "commit": obj["commit"]}


def _context(value: Any, label: str) -> dict:
    obj = _object(value, label)
    for key, length in CONTEXT_FIELDS.items():
        _hash(obj.get(key), length, f"{label}.{key}")
    return {key: obj[key] for key in CONTEXT_FIELDS}


def inventory_sha256(inventory: dict) -> str:
    """Hash the parsed inventory's canonical UTF-8 JSON, including completeness.

    Canonical form uses sorted keys, compact separators, literal Unicode and no
    NaN/Infinity. Callers must compute this from the independently selected suite
    inventory when constructing the expected context.
    """
    encoded = json.dumps(inventory, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_manifest(manifest: dict) -> dict[str, dict]:
    """Validate the contract and return facets indexed by stable ID."""
    _schema(manifest, "manifest")
    _target(manifest.get("target"), "manifest.target")
    _strings(manifest.get("required_profiles"), "manifest.required_profiles", nonempty=True)
    entries = manifest.get("facets")
    _require(isinstance(entries, list) and bool(entries), "manifest.facets must not be empty")
    facets: dict[str, dict] = {}
    for entry in entries:
        facet = _object(entry, "facet")
        fid = _text(facet.get("id"), "facet.id")
        _text(facet.get("title"), f"{fid}.title")
        _require(fid not in facets, f"Duplicate facet: {fid}")
        _strings(facet.get("depends_on", []), f"{fid}.depends_on")
        required = _strings(facet.get("required_kinds", ["upstream", "workflow"]),
                            f"{fid}.required_kinds", nonempty=True)
        _require(set(required) <= KINDS, f"Unknown required kind in {fid}")
        _require("upstream" in required and bool({"feature", "workflow"} & set(required)),
                 f"{fid} must require upstream and feature/workflow obligations")
        facets[fid] = facet
    for fid, facet in facets.items():
        unknown = set(facet.get("depends_on", [])) - facets.keys()
        _require(not unknown, f"Unknown dependencies for {fid}: {sorted(unknown)}")
    visiting, done = set(), set()

    def visit(fid: str) -> None:
        _require(fid not in visiting, f"Dependency cycle at {fid}")
        if fid in done:
            return
        visiting.add(fid)
        for dependency in facets[fid].get("depends_on", []):
            visit(dependency)
        visiting.remove(fid)
        done.add(fid)

    for fid in facets:
        visit(fid)
    return facets


def validate_inventory(inventory: dict, manifest: dict, facets: dict[str, dict] | None = None) -> dict[str, dict]:
    """Validate the declared denominator; absence never means success."""
    facets = facets if facets is not None else validate_manifest(manifest)
    _schema(inventory, "inventory")
    _require(_target(inventory.get("target"), "inventory.target") ==
             _target(manifest["target"], "manifest.target"), "Inventory targets a different Blender revision")
    _require(type(inventory.get("enumeration_complete")) is bool,
             "inventory.enumeration_complete must be boolean")
    complete = _strings(inventory.get("facets_complete"), "inventory.facets_complete")
    _require(set(complete) <= facets.keys(), "Inventory completes unknown facets")
    entries = inventory.get("cases")
    _require(isinstance(entries, list), "inventory.cases must be a list")
    cases: dict[str, dict] = {}
    for entry in entries:
        case = _object(entry, "case")
        cid = _text(case.get("id"), "case.id")
        _require(cid not in cases, f"Duplicate case: {cid}")
        _require(case.get("facet") in facets, f"Case {cid} has unknown facet")
        _require(case.get("kind") in KINDS, f"Case {cid} has unknown kind")
        profiles = _strings(case.get("required_profiles"), f"{cid}.required_profiles", nonempty=True)
        _require(set(manifest["required_profiles"]) <= set(profiles),
                 f"Case {cid} drops a required profile")
        _require(set(profiles) <= set(manifest["required_profiles"]),
                 f"Case {cid} has an unknown gate profile")
        cases[cid] = case
    return cases


def _evidence_problem(evidence: Any, evidence_root: Path | None) -> str | None:
    if not isinstance(evidence, list) or not evidence:
        return "missing evidence"
    if evidence_root is None:
        return "missing evidence root"
    root = Path(evidence_root).resolve()
    if not root.is_dir():
        return "evidence root is not a directory"
    seen = set()
    for entry in evidence:
        if not isinstance(entry, dict):
            return "malformed evidence entry"
        name, digest = entry.get("path"), entry.get("sha256")
        if not isinstance(name, str) or not name or "\\" in name:
            return "invalid evidence path"
        relative = PurePosixPath(name)
        if relative.is_absolute() or any(p in {"..", "."} for p in name.split("/")):
            return "evidence path escapes or is not canonical"
        if name in seen:
            return "duplicate evidence path"
        seen.add(name)
        if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            return "invalid evidence hash"
        candidate = root
        for part in relative.parts:
            candidate /= part
            if candidate.is_symlink():
                return "symlink evidence is not allowed"
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            if not resolved.is_file():
                return "evidence is not a file"
            with resolved.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != digest:
                return "evidence hash mismatch"
        except (OSError, ValueError):
            return "evidence missing or outside root"
    return None


def evaluate(manifest: dict, inventory: dict, results: dict | None = None,
             expected_context: dict | None = None,
             evidence_root: Path | str | None = None) -> dict:
    """Return a strict status for the declared target/profile/facet contract.

    expected_context must come from the independently selected build and fixture
    manifests, not be copied from the result being judged. Coverage metadata is
    a reviewed input, not inferred from whichever tests happened to execute.
    """
    facets = validate_manifest(manifest)
    cases = validate_inventory(inventory, manifest, facets)
    target = _target(manifest["target"], "manifest.target")
    expected = _context(expected_context, "expected_context") if expected_context is not None else None
    records: dict[tuple[str, str], dict] = {}
    context_problem = "no execution results"
    if results is not None:
        _schema(results, "results")
        _require(_target(results.get("target"), "results.target") == target,
                 "Results target a different Blender revision")
        actual_context = _context(results.get("context"), "results.context")
        context_problem = ("missing independent expected context" if expected is None else
                           "execution context does not match expected build/fixtures/policy"
                           if actual_context != expected else None)
        if context_problem is None and expected["suite_manifest_sha256"] != inventory_sha256(inventory):
            context_problem = "inventory does not match expected suite manifest digest"
        entries = results.get("records")
        _require(isinstance(entries, list), "results.records must be a list")
        for entry in entries:
            record = _object(entry, "result record")
            cid = _text(record.get("case_id"), "record.case_id")
            profile = _text(record.get("profile"), "record.profile")
            _require(cid in cases, f"Result has unknown case: {cid}")
            _require(profile in cases[cid]["required_profiles"], f"Result {cid} has unexpected profile: {profile}")
            _require(record.get("status") in STATUSES, f"Result {cid} has unknown status")
            key = (cid, profile)
            _require(key not in records, f"Duplicate result: {cid} / {profile}")
            records[key] = record

    facet_reports: dict[str, dict] = {}
    counts: Counter = Counter()
    obligation_count = 0
    details = []
    for fid, facet in facets.items():
        own_cases = [case for case in cases.values() if case["facet"] == fid]
        own_counts: Counter = Counter()
        blockers = []
        if fid not in inventory["facets_complete"]:
            blockers.append("facet_inventory_incomplete")
        required_kinds = set(facet.get("required_kinds", ["upstream", "workflow"]))
        missing_kinds = required_kinds - {case["kind"] for case in own_cases}
        blockers.extend("missing_obligation_kind:" + kind for kind in sorted(missing_kinds))
        if not own_cases:
            blockers.append("empty_facet")
        for case in own_cases:
            for profile in case["required_profiles"]:
                obligation_count += 1
                record = records.get((case["id"], profile))
                status = record["status"] if record else "missing_result"
                reason = None
                if status == "passed":
                    reason = context_problem or _evidence_problem(record.get("evidence"),
                                                                  Path(evidence_root) if evidence_root is not None else None)
                    if reason:
                        status = "invalid_evidence"
                own_counts[status] += 1
                if status != "passed":
                    detail = {"case_id": case["id"], "profile": profile, "status": status}
                    if reason:
                        detail["reason"] = reason
                    details.append(detail)
        if any(status != "passed" and count for status, count in own_counts.items()):
            blockers.append("non_passing_obligations")
        counts.update(own_counts)
        facet_reports[fid] = {
            "id": fid, "title": facet["title"], "status": "blocked" if blockers else "passed",
            "case_count": len(own_cases), "obligation_count": sum(own_counts.values()),
            "counts": dict(sorted(own_counts.items())), "blockers": blockers,
        }

    assessed = set()

    def apply_dependencies(fid: str) -> None:
        if fid in assessed:
            return
        for dependency in facets[fid].get("depends_on", []):
            apply_dependencies(dependency)
            if facet_reports[dependency]["status"] != "passed":
                facet_reports[fid]["blockers"].append("dependency:" + dependency)
                facet_reports[fid]["status"] = "blocked"
        assessed.add(fid)

    for fid in facets:
        apply_dependencies(fid)
    coverage_complete = (inventory["enumeration_complete"] and
                         set(inventory["facets_complete"]) == facets.keys() and
                         all(not any(b == "empty_facet" or b.startswith("missing_obligation_kind:")
                                     for b in report["blockers"]) for report in facet_reports.values()))
    passed = bool(cases) and coverage_complete and all(f["status"] == "passed" for f in facet_reports.values())
    report = {
        "schema": 1, "target": target, "gate": "passed" if passed else "blocked",
        "full_feature_parity": passed,
        "claim_scope": "Declared target, profiles, and reviewed facet contract only; evidence semantics are the test producer's responsibility.",
        "enumeration_complete": inventory["enumeration_complete"],
        "coverage_complete": coverage_complete,
        "known_case_count": len(cases), "known_obligation_count": obligation_count,
        "passed_obligation_count": counts["passed"], "counts": dict(sorted(counts.items())),
        "facets": list(facet_reports.values()), "non_passing": details,
    }
    if coverage_complete and obligation_count:
        report["pass_rate_percent"] = round(100 * counts["passed"] / obligation_count, 3)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Reviewed facet and browser-profile contract")
    parser.add_argument("--inventory", type=Path, required=True, help="Reference-derived complete or explicitly incomplete inventory")
    parser.add_argument("--results", type=Path, help="Execution result records; omission means not run")
    parser.add_argument("--context", type=Path, help="Independent expected build, fixture and comparison-policy identity")
    parser.add_argument("--evidence-root", type=Path, help="Directory containing the hash-bound execution evidence")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-only", action="store_true", help="Write valid blocked reports successfully; never promotes their status")
    args = parser.parse_args(argv)

    def read(path: Path | None) -> dict | None:
        return json.loads(path.read_text()) if path is not None else None

    try:
        report = evaluate(read(args.manifest), read(args.inventory), read(args.results),
                          read(args.context), args.evidence_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    except (OSError, ValueError, TypeError) as exc:
        # Do not leave an earlier passing report at the requested output path.
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"schema": 1, "gate": "invalid",
                                              "full_feature_parity": False,
                                              "error": str(exc)}, indent=2) + "\n")
        except OSError:
            pass
        parser.exit(2, f"Invalid parity input: {exc}\n")
    print(json.dumps({key: report[key] for key in ("gate", "full_feature_parity", "known_case_count",
                                                  "known_obligation_count", "passed_obligation_count")}))
    return 0 if args.report_only or report["full_feature_parity"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
