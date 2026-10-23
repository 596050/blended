#!/usr/bin/env python3
"""Independently reconcile preserved LibMV/native evidence; execute no tests."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import tarfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent
BASE = REPO / "compatibility/evidence/product-native-gtest-2026-10-23"
COMMIT = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
SOURCE = WORKSPACE / ("runtime/upstream-product/blender-" + COMMIT)
ARCHIVE = WORKSPACE / "runtime/blender-product-94363991.tar.gz"
RESECT = "intern/libmv/libmv/simple_pipeline/resect_test.cc"
inputs = {}


def check(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def identity(path):
    path = Path(path)
    data = path.read_bytes()
    label = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
    result = {"path": label, "bytes": len(data), "sha256": sha(data)}
    check(label not in inputs or inputs[label] == result, "input changed during review")
    inputs[label] = result
    return result


def resolve(path):
    path = str(path)
    if "/blended/" in path:
        return REPO / path.split("/blended/", 1)[1]
    if "/runtime/" in path:
        return WORKSPACE / "runtime" / path.split("/runtime/", 1)[1]
    return Path(path) if Path(path).is_absolute() else REPO / path


def verify(record):
    current = identity(resolve(record["path"]))
    check(all(current[key] == record[key] for key in ("bytes", "sha256")), "input hash differs: " + record["path"])
    return current


def load(path):
    identity(path)
    def pairs(items):
        value = {}
        for key, item in items:
            check(key not in value, "duplicate JSON key")
            value[key] = item
        return value
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs)


def names(path):
    result = []
    suite = None
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("Running main() from "):
            continue
        value = line.split(" #", 1)[0].strip()
        if line.startswith("  "):
            check(suite is not None and value and not any(char.isspace() for char in value), "unknown runtime case line")
            result.append(suite + "." + value)
        else:
            check(value.endswith(".") and not any(char.isspace() for char in value), "unknown runtime suite line")
            suite = value[:-1]
    return result


def original_xml(path):
    root = ET.parse(path).getroot()
    result = []
    for suite in root.findall("testsuite"):
        for node in suite.findall("testcase"):
            attributes = dict(node.attrib)
            children = {tag: [{"attributes": dict(child.attrib), "text": child.text or ""}
                              for child in node.findall(tag)] for tag in ("failure", "error", "skipped")}
            if children["failure"]:
                outcome = "failed"
            elif children["error"]:
                outcome = "error"
            elif children["skipped"] or attributes.get("result") == "skipped":
                outcome = "skipped"
            elif attributes.get("status") == "run" and attributes.get("result") == "completed":
                outcome = "passed"
            elif attributes.get("status") == "notrun" or attributes.get("result") == "suppressed":
                outcome = "not_run"
            else:
                outcome = "unknown"
            result.append({"identity": attributes.get("classname", suite.get("name", "")) + "." + attributes["name"],
                           "outcome": outcome, "attributes": attributes, "failures": children["failure"],
                           "errors": children["error"], "skipped": children["skipped"]})
    check(len(result) == int(root.get("tests")), "XML observation total differs")
    return root, result


started = datetime.now(timezone.utc).isoformat()
summary = load(BASE / "summary.json")
check(identity(BASE / "summary.json")["sha256"] == "49fa3a4710cd5e192044c0aed8a50ea1460761caeb04909e2be30b987ba6f492",
      "reviewed summary changed")
batch = load(BASE / "libmv-capture-batch.json")
qualified = load(BASE / "source-qualified-observations.json")
prior = load(REPO / "compatibility/evidence/product-native-independent-review-2026-10-23/report.json")
check(identity(REPO / "compatibility/evidence/product-native-independent-review-2026-10-23/report.json")["sha256"] ==
      "7ff1aa55c0f57eba41bd7166e22602c74cf75c6427c51bc1b177f90ac7b1d192", "prior five-suite audit changed")
for key in ("source_archive", "source_configuration_receipt", "build_config", "configured_base_inventory",
            "fixture_candidate_hydration_receipt", "libmv_batch", "source_qualified_observations", "summary_script", "source_identity_adapter"):
    verify(summary[key])
for key in ("capture_script", "batch_script"):
    verify(batch[key])
check(summary["source_commit"] == qualified["source_commit"] == COMMIT, "wrong source pin")
check(identity(ARCHIVE)["sha256"] == "e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7", "wrong archive")
check(batch["all_captures_succeeded"] and len(batch["invocations"]) == 32, "LibMV batch incomplete")
libmv_names = {entry["ctest_name"] for entry in batch["invocations"]}
check(len(libmv_names) == 32 and all(name.startswith("libmv_") for name in libmv_names), "duplicate or non-LibMV batch row")
for entry in batch["invocations"]:
    check(entry["returncode"] == 0, "LibMV capture failed")
    for key in ("native_reference", "build_receipt", "stdout", "stderr"):
        verify(entry[key])
    check(entry["command"][1:] == [batch["capture_script"]["path"], entry["ctest_name"], entry["target"]], "capture argv differs")
registered = {entry["ctest_name"]: entry for entry in summary["invocations"]}
check(len(registered) == len(summary["invocations"]) == 37, "summary invocation duplicated or missing")
check(set(registered) == libmv_names | {"atomic", "guardedalloc", "BLI", "makesdna", "shader_tool"},
      "summary incorporates another driver or excludes a measured driver")
check("script_validate_on_system_python" not in registered, "system-Python driver was added to GTest count")
references = {name: load(resolve(entry["native_reference"]["path"])) for name, entry in registered.items()}
xml_data = {name: original_xml(resolve(reference["gtest_xml"]["path"])) for name, reference in references.items()}
needed = {case["attributes"]["file"] for _, cases in xml_data.values() for case in cases}
needed.update({RESECT, "intern/libmv/CMakeLists.txt", "build_files/cmake/testing.cmake"})
source_bytes = {}
with tarfile.open(ARCHIVE, "r:gz") as archive:
    for path in sorted(needed):
        check(not Path(path).is_absolute() and ".." not in Path(path).parts, "unconfined source path")
        member = archive.getmember("blender-" + COMMIT + "/" + path)
        check(member.isfile(), "source declaration is not regular")
        original = archive.extractfile(member).read()
        check((SOURCE / path).read_bytes() == original, "source differs from pinned archive")
        source_bytes[path] = original

observations = []
invocations = []
all_outcomes = Counter()
libmv_outcomes = Counter()
for name, entry in registered.items():
    reference = references[name]
    directory = resolve(entry["native_reference"]["path"]).parent
    ref_identity = verify(entry["native_reference"])
    check(reference["original_registration"]["identity"] == name, "invocation name differs")
    for key in ("artifact", "build_receipt", "source_configuration_receipt", "gtest_xml", "ctest_junit"):
        verify(reference[key])
    if name in libmv_names:
        for key in ("capture_script", "inventory_adapter", "source_archive", "fixture_candidate_hydration_receipt"):
            verify(reference[key])
        check(reference["capture_script"] == batch["capture_script"], "LibMV capture harness differs")
    build = load(resolve(reference["build_receipt"]["path"]))
    check(build["status"] == "built" and build["returncode"] == 0 and build["artifact"] == reference["artifact"], "build binding differs")
    check(build["cache_before"] == build["cache_after"] == summary["build_config"], "build configuration changed")
    for key in ("log", "generated_target_rules"):
        verify(build[key])
    rules = load(resolve(build["generated_target_rules"]["path"]))
    for rule in rules:
        check(len(rule["content"].encode()) == rule["bytes"] and sha(rule["content"].encode()) == rule["sha256"], "build-rule payload differs")
    rule_text = "\n".join(rule["content"] for rule in rules)
    for stage in reference["stages"]:
        verify(stage["stdout"])
        verify(stage["stderr"])
        check(stage["returncode"] == 0 and not stage["timed_out"], "capture did not complete")
    check(reference["execution"] == reference["stages"][-1], "execution stage mismatch")
    registration = reference["original_registration"]
    original_registration = load(directory / "ctest-registration.stdout.txt")
    check(original_registration["tests"] == [registration["raw_registration"]], "original CTest registration changed")
    check(registration["command"] == registration["raw_registration"]["command"], "registered argv changed")
    props = {prop["name"]: prop["value"] for prop in registration["properties"]}
    check(registration["properties"] == registration["raw_registration"]["properties"], "CTest properties changed")
    check(reference["removed_inherited_gtest_environment_keys"] == [], "unexpected inherited GTest environment")
    check(reference["additional_execution_environment"] == {"GTEST_OUTPUT": "xml:" + reference["gtest_xml"]["path"]}, "unexpected added environment")
    check(reference["original_environment_properties"] == props["ENVIRONMENT"], "original environment differs")
    listed = {}
    for kind in ("registered", "unfiltered"):
        inventory = reference["inventories"][kind]
        verify(inventory["inventory"])
        parsed = load(resolve(inventory["inventory"]["path"]))
        listed[kind] = names(directory / (kind + "-listing.stdout.txt"))
        check(Counter(listed[kind]) == Counter(case["identity"] for case in parsed["cases"]), "runtime listing lost observation")
        check(not parsed["unparsed_lines"] and not parsed["empty_suites"] and parsed["counts"]["disabled"] == 0,
              "unparsed or disabled listing case")
        check(entry[kind + "_discovered"] == len(listed[kind]), "summary discovery total differs")
        check(entry[kind + "_inventory_blockers"] == parsed["blockers"], "summary discarded inventory blockers")
        expected_argv = registration["command"] + ["--gtest_list_tests"] if kind == "registered" else (
            [arg for arg in registration["command"] if not arg.startswith("--gtest_filter=")] + ["--gtest_filter=*", "--gtest_list_tests"])
        check(inventory["capture"]["argv"] == expected_argv and inventory["capture"]["cwd"] == props["WORKING_DIRECTORY"], "listing context changed")
    check((directory / "registered-listing.stdout.txt").read_bytes() == (directory / "unfiltered-listing.stdout.txt").read_bytes(),
          "registered filter omitted compiled cases")
    xml, cases = xml_data[name]
    check(xml.attrib == reference["xml_counters"], "XML counters differ")
    outcome = Counter(case["outcome"] for case in cases)
    check(outcome == Counter(reference["observed_outcome_counts"]), "outcome totals differ")
    check(Counter(case["identity"] for case in cases) == Counter(listed["registered"]), "original XML omitted listed case")
    check(Counter(canonical(case) for case in cases) == Counter(canonical({key: case[key] for key in
          ("identity", "outcome", "attributes", "failures", "errors", "skipped")}) for case in reference["cases"]), "raw outcome differs")
    captured = {(case["identity"], case["attributes"]["file"], int(case["attributes"]["line"])): case for case in reference["cases"]}
    for case in cases:
        path = case["attributes"]["file"]
        line = int(case["attributes"]["line"])
        source = source_bytes[path]
        check(1 <= line <= len(source.splitlines()) and str(SOURCE / path) in rule_text, "declaration not bound to original build source")
        source_id = "gtest-source:" + sha(canonical({"scope": {"source_commit": COMMIT}, "identity": {
            "name": case["identity"], "source_path": path, "source_sha256": sha(source), "source_line": line}}))
        raw_case = captured[(case["identity"], path, line)]
        check(raw_case.get("case_id", source_id) == source_id, "original source case ID differs")
        observations.append({"case_id": source_id, "identity": case["identity"], "outcome": case["outcome"],
                             "ctest_name": name, "native_reference_sha256": ref_identity["sha256"], "source_path": path,
                             "source_line": line, "source_sha256": sha(source), "identity_status": "source_qualified"})
    log = (directory / "ctest-execution.stdout.txt").read_bytes().decode("utf-8", "surrogateescape")
    commands = re.findall(r"^\d+: Test command: (.*)$", log, re.M)
    check(len(commands) == 1 and shlex.split(commands[0]) == registration["command"], "actual original argv differs")
    check(re.findall(r"^\d+: Working Directory: (.*)$", log, re.M) == [props["WORKING_DIRECTORY"]], "actual CWD differs")
    for setting in props["ENVIRONMENT"]:
        check(re.search(r"^\d+:  " + re.escape(setting) + "$", log, re.M), "original environment missing from CTest log")
    check(Counter(re.findall(r"^\d+: \[ RUN +\] (\S+)$", log, re.M)) == Counter(case["identity"] for case in cases), "RUN callbacks differ")
    check(Counter(re.findall(r"^\d+: \[ +OK +\] (\S+) \([0-9]+ ms\)$", log, re.M)) ==
          Counter(case["identity"] for case in cases if case["outcome"] == "passed"), "pass callbacks differ")
    junit = ET.parse(directory / "ctest-results.xml").getroot().findall("testcase")
    check(len(junit) == 1 and junit[0].get("name") == name and junit[0].get("status") == "run" and
          not any(junit[0].find(tag) is not None for tag in ("failure", "error", "skipped")), "CTest driver did not pass")
    for label in ("passed", "skipped", "failed", "error", "not_run", "unknown"):
        check(entry[label] == outcome[label], "derived invocation outcome changed")
    check(entry["executed"] == sum(case["attributes"].get("status") == "run" for case in cases), "derived execution total changed")
    check(entry["xml_observations"] == len(cases) and entry["ctest_returncode"] == reference["execution"]["returncode"] == 0,
          "summary driver status changed")
    check(reference["browser_cases_executed"] == 0 and not reference["browser_parity"], "native pass promoted to browser")
    all_outcomes.update(outcome)
    if name in libmv_names:
        libmv_outcomes.update(outcome)
        invocations.append({"ctest_name": name, "native_reference": ref_identity, "raw_observations": len(cases),
                            "outcomes": dict(outcome), "registered_unfiltered_xml_names_agree": True,
                            "original_ctest_argv_cwd_environment_agree": True, "ctest_returncode": 0})

check(libmv_outcomes == Counter(passed=145), "LibMV count differs")
check(all_outcomes == Counter(passed=2015, skipped=1) and len(observations) == 2016, "combined counts differ")
check(Counter(canonical(case) for case in observations) == Counter(canonical(case) for case in qualified["observations"]),
      "derived source-qualified observations differ from raw XML")
check(len({case["case_id"] for case in observations}) == 2016 and not summary["repeated_source_qualified_cases"], "source identity duplicated")
expected_counts = {"ctest_invocations": 37, "ctest_invocations_exit_zero": 37, "empty_runtime_registrations": 1,
                   "nonempty_runtime_registrations": 36, "registered_discovered": 2016, "unfiltered_discovered": 2016,
                   "registered_disabled": 0, "unfiltered_disabled": 0, "xml_observations": 2016, "executed": 2016,
                   "unique_source_qualified_cases": 2016, "passed": 2015, "skipped": 1, "failed": 0,
                   "error": 0, "not_run": 0, "unknown": 0}
check(summary["counts"] == expected_counts, "final summary totals differ")
for path, entry in qualified["verified_original_declaration_files"].items():
    data = source_bytes[path]
    check(entry == {"path": path, "bytes": len(data), "sha256": sha(data), "line_count": len(data.splitlines()),
                    "verified_against_archive": True}, "derived source file binding differs")
lines = source_bytes[RESECT].decode().splitlines()
check(lines[24] == "#if 0" and lines[233] == "#endif", "upstream resect block differs")
directives = [(number, line) for number, line in enumerate(lines, 1) if re.match(r"\s*#\s*(if|else|elif|endif)\b", line)]
check(directives == [(25, "#if 0"), (156, "#  if 0"), (166, "#  endif"), (234, "#endif")],
      "resect preprocessor nesting differs")
disabled_tests = [{"line": number, "declaration": line} for number, line in enumerate(lines, 1) if line.startswith("TEST(")]
check(len(disabled_tests) == 3 and all(25 < case["line"] < 234 for case in disabled_tests), "resect source test outside disabled block")
empty = summary["empty_runtime_registration"]
check(empty["ctest_name"] == "libmv_resect" and empty["native_case_passes"] == 0 and
      empty["classification"] == "empty_runtime_listing" and empty["blocker_retained"] and not empty["parity_qualified"],
      "empty runtime invocation incorrectly qualifies a pass")
check(registered["libmv_resect"]["classification"] == "empty_runtime_listing" and
      "empty_runtime_listing" in registered["libmv_resect"]["registered_inventory_blockers"], "empty discovery blocker discarded")
check([entry["ctest_name"] for entry in invocations if entry["raw_observations"] == 0] == ["libmv_resect"], "another empty invocation hidden")
collisions = defaultdict(set)
for case in observations:
    collisions[case["identity"]].add((case["source_path"], case["source_line"]))
duplicate_names = {name: [{"path": path, "line": line} for path, line in sorted(locations)]
                   for name, locations in collisions.items() if len(locations) > 1}
check(duplicate_names == summary["duplicate_names_with_distinct_sources"], "summary raw-name collisions differ")
klt = [case for case in observations if case["identity"] == "KltRegionTracker.Track"]
check({(case["source_path"], case["source_line"]) for case in klt} == {
    ("intern/libmv/libmv/tracking/brute_region_tracker_test.cc", 29),
    ("intern/libmv/libmv/tracking/klt_region_tracker_test.cc", 28)}, "KltRegionTracker source locations differ")
check(len(klt) == len({case["case_id"] for case in klt}) == 2, "KltRegionTracker source cases merged")
for case in klt:
    check(source_bytes[case["source_path"]].decode().splitlines()[case["source_line"] - 1] == "TEST(KltRegionTracker, Track) {",
          "KltRegionTracker original declaration differs")
check(summary["browser_cases_executed"] == batch["browser_cases_executed"] == qualified["browser_cases_executed"] == 0 and
      not summary["browser_parity"] and not summary["runtime_enumeration_complete"] and not summary["all_upstream_tests_enumerated"],
      "summary overclaims browser or product coverage")

report = {"schema": 1, "status": "verified", "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
          "source_commit": COMMIT, "audit_script": identity(Path(__file__)), "reviewed_summary": identity(BASE / "summary.json"),
          "libmv_invocation_count": len(invocations), "libmv_raw_outcomes": dict(libmv_outcomes), "libmv_invocations": invocations,
          "combined_counts_recomputed": expected_counts, "system_python_driver_included": False,
          "distinct_klt_region_tracker_sources": klt,
          "empty_resect": {"original_source": qualified["verified_original_declaration_files"][RESECT],
                            "disabled_block": {"start_line": 25, "end_line": 234, "directive": "#if 0"},
                            "nested_disabled_block": {"start_line": 156, "end_line": 166, "directive": "#  if 0"},
                            "original_disabled_declarations": disabled_tests, "runtime_observations": 0,
                            "native_case_passes": 0, "ctest_process_returncode": 0, "parity_qualified": False},
          "duplicate_names_with_distinct_sources": duplicate_names,
          "all_raw_observations_match_derived_source_record": True, "source_qualified_ids_unique": True,
          "verified_original_source_files": [{"path": path, "bytes": len(data), "sha256": sha(data)}
                                              for path, data in sorted(source_bytes.items())],
          "checked_input_files": sorted(inputs.values(), key=lambda entry: entry["path"]),
          "new_tests_executed_by_review": 0, "browser_cases_executed": 0, "browser_passes_inferred": 0,
          "full_feature_parity": False, "all_upstream_tests_enumerated": False,
          "limitations": ["One selected Linux Release configuration; no completeness claim for Blender's full test denominator.",
                          "The resect source-disabled declarations are preserved as source obligations, not runtime passes or skips.",
                          "System-Python remains a separate CTest driver and contributes no GoogleTest case count.",
                          "Review re-reads preserved evidence only; no compiler, original executable, CTest, or production test ran."]}
output = HERE / "report.json"
check(not output.exists(), "retain immutable prior review")
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": "verified", "libmv_outcomes": dict(libmv_outcomes), "combined_outcomes": dict(all_outcomes),
                  "report": {"path": str(output), "bytes": output.stat().st_size, "sha256": sha(output.read_bytes())}}, indent=2))
