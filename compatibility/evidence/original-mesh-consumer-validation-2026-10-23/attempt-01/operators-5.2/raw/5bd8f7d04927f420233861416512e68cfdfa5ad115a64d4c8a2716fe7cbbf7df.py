#!/usr/bin/env python3
"""Execute one original source-derived full mesh-operators invocation, retaining raw results."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"
SOURCE_COMMIT = "fbe6228777e7d9afefcd61a413844e790ae75db7"
SOURCE_ARCHIVE_SHA256 = "de0fdadf28015805370d1815facaf9139fbb1e161d8c540d1765484beabb3a99"
CATALOG_SHA256 = "c326f9a99e665b15901dda134afd0c074c5c150441ed2971d977ce134a1fe7f2"
EXECUTABLE_SHA256 = "83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27"
FIXTURE_PATH = "tests/files/modeling/operators.blend"
SOURCE_PATHS = ("tests/CMakeLists.txt", "tests/python/CMakeLists.txt", "build_files/cmake/testing.cmake",
                "tests/python/operators.py", "tests/python/modules/mesh_test.py")


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def write_new(path, value):
    with path.open("x") as output:
        output.write(json.dumps(value, indent=2) + "\n")


def original_observations(text, declarations):
    starts = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.fullmatch(r"START (.+) test\.", line)
        if match:
            starts.append((index, match[1]))
    declared = {item["name"]: item for item in declarations}
    observations = []
    for position, (line_index, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        segment = lines[line_index + 1:end]
        passed = [line for line in segment if line == f"PASSED {name} test successfully."]
        failed = [line for line in segment if line == f"FAILED {name} test with the following: "]
        compare = [line.split(" : ", 1)[1] for line in segment if line.startswith("Mesh Comparison : ")]
        validate = [line.split(" : ", 1)[1] for line in segment if line.startswith("Mesh Validation : ")]
        if len(passed) == 1 and not failed and compare == ["Same"] and validate == ["Valid"]:
            state = "passed"
        elif len(failed) == 1 and not passed:
            state = "failed"
        else:
            state = "ambiguous_or_incomplete"
        row = {"name": name, "status": state, "start_log_line": line_index + 1,
               "terminal_log_lines": passed + failed, "mesh_comparison": compare, "mesh_validation": validate}
        if name in declared:
            row["original_source_declaration"] = declared[name]
        observations.append(row)
    seen = [row["name"] for row in observations]
    duplicate_names = sorted({name for name in seen if seen.count(name) > 1})
    missing = sorted(set(declared) - set(seen))
    unexpected = sorted(set(seen) - set(declared))
    return {"kind": "original-mesh-test-stdout-observations", "observations": observations,
            "observed_starts": len(observations),
            "observed_passes": sum(row["status"] == "passed" for row in observations),
            "observed_failures": sum(row["status"] == "failed" for row in observations),
            "observed_ambiguous_or_incomplete": sum(row["status"] == "ambiguous_or_incomplete" for row in observations),
            "duplicate_names": duplicate_names, "missing_declared_names": missing, "unexpected_names": unexpected,
            "static_declarations_used_only_to_detect_missing_or_unexpected_cases": True}


def main():
    if (HERE / "execution.json").exists() or (HERE / "prospective-command.json").exists():
        raise FileExistsError("this immutable attempt has already started")
    archive_path = RUNTIME / "upstream-5.2.tar.gz"
    archive_identity = identity(archive_path)
    assert archive_identity["sha256"] == SOURCE_ARCHIVE_SHA256
    catalog_path = REPO / "tools/upstream_invocations_5_2.json"
    assert identity(catalog_path)["sha256"] == CATALOG_SHA256
    catalog = json.loads(catalog_path.read_text())
    assert catalog["upstream_commit"] == SOURCE_COMMIT and len(catalog["declarations"]) == 132
    registration = catalog["declarations"][74]
    assert registration["line"] == 703 and registration["name"] == "add_blender_test"
    assert registration["context"] == [{"opener": "if(TEST_SRC_DIR_EXISTS)", "line": 702}]
    source = HERE / "source"
    source.mkdir(exist_ok=False)
    required = set(SOURCE_PATHS) | {FIXTURE_PATH}
    archived = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or "/" not in member.name:
                continue
            relative = member.name.split("/", 1)[1]
            if relative in required:
                if relative in archived:
                    raise ValueError("duplicate source archive member")
                archived[relative] = archive.extractfile(member).read()
    assert set(archived) == required
    for item in catalog["sources"]:
        data = archived[item["upstream_path"]]
        assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
    for relative in SOURCE_PATHS:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archived[relative])
    pointer = archived[FIXTURE_PATH]
    pointer_match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n", pointer)
    assert pointer_match is not None
    expected_sha, expected_bytes = pointer_match[1].decode(), int(pointer_match[2])
    fixture_source = RUNTIME / "upstream-product/blender-94363991e7dcf39e2d70614aa002ab6f67764a5d" / FIXTURE_PATH
    fixture_identity = identity(fixture_source)
    assert fixture_identity["sha256"] == expected_sha and fixture_identity["bytes"] == expected_bytes
    fixture = source / FIXTURE_PATH
    fixture.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fixture_source, fixture)
    (HERE / "original-fixture-pointer.txt").write_bytes(pointer)
    assert identity(fixture)["sha256"] == expected_sha
    test_script = source / "tests/python/operators.py"
    tree = ast.parse(test_script.read_text())
    original_main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    assignment = next(node for node in original_main.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "tests" for target in node.targets))
    assert isinstance(assignment.value, ast.List)
    declarations = []
    for node in assignment.value.elts:
        assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "SpecMeshTest"
        # Original constructor defaults retain the original mesh comparison policy.
        # This is an identity check, never a source of inferred runtime passes.
        assert len(node.args) == 4 and not node.keywords
        name = ast.literal_eval(node.args[0])
        assert isinstance(name, str)
        declarations.append({"name": name, "line": node.lineno, "upstream_path": "tests/python/operators.py",
                             "source_sha256": identity(test_script)["sha256"],
                             "spec_sha256": hashlib.sha256(ast.get_source_segment(test_script.read_text(), node).encode()).hexdigest()})
    assert len(declarations) == len({row["name"] for row in declarations}) == 105
    native = RUNTIME / "native/blender-5.2.0-linux-x64/blender"
    executable = identity(native)
    assert executable["sha256"] == EXECUTABLE_SHA256
    prior_path = REPO / "compatibility/evidence/unittest-native-5.2-2026-10-23/script_pyapi_bmesh/native_reference.json"
    prior = json.loads(prior_path.read_text())
    assert prior["executable"]["sha256"] == executable["sha256"]
    assert prior["official_release_checksum_verified"] and prior["upstream_build_hash_verified"]
    assert prior["upstream"]["commit"] == SOURCE_COMMIT
    argv = [str(native), "--background", "--console-crash-handler", "--factory-startup",
            "--debug-memory", "--debug-exit-on-error", "--python-exit-code", "1", "--python-expr",
            "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'",
            str(fixture), "--python", str(test_script), "--", "--run-all-tests"]
    env = os.environ.copy()
    if "BLENDER_TEST_UPDATE" in env:
        raise ValueError("original mesh oracle update environment must be absent")
    overrides = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
    env.update(overrides)
    inputs = [identity(source / relative) for relative in SOURCE_PATHS] + [identity(fixture)]
    prospective = {
        "schema": 1, "kind": "source-derived-original-blender-invocation", "source_commit": SOURCE_COMMIT,
        "configured_ctest_execution": False, "ctest_configuration_receipt": None,
        "original_declaration": registration, "declaration_catalog": identity(catalog_path),
        "source_archive": archive_identity, "native_executable": executable,
        "prior_native_release_receipt": identity(prior_path),
        "native_source_build_correspondence_verified": prior["source_correspondence_verified"],
        "capture_driver": identity(Path(__file__).resolve()), "command": argv, "cwd": str(HERE),
        "environment_overrides": overrides,
        "execution_environment": "Authorized elevated local execution, retaining the exact original command and inputs.",
        "test_selection": {"full_original_run_all_tests": True, "case_filter": None,
                           "failfast": False, "shard": None, "random_seed": "Original operators.py calls seed(0), unchanged."},
        "oracle_update_environment_absent": "BLENDER_TEST_UPDATE" not in env,
        "verbose_environment_present": "BLENDER_VERBOSE" in env,
        "thread_limit_scope": "OpenMP and numeric-library environment requests only; no claim that all Blender worker pools obey them",
        "timeout_seconds": 180, "minimum_disk_reserve_bytes": 4 * 1024 ** 3,
        "inputs": inputs, "fixture_original_pointer": identity(HERE / "original-fixture-pointer.txt"),
        "fixture_payload_source": fixture_identity, "fixture_expected_sha256": expected_sha,
        "fixture_expected_bytes": expected_bytes,
        "fixture_reuse_reason": "Payload is byte-identical to the original 5.2 archive's LFS pointer, independently of the newer source tree holding that payload.",
        "static_declared_specs": declarations, "static_declared_specs_are_runtime_results": False,
        "declaration_context": {"TEST_SRC_DIR_EXISTS": "Original check is presence of tests/files/render directory; present in the pinned 5.2 source tree, but no configured CTest inventory is claimed."},
        "original_sources_modified": False, "original_assertions_or_tolerances_modified": False,
        "original_comparison_mode": "The original --run-all-tests branch sets RunTest.do_compare=True.",
        "browser_tests_executed": False, "browser_test_passes": 0, "full_feature_parity": False,
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_new(HERE / "prospective-command.json", prospective)
    if shutil.disk_usage(HERE).free < prospective["minimum_disk_reserve_bytes"]:
        raise RuntimeError("insufficient disk reserve before launch")
    started = time.monotonic()
    peak_rss_kib, peak_threads, timed_out, termination = 0, 0, False, None
    sampled_procfs_identity_verified = False
    with (HERE / "original-driver.log").open("xb") as log:
        process = subprocess.Popen(argv, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        while process.poll() is None:
            elapsed = time.monotonic() - started
            try:
                procfs_command = Path(f"/proc/{process.pid}/cmdline").read_bytes().split(b"\0")
                if procfs_command and procfs_command[-1] == b"":
                    procfs_command.pop()
                if procfs_command != [argument.encode() for argument in argv]:
                    raise ProcessLookupError("procfs PID does not identify the actual Blender child")
                sampled_procfs_identity_verified = True
                status = Path(f"/proc/{process.pid}/status").read_text()
                rss = re.search(r"^VmRSS:\s+(\d+) kB$", status, re.M)
                threads = re.search(r"^Threads:\s+(\d+)$", status, re.M)
                peak_rss_kib = max(peak_rss_kib, int(rss[1]) if rss else 0)
                peak_threads = max(peak_threads, int(threads[1]) if threads else 0)
            except (FileNotFoundError, ProcessLookupError):
                pass
            if elapsed >= prospective["timeout_seconds"]:
                timed_out, termination = True, "180-second timeout"
            elif shutil.disk_usage(HERE).free < prospective["minimum_disk_reserve_bytes"]:
                termination = "minimum disk reserve reached"
            if termination:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                break
            time.sleep(0.1)
        returncode = process.wait()
    process_elapsed_seconds = time.monotonic() - started
    reconciliation = original_observations((HERE / "original-driver.log").read_text(errors="replace"), declarations)
    after = [identity(Path(item["path"])) for item in inputs]
    unchanged = after == inputs
    completed = (returncode == 0 and not timed_out and termination is None and unchanged
                 and not reconciliation["duplicate_names"] and not reconciliation["missing_declared_names"]
                 and not reconciliation["unexpected_names"] and reconciliation["observed_starts"] > 0
                 and reconciliation["observed_passes"] == reconciliation["observed_starts"])
    report = {"schema": 1, "kind": "source-derived-original-blender-native-execution",
              "prospective_command": identity(HERE / "prospective-command.json"),
              "capture_driver": identity(Path(__file__).resolve()), "native_executable": executable,
              "source_commit": SOURCE_COMMIT, "ctest_name_from_source": "operators",
              "configured_ctest_execution": False, "actual_process_started": True, "actual_process_returncode": returncode,
              "timed_out": timed_out, "termination_reason": termination,
              "elapsed_seconds": round(process_elapsed_seconds, 6),
              "finished_utc": datetime.now(timezone.utc).isoformat(),
              "sampled_process_peak_rss_kib": peak_rss_kib if sampled_procfs_identity_verified else None,
              "sampled_process_peak_thread_count": peak_threads if sampled_procfs_identity_verified else None,
              "sampled_procfs_identity_verified": sampled_procfs_identity_verified,
              "child_max_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
              "raw_log": identity(HERE / "original-driver.log"), "original_case_observations": reconciliation,
              "inputs_after": after, "all_original_inputs_unchanged": unchanged,
              "completed_successfully": completed, "original_blender_invocations_executed": 1,
              "browser_tests_executed": False, "browser_test_passes": 0, "full_feature_parity": False,
              "scope": "One source-derived original full CPU mesh-operators invocation in the authorized elevated local environment; not a configured CTest execution or a browser result."}
    write_new(HERE / "execution.json", report)
    print(json.dumps({key: report[key] for key in ("actual_process_returncode", "timed_out", "elapsed_seconds",
                     "sampled_process_peak_rss_kib", "sampled_process_peak_thread_count", "all_original_inputs_unchanged", "completed_successfully")}, indent=2))
    print(json.dumps({key: value for key, value in reconciliation.items() if key != "observations"}, indent=2))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
