"""List native GTests and execute their unchanged original CTest invocation."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
sys.path.insert(0, str(repo))
from tools.test_registration_inventory import gtest_source_case_id, inventory_ctest, inventory_gtest

if len(sys.argv) not in (3, 4):
    raise SystemExit("usage: capture-native-gtest.py CTEST_NAME TARGET_NAME [ATTEMPT_NAME]")
name, target = sys.argv[1:3]
attempt_name = sys.argv[3] if len(sys.argv) == 4 else name
if not all(re.fullmatch(r"[A-Za-z0-9_-]+", value) for value in (name, target, attempt_name)):
    raise ValueError("simple configured target names required")
capture_base = repo / "compatibility/evidence/product-native-gtest-2026-10-23"
capture_root = capture_base / attempt_name
if capture_root.exists():
    raise RuntimeError("native execution output already exists; retain immutable attempts")
capture_root.mkdir()
configuration_path = evidence / "configure-with-optix.json"
configuration = json.loads(configuration_path.read_text())
build_receipt_path = capture_base / (target + "-build.json")
build_receipt = json.loads(build_receipt_path.read_text())
if build_receipt.get("status") != "built" or build_receipt.get("returncode") != 0:
    raise RuntimeError("target has not built successfully")
build = Path(configuration["command"][configuration["command"].index("-B") + 1])
ctest = workspace / "runtime/browser-python/bin/ctest"
now = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


environment = dict(os.environ)
removed_environment_keys = sorted(key for key in environment if key.startswith("GTEST_"))
for key in removed_environment_keys:
    environment.pop(key)
environment.update(configuration["environment_overrides"])
stages = []


def run(stage_name, command, *, cwd, env, timeout=600):
    stdout_path = capture_root / (stage_name + ".stdout.txt")
    stderr_path = capture_root / (stage_name + ".stderr.txt")
    record = {"name": stage_name, "argv": command, "cwd": str(cwd), "started_utc": now(),
              "timeout_seconds": timeout, "timed_out": False}
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            record["returncode"] = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            record.update(returncode=process.returncode, timed_out=True)
    record.update(finished_utc=now(), stdout=identity(stdout_path), stderr=identity(stderr_path))
    stages.append(record)
    return record


filter_args = ["--test-dir", str(build), "--build-config", "Release", "--tests-regex", "^" + re.escape(name) + "$"]
ctest_capture = run("ctest-registration", [str(ctest), *filter_args, "--show-only=json-v1"], cwd=repo, env=environment)
if ctest_capture["returncode"] != 0:
    raise RuntimeError("configured CTest listing failed")
build_config_sha256 = identity(build / "CMakeCache.txt")["sha256"]
registrations = inventory_ctest((capture_root / "ctest-registration.stdout.txt").read_text(),
                                source_commit=configuration["source_commit"], build_config_sha256=build_config_sha256,
                                configuration="Release", provenance=ctest_capture)
if len(registrations["registrations"]) != 1:
    raise RuntimeError("exact original registration was not found")
registration = registrations["registrations"][0]
original_command = registration["command"]
if not original_command or Path(original_command[0]).name != target:
    raise RuntimeError("CTest did not resolve the expected original executable")
artifact = identity(Path(original_command[0]))
if artifact != build_receipt["artifact"]:
    raise RuntimeError("built test binary changed")
properties = {item["name"]: item["value"] for item in registration["properties"]}
runtime_environment = dict(environment)
original_environment = properties.get("ENVIRONMENT", [])
for value in original_environment:
    if "=" in value:
        key, setting = value.split("=", 1)
        runtime_environment[key] = setting
working_directory = Path(properties.get("WORKING_DIRECTORY", str(build)))

# Preserve the original registered filter for its concrete expansion. Separately
# enumerate the whole binary to expose cases that the original source scanner omitted.
registered_listing = run("registered-listing", [*original_command, "--gtest_list_tests"],
                         cwd=working_directory, env=runtime_environment)
unfiltered_command = [value for value in original_command if not value.startswith("--gtest_filter=")]
unfiltered_listing = run("unfiltered-listing", [*unfiltered_command, "--gtest_filter=*", "--gtest_list_tests"],
                         cwd=working_directory, env=runtime_environment)
inventories = {}
listing_objects = {}
for label, capture in (("registered", registered_listing), ("unfiltered", unfiltered_listing)):
    listing_path = capture_root / (label + "-listing.stdout.txt")
    listing = inventory_gtest(listing_path.read_text(), source_commit=configuration["source_commit"],
                              build_config_sha256=build_config_sha256, artifact_sha256=artifact["sha256"],
                              registration_id=registration["id"], provenance=capture)
    path = capture_root / (label + "-gtest-inventory.json")
    path.write_text(json.dumps(listing, indent=2) + "\n")
    inventories[label] = {"capture": capture, "inventory": identity(path), "counts": listing["counts"]}
    listing_objects[label] = listing

source_archive = workspace / "runtime/blender-product-94363991.tar.gz"
source_archive_identity = identity(source_archive)
if source_archive_identity["sha256"] != "e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7":
    raise RuntimeError("original source archive identity changed")
source_root = Path(configuration["command"][configuration["command"].index("-S") + 1])

# GTEST_OUTPUT is the upstream framework's report option. CTest supplies the exact
# unchanged registered argv, working directory, environment properties and process exit.
gtest_xml = capture_root / "gtest-results.xml"
ctest_junit = capture_root / "ctest-results.xml"
execution_environment = dict(environment)
execution_environment["GTEST_OUTPUT"] = "xml:" + str(gtest_xml)
execution_command = [str(ctest), *filter_args, "--verbose", "--no-tests=error", "--timeout", "600",
                     "--output-junit", str(ctest_junit)]
execution = run("ctest-execution", execution_command, cwd=repo, env=execution_environment, timeout=630)
cases = []
xml_counters = None
if gtest_xml.is_file():
    xml = ET.parse(gtest_xml).getroot()
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
source_files = {}
identity_blockers = []
with tarfile.open(source_archive, "r:gz") as archive:
    for case in cases:
        attributes = case["attributes"]
        source_path = attributes.get("file", "")
        try:
            source_line = int(attributes.get("line", "0"))
            if source_path not in source_files:
                # Validate path syntax before accessing a source file.
                gtest_source_case_id(case["identity"], source_commit=configuration["source_commit"],
                                    source_path=source_path, source_sha256="0" * 64, source_line=source_line)
                member = archive.getmember("blender-" + configuration["source_commit"] + "/" + source_path)
                original = archive.extractfile(member).read()
                current_path = source_root / source_path
                if current_path.read_bytes() != original:
                    raise ValueError("source file differs from pinned archive")
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
        except (KeyError, ValueError, OSError, AttributeError) as error:
            case.update(case_id=None, identity_status="unresolved_source_location", identity_error=str(error))
            identity_blockers.append({"name": case["identity"], "reason": str(error)})
source_id_counts = Counter(case["case_id"] for case in cases if case["case_id"] is not None)
for case in cases:
    if case["case_id"] is not None and source_id_counts[case["case_id"]] > 1:
        case.update(candidate_source_case_id=case["case_id"], case_id=None, identity_status="ambiguous_source_location")
        identity_blockers.append({"name": case["identity"], "reason": "duplicate source-qualified runtime identity"})
listed_name_counts = Counter(case["identity"] for case in listing_objects["registered"]["cases"])
executed_report_name_counts = Counter(case["identity"] for case in cases)
name_multiplicities_match = listed_name_counts == executed_report_name_counts
if not name_multiplicities_match:
    identity_blockers.append({"reason": "registered listing and original XML name multiplicities differ",
                              "missing": dict(listed_name_counts - executed_report_name_counts),
                              "unexpected": dict(executed_report_name_counts - listed_name_counts)})
record = {
    "schema": 1, "source_commit": configuration["source_commit"], "source_configuration_receipt": identity(configuration_path),
    "build_receipt": identity(build_receipt_path), "build_config_sha256": build_config_sha256,
    "artifact": artifact, "original_registration": registration, "inventories": inventories,
    "environment_overrides": configuration["environment_overrides"], "removed_inherited_gtest_environment_keys": removed_environment_keys,
    "original_environment_properties": original_environment,
    "additional_execution_environment": {"GTEST_OUTPUT": execution_environment["GTEST_OUTPUT"]},
    "execution": execution, "stages": stages, "xml_counters": xml_counters, "cases": cases,
    "capture_script": identity(Path(__file__)), "inventory_adapter": identity(repo / "tools/test_registration_inventory.py"),
    "source_archive": source_archive_identity, "verified_original_declaration_files": source_files,
    "name_multiplicities_match": name_multiplicities_match, "source_identity_blockers": identity_blockers,
    "all_observed_source_identities_resolved": not identity_blockers,
    "observed_outcome_counts": dict(Counter(case["outcome"] for case in cases)),
    "gtest_xml": identity(gtest_xml) if gtest_xml.is_file() else None,
    "ctest_junit": identity(ctest_junit) if ctest_junit.is_file() else None,
    "browser_cases_executed": 0, "browser_parity": False,
    "all_upstream_tests_enumerated": False, "runtime_enumeration_complete": False,
}
fixture_receipt = repo / "compatibility/evidence/product-fixture-hydration-2026-10-23/report.json"
if fixture_receipt.is_file():
    record["fixture_candidate_hydration_receipt"] = identity(fixture_receipt)
(capture_root / "native-reference.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"ctest_name": name, "returncode": execution["returncode"],
                  "observed_outcome_counts": record["observed_outcome_counts"],
                  "xml_counters": xml_counters, "browser_parity": False}))
raise SystemExit(0 if execution["returncode"] == 0 else 1)
