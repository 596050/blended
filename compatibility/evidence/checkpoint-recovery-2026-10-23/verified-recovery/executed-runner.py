#!/usr/bin/env python3
"""Record a prospective recovery audit from a public base and a delta bundle."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def digest(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    args = parser.parse_args()
    source, checkout, bundle, audit = (path.resolve() for path in
        (args.source_repo, args.checkout, args.bundle, args.audit))
    base = "b2fa1b96db519d86adb7809ad5f881c26124ac70"
    head = "0d09949783ffd696edc575359a62a662580a8964"
    origin = "https://github.com/596050/blended.git"
    assert not checkout.exists(), "independent checkout must not already exist"
    audit.mkdir(parents=True, exist_ok=True)
    assert not (audit / "audit.json").exists(), "audit output already exists"
    logs = audit / "commands"
    logs.mkdir(exist_ok=False)
    snapshot = audit / "executed-runner.py"
    snapshot.write_bytes(Path(__file__).resolve().read_bytes())
    record = {
        "schema": 1, "kind": "git-bundle-recovery-audit", "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source_repository": str(source), "independent_checkout": str(checkout),
        "expected_base": base, "expected_head": head, "public_origin": origin,
        "base_origin": "Fetched the exact public base commit from the public HTTPS remote into an empty Git repository; no clone, local object alternate, or fetch from the working repository was used.",
        "bundle": digest(bundle), "audit_runner": digest(Path(__file__).resolve()),
        "executed_runner_snapshot": {**digest(snapshot), "path": snapshot.relative_to(audit).as_posix()},
        "commands": [], "verification": {},
        "claim_limit": "This verifies bundle recovery and replay of committed, bounded test evidence. It is not a new Blender execution, full upstream test pass, or application feature parity proof.",
    }

    def save() -> None:
        (audit / "audit.json").write_text(json.dumps(record, indent=2) + "\n")

    def run(label: str, command: list[str], cwd: Path, expected=0, timeout=120) -> subprocess.CompletedProcess:
        entry = {"label": label, "command": command, "cwd": str(cwd),
                 "started_at": datetime.now(timezone.utc).isoformat()}
        record["commands"].append(entry)
        save()
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout,
                                    env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            entry["returncode"] = result.returncode
            entry["timed_out"] = False
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired as exc:
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
            entry.update(returncode=None, timed_out=True)
            result = None
        entry["completed_at"] = datetime.now(timezone.utc).isoformat()
        entry["duration_seconds"] = round(time.monotonic() - started, 6)
        prefix = f"{len(record['commands']):02d}-{label}"
        for stream, payload in (("stdout", stdout), ("stderr", stderr)):
            path = logs / (prefix + "." + stream + ".log")
            path.write_bytes(payload)
            entry[stream] = {**digest(path), "path": path.relative_to(audit).as_posix()}
        allowed = {expected} if isinstance(expected, int) else set(expected)
        entry["expected_returncodes"] = sorted(allowed)
        entry["expected_result_observed"] = result is not None and result.returncode in allowed
        save()
        print(json.dumps({"label": label, "returncode": entry["returncode"],
                          "expected_result_observed": entry["expected_result_observed"]}), flush=True)
        assert entry["expected_result_observed"], f"unexpected result in {label}: {stderr.decode(errors='replace')}"
        return result

    try:
        # Record prerequisites before receiving any commit from the bundle.
        with bundle.open("rb") as stream:
            header = []
            while True:
                line = stream.readline()
                if not line or line == b"\n":
                    break
                header.append(line.decode("utf-8").rstrip("\n"))
        record["bundle_header"] = header
        prerequisites = [line[1:].split(" ", 1)[0] for line in header if line.startswith("-")]
        assert prerequisites == [base], "bundle prerequisite differs from the specified public base"
        save()
        source_identity = run("source-identity", ["git", "rev-parse", "HEAD", "HEAD^{tree}"], source)
        source_head, source_tree = source_identity.stdout.decode().splitlines()
        assert source_head == head, "working repository HEAD differs from expected checkpoint"
        source_commit = run("source-commit", ["git", "cat-file", "commit", head], source)
        heads = run("bundle-heads", ["git", "bundle", "list-heads", str(bundle)], source)
        assert heads.stdout.decode().splitlines() == [head + " HEAD"]
        checkout.mkdir()
        run("init-empty", ["git", "init", "--initial-branch=recovery"], checkout)
        run("bundle-prerequisite-absent", ["git", "bundle", "verify", str(bundle)], checkout, expected=1)
        run("add-public-origin", ["git", "remote", "add", "origin", origin], checkout)
        run("fetch-public-base", ["git", "fetch", "--no-tags", "--no-progress", "origin", base], checkout)
        run("checkout-public-base", ["git", "checkout", "--detach", base], checkout)
        base_identity = run("base-identity", ["git", "rev-parse", "HEAD", "HEAD^{tree}"], checkout)
        assert base_identity.stdout.decode().splitlines()[0] == base
        run("target-absent-before-bundle", ["git", "cat-file", "-e", head + "^{commit}"], checkout, expected=128)
        run("verify-bundle-prerequisite", ["git", "bundle", "verify", str(bundle)], checkout)
        run("fetch-bundle", ["git", "fetch", "--no-tags", str(bundle), "HEAD:refs/heads/recovered-checkpoint"], checkout)
        run("checkout-recovered", ["git", "checkout", "recovered-checkpoint"], checkout)
        recovered = run("recovered-identity", ["git", "rev-parse", "HEAD", "HEAD^{tree}"], checkout)
        recovered_head, recovered_tree = recovered.stdout.decode().splitlines()
        assert (recovered_head, recovered_tree) == (source_head, source_tree)
        recovered_commit = run("recovered-commit", ["git", "cat-file", "commit", head], checkout)
        assert recovered_commit.stdout == source_commit.stdout
        parents = run("recovered-parent", ["git", "rev-list", "--parents", "-n", "1", head], checkout)
        assert parents.stdout.decode().strip() == head + " " + base
        run("object-integrity", ["git", "fsck", "--full", "--no-reflogs"], checkout)
        run("working-tree-diff", ["git", "diff", "--exit-code", "HEAD", "--"], checkout)
        clean = run("working-tree-status", ["git", "status", "--porcelain", "--untracked-files=all"], checkout)
        assert not clean.stdout
        normalized = Path("compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2")
        replay = audit / "replayed-ledger-report.json"
        run("strict-ledger-replay", [sys.executable, str(normalized / "normalizer/test_parity_ledger.py"),
            "--contract", str(normalized / "contract.json"),
            "--inventory", str(normalized / "inventory.json"),
            "--executions", str(normalized / "executions.json"),
            "--evidence-root", str(normalized), "--output", str(replay)], checkout, expected=1)
        expected_report = checkout / normalized / "report.json"
        report = json.loads(replay.read_bytes())
        original = json.loads(expected_report.read_bytes())
        supplemental = {"unexpected_browser_subtest_count", "observation_count_limit",
                        "observation_totals", "missing_browser_subtest_count"}
        assert set(original) - set(report) == supplemental, "unexpected report schema difference"
        assert all(key in original and original[key] == value for key, value in report.items()), \
            "replayed assessment differs from the committed report"
        expected_fields = {
            "gate": "blocked", "paired_obligation_count": 829,
            "successful_execution_pair_count": 512, "outcome_agreement_count": 597,
            "required_registration_count": 132, "unresolved_registration_count": 101,
            "declared_scope_test_parity": False, "all_upstream_test_parity": False,
            "full_feature_parity": False,
        }
        assert all(report[key] == value for key, value in expected_fields.items())
        final_clean = run("final-working-tree-status", ["git", "status", "--porcelain", "--untracked-files=all"], checkout)
        assert not final_clean.stdout
        record["verification"] = {
            "public_base_fetched_directly": True,
            "bundle_rejected_without_prerequisite": True,
            "target_commit_absent_before_bundle": True,
            "bundle_verified_with_public_base": True,
            "recovered_head": recovered_head, "recovered_tree": recovered_tree,
            "source_head_and_tree_identical": True, "raw_commit_bytes_identical": True,
            "recovered_parent": base, "git_fsck_passed": True,
            "recovered_working_tree_clean": True,
            "strict_ledger_expected_exit_code": 1,
            "strict_ledger_report_byte_identical": replay.read_bytes() == expected_report.read_bytes(),
            "strict_ledger_assessment_identical": True,
            "converter_only_diagnostic_fields": sorted(supplemental),
            "assessment_comparison": "Every field emitted by the archived standalone ledger, including all registrations and all 829 pairs, matches the committed converter report. The converter report separately adds four observation diagnostics; its key ordering and complete raw JSON bytes therefore differ.",
            "strict_ledger_result": expected_fields,
            "strict_ledger_report": {**digest(replay), "path": replay.relative_to(audit).as_posix()},
        }
        record["status"] = "verified"
    except Exception as exc:
        record["status"] = "failed"
        record["error"] = str(exc)
        raise
    finally:
        record["completed_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
