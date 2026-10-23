#!/usr/bin/env python3
"""Compare four final Blender IO outputs through the verified native reader.

Inputs are qualification directories containing their producer JSON receipt and
the original ``blendfiles/`` transfer. Every attempted invocation writes
``exchange.json``; missing prerequisites, provenance blockers, and differences
return nonzero. Each file is opened in a fresh official Blender 5.2.0 process.
This checks final bundles only. It does not cover overwritten method-end file
versions, persistent library linking, browser persistence, or full facet parity.
Python 3.12 and a compatible Linux x64 host are required.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import traceback

try:
    from . import probe_browser_port as shared
    from . import probe_native_reference as native
    from .probe_io_files import validate_inventory
except ImportError:
    import probe_browser_port as shared
    import probe_native_reference as native
    from probe_io_files import validate_inventory


CURRENT_FILES = (
    "blendfile_io.blend", "blendfile_io_partial.blend",
    "blendfileTestIdRuntimeTag.blend", "blendlib_runtimetag_basicTestIdRuntimeTag.blend",
)
NATIVE_EXECUTABLE_SHA256 = "83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27"
MAX_RECEIPT_BYTES = 16 * 1024 * 1024
SOURCE_KEYS = ("upstream_path", "sha256", "bytes")


class InvalidEvidence(ValueError):
    """An observed receipt, input, or result contradicts the fixed contract."""


def fingerprint(path):
    return {"bytes": path.stat().st_size, "sha256": shared.digest(path)}


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvidence("JSON contains duplicate field: " + key)
        result[key] = value
    return result


def check(condition, reason):
    if not condition:
        raise InvalidEvidence(reason)


def source_identity(row):
    value = {key: row.get(key) for key in SOURCE_KEYS}
    if "support_files" in row:
        value.update({key: row.get(key) for key in ("expected_cases", "case_ids", "driver", "required_background")})
        value["support_files"] = [source_identity(source) for source in row["support_files"]]
    return value


def verify_file(root, row):
    """Recheck a confined immutable input before each native open."""
    if root.is_symlink():
        raise InvalidEvidence("blendfiles root is a symlink")
    path = root / row["path"]
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise InvalidEvidence("generated file is not a confined regular file: " + row["path"])
    if not path.is_file():
        raise shared.Blocked("generated file is missing: " + row["path"])
    check(path.stat().st_size == row["bytes"], "generated file byte count changed: " + row["path"])
    check(shared.digest(path) == row["sha256"], "generated file digest changed: " + row["path"])
    return path


def read_producer_receipt(directory, producer):
    """Preserve bounded source evidence before qualification prerequisites run."""
    directory = Path(directory)
    check(producer in ("native", "browser"), "unknown producer")
    if not directory.is_dir():
        raise shared.Blocked(producer + " evidence directory is missing")
    check(not directory.is_symlink(), producer + " evidence directory is a symlink")
    path = directory / ("native_reference.json" if producer == "native" else "qualification.json")
    check(not path.is_symlink(), producer + " receipt is a symlink")
    if not path.is_file():
        raise shared.Blocked(producer + " qualification receipt is missing")
    check(0 < path.stat().st_size <= MAX_RECEIPT_BYTES, "producer receipt exceeds its byte bound")
    receipt = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    check(isinstance(receipt, dict), "producer receipt is not an object")
    return {"directory": str(directory.resolve()), "receipt_path": path.name, "receipt_file": fingerprint(path),
            "receipt": receipt, "file_integrity_verified": False}


def reported_producer_blockers(receipt, producer):
    """Carry source failures even when methods or transfer prerequisites fail."""
    blockers = []
    for blocker in receipt.get("blockers", []):
        check(blocker.get("status") in ("blocked", "failed"), "unknown producer blocker status")
        source_scope = str(blocker.get("scope", "producer"))
        value = {"scope": source_scope if source_scope.startswith(producer + "_") else producer + "_" + source_scope,
                 "status": blocker["status"], "reason": str(blocker.get("reason", "unspecified producer blocker"))}
        if value not in blockers:
            blockers.append(value)
    for error in receipt.get("browser_errors", []):
        blockers.append({"scope": "browser_runtime", "status": "failed", "reason": str(error)})
    if receipt.get("status") not in ("passed", "blocked", "failed"):
        raise InvalidEvidence("unknown producer qualification status")
    source_status_missing = (receipt["status"] == "failed" and not any(row["status"] == "failed" for row in blockers)) or (
        receipt["status"] == "blocked" and not blockers)
    if source_status_missing:
        blockers.append({"scope": producer + "_qualification", "status": receipt["status"],
                         "reason": str(receipt.get("reason", "producer did not qualify"))})
    return blockers


def inspect_producer(directory, producer, catalog):
    """Require the fixed original suite and verified transfer before native reads."""
    return inspect_loaded_producer(read_producer_receipt(directory, producer), producer, catalog)


def inspect_loaded_producer(info, producer, catalog):
    directory, receipt = Path(info["directory"]), info["receipt"]
    check(receipt.get("schema") == 1, "unknown producer receipt schema")
    check(receipt.get("upstream", {}).get("commit") == shared.UPSTREAM_SHA and
          receipt.get("upstream", {}).get("repository") == "blender/blender", "producer upstream source pin changed")
    cohort = receipt.get("cohort", {})
    check(all(cohort.get(key) == catalog[key] for key in ("id", "manifest_sha256", "expected_cases")) and
          cohort.get("complete_cohort_requested") is True, "producer fixed cohort identity changed")
    sources = receipt.get("suite_sources", [])
    check([source_identity(row) for row in sources] == [source_identity(row) for row in catalog["suites"]],
          "producer source or helper identity differs from the fixed manifest")
    check(receipt.get("selected_suites_passed") is True, "all four original cases must pass before exchange")
    execution = receipt.get("execution", {})
    check(execution.get("execution_context", {}).get("background") is True,
          "original blend-file CTest driver requires observed bpy.app.background=True for both producers")
    try:
        shared.validate_suite_execution(execution, catalog["suites"])
    except (RuntimeError, KeyError, TypeError, ValueError) as error:
        raise InvalidEvidence("fixed original case outcomes are invalid: " + str(error)) from error
    observation = execution.get("io_observation", {})
    check(all(observation.get(key) is True for key in (
        "source_bytes_preserved", "helper_import_verified", "module_returned_normally", "driver_completed_as_expected")) and
        observation.get("observer_errors") == [], "original IO source/driver observation is incomplete")
    expected_sources = [source_identity(row) for row in
                        [catalog["suites"][0], *catalog["suites"][0]["support_files"]]]
    expected_sources = [{key: row[key] for key in SOURCE_KEYS} for row in expected_sources]
    observed_sources = [{key: row.get(key) for key in SOURCE_KEYS} for row in observation.get("source_files", [])]
    check(observed_sources == expected_sources, "observed original source/helper bytes changed")
    cases = observation.get("cases", [])
    ids = execution["suites"][0]["discovered_ids"]
    check([row.get("id") for row in cases] == ids, "original method observation lost fixed case IDs")
    phases = [(phase, event) for phase in ("setup", "body", "teardown") for event in ("start", "return")]
    for row in cases:
        check(row.get("status") == "passed" and
              [(event.get("phase"), event.get("event")) for event in row.get("events", [])] == phases and
              not any(event.get("exception") for event in row.get("events", [])), "original method lifecycle did not pass")
    transfer = receipt.get("generated_file_transfer", {})
    generated = execution.get("generated_files", {})
    check(transfer.get("status") == "verified" and transfer.get("semantic_equivalence_verified") is False,
          "generated file transfer is not independently verified")
    expected_origin = "native-filesystem" if producer == "native" else "browser-wasm-filesystem"
    check(transfer.get("origin") == expected_origin, "generated file transfer origin differs from producer")
    check(isinstance(generated.get("root"), str) and bool(generated["root"]), "engine file inventory has no root")
    try:
        files = validate_inventory(transfer, generated["root"])
        engine_files = validate_inventory(generated, generated["root"])
    except ValueError as error:
        raise InvalidEvidence(str(error)) from error
    check(files == engine_files, "transferred inventory differs from the executed engine inventory")
    check(transfer.get("bytes") == sum(row["bytes"] for row in files), "transferred inventory total byte count changed")
    current = {row["path"]: row for row in files if row["path"].endswith(".blend")}
    missing = sorted(set(CURRENT_FILES) - set(current))
    if missing:
        raise shared.Blocked("fixed current file inventory is missing: " + ", ".join(missing))
    check(set(current) == set(CURRENT_FILES), "unexpected current .blend file changes the fixed exchange inventory")
    file_root = directory / "blendfiles"
    if not file_root.is_dir():
        raise shared.Blocked(producer + " blendfiles directory is missing")
    check(not file_root.is_symlink(), "blendfiles root is a symlink")
    check({item.name for item in file_root.iterdir()} == {row["path"] for row in files},
          "local blendfiles differ from the complete transfer inventory")
    for row in files:
        verify_file(file_root, row)
    artifact = receipt.get("artifact", {})
    check(isinstance(artifact.get("observed_sha256"), str) and
          re.fullmatch(r"[0-9a-f]{64}", artifact["observed_sha256"]) and
          artifact.get("expected_sha256") == artifact["observed_sha256"] and
          type(artifact.get("observed_bytes")) is int and artifact["observed_bytes"] > 0 and
          artifact.get("expected_bytes") == artifact["observed_bytes"], "producer artifact identity is incomplete")
    blockers = []
    profile = receipt.get("profile", "")
    if producer == "native":
        check(profile == "native-reference", "native producer profile changed")
        check(artifact["observed_sha256"] == native.ASSET_SHA256 and artifact["observed_bytes"] == native.ASSET_BYTES and
              receipt.get("official_release_checksum_verified") is True, "native producer is not the pinned official artifact")
        shared.validate_build_identity(execution.get("identity", {}))
    else:
        check(isinstance(profile, str) and profile.startswith("chromium-"), "browser producer profile is not Chromium")
        candidate = receipt.get("candidate", {})
        if (candidate.get("kind") == "blender-source-development" or
                receipt.get("source_build_receipt_verified") or receipt.get("source_build")):
            raise shared.Blocked("development browser artifacts require an explicitly supplied and independently validated build receipt; this exchange gate qualifies the pinned release only")
        check(artifact["observed_sha256"] == shared.ASSET_SHA256 and artifact["observed_bytes"] == shared.ASSET_BYTES,
              "browser artifact differs from the independently pinned v0.1.1 release")
        check(candidate.get("repository") == "gessa-ai/blender-web" and candidate.get("tag") == "v0.1.1" and
              candidate.get("source_commit") == shared.PORT_SOURCE_SHA, "browser candidate source identity differs from the pinned release")
        try:
            shared.validate_build_identity(execution.get("identity", {}))
        except shared.Blocked as error:
            blockers.append({"scope": "browser_provenance", "status": "blocked", "reason": str(error)})
    for value in reported_producer_blockers(receipt, producer):
        if value not in blockers:
            blockers.append(value)
    return {**info, "current_files": current,
            "excluded_backups": sorted(row["path"] for row in files if row["path"] not in current),
            "blockers": blockers, "file_integrity_verified": True}


READER_SOURCE = r'''
def _blended_exchange_read(config):
    import base64, hashlib, json
    from pathlib import Path
    import traceback, types
    report = {"schema": 1, "status": "failed", "identity": {}, "exception": None}
    def fingerprint(path):
        data = path.read_bytes()
        return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    try:
        import bpy
        report["identity"] = {"version": list(bpy.app.version), "version_string": bpy.app.version_string,
                              "build_hash": bpy.app.build_hash.decode("utf-8", "replace")}
        path, root = Path(config["file"]), Path(config["root"])
        if path.is_symlink() or root.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise RuntimeError("reader input is not confined")
        before = fingerprint(path)
        if before != {key: config["expected"][key] for key in ("bytes", "sha256")}:
            raise RuntimeError("reader input bytes changed before open")
        data = base64.b64decode(config["helper_b64"], validate=True)
        if len(data) != config["helper"]["bytes"] or hashlib.sha256(data).hexdigest() != config["helper"]["sha256"]:
            raise RuntimeError("upstream helper changed before execution")
        helper_module = types.ModuleType("blended_exchange_original_helper")
        helper_module.__file__ = config["helper"]["upstream_path"]
        exec(compile(data, helper_module.__file__, "exec"), helper_module.__dict__)
        helper = helper_module.TestHelper
        report["input"] = {"path": path.name, **before}
        report["helper"] = config["helper"]
        if bpy.ops.wm.open_mainfile(filepath=str(path.resolve()), load_ui=False) != {"FINISHED"}:
            raise RuntimeError("native open_mainfile did not finish")
        report["snapshot"] = helper.blender_data_to_tuple(bpy.data)
        encoded = json.dumps(report["snapshot"], ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
        report["snapshot_sha256"] = hashlib.sha256(encoded).hexdigest()
        report["id_count"] = len(report["snapshot"])
        report["dependency_edges"] = sum(len(row[1]) for row in report["snapshot"])
        flags = []
        for item in bpy.data.user_map():
            flags.append({"uid": helper.id_to_uid(item), "runtime": bool(item.is_runtime_data),
                          "fake_user": bool(item.use_fake_user), "library_indirect": bool(item.is_library_indirect),
                          "library": helper.id_to_uid(item.library) if item.library else None,
                          "missing": bool(item.is_missing)})
        report["id_flags"] = sorted(flags, key=lambda row: row["uid"])
        libraries = []
        for library in bpy.data.libraries:
            resolved = Path(bpy.path.abspath(library.filepath, library=library.parent)).resolve()
            confined = resolved.is_relative_to(root.resolve())
            libraries.append({"uid": helper.id_to_uid(library), "filepath": library.filepath,
                              "resolved_path": str(resolved), "parent": helper.id_to_uid(library.parent) if library.parent else None,
                              "bundle_relative_path": resolved.relative_to(root.resolve()).as_posix() if confined else None,
                              "is_missing": bool(library.is_missing), "is_archive": bool(library.is_archive),
                              "exists": resolved.is_file(),
                              "file": fingerprint(resolved) if confined and resolved.is_file() else None})
        report["libraries"] = sorted(libraries, key=lambda row: row["uid"])
        if fingerprint(path) != before:
            raise RuntimeError("native reader changed the input file")
        report["status"] = "loaded"
    except BaseException:
        report["exception"] = traceback.format_exc()
    print(config["marker"] + json.dumps(report, sort_keys=True), flush=True)
'''


def reader_payload(file_path, bundle_root, expected_file, helper_source, helper_metadata, marker):
    check(len(helper_source) == helper_metadata["bytes"] and
          hashlib.sha256(helper_source).hexdigest() == helper_metadata["sha256"], "upstream helper bytes changed")
    configuration = {"file": str(file_path.resolve()), "root": str(bundle_root.resolve()),
                     "expected": expected_file, "helper": {key: helper_metadata[key] for key in SOURCE_KEYS},
                     "helper_b64": base64.b64encode(helper_source).decode("ascii"), "marker": marker}
    return READER_SOURCE + "\n_blended_exchange_read(" + repr(configuration) + ")\n"


def validate_reader_result(result, expected, helper, inventory):
    check(result.get("schema") == 1 and result.get("status") == "loaded" and not result.get("exception"),
          "native reader did not complete: " + str(result.get("exception")))
    shared.validate_build_identity(result.get("identity", {}))
    check(result.get("input") == expected, "native reader input identity changed")
    check(result.get("helper") == {key: helper[key] for key in SOURCE_KEYS}, "native reader helper identity changed")
    snapshot = result.get("snapshot")
    check(isinstance(snapshot, list) and bool(snapshot), "native reader emitted no ID snapshot")
    def valid_uid(value):
        return (isinstance(value, list) and len(value) == 3 and isinstance(value[0], str) and
                isinstance(value[1], str) and type(value[2]) is int and value[2] >= 0)
    check(all(isinstance(row, list) and len(row) == 2 and valid_uid(row[0]) and isinstance(row[1], list) and
              all(valid_uid(uid) for uid in row[1]) and row[1] == sorted(row[1]) for row in snapshot),
          "native reader ID/user snapshot is malformed")
    check(snapshot == sorted(snapshot) and result.get("id_count") == len(snapshot) and
          result.get("dependency_edges") == sum(len(row[1]) for row in snapshot), "native reader snapshot counts/order changed")
    check(result.get("snapshot_sha256") == hashlib.sha256(canonical_bytes(snapshot)).hexdigest(),
          "native reader snapshot digest changed")
    flags = result.get("id_flags", [])
    check(sorted(row.get("uid", []) for row in flags) == sorted(row[0] for row in snapshot),
          "native reader supplemental ID inventory is incomplete")
    check(not any(row.get("missing") for row in flags), "native re-open contains missing IDs")
    for library in result.get("libraries", []):
        name = library.get("bundle_relative_path")
        check(name in inventory and library.get("exists") is True and library.get("is_missing") is False and
              library.get("file") == {key: inventory[name][key] for key in ("bytes", "sha256")},
              "native re-open has an unresolved or unmanifested library dependency")


def value_differences(native_value, browser_value, path="snapshot"):
    if native_value == browser_value:
        return []
    if isinstance(native_value, list) and isinstance(browser_value, list):
        result = []
        for index in range(max(len(native_value), len(browser_value))):
            left = native_value[index] if index < len(native_value) else {"missing": True}
            right = browser_value[index] if index < len(browser_value) else {"missing": True}
            result.extend(value_differences(left, right, path + "/" + str(index)))
        return result
    if isinstance(native_value, dict) and isinstance(browser_value, dict):
        result = []
        for key in sorted(set(native_value) | set(browser_value)):
            result.extend(value_differences(native_value.get(key, {"missing": True}),
                                            browser_value.get(key, {"missing": True}), path + "/" + key))
        return result
    return [{"path": path, "native": native_value, "browser": browser_value}]


def compare_loaded(name, native_result, browser_result):
    differences = value_differences(native_result["snapshot"], browser_result["snapshot"])
    differences.extend(value_differences(native_result["id_flags"], browser_result["id_flags"], "id_flags"))
    return {"file": name, "status": "different" if differences else "matched",
            "snapshot_equal": native_result["snapshot"] == browser_result["snapshot"],
            "id_flags_equal": native_result["id_flags"] == browser_result["id_flags"],
            "native_input": native_result["input"], "browser_input": browser_result["input"],
            "native_snapshot_sha256": native_result.get("snapshot_sha256"),
            "browser_snapshot_sha256": browser_result.get("snapshot_sha256"),
            "native_libraries": native_result["libraries"], "browser_libraries": browser_result["libraries"],
            "differences": differences}


def assess_comparisons(comparisons, blockers):
    blockers = list(blockers)
    names = [row.get("file") for row in comparisons]
    valid_inventory = len(names) == len(set(names)) and set(names).issubset(CURRENT_FILES)
    if not valid_inventory:
        blockers.append({"scope": "exchange_inventory", "status": "failed", "reason": "duplicate or unknown fixed file comparison"})
    by_name = {row.get("file"): row for row in comparisons} if valid_inventory else {}
    matched = sum(by_name.get(name, {}).get("status") == "matched" for name in CURRENT_FILES)
    different = sum(by_name.get(name, {}).get("status") in ("different", "failed") for name in CURRENT_FILES)
    pending = [name for name in CURRENT_FILES if by_name.get(name, {}).get("status") not in ("matched", "different", "failed")]
    if different:
        blockers.append({"scope": "file_semantics", "status": "failed", "reason": "one or more final files differ or could not be read"})
    if pending:
        blockers.append({"scope": "exchange_inventory", "status": "blocked", "reason": "fixed final files not compared: " + ", ".join(pending)})
    status = "failed" if any(row["status"] == "failed" for row in blockers) else "blocked" if blockers else "passed"
    return {"status": status, "selected_file_comparisons_passed": matched == len(CURRENT_FILES) and valid_inventory,
            "summary": {"expected_files": len(CURRENT_FILES), "compared": matched + different,
                        "matched": matched, "different_or_failed": different, "missing_or_blocked": len(pending)},
            "blockers": blockers}


def checkpoint(output, report):
    temporary = output / "exchange.json.tmp"
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output / "exchange.json")


def obtain_native(args, work, report):
    archive = args.asset.resolve() if args.asset else work / "native-reference.tar.xz"
    if args.asset is None:
        shared.download(native.ASSET_URL, archive, native.ASSET_BYTES)
    if not archive.is_file():
        raise shared.Blocked("official native reader archive is missing")
    artifact = {"url": native.ASSET_URL, "expected_sha256": native.ASSET_SHA256,
                "expected_bytes": native.ASSET_BYTES, "observed_bytes": archive.stat().st_size}
    report["native_reader_artifact"] = artifact
    if archive.stat().st_size != native.ASSET_BYTES:
        raise shared.Blocked("native reader archive byte count differs from the pinned release")
    artifact["observed_sha256"] = shared.digest(archive)
    if artifact["observed_sha256"] != native.ASSET_SHA256:
        raise shared.Blocked("native reader archive checksum differs from the pinned release")
    unpacked = work / "unpacked"
    unpacked.mkdir()
    report["native_reader_extraction"] = native.extract_reference(archive, unpacked)
    binary = (unpacked / native.ARCHIVE_ROOT / "blender").resolve()
    check(binary.is_relative_to(unpacked.resolve()) and binary.is_file(), "native reader executable is not confined")
    report["native_reader_executable"] = {"path": str(binary.relative_to(unpacked)), **fingerprint(binary)}
    check(report["native_reader_executable"]["sha256"] == NATIVE_EXECUTABLE_SHA256, "native reader executable checksum changed")
    return binary


def run_reader(binary, producer, info, row, helper_data, helper, work, output, timeout):
    root = Path(info["directory"]) / "blendfiles"
    path = verify_file(root, row)
    marker = "BLENDED_EXCHANGE_" + secrets.token_hex(12) + ":"
    program = reader_payload(path, root, row, helper_data, helper, marker)
    runner = work / (producer + "-reader.py")
    runner.write_text(program, encoding="utf-8")
    log = output / ("read-" + producer + "-" + row["path"] + ".log")
    record = {"producer": producer, "file": row["path"], "status": "blocked",
              "runner_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(), "execution": None,
              "process": {"returncode": None, "timeout_seconds": timeout}}
    flags = ["--background", "--factory-startup", "--threads", "1", "--disable-autoexec", "--python-exit-code", "1"]
    record["process"]["flags"] = flags
    try:
        with log.open("wb") as stream:
            process = subprocess.run([str(binary), *flags, "--python", str(runner)], cwd=work,
                                     stdout=stream, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        record["process"]["returncode"] = process.returncode
        check(log.stat().st_size <= 64 * 1024 * 1024, "native reader log exceeded the parsing bound")
        messages = []
        with log.open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                if marker in line:
                    check(line.startswith(marker), "native reader marker is contaminated")
                    messages.append(json.loads(line[len(marker):], object_pairs_hook=unique_object))
        check(len(messages) == 1, "native reader did not emit exactly one complete result")
        record["execution"] = messages[0]
        check(process.returncode == 0, "native reader exited with code " + str(process.returncode))
        validate_reader_result(messages[0], row, helper, {value["path"]: value for value in info["receipt"]["generated_file_transfer"]["files"]})
        verify_file(root, row)
        record["status"] = "loaded"
    except (shared.Blocked, subprocess.TimeoutExpired) as error:
        record["status"], record["reason"] = "blocked", str(error)
    except Exception as error:
        record["status"], record["reason"] = "failed", str(error)
        record["traceback"] = traceback.format_exc()
    finally:
        if log.is_file():
            record["log"] = {"path": log.name, **fingerprint(log)}
    return record


def probe(args, report):
    catalog = shared.load_suite_catalog("blendio52")
    report["cohort"] = {key: value for key, value in catalog.items() if key != "suites"}
    valid = {}
    for producer, directory in (("native", args.native_evidence), ("browser", args.browser_evidence)):
        loaded = {"directory": str(directory), "file_integrity_verified": False}
        try:
            loaded = read_producer_receipt(directory, producer)
            report["inputs"][producer] = loaded
            loaded["blockers"] = reported_producer_blockers(loaded["receipt"], producer)
            report["blockers"].extend(loaded["blockers"])
            info = inspect_loaded_producer(loaded, producer, catalog)
            report["inputs"][producer] = info
            for blocker in info["blockers"]:
                if blocker not in report["blockers"]:
                    report["blockers"].append(blocker)
            valid[producer] = info
        except Exception as error:
            status = "blocked" if isinstance(error, shared.Blocked) else "failed"
            report["inputs"][producer] = {**loaded, "status": status, "reason": str(error)}
            report["blockers"].append({"scope": producer + "_input", "status": status, "reason": str(error)})
    checkpoint(args.output, report)
    if len(valid) != 2:
        return
    with tempfile.TemporaryDirectory(prefix="blended-file-exchange-") as temporary:
        work = Path(temporary)
        helper = catalog["suites"][0]["support_files"][0]
        helper_path = work / "bl_blendfile_utils.py"
        url = "https://raw.githubusercontent.com/blender/blender/" + shared.UPSTREAM_SHA + "/" + helper["upstream_path"]
        shared.download(url, helper_path, helper["bytes"])
        helper_data = helper_path.read_bytes()
        check(len(helper_data) == helper["bytes"] and hashlib.sha256(helper_data).hexdigest() == helper["sha256"],
              "native reader upstream helper bytes changed")
        report["helper"] = {**helper, "url": url}
        binary = obtain_native(args, work, report)
        checkpoint(args.output, report)
        for index, name in enumerate(CURRENT_FILES):
            loaded = {}
            for producer in ("native", "browser"):
                try:
                    record = run_reader(binary, producer, valid[producer], valid[producer]["current_files"][name],
                                        helper_data, helper, work, args.output, args.timeout)
                except Exception as error:
                    record = {"producer": producer, "file": name, "status": "blocked" if isinstance(error, shared.Blocked) else "failed",
                              "reason": str(error), "execution": None}
                report["loads"].append(record)
                if record["status"] == "loaded":
                    loaded[producer] = record["execution"]
                else:
                    report["blockers"].append({"scope": "native_reopen", "producer": producer, "file": name,
                                               "status": record["status"], "reason": record.get("reason", "native read incomplete")})
                checkpoint(args.output, report)
            if len(loaded) == 2:
                report["comparisons"][index] = compare_loaded(name, loaded["native"], loaded["browser"])
            else:
                failed = any(row["status"] == "failed" for row in report["loads"] if row["file"] == name)
                report["comparisons"][index] = {"file": name, "status": "failed" if failed else "blocked",
                                                 "reason": "both producer files did not complete verified native re-open"}
            checkpoint(args.output, report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-evidence", type=Path, required=True, help="Directory containing native_reference.json and blendfiles/")
    parser.add_argument("--browser-evidence", type=Path, required=True, help="Directory containing qualification.json and blendfiles/")
    parser.add_argument("--output", type=Path, required=True, help="Directory for exchange.json and all native reader logs")
    parser.add_argument("--asset", type=Path, help="Exact official Blender 5.2.0 Linux x64 tar.xz; downloaded otherwise")
    parser.add_argument("--timeout", type=int, default=30, help="Per-file native execution bound in seconds, 1 through 600")
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"schema": 1, "status": "running", "started_utc": shared.now(), "finished_utc": None,
              "scope": "four final-bundle files from the fixed Blender 5.2.0 IO cohort reopened in the same verified native reader",
              "final_bundle_only": True, "persistent_link_coverage": False, "overwritten_method_versions_covered": False,
              "browser_persistence_verified": False, "full_parity": False, "full_feature_parity": False,
              "full_facet_parity": False, "product_target_parity": False,
              "upstream": {"repository": "blender/blender", "commit": shared.UPSTREAM_SHA},
              "comparison_policy": "Exact complete unchanged upstream helper tuples and supplemental ID flags; no cross-producer file-byte equality",
              "runner_sha256": shared.digest(Path(__file__)), "inputs": {}, "loads": [], "blockers": [],
              "comparisons": [{"file": name, "status": "blocked", "reason": "not yet compared"} for name in CURRENT_FILES]}
    try:
        if args.timeout <= 0 or args.timeout > 600:
            raise shared.Blocked("timeout must be between 1 and 600 seconds per native read")
        probe(args, report)
    except Exception as error:
        status = "blocked" if isinstance(error, shared.Blocked) else "failed"
        report["blockers"].append({"scope": "infrastructure", "status": status, "reason": str(error)})
        report["traceback"] = traceback.format_exc()
    finally:
        report.update(assess_comparisons(report["comparisons"], report["blockers"]))
        report["finished_utc"] = shared.now()
        checkpoint(args.output, report)
        print(json.dumps({"status": report["status"], "summary": report["summary"], "evidence": str(args.output / "exchange.json")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
