"""Validate exact producer allowlists, without creating runtime observations.

Temporary contexts combine reviewed source bytes with synthetic run metadata.
They exercise the evidence consumer only and cannot establish Blender parity.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.reconcile_unittest_matrix import (
    CI_CWD_BASIS, CI_PRODUCER_COMMIT, CI_PRODUCER_FILES,
    CI_PRODUCER_PROFILES, CI_PRODUCER_RULE, CI_SOURCE_MODE, Evidence,
    check_producer_matrix, read_producer_compatibility,
)


ROOT = Path(__file__).resolve().parents[1]
OLD_CONTEXT = ROOT / "compatibility/evidence/runtime-context-source-build-39986612484"
OLD_MATRIX = ROOT / "compatibility/evidence/source-rebuild-unittest-39986612484/main"
DPX_RULE = "original-unittest-downloaded-sources-03913290e92a-v1"
DPX_COMMIT = "03913290e92a98cd9c45fdecf679072587c4dbe7"
DPX_SOURCES = ROOT / "compatibility/evidence/source-producer-review-03913290e92a-2026-10-23/sources"


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def pin(path):
    data = path.read_bytes()
    return {"path": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class ExactProducerProfilesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="blended-producer-profiles-")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.root = self.workspace / "repository"
        self.root.mkdir()
        self.sequence = 0

    def fixture(self, rule):
        profile = CI_PRODUCER_PROFILES[rule]
        directory = self.root / ("fixture-" + str(self.sequence))
        self.sequence += 1
        directory.mkdir()
        producer = {
            "schema": 1, "kind": "source-derived-frozen-producer-context",
            "rule": rule, "source_commit": profile["commit"],
            "cwd_basis": CI_CWD_BASIS, "source_mode": CI_SOURCE_MODE,
            "os_cwd_observed": False, "checkout_root": "/home/runner/work/blended/blended",
            "original_entrypoint": "/home/runner/work/blended/blended/tools/run_unittest_browser_matrix.py",
            "run_id": 1,
            "fixture_notice": "Synthetic infrastructure fixture; no runtime execution is asserted.",
        }
        for field, (source_path, _, _) in profile["files"].items():
            if rule == CI_PRODUCER_RULE:
                original = (OLD_CONTEXT / "browser-source-build.yml" if field == "workflow"
                            else OLD_MATRIX / "harness" / source_path)
            else:
                original = DPX_SOURCES / source_path
            path = directory / field
            path.write_bytes(original.read_bytes())
            producer[field] = {**pin(path), "upstream_path": source_path}
        matrix_path = directory / "matrix.json"
        matrix_path.write_bytes((OLD_MATRIX / "matrix.json").read_bytes())
        producer["matrices"] = [{"plan": "main", "matrix": pin(matrix_path)}]
        run = {
            "id": 1, "head_sha": profile["commit"],
            "path": ".github/workflows/browser-source-build.yml", "status": "completed",
            "run_started_at": "2026-10-23T00:00:00Z", "updated_at": "2026-10-24T00:00:00Z",
            "fixture_notice": "Synthetic infrastructure fixture; no runtime execution is asserted.",
        }
        write_json(directory / "run.json", run)
        producer["ci_run"] = pin(directory / "run.json")
        self.save(directory, producer)
        return directory, producer

    def save(self, directory, producer):
        write_json(directory / "producer.json", producer)
        write_json(directory / "context.json", {
            "source_derived_producer_context": pin(directory / "producer.json"),
        })

    def read(self, directory):
        output = self.workspace / ("capture-" + str(self.sequence))
        self.sequence += 1
        evidence = Evidence(self.root, output)
        context = evidence.capture(directory / "context.json")
        producer, references = read_producer_compatibility(evidence, context, context.json())
        return evidence, producer, references

    def test_original_profile_keeps_its_exact_commit_and_source_identities(self):
        directory, _ = self.fixture(CI_PRODUCER_RULE)
        _, producer, references = self.read(directory)
        self.assertEqual(producer["rule"], CI_PRODUCER_RULE)
        self.assertEqual(producer["run"]["head_sha"], CI_PRODUCER_COMMIT)
        for field, (_, size, digest) in CI_PRODUCER_FILES.items():
            self.assertEqual((len(producer["files"][field].data), producer["files"][field].ref["sha256"]),
                             (size, digest))
        self.assertEqual(len(references), 6)

    def test_dpx_profile_binds_the_separately_reviewed_commit_and_probe(self):
        directory, _ = self.fixture(DPX_RULE)
        _, producer, _ = self.read(directory)
        self.assertEqual(producer["rule"], DPX_RULE)
        self.assertEqual(producer["run"]["head_sha"], DPX_COMMIT)
        self.assertEqual(producer["files"]["probe"].ref["sha256"],
                         "bd975ec99e30c5d33496fc94a3d0f00837e181a5b5ea543431829fcbb71c1887")
        self.assertNotEqual(producer["files"]["probe"].ref["sha256"], CI_PRODUCER_FILES["probe"][2])

    def test_reviewed_dpx_producer_diff_is_only_the_codec_manifest_digest(self):
        old = (OLD_MATRIX / "harness/tools/probe_browser_port.py").read_bytes()
        current = (DPX_SOURCES / "tools/probe_browser_port.py").read_bytes()
        before = b'b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708'
        after = b'1c98842c68dc7706630ce31132cdab20649ea61b860dd05b88722dc1a79b0bcf'
        self.assertEqual(old.count(before), 1)
        self.assertEqual(old.replace(before, after), current)
        for field in ("workflow", "matrix_driver"):
            self.assertEqual(CI_PRODUCER_PROFILES[DPX_RULE]["files"][field], CI_PRODUCER_FILES[field])

    def test_self_consistent_probe_repinning_cannot_cross_profiles(self):
        for rule, alternate in ((CI_PRODUCER_RULE, DPX_RULE), (DPX_RULE, CI_PRODUCER_RULE)):
            with self.subTest(rule=rule):
                directory, producer = self.fixture(rule)
                other, _ = self.fixture(alternate)
                (directory / "probe").write_bytes((other / "probe").read_bytes())
                producer["probe"].update(pin(directory / "probe"))
                self.save(directory, producer)
                with self.assertRaisesRegex(ValueError, "reviewed exact workflow and source pair"):
                    self.read(directory)

    def test_rehashed_edits_to_each_reviewed_dpx_file_are_rejected(self):
        for field in ("workflow", "matrix_driver", "probe"):
            with self.subTest(field=field):
                directory, producer = self.fixture(DPX_RULE)
                path = directory / field
                path.write_bytes(path.read_bytes() + b"\n# unreviewed source edit\n")
                producer[field].update(pin(path))
                self.save(directory, producer)
                with self.assertRaisesRegex(ValueError, "reviewed exact workflow and source pair"):
                    self.read(directory)

    def test_profile_commit_cannot_be_relabelled(self):
        for rule, wrong in ((CI_PRODUCER_RULE, DPX_COMMIT), (DPX_RULE, CI_PRODUCER_COMMIT)):
            with self.subTest(rule=rule):
                directory, producer = self.fixture(rule)
                producer["source_commit"] = wrong
                self.save(directory, producer)
                with self.assertRaisesRegex(ValueError, "unreviewed source-derived producer"):
                    self.read(directory)

    def test_unknown_and_non_string_rules_are_controlled_rejections(self):
        for rule in ("unreviewed-future-head", None, [], {}, 1, True):
            with self.subTest(rule=rule):
                directory, producer = self.fixture(DPX_RULE)
                producer["rule"] = rule
                self.save(directory, producer)
                with self.assertRaisesRegex(ValueError, "unreviewed source-derived producer"):
                    self.read(directory)

    def test_dpx_profile_still_requires_completed_run_from_exact_head(self):
        for field, value in (("head_sha", CI_PRODUCER_COMMIT), ("status", "in_progress"),
                             ("id", 2), ("path", ".github/workflows/test-parity-ledger.yml")):
            with self.subTest(field=field):
                directory, producer = self.fixture(DPX_RULE)
                path = directory / "run.json"
                run = json.loads(path.read_bytes())
                run[field] = value
                write_json(path, run)
                producer["ci_run"] = pin(path)
                self.save(directory, producer)
                with self.assertRaisesRegex(ValueError, "completed exact workflow run"):
                    self.read(directory)

    def test_dpx_matrix_returns_selected_rule_and_binds_selected_harness(self):
        directory, _ = self.fixture(DPX_RULE)
        evidence, producer, _ = self.read(directory)
        captured = evidence.capture(directory / "matrix.json")
        matrix = captured.json()
        harness = {CI_PRODUCER_FILES[field][0]: producer["files"][field]
                   for field in ("matrix_driver", "probe")}
        mode = check_producer_matrix(producer, captured, matrix, harness)
        self.assertEqual(mode["rule"], DPX_RULE)
        self.assertIn("not an OS-observed cwd", mode["cwd_basis"])
        wrong = copy.deepcopy(harness)
        wrong["tools/probe_browser_port.py"].data = (OLD_MATRIX / "harness/tools/probe_browser_port.py").read_bytes()
        with self.assertRaisesRegex(ValueError, "matrix harness differs"):
            check_producer_matrix(producer, captured, matrix, wrong)


if __name__ == "__main__":
    unittest.main()
