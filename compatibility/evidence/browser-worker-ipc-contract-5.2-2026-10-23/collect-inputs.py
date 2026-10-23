#!/usr/bin/env python3
"""Freeze read-only source and existing runtime evidence for an IPC proposal."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO.parent / "runtime"
PORT = RUNTIME / "browser-sqlite-work/gessa"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "tools"))
from browser_package_overlay import parse_preload


def identity(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    return identity(path)


def archive_members(path, selected):
    result = {}
    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            if not member.isfile() or "/" not in member.name:
                continue
            relative = member.name.split("/", 1)[1]
            if relative in selected:
                if relative in result:
                    raise ValueError("duplicate archive member")
                result[relative] = archive.extractfile(member).read()
    if set(result) != set(selected):
        raise ValueError("source closure member missing")
    return result


def main():
    if (HERE / "source-bindings.json").exists():
        raise FileExistsError("inputs are already frozen")
    initial = json.loads((HERE / "source-inputs-initial.json").read_text())
    assert identity(Path(initial["source_archive"]["path"])) == initial["source_archive"]
    blender = {entry["upstream_path"]: (HERE / "source/blender" / entry["upstream_path"]).read_bytes()
               for entry in initial["inputs"]}
    for item in initial["inputs"]:
        data = blender[item["upstream_path"]]
        assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
    extra = archive_members(Path(initial["source_archive"]["path"]), {"doc/python_api/sphinx_stub_gen.py"})
    for name, data in extra.items():
        blender[name] = data
        write_bytes(HERE / "source/blender" / name, data)

    patch_manifest_path = REPO / "patches/browser-sqlite/manifest.json"
    patch_manifest = json.loads(patch_manifest_path.read_text())
    python_pin = patch_manifest["python"]
    python_archive = PORT / "build-deps/_cache" / python_pin["archive"]
    python_archive_id = identity(python_archive)
    assert python_archive_id["sha256"] == python_pin["sha256"]
    assert python_archive_id["bytes"] == python_pin["bytes"]
    with python_archive.open("rb") as stream:
        assert hashlib.file_digest(stream, "md5").hexdigest() == python_pin["original_blender_pin"]["value"]
    python_names = {
        "configure.ac", "Tools/wasm/config.site-wasm32-emscripten",
        "Python/thread.c", "Python/thread_pthread.h", "Modules/_threadmodule.c",
        "Modules/_multiprocessing/semaphore.c", "Lib/socket.py", "Lib/subprocess.py",
        "Lib/threading.py", "Lib/queue.py",
    } | {"Lib/multiprocessing/" + name + ".py" for name in (
        "context", "process", "connection", "popen_spawn_posix", "popen_fork", "spawn",
        "util", "reduction", "resource_tracker", "synchronize")}
    python = archive_members(python_archive, python_names)
    python_snapshots = []
    for name, data in sorted(python.items()):
        snapshot = write_bytes(HERE / "source/cpython-3.13.13" / name, data)
        assert (PORT / "build-deps/python/Python-3.13.13" / name).read_bytes() == data
        python_snapshots.append({"upstream_path": name, "snapshot": snapshot})

    # Reconstruct only a new evidence copy of the original pinned port recipe.
    # The exact baseline hash is independently present in the old build receipt.
    patch = patch_manifest["patches"][0]
    current_recipe = PORT / patch["destination"]
    assert identity(current_recipe)["sha256"] == patch["after_sha256"]
    original_recipe = HERE / "source/port" / patch["destination"]
    write_bytes(original_recipe, current_recipe.read_bytes())
    patch_path = REPO / "patches/browser-sqlite" / patch["file"]
    assert identity(patch_path)["sha256"] == patch["sha256"]
    command = ["patch", "--reverse", "--batch", "--fuzz=0", "-p1", "--input", str(patch_path)]
    process = subprocess.run(command, cwd=HERE / "source/port", capture_output=True, timeout=10)
    write_bytes(HERE / "original-recipe-reconstruction.log", process.stdout + process.stderr)
    assert process.returncode == 0
    assert identity(original_recipe)["sha256"] == patch["before_sha256"]
    recipes_path = RUNTIME / "source/dependency-recipe-inputs.json"
    recipes = json.loads(recipes_path.read_text())
    assert recipes["python"]["sha256"] == identity(original_recipe)["sha256"]
    assert recipes["python"]["bytes"] == identity(original_recipe)["bytes"]

    build_path = RUNTIME / "source/source-build.json"
    build = json.loads(build_path.read_text())
    assert build["port_commit"] == "0e02e84b2bc5d9b27a6dc6e275443292f781fbad"
    assert build["upstream_commit"] == initial["source_commit"]
    engine = RUNTIME / "source/engine/blender-source-development/bin"
    verified_engine = []
    for expected in build["engine_files"]:
        path = engine / Path(expected["path"]).name
        actual = identity(path)
        assert actual["sha256"] == expected["sha256"] and actual["bytes"] == expected["bytes"]
        verified_engine.append(actual)
    entries, size = parse_preload((engine / "blender_browser.js").read_text())
    assert size == (engine / "blender_browser.data").stat().st_size
    mapping = {entry["filename"]: entry for entry in entries}
    payload_names = {"/bw/python/lib/python3.13/" + path[4:]: ("cpython-3.13.13", path)
                     for path in python if path.startswith("Lib/")}
    payload_names["/bw/scripts/modules/_bpy_internal/http/downloader.py"] = (
        "blender", "scripts/modules/_bpy_internal/http/downloader.py")
    payload_names["/bw/python/lib/python3.13/_multiprocessing.py"] = ("port", None)
    config_name = "/bw/python/lib/python3.13/_sysconfigdata__emscripten_wasm32-emscripten.py"
    payload_names[config_name] = ("generated-config", None)
    shipped = []
    generated_config = None
    with (engine / "blender_browser.data").open("rb") as datafile:
        for name, (origin, relative) in sorted(payload_names.items()):
            entry = mapping[name]
            datafile.seek(entry["start"])
            data = datafile.read(entry["end"] - entry["start"])
            row = {"runtime_path": name, "offset": entry["start"], "bytes": len(data),
                   "sha256": hashlib.sha256(data).hexdigest(), "source_kind": origin}
            if origin == "cpython-3.13.13":
                assert data == python[relative]
                row["source_path"] = "source/cpython-3.13.13/" + relative
            elif origin == "blender":
                assert data == blender[relative]
                row["source_path"] = "source/blender/" + relative
            elif origin == "port":
                original = PORT / "scripts/deps/python-shims/_multiprocessing.py"
                assert data == original.read_bytes()
                snapshot = write_bytes(HERE / "source/port/scripts/deps/python-shims/_multiprocessing.py", data)
                row["snapshot"] = snapshot
            else:
                snapshot = write_bytes(HERE / "source/base-runtime" / name.lstrip("/"), data)
                row["snapshot"] = snapshot
                tree = ast.parse(data.decode())
                assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                                  and any(isinstance(target, ast.Name) and target.id == "build_time_vars"
                                          for target in node.targets))
                generated_config = ast.literal_eval(assignment.value)
            shipped.append(row)
    config_keys = [key for key in generated_config if any(token in key for token in (
        "MULTIPROCESS", "POSIXSHMEM", "POSIXSUBPROCESS", "SOCKETPAIR", "HAVE_FORK", "HAVE_VFORK",
        "HAVE_SEM", "HAVE_PTHREAD_STUBS")) or key in (
        "MODULE__SOCKET_STATE", "CONFIG_ARGS", "CFLAGS", "CFLAGS_NODIST", "LDFLAGS_NODIST", "LINKFORSHARED")]

    sdk = PORT / "tools/emsdk/upstream/emscripten"
    sdk_names = ["emscripten-version.txt", "system/lib/libc/emscripten_libc_stubs.c",
                 "system/lib/libc/emscripten_syscall_stubs.c", "system/lib/pthread/library_pthread_stub.c"]
    sdk_snapshots = [write_bytes(HERE / "source/emscripten-6.0.5" / name, (sdk / name).read_bytes())
                     for name in sdk_names]
    assert (sdk / "emscripten-version.txt").read_text().strip() == '"6.0.5"'
    canonical = PORT / "patches/PREVIEW_SNAPSHOT.patch"
    assert identity(canonical)["sha256"] == build["canonical_patch_sha256"]

    receipt_paths = {
        "manifest": "compatibility/candidate-suites/unittest-main-5.2/script_http_downloader.json",
        "native": "compatibility/evidence/unittest-native-5.2-2026-10-23/script_http_downloader/native_reference.json",
        "browser": "compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23/script_http_downloader/qualification.json",
        "docgen_browser": "compatibility/evidence/unittest-browser-resources-5.2-2026-10-23/script_pyapi_doc_gen/qualification.json",
    }
    receipts = {key: identity(REPO / path) for key, path in receipt_paths.items()}
    native = json.loads((REPO / receipt_paths["native"]).read_text())
    browser = json.loads((REPO / receipt_paths["browser"]).read_text())
    docs = json.loads((REPO / receipt_paths["docgen_browser"]).read_text())
    manifest = json.loads((REPO / receipt_paths["manifest"]).read_text())
    assert receipts["native"]["sha256"] == manifest["native_discovery"]["sha256"]
    assert native["execution"]["suites"][0]["discovered_ids"] == browser["execution"]["suites"][0]["discovered_ids"]
    baseline = {"native": {"status": native["status"], "process": native["process"],
                           "driver": native["execution"]["driver_observation"], "suites": native["execution"]["suites"]},
                "browser": {"status": browser["status"], "driver": browser["execution"]["driver_observation"],
                            "suites": browser["execution"]["suites"], "browser_errors": browser["browser_errors"]},
                "docgen_browser": {"status": docs["status"], "suites": docs["execution"]["suites"],
                                   "host_tools": docs["execution"]["driver_observation"]["host_tools"]}}
    baseline_id = write_bytes(HERE / "existing-observations.json", (json.dumps(baseline, indent=2) + "\n").encode())
    report = {
        "schema": 1, "kind": "read-only-browser-worker-ipc-analysis-inputs",
        "created_utc": datetime.now(timezone.utc).isoformat(), "collector": identity(Path(__file__).resolve()),
        "source_commit": initial["source_commit"], "blender_archive": initial["source_archive"],
        "blender_snapshots": [identity(HERE / "source/blender" / name) for name in sorted(blender)],
        "python_archive": python_archive_id, "python_pin_manifest": identity(patch_manifest_path),
        "python_snapshots": python_snapshots,
        "port_commit": build["port_commit"], "port_recipe": identity(original_recipe),
        "port_recipe_old_build_identity": recipes["python"],
        "recipe_reconstruction": {"command": command, "returncode": process.returncode,
                                  "log": identity(HERE / "original-recipe-reconstruction.log"),
                                  "production_files_modified": False},
        "base_build_receipt": identity(build_path), "base_recipe_receipt": identity(recipes_path),
        "base_artifact_identity": build["artifact"], "verified_base_engine_files": verified_engine,
        "preload_parser": identity(REPO / "tools/browser_package_overlay.py"),
        "packaged_source_comparisons": shipped,
        "packaged_python_configuration": {key: generated_config[key] for key in sorted(config_keys)},
        "docutils_packaged_paths": [name for name in mapping if "/site-packages/docutils/" in name],
        "sdk_version": "6.0.5", "sdk_source_snapshots": sdk_snapshots,
        "sdk_source_authority_limit": "Exact bytes from the previously installed pinned SDK; this analysis does not repeat verification against its full SDK release archive.",
        "canonical_port_patch": identity(canonical),
        "existing_receipts": receipts, "existing_observations": baseline_id,
        "source_files_changed": False, "tests_changed": False,
        "new_tests_executed": 0, "new_browser_passes": 0, "full_feature_parity": False,
    }
    out = write_bytes(HERE / "source-bindings.json", (json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps({"receipt": out, "packaged_config": report["packaged_python_configuration"],
                      "docutils_packaged_path_count": len(report["docutils_packaged_paths"])}, indent=2))


if __name__ == "__main__":
    main()
