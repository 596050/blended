"""Hash-bound original unittest invocations with an independent native inventory.

The external contract runs one complete upstream script per fresh process. Its
case denominator comes from unittest's actual native loader, including
``load_tests``, rather than method-name scanning or browser discovery. This is
selected-script evidence; it does not certify all Blender CTests or features.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex

UPSTREAM_SHA = "fbe6228777e7d9afefcd61a413844e790ae75db7"
NATIVE_ARCHIVE_SHA256 = "96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48"
NATIVE_ARCHIVE_BYTES = 384441228
CTEST_BLENDER_ARGS = [
    "--background", "--console-crash-handler", "--factory-startup", "--debug-memory",
    "--debug-exit-on-error", "--python-exit-code", "1", "--python-expr",
    "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'",
]
CMAKE_SOURCES = [
    {"upstream_path": "tests/CMakeLists.txt", "bytes": 5871,
     "sha256": "1170647b903d4d730c938a57b44b3aebcbc0f424bcf1c6efa67b5fd55bbc4b3c"},
    {"upstream_path": "tests/python/CMakeLists.txt", "bytes": 50161,
     "sha256": "d787d904f8488ccada448a062dae412255eee5e5a8a2daa605351fe9e204248c"},
]
_SHA256 = re.compile(r"[0-9a-f]{64}")
_PATH = re.compile(r"tests/python/[A-Za-z0-9_./-]+\.py")
_MAX_JSON_BYTES = 32 * 1024 * 1024


class ManifestError(ValueError):
    """An invocation, its source identity, or its frozen evidence is incomplete."""


def require(condition, message):
    if not condition:
        raise ManifestError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "duplicate JSON field in candidate evidence: " + key)
        value[key] = item
    return value


def read_bound_json(path, expected_sha256, expected_bytes=None, label="manifest"):
    path = Path(path)
    require(isinstance(expected_sha256, str) and _SHA256.fullmatch(expected_sha256), label + " checksum is required")
    require(path.is_file(), label + " file is missing")
    require(0 < path.stat().st_size <= _MAX_JSON_BYTES, label + " exceeds its byte bound")
    data = path.read_bytes()
    require(digest(data) == expected_sha256, label + " checksum changed")
    require(expected_bytes is None or expected_bytes == len(data), label + " byte count changed")
    try:
        value = json.loads(data, object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ManifestError(label + " is not valid JSON") from error
    require(isinstance(value, dict), label + " must be an object")
    return value


def case_id(value):
    """Remove only __main__; preserve imported classes' qualified module names."""
    require(isinstance(value, str) and "." in value, "native case ID is invalid")
    return value.removeprefix("__main__.")


def _source(row):
    require(isinstance(row, dict), "upstream source metadata must be an object")
    path = row.get("upstream_path")
    require(isinstance(path, str) and _PATH.fullmatch(path) and ".." not in PurePosixPath(path).parts,
            "source path must be a confined original tests/python script")
    require(isinstance(row.get("sha256"), str) and _SHA256.fullmatch(row["sha256"]), "source checksum is invalid")
    require(type(row.get("bytes")) is int and 0 < row["bytes"] <= 4 * 1024 * 1024, "source byte count is invalid")


def validate_manifest(value, *, allow_discovery=False):
    require(value.get("schema") == 2 and value.get("suite_kind") == "unittest-main", "unsupported original unittest manifest schema or driver")
    require(value.get("stage") in ("native-discovery", "frozen"), "manifest discovery stage is invalid")
    require(value["stage"] == "frozen" or allow_discovery, "independent native discovery must freeze the case inventory before browser execution")
    require(value.get("upstream") == {"repository": "blender/blender", "commit": UPSTREAM_SHA}, "manifest differs from the pinned Blender 5.2 source")
    require(isinstance(value.get("cohort_id"), str) and re.fullmatch(r"[A-Za-z0-9_.-]+", value["cohort_id"]), "cohort identity is invalid")
    suites = value.get("suites")
    require(isinstance(suites, list) and len(suites) == 1, "one original script per process is required for CTest isolation")
    row = suites[0]
    _source(row)
    support = row.get("support_files", [])
    require(isinstance(support, list) and len(support) <= 32, "support file inventory is invalid")
    for helper in support:
        _source(helper)
    try:
        from .upstream_resources import validate_resources
    except ImportError:
        from upstream_resources import validate_resources
    validate_resources(row.get("resource_files", []))
    paths = [entry["upstream_path"] for entry in [row, *support]]
    require(len(paths) == len(set(paths)), "duplicate original source or helper path")
    execution = value.get("execution")
    require(isinstance(execution, dict), "original invocation context is missing")
    require(execution.get("entrypoint") == "original __main__" and execution.get("process_isolation") == "one-upstream-script",
            "original entrypoint and process isolation must be preserved")
    require(execution.get("background") is True, "this adapter requires the original background CTest context")
    require(execution.get("cmake_sources") == CMAKE_SOURCES, "pinned original CMake invocation sources changed")
    require(execution.get("blender_args") == CTEST_BLENDER_ARGS, "complete original CTest Blender flags must be retained")
    name, registration = execution.get("ctest_name"), execution.get("registration")
    require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_]+", name), "original CTest name is missing")
    require(isinstance(registration, str) and len(registration) < 8192 and
            re.search(r"add_blender_test\s*\(\s*" + re.escape(name) + r"\s+", registration) and
            ("/" + PurePosixPath(row["upstream_path"]).name) in registration,
            "original CMake registration must name the complete script")
    arguments = execution.get("script_args")
    require(isinstance(arguments, list) and len(arguments) <= 64 and
            all(isinstance(arg, str) and len(arg) <= 4096 and "\x00" not in arg for arg in arguments),
            "original script arguments must be an explicit bounded vector")
    try:
        registered = shlex.split(registration[registration.index("(") + 1:registration.rindex(")")], comments=True)
    except ValueError as error:
        raise ManifestError("original CMake registration cannot be parsed") from error
    source_relative = row["upstream_path"].removeprefix("tests/python/")
    require(len(registered) >= 3 and registered[:2] == [name, "--python"] and
            registered[2] in ("${CMAKE_CURRENT_LIST_DIR}/" + source_relative, "${TEST_PYTHON_DIR}/" + source_relative),
            "original registration must execute the exact complete Python script")
    trailing = registered[3:]
    require(not trailing or trailing[0] == "--", "additional Blender invocation arguments need a reviewed driver")
    registered_arguments = [arg.replace("${TEST_SRC_DIR}", "{fixture_root}") for arg in trailing[1:]] if trailing else []
    require(arguments == registered_arguments, "script arguments differ from the original CMake registration")
    require(not any(arg in ("-k", "--keyword", "--failfast", "-f", "--generate", "--skip-stubs") or
                    arg.startswith(("-k=", "--keyword=", "--generate=")) for arg in arguments),
            "test filtering, reference regeneration, or fail-fast cannot reduce the native denominator")
    fixtures = row.get("fixture_files", [])
    require(isinstance(fixtures, list), "fixture inventory must be explicit")
    if fixtures:
        try:
            from .probe_blender_fixtures import _validate_rows
        except ImportError:
            from probe_blender_fixtures import _validate_rows
        _validate_rows(fixtures, UPSTREAM_SHA)
        require(execution.get("fixture_mount") == "original-tests-files" or any("{fixture_root}" in arg for arg in arguments),
                "fixture inventory has no original source-relative or CLI mount")
    else:
        require(not any("{fixture_root}" in arg for arg in arguments), "original fixture arguments require pinned fixture bytes")
    host_tools = execution.get("host_tools", [])
    require(isinstance(host_tools, list) and len(host_tools) <= 8, "host tool inventory is invalid")
    for tool in host_tools:
        require(isinstance(tool, dict) and tool.get("environment") in ("IDIFF_BIN", "PYTHON_BIN") and
                isinstance(tool.get("sha256"), str) and _SHA256.fullmatch(tool["sha256"]) and
                type(tool.get("bytes")) is int and tool["bytes"] > 0, "original host tool identity is invalid")
    require(len({tool["environment"] for tool in host_tools}) == len(host_tools), "duplicate original host tool")
    if value["stage"] == "native-discovery":
        require(not any(key in row for key in ("case_ids", "expected_cases", "mandatory_case_ids")),
                "native discovery input must not preselect case IDs")
        require("expected_total_cases" not in value and "native_discovery" not in value,
                "native discovery input must not declare a frozen denominator")
    else:
        ids = row.get("case_ids")
        require(isinstance(ids, list) and ids and all(isinstance(x, str) and x for x in ids) and len(ids) == len(set(ids)),
                "frozen native case inventory is empty or duplicated")
        require(row.get("mandatory_case_ids") == ids and row.get("expected_cases") == len(ids) and
                value.get("expected_total_cases") == len(ids), "frozen mandatory denominator changed")
    return value


def validate_native_discovery(manifest, receipt, proposal_sha256):
    require(receipt.get("profile") == "native-reference" and receipt.get("official_release_checksum_verified") is True,
            "native discovery requires an independently checksum-verified official release")
    require(receipt.get("upstream") == manifest["upstream"] or
            (receipt.get("upstream", {}).get("repository") == "blender/blender" and
             receipt.get("upstream", {}).get("commit") == UPSTREAM_SHA), "native discovery source pin changed")
    artifact = receipt.get("artifact", {})
    require(artifact.get("observed_sha256") == NATIVE_ARCHIVE_SHA256 and artifact.get("observed_bytes") == NATIVE_ARCHIVE_BYTES,
            "native discovery artifact identity changed")
    require(receipt.get("cohort", {}).get("manifest_sha256") == proposal_sha256, "native discovery does not bind the original proposal")
    require(receipt.get("process", {}).get("flags") == manifest["execution"]["blender_args"], "native discovery CTest arguments changed")
    require(type(receipt.get("process", {}).get("returncode")) is int and receipt["process"]["returncode"] in (0, 1),
            "native discovery process did not finish with an original unittest exit code")
    transport = receipt.get("transport", {})
    require(transport.get("result_markers") == 1 and not transport.get("trailing_runtime_text"), "native discovery transport is incomplete")
    result = receipt.get("execution", {})
    require(isinstance(result, dict) and result.get("exception") is None, "native discovery did not complete the original script")
    identity = result.get("identity", {})
    require(identity.get("version") == [5, 2, 0] and identity.get("build_hash") in (UPSTREAM_SHA, UPSTREAM_SHA[:12]), "native discovery build identity differs")
    require(result.get("execution_context", {}).get("background") is True, "native discovery did not observe the original background context")
    observed = result.get("driver_observation", {})
    require(observed.get("entrypoint") == "original __main__" and observed.get("runner_invocations") == 1,
            "native discovery did not observe one original unittest invocation")
    require(observed.get("failfast") is False, "native discovery used fail-fast")
    sources, results = receipt.get("suite_sources"), result.get("suites")
    require(isinstance(sources, list) and len(sources) == 1 and isinstance(results, list) and len(results) == 1,
            "native discovery must contain the whole single-script invocation")
    expected = manifest["suites"][0]
    for key in ("upstream_path", "sha256", "bytes", "fixture_files", "resource_files"):
        require(sources[0].get(key, []) == expected.get(key, []), "native discovery source or fixture inventory changed: " + key)
    source_fields = ("upstream_path", "sha256", "bytes")
    observed_helpers = [{key: helper.get(key) for key in source_fields} for helper in sources[0].get("support_files", [])]
    expected_helpers = [{key: helper.get(key) for key in source_fields} for helper in expected.get("support_files", [])]
    require(observed_helpers == expected_helpers, "native discovery support source inventory changed")
    expected_resources = [{key: resource.get(key) for key in source_fields} for resource in expected.get("resource_files", [])]
    require(observed.get("resource_files", []) == expected_resources, "native discovery original resource bytes were not observed")
    tools_by_name = {tool.get("environment"): tool for tool in observed.get("host_tools", [])}
    for tool in manifest["execution"].get("host_tools", []):
        actual = tools_by_name.get(tool["environment"], {})
        require(actual.get("available") is True and actual.get("sha256") == tool["sha256"] and actual.get("bytes") == tool["bytes"],
                "native discovery original host tool identity was not observed")
    require(sources[0].get("driver_execution") == manifest["execution"], "native discovery lost original invocation context")
    row = results[0]
    require(row.get("upstream_path") == expected["upstream_path"] and row.get("sha256") == expected["sha256"], "native discovery executed different source bytes")
    ids = row.get("discovered_ids")
    require(isinstance(ids, list) and ids and all(isinstance(x, str) for x in ids) and len(ids) == len(set(ids)) and
            row.get("discovered") == len(ids), "native discovery inventory is empty, duplicated, or truncated")
    require(not any("._FailedTest." in value for value in ids), "native loader failure is not a complete test inventory")
    normalized = [case_id(value) for value in ids]
    require(len(normalized) == len(set(normalized)), "normalized native case IDs are ambiguous")
    return normalized


def load_manifest(path, expected_sha256, *, allow_discovery=False):
    path = Path(path).resolve()
    value = validate_manifest(read_bound_json(path, expected_sha256), allow_discovery=allow_discovery)
    row = copy.deepcopy(value["suites"][0])
    if value["stage"] == "frozen":
        pin = value.get("native_discovery", {})
        require(isinstance(pin.get("path"), str), "native discovery receipt path is missing")
        receipt = read_bound_json(path.parent / pin["path"], pin.get("sha256"), pin.get("bytes"), "native discovery")
        ids = validate_native_discovery(value, receipt, value.get("discovery_manifest_sha256"))
        require(row["case_ids"] == ids, "frozen cases differ from the independently observed native case inventory")
    row.update(driver="unittest-main", required_background=True, driver_execution=copy.deepcopy(value["execution"]),
               case_id_normalization="original-main")
    return {"id": value["cohort_id"], "manifest_sha256": expected_sha256, "stage": value["stage"],
            "expected_cases": value.get("expected_total_cases"), "suite_kind": "unittest-main", "suites": [row],
            "blender_args": value["execution"]["blender_args"], "original_invocation": value["execution"],
            "native_discovery": value.get("native_discovery")}


def freeze_manifest(proposal_path, proposal_sha256, receipt_path, destination):
    proposal_path, receipt_path, destination = Path(proposal_path), Path(receipt_path).resolve(), Path(destination).resolve()
    value = validate_manifest(read_bound_json(proposal_path, proposal_sha256), allow_discovery=True)
    require(value["stage"] == "native-discovery", "only a fresh native discovery proposal can be frozen")
    data = receipt_path.read_bytes()
    receipt = read_bound_json(receipt_path, digest(data), len(data), "native discovery")
    ids = validate_native_discovery(value, receipt, proposal_sha256)
    value = copy.deepcopy(value)
    value.update(stage="frozen", discovery_manifest_sha256=proposal_sha256, expected_total_cases=len(ids),
                 native_discovery={"path": os.path.relpath(receipt_path, destination.parent), "sha256": digest(data), "bytes": len(data)})
    value["suites"][0].update(case_ids=ids, mandatory_case_ids=ids, expected_cases=len(ids))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
    return {"path": str(destination), "sha256": digest(destination.read_bytes()), "expected_cases": len(ids)}


def python_payload(suites, marker, execution_root=None):
    require(len(suites) == 1, "original unittest driver requires one script per process")
    row, source = suites[0]
    encoded = {**row, "source_b64": base64.b64encode(source).decode("ascii")}
    return _PAYLOAD.replace("PAYLOAD_JSON", repr(json.dumps(encoded))).replace("MARKER_JSON", repr(marker)).replace("ROOT_JSON", repr(execution_root))


_PAYLOAD = r'''
import base64, hashlib, json, os, pathlib, runpy, shutil, sys, tempfile, traceback, unittest
_row = json.loads(PAYLOAD_JSON)
_marker, _requested_root = MARKER_JSON, ROOT_JSON
_report = {"suites": [], "identity": {}, "exception": None,
           "driver_observation": {"entrypoint": "original __main__", "runner_invocations": 0,
                                  "support_files": [], "resource_files": [], "host_tools": [], "failfast": None},
           "io_observation": {"fixture_files": [], "fixture_bytes_preserved": False}}
_old_argv, _old_path, _old_cwd = sys.argv[:], sys.path[:], os.getcwd()
_old_export_runner, _old_runner = unittest.TextTestRunner, unittest.runner.TextTestRunner
_exit = None
_temporary = None
try:
    import bpy
    def _text(value):
        return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
    _report["identity"] = {"version": list(bpy.app.version), "version_string": bpy.app.version_string,
        "build_hash": _text(bpy.app.build_hash), "build_branch": _text(bpy.app.build_branch), "binary_path": bpy.app.binary_path}
    # Browser --python-expr transports this complete observer as an argument.
    # Preserve its identity without recursively embedding the source and marker.
    _observed_argv = []
    for _argument in sys.argv:
        if _marker in _argument:
            _observed_argv.append({"injected_runner_sha256": hashlib.sha256(_argument.encode()).hexdigest(),
                                   "bytes": len(_argument.encode())})
        else:
            _observed_argv.append(_argument)
    _report["execution_context"] = {"background": bpy.app.background, "runtime_argv": _observed_argv,
        "entrypoint": "original __main__"}
    if _requested_root is None:
        _temporary = tempfile.TemporaryDirectory(prefix="blended-original-unittest-")
        _root = pathlib.Path(_temporary.name)
    else:
        _root = pathlib.Path(_requested_root)
        _root.mkdir(parents=True, exist_ok=True)
    def _write(source, destination):
        data = base64.b64decode(source["source_b64"], validate=True)
        if len(data) != source["bytes"] or hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise RuntimeError("original source or fixture changed in transport")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        if destination.read_bytes() != data:
            raise RuntimeError("original source or fixture changed during materialization")
    _main_path = _root / _row["upstream_path"]
    _write(_row, _main_path)
    for _helper in _row.get("_support_payloads", []):
        _write(_helper, _root / _helper["upstream_path"])
        _report["driver_observation"]["support_files"].append({key: _helper[key] for key in ("upstream_path", "bytes", "sha256")})
    for _resource in _row.get("_resource_payloads", []):
        _write(_resource, _root / _resource["upstream_path"])
        _report["driver_observation"]["resource_files"].append({key: _resource[key] for key in ("upstream_path", "sha256", "bytes")})
    for _tool in _row["driver_execution"].get("host_tools", []):
        _environment = _tool["environment"]
        _tool_path = os.environ.get(_environment) or (shutil.which("idiff") if _environment == "IDIFF_BIN" else sys.executable)
        _observation = {"environment": _environment, "path": _tool_path, "available": False}
        if _tool_path and pathlib.Path(_tool_path).is_file():
            _tool_data = pathlib.Path(_tool_path).read_bytes()
            _observation.update(available=True, bytes=len(_tool_data), sha256=hashlib.sha256(_tool_data).hexdigest())
        _report["driver_observation"]["host_tools"].append(_observation)
    _fixture_root = _root / "tests/files"
    for _fixture in _row.get("_fixture_payloads", []):
        _write(_fixture, _fixture_root / _fixture["relative_path"])
        _report["io_observation"]["fixture_files"].append({key: _fixture[key] for key in ("relative_path", "upstream_path", "bytes", "sha256")})
    _report["io_observation"]["fixture_bytes_preserved"] = True
    def _id(test):
        return unittest.TestCase.id(test) if isinstance(test, unittest.TestCase) else test.id()
    def _ids(suite):
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                yield from _ids(test)
            else:
                yield _id(test)
    class _Result(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.case_outcomes = []
        def _record(self, test, status, detail=None, kind="test", parent_id=None):
            identity = parent_id + " " + test._subDescription() if kind == "subtest" else _id(test)
            self.case_outcomes.append({"id": identity, "kind": kind, "parent_id": parent_id, "status": status, "detail": detail})
        def addSuccess(self, test):
            super().addSuccess(test); self._record(test, "passed")
        def addFailure(self, test, err):
            super().addFailure(test, err); self._record(test, "failed", self._exc_info_to_string(err, test))
        def addError(self, test, err):
            super().addError(test, err); self._record(test, "error", self._exc_info_to_string(err, test))
        def addSkip(self, test, reason):
            super().addSkip(test, reason); self._record(test, "skipped", reason)
        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err); self._record(test, "expected_failure", self._exc_info_to_string(err, test))
        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test); self._record(test, "unexpected_success")
        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            status = "passed" if err is None else ("failed" if issubclass(err[0], test.failureException) else "error")
            self._record(subtest, status,
                         None if err is None else self._exc_info_to_string(err, test), "subtest", _id(test))
    class _Runner(_old_runner):
        def __init__(self, *args, **kwargs):
            if kwargs.get("resultclass") is not None:
                raise RuntimeError("custom unittest results require a separate reviewed adapter")
            kwargs["resultclass"] = _Result
            super().__init__(*args, **kwargs)
        def run(self, test):
            _report["driver_observation"]["runner_invocations"] += 1
            if _report["driver_observation"]["runner_invocations"] != 1:
                raise RuntimeError("multiple unittest invocations require a separate reviewed adapter")
            _report["driver_observation"]["failfast"] = self.failfast
            identities = list(_ids(test))
            result = super().run(test)
            _report["suites"].append({"upstream_path": _row["upstream_path"], "sha256": _row["sha256"],
                "discovered_ids": identities, "discovered": len(identities), "testsRun": result.testsRun,
                "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
                "outcomes": result.case_outcomes})
            return result
    unittest.TextTestRunner = unittest.runner.TextTestRunner = _Runner
    _execution = _row["driver_execution"]
    _script_args = [arg.replace("{fixture_root}", str(_fixture_root)) for arg in _execution["script_args"]]
    sys.path.insert(0, str(_main_path.parent))
    sys.argv = [bpy.app.binary_path, *_execution["blender_args"], "--python", str(_main_path)]
    if _script_args:
        sys.argv += ["--", *_script_args]
    _report["execution_context"]["script_argv"] = sys.argv[:]
    _report["execution_context"]["source_root"] = str(_root)
    os.chdir(_root)
    runpy.run_path(str(_main_path), run_name="__main__")
except SystemExit as error:
    _exit = error
    _report["driver_observation"]["original_exit_code"] = error.code
except BaseException:
    _report["exception"] = traceback.format_exc()
    _exit = SystemExit(1)
finally:
    unittest.TextTestRunner, unittest.runner.TextTestRunner = _old_export_runner, _old_runner
    sys.argv, sys.path = _old_argv, _old_path
    os.chdir(_old_cwd)
    if _temporary is not None:
        _temporary.cleanup()
    print(_marker + json.dumps(_report, sort_keys=True), flush=True)
if _exit is not None:
    raise _exit
'''
