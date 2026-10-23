"""Infrastructure contracts for the parity gate, not Blender feature passes."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.parity_gate import evaluate


ROOT = Path(__file__).resolve().parents[1]


class ParityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = {"repository": "blender/blender", "commit": "a" * 40}
        self.context = {
            "artifact_sha256": "1" * 64,
            "native_artifact_sha256": "5" * 64,
            "port_commit": "b" * 40,
            "build_config_sha256": "2" * 64,
            "fixture_manifest_sha256": "3" * 64,
            "comparison_policy_sha256": "4" * 64,
        }
        self.manifest = {
            "schema": 1, "target": self.target,
            "required_profiles": ["chromium-webgpu"],
            "facets": [{"id": "mesh", "title": "Mesh editing", "depends_on": []}],
        }
        self.inventory = {
            "schema": 1, "target": self.target, "enumeration_complete": True,
            "facets_complete": ["mesh"],
            "cases": [
                {"id": "upstream.mesh.extrude", "facet": "mesh", "kind": "upstream",
                 "required_profiles": ["chromium-webgpu"]},
                {"id": "workflow.mesh.roundtrip", "facet": "mesh", "kind": "workflow",
                 "required_profiles": ["chromium-webgpu"]},
            ],
        }
        self.refresh_inventory_context()
        self.results = {
            "schema": 1, "target": self.target, "context": self.context, "run_id": "qualification-run-42",
            "records": [
                {"case_id": c["id"], "profile": "chromium-webgpu", "status": "passed"}
                for c in self.inventory["cases"]
            ],
        }
        self.refresh_receipts()

    def refresh_inventory_context(self):
        canonical = json.dumps(self.inventory, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.context["suite_manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if hasattr(self, "results"):
            self.refresh_receipts()

    def refresh_receipts(self):
        self.receipts = []
        for index, record in enumerate(self.results["records"]):
            receipt = {
                "schema": 1, "type": "blender-case-execution", "target": copy.deepcopy(self.target),
                "context": copy.deepcopy(self.context), "run_id": self.results["run_id"],
                "case_id": record["case_id"], "profile": record["profile"], "outcome": "passed",
                "execution": {"started": True, "completed": True, "exit_code": 0,
                              "timed_out": False, "crashed": False},
                "comparison": {"status": "passed", "policy_sha256": self.context["comparison_policy_sha256"]},
            }
            self.receipts.append(receipt)
            self.write_receipt(index, receipt)

    def write_receipt(self, index, receipt=None, *, payload=None):
        if payload is None:
            payload = (json.dumps(receipt if receipt is not None else self.receipts[index]) + "\n").encode()
        name = f"receipt-{index}.json"
        (self.root / name).write_bytes(payload)
        self.results["records"][index]["receipt"] = {"path": name, "sha256": hashlib.sha256(payload).hexdigest()}

    def assert_receipt_blocks(self, report, count=1):
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertFalse(report["full_feature_parity"])
        self.assertEqual(report["gate"], "blocked")
        self.assertEqual(report["counts"]["invalid_evidence"], count)

    def run_gate(self, **kwargs):
        args = {"manifest": self.manifest, "inventory": self.inventory,
                "results": self.results, "expected_context": self.context,
                "evidence_root": self.root}
        args.update(kwargs)
        return evaluate(**args)

    def test_typed_receipts_can_satisfy_declared_contract_without_feature_parity(self):
        report = self.run_gate()
        self.assertTrue(report["declared_contract_satisfied"])
        self.assertFalse(report["full_feature_parity"])
        self.assertIn("No independently validated full feature acceptance", report["full_feature_parity_reason"])
        self.assertEqual(report["gate"], "passed")
        self.assertEqual(report["known_obligation_count"], 2)
        self.assertEqual(report["passed_obligation_count"], 2)

    def test_incomplete_enumeration_cannot_pass_even_if_known_tests_pass(self):
        self.inventory["enumeration_complete"] = False
        self.refresh_inventory_context()
        report = self.run_gate()
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertNotIn("pass_rate_percent", report)
        self.assertEqual(report["passed_obligation_count"], 2)

    def test_incomplete_facet_cannot_pass(self):
        self.inventory["facets_complete"] = []
        self.refresh_inventory_context()
        self.assertFalse(self.run_gate()["declared_contract_satisfied"])

    def test_completed_facet_can_pass_while_application_inventory_is_incomplete(self):
        self.manifest["facets"].append({"id": "rendering", "title": "Rendering", "depends_on": ["mesh"]})
        self.inventory["enumeration_complete"] = False
        self.refresh_inventory_context()
        report = self.run_gate()
        mesh = next(f for f in report["facets"] if f["id"] == "mesh")
        rendering = next(f for f in report["facets"] if f["id"] == "rendering")
        self.assertEqual(mesh["status"], "passed")
        self.assertEqual(rendering["status"], "blocked")
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertNotIn("pass_rate_percent", report)

    def test_empty_inventory_and_no_results_never_pass(self):
        self.inventory["cases"] = []
        report = self.run_gate(results=None, expected_context=None, evidence_root=None)
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertEqual(report["known_obligation_count"], 0)

    def test_upstream_success_alone_does_not_establish_workflow_parity(self):
        self.inventory["cases"].pop()
        self.results["records"].pop()
        self.refresh_inventory_context()
        report = self.run_gate()
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertEqual(report["passed_obligation_count"], 1)
        self.assertIn("missing_obligation_kind:workflow", report["facets"][0]["blockers"])

    def test_every_non_pass_remains_in_denominator(self):
        for status in ("failed", "blocked", "unsupported", "skipped", "not_run",
                       "missing_fixture", "crashed", "timed_out", "disabled", "stale", "missing"):
            with self.subTest(status=status):
                self.results["records"][0]["status"] = status
                report = self.run_gate()
                self.assertFalse(report["declared_contract_satisfied"])
                self.assertEqual(report["known_obligation_count"], 2)
                self.assertEqual(report["passed_obligation_count"], 1)

    def test_missing_record_is_not_an_implicit_pass(self):
        self.results["records"].pop()
        report = self.run_gate()
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertEqual(report["counts"]["missing_result"], 1)

    def test_duplicate_or_unmapped_cases_and_records_are_rejected(self):
        for location in ("case", "record", "unknown_case", "unknown_facet"):
            with self.subTest(location=location):
                inv, result = copy.deepcopy(self.inventory), copy.deepcopy(self.results)
                if location == "case": inv["cases"].append(copy.deepcopy(inv["cases"][0]))
                if location == "record": result["records"].append(copy.deepcopy(result["records"][0]))
                if location == "unknown_case": result["records"][0]["case_id"] = "alien"
                if location == "unknown_facet": inv["cases"][0]["facet"] = "alien"
                with self.assertRaises(ValueError): self.run_gate(inventory=inv, results=result)

    def test_target_and_context_must_match_independent_contract(self):
        inv = copy.deepcopy(self.inventory)
        inv["target"]["commit"] = "c" * 40
        with self.assertRaises(ValueError): self.run_gate(inventory=inv)
        result = copy.deepcopy(self.results)
        result["target"]["commit"] = "c" * 40
        with self.assertRaises(ValueError): self.run_gate(results=result)
        for field in self.context:
            with self.subTest(field=field):
                result = copy.deepcopy(self.results)
                result["context"][field] = "c" * (40 if field == "port_commit" else 64)
                self.assertFalse(self.run_gate(results=result)["declared_contract_satisfied"])

    def test_passes_require_independent_expected_context(self):
        report = self.run_gate(expected_context=None)
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertEqual(report["passed_obligation_count"], 0)

    def test_native_result_cannot_replace_browser_execution(self):
        self.results["records"][0]["profile"] = "native"
        with self.assertRaises(ValueError): self.run_gate()

    def test_case_cannot_drop_required_browser_profile(self):
        self.inventory["cases"][0]["required_profiles"] = ["native"]
        with self.assertRaises(ValueError): self.run_gate()

    def test_unknown_status_and_duplicate_profiles_are_rejected(self):
        self.results["records"][0]["status"] = "looks_good"
        with self.assertRaises(ValueError): self.run_gate()
        self.results["records"][0]["status"] = "passed"
        self.inventory["cases"][0]["required_profiles"] *= 2
        with self.assertRaises(ValueError): self.run_gate()

    def test_unknown_inventory_profile_is_rejected(self):
        self.inventory["cases"][0]["required_profiles"].append("unknown-browser")
        with self.assertRaises(ValueError): self.run_gate()

    def test_native_reference_artifact_identity_is_not_ignored(self):
        result = copy.deepcopy(self.results)
        result["context"]["native_artifact_sha256"] = "f" * 64
        self.assertFalse(self.run_gate(results=result)["declared_contract_satisfied"])

    def test_actual_inventory_is_bound_to_suite_manifest_digest(self):
        added = copy.deepcopy(self.inventory["cases"][0])
        added["id"] = "upstream.mesh.additional"
        self.inventory["cases"].append(added)
        record = copy.deepcopy(self.results["records"][0])
        record["case_id"] = added["id"]
        self.results["records"].append(record)
        # The unchanged expected context still refers to the earlier inventory.
        self.assertFalse(self.run_gate()["declared_contract_satisfied"])

    def test_hash_mismatch_missing_file_or_missing_receipt_blocks_pass(self):
        for receipt in (None, {}, {"path": "missing.json", "sha256": "0" * 64},
                        {"path": "receipt-0.json", "sha256": "0" * 64}):
            with self.subTest(receipt=receipt):
                result = copy.deepcopy(self.results)
                result["records"][0]["receipt"] = receipt
                self.assert_receipt_blocks(self.run_gate(results=result))

    def test_path_escape_absolute_path_and_symlink_cannot_be_evidence(self):
        outside = self.root.parent / (self.root.name + "-external.json")
        outside.write_bytes((self.root / "receipt-0.json").read_bytes())
        self.addCleanup(outside.unlink)
        (self.root / "linked.json").symlink_to(outside)
        for path in ("../" + outside.name, str(outside), "linked.json", "./receipt-0.json", "nested//receipt.json"):
            with self.subTest(path=path):
                result = copy.deepcopy(self.results)
                result["records"][0]["receipt"]["path"] = path
                self.assert_receipt_blocks(self.run_gate(results=result))

    def test_hashed_unrelated_failed_comparison_cannot_support_passed_records(self):
        # This exact shape used to qualify when only the file hash was checked.
        payload = b'{"comparison":"failed","case_id":"unrelated.case","profile":"native-only"}\n'
        self.write_receipt(0, payload=payload)
        self.assert_receipt_blocks(self.run_gate())

    def test_hash_valid_logs_and_legacy_evidence_cannot_replace_execution_receipt(self):
        payload = b"Process completed, PASS\n"
        (self.root / "runner.log").write_bytes(payload)
        attachment = {"path": "runner.log", "sha256": hashlib.sha256(payload).hexdigest()}
        record = self.results["records"][0]
        del record["receipt"]
        record["attachments"] = [attachment]
        record["evidence"] = [attachment]
        self.assert_receipt_blocks(self.run_gate())

    def test_receipt_cannot_be_reused_for_another_case_in_same_run(self):
        self.results["records"][1]["receipt"] = copy.deepcopy(self.results["records"][0]["receipt"])
        self.assert_receipt_blocks(self.run_gate())

    def test_receipt_case_profile_and_run_must_match(self):
        for field, value in (("case_id", "different.case"), ("profile", "native-reference"),
                             ("run_id", "qualification-run-41")):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipts[0])
                receipt[field] = value
                self.write_receipt(0, receipt)
                report = self.run_gate()
                self.assert_receipt_blocks(report)
                self.assertIn(field, report["non_passing"][0]["reason"])

    def test_results_without_run_identity_cannot_qualify(self):
        for value in (None, "", 42):
            with self.subTest(run_id=value):
                result = copy.deepcopy(self.results)
                result["run_id"] = value
                self.assert_receipt_blocks(self.run_gate(results=result), count=2)

    def test_duplicate_json_run_identity_cannot_be_hidden_by_last_value(self):
        # A normal JSON decoder would discard the first, stale run_id.
        payload = b'{"run_id":"qualification-run-41",' + json.dumps(self.receipts[0]).encode()[1:]
        self.write_receipt(0, payload=payload)
        report = self.run_gate()
        self.assert_receipt_blocks(report)
        self.assertIn("duplicate JSON field", report["non_passing"][0]["reason"])

    def test_receipt_target_and_every_context_identity_are_bound(self):
        for field in ("target", *self.context):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipts[0])
                if field == "target":
                    receipt["target"]["commit"] = "c" * 40
                else:
                    receipt["context"][field] = "c" * (40 if field == "port_commit" else 64)
                self.write_receipt(0, receipt)
                self.assert_receipt_blocks(self.run_gate())

    def test_typed_non_pass_outcomes_never_become_functional_passes(self):
        for outcome in ("failed", "skipped", "expected_failure", "unexpected_success", "not_run", None):
            with self.subTest(outcome=outcome):
                receipt = copy.deepcopy(self.receipts[0])
                receipt["outcome"] = outcome
                self.write_receipt(0, receipt)
                self.assert_receipt_blocks(self.run_gate())

    def test_pass_marker_before_timeout_crash_or_nonzero_exit_is_not_completion(self):
        changes = (("started", False), ("completed", False), ("timed_out", True), ("crashed", True),
                   ("exit_code", 1), ("exit_code", -11), ("exit_code", None), ("exit_code", False))
        for field, value in changes:
            with self.subTest(field=field, value=value):
                receipt = copy.deepcopy(self.receipts[0])
                receipt["execution"][field] = value
                self.write_receipt(0, receipt)
                self.assert_receipt_blocks(self.run_gate())

    def test_case_success_cannot_override_failed_or_changed_comparison(self):
        for field, value in (("status", "failed"), ("status", "skipped"), ("policy_sha256", "0" * 64)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipts[0])
                receipt["comparison"][field] = value
                self.write_receipt(0, receipt)
                self.assert_receipt_blocks(self.run_gate())

    def test_unknown_receipt_type_or_schema_does_not_qualify(self):
        for field, value in (("type", "browser-log"), ("schema", 2), ("schema", True)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipts[0])
                receipt[field] = value
                self.write_receipt(0, receipt)
                self.assert_receipt_blocks(self.run_gate())

    def test_optional_attachments_are_checked_separately_from_semantic_receipt(self):
        payload = b"runner diagnostic output\n"
        (self.root / "runner.log").write_bytes(payload)
        attachment = {"path": "runner.log", "sha256": hashlib.sha256(payload).hexdigest()}
        self.results["records"][0]["attachments"] = [attachment]
        self.assertTrue(self.run_gate()["declared_contract_satisfied"])
        (self.root / "runner.log").write_bytes(b"changed output\n")
        self.assert_receipt_blocks(self.run_gate())

    def test_duplicate_receipt_or_attachment_references_are_rejected(self):
        self.results["records"][0]["attachments"] = [self.results["records"][0]["receipt"]]
        self.assert_receipt_blocks(self.run_gate())

    def test_dependency_failure_blocks_dependent_facet(self):
        self.manifest["facets"].append({"id": "files", "title": "Files", "depends_on": ["mesh"]})
        self.inventory["facets_complete"].append("files")
        for kind in ("upstream", "workflow"):
            case = {"id": kind + ".files", "facet": "files", "kind": kind,
                    "required_profiles": ["chromium-webgpu"]}
            self.inventory["cases"].append(case)
            self.results["records"].append({"case_id": case["id"], "profile": "chromium-webgpu",
                                            "status": "passed"})
        self.results["records"][0]["status"] = "failed"
        self.refresh_inventory_context()
        report = self.run_gate()
        files = next(f for f in report["facets"] if f["id"] == "files")
        self.assertEqual(files["status"], "blocked")
        self.assertEqual(files["counts"]["passed"], 2)
        self.assertIn("dependency:mesh", files["blockers"])

    def test_dependency_cycles_unknown_dependencies_and_short_pins_fail(self):
        for change in ("cycle", "unknown", "short"):
            with self.subTest(change=change):
                manifest = copy.deepcopy(self.manifest)
                if change == "cycle": manifest["facets"][0]["depends_on"] = ["mesh"]
                if change == "unknown": manifest["facets"][0]["depends_on"] = ["missing"]
                if change == "short": manifest["target"]["commit"] = "abc123"
                with self.assertRaises(ValueError): self.run_gate(manifest=manifest)

    def test_cli_report_only_preserves_blocked_status_and_strict_gate_fails(self):
        self.inventory["enumeration_complete"] = False
        for name, data in (("manifest", self.manifest), ("inventory", self.inventory)):
            (self.root / (name + ".json")).write_text(json.dumps(data))
        output = self.root / "report.json"
        args = [sys.executable, str(ROOT / "tools/parity_gate.py"),
                "--manifest", str(self.root / "manifest.json"),
                "--inventory", str(self.root / "inventory.json"), "--output", str(output)]
        strict = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(strict.returncode, 1, strict.stderr)
        report_only = subprocess.run(args + ["--report-only"], capture_output=True, text=True)
        self.assertEqual(report_only.returncode, 0, report_only.stderr)
        report = json.loads(output.read_text())
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertFalse(report["full_feature_parity"])

    def test_strict_cli_succeeds_for_declared_contract_without_claiming_full_parity(self):
        for name, data in (("manifest", self.manifest), ("inventory", self.inventory),
                           ("results", self.results), ("context", self.context)):
            (self.root / (name + ".json")).write_text(json.dumps(data))
        output = self.root / "report.json"
        args = [sys.executable, str(ROOT / "tools/parity_gate.py"),
                "--manifest", str(self.root / "manifest.json"),
                "--inventory", str(self.root / "inventory.json"),
                "--results", str(self.root / "results.json"),
                "--context", str(self.root / "context.json"),
                "--evidence-root", str(self.root), "--output", str(output)]
        process = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        for report in (json.loads(output.read_text()), json.loads(process.stdout)):
            self.assertTrue(report["declared_contract_satisfied"])
            self.assertFalse(report["full_feature_parity"])
            self.assertEqual(report["gate"], "passed")

    def test_invalid_cli_input_does_not_leave_a_stale_passing_report(self):
        self.manifest["target"] = {"repository": "blender/blender", "commit": "short"}
        for name, data in (("manifest", self.manifest), ("inventory", self.inventory)):
            (self.root / (name + ".json")).write_text(json.dumps(data))
        output = self.root / "report.json"
        output.write_text('{"declared_contract_satisfied":true,"full_feature_parity":true}')
        args = [sys.executable, str(ROOT / "tools/parity_gate.py"),
                "--manifest", str(self.root / "manifest.json"),
                "--inventory", str(self.root / "inventory.json"), "--output", str(output)]
        process = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        report = json.loads(output.read_text())
        self.assertFalse(report["declared_contract_satisfied"])
        self.assertFalse(report["full_feature_parity"])


if __name__ == "__main__":
    unittest.main()
