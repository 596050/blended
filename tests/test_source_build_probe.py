"""Source-build provenance gates; these are not Blender feature tests."""
import hashlib
import json
import copy
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from tools import probe_browser_port as probe
from tools.run_unittest_browser_matrix import harness_sources, suite_source_arguments


class SourceBuildProbeTests(unittest.TestCase):
    def receipt(self, asset):
        return {
            "schema": 1,
            "artifact_kind": "blender-source-development",
            "status": "built",
            "upstream_commit": probe.UPSTREAM_SHA,
            "port_commit": "0e02e84b2bc5d9b27a6dc6e275443292f781fbad",
            "canonical_patch_sha256": "04ba2e6ba8a04ef37bdaf879b10a135736f07114597a908bbbdea8bba244193c",
            "build_mode": "OFF",
            "with_buildinfo": True,
            "artifact": {"path": asset.name, "bytes": asset.stat().st_size,
                         "sha256": hashlib.sha256(asset.read_bytes()).hexdigest()},
        }

    @staticmethod
    def file_record(path):
        return {"path": str(path), "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def dependency_receipt(self, root, kinds):
        """Synthetic build declarations exercise validation, never engine tests."""
        asset = root / "synthetic.tar.gz"
        asset.write_bytes(b"synthetic build contract, no Blender binary")
        data = self.receipt(asset)
        data["compiler"] = {"version": "6.0.5", "commit": "1db513782be24469589d7cb8a1f1834e9a33f271",
                            "emsdk_commit": "1ab2e627b1a84567f5284d1baaa5f6be7ccf07de",
                            "release": "dbd755b5da399329c2576f6e3dfa7f419f5d8409"}
        order = ["zlib", "openimageio", "python", "numpy"]
        recipes = {}
        for kind in kinds:
            manifest_path = probe.SQLITE_PATCH_MANIFEST if kind == "sqlite" else probe.CODEC_PATCH_MANIFEST
            manifest = json.loads(manifest_path.read_text())
            manifest_pin = self.file_record(manifest_path)
            if kind == "sqlite":
                item = manifest["patches"][0]
                outputs = [{"path": item["destination"], "bytes": item["after_bytes"], "sha256": item["after_sha256"]},
                           *[{"path": entry["destination"], "bytes": entry["bytes"], "sha256": entry["sha256"]}
                             for entry in manifest["install_files"]],
                           {"path": "scripts/deps/sqlite-patchset.json", "bytes": manifest_pin["bytes"], "sha256": manifest_pin["sha256"]}]
                insertion = manifest["dependency_insertion"]
                helper = Path(probe.__file__).with_name("prepare_browser_sqlite.py")
                application = {"schema": 1, "patchset_id": manifest["id"], "manifest": manifest_pin,
                               "inputs": [{key: entry[key] for key in ("file", "bytes", "sha256")}
                                          for entry in manifest["install_files"] + manifest["patches"]],
                               "outputs": copy.deepcopy(outputs),
                               "original_python_recipe": {"bytes": item["before_bytes"], "sha256": item["before_sha256"]},
                               "dependency_insertion": insertion,
                               "environment": {"BLENDED_SQLITE_PATCHSET_SHA256": manifest_pin["sha256"]},
                               "requires_enclosing_driver_source_commit_verification": True,
                               "source_tests_modified": False, "browser_tests_executed": False, "full_feature_parity": False}
                added = [insertion["name"]]
            else:
                outputs = [{"path": entry["path"], "bytes": entry["after_bytes"], "sha256": entry["after_sha256"]}
                           for entry in manifest["files"]]
                insertion = manifest["dependency_recipe_insertion"]
                helper = manifest_path.parent / manifest["application_helper"]["file"]
                application = {"schema": 1, "kind": "browser-codec-patch-application", "status": "applied_and_verified",
                               "id": manifest["id"], "manifest_sha256": manifest_pin["sha256"],
                               "patch_sha256": manifest["patch"]["sha256"], "application": "applied",
                               "files": [{**entry, "observed_before_sha256": entry["before_sha256"],
                                          "observed_after_sha256": entry["after_sha256"]} for entry in manifest["files"]],
                               "commands": [], "port_root": "/synthetic-port",
                               "dependency_build_verified": False, "blender_tests_executed": False, "full_feature_parity": False}
                added = insertion["recipes"]
                data["configured_features"] = dict(manifest["required_blender_cache"])
                data["disabled_features"] = []
            index = order.index(insertion["before"])
            order[index:index] = added
            sidecar = root / (kind + "-application.json")
            sidecar.write_text(json.dumps(application, indent=2) + "\n")
            data[kind + "_patchset"] = {
                "id": manifest["id"], "manifest": manifest_pin, "manifest_sha256": manifest_pin["sha256"],
                "status": "applied_and_verified", "applied": True,
                "application_helper": self.file_record(helper), "application_receipt": self.file_record(sidecar),
                "application": application, "outputs": outputs, "dependency_insertion": insertion,
            }
            if kind == "codec":
                cache = root / "openimageio-CMakeCache.txt"
                cache.write_text("".join(name + ":BOOL=" + value + "\n" for name, value in manifest["required_oiio_cache"].items()))
                data["codec_patchset"].update(configured_oiio_features=dict(manifest["required_oiio_cache"]),
                                              oiio_configuration=self.file_record(cache))
            for output in outputs:
                path = Path(output["path"])
                if path.suffix == ".sh" and path.stem != "codec-common":
                    recipes[path.stem] = {**output, "path": "/synthetic-port/" + output["path"]}
        data["dependency_order"] = order
        for name in order:
            recipes.setdefault(name, {"path": "/synthetic-port/scripts/deps/" + name + ".sh", "bytes": 100, "sha256": "a" * 64})
        data["dependency_receipts"] = [{"name": name, "status": "recipe_completed", "recipe": recipes[name]} for name in order]
        snapshot = root / "dependency-recipe-inputs.json"
        snapshot.write_text(json.dumps({name: recipes[name] for name in order}) + "\n")
        data["dependency_recipe_manifest"] = self.file_record(snapshot)
        return asset, data

    def qualify_dependency_receipt(self, root, asset, data):
        receipt = root / "build.json"
        receipt.write_text(json.dumps(data))
        report = {}
        probe.select_artifact_contract(types.SimpleNamespace(asset=asset, source_build_receipt=receipt), report)
        return report

    def test_source_receipt_cannot_be_labelled_as_the_published_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic artifact, contract test only")
            receipt = root / "build.json"
            receipt.write_text(json.dumps(self.receipt(asset)))
            args = types.SimpleNamespace(asset=asset, source_build_receipt=receipt)
            report = {"candidate": {"tag": "v0.1.1"}, "artifact": {}}
            contract = probe.select_artifact_contract(args, report)
            self.assertEqual(contract["sha256"], self.receipt(asset)["artifact"]["sha256"])
            self.assertEqual(report["candidate"]["source_commit"], self.receipt(asset)["port_commit"])
            self.assertNotIn("tag", report["candidate"])
            self.assertEqual(report["candidate"]["kind"], "blender-source-development")
            self.assertFalse(report["source_correspondence_verified"])
            self.assertTrue(report["source_build_receipt_verified"])
            self.assertFalse(report["source_build"]["numeric_fixes_declared"])
            self.assertFalse(report["source_build"]["sqlite_declared"])
            self.assertFalse(report["source_build"]["codecs_declared"])

    def test_incomplete_or_foreign_build_receipts_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic")
            receipt = root / "build.json"
            invalid = {"status": "building", "upstream_commit": "a" * 40,
                       "port_commit": probe.PORT_SOURCE_SHA,
                       "canonical_patch_sha256": "a" * 64,
                       "build_mode": "APPLY", "with_buildinfo": False,
                       "artifact_kind": "release", "schema": 2}
            for field, value in invalid.items():
                with self.subTest(field=field):
                    data = self.receipt(asset)
                    data[field] = value
                    receipt.write_text(json.dumps(data))
                    with self.assertRaises(probe.Blocked):
                        probe.select_artifact_contract(
                            types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})
            for value in (0, -1, True, 2_000_000_001):
                data = self.receipt(asset)
                data["artifact"]["bytes"] = value
                receipt.write_text(json.dumps(data))
                with self.assertRaises(probe.Blocked):
                    probe.select_artifact_contract(
                        types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})

    def test_source_mode_requires_an_explicit_local_artifact(self):
        with self.assertRaises(probe.Blocked):
            probe.select_artifact_contract(
                types.SimpleNamespace(asset=None, source_build_receipt=Path("build.json")), {})

    def test_unreviewed_numeric_patches_cannot_inherit_the_baseline_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic modified engine")
            receipt = root / "build.json"
            for patchset in ({}, {"id": "unreviewed", "manifest_sha256": "a" * 64,
                                   "applied": True}, "unstructured"):
                with self.subTest(patchset=patchset):
                    data = self.receipt(asset)
                    data["numeric_patchset"] = patchset
                    receipt.write_text(json.dumps(data))
                    with self.assertRaises(probe.Blocked):
                        probe.select_artifact_contract(
                            types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})

    def test_declared_dependency_patchsets_cannot_inherit_the_baseline_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic optional dependency build")
            receipt = root / "build.json"
            for key in ("sqlite_patchset", "codec_patchset"):
                for declaration in ({}, None, {"id": "unreviewed", "applied": True}):
                    with self.subTest(key=key, declaration=declaration):
                        data = self.receipt(asset)
                        data[key] = declaration
                        receipt.write_text(json.dumps(data))
                        with self.assertRaises(probe.Blocked):
                            probe.select_artifact_contract(
                                types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})

    def test_numeric_fixes_require_each_reviewed_patch_and_the_matching_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"synthetic patched engine")
            manifest = json.loads(probe.NUMERIC_PATCH_MANIFEST.read_text())
            keys = ("id", "component", "path", "before_sha256", "after_sha256", "patch_sha256")
            data = self.receipt(asset)
            data["numeric_patchset"] = {
                "id": manifest["id"], "manifest_sha256": probe.digest(probe.NUMERIC_PATCH_MANIFEST),
                "applied": True, "patches": [{k: p[k] for k in keys} for p in manifest["patches"]]}
            data["compiler"] = {key: manifest["toolchain"][value] for key, value in {
                "version": "emscripten_version", "commit": "emscripten_commit",
                "emsdk_commit": "emsdk_repo_commit", "release": "emsdk_release_commit"}.items()}
            receipt = root / "build.json"
            receipt.write_text(json.dumps(data))
            report = {}
            probe.select_artifact_contract(types.SimpleNamespace(asset=asset, source_build_receipt=receipt), report)
            self.assertTrue(report["source_build"]["numeric_fixes_declared"])
            self.assertEqual(report["candidate"]["numeric_patchset_id"], manifest["id"])
            self.assertFalse(report["source_correspondence_verified"])
            for defect in ("changed_source", "missing_patch", "foreign_compiler", "changed_manifest"):
                with self.subTest(defect=defect):
                    changed = json.loads(json.dumps(data))
                    if defect == "changed_source":
                        changed["numeric_patchset"]["patches"][0]["after_sha256"] = "0" * 64
                    elif defect == "missing_patch":
                        changed["numeric_patchset"]["patches"].pop()
                    elif defect == "foreign_compiler":
                        changed["compiler"]["commit"] = "0" * 40
                    else:
                        changed["numeric_patchset"]["manifest_sha256"] = "0" * 64
                    receipt.write_text(json.dumps(changed))
                    with self.assertRaises(probe.Blocked):
                        probe.select_artifact_contract(
                            types.SimpleNamespace(asset=asset, source_build_receipt=receipt), {})

    def test_changed_source_artifact_is_refused_before_unpacking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "development.tar.gz"
            asset.write_bytes(b"original bytes")
            receipt = root / "build.json"
            receipt.write_text(json.dumps(self.receipt(asset)))
            asset.write_bytes(b"modified bytes")
            args = types.SimpleNamespace(output=root, asset=asset, source_build_receipt=receipt)
            with self.assertRaisesRegex(probe.Blocked, "artifact does not match"):
                probe.probe(args, {"artifact": {}})

    def test_reviewed_dependency_receipts_are_distinct_and_portable_without_old_passes(self):
        for kinds in (("sqlite",), ("codec",), ("sqlite", "codec")):
            with self.subTest(kinds=kinds), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                asset, data = self.dependency_receipt(root, kinds)
                report = self.qualify_dependency_receipt(root, asset, data)
                self.assertFalse(report["source_correspondence_verified"])
                self.assertTrue(report["source_build_receipt_verified"])
                for kind in kinds:
                    validated = report["source_build"][kind + "_patchset"]
                    self.assertEqual(report["candidate"][kind + "_patchset_id"], data[kind + "_patchset"]["id"])
                    self.assertTrue(validated["application_sidecar_locally_verified"])
                    self.assertTrue(validated["dependency_recipe_snapshot_locally_verified"])
                    self.assertFalse(validated["runtime_test_passes_inferred"])
                    Path(data[kind + "_patchset"]["application_receipt"]["path"]).unlink()
                Path(data["dependency_recipe_manifest"]["path"]).unlink()
                if "codec" in kinds:
                    Path(data["codec_patchset"]["oiio_configuration"]["path"]).unlink()
                relocated = self.qualify_dependency_receipt(root, asset, data)
                for kind in kinds:
                    validated = relocated["source_build"][kind + "_patchset"]
                    self.assertFalse(validated["application_sidecar_locally_verified"])
                    self.assertFalse(validated["dependency_recipe_snapshot_locally_verified"])

    def test_patch_receipt_tampering_cannot_pass_with_the_same_artifact_digest(self):
        defects = ("applied", "status", "manifest", "manifest_bytes", "helper", "missing_output", "duplicate_output",
                   "output_hash", "output_size_bool", "compiler", "application_schema", "application_missing",
                   "insertion", "order", "execution_order", "recipe", "snapshot", "sidecar", "embedded_application")
        for kind in ("sqlite", "codec"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                asset, original = self.dependency_receipt(root, (kind,))
                for defect in defects:
                    with self.subTest(kind=kind, defect=defect):
                        data = copy.deepcopy(original)
                        item = data[kind + "_patchset"]
                        if defect == "applied": item["applied"] = 1
                        elif defect == "status": item["status"] = "verified_inputs"
                        elif defect == "manifest": item["manifest_sha256"] = "0" * 64
                        elif defect == "manifest_bytes": item["manifest"]["bytes"] += 1
                        elif defect == "helper": item["application_helper"]["sha256"] = "0" * 64
                        elif defect == "missing_output": item["outputs"].pop()
                        elif defect == "duplicate_output": item["outputs"][-1] = item["outputs"][0]
                        elif defect == "output_hash": item["outputs"][0]["sha256"] = "0" * 64
                        elif defect == "output_size_bool": item["outputs"][0]["bytes"] = True
                        elif defect == "compiler": data["compiler"]["commit"] = "0" * 40
                        elif defect == "application_schema": item["application"]["schema"] = True
                        elif defect == "application_missing": del item["application"]
                        elif defect == "insertion": item["dependency_insertion"]["before"] = "numpy"
                        elif defect == "order": data["dependency_order"].append(data["dependency_order"][0])
                        elif defect == "execution_order": data["dependency_receipts"].reverse()
                        elif defect == "recipe":
                            selected = "python" if kind == "sqlite" else "openimageio"
                            next(row for row in data["dependency_receipts"] if row["name"] == selected)["recipe"]["sha256"] = "0" * 64
                        elif defect == "snapshot": data["dependency_recipe_manifest"]["sha256"] = "0" * 64
                        elif defect == "sidecar": item["application_receipt"]["sha256"] = "0" * 64
                        else: item["application"]["port_root"] = "/different-sidecar-context"
                        with self.assertRaises(probe.Blocked):
                            self.qualify_dependency_receipt(root, asset, data)

    def test_independent_manifest_cannot_be_replaced_by_a_self_consistent_declaration(self):
        for kind in ("sqlite", "codec"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                asset, data = self.dependency_receipt(root, (kind,))
                original = probe.SQLITE_PATCH_MANIFEST if kind == "sqlite" else probe.CODEC_PATCH_MANIFEST
                changed = root / "manifest.json"
                changed.write_bytes(original.read_bytes() + b" ")
                data[kind + "_patchset"]["manifest"] = self.file_record(changed)
                data[kind + "_patchset"]["manifest_sha256"] = self.file_record(changed)["sha256"]
                with patch.object(probe, kind.upper() + "_PATCH_MANIFEST", changed), self.assertRaises(probe.Blocked):
                    self.qualify_dependency_receipt(root, asset, data)

    def test_sqlite_preimage_inputs_and_full_sdk_identity_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset, original = self.dependency_receipt(root, ("sqlite",))
            for defect in ("preimage", "inputs", "embedded_outputs", "environment", "tests_modified", "sdk", "release"):
                with self.subTest(defect=defect):
                    data = copy.deepcopy(original)
                    application = data["sqlite_patchset"]["application"]
                    if defect == "preimage": application["original_python_recipe"]["sha256"] = "0" * 64
                    elif defect == "inputs": application["inputs"].pop()
                    elif defect == "embedded_outputs": application["outputs"][0]["sha256"] = "0" * 64
                    elif defect == "environment": application["environment"] = {}
                    elif defect == "tests_modified": application["source_tests_modified"] = True
                    elif defect == "sdk": data["compiler"]["emsdk_commit"] = "0" * 40
                    else: data["compiler"]["release"] = "0" * 40
                    with self.assertRaises(probe.Blocked):
                        self.qualify_dependency_receipt(root, asset, data)

    def test_codec_preimages_and_both_build_feature_profiles_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset, original = self.dependency_receipt(root, ("codec",))
            for defect in ("preimage", "missing_null_preimage", "postimage", "mixed_already_applied", "blender_flag",
                           "contradictory_disabled_flag", "oiio_flag", "oiio_cache", "duplicate_file"):
                with self.subTest(defect=defect):
                    data = copy.deepcopy(original)
                    item = data["codec_patchset"]
                    if defect == "preimage": item["application"]["files"][0]["observed_before_sha256"] = "0" * 64
                    elif defect == "missing_null_preimage":
                        row = next(row for row in item["application"]["files"] if row["before_sha256"] is None)
                        del row["observed_before_sha256"]
                    elif defect == "postimage": item["application"]["files"][0]["observed_after_sha256"] = "0" * 64
                    elif defect == "mixed_already_applied": item["application"]["application"] = "already_applied_exact_bytes"
                    elif defect == "blender_flag": data["configured_features"]["WITH_IMAGE_CINEON"] = "OFF"
                    elif defect == "contradictory_disabled_flag": data["disabled_features"] = ["WITH_IMAGE_OPENJPEG"]
                    elif defect == "oiio_flag": item["configured_oiio_features"]["BUILD_SHARED_LIBS"] = "ON"
                    elif defect == "oiio_cache": item["oiio_configuration"]["sha256"] = "0" * 64
                    else: item["application"]["files"][-1] = item["application"]["files"][0]
                    with self.assertRaises(probe.Blocked):
                        self.qualify_dependency_receipt(root, asset, data)

    def test_codec_exact_reapplication_is_distinguished_from_mixed_preimages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset, data = self.dependency_receipt(root, ("codec",))
            item = data["codec_patchset"]
            item["application"]["application"] = "already_applied_exact_bytes"
            for row in item["application"]["files"]:
                row["observed_before_sha256"] = row["after_sha256"]
            path = Path(item["application_receipt"]["path"])
            path.write_text(json.dumps(item["application"]) + "\n")
            item["application_receipt"] = self.file_record(path)
            self.assertTrue(self.qualify_dependency_receipt(root, asset, data)["source_build"]["codecs_declared"])

    def test_matrix_snapshot_preserves_optional_manifests_and_excludes_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = {"tools/probe_browser_port.py", "tools/prepare_browser_sqlite.py",
                        "patches/browser-numerics/manifest.json", "patches/browser-sqlite/manifest.json",
                        "patches/browser-sqlite/sqlite.sh", "patches/browser-codecs/manifest.json",
                        "patches/browser-codecs/apply.py"}
            for name in expected | {"patches/browser-codecs/__pycache__/apply.cpython-312.pyc",
                                    "patches/browser-codecs/stale.pyc"}:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic snapshot fixture")
            (root / "patches/browser-codecs/alias.py").symlink_to(root / "tools/probe_browser_port.py")
            self.assertEqual({path.relative_to(root).as_posix() for path in harness_sources(root)}, expected)

    def test_optional_source_root_preserves_local_helpers_and_allows_pinned_downloads(self):
        catalog = {"suites": [{"upstream_path": "tests/python/original.py", "support_files": [
            {"upstream_path": "tests/python/helper.py"}]}]}
        self.assertEqual(suite_source_arguments(catalog, None), [])
        root = Path("/synthetic-original-source")
        self.assertEqual(suite_source_arguments(catalog, root), [
            "--suite", str(root / "tests/python/original.py"), "--suite", str(root / "tests/python/helper.py")])


if __name__ == "__main__":
    unittest.main()
