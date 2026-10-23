"""Negative acceptance checks for exact native/browser accounting.

These synthetic cases validate the infrastructure. They are not Blender tests.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools.test_parity_ledger import assess, canonical_sha256


class PairedLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = {"repository": "blender/blender", "commit": "a" * 40}
        context = {key: str(i) * 64 for i, key in enumerate(
            ("artifact_sha256", "build_config_sha256", "adapter_sha256", "runtime_sha256"), 1)}
        self.contract = {
            "schema": 1, "target": self.target, "scope": "selected-original-suites",
            "configurations": [{"id": "release", "registrations": [{
                "id": "python_example", "invocation_sha256": "5" * 64,
                "fixture_manifest_sha256": "6" * 64, "comparison_policy_sha256": "7" * 64,
            }]}],
            "profiles": [
                {"id": "native", "role": "reference", "runtime_kind": "native",
                 "contexts": {"release": copy.deepcopy(context)}},
                {"id": "chromium", "role": "candidate", "runtime_kind": "browser",
                 "contexts": {"release": {**context, "artifact_sha256": "8" * 64}}},
            ],
            "coverage": {"source_registration_reconciliation_complete": False,
                         "configuration_matrix_complete": False,
                         "fixture_closure_complete": False,
                         "blockers": ["Only a selected original registration is available"]},
        }
        self.ids = ["tests/python/example.py::Example.test_a", "tests/python/example.py::Example.test_b"]
        self.process = {"started": True, "completed": True, "exit_code": 0,
                        "timed_out": False, "crashed": False}
        self.raw = self.write_bytes("raw.log", b"synthetic infrastructure evidence\n")
        self.discovery = {
            "schema": 1, "kind": "blender-test-discovery", "target": self.target,
            "contract_sha256": canonical_sha256(self.contract), "profile": "native",
            "runtime_kind": "native", "context": copy.deepcopy(context),
            "configuration": "release", "registration_id": "python_example",
            **self.contract["configurations"][0]["registrations"][0],
            "process": copy.deepcopy(self.process), "case_ids": self.ids,
            "disabled_case_ids": [], "selection": {"filters": [], "shard": None},
            "raw_evidence": [self.raw],
        }
        self.inventory = {
            "schema": 1, "target": self.target, "contract_sha256": canonical_sha256(self.contract),
            "registrations": [{"id": "python_example", "configuration": "release",
                               "status": "expanded", "case_ids": list(self.ids),
                               "disabled_case_ids": [], "discovery": self.write_json("discovery.json", self.discovery)}],
        }
        self.execution = {
            "schema": 1, "target": self.target, "contract_sha256": canonical_sha256(self.contract),
            "inventory_sha256": canonical_sha256(self.inventory), "runs": [],
        }
        self.receipts = {}
        for profile in self.contract["profiles"]:
            pid = profile["id"]
            receipt = {
                "schema": 1, "kind": "blender-test-execution", "target": self.target,
                "contract_sha256": canonical_sha256(self.contract),
                "inventory_sha256": canonical_sha256(self.inventory),
                "profile": pid, "runtime_kind": profile["runtime_kind"],
                "context": copy.deepcopy(profile["contexts"]["release"]),
                "configuration": "release", "registration_id": "python_example", "run_id": "run-" + pid,
                **self.contract["configurations"][0]["registrations"][0],
                "process": copy.deepcopy(self.process), "raw_evidence": [self.raw],
                "selection": {"filters": [], "shard": None},
                "cases": [{"id": cid, "outcome": "passed", "started": True, "completed": True,
                           "comparison": {"status": "passed", "policy_sha256": "7" * 64},
                           "subtests": []} for cid in self.ids],
            }
            self.receipts[pid] = receipt
            self.execution["runs"].append({"profile": pid, "configuration": "release",
                                           "registration_id": "python_example", "run_id": "run-" + pid,
                                           "receipt": self.write_json(pid + ".json", receipt)})

    def write_bytes(self, name, data):
        (self.root / name).write_bytes(data)
        return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}

    def write_json(self, name, value):
        return self.write_bytes(name, (json.dumps(value, sort_keys=True) + "\n").encode())

    def refresh(self, profile):
        for run in self.execution["runs"]:
            if run["profile"] == profile:
                run["receipt"] = self.write_json(profile + ".json", self.receipts[profile])

    def refresh_discovery(self):
        self.inventory["registrations"][0]["discovery"] = self.write_json("discovery.json", self.discovery)
        self.execution["inventory_sha256"] = canonical_sha256(self.inventory)
        for profile in self.receipts:
            self.receipts[profile]["inventory_sha256"] = canonical_sha256(self.inventory)
            self.refresh(profile)

    def add_second_registration(self, **criteria):
        registration = copy.deepcopy(self.contract["configurations"][0]["registrations"][0])
        registration.update(id="python_example_again", **criteria)
        self.contract["configurations"][0]["registrations"].append(registration)
        contract_digest = canonical_sha256(self.contract)
        self.inventory["contract_sha256"] = self.execution["contract_sha256"] = contract_digest
        self.discovery["contract_sha256"] = contract_digest
        self.inventory["registrations"][0]["discovery"] = self.write_json("discovery.json", self.discovery)
        discovery = copy.deepcopy(self.discovery)
        discovery.update(registration_id=registration["id"], **registration)
        self.inventory["registrations"].append({
            "id": registration["id"], "configuration": "release", "status": "expanded",
            "case_ids": list(self.ids), "disabled_case_ids": [],
            "discovery": self.write_json("discovery-again.json", discovery),
        })
        inventory_digest = canonical_sha256(self.inventory)
        self.execution["inventory_sha256"] = inventory_digest
        for profile in self.receipts:
            self.receipts[profile].update(contract_sha256=contract_digest, inventory_sha256=inventory_digest)
            self.refresh(profile)
            receipt = copy.deepcopy(self.receipts[profile])
            receipt.update(registration_id=registration["id"], run_id="again-" + profile, **registration)
            for case in receipt["cases"]:
                case["comparison"]["policy_sha256"] = registration["comparison_policy_sha256"]
            self.execution["runs"].append({
                "profile": profile, "configuration": "release", "registration_id": registration["id"],
                "run_id": receipt["run_id"], "receipt": self.write_json(profile + "-again.json", receipt),
            })

    def report(self):
        return assess(self.contract, self.inventory, self.execution, self.root)

    def test_exact_paired_passes_have_only_scoped_meaning(self):
        result = self.report()
        self.assertTrue(result["declared_scope_test_parity"])
        self.assertEqual(result["successful_execution_pair_count"], 2)
        self.assertEqual(result["outcome_agreement_count"], 2)
        self.assertFalse(result["all_upstream_test_parity"])
        self.assertFalse(result["full_feature_parity"])
        self.assertNotIn("pass_rate_percent", result)

    def test_browser_cannot_replace_a_missing_case_with_same_count(self):
        self.receipts["chromium"]["cases"][1]["id"] = "Other.test_same_count"
        self.refresh("chromium")
        with self.assertRaisesRegex(ValueError, "unknown case"):
            self.report()

    def test_missing_browser_case_retains_denominator(self):
        self.receipts["chromium"]["cases"].pop()
        self.refresh("chromium")
        result = self.report()
        self.assertEqual(result["known_case_configuration_count"], 2)
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertFalse(result["declared_scope_test_parity"])
        self.assertEqual(result["pairs"][1]["browser_outcome"], "missing")

    def test_completed_pass_callbacks_do_not_override_driver_validation_blockers(self):
        self.receipts["chromium"]["validation_blockers"] = ["original_host_tool_unavailable:IDIFF_BIN"]
        self.refresh("chromium")
        result = self.report()
        self.assertEqual(result["successful_execution_pair_count"], 0)
        self.assertEqual(result["outcome_agreement_count"], 0)
        self.assertIn("browser_validation:original_host_tool_unavailable:IDIFF_BIN",
                      result["pairs"][0]["blockers"])
        self.assertEqual(result["pairs"][0]["browser_outcome"], "passed")

    def test_hash_valid_failed_comparison_is_not_a_pass(self):
        self.receipts["chromium"]["cases"][0]["comparison"]["status"] = "failed"
        self.refresh("chromium")
        result = self.report()
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertFalse(result["declared_scope_test_parity"])

    def test_parsed_receipt_is_the_same_payload_that_was_hashed(self):
        self.receipts["chromium"]["cases"][0]["comparison"]["status"] = "failed"
        self.refresh("chromium")
        passed = copy.deepcopy(self.receipts["chromium"])
        passed["cases"][0]["comparison"]["status"] = "passed"
        real_read_bytes = Path.read_bytes

        def replaced_after_hash(path):
            if path == self.root / "chromium.json":
                return json.dumps(passed).encode()
            return real_read_bytes(path)

        # The old two-read consumer checked the failed file's hash, then parsed
        # this substituted passing payload. The consumer must use verified bytes.
        with mock.patch.object(Path, "read_bytes", replaced_after_hash):
            result = self.report()
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertFalse(result["declared_scope_test_parity"])

    def test_timeout_after_partial_success_blocks_run_and_preserves_missing(self):
        self.receipts["chromium"]["cases"].pop()
        self.receipts["chromium"]["process"].update(completed=False, timed_out=True, exit_code=None)
        self.refresh("chromium")
        result = self.report()
        self.assertEqual(result["known_case_configuration_count"], 2)
        self.assertEqual(result["successful_execution_pair_count"], 0)
        self.assertFalse(result["declared_scope_test_parity"])
        self.assertIn("timed_out", result["pairs"][0]["blockers"])

    def test_matching_expected_failures_are_agreement_not_functional_success(self):
        for profile in self.receipts:
            item = self.receipts[profile]["cases"][0]
            item.update(outcome="expected_failure", detail_sha256="9" * 64)
            item["comparison"]["status"] = "failed"
            self.refresh(profile)
        result = self.report()
        self.assertEqual(result["outcome_agreement_count"], 2)
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertFalse(result["declared_scope_test_parity"])

    def test_equal_skip_status_without_same_reason_is_not_agreement(self):
        for index, profile in enumerate(self.receipts, 1):
            self.receipts[profile]["cases"][0].update(outcome="skipped", detail_sha256=str(index) * 64)
            self.refresh(profile)
        self.assertEqual(self.report()["outcome_agreement_count"], 1)

    def test_subtests_are_compared_one_to_one(self):
        for profile in self.receipts:
            self.receipts[profile]["cases"][0]["subtests"] = [{"id": "param=1", "outcome": "passed"}]
        self.receipts["chromium"]["cases"][0]["subtests"][0]["id"] = "param=2"
        for profile in self.receipts:
            self.refresh(profile)
        result = self.report()
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertEqual(result["outcome_agreement_count"], 1)

    def test_duplicate_subtest_identity_is_not_a_second_independent_check(self):
        event = {"id": "param=1", "outcome": "passed"}
        self.receipts["chromium"]["cases"][0]["subtests"] = [event, copy.deepcopy(event)]
        self.refresh("chromium")
        with self.assertRaisesRegex(ValueError, "duplicate subtest identity"):
            self.report()

    def test_matching_nonpassing_subtests_need_reasons_and_cannot_pass(self):
        for profile in self.receipts:
            self.receipts[profile]["cases"][0]["subtests"] = [{"id": "param=1", "outcome": "failed"}]
            self.refresh(profile)
        result = self.report()
        self.assertEqual(result["outcome_agreement_count"], 1)
        self.assertEqual(result["successful_execution_pair_count"], 1)
        for profile in self.receipts:
            self.receipts[profile]["cases"][0]["subtests"][0]["detail_sha256"] = "9" * 64
            self.refresh(profile)
        result = self.report()
        self.assertEqual(result["outcome_agreement_count"], 2)
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertFalse(result["declared_scope_test_parity"])

    def test_native_cannot_be_relabelled_as_browser(self):
        self.receipts["chromium"]["runtime_kind"] = "native"
        self.refresh("chromium")
        with self.assertRaisesRegex(ValueError, "runtime kind"):
            self.report()

    def test_receipts_bind_case_context_profile_run_target_and_inventory(self):
        mutations = {
            "target": lambda r: r["target"].update(commit="b" * 40),
            "profile": lambda r: r.update(profile="native"),
            "run": lambda r: r.update(run_id="another-run"),
            "artifact": lambda r: r["context"].update(artifact_sha256="f" * 64),
            "inventory": lambda r: r.update(inventory_sha256="e" * 64),
            "policy": lambda r: r["cases"][0]["comparison"].update(policy_sha256="e" * 64),
        }
        original = copy.deepcopy(self.receipts["chromium"])
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                self.receipts["chromium"] = copy.deepcopy(original)
                mutate(self.receipts["chromium"])
                self.refresh("chromium")
                with self.assertRaises(ValueError):
                    self.report()

    def test_unexpanded_registration_remains_a_blocker(self):
        self.inventory["registrations"][0].update(status="blocked", reason="renderer disabled", case_ids=[])
        self.execution = None
        result = self.report()
        self.assertFalse(result["scope_enumeration_complete"])
        self.assertFalse(result["declared_scope_test_parity"])
        self.assertEqual(result["unresolved_registration_count"], 1)

    def test_missing_configuration_cannot_shrink_required_registrations(self):
        self.inventory["registrations"].clear()
        self.execution = None
        result = self.report()
        self.assertEqual(result["required_registration_count"], 1)
        self.assertEqual(result["unresolved_registration_count"], 1)
        self.assertFalse(result["scope_enumeration_complete"])

    def test_filtered_native_discovery_does_not_close_registration(self):
        self.discovery["selection"]["filters"] = ["Example.test_a"]
        self.inventory["registrations"][0]["discovery"] = self.write_json("discovery.json", self.discovery)
        self.execution = None
        result = self.report()
        self.assertFalse(result["scope_enumeration_complete"])
        self.assertIn("filtered_discovery", result["registrations"][0]["blockers"])

    def test_matching_receipts_from_filtered_or_sharded_discovery_do_not_agree(self):
        for selection in ({"filters": ["Example.test_a"], "shard": None},
                          {"filters": [], "shard": {"index": 0, "total": 2}}):
            with self.subTest(selection=selection):
                self.discovery["selection"] = selection
                self.refresh_discovery()
                result = self.report()
                self.assertEqual(result["paired_obligation_count"], 2)
                self.assertEqual(result["outcome_agreement_count"], 0)
                self.assertFalse(result["scope_enumeration_complete"])
                self.assertFalse(result["declared_scope_test_parity"])

    def test_incomplete_discovery_cannot_qualify_matching_execution_receipts(self):
        self.discovery["process"].update(completed=False, exit_code=None)
        self.refresh_discovery()
        result = self.report()
        self.assertEqual(result["outcome_agreement_count"], 0)
        self.assertIn("incomplete_native_discovery", result["registrations"][0]["blockers"])
        self.assertFalse(result["declared_scope_test_parity"])

    def test_execution_must_declare_extra_selection_even_when_every_case_passes(self):
        del self.receipts["chromium"]["selection"]
        self.refresh("chromium")
        with self.assertRaisesRegex(ValueError, "execution selection"):
            self.report()

    def test_filtered_or_sharded_execution_retains_but_cannot_close_registration(self):
        for selection in ({"filters": ["Example.*"], "shard": None},
                          {"filters": [], "shard": {"index": 0, "total": 2}}):
            with self.subTest(selection=selection):
                self.receipts["chromium"]["selection"] = selection
                self.refresh("chromium")
                result = self.report()
                self.assertEqual(result["paired_obligation_count"], 2)
                self.assertEqual(result["outcome_agreement_count"], 0)
                self.assertEqual(result["successful_execution_pair_count"], 0)
                self.assertIn("browser_filtered_execution", result["pairs"][0]["blockers"])
                self.assertTrue(result["scope_enumeration_complete"])
                self.assertFalse(result["declared_scope_test_parity"])

    def test_nonzero_or_incomplete_execution_never_becomes_a_functional_pass(self):
        original = copy.deepcopy(self.process)
        for process in ({**original, "exit_code": 1}, {**original, "exit_code": -11},
                        {**original, "completed": False, "exit_code": None},
                        {**original, "crashed": True}):
            with self.subTest(process=process):
                self.receipts["chromium"]["process"] = process
                self.refresh("chromium")
                result = self.report()
                self.assertEqual(result["successful_execution_pair_count"], 0)
                self.assertFalse(result["declared_scope_test_parity"])
                if process["exit_code"] != 1:
                    self.assertEqual(result["outcome_agreement_count"], 0)

    def test_native_discovery_must_have_exact_same_leaf_ids(self):
        self.discovery["case_ids"] = [self.ids[0], "Other.test_same_count"]
        self.inventory["registrations"][0]["discovery"] = self.write_json("discovery.json", self.discovery)
        self.execution = None
        with self.assertRaisesRegex(ValueError, "case IDs"):
            self.report()

    def test_disabled_case_is_enumerated_but_cannot_pass(self):
        self.discovery["disabled_case_ids"] = [self.ids[1]]
        reg = self.inventory["registrations"][0]
        reg["disabled_case_ids"] = [self.ids[1]]
        reg["discovery"] = self.write_json("discovery.json", self.discovery)
        digest = canonical_sha256(self.inventory)
        self.execution["inventory_sha256"] = digest
        for profile in self.receipts:
            self.receipts[profile]["inventory_sha256"] = digest
            self.refresh(profile)
        result = self.report()
        self.assertEqual(result["known_case_configuration_count"], 2)
        self.assertEqual(result["successful_execution_pair_count"], 1)
        self.assertEqual(result["outcome_agreement_count"], 1)
        self.assertFalse(result["declared_scope_test_parity"])

    def test_equivalent_duplicate_registrations_deduplicate_only_final_obligations(self):
        self.add_second_registration()
        result = self.report()
        self.assertEqual(result["required_registration_count"], 2)
        self.assertEqual(result["known_case_count"], 2)
        self.assertEqual(result["paired_obligation_count"], 2)
        self.assertEqual(result["registration_execution_pair_count"], 4)
        self.assertEqual(result["successful_execution_pair_count"], 2)
        self.assertTrue(result["declared_scope_test_parity"])
        self.execution["runs"] = [run for run in self.execution["runs"]
                                  if not (run["profile"] == "chromium" and run["registration_id"] == "python_example_again")]
        result = self.report()
        self.assertEqual(result["paired_obligation_count"], 2)
        self.assertEqual(result["successful_execution_pair_count"], 0)
        self.assertFalse(result["declared_scope_test_parity"])

    def test_distinct_invocations_fixtures_or_policies_are_distinct_obligations(self):
        for field in ("invocation_sha256", "fixture_manifest_sha256", "comparison_policy_sha256"):
            with self.subTest(field=field):
                # Each criterion independently prevents accidental deduplication.
                other = PairedLedgerTests()
                other.setUp()
                try:
                    other.add_second_registration(**{field: "9" * 64})
                    result = other.report()
                finally:
                    other.doCleanups()
                self.assertEqual(result["known_case_count"], 2)
                self.assertEqual(result["paired_obligation_count"], 4)
                self.assertEqual(result["successful_execution_pair_count"], 4)
                self.assertTrue(result["declared_scope_test_parity"])

    def test_self_declared_coverage_flags_never_certify_all_tests_or_features(self):
        self.contract["coverage"] = {
            "source_registration_reconciliation_complete": True,
            "configuration_matrix_complete": True,
            "fixture_closure_complete": True,
            "blockers": [],
        }
        # Rebind the selected receipts to the revised contract without adding
        # any actual registrations or cases to their limited denominator.
        contract_digest = canonical_sha256(self.contract)
        self.discovery["contract_sha256"] = contract_digest
        self.inventory["contract_sha256"] = self.execution["contract_sha256"] = contract_digest
        for profile in self.receipts:
            self.receipts[profile]["contract_sha256"] = contract_digest
        self.refresh_discovery()
        result = self.report()
        self.assertTrue(result["declared_scope_test_parity"])
        self.assertFalse(result["all_upstream_test_parity"])
        self.assertFalse(result["full_feature_parity"])
        self.assertNotIn("pass_rate_percent", result)

    def test_duplicate_case_and_duplicate_run_are_rejected(self):
        self.receipts["chromium"]["cases"].append(copy.deepcopy(self.receipts["chromium"]["cases"][0]))
        self.refresh("chromium")
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            self.report()
        self.receipts["chromium"]["cases"].pop()
        self.refresh("chromium")
        self.execution["runs"].append(copy.deepcopy(self.execution["runs"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate run"):
            self.report()

    def test_duplicate_json_members_are_rejected(self):
        run = self.execution["runs"][1]
        raw = (self.root / "chromium.json").read_bytes()
        run["receipt"] = self.write_bytes("chromium.json", raw.replace(b'{', b'{"run_id":"stale",', 1))
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            self.report()

    def test_hash_mismatch_and_symlink_evidence_fail_closed(self):
        (self.root / "raw.log").write_text("changed raw evidence")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.report()
        (self.root / "real.log").write_bytes(b"synthetic infrastructure evidence\n")
        (self.root / "raw.log").unlink()
        (self.root / "raw.log").symlink_to(self.root / "real.log")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.report()


if __name__ == "__main__":
    unittest.main()
