"""Execute the unchanged original binary beyond its narrower CTest filter."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent
sys.path.insert(0, str(REPO))
from tools.test_registration_inventory import gtest_source_case_id

OUTPUT = HERE / "cycles-unfiltered-supplementary"
OUTPUT.mkdir()
NOW = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


registered_path = HERE / "cycles-runtime-libraries/native-reference.json"
registered = json.loads(registered_path.read_text())
configuration_path = Path(registered["source_configuration_receipt"]["path"])
assert identity(configuration_path) == registered["source_configuration_receipt"]
configuration = json.loads(configuration_path.read_text())
assert identity(Path(registered["artifact"]["path"])) == registered["artifact"]
staging_path = HERE / "runtime-library-staging/report.json"
staging = json.loads(staging_path.read_text())
assert staging["status"] == "verified_staged"
manifest_path = Path(staging["verified_destination"]["path"])
assert identity(manifest_path) == staging["verified_destination"]
for entry in json.loads(manifest_path.read_text()):
    path = Path(staging["destination"]) / entry["destination_name"]
    if entry["kind"] == "symlink":
        assert path.is_symlink() and os.readlink(path) == entry["target"]
    else:
        actual = identity(path)
        assert actual["bytes"] == entry["bytes"] and actual["sha256"] == entry["sha256"]

original_command = registered["original_registration"]["command"]
assert sum(value.startswith("--gtest_filter=") for value in original_command) == 1
command = ["--gtest_filter=*" if value.startswith("--gtest_filter=") else value for value in original_command]
properties = {item["name"]: item["value"] for item in registered["original_registration"]["properties"]}
environment = dict(os.environ)
removed_environment = sorted(key for key in environment if key.startswith("GTEST_"))
for key in removed_environment:
    environment.pop(key)
environment.update(registered["environment_overrides"])
for value in registered["original_environment_properties"]:
    if "=" in value:
        key, setting = value.split("=", 1)
        environment[key] = setting
xml_path = OUTPUT / "gtest-results.xml"
environment["GTEST_OUTPUT"] = "xml:" + str(xml_path)
cwd = properties["WORKING_DIRECTORY"]
execution = {"argv": command, "cwd": cwd, "started_utc": NOW(), "timeout_seconds": 600,
             "timed_out": False, "original_ctest_invocation": False}
started = time.monotonic()
with (OUTPUT / "execution.stdout.txt").open("wb") as stdout, (OUTPUT / "execution.stderr.txt").open("wb") as stderr:
    process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
    try:
        execution["returncode"] = process.wait(timeout=600)
    except subprocess.TimeoutExpired:
        execution["timed_out"] = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        execution["returncode"] = process.returncode
execution.update(finished_utc=NOW(), elapsed_seconds=time.monotonic() - started,
                 stdout=identity(OUTPUT / "execution.stdout.txt"), stderr=identity(OUTPUT / "execution.stderr.txt"))

cases = []
xml_counters = None
if xml_path.is_file():
    xml = ET.parse(xml_path).getroot()
    xml_counters = dict(xml.attrib)
    for suite in xml.findall("testsuite"):
        for node in suite.findall("testcase"):
            attributes = dict(node.attrib)
            failures = [{"attributes": dict(child.attrib), "text": child.text or ""} for child in node.findall("failure")]
            errors = [{"attributes": dict(child.attrib), "text": child.text or ""} for child in node.findall("error")]
            skipped = [{"attributes": dict(child.attrib), "text": child.text or ""} for child in node.findall("skipped")]
            if failures:
                outcome = "failed"
            elif errors:
                outcome = "error"
            elif skipped:
                outcome = "skipped"
            elif attributes.get("status") == "notrun" or attributes.get("result") == "suppressed":
                outcome = "not_run"
            elif attributes.get("status") == "run" and attributes.get("result") == "completed":
                outcome = "passed"
            else:
                outcome = "unknown"
            cases.append({"identity": attributes.get("classname", suite.get("name", "")) + "." + attributes["name"],
                          "outcome": outcome, "attributes": attributes, "failures": failures,
                          "errors": errors, "skipped": skipped})

source_archive = Path(registered["source_archive"]["path"])
assert identity(source_archive) == registered["source_archive"]
source_root = Path(configuration["command"][configuration["command"].index("-S") + 1])
source_files = {}
identity_blockers = []
with tarfile.open(source_archive, "r:gz") as archive:
    for case in cases:
        attributes = case["attributes"]
        source_path = attributes.get("file", "")
        try:
            source_line = int(attributes.get("line", "0"))
            if source_path not in source_files:
                gtest_source_case_id(case["identity"], source_commit=configuration["source_commit"],
                                    source_path=source_path, source_sha256="0" * 64, source_line=source_line)
                original = archive.extractfile("blender-" + configuration["source_commit"] + "/" + source_path).read()
                assert (source_root / source_path).read_bytes() == original
                source_files[source_path] = {"path": source_path, "bytes": len(original),
                                             "sha256": hashlib.sha256(original).hexdigest(),
                                             "line_count": len(original.splitlines()), "verified_against_archive": True}
            source = source_files[source_path]
            if not 1 <= source_line <= source["line_count"]:
                raise ValueError("runtime source location is outside original file")
            case["case_id"] = gtest_source_case_id(case["identity"], source_commit=configuration["source_commit"],
                                                   source_path=source_path, source_sha256=source["sha256"],
                                                   source_line=source_line)
            case["identity_status"] = "source_qualified"
            case["source_location"] = {"path": source_path, "line": source_line, "sha256": source["sha256"]}
        except (KeyError, ValueError, OSError, AttributeError, AssertionError) as error:
            case.update(case_id=None, identity_status="unresolved_source_location", identity_error=str(error))
            identity_blockers.append({"name": case["identity"], "reason": str(error)})
source_id_counts = Counter(case["case_id"] for case in cases if case["case_id"] is not None)
for case in cases:
    if case["case_id"] is not None and source_id_counts[case["case_id"]] > 1:
        case.update(candidate_source_case_id=case["case_id"], case_id=None, identity_status="ambiguous_source_location")
        identity_blockers.append({"name": case["identity"], "reason": "duplicate source-qualified runtime identity"})
listing_path = Path(registered["inventories"]["unfiltered"]["inventory"]["path"])
assert identity(listing_path) == registered["inventories"]["unfiltered"]["inventory"]
listing = json.loads(listing_path.read_text())
listed = Counter(case["identity"] for case in listing["cases"])
observed = Counter(case["identity"] for case in cases)
if listed != observed:
    identity_blockers.append({"reason": "unfiltered listing and original XML name multiplicities differ",
                              "missing": dict(listed - observed), "unexpected": dict(observed - listed)})
original_ids = {case["case_id"] for case in registered["cases"]}
for case in cases:
    case["also_observed_in_original_ctest_invocation"] = case["case_id"] in original_ids if case["case_id"] else None
record = {
    "schema": 1,
    "scope": "Supplementary whole-binary execution with the framework filter broadened to '*'; not the original CTest invocation.",
    "original_ctest_invocation": False,
    "original_test_source_main_and_assertions_unchanged": True,
    "source_commit": configuration["source_commit"],
    "source_configuration_receipt": identity(configuration_path),
    "build_config_sha256": registered["build_config_sha256"],
    "registered_execution_receipt": identity(registered_path),
    "runtime_library_staging_receipt": identity(staging_path),
    "runtime_library_manifest_reverified_before_execution": identity(manifest_path),
    "original_ctest_command": original_command,
    "argument_change": {"old": next(value for value in original_command if value.startswith("--gtest_filter=")), "new": "--gtest_filter=*"},
    "artifact": registered["artifact"],
    "execution": execution,
    "original_environment_properties": registered["original_environment_properties"],
    "environment_overrides": registered["environment_overrides"],
    "additional_execution_environment": {"GTEST_OUTPUT": environment["GTEST_OUTPUT"]},
    "inherited_control_environment": {key: os.environ[key] for key in ("PATH", "TZ", "LANG", "LC_ALL", "LC_CTYPE", "PYTHONOPTIMIZE") if key in os.environ},
    "removed_inherited_gtest_environment_keys": removed_environment,
    "xml_counters": xml_counters,
    "gtest_xml": identity(xml_path) if xml_path.is_file() else None,
    "unfiltered_listing": identity(listing_path),
    "name_multiplicities_match": listed == observed,
    "cases": cases,
    "observed_outcome_counts": dict(Counter(case["outcome"] for case in cases)),
    "additional_source_qualified_case_count": sum(case.get("also_observed_in_original_ctest_invocation") is False for case in cases),
    "source_archive": registered["source_archive"],
    "verified_original_declaration_files": source_files,
    "source_identity_blockers": identity_blockers,
    "all_observed_source_identities_resolved": not identity_blockers,
    "capture_script": identity(Path(__file__)),
    "inventory_adapter": identity(REPO / "tools/test_registration_inventory.py"),
    "browser_cases_executed": 0,
    "browser_parity": False,
    "all_upstream_tests_enumerated": False,
    "runtime_enumeration_complete": False,
}
assert identity(Path(registered["artifact"]["path"])) == registered["artifact"]
(OUTPUT / "native-reference.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"returncode": execution["returncode"], "observed_outcome_counts": record["observed_outcome_counts"],
                  "additional_cases": record["additional_source_qualified_case_count"], "source_identity_blockers": identity_blockers}))
raise SystemExit(0 if execution["returncode"] == 0 else 1)
