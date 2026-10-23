#!/usr/bin/env python3
"""Gate a declared Blender test contract using typed, hash-bound receipts.

Each pass requires a receipt for that exact case, profile, target, execution run
and independently selected context. Attachments are integrity-checked supporting
files, not a substitute for the receipt's successful outcome and completion.
This does not execute Blender, re-run assertions or image comparators, establish
the trustworthiness of a receipt producer, or prove inventory completeness. A
satisfied declared contract never establishes full Blender feature parity.

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
RECEIPT_TYPE = "blender-case-execution"
MAX_RECEIPT_BYTES = 1_048_576


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


def _bound_file(entry: Any, evidence_root: Path | None, *, read_limit: int | None = None) -> bytes | None:
    """Verify one confined file; hash the same bytes used to interpret receipts."""
    _require(evidence_root is not None, "missing evidence root")
    root = Path(evidence_root).resolve()
    _require(root.is_dir(), "evidence root is not a directory")
    _require(isinstance(entry, dict), "missing or malformed evidence reference")
    name, digest = entry.get("path"), entry.get("sha256")
    _require(isinstance(name, str) and bool(name) and "\\" not in name, "invalid evidence path")
    relative = PurePosixPath(name)
    _require(not relative.is_absolute() and not any(p in {"..", ".", ""} for p in name.split("/"))
             and relative.as_posix() == name, "evidence path escapes or is not canonical")
    _hash(digest, 64, "evidence.sha256")
    candidate = root
    for part in relative.parts:
        candidate /= part
        _require(not candidate.is_symlink(), "symlink evidence is not allowed")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        _require(resolved.is_file(), "evidence is not a file")
        with resolved.open("rb") as stream:
            if read_limit is None:
                payload = None
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            else:
                payload = stream.read(read_limit + 1)
                _require(len(payload) <= read_limit, "execution receipt exceeds its byte limit")
                actual = hashlib.sha256(payload).hexdigest()
    except OSError as exc:
        raise ValueError("evidence missing or unreadable") from exc
    _require(actual == digest, "evidence hash mismatch")
    return payload


def _receipt_json(payload: bytes) -> dict:
    """Reject ambiguous duplicate fields and non-JSON numeric values."""
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            _require(key not in obj, "execution receipt contains duplicate JSON field: " + key)
            obj[key] = value
        return obj

    def reject_constant(value):
        raise ValueError("execution receipt contains invalid JSON value: " + value)

    return _schema(json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object,
                              parse_constant=reject_constant), "execution receipt")


def _receipt_problem(record: dict, target: dict, context: dict, run_id: Any,
                     evidence_root: Path | None) -> str | None:
    """Interpret a case receipt; arbitrary logs cannot prove a passing case."""
    try:
        _text(run_id, "results.run_id")
        reference = record.get("receipt")
        _require(isinstance(reference, dict), "missing typed execution receipt")
        receipt = _receipt_json(_bound_file(reference, evidence_root, read_limit=MAX_RECEIPT_BYTES))
        _require(receipt.get("type") == RECEIPT_TYPE, "unsupported execution receipt type")
        for key, expected in (("case_id", record["case_id"]), ("profile", record["profile"]),
                              ("run_id", run_id)):
            _require(receipt.get(key) == expected, "execution receipt " + key + " does not match result")
        _require(_target(receipt.get("target"), "receipt.target") == target,
                 "execution receipt targets a different Blender revision")
        _require(_context(receipt.get("context"), "receipt.context") == context,
                 "execution receipt context differs from independently selected context")
        _require(receipt.get("outcome") == "passed", "execution receipt does not report a passed outcome")
        execution = _object(receipt.get("execution"), "receipt.execution")
        _require(execution.get("started") is True and execution.get("completed") is True,
                 "execution receipt does not record a started and completed execution")
        _require(type(execution.get("exit_code")) is int and execution["exit_code"] == 0,
                 "execution receipt does not record successful process exit")
        _require(execution.get("timed_out") is False and execution.get("crashed") is False,
                 "execution receipt does not exclude timeout and crash")
        comparison = _object(receipt.get("comparison"), "receipt.comparison")
        _require(comparison.get("status") == "passed", "execution receipt comparison did not pass")
        _require(comparison.get("policy_sha256") == context["comparison_policy_sha256"],
                 "execution receipt comparison policy differs from independently selected policy")
        attachments = record.get("attachments", [])
        _require(isinstance(attachments, list), "attachments must be a list")
        seen = {reference["path"]}
        for attachment in attachments:
            _require(isinstance(attachment, dict), "malformed attachment reference")
            name = _text(attachment.get("path"), "attachment.path")
            _require(name not in seen, "duplicate receipt or attachment path")
            seen.add(name)
            _bound_file(attachment, evidence_root)
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        return str(exc)
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
    run_id = None
    context_problem = "no execution results"
    if results is not None:
        _schema(results, "results")
        _require(_target(results.get("target"), "results.target") == target,
                 "Results target a different Blender revision")
        actual_context = _context(results.get("context"), "results.context")
        run_id = results.get("run_id")
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
                    reason = context_problem or _receipt_problem(
                        record, target, expected, run_id,
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
        "declared_contract_satisfied": passed,
        "full_feature_parity": False,
        "full_feature_parity_reason": "No independently validated full feature acceptance mechanism is present.",
        "claim_scope": "Declared target, profiles, inventory and typed execution receipts only. Receipt producer trust, exhaustive enumeration and full feature acceptance are not established by this gate.",
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
                                              "declared_contract_satisfied": False,
                                              "full_feature_parity": False,
                                              "error": str(exc)}, indent=2) + "\n")
        except OSError:
            pass
        parser.exit(2, f"Invalid parity input: {exc}\n")
    print(json.dumps({key: report[key] for key in ("gate", "declared_contract_satisfied", "full_feature_parity", "known_case_count",
                                                  "known_obligation_count", "passed_obligation_count")}))
    return 0 if args.report_only or report["declared_contract_satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
