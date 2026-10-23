#!/usr/bin/env python3
"""Capture a separate DPX diagnostic with one copied archive object replaced."""
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import tarfile
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"
BASELINE_SHA = "c7d69f18506349baa47888cd687d8d33af514d32b3877e771fa1c91544cabeaa"
HELPER_SHA = "8a6b9316adeae5073ee82f143731c1f5b8004c4fbd7e082bab9a0230c556ab72"
PATCH_SHA = "09d43b9a0ad95165198e746fa77c012b5f63be94054a60af9b4101002f791233"
PREIMAGE_SHA = "793e53edfac8dc79b8cea7bf0cc15c29a23b947e5559cf65cbe4bafd7227ebf1"
POSTIMAGE_SHA = "28dd63ce548ee759f09bd23c2a90040408e3f91ffdfc7be3888fb357ad11d9b3"
MEMBER = "DPXColorConverter.cpp.o"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive_members(path):
    """Read every regular GNU archive member, preserving order and duplicates."""
    data = Path(path).read_bytes()
    if data[:8] != b"!<arch>\n":
        raise ValueError("expected a regular archive, not a thin or unknown archive")
    cursor, long_names, rows, occurrences = 8, None, [], {}
    while cursor < len(data):
        header = data[cursor:cursor + 60]
        if len(header) != 60 or header[58:] != b"`\n":
            raise ValueError("malformed archive header")
        size = int(header[48:58].decode("ascii").strip())
        payload = data[cursor + 60:cursor + 60 + size]
        if len(payload) != size:
            raise ValueError("truncated archive member")
        encoded_name = header[:16].decode("ascii").strip()
        if encoded_name in ("/", "/SYM64/"):
            kind, name = "symbol_index", encoded_name
        elif encoded_name == "//":
            kind, name, long_names = "long_name_table", encoded_name, payload
        elif encoded_name.startswith("/") and encoded_name[1:].isdigit():
            if long_names is None:
                raise ValueError("archive long name used before its table")
            offset = int(encoded_name[1:])
            end = long_names.index(b"/\n", offset)
            kind, name = "object", long_names[offset:end].decode("utf-8")
        elif encoded_name.startswith("#1/"):
            raise ValueError("BSD extended names are not part of the observed GNU contract")
        else:
            kind, name = "object", encoded_name.removesuffix("/")
        occurrence = occurrences.get((kind, name), 0)
        occurrences[(kind, name)] = occurrence + 1
        rows.append({"index": len(rows), "kind": kind, "name": name,
            "name_occurrence": occurrence, "header_hex": header.hex(), "bytes": size,
            "sha256": digest(payload), "offset": cursor})
        cursor += 60 + size + (size % 2)
    if cursor != len(data):
        raise ValueError("archive ending is inconsistent")
    return rows


def main():
    helper_path = HERE / "run-baseline.py"
    if digest(helper_path.read_bytes()) != HELPER_SHA:
        raise ValueError("baseline utility source changed")
    spec = importlib.util.spec_from_file_location("retained_dpx_baseline", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    identity, save, now = helper.identity, helper.save, helper.now
    baseline_path = HERE / "baseline-attempt-01/execution.json"
    if digest(baseline_path.read_bytes()) != BASELINE_SHA:
        raise ValueError("baseline execution changed")
    baseline = json.loads(baseline_path.read_text())
    if not baseline["original_input_closure_preserved"] or not baseline["regenerated_inputs_preserved"]:
        raise ValueError("baseline inputs did not survive unchanged")
    expected_names = ["file-created-memory", "file-created-file", "memory-created-memory", "memory-created-file"]
    runtime_rows = baseline["commands"][-4:]
    if [r["name"] for r in runtime_rows] != expected_names:
        raise ValueError("baseline operation names differ")
    for row in runtime_rows:
        if row["actual_returncode"] != 3 or row["timeout_occurred"] or row.get("capture_error"):
            raise ValueError("baseline did not preserve the expected actual exception")
        log = Path(row["stdout"]["path"])
        if identity(log) != row["stdout"]:
            raise ValueError("baseline stdout changed")
        events = [json.loads(line.split(":", 1)[1]) for line in log.read_text().splitlines()
                  if line.startswith("DPX_STANDALONE_DIAGNOSTIC:")]
        if events[-1] != {"kind": "caught_std_exception", "stage": "read_image_before",
            "detail": {"typeid_name": "St12length_error", "what": "vector"}, "qualification_credit": 0}:
            raise ValueError("baseline final exception differs")
    closure_path = HERE / "input-closure.json"
    if identity(closure_path) != baseline["input_closure"]:
        raise ValueError("baseline input closure changed")
    closure = json.loads(closure_path.read_text())
    original_before = helper.verify_inputs(closure)
    baseline_bound = [baseline["compiled_object"], *baseline["standalone_artifacts"],
        *baseline["regenerated_inputs_after"], *baseline["actual_compile_header_inputs"]]
    for row in baseline_bound:
        if identity(row["path"]) != row:
            raise ValueError("bound baseline build/input file changed: " + row["path"])
    if shutil.disk_usage(HERE).free < helper.MINIMUM_FREE_BYTES:
        raise RuntimeError("less than 4 GiB free")
    output = HERE / "one-object-attempt-01"
    output.mkdir(exist_ok=False)
    work = RUNTIME / "dpx-memory-io-diagnostic-5.2-2026-10-23/one-object-build"
    work.mkdir(exist_ok=False)
    sdk, prefix = Path(closure["sdk_root"]), Path(closure["prefix_root"])
    old_root = RUNTIME / "browser-codecs-work/oiio-port/build-deps/openimageio"
    old_source = old_root / "OpenImageIO-3.1.13.1"
    old_build = old_root / "build"
    commands_path = old_build / "compile_commands.json"
    compile_rows = [r for r in json.loads(commands_path.read_text()) if r["file"].endswith("/" + MEMBER[:-2])]
    if len(compile_rows) != 1:
        raise ValueError("original object compile command is not unique")
    original_compile = compile_rows[0]
    original_argv = shlex.split(original_compile["command"])
    original_source = Path(original_compile["file"])
    if digest(original_source.read_bytes()) != PREIMAGE_SHA:
        raise ValueError("upstream source preimage changed")
    patch_path = REPO / "compatibility/evidence/dpx-signed-sentinel-source-analysis-5.2-2026-10-23/prospective-source-fix.patch"
    if digest(patch_path.read_bytes()) != PATCH_SHA:
        raise ValueError("reviewed signed-size patch changed")
    shutil.copyfile(patch_path, output / "applied-source-fix.patch")
    shutil.copyfile(commands_path, output / "original-compile-commands.json")
    for filename in ("flags.make", "build.make"):
        shutil.copyfile(old_build / "src/libOpenImageIO/CMakeFiles/OpenImageIO.dir" / filename, output / filename)
    source_dir = work / "source/src/dpx.imageio/libdpx"
    source_dir.mkdir(parents=True)
    copies = []
    source_archive = RUNTIME / "browser-codecs-work/cache/OpenImageIO-3.1.13.1.tar.gz"
    with tarfile.open(source_archive, "r:gz") as archive:
        for path in sorted(original_source.parent.iterdir()):
            if not path.is_file():
                raise ValueError("unexpected non-file in copied libdpx source directory")
            member = "OpenImageIO-3.1.13.1/" + str(path.relative_to(old_source))
            data = archive.extractfile(member).read()
            if data != path.read_bytes():
                raise ValueError("local libdpx source differs from pinned upstream archive")
            copied = source_dir / path.name
            copied.write_bytes(data)
            copies.append({"archive_member": member, "original": identity(path), "copied_before": identity(copied)})
    modified_source = source_dir / original_source.name
    original_text = modified_source.read_text()
    modified_text = original_text
    for old, new in (("return pixels * -3 * bytes;", "return -int64_t(pixels) * 3 * int64_t(bytes);"),
                     ("return pixels * -4 * bytes;", "return -int64_t(pixels) * 4 * int64_t(bytes);")):
        # A later inactive implementation repeats both expressions. The exact
        # reviewed patch changes only their first, active occurrences.
        if modified_text.count(old) != 2:
            raise ValueError("active and inactive patch preimage count changed")
        modified_text = modified_text.replace(old, new, 1)
    derived_patch = "".join(difflib.unified_diff(original_text.splitlines(keepends=True), modified_text.splitlines(keepends=True),
        fromfile="a/src/dpx.imageio/libdpx/DPXColorConverter.cpp", tofile="b/src/dpx.imageio/libdpx/DPXColorConverter.cpp"))
    if derived_patch.encode() != patch_path.read_bytes() or digest(modified_text.encode()) != POSTIMAGE_SHA:
        raise ValueError("literal source correction does not equal reviewed exact patch/postimage")
    modified_source.write_text(modified_text)
    shutil.copyfile(modified_source, output / "DPXColorConverter.cpp.after")
    source_after = [identity(path) for path in sorted(source_dir.iterdir())]
    include_roots = [old_source / "src/include", old_build / "include", old_build / "src/include", old_build / "deps/include"]
    extra_input_paths = {path for root in include_roots for path in root.rglob("*") if path.is_file()}
    extra_input_paths.update((commands_path, original_source, sdk / "upstream/bin/llvm-ar"))
    extra_before = [identity(path) for path in sorted(extra_input_paths)]
    new_object = work / MEMBER
    compile_argv = list(original_argv)
    compile_argv[compile_argv.index("-o") + 1] = str(new_object)
    compile_argv[compile_argv.index("-c") + 1] = str(modified_source)
    compile_argv += ["-MD", "-MF", str(work / "DPXColorConverter.cpp.o.d")]
    original_archive = prefix / "lib/libOpenImageIO.a"
    copied_archive = work / "libOpenImageIO.a"
    shutil.copyfile(original_archive, copied_archive)
    if identity(original_archive)["sha256"] != identity(copied_archive)["sha256"]:
        raise ValueError("copied archive is not initially identical")
    members_before = archive_members(original_archive)
    if sum(row["kind"] == "object" and row["name"] == MEMBER for row in members_before) != 1:
        raise ValueError("DPX object archive identity is not unique")
    ar_command = [str(sdk / "upstream/bin/llvm-ar"), "rcsD", str(copied_archive), str(new_object)]
    link_command = list(baseline["planned_commands"]["link"])
    if link_command.count(str(original_archive)) != 1:
        raise ValueError("baseline link archive is not unique")
    link_command[link_command.index(str(original_archive))] = str(copied_archive)
    link_command[link_command.index("-o") + 1] = str(work / "dpx-probe.js")
    operations = []
    for row in baseline["planned_commands"]["runtime_operations"]:
        command = list(row["command"])
        command[1] = str(work / "dpx-probe.js")
        command[-1] = str(output / (row["name"] + ".pixels"))
        operations.append({**row, "command": command})
    report = {"schema": 1, "kind": "one-object-controlled-DPX-diagnostic", "status": "running",
        "profile_id": "dpx-standalone-oiio-3.1.13.1-signed-sentinel-one-object-v1", "started_utc": now(),
        "capture_script": identity(__file__), "baseline_script": identity(helper_path), "baseline_receipt": identity(baseline_path),
        "input_closure": identity(closure_path), "original_input_observations_before": original_before,
        "baseline_build_and_input_bindings_before": baseline_bound, "additional_compile_inputs_before": extra_before,
        "source_archive": identity(source_archive), "source_copy_derivation": copies,
        "reviewed_patch": identity(patch_path), "applied_patch": identity(output / "applied-source-fix.patch"),
        "source_postimage": identity(modified_source), "isolated_source_inputs_before": source_after,
        "original_compile_entry": original_compile, "original_compile_argv": original_argv,
        "compile_delta": "Only isolated source/object paths, plus dependency-file observation arguments.",
        "link_delta": "Only copied OpenImageIO archive path and distinct diagnostic output path.",
        "runtime_delta": "Only newly linked diagnostic program path and distinct pixel-output paths.",
        "original_archive": identity(original_archive), "copied_archive_before": identity(copied_archive),
        "archive_members_before": members_before, "environment": baseline["environment"],
        "planned_commands": {"compile": compile_argv, "archive": ar_command, "link": link_command, "runtime_operations": operations},
        "commands": [], "minimum_free_bytes": helper.MINIMUM_FREE_BYTES, "free_bytes_before": shutil.disk_usage(HERE).free,
        "original_Blender_test_cases_executed": 0, "qualification_credit": 0,
        "same_consumer_object_as_baseline": baseline["compiled_object"], "local_archive_equal_CI_claimed": False, "full_parity": False}
    receipt_path = output / "execution.json"
    save(output / "prospective-command.json", report)
    report["prospective_command"] = identity(output / "prospective-command.json")
    save(receipt_path, report)

    def run(name, command, cwd, timeout, require_zero):
        if shutil.disk_usage(HERE).free < helper.MINIMUM_FREE_BYTES:
            raise RuntimeError("less than 4 GiB free")
        row = {"name": name, "argv": command, "cwd": str(cwd), "started_utc": now(), "timeout_seconds": timeout}
        report["commands"].append(row)
        save(receipt_path, report)
        start, process, timed_out, termination = time.monotonic(), None, False, []
        with (output / (name + ".stdout.log")).open("xb") as stdout, (output / (name + ".stderr.log")).open("xb") as stderr:
            try:
                process = subprocess.Popen(command, cwd=cwd, env=report["environment"], stdin=subprocess.DEVNULL,
                    stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    for sig in (signal.SIGTERM, signal.SIGKILL):
                        termination.append({"signal": sig.name, "utc": now()})
                        os.killpg(process.pid, sig)
                        try:
                            process.wait(timeout=5)
                            break
                        except subprocess.TimeoutExpired:
                            continue
            except Exception as error:
                row["capture_error"] = {"type": type(error).__name__, "message": str(error)}
                if process is not None and process.poll() is None:
                    termination.append({"signal": "SIGKILL", "utc": now(), "reason": "capture error"})
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            finally:
                row.update(actual_returncode=process.returncode if process is not None else None,
                    timeout_occurred=timed_out, termination_events=termination, finished_utc=now(), elapsed_seconds=time.monotonic() - start)
        row.update(stdout=identity(output / (name + ".stdout.log")), stderr=identity(output / (name + ".stderr.log")))
        save(receipt_path, report)
        print(json.dumps({"name": name, "actual_returncode": row["actual_returncode"], "timeout_occurred": timed_out, "qualification_credit": 0}), flush=True)
        if require_zero and (row["actual_returncode"] != 0 or timed_out or row.get("capture_error")):
            raise RuntimeError("controlled diagnostic preparation failed: " + name)
        return row

    try:
        run("compile-one-object", compile_argv, original_compile["directory"], 180, True)
        dependency_file = work / "DPXColorConverter.cpp.o.d"
        dependencies = dependency_file.read_text().replace("\\\n", " ").split(":", 1)[1].split()
        report["actual_compile_header_inputs"] = [identity(Path(path)) for path in sorted(set(dependencies))]
        shutil.copyfile(dependency_file, output / "compile-dependencies.d")
        report["replacement_object"] = identity(new_object)
        run("replace-one-archive-object", ar_command, REPO, 30, True)
        members_after = archive_members(copied_archive)
        if len(members_after) != len(members_before):
            raise ValueError("archive member count changed")
        changed = []
        for before, after in zip(members_before, members_after):
            key = lambda row: (row["index"], row["kind"], row["name"], row["name_occurrence"])
            if key(before) != key(after):
                raise ValueError("archive ordered member identities changed")
            if (before["bytes"], before["sha256"]) != (after["bytes"], after["sha256"]):
                changed.append({"before": before, "after": after})
                if after["kind"] != "symbol_index" and not (after["kind"] == "object" and after["name"] == MEMBER):
                    raise ValueError("an unrelated archive payload changed")
        changed_objects = [row for row in changed if row["after"]["kind"] == "object"]
        if len(changed_objects) != 1 or changed_objects[0]["after"]["sha256"] != identity(new_object)["sha256"]:
            raise ValueError("expected exact single-object replacement was not observed")
        report.update(archive_members_after=members_after, archive_payload_changes=changed,
            exactly_one_object_changed=True, modified_archive=identity(copied_archive))
        run("link-same-consumer", link_command, REPO, 180, True)
        report["standalone_artifacts"] = [identity(work / name) for name in ("dpx-probe.js", "dpx-probe.wasm")]
        for operation in operations:
            run(operation["name"], operation["command"], REPO, 30, False)
        report["status"] = "all_four_controlled_operations_captured"
    except Exception as error:
        report.update(status="controlled_diagnostic_preparation_or_capture_failed", error={"type": type(error).__name__, "message": str(error)})
    finally:
        try:
            original_after = helper.verify_inputs(closure)
            report["original_input_observations_after"] = original_after
            report["baseline_build_and_input_bindings_after"] = [identity(row["path"]) for row in baseline_bound]
            report["additional_compile_inputs_after"] = [identity(row["path"]) for row in extra_before]
            report["isolated_source_inputs_after"] = [identity(path) for path in sorted(source_dir.iterdir())]
            preserved = (original_before == original_after and baseline_bound == report["baseline_build_and_input_bindings_after"]
                and extra_before == report["additional_compile_inputs_after"] and source_after == report["isolated_source_inputs_after"]
                and digest(baseline_path.read_bytes()) == BASELINE_SHA)
            report["baseline_original_and_isolated_inputs_preserved"] = preserved
            if not preserved:
                raise ValueError("bound baseline, original or isolated inputs changed")
        except Exception as error:
            report.update(status="controlled_diagnostic_input_integrity_failed", preservation_error={"type": type(error).__name__, "message": str(error)})
        report["raw_pixel_outputs"] = [identity(path) for path in sorted(output.glob("*.pixels"))]
        report["free_bytes_after"] = shutil.disk_usage(HERE).free
        report["finished_utc"] = now()
        save(receipt_path, report)
    print(json.dumps({"receipt": identity(receipt_path), "status": report["status"], "qualification_credit": 0}), flush=True)
    return 0 if report["status"] == "all_four_controlled_operations_captured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
