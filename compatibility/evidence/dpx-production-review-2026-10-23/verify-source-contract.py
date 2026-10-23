#!/usr/bin/env python3
"""Persist a read-only DPX source review; execute no test or decoder program."""
from datetime import datetime, timezone
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PACKAGE = REPO / "patches/browser-codecs"
PINNED_MANIFEST = "1c98842c68dc7706630ce31132cdab20649ea61b860dd05b88722dc1a79b0bcf"
PINNED_ARCHIVE = "0fc59b8e2708ded02d3793b8f3331f037ed49bfcde38158f05ac0e876ebb85b7"
PINNED_HEAD = "9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": digest(data)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def apply_in_memory(original, patch):
    """Interpret exact text hunks; reject context, position or count mismatch."""
    source = original.decode().splitlines(keepends=True)
    patch_lines = patch.decode().splitlines(keepends=True)
    output, cursor, index = [], 0, 0
    while index < len(patch_lines):
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", patch_lines[index])
        index += 1
        if not match:
            continue
        start = int(match[1]) - 1 if int(match[1]) else 0
        old_count, new_count = int(match[2] or 1), int(match[4] or 1)
        require(start >= cursor, "patch hunk order changed")
        output += source[cursor:start]
        cursor, used_old, used_new = start, 0, 0
        while index < len(patch_lines) and not patch_lines[index].startswith("@@ "):
            line = patch_lines[index]
            index += 1
            if line.startswith(("--- ", "+++ ")):
                continue
            if line.startswith(" "):
                require(source[cursor] == line[1:], "patch context differs")
                output.append(source[cursor])
                cursor, used_old, used_new = cursor + 1, used_old + 1, used_new + 1
            elif line.startswith("-"):
                require(source[cursor] == line[1:], "patch removed line differs")
                cursor, used_old = cursor + 1, used_old + 1
            elif line.startswith("+"):
                output.append(line[1:])
                used_new += 1
            else:
                raise ValueError("unsupported patch line: " + repr(line))
        require((used_old, used_new) == (old_count, new_count), "patch hunk counts differ")
    output += source[cursor:]
    return "".join(output).encode()


def main():
    started = now()
    report_path = HERE / "report.json"
    require(not report_path.exists(), "refusing to replace an existing review report")
    observed_inputs = []

    def retain(path, relative):
        data = path.read_bytes()
        destination = HERE / "inputs" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        measured = identity(path)
        require(measured["sha256"] == digest(data), "input changed during snapshot")
        observed_inputs.append({"source": measured, "snapshot": identity(destination)})
        return data

    files = ["manifest.json", "0001-enable-original-image-codecs.patch", "apply.py", "test_patch.py",
             "dependency-patches/openimageio-dpx-signed-buffer.patch",
             "test-data/DPXColorConverter.cpp", "test-data/DPXHeader.h"]
    payloads = {name: retain(PACKAGE / name, "current/patches/browser-codecs/" + name) for name in files}
    additional_paths = ["tools/rebuild_browser_port.py", "tools/probe_browser_port.py",
                        ".github/workflows/browser-source-build.yml"]
    additional = {name: retain(REPO / name, "current/" + name) for name in additional_paths}
    require(digest(payloads["manifest.json"]) == PINNED_MANIFEST, "selected manifest changed")
    manifest = json.loads(payloads["manifest.json"])
    for key in ("patch", "application_helper"):
        row = manifest[key]
        data = payloads[row["file"]]
        require((len(data), digest(data)) == (row["bytes"], row["sha256"]), key + " identity mismatch")
    for row in manifest["dpx_signed_buffer"]["test_preimages"] + [manifest["dpx_signed_buffer"]["patch"]]:
        data = payloads[row["file"]]
        require((len(data), digest(data)) == (row["bytes"], row["sha256"]), "DPX component identity mismatch")

    archive_path = Path("/tmp/blended-dpx-source/OpenImageIO-3.1.13.1.tar.gz")
    archive_identity = identity(archive_path)
    require(archive_identity["sha256"] == PINNED_ARCHIVE, "pinned upstream archive changed")
    source_checks = []
    with tarfile.open(archive_path, "r:gz") as archive:
        for name in ("DPXColorConverter.cpp", "DPXHeader.h"):
            member = "OpenImageIO-3.1.13.1/src/dpx.imageio/libdpx/" + name
            data = archive.extractfile(member).read()
            require(data == payloads["test-data/" + name], "test source differs from pinned archive")
            source_checks.append({"archive_member": member, "bytes": len(data), "sha256": digest(data),
                                  "equals_retained_test_preimage": True})

    original = payloads["test-data/DPXColorConverter.cpp"]
    production_patch = payloads["dependency-patches/openimageio-dpx-signed-buffer.patch"]
    corrected = apply_in_memory(original, production_patch)
    expected = original
    for count in (3, 4):
        old = f"return pixels * -{count} * bytes;".encode()
        new = f"return -int64_t(pixels) * {count} * int64_t(bytes);".encode()
        require(expected.count(old) == 2, "active/inactive expression count changed")
        expected = expected.replace(old, new, 1)
    require(corrected == expected, "production patch changes more than the two active expressions")
    require(digest(corrected) == manifest["dpx_signed_buffer"]["after_sha256"], "source postimage mismatch")
    recovered_patch = REPO / "compatibility/evidence/dpx-standalone-recovery-2026-10-23/reconstructed-code/prospective-source-fix.patch"
    diagnostic_patch = retain(recovered_patch, "prior-diagnostic/prospective-source-fix.patch")
    require(digest(diagnostic_patch) == "09d43b9a0ad95165198e746fa77c012b5f63be94054a60af9b4101002f791233",
            "retained diagnostic patch identity mismatch")
    require(apply_in_memory(original, diagnostic_patch) == corrected, "the two patch encodings produce different source")

    # Git invocations below read existing objects only. They are not test runs.
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    require(head == PINNED_HEAD, "comparison base commit changed")
    old_patch_path = "patches/browser-codecs/0001-enable-original-image-codecs.patch"
    old_patch = subprocess.check_output(["git", "show", PINNED_HEAD + ":" + old_patch_path], cwd=REPO)
    old_manifest_data = subprocess.check_output(["git", "show", PINNED_HEAD + ":patches/browser-codecs/manifest.json"], cwd=REPO)
    old_dir = HERE / "inputs/base-commit"
    old_dir.mkdir(parents=True, exist_ok=True)
    (old_dir / "codec.patch").write_bytes(old_patch)
    (old_dir / "manifest.json").write_bytes(old_manifest_data)
    port_source = REPO / "compatibility/evidence/browser-codecs-5.2-2026-10-23/sources/port"
    port_inputs = {}
    for row in manifest["files"]:
        if row["before_sha256"] is not None:
            data = retain(port_source / row["path"], "original-port/" + row["path"])
            require(digest(data) == row["before_sha256"], "original port preimage mismatch")
            port_inputs[row["path"]] = data

    def derive_outputs(patch):
        result = {}
        for block in re.split(br"(?=^diff --git )", patch, flags=re.M):
            if not block.strip():
                continue
            name = block.splitlines()[0].split(b" b/", 1)[1].decode()
            require(name not in result, "duplicate outer patch path")
            result[name] = apply_in_memory(port_inputs.get(name, b""), block[block.index(b"@@ "):])
        return result

    current = derive_outputs(payloads[manifest["patch"]["file"]])
    previous = derive_outputs(old_patch)
    require(set(current) == {row["path"] for row in manifest["files"]}, "outer patch inventory mismatch")
    output_checks = []
    for row in manifest["files"]:
        data = current[row["path"]]
        require((len(data), digest(data)) == (row["after_bytes"], row["after_sha256"]), "outer postimage mismatch")
        output_checks.append({"path": row["path"], "bytes": len(data), "sha256": digest(data),
                              "equals_manifest": True, "equal_to_previous_patch_output": previous.get(row["path"]) == data})
    changed_paths = sorted(name for name in current if previous.get(name) != current[name])
    require(changed_paths == ["scripts/deps/openimageio-dpx-signed-buffer.patch", "scripts/deps/openimageio.sh"],
            "unexpected output changes beyond DPX recipe and inner patch")
    require(current["scripts/deps/openimageio-dpx-signed-buffer.patch"] == production_patch,
            "delivered inner patch differs from reviewed patch")
    old_manifest = json.loads(old_manifest_data)
    for key in ("dependencies", "dependency_recipe_insertion", "required_blender_cache", "required_oiio_cache", "required_environment"):
        require(manifest[key] == old_manifest[key], "codec build profile changed: " + key)
    pins = []
    for path, name in (("tools/rebuild_browser_port.py", "CODEC_PATCHSET_SHA256"),
                       ("tools/probe_browser_port.py", "CODEC_PATCH_MANIFEST_SHA256")):
        found = re.search(r"^" + name + r' = "([a-f0-9]{64})"', additional[path].decode(), flags=re.M)
        require(found is not None and found[1] == PINNED_MANIFEST, "build/probe manifest pin differs")
        pins.append({"file": path, "constant": name, "sha256": found[1]})
    ast.parse(payloads["test_patch.py"])

    for row in observed_inputs:
        require(identity(row["source"]["path"]) == row["source"], "reviewed source changed during persistence")
        require(identity(row["snapshot"]["path"]) == row["snapshot"], "review snapshot changed")
    require(identity(archive_path) == archive_identity, "upstream archive changed during review")
    report = {
        "schema": 1, "kind": "independent-read-only-DPX-production-source-review",
        "reviewer": "/root/complete_test_inventory", "status": "no_material_blocker_found",
        "persistence_and_source_recheck_started_utc": started, "completed_utc": now(),
        "earlier_review_exact_timestamps_not_reconstructed": True,
        "method": "Actual source reads, hashes, pinned-archive member comparison, exact in-memory patch interpretation and code review. No test or decoder executable was run by this reviewer.",
        "review_script": identity(__file__), "reviewed_input_snapshots": observed_inputs,
        "base_commit": head, "base_patch_snapshot": identity(old_dir / "codec.patch"),
        "base_manifest_snapshot": identity(old_dir / "manifest.json"),
        "upstream_archive": {**archive_identity,
            "url": "https://github.com/AcademySoftwareFoundation/OpenImageIO/archive/refs/tags/v3.1.13.1.tar.gz",
            "archive_retained_by_parent": True, "complete_archive_copied_into_this_review": False},
        "upstream_source_comparisons": source_checks,
        "manifest_sha256": PINNED_MANIFEST, "selected_manifest_pins": pins,
        "source_preimage_sha256": digest(original), "source_postimage_sha256": digest(corrected),
        "production_and_diagnostic_patch_postimages_identical": True,
        "exactly_two_active_expressions_changed": True,
        "inactive_implementation_and_other_source_bytes_unchanged": True,
        "source_diff": list(difflib.unified_diff(original.decode().splitlines(), corrected.decode().splitlines(), n=0)),
        "outer_postimage_checks": output_checks, "changed_outer_outputs": changed_paths,
        "recipe_diff": list(difflib.unified_diff(previous["scripts/deps/openimageio.sh"].decode().splitlines(),
            current["scripts/deps/openimageio.sh"].decode().splitlines(), n=2)),
        "codec_feature_profiles_and_dependency_selection_unchanged": True,
        "recipe_review": [
            "Source and inner patch hashes checked before patch --batch --fuzz=0.",
            "Exact corrected source postimage checked before CMake and compilation.",
            "Unconditional OIIO rebuild remains; an old installed marker cannot skip this recipe.",
            "Outer git apply --whitespace=error-all remains unchanged.",
            "Applied-output receipt inventory includes the inner patch and changed recipe."],
        "regression_source_review": {
            "actual_helper_body_and_descriptor_enum_extracted": True,
            "integer_width_models": [32, 64], "undefined_behavior_sanitizer_requested": True,
            "negative_descriptor_branches": [50, 51, 52, 102, 103],
            "negative_branch_input_combinations_declared": 120,
            "positive_and_default_input_combinations_declared": 380,
            "counts_are_source_inventory_not_execution_results": True,
            "rejection_cases": ["altered upstream source before patching", "altered inner patch before source mutation"],
            "scope": "Host-compiled arithmetic width models and exact recipe application; no Wasm ABI or decoder execution is implied."},
        "parent_reported_regression_result": {"source": "parent collaboration message", "tests_reported": 15,
            "failures_reported": 0, "exit_reported": 0, "elapsed_seconds_reported": 1.348,
            "independently_observed_by_this_reviewer": False, "raw_parent_test_receipt_reviewed": False},
        "reviewer_test_cases_executed": 0, "reviewer_decoder_operations_executed": 0,
        "reviewer_Blender_invocations_executed": 0, "production_source_files_modified_by_reviewer": False,
        "qualification_credit": 0, "full_parity": False,
        "validation_limits": [
            "This report is a source-review record, not a fabricated process or test receipt.",
            "The parent-reported regression run is not attributed to this reviewer.",
            "The interrupted standalone controlled comparison has no observed modified-library runtime result.",
            "Numeric width models do not prove a particular Wasm build or successful DPX decoding.",
            "A new complete original ImBuf invocation is required before changing any original-suite qualification."]}
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": identity(report_path), "status": report["status"],
                      "reviewer_tests_executed": 0, "qualification_credit": 0}))


if __name__ == "__main__":
    main()
