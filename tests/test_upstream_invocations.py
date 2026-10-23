"""A manifest cannot assert its own authority to filter original tests."""
import copy
import json
from pathlib import Path
import unittest

from tools import unittest_cohort as cohort
from tools import upstream_invocations as upstream

ROOT = Path(__file__).resolve().parents[1]


class OriginalDeclarationTests(unittest.TestCase):
    def test_catalog_retains_all_original_declarations_and_complete_source_bytes(self):
        catalog = upstream.load_catalog()
        self.assertEqual(len(catalog["declarations"]), 132)
        self.assertEqual([{key: row[key] for key in ("upstream_path", "bytes", "sha256")}
                          for row in catalog["sources"]], cohort.CMAKE_SOURCES)
        self.assertTrue(any(row["context"] for row in catalog["declarations"]))
        self.assertEqual([row["source_declaration_index"] for row in catalog["declarations"]], list(range(132)))

    def test_exact_declaration_accepts_subset_but_rejects_line_or_context_changes(self):
        record = upstream.load_catalog()["declarations"][0]
        row = {"source_declaration_index": record["source_declaration_index"], "line": record["line"],
               "registration": record["text"], "context": copy.deepcopy(record["context"])}
        upstream.validate_declaration(row)
        for change in ({"line": row["line"] + 1}, {"registration": row["registration"] + " "},
                       {"context": [{"opener": "if(FORGED)", "line": 1}]}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "pinned CMake declaration"):
                upstream.validate_declaration({**row, **change})

    def test_forged_attached_keyword_and_positional_selector_are_rejected(self):
        path = ROOT / "compatibility/candidate-suites/unittest-main-5.2/bl_animation_bake.json"
        value = json.loads(path.read_text())
        for selector in ("-kBake", "TestActionBake.test_action_bake", "--keyword=Bake"):
            forged = copy.deepcopy(value)
            forged["execution"]["script_args"] = [selector]
            registration = forged["execution"]["registration"]
            forged["execution"]["registration"] = registration[:-1] + " -- " + selector + "\n)"
            with self.subTest(selector=selector), self.assertRaisesRegex(ValueError, "pinned CMake declaration"):
                cohort.validate_manifest(forged)

    def test_all_34_frozen_manifests_remain_authentic(self):
        paths = [*sorted((ROOT / "compatibility/candidate-suites/unittest-main-5.2").glob("*.json")),
                 *sorted((ROOT / "compatibility/candidate-suites/unittest-main-resources-5.2").glob("*.json")),
                 ROOT / "compatibility/candidate-suites/bl_animation_bake-5.2.json"]
        self.assertEqual(len(paths), 34)
        for path in paths:
            with self.subTest(manifest=path.name):
                cohort.validate_manifest(json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
