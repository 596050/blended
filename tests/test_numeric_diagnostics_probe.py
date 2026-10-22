import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import probe_numeric_diagnostics as probe


def execution(build_hash=probe.browser_probe.UPSTREAM_SHA[:12]):
    return {
        "schema": 1, "diagnostic_only": True,
        "identity": {"version": [5, 2, 0], "build_hash": build_hash},
        "expected_counts": {"vector_cases": 1, "screw_cases": 1},
        "vector_cases": [{"id": "vector-0", "inputs": [1.0, 2.0, 3.0],
                          "angle": {"value": 1.0, "f32_bits": "3f800000"}}],
        "screw_cases": [{"id": "screw-false", "inputs": {"do_dupli": False},
                         "topology_sha256": "c" * 64,
                         "edges": [{"id": "edge-0", "length": 2.0}]}],
    }


def report(engine, result=None):
    result = result or execution()
    module = probe.native_probe if engine == "native" else probe.browser_probe
    return {
        "schema": 1, "diagnostic_only": True, "engine": engine,
        "payload": {"sha256": "a" * 64},
        "artifact": {"observed_sha256": module.ASSET_SHA256, "observed_bytes": module.ASSET_BYTES},
        "upstream": {"commit": probe.browser_probe.UPSTREAM_SHA},
        "execution": result, **probe.assess_execution(result),
    }


class NumericDiagnosticProbeTests(unittest.TestCase):
    def test_marker_requires_exactly_one_complete_diagnostic_object(self):
        good = probe.MARKER + json.dumps(execution())
        self.assertEqual(probe.parse_marker_lines(["startup", good])["schema"], 1)
        for lines in ([], [good, good], [probe.MARKER + '{"schema":']):
            with self.subTest(lines=lines):
                with self.assertRaises(probe.Blocked):
                    probe.parse_marker_lines(lines)

    def test_unknown_identity_keeps_diagnostics_but_blocks_qualification(self):
        result = probe.assess_execution(execution("Unknown"))
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["diagnostics_complete"])
        self.assertFalse(result["upstream_build_hash_verified"])
        self.assertEqual(result["blockers"][0]["scope"], "provenance")
        self.assertNotIn("passed", result)

    def test_missing_and_duplicate_cases_cannot_look_complete(self):
        missing = execution()
        missing["vector_cases"] = []
        duplicate = execution()
        duplicate["vector_cases"] *= 2
        duplicate["expected_counts"]["vector_cases"] = 2
        for item in (missing, duplicate):
            with self.subTest(item=item):
                with self.assertRaises(probe.Blocked):
                    probe.assess_execution(item)

    def test_comparison_pairs_input_ids_and_preserves_exact_bit_differences(self):
        native, browser = report("native"), report("browser", execution("Unknown"))
        browser["execution"]["vector_cases"][0]["angle"]["f32_bits"] = "3f800001"
        combined = probe.compare_reports(native, browser)
        self.assertEqual(combined["status"], "blocked")
        self.assertTrue(combined["pairing_complete"])
        self.assertEqual(combined["counters"]["paired_cases"], 2)
        difference = combined["cases"][0]["differences"][0]
        self.assertEqual(difference["field"], "/angle/f32_bits")
        self.assertEqual(difference["native"], "3f800000")
        self.assertEqual(difference["browser"], "3f800001")

    def test_changed_payload_inputs_or_artifact_refuse_pairing(self):
        native = report("native")
        changes = []
        changed = report("browser")
        changed["payload"]["sha256"] = "b" * 64
        changes.append(changed)
        changed = report("browser")
        changed["execution"]["vector_cases"][0]["inputs"][0] = 99.0
        changes.append(changed)
        changed = report("browser")
        changed["artifact"]["observed_sha256"] = "0" * 64
        changes.append(changed)
        for changed in changes:
            with self.subTest(changed=changed):
                combined = probe.compare_reports(native, changed)
                self.assertEqual(combined["status"], "blocked")
                self.assertFalse(combined["pairing_complete"])

    def test_mesh_pairing_requires_matching_nonempty_topology_signatures(self):
        for signature in (None, "d" * 64):
            with self.subTest(signature=signature):
                native, browser = report("native"), report("browser")
                browser["execution"]["screw_cases"][0]["topology_sha256"] = signature
                result = probe.compare_reports(native, browser)
                self.assertFalse(result["pairing_complete"])
                self.assertEqual(result["counters"]["paired_cases"], 1)
                self.assertTrue(any(row["scope"] == "topology_pairing" for row in result["blockers"]))

    def test_missing_execution_produces_a_blocked_comparison(self):
        browser = report("browser")
        browser["execution"] = None
        result = probe.compare_reports(report("native"), browser)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["pairing_complete"])
        self.assertFalse(result["diagnostics_complete"])
        self.assertEqual(result["counters"]["paired_cases"], 0)


if __name__ == "__main__":
    unittest.main()
