"""Exchange gate contracts; synthetic bytes here are not Blender feature evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import probe_blendfile_exchange as exchange
from tools import probe_browser_port as shared
from tools import probe_native_reference as native


class BlendFileExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.catalog = shared.load_suite_catalog("blendio52")

    def producer(self, role="browser", build_hash="Unknown"):
        directory = self.root / role
        files_dir = directory / "blendfiles"
        files_dir.mkdir(parents=True)
        rows = []
        for name in (*exchange.CURRENT_FILES, "blendfile_io.blend1"):
            data = ("synthetic integrity fixture " + role + " " + name).encode()
            (files_dir / name).write_bytes(data)
            rows.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        source = copy.deepcopy(self.catalog["suites"][0])
        ids = ["blended_original." + name for name in source["case_ids"]]
        event_pairs = [(phase, event) for phase in ("setup", "body", "teardown") for event in ("start", "return")]
        source_files = [{key: row[key] for key in ("upstream_path", "sha256", "bytes")}
                        for row in [source, *source["support_files"]]]
        execution = {"identity": {"version": [5, 2, 0], "build_hash": build_hash}, "exception": None,
                     "suites": [{"upstream_path": source["upstream_path"], "sha256": source["sha256"],
                                 "discovered_ids": ids, "discovered": 4, "testsRun": 4,
                                 "failures": 0, "errors": 0, "skipped": 0, "expected_failures": 0,
                                 "unexpected_successes": 0,
                                 "outcomes": [{"id": value, "kind": "test", "status": "passed"} for value in ids]}],
                     "io_observation": {"source_bytes_preserved": True, "helper_import_verified": True,
                         "module_returned_normally": True, "driver_completed_as_expected": True,
                         "observer_errors": [], "source_files": source_files,
                         "cases": [{"id": value, "status": "passed", "events": [
                             {"phase": phase, "event": event} for phase, event in event_pairs]} for value in ids]},
                     "generated_files": {"root": "/producer/files", "files": rows}}
        artifact_hash = native.ASSET_SHA256 if role == "native" else shared.ASSET_SHA256
        artifact_bytes = native.ASSET_BYTES if role == "native" else shared.ASSET_BYTES
        report = {"schema": 1, "status": "passed" if role == "native" else "blocked",
                  "profile": "native-reference" if role == "native" else "chromium-software-webgpu",
                  "candidate": {"repository": "gessa-ai/blender-web", "tag": "v0.1.1", "source_commit": shared.PORT_SOURCE_SHA},
                  "upstream": {"repository": "blender/blender", "commit": shared.UPSTREAM_SHA},
                  "cohort": {"id": self.catalog["id"], "manifest_sha256": self.catalog["manifest_sha256"],
                             "expected_cases": 4, "complete_cohort_requested": True},
                  "artifact": {"expected_sha256": artifact_hash, "observed_sha256": artifact_hash,
                               "expected_bytes": artifact_bytes, "observed_bytes": artifact_bytes},
                  "official_release_checksum_verified": role == "native", "selected_suites_passed": True,
                  "suite_sources": [source], "execution": execution, "browser_errors": [], "blockers": [],
                  "generated_file_transfer": {"status": "verified", "origin": "native-filesystem" if role == "native" else "browser-wasm-filesystem",
                      "root": "/producer/files", "files": copy.deepcopy(rows), "bytes": sum(row["bytes"] for row in rows),
                      "semantic_equivalence_verified": False}}
        self.save(directory, role, report)
        return directory, report

    @staticmethod
    def save(directory, role, report):
        name = "native_reference.json" if role == "native" else "qualification.json"
        (directory / name).write_text(json.dumps(report) + "\n")

    def test_missing_input_directories_persist_blocked_fixed_denominator(self):
        output = self.root / "report"
        code = exchange.main(["--native-evidence", str(self.root / "missing-native"),
                              "--browser-evidence", str(self.root / "missing-browser"), "--output", str(output)])
        self.assertEqual(code, 1)
        report = json.loads((output / "exchange.json").read_text())
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["summary"]["expected_files"], 4)
        self.assertEqual(report["summary"]["matched"], 0)
        self.assertEqual({row["file"] for row in report["comparisons"]}, set(exchange.CURRENT_FILES))

    def test_unknown_browser_identity_preserves_verified_files_and_blocker(self):
        directory, _ = self.producer()
        result = exchange.inspect_producer(directory, "browser", self.catalog)
        self.assertEqual(set(result["current_files"]), set(exchange.CURRENT_FILES))
        self.assertEqual(result["excluded_backups"], ["blendfile_io.blend1"])
        self.assertEqual(result["blockers"][0]["scope"], "browser_provenance")

    def test_changed_file_bytes_and_symlink_are_rejected(self):
        directory, report = self.producer()
        path = directory / "blendfiles" / exchange.CURRENT_FILES[0]
        data = path.read_bytes()
        path.write_bytes(data + b"tampered")
        with self.assertRaisesRegex(exchange.InvalidEvidence, "digest|byte count"):
            exchange.inspect_producer(directory, "browser", self.catalog)
        path.unlink()
        target = self.root / "outside.blend"
        target.write_bytes(data)
        path.symlink_to(target)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "regular|symlink|confined"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_missing_current_file_cannot_shrink_transfer_inventory(self):
        directory, report = self.producer()
        name = exchange.CURRENT_FILES[0]
        (directory / "blendfiles" / name).unlink()
        for inventory in [report["generated_file_transfer"], report["execution"]["generated_files"]]:
            inventory["files"] = [row for row in inventory["files"] if row["path"] != name]
        report["generated_file_transfer"]["bytes"] = sum(row["bytes"] for row in report["generated_file_transfer"]["files"])
        self.save(directory, "browser", report)
        with self.assertRaisesRegex(shared.Blocked, "fixed current|missing"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_pass_boolean_cannot_replace_fixed_cases_or_helper_identity(self):
        directory, report = self.producer()
        changed = copy.deepcopy(report)
        row = changed["execution"]["suites"][0]
        row["discovered_ids"].pop(); row["outcomes"].pop()
        row["discovered"] = row["testsRun"] = 3
        self.save(directory, "browser", changed)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "fixed|case|denominator"):
            exchange.inspect_producer(directory, "browser", self.catalog)
        changed = copy.deepcopy(report)
        changed["suite_sources"][0]["support_files"][0]["sha256"] = "0" * 64
        self.save(directory, "browser", changed)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "source|helper"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_transfer_manifest_must_match_engine_inventory(self):
        directory, report = self.producer()
        report["generated_file_transfer"]["root"] = "/other/files"
        self.save(directory, "browser", report)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "root|inventory"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_native_reference_cannot_substitute_for_browser_profile(self):
        directory, report = self.producer()
        report["profile"] = "native-reference"
        self.save(directory, "browser", report)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "profile"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_foreign_browser_artifact_cannot_self_certify_as_release(self):
        directory, report = self.producer()
        report["artifact"]["expected_sha256"] = report["artifact"]["observed_sha256"] = "e" * 64
        self.save(directory, "browser", report)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "pinned.*release|release.*artifact"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_changed_candidate_identity_and_development_artifacts_do_not_inherit_release(self):
        directory, report = self.producer()
        changed = copy.deepcopy(report)
        changed["candidate"]["source_commit"] = "f" * 40
        self.save(directory, "browser", changed)
        with self.assertRaisesRegex(exchange.InvalidEvidence, "candidate|source"):
            exchange.inspect_producer(directory, "browser", self.catalog)
        changed = copy.deepcopy(report)
        changed["candidate"]["kind"] = "blender-source-development"
        changed["source_build_receipt_verified"] = True
        self.save(directory, "browser", changed)
        with self.assertRaisesRegex(shared.Blocked, "development|build receipt"):
            exchange.inspect_producer(directory, "browser", self.catalog)

    def test_matching_files_keep_unknown_provenance_blocked(self):
        comparisons = [{"file": name, "status": "matched"} for name in exchange.CURRENT_FILES]
        result = exchange.assess_comparisons(comparisons, [{"scope": "browser_provenance", "status": "blocked", "reason": "Unknown build hash"}])
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["selected_file_comparisons_passed"])
        self.assertEqual(result["summary"]["matched"], 4)
        result = exchange.assess_comparisons(comparisons[:-1], [])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["summary"]["expected_files"], 4)
        self.assertEqual(result["summary"]["matched"], 3)
        self.assertFalse(result["selected_file_comparisons_passed"])

    def test_source_runtime_failure_survives_four_matching_files(self):
        directory, report = self.producer()
        report["status"] = "failed"
        report["blockers"] = [{"scope": "browser_runtime", "status": "failed", "reason": "trailing GPU failure after complete result"}]
        self.save(directory, "browser", report)
        inputs = exchange.inspect_producer(directory, "browser", self.catalog)
        result = exchange.assess_comparisons(
            [{"file": name, "status": "matched"} for name in exchange.CURRENT_FILES], inputs["blockers"])
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["selected_file_comparisons_passed"])
        self.assertTrue(any(row["reason"] == "trailing GPU failure after complete result" for row in result["blockers"]))

    def test_failed_source_status_cannot_be_downgraded_to_unknown_provenance(self):
        directory, report = self.producer()
        report["status"] = "failed"
        report["reason"] = "producer failed after writing complete evidence"
        self.save(directory, "browser", report)
        inputs = exchange.inspect_producer(directory, "browser", self.catalog)
        result = exchange.assess_comparisons(
            [{"file": name, "status": "matched"} for name in exchange.CURRENT_FILES], inputs["blockers"])
        self.assertEqual(result["status"], "failed")

    def test_complete_tuple_comparison_preserves_difference_without_byte_equality(self):
        left = {"input": {"sha256": "a" * 64}, "snapshot": [[["Mesh", "Mesh", 1], [["Object", "Object", 0]]]],
                "id_flags": [], "libraries": []}
        right = copy.deepcopy(left)
        right["input"]["sha256"] = "b" * 64
        result = exchange.compare_loaded(exchange.CURRENT_FILES[0], left, right)
        self.assertEqual(result["status"], "matched")
        right["snapshot"][0][0][2] = 0
        result = exchange.compare_loaded(exchange.CURRENT_FILES[0], left, right)
        self.assertEqual(result["status"], "different")
        self.assertTrue(result["differences"])
        self.assertIn("native", result["differences"][0])
        self.assertIn("browser", result["differences"][0])

    def test_reader_rejects_changed_helper_before_execution(self):
        metadata = self.catalog["suites"][0]["support_files"][0]
        with self.assertRaisesRegex(exchange.InvalidEvidence, "helper"):
            exchange.reader_payload(self.root / "file.blend", self.root,
                                    {"path": "file.blend", "sha256": "0" * 64, "bytes": 1},
                                    b"changed upstream helper", metadata, "RESULT:")


if __name__ == "__main__":
    unittest.main()
