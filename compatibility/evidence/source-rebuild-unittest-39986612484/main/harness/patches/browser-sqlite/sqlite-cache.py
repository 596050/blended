#!/usr/bin/env python3
"""Validate local SQLite dependency caches against real input and output bytes."""
import hashlib
import json
import os
from pathlib import Path
import sys


def identity(path, root):
    if not path.is_relative_to(root):
        raise ValueError("cache file escapes the dependency root")
    compiler_link = path == root / "tools/emsdk/upstream/bin/clang" and path.is_symlink()
    target = path.resolve() if compiler_link else path
    if compiler_link and not target.is_relative_to(root / "tools/emsdk/upstream/bin"):
        raise ValueError("compiler entrypoint escapes the selected SDK")
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent == path and compiler_link:
            continue
        if parent.is_symlink():
            raise ValueError("cache input or output traverses a symlink: " + str(path))
    if target.is_symlink() or not target.is_file():
        raise ValueError("required regular cache file is absent: " + str(path))
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    result = {"path": str(path.relative_to(root)), "bytes": target.stat().st_size,
              "sha256": digest.hexdigest()}
    if compiler_link:
        result.update(symlink_target=os.readlink(path), resolved_path=str(target.relative_to(root)))
    return result


def snapshot(root, target):
    if target not in ("sqlite", "python"):
        raise ValueError("unknown SQLite cache target")
    lock = root / "scripts/deps/sqlite-patchset.json"
    lock_identity = identity(lock, root)
    selected = os.environ.get("BLENDED_SQLITE_PATCHSET_SHA256")
    if selected and lock_identity["sha256"] != selected:
        raise ValueError("selected SQLite patchset differs from prepared recipe")
    manifest = json.loads(lock.read_text())
    for entry in manifest["install_files"]:
        actual = identity(root / entry["destination"], root)
        if actual["sha256"] != entry["sha256"] or actual["bytes"] != entry["bytes"]:
            raise ValueError("prepared recipe differs from its patchset pin: " + entry["destination"])
    inputs = ["scripts/deps/sqlite-patchset.json", "scripts/deps/sqlite.sh", "scripts/deps/sqlite-cache.py",
              "tools/emsdk/upstream/emscripten/emcc", "tools/emsdk/upstream/bin/clang",
              "build-deps/_cache/" + manifest["sqlite"]["archive"]]
    outputs = ["lib/wasm/lib/libsqlite3.a", "lib/wasm/include/sqlite3.h", "lib/wasm/include/sqlite3ext.h"]
    if target == "python":
        inputs += outputs + ["scripts/deps/python.sh", "build-deps/_cache/" + manifest["python"]["archive"]]
        outputs = ["lib/wasm/lib/libpython3.13.a", "lib/wasm/include/python3.13/Python.h",
                   "lib/wasm/include/python3.13/pyconfig.h", "lib/wasm/lib/python3.13/sqlite3/__init__.py",
                   "lib/wasm/lib/python3.13/sqlite3/dbapi2.py", "lib/wasm/lib/python3.13/sqlite3/dump.py"]
    records = {"schema": 1, "target": target, "manifest_sha256": lock_identity["sha256"],
               "inputs": [identity(root / path, root) for path in inputs],
               "outputs": [identity(root / path, root) for path in outputs],
               "environment": {key: os.environ.get(key) for key in ("EM_CACHE", "EMCC_CFLAGS")},
               "browser_tests_executed": False, "full_feature_parity": False}
    if target == "python":
        expected = manifest["patches"][0]
        actual = next(entry for entry in records["inputs"] if entry["path"] == expected["destination"])
        if actual["sha256"] != expected["after_sha256"] or actual["bytes"] != expected["after_bytes"]:
            raise ValueError("CPython recipe differs from its selected patched bytes")
    for key, archive in (("sqlite", manifest["sqlite"]), ("python", manifest["python"])):
        if target == "sqlite" and key == "python":
            continue
        observed = next(entry for entry in records["inputs"] if entry["path"] == "build-deps/_cache/" + archive["archive"])
        if observed["sha256"] != archive["sha256"] or observed["bytes"] != archive["bytes"]:
            raise ValueError("source archive differs from selected pin: " + key)
    return records


def main(argv):
    if len(argv) != 3 or argv[0] not in ("verify", "record"):
        raise ValueError("usage: sqlite-cache.py verify|record sqlite|python PORT_ROOT")
    action, target, root_text = argv
    root = Path(root_text).resolve()
    path = root / ("lib/wasm/share/blended/" + target + "-sqlite-cache.json")
    try:
        current = snapshot(root, target)
        if action == "verify":
            if path.is_symlink() or json.loads(path.read_text()) != current:
                raise ValueError("cache input/output receipt differs")
        else:
            if path.is_symlink():
                raise ValueError("refuse cache receipt symlink")
            for parent in path.parents:
                if parent == root:
                    break
                if parent.is_symlink():
                    raise ValueError("cache receipt traverses a symlink")
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            if temporary.exists() or temporary.is_symlink():
                raise ValueError("cache receipt temporary path already exists")
            temporary.write_text(json.dumps(current, indent=2) + "\n")
            temporary.replace(path)
    except (OSError, ValueError, StopIteration, KeyError) as error:
        print("SQLite cache " + action + ": " + str(error), file=sys.stderr)
        return 1
    print("SQLite cache " + action + ": verified " + target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
