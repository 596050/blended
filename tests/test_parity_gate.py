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
        payload = b'{"comparison":"passed","native":"reference","browser":"candidate"}\n'
        (self.root / "comparison.json").write_bytes(payload)
        self.evidence = [{"path": "comparison.json", "sha256": hashlib.sha256(payload).hexdigest()}]
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
            "schema": 1, "target": self.target, "context": self.context,
            "records": [
                {"case_id": c["id"], "profile": "chromium-webgpu", "status": "passed",
                 "evidence": copy.deepcopy(self.evidence)} for c in self.inventory["cases"]
            ],
        }

    def refresh_inventory_context(self):
        canonical = json.dumps(self.inventory, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.context["suite_manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def run_gate(self, **kwargs):
        args = {"manifest": self.manifest, "inventory": self.inventory,
                "results": self.results, "expected_context": self.context,
                "evidence_root": self.root}
        args.update(kwargs)
        return evaluate(**args)

    def test_complete_current_evidence_can_pass(self):
        report = self.run_gate()
        self.assertTrue(report["full_feature_parity"])
        self.assertEqual(report["gate"], "passed")
        self.assertEqual(report["known_obligation_count"], 2)
        self.assertEqual(report["passed_obligation_count"], 2)

    def test_incomplete_enumeration_cannot_pass_even_if_known_tests_pass(self):
        self.inventory["enumeration_complete"] = False
        self.refresh_inventory_context()
        report = self.run_gate()
        self.assertFalse(report["full_feature_parity"])
        self.assertNotIn("pass_rate_percent", report)
        self.assertEqual(report["passed_obligation_count"], 2)

    def test_incomplete_facet_cannot_pass(self):
        self.inventory["facets_complete"] = []
        self.refresh_inventory_context()
        self.assertFalse(self.run_gate()["full_feature_parity"])

    def test_completed_facet_can_pass_while_application_inventory_is_incomplete(self):
        self.manifest["facets"].append({"id": "rendering", "title": "Rendering", "depends_on": ["mesh"]})
        self.inventory["enumeration_complete"] = False
        self.refresh_inventory_context()
        report = self.run_gate()
        mesh = next(f for f in report["facets"] if f["id"] == "mesh")
        rendering = next(f for f in report["facets"] if f["id"] == "rendering")
        self.assertEqual(mesh["status"], "passed")
        self.assertEqual(rendering["status"], "blocked")
        self.assertFalse(report["full_feature_parity"])
        self.assertNotIn("pass_rate_percent", report)

    def test_empty_inventory_and_no_results_never_pass(self):
        self.inventory["cases"] = []
        report = self.run_gate(results=None, expected_context=None, evidence_root=None)
        self.assertFalse(report["full_feature_parity"])
        self.assertEqual(report["known_obligation_count"], 0)

    def test_upstream_success_alone_does_not_establish_workflow_parity(self):
        self.inventory["cases"].pop()
        self.results["records"].pop()
        self.assertFalse(self.run_gate()["full_feature_parity"])

    def test_every_non_pass_remains_in_denominator(self):
        for status in ("failed", "blocked", "unsupported", "skipped", "not_run",
                       "missing_fixture", "crashed", "timed_out", "disabled", "stale", "missing"):
            with self.subTest(status=status):
                self.results["records"][0]["status"] = status
                report = self.run_gate()
                self.assertFalse(report["full_feature_parity"])
                self.assertEqual(report["known_obligation_count"], 2)
                self.assertEqual(report["passed_obligation_count"], 1)

    def test_missing_record_is_not_an_implicit_pass(self):
        self.results["records"].pop()
        report = self.run_gate()
        self.assertFalse(report["full_feature_parity"])
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
                self.assertFalse(self.run_gate(results=result)["full_feature_parity"])

    def test_passes_require_independent_expected_context(self):
        report = self.run_gate(expected_context=None)
        self.assertFalse(report["full_feature_parity"])
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
        self.assertFalse(self.run_gate(results=result)["full_feature_parity"])

    def test_actual_inventory_is_bound_to_suite_manifest_digest(self):
        added = copy.deepcopy(self.inventory["cases"][0])
        added["id"] = "upstream.mesh.additional"
        self.inventory["cases"].append(added)
        record = copy.deepcopy(self.results["records"][0])
        record["case_id"] = added["id"]
        self.results["records"].append(record)
        # The unchanged expected context still refers to the earlier inventory.
        self.assertFalse(self.run_gate()["full_feature_parity"])

    def test_hash_mismatch_missing_file_or_empty_evidence_blocks_pass(self):
        for evidence in ([], [{"path": "missing.json", "sha256": "0" * 64}],
                         [{"path": "comparison.json", "sha256": "0" * 64}]):
            with self.subTest(evidence=evidence):
                result = copy.deepcopy(self.results)
                result["records"][0]["evidence"] = evidence
                report = self.run_gate(results=result)
                self.assertFalse(report["full_feature_parity"])
                self.assertEqual(report["counts"]["invalid_evidence"], 1)

    def test_path_escape_absolute_path_and_symlink_cannot_be_evidence(self):
        outside = self.root.parent / (self.root.name + "-external.json")
        outside.write_bytes((self.root / "comparison.json").read_bytes())
        self.addCleanup(outside.unlink)
        (self.root / "linked.json").symlink_to(outside)
        for path in ("../" + outside.name, str(outside), "linked.json"):
            with self.subTest(path=path):
                result = copy.deepcopy(self.results)
                result["records"][0]["evidence"][0]["path"] = path
                self.assertFalse(self.run_gate(results=result)["full_feature_parity"])

    def test_dependency_failure_blocks_dependent_facet(self):
        self.manifest["facets"].append({"id": "files", "title": "Files", "depends_on": ["mesh"]})
        self.inventory["facets_complete"].append("files")
        for kind in ("upstream", "workflow"):
            case = {"id": kind + ".files", "facet": "files", "kind": kind,
                    "required_profiles": ["chromium-webgpu"]}
            self.inventory["cases"].append(case)
            self.results["records"].append({"case_id": case["id"], "profile": "chromium-webgpu",
                                            "status": "passed", "evidence": self.evidence})
        self.results["records"][0]["status"] = "failed"
        self.refresh_inventory_context()
        report = self.run_gate()
        files = next(f for f in report["facets"] if f["id"] == "files")
        self.assertEqual(files["status"], "blocked")
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
        self.assertFalse(json.loads(output.read_text())["full_feature_parity"])

    def test_invalid_cli_input_does_not_leave_a_stale_passing_report(self):
        self.manifest["target"] = {"repository": "blender/blender", "commit": "short"}
        for name, data in (("manifest", self.manifest), ("inventory", self.inventory)):
            (self.root / (name + ".json")).write_text(json.dumps(data))
        output = self.root / "report.json"
        output.write_text('{"full_feature_parity":true}')
        args = [sys.executable, str(ROOT / "tools/parity_gate.py"),
                "--manifest", str(self.root / "manifest.json"),
                "--inventory", str(self.root / "inventory.json"), "--output", str(output)]
        process = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        self.assertFalse(json.loads(output.read_text())["full_feature_parity"])


if __name__ == "__main__":
    unittest.main()
