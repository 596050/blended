#!/usr/bin/env python3
"""Read-only source/fixture audit; this script does not execute Blender tests."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"
SOURCE = RUNTIME / "upstream-5.2"
PRODUCT = RUNTIME / "upstream-product/blender-94363991e7dcf39e2d70614aa002ab6f67764a5d"
COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"
PLAN = REPO / "compatibility/evidence/unittest-native-5.2-2026-10-23/discovery-inventory.json"
CATALOG = REPO / "tools/upstream_invocations_5_2.json"
ARCHIVE = RUNTIME / "upstream-5.2.tar.gz"


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def test_script(row):
    match = re.search(r"\$\{(?:CMAKE_CURRENT_LIST_DIR|TEST_PYTHON_DIR)\}/([A-Za-z0-9_./-]+\.py)", row["registration"])
    return "tests/python/" + match[1] if match else None


def main():
    output = HERE / "proposed-next-invocations.json"
    if output.exists():
        raise FileExistsError("immutable proposal already exists")
    plan_identity, catalog_identity, archive_identity = identity(PLAN), identity(CATALOG), identity(ARCHIVE)
    assert catalog_identity["sha256"] == "c326f9a99e665b15901dda134afd0c074c5c150441ed2971d977ce134a1fe7f2"
    assert archive_identity["sha256"] == "de0fdadf28015805370d1815facaf9139fbb1e161d8c540d1765484beabb3a99"
    plan, catalog = json.loads(PLAN.read_text()), json.loads(CATALOG.read_text())
    assert plan["upstream_commit"] == catalog["upstream_commit"] == COMMIT
    assert len(plan["registrations"]) == len(catalog["declarations"]) == 132
    blocked = [row for row in plan["registrations"] if row["state"] == "blocked"]
    assert len(blocked) == 101
    for row in plan["registrations"]:
        original = catalog["declarations"][row["source_declaration_index"]]
        assert row["line"] == original["line"] and row["registration"] == original["text"] and row["context"] == original["context"]
    candidates = [
        {"index": 49, "priority": 1, "facet": "Mesh bevel geometry regression", "driver": "original RunTest/SpecMeshTest",
         "fixture_paths": ["tests/files/modeling/bevel_regression.blend"], "support_paths": ["tests/python/modules/mesh_test.py"],
         "reason": "88 distinct literal SpecMeshTest specifications compare generated geometry with original golden meshes and validate mesh integrity; no render or external comparator.",
         "cost": "Bounded finite geometry cases and a 2.39 MB input; expected low-to-moderate CPU cost from source review. Actual runtime must be measured.",
         "extra_prerequisites": ["Keep --run-all-tests exactly; --run-test disables comparison in the original script and cannot qualify a case.", "BLENDER_TEST_UPDATE must be absent so no original golden object can be rewritten.", "Preserve original stdout start/pass/fail and mesh-comparison/validation observations; do not derive outcomes from the static list."]},
        {"index": 74, "priority": 2, "facet": "Mesh editing operator geometry regression", "driver": "original RunTest/SpecMeshTest",
         "fixture_paths": ["tests/files/modeling/operators.blend"], "support_paths": ["tests/python/modules/mesh_test.py"],
         "reason": "105 distinct literal SpecMeshTest specifications cover a wider range of mesh operators with original golden geometry.",
         "cost": "Finite small modelling scenes, 4.03 MB fixture, no rendering; broader than bevel. Use a single bounded process and measure actual RSS/time.",
         "extra_prerequisites": ["Preserve original --run-all-tests, random seed, thresholds and golden geometry.", "BLENDER_TEST_UPDATE must be absent; do not select --run-test because it disables comparison."]},
        {"index": 93, "priority": 3, "facet": "Geometry, shader and compositor node-group interfaces", "driver": "original unittest __main__",
         "fixture_paths": ["tests/files/node_group/empty.blend"], "support_paths": [],
         "reason": "Node socket types, ordering, panels, insertion/removal and iteration across three node systems; 22 declared test methods include inherited mixin methods, so declarations are not a runtime denominator.",
         "cost": "Small 79,690-byte empty scene and data-model operations; expected low CPU cost, no rendering or image oracle.",
         "extra_prerequisites": ["Retain the original --testdir and __main__ argparse/unittest path; freeze actual inherited leaf IDs from execution."]},
        {"index": 73, "priority": 4, "facet": "Object and bone constraints", "driver": "original unittest __main__",
         "fixture_paths": ["tests/files/constraints/constraints.blend"], "support_paths": [],
         "reason": "14 declared test methods cover child-of, object solver, custom spaces, copy transforms, action slots and geometry-attribute constraints with original numerical assertions.",
         "cost": "933,385-byte scene, transform/dependency evaluation and subtest loops; expected low CPU cost, no renderer.",
         "extra_prerequisites": ["Preserve exact numeric tolerances and all original subtest outcomes; bind the single fixture before execution."]},
        {"index": 54, "priority": 5, "facet": "Mesh joining, material indices, shape keys and face sets", "driver": "original unittest __main__",
         "fixture_paths": [], "support_paths": [],
         "reason": "Ten original declared methods generate their own meshes, including shared object data and shape keys. No LFS input is required by the script.",
         "cost": "Primitive geometry and small generated meshes; expected low CPU/memory cost with no renderer.",
         "extra_prerequisites": ["The original registration is conditional on TEST_SRC_DIR_EXISTS even though this script does not load a fixture; preserve that source context."]},
        {"index": 41, "priority": 6, "facet": "Blend-file serialization, partial saves and runtime IDs", "driver": "original TestHelper.run_all_tests",
         "fixture_paths": [], "support_paths": ["tests/python/bl_blendfile_utils.py"],
         "reason": "Four explicitly declared methods across three original helper classes create, save, reopen and link their own data; this expands file IO beyond existing API-only cohorts.",
         "cost": "A handful of generated blend files and save/reopen operations; expected low-to-moderate filesystem cost. Requires a writable isolated output directory.",
         "extra_prerequisites": ["Preserve TestHelper's direct callable loop, setup/teardown and exception propagation; do not replace it with unittest loading.", "Retain --output-dir in the original argument position and bind generated outputs separately.", "Per-method results need a reviewed observer or must remain invocation-level; a zero process exit alone is not four measured leaf passes."]},
        {"index": 59, "priority": 7, "facet": "Geometry node tools and object inputs", "driver": "original unittest __main__",
         "fixture_paths": [], "support_paths": [],
         "reason": "Four declared methods construct node tools and exercise their original operators on generated meshes.",
         "cost": "Generated small object/node graphs; expected low CPU cost. Original context operators still need actual execution.",
         "extra_prerequisites": ["Retain operator context and the source conditional registration; do not replace operator calls with direct API equivalents."]},
        {"index": 117, "priority": 8, "facet": "Video sequencer strip naming", "driver": "original unittest __main__",
         "fixture_paths": [], "support_paths": [],
         "reason": "Six declared methods create meta strips and assert exact duplicate-name handling; expands the sequencer facet without video decoding or rendering.",
         "cost": "Small metadata-only CPU operations, no media input files.",
         "extra_prerequisites": ["Retain original sequence-editor setup/teardown and source registration condition."]},
    ]
    requested = {path for row in blocked if (path := test_script(row))}
    requested.update({"tests/CMakeLists.txt", "tests/python/CMakeLists.txt", "build_files/cmake/testing.cmake"})
    requested.update(path for row in candidates for path in row["fixture_paths"] + row["support_paths"])
    members = {}
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or "/" not in member.name:
                continue
            relative = member.name.split("/", 1)[1]
            if relative in requested:
                assert relative not in members
                members[relative] = archive.extractfile(member).read()
    source_bindings = {}
    for path, data in members.items():
        local = SOURCE / path
        assert local.is_file() and local.read_bytes() == data
        source_bindings[path] = {"upstream_path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                 "matches_exact_source_archive": True}
    audit_rows = []
    candidate_indices = {row["index"] for row in candidates}
    for row in blocked:
        index = row["source_declaration_index"]
        original = catalog["declarations"][index]
        contexts = [context["opener"] for context in row["context"]]
        path = test_script(row)
        if any(context.startswith("function(") for context in contexts):
            category = "helper_declaration_not_one_runtime_test"
        elif original["name"].startswith("add_blender_test_ui") or any("UI_TESTS" in context for context in contexts):
            category = "ui_environment_required"
        elif "gpu-backend" in row["registration"] or "--mode=GPU" in row["registration"]:
            category = "gpu_or_disabled_backend_registration"
        elif any(context.startswith("foreach(") for context in contexts):
            category = "generated_registration_requires_configured_inventory"
        elif path and path not in members:
            category = "referenced_script_absent_from_pinned_source_archive"
        elif index in candidate_indices:
            category = "detailed_cpu_candidate"
        elif original["name"] == "add_blender_test_allow_error":
            category = "error_allowing_original_driver_requires_separate_adapter"
        elif path and b"unittest.main" in members[path]:
            category = "unittest_resource_or_configuration_closure_not_detailed_here"
        else:
            category = "custom_driver_or_embedded_text_requires_separate_adapter"
        entry = {"source_declaration_index": index, "line": row["line"], "registration": row["registration"],
                 "context": row["context"], "frozen_state": row["state"], "frozen_reason": row["reason"],
                 "read_only_audit_category": category, "registration_authenticated": True}
        if path:
            entry["test_script"] = path
            entry["source_binding"] = source_bindings.get(path)
            if path in members:
                tree = ast.parse(members[path].decode())
                entry["static_declared_test_method_count"] = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") for node in ast.walk(tree))
                entry["static_count_is_runtime_inventory"] = False
        audit_rows.append(entry)
    native_path = RUNTIME / "native/blender-5.2.0-linux-x64/blender"
    native_identity = identity(native_path)
    assert native_identity["sha256"] == "83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27"
    base_args = ["--background", "--console-crash-handler", "--factory-startup", "--debug-memory",
                 "--debug-exit-on-error", "--python-exit-code", "1", "--python-expr",
                 "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'"]
    substitutions = {"${CMAKE_CURRENT_LIST_DIR}": str(SOURCE / "tests/python"), "${TEST_PYTHON_DIR}": str(SOURCE / "tests/python"),
                     "${TEST_SRC_DIR}": str(SOURCE / "tests/files"), "${TEST_OUT_DIR}": str(RUNTIME / "proposed-original-5.2-output/tests")}
    for candidate in candidates:
        row = plan["registrations"][candidate["index"]]
        original = catalog["declarations"][candidate["index"]]
        candidate["original_registration"] = original
        candidate["test_script"] = test_script(row)
        candidate["source_closure"] = [source_bindings[path] for path in [candidate["test_script"]] + candidate["support_paths"]]
        args = shlex.split(original["arguments"], comments=True)
        candidate["ctest_name_from_source"] = args.pop(0)
        for old, new in substitutions.items():
            args = [value.replace(old, new) for value in args]
        assert not any("${" in value for value in args)
        candidate["proposed_argv_after_prerequisites"] = [str(native_path)] + base_args + args
        candidate["proposed_execution_kind"] = "source-derived original invocation unless a real configured CTest receipt is obtained"
        candidate["original_context_condition_status"] = {
            "TEST_SRC_DIR_EXISTS": (SOURCE / "tests/files/render").is_dir(),
            "basis": "Original CMake checks only whether tests/files/render is a directory; this audit did not configure CMake."}
        candidate["fixture_availability"] = []
        for path in candidate["fixture_paths"]:
            pointer = members[path]
            match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n", pointer)
            assert match
            cached = PRODUCT / path
            actual = identity(cached)
            assert actual["sha256"] == match[1].decode() and actual["bytes"] == int(match[2])
            candidate["fixture_availability"].append({"upstream_path": path, "original_pointer": source_bindings[path],
                                                     "expected_sha256": match[1].decode(), "expected_bytes": int(match[2]),
                                                     "verified_available_payload": actual, "exact_5_2_payload_available": True,
                                                     "original_5_2_tree_still_contains_pointer": True,
                                                     "materialization_performed_by_this_audit": False})
        tree = ast.parse(members[candidate["test_script"]].decode())
        candidate["static_declared_test_methods"] = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
        specs = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "SpecMeshTest"]
        candidate["static_literal_mesh_specs"] = [{"name": ast.literal_eval(node.args[0]), "line": node.lineno} for node in specs]
        candidate["static_lists_are_native_outcomes"] = False
        candidate["runtime_leaf_inventory"] = None
        candidate["recommended_initial_timeout_seconds"] = 180
        candidate["expected_cost_is_measured"] = False
        candidate["common_prerequisites"] = [
            "Use the exact original script/helper closure and original invocation flags; hash all inputs before and after.",
            "For fixtures, materialize the pointer-verified original payload at its original relative path in a separately recorded staging tree; copying a file merely because it comes from another Blender version is insufficient.",
            "Freeze actual runtime identities and original subtest/driver results; process completion and stdout agreement must both be retained.",
            "A native process result contributes no browser passes. A new browser artifact needs independent original invocation execution.",
            "The current unittest-main manifest validator rejects conditional registrations; extend only with independent configured CTest/source context evidence, never bypass that check or edit the frozen plan.",
        ]
    report = {"schema": 1, "kind": "read-only-proposed-original-invocations", "created_utc": datetime.now(timezone.utc).isoformat(),
              "audit_driver": identity(Path(__file__).resolve()), "source_commit": COMMIT, "frozen_plan": plan_identity,
              "declaration_catalog": catalog_identity, "source_archive": archive_identity, "native_executable": native_identity,
              "reviewed_source_declarations": 132, "retained_unexpanded_declarations": 101,
              "detailed_cpu_candidates": len(candidates), "all_101_authenticated_and_retained": len(audit_rows) == 101,
              "review_depth": "All 101 blocked declarations authenticated and categorized; eight CPU candidates received detailed source, original-driver and exact fixture checks.",
              "category_counts": dict(sorted(Counter(row["read_only_audit_category"] for row in audit_rows).items())),
              "proposed_candidates": candidates, "unexpanded_declaration_audit": audit_rows,
              "additional_followup": {"name": "bl_sculpt_brushes", "source_declaration_index": 126,
                                      "reason": "Substantial 65-method brush/stroke suite with generated meshes, native Essentials asset and numpy; original view3D context and multi-backend subtest behavior need a separate audit before calling it CPU-only and execution-ready."},
              "configured_ctest_inventory": False, "frozen_plan_modified": False,
              "test_sources_or_assertions_modified": False, "resources_downloaded": 0,
              "tests_executed_by_this_audit": 0, "native_passes_claimed_by_this_audit": 0,
              "browser_passes_claimed_by_this_audit": 0, "complete_test_denominator": False, "full_feature_parity": False,
              "separate_authorized_execution_evidence": ["compatibility/evidence/bmesh-bevel-source-native-5.2-2026-10-23/",
                                                        "compatibility/evidence/bmesh-bevel-source-native-elevated-5.2-2026-10-23/"],
              "separate_execution_note": "The parent separately authorized one bounded bevel invocation and one environment retry. Their raw outcomes are not imported into this proposed-invocation audit."}
    assert identity(PLAN) == plan_identity and identity(CATALOG) == catalog_identity
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": identity(output), "category_counts": report["category_counts"]}, indent=2))


if __name__ == "__main__":
    main()
