"""Evidence-consumer regressions, not additional Blender feature tests.

The fixture starts with a small immutable original execution. Mutated copies
exercise integrity, completion and denominator failures without changing any
published observation. The image-codec regression uses its real raw receipts.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.reconcile_unittest_matrix import (
    BROWSER, NATIVE, POLICY, driver_blockers, normalize_outcomes, process_observation, reconcile,
)
from tools.test_parity_ledger import assess, canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
BASE = Path("compatibility/evidence/unittest-native-5.2-2026-10-23")
MATRIX = Path("compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23")
CONTEXT = Path("compatibility/evidence/runtime-context-2026-10-23")
OVERLAY_MATRIX = Path("compatibility/evidence/unittest-browser-essentials-5.2-2026-10-23")
OVERLAY_CONTEXT = Path("compatibility/evidence/runtime-context-essentials-2026-10-23")
OVERLAY_PACKAGE = Path("compatibility/evidence/brush-package-overlay-5.2-2026-10-23")
MANIFESTS = Path("compatibility/candidate-suites/unittest-main-5.2")


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def refresh_pin(pin, path):
    data = Path(path).read_bytes()
    pin.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


class Fixture:
    def __init__(self, root, name="bl_animation_bake", overlay=False):
        self.root, self.name = root, name
        self.matrix_path = OVERLAY_MATRIX if overlay else MATRIX
        self.context_path = OVERLAY_CONTEXT if overlay else CONTEXT
        matrix_path = self.matrix_path
        root.mkdir()
        for relative in (CONTEXT, BASE / name, matrix_path / name, matrix_path / "harness"):
            shutil.copytree(ROOT / relative, root / relative)
        if overlay:
            shutil.copytree(ROOT / OVERLAY_CONTEXT, root / OVERLAY_CONTEXT)
        extra = (matrix_path / "package-overlay.json", OVERLAY_PACKAGE / "package-overlay.json") if overlay else ()
        for relative in (MANIFESTS / (name + ".json"), matrix_path / "source-build.json", matrix_path / "harness-manifest.json", *extra):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, root / relative)
        self.plan = read(ROOT / BASE / "discovery-inventory.json")
        chosen = next(row for row in self.plan["registrations"] if row.get("ctest_name") == name)
        self.index = chosen["source_declaration_index"]
        # Keep every authentic declaration. Synthetic infrastructure fixtures
        # execute only this copied invocation; all other obligations stay blocked.
        for row in self.plan["registrations"]:
            if row is not chosen:
                row.update(state="blocked", reason="Synthetic infrastructure fixture omits this execution.")
                for field in ("manifest", "native_receipt", "expected_cases", "native_exit_code", "native_status"):
                    row.pop(field, None)
        self.plan["declaration_counts"] = {"blocked": 131, "native_inventory_frozen": 1}
        self.matrix = read(ROOT / matrix_path / "matrix.json")
        for row in self.matrix["registrations"]:
            if row["source_declaration_index"] != self.index:
                row.update(state="blocked", browser_state="blocked_before_browser_execution")
                for field in ("manifest", "host_process", "browser_receipt", "expected_cases", "browser_summary"):
                    row.pop(field, None)
        self.matrix_row = next(row for row in self.matrix["registrations"] if row["source_declaration_index"] == self.index)
        self.plan_row = chosen
        self.native = read(root / BASE / name / "native_reference.json")
        self.browser = read(root / matrix_path / name / "qualification.json")
        self.host = read(root / matrix_path / name / "host-process.json")
        self.manifest = read(root / MANIFESTS / (name + ".json"))
        self.save_indexes()

    def save_indexes(self):
        path = self.root / BASE / "discovery-inventory.json"
        write(path, self.plan)
        shutil.copyfile(path, self.root / self.matrix_path / "native-discovery-inventory.json")
        refresh_pin(self.matrix["native_inventory"], path)
        write(self.root / self.matrix_path / "matrix.json", self.matrix)

    def replace_observation(self, native):
        path = self.root / (BASE if native else self.matrix_path) / self.name / ("native-reference.log" if native else "browser.log")
        prefix = "BLENDED_NATIVE_REFERENCE_" if native else "log BLENDED_QUALIFICATION_"
        report = self.native if native else self.browser
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.startswith(prefix):
                lines[i] = line[:line.index(":") + 1] + json.dumps(report["execution"], sort_keys=True)
        path.write_text("\n".join(lines) + "\n")
        if native:
            refresh_pin(report["log"], path)

    def save_browser(self, update_log=True):
        if update_log:
            self.replace_observation(False)
        path = self.root / self.matrix_path / self.name / "qualification.json"
        write(path, self.browser)
        refresh_pin(self.matrix_row["browser_receipt"], path)
        self.save_indexes()

    def save_host(self):
        path = self.root / self.matrix_path / self.name / "host-process.json"
        write(path, self.host)
        refresh_pin(self.matrix_row["host_process"], path)
        self.save_indexes()

    def save_native(self):
        self.replace_observation(True)
        path = self.root / BASE / self.name / "native_reference.json"
        write(path, self.native)
        refresh_pin(self.plan_row["native_receipt"], path)
        refresh_pin(self.manifest["native_discovery"], path)
        manifest_path = self.root / MANIFESTS / (self.name + ".json")
        write(manifest_path, self.manifest)
        refresh_pin(self.plan_row["manifest"], manifest_path)
        refresh_pin(self.matrix_row["manifest"], manifest_path)
        self.browser["cohort"]["native_discovery"] = copy.deepcopy(self.manifest["native_discovery"])
        self.browser["cohort"]["manifest_sha256"] = self.plan_row["manifest"]["sha256"]
        command = self.host["command"]
        command[command.index("--suite-manifest-sha256") + 1] = self.plan_row["manifest"]["sha256"]
        self.save_host()
        self.save_browser()

    def run(self, output, root=None):
        return reconcile(root or self.root, BASE / "discovery-inventory.json", [self.matrix_path / "matrix.json"],
                         CONTEXT / "native-context.json", self.context_path / "browser-context.json", output)


class ReconcileMatrixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.fixture = Fixture(self.workspace / "checkout")
        self.output = self.workspace / "normalized"

    def test_actual_complete_selected_script_and_unexpanded_declaration_remain_distinct(self):
        report = self.fixture.run(self.output)
        self.assertEqual(report["required_registration_count"], 132)
        self.assertEqual(report["unresolved_registration_count"], 131)
        self.assertEqual(report["paired_obligation_count"], 5)
        self.assertEqual(report["successful_execution_pair_count"], 5)
        self.assertEqual(report["outcome_agreement_count"], 5)
        self.assertFalse(report["declared_scope_test_parity"])
        self.assertFalse(report["all_upstream_test_parity"])
        self.assertFalse(report["full_feature_parity"])
        receipt = read(self.output / "receipts" / str(self.fixture.index) / (BROWSER + ".json"))
        self.assertEqual(receipt["producer"]["runner_sha256"], self.fixture.browser["runner_sha256"])
        self.assertNotEqual(receipt["context"]["adapter_sha256"], receipt["producer"]["runner_sha256"])

    def test_conversion_and_receipt_consumption_are_reproducible_after_checkout_relocation(self):
        first = self.fixture.run(self.output)
        clone = self.workspace / "another-checkout"
        shutil.copytree(self.fixture.root, clone)
        second_output = self.workspace / "second-normalized"
        second = self.fixture.run(second_output, root=clone)
        self.assertEqual(first, second)
        for relative in ("contract.json", "inventory.json", "executions.json", "conversion.json"):
            self.assertEqual((self.output / relative).read_bytes(), (second_output / relative).read_bytes())
        standalone = self.workspace / "standalone-bundle"
        shutil.copytree(self.output, standalone)
        independently_read = assess(read(standalone / "contract.json"), read(standalone / "inventory.json"),
                                    read(standalone / "executions.json"), standalone)
        self.assertEqual(independently_read["pairs"], first["pairs"])

    def test_host_exit_zero_cannot_supply_a_missing_wasm_exit(self):
        self.fixture.browser["execution_mode"]["runtime_exit_code"] = None
        self.fixture.save_browser()
        report = self.fixture.run(self.output)
        self.assertEqual(report["observation_totals"]["browser"]["passed"], 5)
        self.assertEqual(report["successful_execution_pair_count"], 0)
        self.assertEqual(report["outcome_agreement_count"], 0)
        self.assertIn("browser_process_incomplete_or_failed", report["pairs"][0]["blockers"])

    def test_base_plan_cannot_drop_an_unexpanded_literal_declaration(self):
        self.fixture.plan["registrations"].pop(0)
        self.fixture.save_indexes()
        with self.assertRaisesRegex(ValueError, "complete pinned declaration set"):
            self.fixture.run(self.output)

    def test_self_consistent_changed_source_declaration_cannot_create_original_authority(self):
        self.fixture.plan_row["registration"] = self.fixture.plan_row["registration"].replace(".py", ".py -- -kOnlyPassing")
        self.fixture.save_indexes()
        with self.assertRaisesRegex(ValueError, "independently pinned CMake declaration"):
            self.fixture.run(self.output)

    def test_boolean_is_not_an_actual_process_return_code(self):
        self.fixture.browser["execution_mode"]["runtime_exit_code"] = False
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "runtime exit must be an integer"):
            self.fixture.run(self.output)

    def test_legitimate_boolean_original_system_exit_is_distinct_from_process_status(self):
        result = copy.deepcopy(self.fixture.browser["execution"])
        result["driver_observation"]["original_exit_code"] = False
        self.assertEqual(driver_blockers(result, self.fixture.manifest), [])
        process = process_observation(self.fixture.browser, self.fixture.host)
        self.assertTrue(process["completed"])
        self.assertIs(type(process["exit_code"]), int)

    def test_preloader_exception_preserves_every_missing_native_case(self):
        result = self.fixture.browser["execution"]
        result.update(suites=[], exception="ModuleNotFoundError: missing runtime module")
        result["driver_observation"].update(runner_invocations=0, failfast=None)
        self.fixture.browser["execution_mode"]["runtime_exit_code"] = 1
        self.fixture.save_browser()
        report = self.fixture.run(self.output)
        self.assertEqual(report["paired_obligation_count"], 5)
        self.assertEqual(report["observation_totals"]["browser"]["missing_outcomes"], 5)
        self.assertEqual(report["observation_totals"]["browser"]["discovered"], 0)
        self.assertTrue(all(row["browser_outcome"] == "missing" for row in report["pairs"]))

    def test_partial_callback_vector_cannot_shrink_the_frozen_denominator(self):
        self.fixture.browser["execution"]["suites"][0]["outcomes"].pop()
        self.fixture.save_browser()
        report = self.fixture.run(self.output)
        self.assertEqual(report["paired_obligation_count"], 5)
        self.assertEqual(report["observation_totals"]["browser"]["passed"], 4)
        self.assertEqual(report["observation_totals"]["browser"]["missing_outcomes"], 1)
        self.assertEqual(report["successful_execution_pair_count"], 4)

    def test_original_failure_counter_blocks_contradictory_all_pass_callbacks(self):
        self.fixture.browser["execution"]["suites"][0]["failures"] = 1
        self.fixture.save_browser()
        report = self.fixture.run(self.output)
        self.assertEqual(report["observation_totals"]["browser"]["passed"], 5)
        self.assertEqual(report["successful_execution_pair_count"], 0)
        self.assertEqual(report["outcome_agreement_count"], 0)
        self.assertIn("browser_validation:original_unittest_counters_disagree_with_outcome_events",
                      report["pairs"][0]["blockers"])

    def test_matched_expected_failure_is_agreement_and_never_functional_pass(self):
        for raw in (self.fixture.native, self.fixture.browser):
            suite = raw["execution"]["suites"][0]
            suite["outcomes"][0].update(status="expected_failure", detail="AssertionError: same original expected failure\n")
            suite["expected_failures"] = 1
        self.fixture.save_native()
        report = self.fixture.run(self.output)
        self.assertEqual(report["outcome_agreement_count"], 5)
        self.assertEqual(report["successful_execution_pair_count"], 4)
        failed = next(row for row in report["pairs"] if row["native_outcome"] == "expected_failure")
        self.assertTrue(failed["outcome_agreement"])
        self.assertFalse(failed["successful_execution"])

    def test_subtest_only_success_does_not_fabricate_a_parent_pass(self):
        result = copy.deepcopy(self.fixture.native["execution"])
        suite = result["suites"][0]
        parent = suite["outcomes"][0]
        parent.update(kind="subtest", parent_id=parent["id"], id=parent["id"] + " (value=1)")
        cases, counts, _ = normalize_outcomes(result, self.fixture.manifest, canonical_sha256(POLICY))
        self.assertEqual(len(cases), 4)
        self.assertEqual(counts["missing_outcomes"], 1)

    def test_duplicate_parameter_identity_is_not_silently_deduplicated(self):
        result = copy.deepcopy(self.fixture.native["execution"])
        parent = result["suites"][0]["outcomes"][0]["id"]
        event = {"kind": "subtest", "parent_id": parent, "id": parent + " (value=1)", "status": "passed", "detail": None}
        result["suites"][0]["outcomes"].extend([event, copy.deepcopy(event)])
        with self.assertRaisesRegex(ValueError, "duplicate subtest identity"):
            normalize_outcomes(result, self.fixture.manifest, canonical_sha256(POLICY))

    def test_same_parent_passes_cannot_hide_fourteen_missing_real_codec_subtests(self):
        fixture = Fixture(self.workspace / "codec-checkout", "imbuf_py_api")
        report = fixture.run(self.output)
        self.assertEqual(report["paired_obligation_count"], 80)
        self.assertEqual(report["missing_browser_subtest_count"], 14)
        self.assertEqual(report["unexpected_browser_subtest_count"], 0)
        parent = next(row for row in report["pairs"] if row["case_id"].endswith("TestImBufFileTypes.test_file_types_have_id_and_extensions"))
        self.assertEqual((parent["native_outcome"], parent["browser_outcome"]), ("passed", "passed"))
        self.assertFalse(parent["outcome_agreement"])
        self.assertIn("outcome_or_subtest_disagreement", parent["blockers"])

    def test_wrong_runtime_profile_is_rejected_even_with_valid_file_hashes(self):
        self.fixture.browser["profile"] = "native-reference"
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "another runtime profile"):
            self.fixture.run(self.output)

    def test_browser_cannot_substitute_another_frozen_manifest(self):
        self.fixture.browser["cohort"]["manifest_sha256"] = "a" * 64
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "manifest binding differs"):
            self.fixture.run(self.output)

    def test_observed_script_argv_cannot_drop_original_flags(self):
        self.fixture.browser["execution"]["execution_context"]["script_argv"].remove("--debug-exit-on-error")
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "script argv differs"):
            self.fixture.run(self.output)

    def test_hash_valid_report_must_match_its_raw_execution_log(self):
        self.fixture.browser["execution"]["suites"][0]["outcomes"][0]["status"] = "failed"
        self.fixture.save_browser(update_log=False)
        with self.assertRaisesRegex(ValueError, "single original log observation"):
            self.fixture.run(self.output)

    def test_stale_same_script_receipt_is_rejected_by_the_host_interval(self):
        self.fixture.browser["finished_utc"] = "2020-01-01T00:00:00+00:00"
        self.fixture.browser["started_utc"] = "2020-01-01T00:00:00+00:00"
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "stale or outside"):
            self.fixture.run(self.output)

    def test_host_command_must_name_the_measured_harness_snapshot(self):
        self.fixture.host["command"][1] = "/unrelated/harness/tools/probe_browser_port.py"
        self.fixture.save_host()
        with self.assertRaisesRegex(ValueError, "not the bound harness"):
            self.fixture.run(self.output)

    def test_host_command_cannot_add_a_hidden_selection_flag(self):
        self.fixture.host["command"].extend(["--cohort", "numeric"])
        self.fixture.save_host()
        with self.assertRaisesRegex(ValueError, "unreviewed argument or selection"):
            self.fixture.run(self.output)

    def test_absent_independent_build_configuration_is_not_replaced_by_a_hash(self):
        path = self.fixture.root / CONTEXT / "native-context.json"
        context = read(path)
        context["raw_evidence"] = []
        write(path, context)
        with self.assertRaisesRegex(ValueError, "not independently bound"):
            self.fixture.run(self.output)

    def test_symlink_input_cannot_escape_the_relocated_evidence_root(self):
        path = self.fixture.root / MATRIX / self.fixture.name / "qualification.json"
        outside = self.workspace / "external.json"
        shutil.copyfile(path, outside)
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink evidence"):
            self.fixture.run(self.output)

    def test_existing_output_is_never_overwritten(self):
        self.fixture.run(self.output)
        before = (self.output / "report.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "previous evidence is immutable"):
            self.fixture.run(self.output)
        self.assertEqual((self.output / "report.json").read_bytes(), before)


class PackageOverlayReconcileTests(unittest.TestCase):
    """Actual augmented brush execution remains distinct from its base package."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.fixture = Fixture(self.workspace / "checkout", "bl_brush", overlay=True)
        self.output = self.workspace / "normalized"
        self.context_file = self.fixture.root / OVERLAY_CONTEXT / "browser-context.json"
        self.context = read(self.context_file)
        self.measurement_file = self.fixture.root / OVERLAY_CONTEXT / "package-measurement.json"
        self.measurement = read(self.measurement_file)

    def save_context(self):
        write(self.context_file, self.context)

    def save_measurement(self):
        write(self.measurement_file, self.measurement)
        refresh_pin(self.context["package_overlay_measurement"], self.measurement_file)
        self.save_context()

    def test_actual_overlay_brush_results_bind_new_artifact_and_original_build_separately(self):
        report = self.fixture.run(self.output)
        self.assertEqual(report["paired_obligation_count"], 4)
        self.assertEqual(report["successful_execution_pair_count"], 4)
        self.assertFalse(report["full_feature_parity"])
        receipt = read(self.output / "receipts" / str(self.fixture.index) / (BROWSER + ".json"))
        self.assertEqual(receipt["context"]["artifact_sha256"], self.context["engine_archive"]["sha256"])
        self.assertNotEqual(receipt["context"]["artifact_sha256"], self.context["package_base_asset"]["sha256"])
        self.assertEqual(self.fixture.browser["source_build"]["receipt_sha256"],
                         self.context["source_build_receipt"]["sha256"])
        bound_hashes = {row["sha256"] for row in receipt["raw_evidence"]}
        self.assertIn(self.context["package_overlay_measurement"]["sha256"], bound_hashes)
        self.assertIn(self.context["package_overlay_receipt"]["sha256"], bound_hashes)

    def test_overlay_conversion_and_consumer_replay_survive_checkout_relocation(self):
        first = self.fixture.run(self.output)
        clone = self.workspace / "relocated"
        shutil.copytree(self.fixture.root, clone)
        second_output = self.workspace / "relocated-normalized"
        second = self.fixture.run(second_output, root=clone)
        self.assertEqual(first, second)
        self.assertEqual((self.output / "conversion.json").read_bytes(), (second_output / "conversion.json").read_bytes())
        independently_read = assess(read(second_output / "contract.json"), read(second_output / "inventory.json"),
                                    read(second_output / "executions.json"), second_output)
        self.assertEqual(independently_read["pairs"], first["pairs"])

    def test_overlay_receipt_alone_cannot_replace_independent_member_measurement(self):
        del self.context["package_overlay_measurement"]
        self.save_context()
        with self.assertRaisesRegex(ValueError, "requires receipt, base asset and independent measurement"):
            self.fixture.run(self.output)

    def test_present_verifier_file_does_not_replace_missing_measurement_tool_binding(self):
        del self.measurement["verification_tool"]
        self.save_measurement()
        with self.assertRaisesRegex(ValueError, "package verification tool identity is missing"):
            self.fixture.run(self.output)

    def test_changed_package_cannot_inherit_base_artifact_identity(self):
        self.context["engine_archive"] = copy.deepcopy(self.context["package_base_asset"])
        self.save_context()
        with self.assertRaisesRegex(ValueError, "select a distinct artifact"):
            self.fixture.run(self.output)

    def test_even_matching_measurement_and_browser_cannot_change_original_wasm(self):
        for entries in (self.measurement["engine_files"], self.fixture.browser["engine_files"]):
            next(row for row in entries if row["path"].endswith(".wasm"))["sha256"] = "a" * 64
        self.save_measurement()
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "retain Wasm and account"):
            self.fixture.run(self.output)

    def test_old_preload_hashes_cannot_be_reused_under_new_archive_identity(self):
        self.fixture.browser["engine_files"] = read(self.fixture.root / CONTEXT / "source-build.json")["engine_files"]
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "extracted engine files differ"):
            self.fixture.run(self.output)

    def test_self_consistent_altered_preload_length_does_not_hide_unaccounted_resources(self):
        for entries in (self.measurement["engine_files"], self.fixture.browser["engine_files"]):
            next(row for row in entries if row["path"].endswith(".data"))["bytes"] += 1
        self.save_measurement()
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "retain Wasm and account"):
            self.fixture.run(self.output)

    def test_browser_cannot_replace_source_receipt_with_overlay_receipt(self):
        self.fixture.browser["source_build"]["receipt_sha256"] = self.context["package_overlay_receipt"]["sha256"]
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "independently supplied source build"):
            self.fixture.run(self.output)

    def test_matrix_cannot_substitute_its_base_archive(self):
        self.fixture.matrix["package_base_asset"]["sha256"] = "b" * 64
        self.fixture.save_indexes()
        with self.assertRaisesRegex(ValueError, "matrix package overlay or base archive differs"):
            self.fixture.run(self.output)

    def test_host_must_actually_request_the_bound_overlay_receipt(self):
        command = self.fixture.host["command"]
        command[command.index("--package-overlay-receipt") + 1] = "/other/package-overlay.json"
        self.fixture.save_host()
        with self.assertRaisesRegex(ValueError, "host command substituted the package overlay"):
            self.fixture.run(self.output)

    def test_browser_must_report_verification_of_the_same_overlay(self):
        self.fixture.browser["package_overlay"]["receipt_sha256"] = "c" * 64
        self.fixture.save_browser()
        with self.assertRaisesRegex(ValueError, "did not independently verify the selected package overlay"):
            self.fixture.run(self.output)

    def test_hash_valid_overlay_cannot_add_an_unreviewed_resource(self):
        path = self.fixture.root / OVERLAY_PACKAGE / "package-overlay.json"
        receipt = read(path)
        receipt["additions"][0]["destination"] = "/bw/datafiles/unreviewed.blend"
        write(path, receipt)
        refresh_pin(self.context["package_overlay_receipt"], path)
        self.save_context()
        with self.assertRaisesRegex(ValueError, "independently reviewed resource plan"):
            self.fixture.run(self.output)


if __name__ == "__main__":
    unittest.main()
