#!/usr/bin/env python3
"""Reconcile a fixed native denominator with exact browser execution receipts.

This is a scoped test-conformance ledger, not a proof that Blender's upstream
tests cover every application feature. Required registrations are independent
contract inputs. Their concrete cases come from native discovery. Missing,
disabled, filtered and unexpanded obligations cannot disappear from the report.

Receipt producers remain a trust boundary: hashes establish identity, not that
a machine really executed a claimed operation. This consumer checks receipt
semantics and binding; original-driver validation belongs to the producer.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


CONTEXT_KEYS = ("artifact_sha256", "build_config_sha256", "adapter_sha256", "runtime_sha256")
REGISTRATION_KEYS = ("invocation_sha256", "fixture_manifest_sha256", "comparison_policy_sha256")
OUTCOMES = {
    "passed", "failed", "error", "skipped", "expected_failure", "unexpected_success",
    "blocked", "disabled", "unsupported", "not_run", "missing_fixture", "crashed", "timed_out",
}
REGISTRATION_STATUSES = {"expanded", "blocked", "disabled", "unsupported", "not_run", "missing_fixture"}
COVERAGE_KEYS = ("source_registration_reconciliation_complete", "configuration_matrix_complete",
                 "fixture_closure_complete")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a nonempty string")
    return value


def digest(value: Any, label: str, length: int = 64) -> str:
    require(isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None,
            f"{label} requires a lowercase {length}-character hash")
    return value


def strings(value: Any, label: str) -> list[str]:
    require(isinstance(value, list), f"{label} must be a list")
    for item in value:
        text(item, label)
    require(len(value) == len(set(value)), f"{label} contains duplicates")
    return value


def obj(value: Any, label: str) -> dict:
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def schema(value: Any, label: str) -> dict:
    value = obj(value, label)
    require(type(value.get("schema")) is int and value["schema"] == 1, f"unsupported {label} schema")
    return value


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _no_duplicate_members(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON member: {key}")
        result[key] = value
    return result


def load_json(raw: bytes | str) -> Any:
    return json.loads(raw, object_pairs_hook=_no_duplicate_members,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant: {value}")))


def _file(entry: Any, root: Path, *, read_payload: bool = False) -> Path | bytes:
    entry = obj(entry, "evidence reference")
    name = text(entry.get("path"), "evidence path")
    require("\\" not in name and not PurePosixPath(name).is_absolute() and
            all(part not in {"", ".", ".."} for part in name.split("/")), "noncanonical evidence path")
    expected = digest(entry.get("sha256"), "evidence sha256")
    candidate = root
    for part in name.split("/"):
        candidate /= part
        require(not candidate.is_symlink(), "symlink evidence is not allowed")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        require(resolved.is_file(), "evidence must be a regular file")
        with resolved.open("rb") as stream:
            if read_payload:
                payload = stream.read()
                actual = hashlib.sha256(payload).hexdigest()
            else:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
    except (OSError, ValueError) as exc:
        raise ValueError(f"missing or unsafe evidence: {name}") from exc
    require(actual == expected, f"evidence hash mismatch: {name}")
    return payload if read_payload else resolved


def _receipt(entry: Any, root: Path, kind: str) -> dict:
    # Interpret exactly the bytes whose digest was verified, without a second
    # open that could read a replacement file after the integrity check.
    value = schema(load_json(_file(entry, root, read_payload=True)), kind)
    require(value.get("kind") == kind, f"expected receipt kind {kind}")
    raw = value.get("raw_evidence")
    require(isinstance(raw, list) and bool(raw), "receipt must bind raw evidence")
    names = []
    for item in raw:
        _file(item, root)
        names.append(item["path"])
    require(len(names) == len(set(names)), "duplicate raw evidence path")
    return value


def _process(value: Any) -> dict:
    value = obj(value, "process")
    for field in ("started", "completed", "timed_out", "crashed"):
        require(type(value.get(field)) is bool, f"process.{field} must be boolean")
    require(value.get("exit_code") is None or type(value["exit_code"]) is int,
            "process.exit_code must be an integer or null")
    require(not value["completed"] or value["started"], "completed process was never started")
    return value


def _normal(process: dict) -> bool:
    return (process["started"] and process["completed"] and not process["timed_out"]
            and not process["crashed"] and process["exit_code"] is not None
            and process["exit_code"] >= 0)


def _filtered_selection(value: Any, label: str) -> bool:
    """Check extra narrowing beyond the original hash-bound invocation.

    An upstream CTest registration's own suite filter belongs to its invocation
    identity. This metadata records additional runner filters or sharding.
    """
    selection = obj(value, label + " selection")
    filters = strings(selection.get("filters"), label + " filters")
    require("shard" in selection, label + " must declare shard state")
    return bool(filters) or selection["shard"] is not None


def _contract(value: dict) -> tuple[dict, dict, str, list[str]]:
    schema(value, "contract")
    target = obj(value.get("target"), "contract.target")
    text(target.get("repository"), "target.repository")
    digest(target.get("commit"), "target.commit", 40)
    text(value.get("scope"), "contract.scope")
    configurations = value.get("configurations")
    require(isinstance(configurations, list) and bool(configurations), "required configurations are missing")
    required, config_ids = {}, []
    for configuration in configurations:
        configuration = obj(configuration, "configuration")
        cid = text(configuration.get("id"), "configuration.id")
        require(cid not in config_ids, "duplicate configuration")
        config_ids.append(cid)
        entries = configuration.get("registrations")
        require(isinstance(entries, list), "configuration.registrations must be a list")
        for entry in entries:
            entry = obj(entry, "required registration")
            rid = text(entry.get("id"), "registration.id")
            key = (cid, rid)
            require(key not in required, "duplicate required registration")
            for field in REGISTRATION_KEYS:
                digest(entry.get(field), field)
            required[key] = entry
    profiles = {}
    entries = value.get("profiles")
    require(isinstance(entries, list) and bool(entries), "required profiles are missing")
    for profile in entries:
        profile = obj(profile, "profile")
        pid = text(profile.get("id"), "profile.id")
        require(pid not in profiles, "duplicate profile")
        require(profile.get("role") in {"reference", "candidate"}, "unknown profile role")
        kind = "native" if profile["role"] == "reference" else "browser"
        require(profile.get("runtime_kind") == kind, "profile runtime kind does not match its role")
        contexts = obj(profile.get("contexts"), "profile.contexts")
        require(set(contexts) == set(config_ids), "profile must bind every required configuration")
        for context in contexts.values():
            obj(context, "profile context")
            for field in CONTEXT_KEYS:
                digest(context.get(field), field)
        profiles[pid] = profile
    references = [p for p, entry in profiles.items() if entry["role"] == "reference"]
    browsers = [p for p, entry in profiles.items() if entry["role"] == "candidate"]
    require(len(references) == 1 and bool(browsers), "exactly one native reference and at least one browser are required")
    coverage = obj(value.get("coverage"), "coverage")
    for field in COVERAGE_KEYS:
        require(type(coverage.get(field)) is bool, f"coverage.{field} must be boolean")
    strings(coverage.get("blockers"), "coverage.blockers")
    return required, profiles, references[0], browsers


def _bound(receipt: dict, contract: dict, profile: dict, config: str, registration: dict) -> None:
    require(receipt.get("target") == contract["target"], "receipt targets another upstream revision")
    require(receipt.get("contract_sha256") == canonical_sha256(contract), "receipt contract mismatch")
    require(receipt.get("profile") == profile["id"], "receipt profile mismatch")
    require(receipt.get("runtime_kind") == profile["runtime_kind"], "receipt runtime kind mismatch")
    require(receipt.get("context") == profile["contexts"][config], "receipt execution context mismatch")
    require(receipt.get("configuration") == config, "receipt configuration mismatch")
    require(receipt.get("registration_id") == registration["id"], "receipt registration mismatch")
    for field in REGISTRATION_KEYS:
        require(receipt.get(field) == registration[field], f"receipt {field} mismatch")
    _process(receipt.get("process"))


def _case(value: Any, policy: str) -> dict:
    value = obj(value, "case outcome")
    text(value.get("id"), "case.id")
    require(value.get("outcome") in OUTCOMES, "unknown case outcome")
    for field in ("started", "completed"):
        require(type(value.get(field)) is bool, f"case.{field} must be boolean")
    require(not value["completed"] or value["started"], "completed case was never started")
    comparison = obj(value.get("comparison"), "case.comparison")
    require(comparison.get("status") in {"passed", "failed", "not_applicable", "not_run"}, "unknown comparison status")
    require(comparison.get("policy_sha256") == policy, "case comparison policy mismatch")
    if value.get("detail_sha256") is not None:
        digest(value["detail_sha256"], "case detail hash")
    subtests = value.get("subtests")
    require(isinstance(subtests, list), "case.subtests must be a list")
    ids = []
    for event in subtests:
        event = obj(event, "subtest")
        ids.append(text(event.get("id"), "subtest.id"))
        require(event.get("outcome") in OUTCOMES, "unknown subtest outcome")
        if event.get("detail_sha256") is not None:
            digest(event["detail_sha256"], "subtest detail hash")
    require(len(ids) == len(set(ids)), "duplicate subtest identity")
    return value


def _subtests(value: dict) -> list[tuple]:
    return sorted((row["id"], row["outcome"], row.get("detail_sha256")) for row in value["subtests"])


def _agreement(native: dict | None, browser: dict | None, nr: dict | None, br: dict | None) -> bool:
    if not native or not browser or not nr or not br or not _normal(nr["process"]) or not _normal(br["process"]):
        return False
    if (nr["selection_blockers"] or br["selection_blockers"]
            or nr["validation_blockers"] or br["validation_blockers"]):
        return False
    if not all(row["started"] and row["completed"] for row in (native, browser)):
        return False
    if (native["outcome"], native["comparison"]["status"], _subtests(native)) != (
            browser["outcome"], browser["comparison"]["status"], _subtests(browser)):
        return False
    # Matching labels alone do not establish that non-passing subtests failed
    # for the same reason. Their normalized details use the bound policy.
    if any(event["outcome"] != "passed" and not event.get("detail_sha256")
           for event in native["subtests"]):
        return False
    if native["outcome"] != "passed":
        return bool(native.get("detail_sha256")) and native.get("detail_sha256") == browser.get("detail_sha256")
    return True


def assess(contract: dict, inventory: dict, executions: dict | None, evidence_root: Path | str) -> dict:
    required, profiles, reference, browsers = _contract(contract)
    root = Path(evidence_root)
    require(not root.is_symlink() and root.is_dir(), "evidence root must be a directory, not a symlink")
    root = root.resolve()
    schema(inventory, "inventory")
    require(inventory.get("target") == contract["target"], "inventory targets another upstream revision")
    require(inventory.get("contract_sha256") == canonical_sha256(contract), "inventory contract mismatch")
    entries = inventory.get("registrations")
    require(isinstance(entries, list), "inventory.registrations must be a list")
    registrations, registration_reports = {}, []
    for row in entries:
        row = obj(row, "inventory registration")
        key = (row.get("configuration"), row.get("id"))
        require(key in required, "unknown inventory registration")
        require(key not in registrations, "duplicate inventory registration")
        require(row.get("status") in REGISTRATION_STATUSES, "unknown registration status")
        strings(row.get("case_ids"), "registration case IDs")
        disabled = strings(row.get("disabled_case_ids", []), "disabled case IDs")
        require(set(disabled) <= set(row["case_ids"]), "unknown disabled case")
        blockers = []
        if row["status"] != "expanded":
            blockers.append(row["status"])
        else:
            receipt = _receipt(row.get("discovery"), root, "blender-test-discovery")
            _bound(receipt, contract, profiles[reference], key[0], required[key])
            require(set(strings(receipt.get("case_ids"), "discovered case IDs")) == set(row["case_ids"]),
                    "native discovery case IDs differ from the fixed inventory")
            require(set(strings(receipt.get("disabled_case_ids"), "discovered disabled IDs")) == set(disabled),
                    "native disabled case IDs differ from the fixed inventory")
            if _filtered_selection(receipt.get("selection"), "discovery"):
                blockers.append("filtered_discovery")
            if not _normal(receipt["process"]) or receipt["process"]["exit_code"] != 0:
                blockers.append("incomplete_native_discovery")
            if not row["case_ids"]:
                blockers.append("empty_expansion")
        registrations[key] = {**row, "blockers": blockers}
    for key in required:
        row = registrations.get(key)
        registration_reports.append({"configuration": key[0], "registration_id": key[1],
                                     "case_count": len(row["case_ids"]) if row else 0,
                                     "blockers": row["blockers"] if row else ["missing_registration"]})

    runs = {}
    if executions is not None:
        schema(executions, "execution index")
        require(executions.get("target") == contract["target"], "execution index targets another upstream revision")
        require(executions.get("contract_sha256") == canonical_sha256(contract), "execution index contract mismatch")
        require(executions.get("inventory_sha256") == canonical_sha256(inventory), "execution index inventory mismatch")
        entries = executions.get("runs")
        require(isinstance(entries, list), "execution runs must be a list")
        for entry in entries:
            entry = obj(entry, "execution run")
            key = (entry.get("configuration"), entry.get("registration_id"))
            pid = entry.get("profile")
            require(key in required and key in registrations, "run has an unknown registration")
            require(pid in profiles, "run has an unknown profile")
            rkey = (*key, pid)
            require(rkey not in runs, "duplicate run for a registration/profile")
            run_id = text(entry.get("run_id"), "run_id")
            receipt = _receipt(entry.get("receipt"), root, "blender-test-execution")
            _bound(receipt, contract, profiles[pid], key[0], required[key])
            require(receipt.get("run_id") == run_id, "receipt run identity mismatch")
            require(receipt.get("inventory_sha256") == canonical_sha256(inventory), "receipt inventory mismatch")
            selection_blockers = (["filtered_execution"]
                                  if _filtered_selection(receipt.get("selection"), "execution") else [])
            validation_blockers = strings(receipt.get("validation_blockers", []), "execution validation blockers")
            rows = receipt.get("cases")
            require(isinstance(rows, list), "execution cases must be a list")
            outcomes = {}
            for outcome in rows:
                outcome = _case(outcome, required[key]["comparison_policy_sha256"])
                cid = outcome["id"]
                require(cid in registrations[key]["case_ids"], f"execution contains unknown case: {cid}")
                require(cid not in outcomes, f"duplicate case outcome: {cid}")
                outcomes[cid] = outcome
            runs[rkey] = {**receipt, "outcomes": outcomes, "selection_blockers": selection_blockers,
                         "validation_blockers": validation_blockers}

    pairs = []
    grouped = defaultdict(list)
    case_ids, case_configurations = set(), set()
    for key, registration in registrations.items():
        native_run = runs.get((*key, reference))
        for cid in registration["case_ids"]:
            case_ids.add(cid)
            case_configurations.add((key[0], cid))
            native = native_run["outcomes"].get(cid) if native_run else None
            for browser_profile in browsers:
                browser_run = runs.get((*key, browser_profile))
                browser = browser_run["outcomes"].get(cid) if browser_run else None
                blockers = list(registration["blockers"])
                if cid in registration.get("disabled_case_ids", []):
                    blockers.append("disabled")
                for label, run, outcome in (("native", native_run, native), ("browser", browser_run, browser)):
                    if not run:
                        blockers.append(label + "_missing_run")
                    else:
                        blockers.extend(label + "_" + reason for reason in run["selection_blockers"])
                        blockers.extend(label + "_validation:" + reason for reason in run["validation_blockers"])
                        if not _normal(run["process"]) or run["process"]["exit_code"] != 0:
                            blockers.append("timed_out" if run["process"]["timed_out"] else
                                            "crashed" if run["process"]["crashed"] else label + "_process_incomplete_or_failed")
                    if not outcome:
                        blockers.append(label + "_missing_case")
                    elif not (outcome["started"] and outcome["completed"] and outcome["outcome"] == "passed"
                              and outcome["comparison"]["status"] == "passed"
                              and all(event["outcome"] == "passed" for event in outcome["subtests"])):
                        blockers.append(label + "_nonpassing_case")
                discovery_qualified = (not registration["blockers"]
                                       and cid not in registration.get("disabled_case_ids", []))
                agreement = discovery_qualified and _agreement(native, browser, native_run, browser_run)
                if not agreement:
                    blockers.append("outcome_or_subtest_disagreement")
                pair = {"configuration": key[0], "registration_id": key[1], "case_id": cid,
                        "criteria": {field: required[key][field] for field in REGISTRATION_KEYS},
                        "native_profile": reference, "browser_profile": browser_profile,
                        "native_outcome": native["outcome"] if native else "missing",
                        "browser_outcome": browser["outcome"] if browser else "missing",
                        "outcome_agreement": agreement, "successful_execution": not blockers,
                        "blockers": sorted(set(blockers))}
                pairs.append(pair)
                # A repeated registration of the same case is only equivalent
                # when its invocation, inputs and acceptance criteria match.
                criteria = tuple(required[key][field] for field in REGISTRATION_KEYS)
                grouped[(key[0], cid, browser_profile, *criteria)].append(pair)

    unresolved = sum(bool(row["blockers"]) for row in registration_reports)
    closed = bool(required) and unresolved == 0
    successes = sum(all(row["successful_execution"] for row in rows) for rows in grouped.values())
    agreements = sum(all(row["outcome_agreement"] for row in rows) for rows in grouped.values())
    scoped_pass = closed and bool(grouped) and successes == len(grouped)
    return {
        "schema": 1, "target": contract["target"], "scope": contract["scope"],
        "contract_sha256": canonical_sha256(contract), "inventory_sha256": canonical_sha256(inventory),
        "gate": "passed" if scoped_pass else "blocked", "declared_scope_test_parity": scoped_pass,
        "scope_enumeration_complete": closed,
        "required_registration_count": len(required), "unresolved_registration_count": unresolved,
        "known_case_count": len(case_ids), "known_case_configuration_count": len(case_configurations),
        "paired_obligation_count": len(grouped), "registration_execution_pair_count": len(pairs),
        "obligation_identity_fields": ["configuration", "case_id", "browser_profile", *REGISTRATION_KEYS],
        "successful_execution_pair_count": successes, "outcome_agreement_count": agreements,
        "all_upstream_test_parity": False, "full_feature_parity": False,
        "coverage_review": contract["coverage"],
        "claim_limit": "Only the independently supplied registrations and native-expanded cases are assessed. "
                       "Outcome agreement requires complete, unfiltered discovery and executions. "
                       "Coverage review flags do not certify an exhaustive upstream universe or application feature parity.",
        "registrations": registration_reports, "pairs": pairs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--executions", type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        read = lambda path: load_json(path.read_bytes())
        report = assess(read(args.contract), read(args.inventory),
                        read(args.executions) if args.executions else None, args.evidence_root)
        status = 0 if args.report_only or report["declared_scope_test_parity"] else 1
    except (OSError, ValueError, TypeError) as exc:
        report = {"schema": 1, "gate": "invalid", "declared_scope_test_parity": False,
                  "all_upstream_test_parity": False, "full_feature_parity": False, "error": str(exc)}
        status = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {"pairs", "registrations", "coverage_review"}}))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
