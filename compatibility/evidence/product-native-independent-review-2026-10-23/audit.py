#!/usr/bin/env python3
"""Read-only independent reconciliation of five preserved native GTest captures.

Uses only Python's standard library, not the production inventory adapter.
Writes only its own report. Does not rerun, modify, or add passes to any test.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import sys
import tarfile
import xml.etree.ElementTree as ET


OUTPUT = Path(__file__).resolve().parent
REPO = OUTPUT.parents[2]
WORKSPACE = REPO.parent
CAPTURES = REPO / "compatibility/evidence/product-native-gtest-2026-10-23"
COMMIT = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
ARCHIVE = WORKSPACE / "runtime/blender-product-94363991.tar.gz"
ARCHIVE_SHA = "e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7"
SOURCE = WORKSPACE / ("runtime/upstream-product/blender-" + COMMIT)
SUITES = ["BLI-source-identities", "atomic", "guardedalloc", "makesdna", "shader_tool"]
EXPECTED = {
    "BLI-source-identities": {"passed": 1742}, "atomic": {"passed": 56},
    "guardedalloc": {"passed": 6}, "makesdna": {"passed": 5},
    "shader_tool": {"passed": 61, "skipped": 1},
}
checked_files = {}
checks = 0


def require(condition, message):
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def resolve(value):
    path = Path(value)
    if not path.is_absolute():
        return REPO / path
    # Preserve historical argv while allowing evidence paths to move with a clone.
    text = str(path)
    for token, base in (("/blended/", REPO), ("/runtime/", WORKSPACE / "runtime")):
        if token in text:
            return base / text.split(token, 1)[1]
    return path


def file_identity(path):
    path = Path(path)
    data = path.read_bytes()
    try:
        label = str(path.relative_to(REPO))
    except ValueError:
        label = str(path)
    record = {"path": label, "bytes": len(data), "sha256": digest(data)}
    old = checked_files.get(label)
    require(old is None or old == record, "input changed during audit: " + label)
    checked_files[label] = record
    return record


def verify(record):
    current = file_identity(resolve(record["path"]))
    require(current["bytes"] == record["bytes"] and current["sha256"] == record["sha256"],
            "file binding differs: " + record["path"])
    return current


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    file_identity(path)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs)


def listing_names(path):
    suite = None
    names = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("Running main() from "):
            continue
        if line.startswith("  "):
            require(suite is not None, "listing case without suite")
            token = line[2:].split(" #", 1)[0].strip()
            require(bool(token) and not any(char.isspace() for char in token), "malformed case line")
            names.append(suite + "." + token)
        else:
            token = line.split(" #", 1)[0].strip()
            require(token.endswith(".") and not any(char.isspace() for char in token), "malformed suite line")
            suite = token[:-1]
    return names


def xml_cases(path):
    root = ET.parse(path).getroot()
    cases = []
    for suite in root.findall("testsuite"):
        for node in suite.findall("testcase"):
            attributes = dict(node.attrib)
            detail = {tag: [{"attributes": dict(item.attrib), "text": item.text or ""}
                            for item in node.findall(tag)] for tag in ("failure", "error", "skipped")}
            if detail["failure"]:
                status = "failed"
            elif detail["error"]:
                status = "error"
            elif detail["skipped"] or attributes.get("result") == "skipped":
                status = "skipped"
            elif attributes.get("status") == "run" and attributes.get("result") == "completed":
                status = "passed"
            elif attributes.get("status") == "notrun" or attributes.get("result") == "suppressed":
                status = "not_run"
            else:
                status = "unknown"
            cases.append({"identity": attributes.get("classname", suite.get("name", "")) + "." + attributes["name"],
                          "outcome": status, "attributes": attributes, "failures": detail["failure"],
                          "errors": detail["error"], "skipped": detail["skipped"]})
    require(int(root.get("tests")) == len(cases), "XML total differs from actual testcase elements")
    return root, cases


def source_case_id(case, source_bytes):
    attributes = case["attributes"]
    identity = {"name": case["identity"], "source_path": attributes["file"],
                "source_sha256": digest(source_bytes), "source_line": int(attributes["line"])}
    return "gtest-source:" + digest(canonical({"scope": {"source_commit": COMMIT}, "identity": identity}))


started = datetime.now(timezone.utc).isoformat()
archive_identity = file_identity(ARCHIVE)
require(archive_identity["sha256"] == ARCHIVE_SHA and archive_identity["bytes"] == 80900636,
        "pinned source archive differs")
records = {suite: read_json(CAPTURES / suite / "native-reference.json") for suite in SUITES}
require(file_identity(CAPTURES / "BLI-source-identities/native-reference.json")["sha256"] ==
        "251cf1a315b0014d29eaca2cd5078a4adec375b637957bf9d7b4ef2944663dfe", "BLI receipt changed")
raw = {suite: xml_cases(CAPTURES / suite / "gtest-results.xml") for suite in SUITES}
needed_sources = {case["attributes"]["file"] for _, cases in raw.values() for case in cases}
for record in records.values():
    for entry in record["original_registration"]["backtrace"]:
        if "file" in entry:
            needed_sources.add(str(resolve(entry["file"]).relative_to(SOURCE)))
originals = {}
with tarfile.open(ARCHIVE, "r:gz") as archive:
    for relative in sorted(needed_sources):
        safe = PurePosixPath(relative)
        require(not safe.is_absolute() and ".." not in safe.parts and str(safe) == relative,
                "non-confined original source path")
        member = archive.getmember("blender-" + COMMIT + "/" + relative)
        require(member.isfile(), "original declaration is not regular source")
        data = archive.extractfile(member).read()
        require((SOURCE / relative).read_bytes() == data, "current source differs from archive: " + relative)
        originals[relative] = data

summaries = []
for suite, record in records.items():
    directory = CAPTURES / suite
    require(record["source_commit"] == COMMIT, suite + " wrong source pin")
    for key in ("source_configuration_receipt", "build_receipt", "artifact", "gtest_xml", "ctest_junit",
                "capture_script", "inventory_adapter", "source_archive", "fixture_candidate_hydration_receipt"):
        if key in record:
            verify(record[key])
    configuration = read_json(resolve(record["source_configuration_receipt"]["path"]))
    build = read_json(resolve(record["build_receipt"]["path"]))
    require(configuration["configured"] and configuration["returncode"] == 0, "configuration incomplete")
    require(build["status"] == "built" and build["returncode"] == 0, "build incomplete")
    require(build["artifact"] == record["artifact"], "execution artifact differs from build")
    require(build["source_commit"] == configuration["source_commit"] == COMMIT, "build source mismatch")
    require(build["source_configuration_receipt"] == record["source_configuration_receipt"], "configuration binding mismatch")
    for key in ("cache_before", "cache_after", "log", "generated_target_rules"):
        verify(build[key])
    require(build["cache_before"]["sha256"] == build["cache_after"]["sha256"] == record["build_config_sha256"],
            "build cache changed")
    for entry in configuration["generated_configuration_files"]:
        verify(entry)
    rules = read_json(resolve(build["generated_target_rules"]["path"]))
    for entry in rules:
        verify(entry)
        require(digest(entry["content"].encode()) == entry["sha256"], "preserved build-rule content differs")
    rule_text = "\n".join(entry["content"] for entry in rules)
    for stage in record["stages"]:
        require(stage["returncode"] == 0 and not stage["timed_out"], "capture stage incomplete")
        verify(stage["stdout"])
        verify(stage["stderr"])
    require(record["stages"][-1] == record["execution"], "execution differs from captured stage")
    registration = record["original_registration"]
    registration_json = read_json(directory / "ctest-registration.stdout.txt")
    require(len(registration_json["tests"]) == 1 and registration["raw_registration"] == registration_json["tests"][0],
            "registration differs from original CTest JSON")
    require(registration["command"] == registration["raw_registration"]["command"], "registered argv changed")
    properties = {entry["name"]: entry["value"] for entry in registration["properties"]}
    require(registration["properties"] == registration["raw_registration"]["properties"], "original properties changed")
    require(properties["ENVIRONMENT"] == record["original_environment_properties"], "environment properties changed")
    require(record["environment_overrides"] == configuration["environment_overrides"], "configured environment changed")
    require(record["removed_inherited_gtest_environment_keys"] == [], "unexpected inherited GoogleTest control")
    require(record["additional_execution_environment"] == {"GTEST_OUTPUT": "xml:" + record["gtest_xml"]["path"]},
            "unexpected additional test environment")
    require(not any(str(value).startswith("GTEST_") for value in properties["ENVIRONMENT"]), "registered test selection environment")
    require(not any(key.startswith("GTEST_") for key in record["environment_overrides"]), "configured test selection environment")
    command = registration["command"]
    gtest_flags = [arg for arg in command if arg.startswith("--gtest_")]
    require(len(gtest_flags) <= 1 and all(arg.startswith("--gtest_filter=") for arg in gtest_flags),
            "unexpected GoogleTest selector")
    names = {}
    for label in ("registered", "unfiltered"):
        inventory = record["inventories"][label]
        verify(inventory["inventory"])
        observed = read_json(resolve(inventory["inventory"]["path"]))
        names[label] = listing_names(directory / (label + "-listing.stdout.txt"))
        require(Counter(names[label]) == Counter(case["identity"] for case in observed["cases"]), "listing parser dropped case")
        require(observed["unparsed_lines"] == [] and observed["empty_suites"] == [], "unparsed runtime listing")
        require(observed["counts"]["cases"] == len(names[label]) and observed["counts"]["disabled"] == 0,
                "listing totals or disabled count differs")
        require(all(not case["disabled"] and case["execution"] == "not_run" for case in observed["cases"]),
                "listing promoted to execution or omitted disabled case")
        expected_command = command + ["--gtest_list_tests"] if label == "registered" else (
            [arg for arg in command if not arg.startswith("--gtest_filter=")] + ["--gtest_filter=*", "--gtest_list_tests"])
        require(inventory["capture"]["argv"] == expected_command, "runtime listing command differs")
        require(inventory["capture"]["cwd"] == properties["WORKING_DIRECTORY"], "listing working directory differs")
    require(Counter(names["registered"]) == Counter(names["unfiltered"]), "registered filter excludes compiled cases")
    require((directory / "registered-listing.stdout.txt").read_bytes() == (directory / "unfiltered-listing.stdout.txt").read_bytes(),
            "runtime listing bytes differ")
    xml, cases = raw[suite]
    require(dict(xml.attrib) == record["xml_counters"], "XML counters differ")
    outcomes = Counter(case["outcome"] for case in cases)
    require(dict(outcomes) == record["observed_outcome_counts"] == EXPECTED[suite], "outcomes differ")
    require(Counter(case["identity"] for case in cases) == Counter(names["registered"]), "runtime observations missing or added")
    fields = ("identity", "outcome", "attributes", "failures", "errors", "skipped")
    require(Counter(canonical(case) for case in cases) ==
            Counter(canonical({key: case[key] for key in fields}) for case in record["cases"]), "normalized outcome differs from XML")
    canonical_ids = []
    declaration_files = set()
    indexed = {(case["identity"], case["attributes"]["file"], case["attributes"]["line"]): case for case in record["cases"]}
    require(len(indexed) == len(cases), "duplicate original source tuple remains")
    for case in cases:
        attributes = case["attributes"]
        path, line = attributes["file"], int(attributes["line"])
        data = originals[path]
        require(0 < line <= len(data.splitlines()), "source line outside original file")
        require(str(SOURCE / path) in rule_text, "reported declaration absent from captured build rules")
        declaration_files.add(path)
        identifier = source_case_id(case, data)
        canonical_ids.append(identifier)
        normalized = indexed[(case["identity"], path, str(line))]
        if "case_id" in normalized:
            require(normalized["case_id"] == identifier and normalized["identity_status"] == "source_qualified", "source ID differs")
            require(normalized["source_location"] == {"path": path, "line": line, "sha256": digest(data)}, "source binding differs")
    require(len(set(canonical_ids)) == len(cases), "source IDs still ambiguous")
    if "verified_original_declaration_files" in record:
        require(set(record["verified_original_declaration_files"]) == declaration_files, "declaration-file inventory differs")
        for path, entry in record["verified_original_declaration_files"].items():
            data = originals[path]
            require(entry == {"path": path, "bytes": len(data), "sha256": digest(data),
                              "line_count": len(data.splitlines()), "verified_against_archive": True}, "source file receipt differs")
        require(record["name_multiplicities_match"] and record["all_observed_source_identities_resolved"] and
                record["source_identity_blockers"] == [], "unresolved source identity")
    log = (directory / "ctest-execution.stdout.txt").read_bytes().decode("utf-8", "surrogateescape")
    command_lines = re.findall(r"^\d+: Test command: (.*)$", log, re.M)
    require(len(command_lines) == 1 and shlex.split(command_lines[0]) == command, "CTest executed changed argv")
    require(re.findall(r"^\d+: Working Directory: (.*)$", log, re.M) == [properties["WORKING_DIRECTORY"]], "CTest changed working directory")
    for value in properties["ENVIRONMENT"]:
        require(bool(re.search(r"^\d+:  " + re.escape(value) + "$", log, re.M)), "CTest environment property absent")
    runs = Counter(re.findall(r"^\d+: \[ RUN +\] (\S+)$", log, re.M))
    passes = Counter(re.findall(r"^\d+: \[ +OK +\] (\S+) \([0-9]+ ms\)$", log, re.M))
    skips = Counter(re.findall(r"^\d+: \[ +SKIPPED +\] (\S+) \([0-9]+ ms\)$", log, re.M))
    require(runs == Counter(case["identity"] for case in cases), "original RUN callbacks differ from XML")
    require(passes == Counter(case["identity"] for case in cases if case["outcome"] == "passed"), "original OK callbacks differ")
    require(skips == Counter(case["identity"] for case in cases if case["outcome"] == "skipped"), "original skip callbacks differ")
    require("Added 0 tests to meet fixture requirements" in log, "unexpected fixture execution")
    junit = ET.parse(directory / "ctest-results.xml").getroot()
    leaves = junit.findall("testcase")
    require(len(leaves) == 1 and leaves[0].get("name") == registration["identity"] and leaves[0].get("status") == "run",
            "CTest driver result missing")
    require(not any(leaves[0].find(tag) is not None for tag in ("failure", "error", "skipped")), "CTest driver did not pass")
    expected_ctest = [record["execution"]["argv"][0], "--test-dir", configuration["command"][configuration["command"].index("-B") + 1],
                      "--build-config", "Release", "--tests-regex", "^" + registration["identity"] + "$", "--verbose",
                      "--no-tests=error", "--timeout", "600", "--output-junit", record["ctest_junit"]["path"]]
    require(record["execution"]["argv"] == expected_ctest, "unexpected CTest wrapper selection")
    require(record["browser_cases_executed"] == 0 and record["browser_parity"] is False and
            record["all_upstream_tests_enumerated"] is False and record["runtime_enumeration_complete"] is False,
            "native results promoted to product/browser completeness")
    summaries.append({"suite": suite, "reference": file_identity(directory / "native-reference.json"),
                      "listed_observations": len(names["registered"]), "distinct_display_names": len(set(names["registered"])),
                      "raw_xml_outcomes": dict(outcomes), "unique_source_identities_recomputed": len(set(canonical_ids)),
                      "declaration_files_verified": len(declaration_files), "registered_filter_missing_from_unfiltered": {},
                      "listing_xml_missing_or_added": {}, "ctest_driver_returncode": record["execution"]["returncode"],
                      "original_argv_environment_cwd_confirmed_in_log": True, "browser_cases_executed": 0,
                      "source_identity_fields_present_in_original_receipt": "capture_script" in record,
                      "skips": [case for case in cases if case["outcome"] == "skipped"]})

bli = records["BLI-source-identities"]
duplicates = []
for case in bli["cases"]:
    if case["identity"] == "stack.Peek":
        path, line = case["source_location"]["path"], case["source_location"]["line"]
        text = originals[path].decode("utf-8").splitlines()
        require(text[line - 1] == "TEST(stack, Peek)", "stack.Peek is not at its original declaration")
        duplicates.append({"display_name": case["identity"], "source_location": case["source_location"],
                           "case_id": case["case_id"], "declaration": text[line - 1],
                           "namespace": next(value for value in text if value.startswith("namespace ")),
                           "outcome": case["outcome"]})
require(len(duplicates) == 2 and len({entry["case_id"] for entry in duplicates}) == 2, "stack.Peek remains ambiguous")
require({source_case_id(case, originals[case["attributes"]["file"]]) for case in reversed(bli["cases"])} ==
        {case["case_id"] for case in bli["cases"]}, "identities depend on traversal order")
prior = read_json(CAPTURES / "BLI/failed-capture.json")
for entry in prior["files"]:
    verify(entry)
require(prior["tests_executed"] == 0 and prior["original_test_assertions_changed"] is False, "failed attempt altered")
require(not (CAPTURES / "BLI/gtest-results.xml").exists(), "earlier failed inventory attempt contains unexplained execution")

report = {
    "schema": 1, "review": "independent native product GoogleTest evidence reconciliation", "status": "verified",
    "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(), "source_commit": COMMIT,
    "source_archive": archive_identity, "audit_script": file_identity(Path(__file__)),
    "asserted_invariants_checked": checks, "suites": summaries, "duplicate_stack_peek": duplicates,
    "canonical_identity_uses_list_order": False, "canonical_identity_reverse_order_check": True,
    "preserved_initial_bli_failure": file_identity(CAPTURES / "BLI/failed-capture.json"),
    "original_files_verified_against_archive": [{"path": path, "bytes": len(data), "sha256": digest(data)}
                                               for path, data in sorted(originals.items())],
    "checked_input_files": sorted(checked_files.values(), key=lambda entry: entry["path"]),
    "new_native_tests_executed_by_review": 0, "browser_cases_executed": 0, "browser_passes_inferred": 0,
    "browser_parity": False, "all_upstream_tests_enumerated": False, "full_feature_parity": False,
    "limitations": [
        "This audits five already-executed native CTest drivers for one Linux Release configuration, not all Blender tests or configurations.",
        "Atomic and guardedalloc predate capture-script and source-case identity fields; their original XML/listings/build/CTest bindings are checked independently without rewriting historical receipts.",
        "Registered and unfiltered equality proves coverage of these compiled executable listings, not source cases excluded by compile-time platform/feature conditions or unbuilt executables.",
        "No browser execution, engine changes, original assertion changes, or new test passes are produced by this review.",
        "Hash-bound capture code removes inherited GTEST_* variables; captured original argv/properties and full runtime listing/XML reconciliation support the no-hidden-filter conclusion. The complete inherited non-GTEST environment was not archived.",
    ],
}
output = OUTPUT / "report.json"
if output.exists():
    raise RuntimeError("audit report already exists; retain immutable reviews")
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": report["status"], "suites": [{"suite": row["suite"], "outcomes": row["raw_xml_outcomes"]}
                                                        for row in summaries],
                  "report": {"path": str(output), "bytes": output.stat().st_size, "sha256": digest(output.read_bytes())},
                  "browser_passes_inferred": 0}, indent=2))
