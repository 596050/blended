"""New infrastructure regressions for retained original mesh evidence.

These tests consume captured original results and mutate temporary copies. They
do not run Blender, modify original tests, or create additional feature credit.
The source declarations and expected case IDs come from retained original
evidence, independently of the consumer under test.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import reconcile_original_mesh as mesh
from tools.test_parity_ledger import assess


ROOT = Path(__file__).resolve().parents[1]
SELECTORS = Path("compatibility/mesh-driver-profiles")
EVIDENCE = Path("compatibility/evidence")
BEVEL_SOURCE = EVIDENCE / "bmesh-bevel-source-native-5.2-2026-10-23"
BEVEL_NATIVE = EVIDENCE / "bmesh-bevel-source-native-elevated-5.2-2026-10-23"
BEVEL_BROWSER = EVIDENCE / "bmesh-bevel-browser-essentials-5.2-2026-10-23"
OPERATORS_SOURCE = EVIDENCE / "mesh-operators-source-native-5.2-2026-10-23"
OPERATORS_BROWSER = EVIDENCE / "mesh-operators-browser-essentials-5.2-2026-10-23"
HISTORICAL_ROOT = "/workspace/scratch/d63596d831b2/blended"
OLD_PROBE_SHA = "2dd05ff937337d861972e224c63639f90c471002eab496a1f2595853303672cd"
SAVED_PROBE = EVIDENCE / "source-rebuild-unittest-39986612484/main/harness/tools/probe_browser_port.py"


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def file_pin(path, recorded_path=None):
    data = Path(path).read_bytes()
    return {"path": recorded_path or str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def first_original_segment():
    text = (ROOT / BEVEL_NATIVE / "original-driver.log").read_text()
    start = text.index("START Cube_test_1 test.\n")
    end = text.index("START Cube_test_2 test.\n", start)
    return text[start:end]


class OriginalMeshParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.declarations = read(ROOT / BEVEL_SOURCE / "prospective-command.json")["static_declared_specs"]
        cls.segment = first_original_segment()

    def parse(self, text, declarations=None):
        return mesh.original_observations(text, declarations or self.declarations[:1])

    def test_actual_native_logs_equal_recorded_original_observations(self):
        for source, native in ((BEVEL_SOURCE, BEVEL_NATIVE), (OPERATORS_SOURCE, OPERATORS_SOURCE)):
            with self.subTest(source=source.name):
                declarations = read(ROOT / source / "prospective-command.json")["static_declared_specs"]
                expected = read(ROOT / native / "execution.json")["original_case_observations"]
                observed = self.parse((ROOT / native / "original-driver.log").read_text(), declarations)
                self.assertEqual(observed, expected)

    def test_real_operator_failures_preserve_original_oracle_text(self):
        declarations = read(ROOT / OPERATORS_SOURCE / "prospective-command.json")["static_declared_specs"]
        observed = self.parse((ROOT / OPERATORS_BROWSER / "attempt-01-elevated/original-stdout.log").read_text(),
                              declarations)
        self.assertEqual(observed["observed_starts"], 105)
        self.assertEqual(observed["observed_passes"], 103)
        failures = {row["name"]: row for row in observed["observations"] if row["status"] == "failed"}
        self.assertEqual(set(failures), {"IcosphereFill", "IcosphereFillUseBeautyFalse"})
        for row in failures.values():
            self.assertEqual(row["mesh_comparison"], ["The edge topology is different"])
            self.assertEqual(row["mesh_validation"], ["Valid"])
            self.assertNotEqual(row["status"], "expected_failure")

    def test_orphan_terminal_before_first_start_is_invalid(self):
        with self.assertRaisesRegex(ValueError, "orphan|mismatched"):
            self.parse("PASSED Cube_test_1 test successfully.\n" + self.segment)

    def test_terminal_for_another_known_case_cannot_hide_in_segment(self):
        for terminal in ("PASSED Cube_test_2 test successfully.\n",
                         "FAILED Cube_test_2 test with the following: \n"):
            with self.subTest(terminal=terminal), self.assertRaisesRegex(ValueError, "orphan|mismatched"):
                self.parse(self.segment + terminal, self.declarations[:2])

    def test_duplicate_and_contradictory_terminals_are_invalid(self):
        for terminal in ("PASSED Cube_test_1 test successfully.\n",
                         "FAILED Cube_test_1 test with the following: \n"):
            with self.subTest(terminal=terminal), self.assertRaisesRegex(ValueError, "duplicate|contradictory"):
                self.parse(self.segment + terminal)

    def test_missing_terminal_remains_incomplete(self):
        observed = self.parse(self.segment.replace("PASSED Cube_test_1 test successfully.\n", ""))
        self.assertEqual(observed["observed_starts"], 1)
        self.assertEqual(observed["observed_passes"], 0)
        self.assertEqual(observed["observed_ambiguous_or_incomplete"], 1)
        self.assertEqual(observed["observations"][0]["terminal_log_lines"], [])

    def test_pass_marker_requires_exact_original_comparison_and_validation(self):
        variants = [
            self.segment.replace("Mesh Comparison : Same\n", ""),
            self.segment.replace("Mesh Comparison : Same\n", "Mesh Comparison : Different\n"),
            self.segment.replace("Mesh Comparison : Same\n", "Mesh Comparison : Same\n" * 2),
            self.segment.replace("Mesh Validation : Valid\n", ""),
            self.segment.replace("Mesh Validation : Valid\n", "Mesh Validation : Invalid Mesh\n"),
            self.segment.replace("Mesh Validation : Valid\n", "Mesh Validation : Valid\n" * 2),
        ]
        for index, text in enumerate(variants):
            with self.subTest(index=index):
                observed = self.parse(text)
                self.assertEqual(observed["observed_passes"], 0)
                self.assertEqual(observed["observed_ambiguous_or_incomplete"], 1)

    def test_duplicate_start_is_retained_as_duplicate_observation(self):
        observed = self.parse(self.segment + self.segment)
        self.assertEqual(observed["observed_starts"], 2)
        self.assertEqual(observed["duplicate_names"], ["Cube_test_1"])
        self.assertEqual(len(observed["observations"]), 2)

    def test_missing_and_unexpected_original_names_do_not_disappear(self):
        missing = self.parse(self.segment, self.declarations[:2])
        self.assertEqual(missing["missing_declared_names"], ["Cube_test_2"])
        unexpected = self.parse(self.segment, self.declarations[1:2])
        self.assertEqual(unexpected["unexpected_names"], ["Cube_test_1"])
        self.assertNotIn("original_source_declaration", unexpected["observations"][0])

    def test_malformed_original_marker_is_invalid(self):
        for text in (self.segment.replace("START Cube_test_1 test.", "START Cube_test_1 test"),
                     self.segment.replace("PASSED Cube_test_1 test successfully.",
                                          "PASSED Cube_test_1 test successfully"),
                     self.segment.replace("PASSED Cube_test_1 test successfully.",
                                          "FAILED Cube_test_1 test with the following:")):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "malformed"):
                self.parse(text)

    def test_empty_log_does_not_promote_static_declarations(self):
        observed = self.parse("", self.declarations)
        self.assertEqual(observed["observations"], [])
        self.assertEqual(observed["observed_passes"], 0)
        self.assertEqual(set(observed["missing_declared_names"]), {row["name"] for row in self.declarations})


class OriginalMeshSourceTests(unittest.TestCase):
    def test_retained_original_declaration_details_match_exact_source_bytes(self):
        for source, script in ((BEVEL_SOURCE, "bevel_operator.py"), (OPERATORS_SOURCE, "operators.py")):
            with self.subTest(script=script):
                expected = read(ROOT / source / "prospective-command.json")["static_declared_specs"]
                payload = (ROOT / source / "source/tests/python" / script).read_bytes()
                self.assertEqual(mesh.static_specs(payload, "tests/python/" + script), expected)

    def test_source_inspection_does_not_execute_original_code(self):
        # This is an infrastructure-only source fixture. Its name belongs to the
        # first actual original case; it does not add a discovered Blender ID.
        payload = b"raise RuntimeError('must not execute')\ndef main():\n    tests = [SpecMeshTest('Cube_test_1', 'a', 'b', [])]\n"
        rows = mesh.static_specs(payload, "tests/python/bevel_operator.py")
        self.assertEqual([row["name"] for row in rows], ["Cube_test_1"])
        self.assertEqual(rows[0]["line"], 3)
        self.assertEqual(rows[0]["source_sha256"], hashlib.sha256(payload).hexdigest())

    def test_dynamic_or_ambiguous_declaration_shape_is_rejected(self):
        samples = (
            b"def main():\n    tests = make_tests()\n",
            b"def main():\n    tests = [SpecMeshTest(name, 'a', 'b', [])]\n",
            b"def main():\n    tests = [OtherTest('Cube_test_1')]\n",
            b"def main():\n    tests = []\n    tests = []\n",
            b"def main():\n    tests = []\ndef main():\n    tests = []\n",
            b"def main():\n    tests = [SpecMeshTest('Cube_test_1'), SpecMeshTest('Cube_test_1')]\n",
        )
        for payload in samples:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                mesh.static_specs(payload, "tests/python/bevel_operator.py")


class RuntimeFixture:
    """Decoded original observations, with mutations confined to memory."""

    def __init__(self, profile="bmesh-bevel-5.2"):
        definition = mesh.PROFILES[profile]
        source = ROOT / EVIDENCE / definition["source_dir"]
        attempt = ROOT / EVIDENCE / definition["browser_dir"] / definition["attempt"]
        original = read(source / "prospective-command.json")
        browser = read(attempt / "execution.json")
        self.values = {
            "profile": definition,
            "browser": browser,
            "events": [json.loads(line) for line in (attempt / "launcher-events.jsonl").read_text().splitlines()],
            "console": [json.loads(line) for line in (attempt / "browser-console.jsonl").read_text().splitlines()],
            "state": read(attempt / "browser-state.json"),
            "stdout": (attempt / "original-stdout.log").read_text(),
            "stderr": (attempt / "original-stderr.log").read_text(),
            "native": {key: original[key] for key in ("command", "cwd", "inputs")},
            "manifest": read(attempt / "input-manifest.json"),
            "observations": copy.deepcopy(browser["original_stdout_observations"]),
        }

    def event(self, kind):
        return next(row for row in self.values["events"] if row["kind"] == kind)

    def synchronize(self):
        """Keep copied transports consistent so semantic gates see mutations."""
        marker = self.values["profile"]["marker"]
        original_console = self.values["console"]
        template = copy.deepcopy(next(row for row in original_console if row["text"].startswith(marker)))
        console = [row for row in original_console if not row["text"].startswith(marker)]
        for index, row in enumerate(self.values["events"]):
            row["sequence"] = index
            console.append({**template, "text": marker + json.dumps(row)})
        self.values["console"] = console
        self.values["browser"]["observed_console_events"] = len(console)
        self.values["state"]["events"] = copy.deepcopy(self.values["events"])
        self.values["browser"]["runtime_state"] = copy.deepcopy(self.values["state"])
        for kind in ("stdout", "stderr"):
            self.values[kind] = "".join(row["detail"] + "\n" for row in self.values["events"] if row["kind"] == kind)

    def qualify_as_blocked(self, *failed_checks):
        browser = self.values["browser"]
        for name in failed_checks:
            browser["qualification_checks"][name] = False
        browser.update(qualified_original_invocation=False, qualified_original_browser_passes=0,
                       status="failed_or_blocked")

    def consume(self):
        return mesh.check_runtime_events(**self.values)


class OriginalMeshRuntimeEventTests(unittest.TestCase):
    def test_actual_event_streams_recompute_the_original_checks(self):
        for profile, failures in (("bmesh-bevel-5.2", []),
                                  ("operators-5.2", ["all_original_mesh_oracles_passed",
                                                    "exactly_one_successful_runtime_exit"])):
            with self.subTest(profile=profile):
                fixture = RuntimeFixture(profile)
                checks, blockers = fixture.consume()
                self.assertEqual(checks, fixture.values["browser"]["qualification_checks"])
                self.assertEqual(blockers, failures)

    def test_zero_chrome_exit_cannot_supply_a_missing_wasm_exit(self):
        fixture = RuntimeFixture()
        state, browser = fixture.values["state"], fixture.values["browser"]
        fixture.values["events"] = [row for row in fixture.values["events"] if row["kind"] != "runtime_exit"]
        state["runtimeExitCodes"] = []
        state.pop("actualArgvAtRuntimeExit")
        state["finished"] = False
        browser["timed_out"] = True
        browser["errors"] = ["TimeoutError: infrastructure mutation after original quit"]
        browser["original_quit_byte_observation_boundary_verified"] = False
        fixture.qualify_as_blocked("exactly_one_successful_runtime_exit", "original_command_observed_at_runtime_exit",
                                   "byte_observation_after_all_original_case_results_before_runtime_exit",
                                   "no_timeout", "no_host_or_page_errors")
        fixture.synchronize()
        checks, blockers = fixture.consume()
        self.assertEqual(browser["actual_chrome_process_returncode"], 0)
        self.assertEqual(fixture.values["observations"]["observed_passes"], 88)
        self.assertFalse(checks["exactly_one_successful_runtime_exit"])
        self.assertIn("single_final_runtime_exit_not_observed", blockers)
        self.assertIn("original_runtime_not_finished", blockers)

    def test_nonzero_and_negative_exit_preserve_observations_but_block_success(self):
        for code in (1, -1):
            with self.subTest(code=code):
                fixture = RuntimeFixture()
                fixture.event("runtime_exit")["detail"]["code"] = code
                fixture.values["state"]["runtimeExitCodes"] = [code]
                fixture.qualify_as_blocked("exactly_one_successful_runtime_exit")
                fixture.synchronize()
                checks, blockers = fixture.consume()
                self.assertEqual(fixture.values["observations"]["observed_passes"], 88)
                self.assertFalse(checks["exactly_one_successful_runtime_exit"])
                self.assertIn("exactly_one_successful_runtime_exit", blockers)

    def test_multiple_exit_observations_are_not_one_successful_exit(self):
        fixture = RuntimeFixture()
        duplicate = copy.deepcopy(fixture.event("runtime_exit"))
        fixture.values["events"].append(duplicate)
        fixture.values["state"]["runtimeExitCodes"] = [0, 0]
        fixture.values["browser"]["original_quit_byte_observation_boundary_verified"] = False
        fixture.qualify_as_blocked("exactly_one_successful_runtime_exit",
                                   "byte_observation_after_all_original_case_results_before_runtime_exit")
        fixture.synchronize()
        checks, blockers = fixture.consume()
        self.assertFalse(checks["exactly_one_successful_runtime_exit"])
        self.assertIn("single_final_runtime_exit_not_observed", blockers)

    def test_boolean_exit_codes_and_main_counters_are_not_integer_observations(self):
        for field in ("wasm", "chrome", "manual_main", "original_quit"):
            with self.subTest(field=field):
                fixture = RuntimeFixture()
                if field == "wasm":
                    fixture.event("runtime_exit")["detail"]["code"] = False
                    fixture.values["state"]["runtimeExitCodes"] = [False]
                elif field == "chrome":
                    fixture.values["browser"]["actual_chrome_process_returncode"] = False
                elif field == "manual_main":
                    fixture.values["state"]["manualMainCalls"] = False
                else:
                    fixture.values["state"]["originalQuitObservations"] = True
                fixture.synchronize()
                with self.assertRaisesRegex(ValueError, "integer"):
                    fixture.consume()

    def test_original_run_all_command_cannot_be_replaced_by_visual_run_test(self):
        for location in ("manifest", "state", "launch"):
            with self.subTest(location=location):
                fixture = RuntimeFixture()
                if location == "manifest":
                    fixture.values["manifest"]["command"][-1] = "--run-test"
                elif location == "state":
                    fixture.values["state"]["actualArgvAtRuntimeExit"][-1] = "--run-test"
                else:
                    fixture.event("launch_original_main")["detail"]["command"][-1] = "--run-test"
                fixture.synchronize()
                with self.assertRaisesRegex(ValueError, "manifest|argv|boundary"):
                    fixture.consume()

    def test_update_and_verbose_environment_keys_are_forbidden_even_when_falsey(self):
        for key in ("BLENDER_TEST_UPDATE", "BLENDER_VERBOSE"):
            for value in ("", "0", False, None):
                with self.subTest(key=key, value=value):
                    fixture = RuntimeFixture()
                    fixture.values["state"]["preMainEnvironment"][key] = value
                    fixture.synchronize()
                    with self.assertRaisesRegex(ValueError, "forbidden"):
                        fixture.consume()

    def test_mounted_original_bytes_cannot_be_changed_before_main_or_at_quit(self):
        for boundary, field in (("verified_original_inputs_before_main", "mountedFilesBeforeMain"),
                                ("original_inputs_observed_at_original_quit", "mountedFilesAtOriginalQuit")):
            with self.subTest(boundary=boundary):
                fixture = RuntimeFixture()
                fixture.event(boundary)["detail"]["files"][0]["byte_for_byte_equal_to_verified_input"] = False
                fixture.values["state"][field][0]["byte_for_byte_equal_to_verified_input"] = False
                fixture.synchronize()
                with self.assertRaisesRegex(ValueError, "boundary|readback|bytes"):
                    fixture.consume()

    def test_quit_readback_after_runtime_exit_is_blocked(self):
        fixture = RuntimeFixture()
        readback = fixture.event("original_inputs_observed_at_original_quit")
        fixture.values["events"].remove(readback)
        readback["milliseconds"] = fixture.event("runtime_exit")["milliseconds"]
        fixture.values["events"].append(readback)
        fixture.values["browser"]["original_quit_byte_observation_boundary_verified"] = False
        fixture.qualify_as_blocked("byte_observation_after_all_original_case_results_before_runtime_exit")
        fixture.synchronize()
        checks, blockers = fixture.consume()
        self.assertFalse(checks["byte_observation_after_all_original_case_results_before_runtime_exit"])
        self.assertIn("single_final_runtime_exit_not_observed", blockers)

    def test_console_and_saved_state_must_bind_the_same_event_stream(self):
        for location in ("console", "saved_state", "receipt_state", "stdout", "stderr"):
            with self.subTest(location=location):
                fixture = RuntimeFixture()
                if location == "console":
                    fixture.values["console"] = fixture.values["console"][:-1]
                elif location == "saved_state":
                    fixture.values["state"]["events"] = fixture.values["state"]["events"][:-1]
                elif location == "receipt_state":
                    fixture.values["browser"]["runtime_state"]["events"] = []
                else:
                    fixture.values[location] += "unobserved output\n"
                with self.assertRaisesRegex(ValueError, "differs"):
                    fixture.consume()

    def test_event_sequence_and_time_types_cannot_mask_missing_events(self):
        for field, value in (("sequence", False), ("sequence", 100), ("milliseconds", -1),
                             ("milliseconds", float("nan")), ("milliseconds", True)):
            with self.subTest(field=field, value=value):
                fixture = RuntimeFixture()
                fixture.values["events"][0][field] = value
                # Keep raw transports identical without renumbering the event.
                event = fixture.values["events"][0]
                fixture.values["state"]["events"][0] = copy.deepcopy(event)
                fixture.values["browser"]["runtime_state"]["events"][0] = copy.deepcopy(event)
                marker = fixture.values["profile"]["marker"]
                console = next(row for row in fixture.values["console"] if row["text"].startswith(marker))
                console["text"] = marker + json.dumps(event)
                with self.assertRaises(ValueError):
                    fixture.consume()

    def test_original_exit_must_be_last_even_after_successful_case_output(self):
        fixture = RuntimeFixture()
        exit_event = fixture.event("runtime_exit")
        fixture.values["events"].append({"sequence": 0, "milliseconds": exit_event["milliseconds"],
                                         "kind": "stdout", "detail": "output after runtime exit"})
        fixture.synchronize()
        checks, blockers = fixture.consume()
        self.assertTrue(checks["all_original_mesh_oracles_passed"])
        self.assertIn("single_final_runtime_exit_not_observed", blockers)

    def test_success_claim_cannot_override_a_recorded_failed_exit(self):
        fixture = RuntimeFixture()
        fixture.event("runtime_exit")["detail"]["code"] = 1
        fixture.values["state"]["runtimeExitCodes"] = [1]
        fixture.synchronize()
        with self.assertRaisesRegex(ValueError, "qualification checks contradict"):
            fixture.consume()

    def test_inflated_qualified_count_is_invalid_even_with_passing_markers(self):
        fixture = RuntimeFixture()
        fixture.values["browser"]["qualified_original_browser_passes"] = 89
        with self.assertRaisesRegex(ValueError, "qualified pass count"):
            fixture.consume()

    def test_missing_or_repeated_automatic_launch_boundary_cannot_qualify(self):
        for kind in ("launch_original_main", "module_resolved"):
            for mode in ("missing", "repeated"):
                with self.subTest(kind=kind, mode=mode):
                    fixture = RuntimeFixture()
                    event = fixture.event(kind)
                    if mode == "missing":
                        fixture.values["events"].remove(event)
                    else:
                        first = fixture.values["events"].index(event)
                        fixture.values["events"].insert(first, copy.deepcopy(event))
                    quit_sequence = next(index for index, row in enumerate(fixture.values["events"])
                                         if row["kind"] == "stdout" and row["detail"] == "Blender quit")
                    fixture.values["state"]["originalQuitStdoutSequence"] = quit_sequence
                    fixture.event("original_inputs_observed_at_original_quit")["detail"]["original_quit_stdout_sequence"] = quit_sequence
                    fixture.event("runtime_exit")["detail"]["original_quit_stdout_sequence"] = quit_sequence
                    fixture.synchronize()
                    if mode == "missing":
                        _, blockers = fixture.consume()
                        self.assertIn("original_automatic_main_startup_not_observed_once", blockers)
                    else:
                        # A repeated boundary is structurally invalid even if
                        # every original case result and runtime exit exist.
                        with self.assertRaisesRegex(ValueError, "duplicate original launch boundary"):
                            fixture.consume()


def replace_context_identity(value, original, replacement):
    """Coordinate copied metadata references without altering retained files."""
    if isinstance(value, str):
        return replacement if value == original else value
    if isinstance(value, dict):
        return {key: replace_context_identity(item, original, replacement) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_context_identity(item, original, replacement) for item in value]
    if isinstance(value, tuple):
        return tuple(replace_context_identity(item, original, replacement) for item in value)
    if isinstance(value, mesh.Captured):
        return mesh.Captured(value.path, value.data, replace_context_identity(value.ref, original, replacement))
    return value


class OriginalMeshContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        evidence = mesh.MeshEvidence(ROOT, Path(cls.temp.name) / "context")
        cls.context = mesh.read_contexts(
            evidence, EVIDENCE / "runtime-context-2026-10-23/native-context.json",
            EVIDENCE / "runtime-context-essentials-2026-10-23/browser-context.json", "0" * 64)

    def test_actual_original_essentials_context_is_selected(self):
        mesh.check_context_profile(self.context)
        self.assertEqual(self.context["browser"]["engine_archive"]["sha256"],
                         "3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910")
        self.assertIsNone(self.context["producer"])

    def test_consistent_metadata_repins_cannot_select_a_different_runtime_or_build(self):
        pins = {
            "native_executable": self.context["native"]["executable"]["sha256"],
            "chrome_executable": self.context["browser"]["browser"]["sha256"],
            "engine_archive": self.context["browser"]["engine_archive"]["sha256"],
            "source_build_receipt": self.context["source"].ref["sha256"],
            "cmake_cache": self.context["browser"]["build_configuration"]["sha256"],
        }
        for name, original in pins.items():
            with self.subTest(name=name):
                context = replace_context_identity(copy.deepcopy(self.context), original, "f" * 64)
                with self.assertRaisesRegex(ValueError, "exact historical"):
                    mesh.check_context_profile(context)

    def test_each_original_engine_member_identity_remains_bound(self):
        for member, (original, _) in self.context["engine_files"].items():
            with self.subTest(member=member):
                context = replace_context_identity(copy.deepcopy(self.context), original, "e" * 64)
                with self.assertRaisesRegex(ValueError, "engine members"):
                    mesh.check_context_profile(context)

    def test_native_configuration_measurement_cannot_be_relabelled(self):
        context = copy.deepcopy(self.context)
        original = context["contexts"][mesh.CONTEXT_NATIVE]["build_config_sha256"]
        context = replace_context_identity(context, original, "d" * 64)
        with self.assertRaisesRegex(ValueError, "native configuration"):
            mesh.check_context_profile(context)

    def test_browser_version_is_part_of_the_recorded_profile(self):
        context = copy.deepcopy(self.context)
        context["browser"]["browser"]["version"] = "Google Chrome for Testing 156.0.0.0"
        with self.assertRaisesRegex(ValueError, "Chrome version"):
            mesh.check_context_profile(context)

    def test_original_package_profile_cannot_be_converted_into_a_new_source_build(self):
        for key, value in (("overlay", None), ("producer", {"kind": "new-source-build"})):
            with self.subTest(key=key):
                context = copy.deepcopy(self.context)
                context[key] = value
                with self.assertRaisesRegex(ValueError, "original Essentials"):
                    mesh.check_context_profile(context)

    def test_recorded_runtime_byte_count_cannot_be_a_boolean_or_changed_size(self):
        for field in ("executable", "archive"):
            for value in (True, 1):
                with self.subTest(field=field, value=value):
                    context = copy.deepcopy(self.context)
                    if field == "executable":
                        context["native"]["executable"]["bytes"] = value
                    else:
                        context["browser"]["engine_archive"]["bytes"] = value
                    with self.assertRaises(ValueError):
                        mesh.check_context_profile(context)


class MeshEvidenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.root = self.work / "checkout"
        self.root.mkdir()
        self.payload = self.root / "payload.log"
        self.payload.write_bytes(b"retained original input\n")
        self.evidence = mesh.MeshEvidence(self.root, self.work / "bundle")

    def test_historical_checkout_relocation_preserves_exact_bytes(self):
        pin = file_pin(self.payload, HISTORICAL_ROOT + "/payload.log")
        captured = self.evidence.reference(pin)
        self.assertEqual(captured.data, self.payload.read_bytes())
        self.assertEqual(captured.path, self.payload)
        self.assertEqual((self.evidence.output / captured.ref["path"]).read_bytes(), self.payload.read_bytes())

    def test_noncanonical_and_unbound_paths_are_rejected(self):
        for name in ("../payload.log", "child/../payload.log", "./payload.log", "child//payload.log",
                     "child/./payload.log", "//workspace/scratch/d63596d831b2/blended/payload.log",
                     HISTORICAL_ROOT + "/child/../payload.log", "payload.log\n", "payload\\log",
                     "/unbound/compatibility/payload.log"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.evidence.capture(name)

    def test_symlink_file_and_parent_are_rejected(self):
        alias = self.root / "alias.log"
        alias.symlink_to(self.payload)
        folder = self.root / "alias-directory"
        folder.symlink_to(self.root, target_is_directory=True)
        for name in ("alias.log", "alias-directory/payload.log"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "symlink"):
                self.evidence.capture(name)

    def test_explicit_context_parent_reference_stays_confined(self):
        (self.root / "context").mkdir()
        captured = self.evidence.reference(file_pin(self.payload, "../payload.log"), self.root / "context")
        self.assertEqual(captured.data, self.payload.read_bytes())
        external = self.work / "outside.log"
        external.write_text("outside\n")
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.evidence.reference(file_pin(external, "../../outside.log"), self.root / "context")

    def test_digest_and_byte_count_are_independently_required(self):
        for changes in ({"sha256": "0" * 64}, {"bytes": self.payload.stat().st_size + 1},
                        {"bytes": True}, {"bytes": -1}, {"sha256": "ABC"}):
            pin = {**file_pin(self.payload, "payload.log"), **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.evidence.reference(pin)

    def test_change_after_capture_is_rejected_even_without_another_caller_pin(self):
        self.evidence.capture("payload.log")
        self.payload.write_bytes(b"changed original input\n")
        with self.assertRaisesRegex(ValueError, "hash|changed"):
            self.evidence.capture("payload.log")
        with self.assertRaisesRegex(ValueError, "hash|changed"):
            self.evidence.verify_unchanged()

    def test_duplicate_json_member_is_invalid(self):
        path = self.root / "duplicate.json"
        path.write_bytes(b'{"schema": 1, "schema": 1}\n')
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            self.evidence.capture("duplicate.json").json()

    def test_historical_probe_requires_exact_saved_copy_despite_current_tool(self):
        saved = self.root / SAVED_PROBE
        saved.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / SAVED_PROBE, saved)
        current = self.root / "tools/probe_browser_port.py"
        current.parent.mkdir(parents=True)
        current.write_text("# Different current tool is not the historical producer.\n")
        original = HISTORICAL_ROOT + "/tools/probe_browser_port.py"
        captured = self.evidence.reference({"path": original, "bytes": 75480, "sha256": OLD_PROBE_SHA})
        self.assertEqual(captured.path, saved)
        self.assertEqual(captured.ref["sha256"], OLD_PROBE_SHA)
        self.assertEqual(self.evidence.saved_bindings[original]["saved_path"], SAVED_PROBE.as_posix())
        with self.assertRaisesRegex(ValueError, "reviewed exact source"):
            self.evidence.reference(file_pin(current, original))

    def test_current_probe_cannot_replace_missing_saved_snapshot(self):
        current = self.root / "tools/probe_browser_port.py"
        current.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / SAVED_PROBE, current)
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.evidence.reference({"path": HISTORICAL_ROOT + "/tools/probe_browser_port.py",
                                     "bytes": 75480, "sha256": OLD_PROBE_SHA})


class OriginalMeshSelectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.root = self.work / "checkout"
        self.root.mkdir()
        self.path = SELECTORS / "bmesh-bevel-5.2.json"
        self.selector = read(ROOT / self.path)
        for pin in self.selector["inputs"].values():
            destination = self.root / pin["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / pin["path"], destination)
        write(self.root / self.path, self.selector)

    def consume(self, suffix="bundle"):
        write(self.root / self.path, self.selector)
        return mesh.read_selector(mesh.MeshEvidence(self.root, self.work / suffix), self.path)

    def test_explicit_profile_pins_actual_selected_evidence(self):
        _, profile, retained = self.consume()
        self.assertEqual(profile["registration"], "bmesh_bevel")
        self.assertEqual(profile["count"], 88)
        self.assertEqual(set(retained), set(self.selector["inputs"]))
        for role, captured in retained.items():
            self.assertEqual(captured.ref["sha256"], self.selector["inputs"][role]["sha256"])

    def test_unknown_profile_or_upstream_commit_cannot_be_selected(self):
        original = copy.deepcopy(self.selector)
        for index, mutate in enumerate((lambda row: row.update(id="unknown"),
                                         lambda row: row["target"].update(commit="0" * 40))):
            self.selector = copy.deepcopy(original)
            mutate(self.selector)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.consume("bundle-" + str(index))

    def test_denominator_and_claim_scope_cannot_be_relabelled(self):
        original = copy.deepcopy(self.selector)
        changes = (
            lambda row: row["registration"].update(observed_native_case_count=87),
            lambda row: row["registration"].update(source_declaration_index=True),
            lambda row: row["claim_limits"].update(configured_ctest_execution=True),
            lambda row: row["claim_limits"].update(all_upstream_test_parity=True),
            lambda row: row["claim_limits"].update(full_feature_parity=True),
            lambda row: row["claim_limits"].update(new_original_executions=False),
            lambda row: row["claim_limits"].update(extends_829_unittest_scope=True),
        )
        for index, mutate in enumerate(changes):
            self.selector = copy.deepcopy(original)
            mutate(self.selector)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.consume("bundle-" + str(index))

    def test_extra_missing_or_relocated_input_role_is_invalid(self):
        original = copy.deepcopy(self.selector)
        changes = (
            lambda row: row["inputs"].pop("host_capture"),
            lambda row: row["inputs"].update(other=copy.deepcopy(row["inputs"]["native_execution"])),
            lambda row: row["inputs"]["browser_execution"].update(
                path=row["inputs"]["browser_execution"]["path"].replace("attempt-03-v2-elevated", "attempt-02")),
        )
        for index, mutate in enumerate(changes):
            self.selector = copy.deepcopy(original)
            mutate(self.selector)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.consume("bundle-" + str(index))

    def test_historical_producer_mapping_cannot_be_changed_or_duplicated(self):
        original = copy.deepcopy(self.selector)
        changes = (
            lambda row: row.update(saved_copies=[]),
            lambda row: row["saved_copies"].append(copy.deepcopy(row["saved_copies"][0])),
            lambda row: row["saved_copies"][0].update(path="tools/probe_browser_port.py"),
            lambda row: row["saved_copies"][0].update(sha256="0" * 64),
        )
        for index, mutate in enumerate(changes):
            self.selector = copy.deepcopy(original)
            mutate(self.selector)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.consume("bundle-" + str(index))

    def test_selected_receipt_mutation_requires_valid_original_binding(self):
        path = self.root / self.selector["inputs"]["native_execution"]["path"]
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.consume()


class OriginalMeshCapturedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.reports = {}
        cls.outputs = {}
        for profile in ("bmesh-bevel-5.2", "operators-5.2"):
            output = cls.work / profile
            cls.reports[profile] = mesh.reconcile(ROOT, SELECTORS / (profile + ".json"), output)
            cls.outputs[profile] = output

    def test_real_bevel_capture_has_exactly_88_qualified_original_pairs(self):
        report = self.reports["bmesh-bevel-5.2"]
        self.assertEqual(report["gate"], "passed")
        self.assertTrue(report["declared_scope_test_parity"])
        self.assertEqual(report["required_registration_count"], 1)
        self.assertEqual(report["paired_obligation_count"], 88)
        self.assertEqual(report["successful_execution_pair_count"], 88)
        self.assertEqual(report["outcome_agreement_count"], 88)
        self.assertEqual(report["raw_terminal_outcome_agreement_count"], 88)
        self.assertTrue(all(row["successful_execution"] for row in report["pairs"]))

    def test_real_operator_capture_is_valid_blocked_with_all_105_obligations(self):
        report = self.reports["operators-5.2"]
        self.assertEqual(report["gate"], "blocked")
        self.assertFalse(report["declared_scope_test_parity"])
        self.assertEqual(report["paired_obligation_count"], 105)
        self.assertEqual(report["successful_execution_pair_count"], 0)
        self.assertEqual(report["outcome_agreement_count"], 0)
        self.assertEqual(report["raw_terminal_outcome_agreement_count"], 103)
        self.assertEqual(sum(row["browser_outcome"] == "passed" for row in report["pairs"]), 103)
        failures = [row for row in report["pairs"] if row["browser_outcome"] == "failed"]
        self.assertEqual(len(failures), 2)
        self.assertEqual({row["case_id"].split(":")[-2] for row in failures},
                         {"IcosphereFill", "IcosphereFillUseBeautyFalse"})
        self.assertTrue(all(row["native_outcome"] == "passed" for row in report["pairs"]))
        self.assertFalse(any(row["browser_outcome"] == "expected_failure" for row in report["pairs"]))

    def test_reported_case_ids_equal_existing_original_summary_ids_one_to_one(self):
        for profile, browser in (("bmesh-bevel-5.2", BEVEL_BROWSER), ("operators-5.2", OPERATORS_BROWSER)):
            with self.subTest(profile=profile):
                expected = [row["case_id"] for row in read(ROOT / browser / "summary.json")["cases"]]
                report = self.reports[profile]
                actual = [row["case_id"] for row in report["pairs"]]
                diagnostics = report["original_observations_diagnostics"]["cases"]
                self.assertEqual(len(actual), len(set(actual)))
                self.assertEqual(set(actual), set(expected))
                self.assertEqual(len(diagnostics), len(expected))
                self.assertEqual({row["case_id"] for row in diagnostics}, set(expected))

    def test_bundles_remain_independent_and_do_not_claim_all_application_features(self):
        profiles = []
        for profile, report in self.reports.items():
            with self.subTest(profile=profile):
                self.assertFalse(report["all_upstream_test_parity"])
                self.assertFalse(report["full_feature_parity"])
                coverage = report["coverage_review"]
                self.assertFalse(coverage["source_registration_reconciliation_complete"])
                self.assertFalse(coverage["configuration_matrix_complete"])
                self.assertEqual(report["required_registration_count"], 1)
                candidates = {row["browser_profile"] for row in report["pairs"]}
                self.assertEqual(len(candidates), 1)
                profiles.extend(candidates)
        self.assertEqual(len(set(profiles)), 2)

    def test_emitted_bundle_reassesses_with_unchanged_generic_ledger(self):
        for profile, output in self.outputs.items():
            with self.subTest(profile=profile):
                relocated = self.work / (profile + "-standalone")
                shutil.copytree(output, relocated)
                verified = assess(read(relocated / "contract.json"), read(relocated / "inventory.json"),
                                  read(relocated / "executions.json"), relocated)
                report = self.reports[profile]
                for key in ("gate", "paired_obligation_count", "successful_execution_pair_count",
                            "outcome_agreement_count", "pairs"):
                    self.assertEqual(verified[key], report[key])

    def test_strict_cli_distinguishes_passed_blocked_and_invalid(self):
        for profile, expected in (("bmesh-bevel-5.2", 0), ("operators-5.2", 1)):
            with self.subTest(profile=profile):
                output = self.work / (profile + "-cli")
                completed = subprocess.run(
                    [sys.executable, "-m", "tools.reconcile_original_mesh", "--repo-root", str(ROOT),
                     "--profile", str(SELECTORS / (profile + ".json")), "--output", str(output)],
                    cwd=ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode, expected, completed.stderr + completed.stdout)
                self.assertEqual(read(output / "report.json")["gate"], "passed" if expected == 0 else "blocked")
        invalid_root = self.work / "invalid-checkout"
        invalid_root.mkdir()
        (invalid_root / "profile.json").write_text('{"schema": 1, "schema": 1}\n')
        invalid_output = self.work / "invalid-cli"
        completed = subprocess.run(
            [sys.executable, "-m", "tools.reconcile_original_mesh", "--repo-root", str(invalid_root),
             "--profile", "profile.json", "--output", str(invalid_output)],
            cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
        self.assertEqual(read(invalid_output / "invalid.json")["gate"], "invalid")

    def test_report_only_does_not_relabel_the_operator_result(self):
        output = self.work / "operators-report-only"
        completed = subprocess.run(
            [sys.executable, "-m", "tools.reconcile_original_mesh", "--repo-root", str(ROOT),
             "--profile", str(SELECTORS / "operators-5.2.json"), "--output", str(output), "--report-only"],
            cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        report = read(output / "report.json")
        self.assertEqual(report["gate"], "blocked")
        self.assertEqual(report["paired_obligation_count"], 105)
        self.assertEqual(report["successful_execution_pair_count"], 0)


if __name__ == "__main__":
    unittest.main()
