"""Stage the pinned tracked subset of Blender's configured shared-library install."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent
SOURCE_COMMIT = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
LIBRARY_COMMIT = "2b5fbb917a1bf7537cb25456fcb9064302d7e168"
LIBRARIES = WORKSPACE / "runtime/product-native-libs/linux_x64"
BUILD = WORKSPACE / "runtime/product-native-configure-optix"
DESTINATION = BUILD / "bin/lib"
OUTPUT = HERE / "runtime-library-staging"
OUTPUT.mkdir()
NOW = lambda: datetime.now(timezone.utc).isoformat()


def identity(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
            size += len(data)
    return {"path": str(path), "bytes": size, "sha256": digest.hexdigest()}


def write(name, data):
    path = OUTPUT / name
    path.write_text(json.dumps(data, indent=2) + "\n")
    return identity(path)


def git(*args, input=None):
    return subprocess.check_output(["git", *args], cwd=LIBRARIES, input=input)


report = {
    "schema": 1,
    "started_utc": NOW(),
    "source_commit": SOURCE_COMMIT,
    "library_commit": LIBRARY_COMMIT,
    "library_repository": "https://projects.blender.org/blender/lib-linux_x64.git",
    "destination": str(DESTINATION),
    "status": "preflight",
    "tests_executed": 0,
    "runtime_dependency_closure_claimed": False,
    "script": identity(Path(__file__)),
}
try:
    assert git("rev-parse", "HEAD").decode().strip() == LIBRARY_COMMIT
    configuration_path = REPO / "compatibility/evidence/product-configure-2026-10-23/configure-with-optix.json"
    configuration = json.loads(configuration_path.read_text())
    report["configuration_receipt"] = identity(configuration_path)
    report["native_library_hydration_receipt"] = identity(
        REPO / "compatibility/evidence/product-configure-2026-10-23/native-library-hydration.json")
    report["build_receipt"] = identity(HERE / "build.json")
    report["cache_before"] = identity(BUILD / "CMakeCache.txt")
    report["binary_before"] = identity(BUILD / "bin/tests/cycles_test")
    report["initial_free_disk_bytes"] = shutil.disk_usage(WORKSPACE).free
    report["initial_destination_entries"] = sorted(path.name for path in DESTINATION.iterdir())
    assert not report["initial_destination_entries"], "destination must be empty"

    # Bind the generating source rules to the original source archive.
    archive_path = WORKSPACE / "runtime/blender-product-94363991.tar.gz"
    report["source_archive"] = identity(archive_path)
    assert report["source_archive"]["sha256"] == "e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7"
    source = Path(configuration["command"][configuration["command"].index("-S") + 1])
    report["original_rules"] = []
    with tarfile.open(archive_path, "r:gz") as archive:
        for relative in ["source/creator/CMakeLists.txt", "build_files/cmake/platform/platform_unix.cmake", "build_files/cmake/testing.cmake"]:
            data = archive.extractfile("blender-" + SOURCE_COMMIT + "/" + relative).read()
            current = source / relative
            assert current.read_bytes() == data, relative
            report["original_rules"].append(identity(current))

    # This is a deliberately bounded extraction of one known generated block,
    # not a general CMake parser or a claim to full dependency discovery.
    install_path = BUILD / "source/creator/cmake_install.cmake"
    install_text = install_path.read_text()
    blocks = list(re.finditer(r'  file\(INSTALL DESTINATION "\$\{CMAKE_INSTALL_PREFIX\}/lib" TYPE FILE MESSAGE_LAZY FILES\n(.*?)\n    \)', install_text, re.S))
    assert len(blocks) == 1, "expected exactly one configured shared-library block"
    block = blocks[0]
    (OUTPUT / "original-generated-library-install.cmake.txt").write_text(block.group(0) + "\n")
    report["generated_install_script"] = identity(install_path)
    report["original_generated_block"] = identity(OUTPUT / "original-generated-library-install.cmake.txt")
    paths = []
    for line in block.group(1).splitlines():
        match = re.fullmatch(r'    "([^"$;\\]+)"', line)
        assert match is not None, "unexpected generated path syntax"
        path = Path(match.group(1))
        path.relative_to(LIBRARIES)
        paths.append(path)
    assert len(set(paths)) == len(paths)

    raw_tree = git("ls-tree", "-rz", LIBRARY_COMMIT)
    (OUTPUT / "native-library-git-tree.bin").write_bytes(raw_tree)
    tree = {}
    for entry in raw_tree.split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, blob = metadata.decode().split()
            tree[name.decode()] = {"mode": mode, "type": kind, "blob": blob}
    report["native_library_git_tree"] = identity(OUTPUT / "native-library-git-tree.bin")
    selected = [path for path in paths if path.relative_to(LIBRARIES).as_posix() in tree]
    excluded = [path for path in paths if path not in selected]
    assert len({path.name for path in selected}) == len(selected), "destination basename collision"
    blobs = sorted({tree[path.relative_to(LIBRARIES).as_posix()]["blob"] for path in selected})
    batch = git("cat-file", "--batch", input=("\n".join(blobs) + "\n").encode())
    originals = {}
    position = 0
    for expected in blobs:
        end = batch.index(b"\n", position)
        blob, kind, size_text = batch[position:end].decode().split()
        assert blob == expected and kind == "blob"
        size = int(size_text)
        position = end + 1
        originals[blob] = batch[position:position + size]
        assert len(originals[blob]) == size and batch[position + size:position + size + 1] == b"\n"
        assert hashlib.sha1(b"blob " + str(size).encode() + b"\0" + originals[blob]).hexdigest() == blob
        position += size + 1
    assert position == len(batch)

    entries = []
    regular_bytes = 0
    for path in selected:
        relative = path.relative_to(LIBRARIES).as_posix()
        metadata = tree[relative]
        original = originals[metadata["blob"]]
        entry = {"source": str(path), "library_relative_path": relative,
                 "destination_name": path.name, "git": metadata}
        if metadata["mode"] == "120000":
            assert path.is_symlink() and os.fsencode(os.readlink(path)) == original
            target = os.readlink(path)
            assert not Path(target).is_absolute() and Path(target).name == target
            assert target in {item.name for item in selected}, "symlink target outside staged selection"
            entry.update(kind="symlink", target=target, bytes=len(original), sha256=hashlib.sha256(original).hexdigest())
        else:
            assert metadata["mode"] in {"100644", "100755"} and path.is_file() and not path.is_symlink()
            pointer = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n", original)
            actual = identity(path)
            if pointer:
                assert actual["sha256"] == pointer[1].decode() and actual["bytes"] == int(pointer[2])
                entry["original_lfs_pointer"] = original.decode()
            else:
                assert path.read_bytes() == original
            entry.update(kind="file", bytes=actual["bytes"], sha256=actual["sha256"])
            regular_bytes += actual["bytes"]
        entries.append(entry)
    report.update(generated_entry_count=len(paths), selected_tracked_entries=len(entries),
                  excluded_untracked_entries=[{"source": str(path), "reason": "not in pinned native-library Git tree", "identity": identity(path)} for path in excluded],
                  regular_file_count=sum(item["kind"] == "file" for item in entries),
                  symlink_count=sum(item["kind"] == "symlink" for item in entries),
                  regular_file_bytes=regular_bytes)
    assert report["initial_free_disk_bytes"] - regular_bytes >= 4 * 1024**3, "disk reserve would be exceeded"
    report["verified_inputs"] = write("verified-inputs.json", entries)
    report["status"] = "verified_before_install"
    write("preflight.json", report)

    # Use the same CMake file(INSTALL) operation and configured destination,
    # selecting only files actually tracked by the pinned upstream library commit.
    stage_path = OUTPUT / "install-verified-runtime-libraries.cmake"
    stage_path.write_text('file(INSTALL DESTINATION "' + str(DESTINATION) + '" TYPE FILE MESSAGE_LAZY FILES\n' +
                          "".join('  "' + str(path) + '"\n' for path in selected) + ')\n')
    command = [str(WORKSPACE / "runtime/browser-python/bin/cmake"), "-P", str(stage_path)]
    environment = dict(os.environ)
    environment.update(configuration["environment_overrides"])
    stage = {"argv": command, "cwd": str(REPO), "environment_overrides": configuration["environment_overrides"],
             "started_utc": NOW(), "timeout_seconds": 180, "script": identity(stage_path)}
    start = time.monotonic()
    with (OUTPUT / "install.stdout.txt").open("wb") as stdout, (OUTPUT / "install.stderr.txt").open("wb") as stderr:
        try:
            result = subprocess.run(command, cwd=REPO, env=environment, stdout=stdout, stderr=stderr, timeout=180)
            stage.update(returncode=result.returncode, timed_out=False)
        except subprocess.TimeoutExpired:
            stage.update(returncode=None, timed_out=True)
    stage.update(finished_utc=NOW(), elapsed_seconds=time.monotonic() - start,
                 stdout=identity(OUTPUT / "install.stdout.txt"), stderr=identity(OUTPUT / "install.stderr.txt"))
    report["stage"] = stage
    assert stage["returncode"] == 0 and not stage["timed_out"], "install did not complete successfully"
    assert sorted(path.name for path in DESTINATION.iterdir()) == sorted(item["destination_name"] for item in entries)
    for entry in entries:
        path = DESTINATION / entry["destination_name"]
        if entry["kind"] == "symlink":
            assert path.is_symlink() and os.readlink(path) == entry["target"]
            assert path.resolve().is_relative_to(DESTINATION) and path.is_file()
        else:
            actual = identity(path)
            assert not path.is_symlink() and actual["sha256"] == entry["sha256"] and actual["bytes"] == entry["bytes"]
    report["verified_destination"] = write("verified-destination.json", entries)
    report["cache_after"] = identity(BUILD / "CMakeCache.txt")
    report["binary_after"] = identity(BUILD / "bin/tests/cycles_test")
    assert report["cache_after"] == report["cache_before"]
    assert report["binary_after"] == report["binary_before"]
    report.update(status="verified_staged", final_free_disk_bytes=shutil.disk_usage(WORKSPACE).free)
except BaseException as error:
    report.update(status="failed", error_type=type(error).__name__, error=str(error))
    raise
finally:
    report["finished_utc"] = NOW()
    write("report.json", report)
    print(json.dumps({key: report.get(key) for key in ("status", "selected_tracked_entries", "regular_file_count", "symlink_count", "regular_file_bytes", "error")}))
