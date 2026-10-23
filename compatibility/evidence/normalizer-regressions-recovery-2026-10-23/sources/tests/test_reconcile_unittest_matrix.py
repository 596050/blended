"""Evidence-consumer regressions, not additional Blender feature tests.

The fixture starts with a small immutable original execution. Mutated copies
exercise integrity, completion and denominator failures without changing any
published observation. The image-codec regression uses its real raw receipts.
"""
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import unittest

from tools.reconcile_unittest_matrix import (
    BROWSER, NATIVE, POLICY, CI_PRODUCER_FILES, Captured, Evidence,
    check_browser, check_producer_matrix, driver_blockers, normalize_outcomes,
    process_observation, read_contexts, reconcile,
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
CI_CONTEXT = Path("compatibility/evidence/runtime-context-source-build-39986612484")
CI_MATRIX = Path("compatibility/evidence/source-rebuild-unittest-39986612484")


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


class ExactEvidencePathMapTests(unittest.TestCase):
    """New post-recovery checks, not recovered copies of the lost test file."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.root = self.workspace / "checkout"
        self.root.mkdir()
        self.target = self.root / "retained/result.json"
        self.target.parent.mkdir()
        self.target.write_bytes(b'{"observed": true}\n')
        self.original = "/home/runner/work/project/artifacts/result.json"
        self.row = {"original_path": self.original, "path": "retained/result.json"}
        refresh_pin(self.row, self.target)
        self.mapping = {"schema": 1, "kind": "exact-evidence-path-map", "entries": [self.row]}
        self.map_path = self.root / "path-map.json"
        self.sequence = 0

    def evidence(self):
        self.sequence += 1
        write(self.map_path, self.mapping)
        return Evidence(self.root, self.workspace / ("normalized-" + str(self.sequence)), self.map_path)

    def test_exact_mapping_preserves_bytes_and_binds_both_origins(self):
        evidence = self.evidence()
        actual = evidence.reference({"path": self.original, "bytes": self.row["bytes"], "sha256": self.row["sha256"]})
        self.assertEqual(actual.data, self.target.read_bytes())
        self.assertEqual(actual.path, self.target)
        self.assertEqual(evidence.used_path_mappings[self.original]["raw_evidence"], actual.ref)
        self.assertEqual(evidence.origins[self.row["path"]], actual.ref)
        self.assertEqual((evidence.output / actual.ref["path"]).read_bytes(), self.target.read_bytes())

    def test_duplicate_original_cannot_select_between_two_retained_files(self):
        other = self.root / "retained/other.json"
        other.write_bytes(self.target.read_bytes())
        self.mapping["entries"].append({**self.row, "path": "retained/other.json"})
        with self.assertRaisesRegex(ValueError, "duplicate or ambiguous"):
            self.evidence()

    def test_duplicate_target_cannot_alias_two_historical_files(self):
        self.mapping["entries"].append({**self.row, "original_path": "/different/result.json"})
        with self.assertRaisesRegex(ValueError, "duplicate or ambiguous"):
            self.evidence()

    def test_noncanonical_absolute_and_relative_paths_are_rejected(self):
        original, target = self.row["original_path"], self.row["path"]
        for field, names in (
            ("original_path", ["//host/result.json", "/a/../result.json", "/a/./result.json",
                               "/a//result.json", "relative/result.json", "/", "/a\\result.json", "/a/\nresult.json"]),
            ("path", ["/retained/result.json", "../result.json", "retained/../result.json",
                      "retained/./result.json", "retained//result.json", "retained/result.json/",
                      "retained\\result.json", "retained/\x7fresult.json"]),
        ):
            for name in names:
                with self.subTest(field=field, name=repr(name)):
                    self.row.update(original_path=original, path=target)
                    self.row[field] = name
                    with self.assertRaisesRegex(ValueError, "map path"):
                        self.evidence()

    def test_mapping_cannot_shadow_a_current_checkout_path(self):
        self.row["original_path"] = str(self.root / "retained/result.json")
        with self.assertRaisesRegex(ValueError, "shadow a current repository path"):
            self.evidence()

    def test_symlink_target_is_rejected_even_when_bytes_match(self):
        outside = self.workspace / "outside.json"
        outside.write_bytes(self.target.read_bytes())
        self.target.unlink()
        self.target.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink evidence"):
            self.evidence()

    def test_symlink_parent_is_rejected_even_when_target_returns_inside_root(self):
        alias = self.root / "alias"
        alias.symlink_to(self.target.parent, target_is_directory=True)
        self.row["path"] = "alias/result.json"
        with self.assertRaisesRegex(ValueError, "symlink evidence"):
            self.evidence()

    def test_every_mapping_is_checked_before_any_selected_capture(self):
        other = self.root / "retained/unused.json"
        other.write_bytes(b"corrupt unused bytes\n")
        self.mapping["entries"].append({**self.row, "original_path": "/unused/result.json", "path": "retained/unused.json"})
        with self.assertRaisesRegex(ValueError, "exact evidence map identity mismatch"):
            self.evidence()

    def test_changed_target_is_rechecked_after_map_loading(self):
        evidence = self.evidence()
        self.target.write_bytes(b'{"observed":false}\n')
        for path in (self.original, self.row["path"]):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "exact evidence map identity mismatch"):
                evidence.capture(path)

    def test_map_does_not_replace_a_callers_independent_digest_or_size(self):
        evidence = self.evidence()
        pin = {"path": self.original, "bytes": self.row["bytes"], "sha256": self.row["sha256"]}
        for changed in ({"sha256": "0" * 64}, {"bytes": self.row["bytes"] + 1}):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, "input (hash|byte count) mismatch"):
                evidence.reference({**pin, **changed})

    def test_boolean_schema_and_byte_count_do_not_pass_integer_validation(self):
        self.mapping["schema"] = True
        with self.assertRaisesRegex(ValueError, "invalid exact evidence path map"):
            self.evidence()
        self.mapping["schema"] = 1
        self.row["bytes"] = True
        with self.assertRaisesRegex(ValueError, "byte count"):
            self.evidence()

    def test_no_basename_guessing_is_added_for_unmapped_paths(self):
        evidence = self.evidence()
        with self.assertRaisesRegex(ValueError, "external evidence path is not relocatable"):
            evidence.capture("/unmapped/result.json")

    def test_existing_compatibility_relocation_remains_available_without_a_map(self):
        path = self.root / "compatibility/retained/result.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(self.target.read_bytes())
        evidence = Evidence(self.root, self.workspace / "legacy-relocation")
        captured = evidence.capture("/former/checkout/compatibility/retained/result.json")
        self.assertEqual(captured.path, path)
        self.assertEqual(captured.data, self.target.read_bytes())
        self.assertIsNone(evidence.path_map_ref)


class MissingExecutionObservationTests(unittest.TestCase):
    """A failed producer without a payload must retain the native denominator."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.fixture = Fixture(self.workspace / "checkout", "imbuf_py_api")
        self.log = self.fixture.root / MATRIX / self.fixture.name / "browser.log"
        self.original_log = self.log.read_bytes()
        self.log.write_bytes(b"\n".join(line for line in self.original_log.splitlines()
                                      if not line.startswith((b"log BLENDED_QUALIFICATION_", b"BLENDED_QUALIFICATION_"))) + b"\n")
        self.fixture.browser.update(execution=None, status="failed", selected_suites_passed=False, summary=None)
        self.fixture.browser["execution_mode"]["runtime_exit_code"] = None
        self.fixture.browser["transport"]["result_markers"] = 0
        self.fixture.matrix_row.update(browser_state="failed", browser_summary=None)
        self.fixture.save_browser(update_log=False)
        self.output = self.workspace / "normalized"

    def test_absent_original_payload_keeps_all_eighty_parents_and_fifty_seven_subtests_missing(self):
        report = self.fixture.run(self.output)
        self.assertEqual(report["paired_obligation_count"], 80)
        self.assertEqual(report["observation_totals"]["browser"]["missing_outcomes"], 80)
        self.assertEqual(report["missing_browser_subtest_count"], 57)
        self.assertEqual(report["unexpected_browser_subtest_count"], 0)
        self.assertEqual(report["successful_execution_pair_count"], 0)
        self.assertEqual(report["outcome_agreement_count"], 0)
        self.assertTrue(all(pair["browser_outcome"] == "missing" for pair in report["pairs"]))
        receipt = read(self.output / "receipts" / str(self.fixture.index) / (BROWSER + ".json"))
        self.assertEqual(receipt["cases"], [])
        self.assertFalse(receipt["process"]["completed"])
        self.assertIsNone(receipt["process"]["exit_code"])
        self.assertIn("missing_execution_observation", receipt["validation_blockers"])
        self.assertIn("actual_runtime_process_completion_not_observed", receipt["validation_blockers"])

    def test_null_payload_cannot_claim_success_in_any_producer_summary(self):
        for field, value in (("status", "passed"), ("selected_suites_passed", True), ("summary", {})):
            with self.subTest(field=field):
                original = self.fixture.browser[field]
                self.fixture.browser[field] = value
                self.fixture.save_browser(update_log=False)
                with self.assertRaisesRegex(ValueError, "missing execution observation contradicts"):
                    self.fixture.run(self.workspace / ("contradiction-" + field))
                self.fixture.browser[field] = original
        self.fixture.save_browser(update_log=False)
        self.fixture.matrix_row["browser_state"] = "passed"
        self.fixture.save_indexes()
        with self.assertRaisesRegex(ValueError, "missing execution observation contradicts"):
            self.fixture.run(self.output)

    def test_null_payload_cannot_discard_an_actual_original_payload_in_the_log(self):
        self.log.write_bytes(self.original_log)
        with self.assertRaisesRegex(ValueError, "original payload log"):
            self.fixture.run(self.output)

    def test_a_null_marker_is_still_an_observation_and_cannot_mean_no_payload(self):
        with self.log.open("ab") as stream:
            stream.write(b"log BLENDED_QUALIFICATION_abcd:null\n")
        with self.assertRaisesRegex(ValueError, "original payload log"):
            self.fixture.run(self.output)

    def test_absent_field_and_malformed_nonnull_payload_are_not_accepted_as_null(self):
        for label, value in (("list", []), ("string", "missing"), ("boolean", False), ("absent", None)):
            with self.subTest(label=label):
                if label == "absent":
                    self.fixture.browser.pop("execution")
                else:
                    self.fixture.browser["execution"] = value
                self.fixture.save_browser(update_log=False)
                with self.assertRaisesRegex(ValueError, "execution observation is malformed"):
                    self.fixture.run(self.workspace / ("malformed-" + label))

    def test_null_payload_still_requires_the_bound_engine_artifact(self):
        self.fixture.browser["artifact"]["observed_sha256"] = "0" * 64
        self.fixture.save_browser(update_log=False)
        with self.assertRaisesRegex(ValueError, "another engine artifact"):
            self.fixture.run(self.output)

    def test_null_payload_still_rejects_a_hidden_host_selection_filter(self):
        self.fixture.host["command"].extend(["--cohort", "passing-subset"])
        self.fixture.save_host()
        with self.assertRaisesRegex(ValueError, "unreviewed argument or selection"):
            self.fixture.run(self.output)


class FrozenCIProducerCompatibilityTests(unittest.TestCase):
    """Verify the recovered source rule against real immutable CI producer bytes."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.root = self.workspace / "checkout"
        self.root.mkdir()
        for relative in (CONTEXT, CI_CONTEXT, CI_MATRIX / "main/harness"):
            shutil.copytree(ROOT / relative, self.root / relative)
        for relative in (CI_MATRIX / "main/matrix.json", CI_MATRIX / "resources/matrix.json",
                         MANIFESTS / "bl_animation_bake.json"):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, self.root / relative)
        self.context_file = self.root / CI_CONTEXT / "browser-context.json"
        self.context_value = read(self.context_file)
        self.producer_file = self.root / CI_CONTEXT / "producer-context.json"
        self.producer_value = read(self.producer_file)
        self.matrix_path = CI_MATRIX / "main/matrix.json"
        self.matrix = read(self.root / self.matrix_path)
        self.row = next(row for row in self.matrix["registrations"] if row.get("ctest_name") == "bl_animation_bake")
        self.browser = read(ROOT / CI_MATRIX / "main/bl_animation_bake/qualification.json")
        self.host = read(ROOT / CI_MATRIX / "main/bl_animation_bake/host-process.json")
        self.sequence = 0

    def save_producer(self):
        write(self.producer_file, self.producer_value)
        refresh_pin(self.context_value["source_derived_producer_context"], self.producer_file)
        write(self.context_file, self.context_value)

    def context(self):
        self.sequence += 1
        evidence = Evidence(self.root, self.workspace / ("captured-" + str(self.sequence)))
        adapter_sha = hashlib.sha256((ROOT / "tools/reconcile_unittest_matrix.py").read_bytes()).hexdigest()
        context = read_contexts(evidence, CONTEXT / "native-context.json", CI_CONTEXT / "browser-context.json", adapter_sha)
        return evidence, context

    def observation(self, evidence, context):
        captured = evidence.capture(self.matrix_path)
        harness = {name: evidence.capture(CI_MATRIX / "main/harness" / name)
                   for name, _, _ in CI_PRODUCER_FILES.values() if name.startswith("tools/")}
        mode = check_producer_matrix(context["producer"], captured, self.matrix, harness)
        return {"matrix": self.matrix, "row": self.row, "producer_mode": mode,
                "manifest_retained_path": (MANIFESTS / "bl_animation_bake.json").as_posix()}

    def check(self):
        evidence, context = self.context()
        observation = self.observation(evidence, context)
        manifest = evidence.capture(MANIFESTS / "bl_animation_bake.json")
        check_browser(self.browser, self.host, observation, manifest, context)
        return evidence, context, observation, manifest

    def test_actual_frozen_download_command_is_accepted_without_claiming_os_observed_cwd(self):
        _, context, observation, _ = self.check()
        self.assertEqual(context["producer"]["checkout_root"], PurePosixPath("/home/runner/work/blended/blended"))
        self.assertFalse(self.producer_value["os_cwd_observed"])
        self.assertIn("not an OS-observed cwd", observation["producer_mode"]["cwd_basis"])
        self.assertNotIn("--suite", self.host["command"])
        self.assertEqual(context["producer"]["run"]["id"], 39986612484)

    def test_even_self_consistent_repinning_cannot_change_a_frozen_source(self):
        original_context = copy.deepcopy(self.context_value)
        original_producer = copy.deepcopy(self.producer_value)
        for field in ("workflow", "matrix_driver", "probe"):
            with self.subTest(field=field):
                self.context_value = copy.deepcopy(original_context)
                self.producer_value = copy.deepcopy(original_producer)
                relative = (CI_CONTEXT / "browser-source-build.yml" if field == "workflow"
                            else CI_MATRIX / "main/harness" / CI_PRODUCER_FILES[field][0])
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b"\n# changed producer bytes\n")
                refresh_pin(self.producer_value[field], path)
                self.save_producer()
                with self.assertRaisesRegex(ValueError, "reviewed exact workflow and source pair"):
                    self.context()
                path.write_bytes(original)

    def test_unreviewed_context_claims_cannot_expand_the_source_rule(self):
        for field, value in (("os_cwd_observed", True), ("source_commit", "0" * 40),
                             ("rule", "generic-downloaded-sources"), ("schema", True)):
            with self.subTest(field=field):
                original = self.producer_value[field]
                self.producer_value[field] = value
                self.save_producer()
                with self.assertRaisesRegex(ValueError, "unreviewed source-derived producer"):
                    self.context()
                self.producer_value[field] = original

    def test_run_binding_rejects_incomplete_or_different_workflow_even_when_rehashed(self):
        path = self.root / CI_CONTEXT / "ci-run.json"
        original = read(path)
        for field, value in (("status", "in_progress"), ("head_sha", "0" * 40),
                             ("path", ".github/workflows/other.yml"), ("id", 39986612485)):
            with self.subTest(field=field):
                write(path, {**original, field: value})
                refresh_pin(self.producer_value["ci_run"], path)
                self.save_producer()
                with self.assertRaisesRegex(ValueError, "completed exact workflow run"):
                    self.context()

    def test_unbound_matrix_digest_cannot_reuse_a_known_checkout(self):
        evidence, context = self.context()
        captured = evidence.capture(self.matrix_path)
        captured.ref["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "lacks an exact source-derived producer binding"):
            check_producer_matrix(context["producer"], captured, self.matrix, {})

    def test_matrix_execution_paths_browser_and_concurrency_are_exact(self):
        evidence, context = self.context()
        captured = evidence.capture(self.matrix_path)
        for field, key, value in (("native_inventory", "path", "/other/native-discovery-inventory.json"),
                                  ("asset", "path", "/other/blender-source-development-essentials.tar.gz"),
                                  ("browser_executable", "path", "/other/google/chrome/chrome"),
                                  ("jobs", None, 2), ("jobs", None, True)):
            with self.subTest(field=field, value=value):
                matrix = copy.deepcopy(self.matrix)
                if key:
                    matrix[field][key] = value
                else:
                    matrix[field] = value
                with self.assertRaisesRegex(ValueError, "exact (checkout|workflow)"):
                    check_producer_matrix(context["producer"], captured, matrix, {})

    def test_matrix_completion_must_fit_within_the_bound_workflow_interval(self):
        evidence, context = self.context()
        captured = evidence.capture(self.matrix_path)
        matrix = copy.deepcopy(self.matrix)
        matrix["finished_utc"] = "2099-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "outside its bound workflow run interval"):
            check_producer_matrix(context["producer"], captured, matrix, {})

    def test_harness_basename_cannot_replace_exact_frozen_bytes(self):
        evidence, context = self.context()
        captured = evidence.capture(self.matrix_path)
        harness = {name: evidence.capture(CI_MATRIX / "main/harness" / name)
                   for name, _, _ in CI_PRODUCER_FILES.values() if name.startswith("tools/")}
        harness["tools/probe_browser_port.py"].data += b"\n# changed runtime producer\n"
        with self.assertRaisesRegex(ValueError, "matrix harness differs"):
            check_producer_matrix(context["producer"], captured, self.matrix, harness)

    def test_download_command_requires_the_whole_literal_expansion(self):
        evidence, context = self.context()
        observation = self.observation(evidence, context)
        manifest = evidence.capture(MANIFESTS / "bl_animation_bake.json")
        original = self.host["command"]
        changed_commands = []
        for flag, value in (("--asset", "/different/blender-source-development-essentials.tar.gz"),
                            ("--timeout", "241"), ("--output", original[original.index("--output") + 1] + "-retry")):
            command = original.copy()
            command[command.index(flag) + 1] = value
            changed_commands.append(command)
        changed_commands.append(original + ["--suite", "/source/tests/python/bl_animation_bake.py"])
        changed_commands.append(original[:2] + original[4:6] + original[2:4] + original[6:])
        for command in changed_commands:
            with self.subTest(command=command):
                host = {**self.host, "command": command}
                with self.assertRaisesRegex(ValueError, "source-derived producer command differs"):
                    check_browser(self.browser, host, observation, manifest, context)

    def test_unbound_producer_cannot_infer_downloaded_source_mode_from_a_similar_command(self):
        evidence, context = self.context()
        observation = self.observation(evidence, context)
        observation["producer_mode"] = None
        observation["matrix"] = copy.deepcopy(self.matrix)
        observation["matrix"]["asset"]["path"] = self.host["command"][self.host["command"].index("--asset") + 1]
        manifest = evidence.capture(MANIFESTS / "bl_animation_bake.json")
        with self.assertRaisesRegex(ValueError, "omits or substitutes an original source file"):
            check_browser(self.browser, self.host, observation, manifest, context)

    def test_downloaded_sources_still_require_the_original_source_digest(self):
        self.browser["suite_sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source"):
            self.check()


if __name__ == "__main__":
    unittest.main()
