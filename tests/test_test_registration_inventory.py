"""Registration inventory tests; these do not execute Blender tests."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.test_registration_inventory import (
    inventory_ctest,
    inventory_gtest,
    load_json_strict,
)


PRODUCT_COMMIT = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
CANDIDATE_COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"
BUILD_HASH = "a" * 64
ARTIFACT_HASH = "b" * 64


def ctest_document(*tests):
    return {
        "kind": "ctestInfo",
        "version": {"major": 1, "minor": 0},
        "backtraceGraph": {
            "commands": ["add_test"],
            "files": ["/source/tests/CMakeLists.txt"],
            "nodes": [{"file": 0}, {"file": 0, "line": 12, "command": 0, "parent": 0}],
        },
        "tests": list(tests),
    }


def registration(name="blenlib", **extra):
    return {
        "name": name,
        "command": ["/build/blender_test", "--gtest_filter=BLI.*"],
        "backtrace": 1,
        **extra,
    }


def ctest_inventory(document, **extra):
    return inventory_ctest(
        document,
        **{
            "source_commit": PRODUCT_COMMIT,
            "build_config_sha256": BUILD_HASH,
            "configuration": None,
            "provenance": {"returncode": 0, "argv": ["ctest", "--show-only=json-v1"]},
            **extra,
        },
    )


def gtest_inventory(text, **extra):
    return inventory_gtest(
        text,
        **{
            "source_commit": PRODUCT_COMMIT,
            "build_config_sha256": BUILD_HASH,
            "artifact_sha256": ARTIFACT_HASH,
            "registration_id": "ctest:example",
            "provenance": {"returncode": 0, "argv": ["test", "--gtest_list_tests"]},
            **extra,
        },
    )


class CTestRegistrationInventoryTests(unittest.TestCase):
    def test_aggregate_registration_requires_child_cases(self):
        result = ctest_inventory(ctest_document(registration()))
        case = result["registrations"][0]
        self.assertEqual(case["identity"], "blenlib")
        self.assertEqual(case["command"][1], "--gtest_filter=BLI.*")
        self.assertEqual(case["expansion_obligation"]["status"], "required")
        self.assertEqual(case["expansion_obligation"]["children"], [])
        self.assertEqual(case["execution"], "not_run")
        self.assertFalse(result["runtime_enumeration_complete"])
        self.assertFalse(result["registration_enumeration_complete"])

    def test_empty_listing_does_not_prove_no_obligations(self):
        result = ctest_inventory(ctest_document())
        self.assertFalse(result["runtime_enumeration_complete"])
        self.assertFalse(result["registration_enumeration_complete"])
        self.assertIn("empty_registration_listing", result["blockers"])

    def test_disabled_fixture_registration_is_preserved(self):
        props = [
            {"name": "DISABLED", "value": True},
            {"name": "LABELS", "value": ["geometry", "native"]},
            {"name": "FIXTURES_SETUP", "value": ["assets"]},
            {"name": "FIXTURES_REQUIRED", "value": ["environment"]},
            {"name": "FIXTURES_CLEANUP", "value": ["scratch"]},
            {"name": "ENVIRONMENT", "value": ["A=one;two"]},
            {"name": "SKIP_RETURN_CODE", "value": 77},
        ]
        result = ctest_inventory(ctest_document(registration(properties=props)))
        case = result["registrations"][0]
        self.assertTrue(case["disabled"])
        self.assertEqual(case["labels"], ["geometry", "native"])
        self.assertEqual(case["fixtures"], {
            "setup": ["assets"], "required": ["environment"], "cleanup": ["scratch"],
        })
        self.assertEqual(case["properties"], props)
        self.assertEqual(case["execution"], "not_run")
        self.assertEqual(result["fixture_completeness"], "unknown")

    def test_missing_or_empty_command_keeps_unresolved_registration(self):
        missing = registration("missing")
        del missing["command"]
        result = ctest_inventory(ctest_document(missing, registration("empty", command=[])))
        self.assertEqual(len(result["registrations"]), 2)
        for case in result["registrations"]:
            self.assertEqual(case["command_status"], "unavailable")
            self.assertEqual(case["expansion_obligation"]["status"], "unresolved")

    def test_configuration_and_source_backtrace_are_preserved(self):
        result = ctest_inventory(ctest_document(registration(config="Debug")), configuration="Debug")
        case = result["registrations"][0]
        self.assertEqual(case["config"], "Debug")
        self.assertEqual(case["backtrace"][0], {
            "file": "/source/tests/CMakeLists.txt", "line": 12, "command": "add_test",
        })
        self.assertEqual(result["scope"]["configuration"], "Debug")

    def test_configuration_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "configuration"):
            ctest_inventory(ctest_document(registration(config="Debug")), configuration="Release")

    def test_source_and_build_changes_cannot_reuse_registration_ids(self):
        document = ctest_document(registration())
        ids = {
            ctest_inventory(document)["registrations"][0]["id"],
            ctest_inventory(document, source_commit=CANDIDATE_COMMIT)["registrations"][0]["id"],
            ctest_inventory(document, build_config_sha256="c" * 64)["registrations"][0]["id"],
            ctest_inventory(document, configuration="Release")["registrations"][0]["id"],
        }
        self.assertEqual(len(ids), 4)

    def test_registration_order_does_not_change_identity(self):
        first = ctest_inventory(ctest_document(registration("one"), registration("two")))
        second = ctest_inventory(ctest_document(registration("two"), registration("one")))
        self.assertEqual(
            {r["identity"]: r["id"] for r in first["registrations"]},
            {r["identity"]: r["id"] for r in second["registrations"]},
        )

    def test_duplicate_names_and_properties_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            ctest_inventory(ctest_document(registration(), registration()))
        props = [{"name": "DISABLED", "value": True}, {"name": "DISABLED", "value": False}]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            ctest_inventory(ctest_document(registration(properties=props)))

    def test_unknown_disabled_type_does_not_turn_into_false(self):
        result = ctest_inventory(ctest_document(registration(properties=[
            {"name": "DISABLED", "value": "perhaps"},
        ])))
        case = result["registrations"][0]
        self.assertIsNone(case["disabled"])
        self.assertEqual(case["expansion_obligation"]["status"], "unresolved")
        self.assertIn("unrecognized_disabled_property", case["diagnostics"])

    def test_invalid_graph_indices_and_cycles_are_rejected(self):
        for broken in ("index", "cycle"):
            with self.subTest(broken=broken):
                document = ctest_document(registration())
                document["backtraceGraph"]["nodes"][1]["parent"] = 99 if broken == "index" else 1
                with self.assertRaisesRegex(ValueError, "backtrace"):
                    ctest_inventory(document)

    def test_unsupported_version_and_malformed_tests_are_rejected(self):
        for change in ({"version": {"major": 2, "minor": 0}}, {"tests": {}}, {"tests": [registration(command="test")]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                ctest_inventory({**ctest_document(), **change})

    def test_future_property_values_are_preserved_without_claiming_support(self):
        document = ctest_document(registration(properties=[
            {"name": "FUTURE_PROPERTY", "value": {"scope": ["one", "two"]}},
        ]))
        before = copy.deepcopy(document)
        result = ctest_inventory(document)
        self.assertEqual(result["registrations"][0]["properties"], before["tests"][0]["properties"])
        result["registrations"][0]["properties"][0]["value"]["scope"].append("three")
        self.assertEqual(document, before)

    def test_failed_capture_never_becomes_complete(self):
        result = ctest_inventory(ctest_document(registration()), provenance={"returncode": 1})
        self.assertIn("capture_failed", result["blockers"])
        self.assertFalse(result["registration_enumeration_complete"])

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for text in ('{"tests":[],"tests":[1]}', '{"timeout":NaN}', '{"timeout":Infinity}', '{"timeout":1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_json_strict(text)

    def test_raw_listing_hash_keeps_original_bytes_and_encoding(self):
        text = json.dumps(ctest_document(registration()), indent=4) + "\n"
        result = ctest_inventory(text)
        self.assertEqual(result["input_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(result["input_hash_encoding"], "raw_utf8")
        parsed = ctest_inventory(json.loads(text))
        self.assertEqual(parsed["input_hash_encoding"], "canonical_json_utf8")
        self.assertNotEqual(result["input_sha256"], parsed["input_sha256"])


class GTestRuntimeInventoryTests(unittest.TestCase):
    def test_runtime_names_keep_typed_and_value_parameter_suffixes(self):
        text = (
            "TypedSuite/0.  # TypeParam = unsigned int\n"
            "  Clamp\n"
            "TypedSuite/1.  # TypeParam = float\n"
            "  Clamp\n"
            "Instantiated/Values.\n"
            "  KeepsValue/zero  # GetParam() = (0, \"a # b\")\n"
            "  KeepsValue/one  # GetParam() = (1, \"a # b\")\n"
        )
        result = gtest_inventory(text)
        self.assertEqual([c["identity"] for c in result["cases"]], [
            "TypedSuite/0.Clamp", "TypedSuite/1.Clamp",
            "Instantiated/Values.KeepsValue/zero", "Instantiated/Values.KeepsValue/one",
        ])
        self.assertEqual(result["cases"][0]["type_parameter"], "unsigned int")
        self.assertEqual(result["cases"][2]["value_parameter"], '(0, "a # b")')
        self.assertEqual(len({c["id"] for c in result["cases"]}), 4)
        self.assertTrue(result["listing_parse_complete"])
        self.assertFalse(result["runtime_enumeration_complete"])

    def test_disabled_instantiated_suites_and_cases_stay_in_denominator(self):
        result = gtest_inventory(
            "Prefix/DISABLED_Typed/0.\n  Case\n"
            "Values.\n  DISABLED_Case/0\n  Case/DISABLED_value\n  NOT_DISABLED_Case\n"
        )
        self.assertEqual([c["disabled"] for c in result["cases"]], [True, True, True, False])
        self.assertTrue(all(c["execution"] == "not_run" for c in result["cases"]))
        self.assertIn("DISABLED_", result["cases"][0]["identity"])

    def test_annotations_are_display_metadata_not_parameter_identity(self):
        first = gtest_inventory("S.\n  C/0  # GetParam() = value...\n")["cases"][0]
        second = gtest_inventory("S.\n  C/0  # GetParam() = more detail\n")["cases"][0]
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["parameter_metadata_fidelity"], "display_only_may_be_truncated")

    def test_same_leaf_under_multiple_registrations_has_one_execution_identity(self):
        a = gtest_inventory("S.\n  C\n", registration_id="ctest:one")["cases"][0]
        b = gtest_inventory("S.\n  C\n", registration_id="ctest:two")["cases"][0]
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(a["registration_ids"], ["ctest:one"])
        self.assertEqual(b["registration_ids"], ["ctest:two"])

    def test_wrong_source_build_or_artifact_cannot_reuse_case_identity(self):
        ids = {
            gtest_inventory("S.\n  C\n")["cases"][0]["id"],
            gtest_inventory("S.\n  C\n", source_commit=CANDIDATE_COMMIT)["cases"][0]["id"],
            gtest_inventory("S.\n  C\n", build_config_sha256="c" * 64)["cases"][0]["id"],
            gtest_inventory("S.\n  C\n", artifact_sha256="d" * 64)["cases"][0]["id"],
        }
        self.assertEqual(len(ids), 4)

    def test_unknown_lines_and_orphans_cannot_be_silently_dropped(self):
        result = gtest_inventory("  Orphan\nS.\n  Good\n  cannot parse this\n")
        self.assertEqual([c["identity"] for c in result["cases"]], ["S.Good"])
        self.assertEqual([x["line"] for x in result["unparsed_lines"]], [1, 4])
        self.assertFalse(result["listing_parse_complete"])
        self.assertIn("unparsed_listing_lines", result["blockers"])

    def test_unparsed_suite_cannot_reassign_cases_to_previous_suite(self):
        result = gtest_inventory("Old.\n  First\nBad suite.\n  Next\n")
        self.assertEqual([c["identity"] for c in result["cases"]], ["Old.First"])
        self.assertEqual(len(result["unparsed_lines"]), 2)

    def test_duplicate_case_or_suite_is_rejected(self):
        for text in ("S.\n  C\n  C\n", "S.\n  C\nS.\n  D\n"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "Duplicate"):
                gtest_inventory(text)

    def test_empty_listing_and_empty_suite_keep_unknown_denominator(self):
        empty = gtest_inventory("")
        self.assertIn("empty_runtime_listing", empty["blockers"])
        self.assertFalse(empty["runtime_enumeration_complete"])
        suite = gtest_inventory("Unfinished.\n")
        self.assertFalse(suite["listing_parse_complete"])
        self.assertIn("empty_suites", suite["blockers"])

    def test_known_main_banner_is_retained(self):
        result = gtest_inventory("Running main() from /source/gtest_main.cc\nS.\n  C\n")
        self.assertEqual(len(result["preamble"]), 1)
        self.assertTrue(result["listing_parse_complete"])

    def test_filter_and_environment_are_not_assumed_universal(self):
        result = gtest_inventory("S.\n  C\n", provenance={
            "returncode": 0, "argv": ["test", "--gtest_list_tests", "--gtest_filter=S.C"],
            "environment": {"GTEST_FILTER": "S.C"},
        })
        self.assertFalse(result["runtime_enumeration_complete"])
        self.assertIn("capture_scope_requires_attestation", result["blockers"])

    def test_source_commit_and_artifact_require_full_hashes(self):
        for change in ({"source_commit": "main"}, {"artifact_sha256": "abc"}, {"build_config_sha256": False}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                gtest_inventory("S.\n  C\n", **change)


class CTestInfrastructureIntegrationTests(unittest.TestCase):
    def test_real_configuration_fixture_and_unavailable_command_inventory(self):
        cmake = os.environ.get("BLENDED_INVENTORY_CMAKE") or shutil.which("cmake")
        if not cmake:
            self.skipTest("CMake is needed for the standalone infrastructure fixture")
        ctest = str(Path(cmake).with_name("ctest"))
        fixture = Path(__file__).resolve().parents[1] / "compatibility/evidence/registration-inventory-2026-10-23/fixture"
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary) / "build"
            configured = subprocess.run([cmake, "-S", str(fixture), "-B", str(build)], capture_output=True, text=True, timeout=60)
            self.assertEqual(configured.returncode, 0, configured.stderr)
            inventories = {}
            for configuration in ("Debug", "Release"):
                argv = [ctest, "--test-dir", str(build), "--show-only=json-v1", "-C", configuration]
                listed = subprocess.run(argv, capture_output=True, text=True, timeout=60)
                self.assertEqual(listed.returncode, 0, listed.stderr)
                inventories[configuration] = ctest_inventory(listed.stdout, configuration=configuration,
                                                            provenance={"argv": argv, "returncode": listed.returncode})
            debug = {c["identity"]: c for c in inventories["Debug"]["registrations"]}
            release = {c["identity"]: c for c in inventories["Release"]["registrations"]}
            self.assertIn("debug_only", debug)
            self.assertNotIn("debug_only", release)
            self.assertEqual(debug["aggregate"]["fixtures"]["required"], ["assets"])
            self.assertTrue(debug["disabled"]["disabled"])
            self.assertEqual(debug["unavailable"]["command_status"], "unavailable")
            self.assertNotEqual(debug["aggregate"]["id"], release["aggregate"]["id"])
            self.assertFalse(inventories["Debug"]["registration_enumeration_complete"])


if __name__ == "__main__":
    unittest.main()
