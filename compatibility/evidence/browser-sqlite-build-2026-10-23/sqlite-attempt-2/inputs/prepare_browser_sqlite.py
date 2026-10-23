#!/usr/bin/env python3
"""Prepare an explicitly selected, byte-bound SQLite/CPython dependency patchset.

This helper does not download, compile, execute tests, or modify Blender sources.
The enclosing source-build driver verifies the port/source Git commits and runs
the recipes. All preparation inputs and outputs are bound to exact file bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


INSTALL_DESTINATIONS = {"scripts/deps/sqlite.sh", "scripts/deps/sqlite-cache.py"}
PYTHON_DESTINATION = "scripts/deps/python.sh"
LOCK_DESTINATION = "scripts/deps/sqlite-patchset.json"
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)\n$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(label + " must be an exact lowercase SHA-256")
    return value


def _safe_path(root: Path, name: object) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid patchset path")
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("patchset path escapes its selected root")
    path = root.joinpath(*relative.parts)
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("patchset path traverses a symlink: " + str(path))
    return path


def _read_bound(root: Path, entry: dict, key: str = "file") -> tuple[Path, bytes]:
    path = _safe_path(root, entry[key])
    if not path.is_file():
        raise ValueError("patchset input is not a regular file: " + str(path))
    data = path.read_bytes()
    if type(entry.get("bytes")) is not int or entry["bytes"] != len(data):
        raise ValueError("patchset input length mismatch: " + str(path))
    if _digest(entry.get("sha256"), "patchset input hash") != _sha256(data):
        raise ValueError("patchset input hash mismatch: " + str(path))
    return path, data


def load_patchset(manifest_path: str | Path, expected_sha256: str) -> dict:
    """Validate a selected manifest and every local patch/recipe input.

    The returned dictionary is JSON serializable. Its manifest SHA must come
    from the caller's reviewed build configuration, not from this manifest.
    """
    path = Path(manifest_path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("SQLite manifest must be a regular file")
    path = path.resolve()
    data = path.read_bytes()
    if _sha256(data) != _digest(expected_sha256, "selected manifest hash"):
        raise ValueError("SQLite manifest hash mismatch")
    document = json.loads(data)
    if not isinstance(document, dict) or document.get("schema") != 1:
        raise ValueError("unsupported SQLite patchset schema")
    copies = document.get("install_files")
    patches = document.get("patches")
    if not isinstance(copies, list) or len(copies) != 2:
        raise ValueError("SQLite patchset must supply both dependency helpers")
    if {item.get("destination") for item in copies} != INSTALL_DESTINATIONS:
        raise ValueError("SQLite patchset has unapproved install destinations")
    if not isinstance(patches, list) or len(patches) != 1 or patches[0].get("destination") != PYTHON_DESTINATION:
        raise ValueError("SQLite patchset must patch only the CPython dependency recipe")
    inputs = []
    for entry in copies + patches:
        local, content = _read_bound(path.parent, entry)
        inputs.append({"file": entry["file"], "bytes": len(content), "sha256": _sha256(content)})
        _safe_path(Path("/selected-port"), entry["destination"])
    for side in ("before", "after"):
        _digest(patches[0].get(side + "_sha256"), "CPython " + side + " hash")
        if type(patches[0].get(side + "_bytes")) is not int or patches[0][side + "_bytes"] < 1:
            raise ValueError("invalid CPython recipe byte bound")
    for dependency in ("sqlite", "python"):
        archive = document.get(dependency)
        if not isinstance(archive, dict):
            raise ValueError("missing dependency source pin: " + dependency)
        _safe_path(Path("/selected-cache"), archive.get("archive"))
        if "/" in archive["archive"] or type(archive.get("bytes")) is not int or archive["bytes"] < 1:
            raise ValueError("invalid dependency source archive bound")
        _digest(archive.get("sha256"), dependency + " source archive hash")
    return {"manifest_path": str(path), "manifest_sha256": expected_sha256,
            "manifest_bytes": len(data), "manifest": document, "inputs": inputs}


def apply_exact_patch(original: bytes, patch: bytes, destination: str) -> bytes:
    """Apply one ordinary unified diff, with exact positions and zero fuzz."""
    lines = patch.decode("utf-8").splitlines(keepends=True)
    if lines[:2] != ["--- a/" + destination + "\n", "+++ b/" + destination + "\n"]:
        raise ValueError("patch headers do not identify the approved file")
    source = original.decode("utf-8").splitlines(keepends=True)
    output = []
    source_index = 0
    cursor = 2
    hunks = 0
    while cursor < len(lines):
        match = HUNK.fullmatch(lines[cursor])
        if match is None:
            raise ValueError("unsupported or malformed patch hunk")
        old_start, old_count, new_start, new_count = (int(value) if value is not None else 1 for value in match.groups())
        old_index = old_start - 1 if old_count else old_start
        new_index = new_start - 1 if new_count else new_start
        if old_index < source_index or old_index > len(source):
            raise ValueError("patch hunk source position is inconsistent")
        output.extend(source[source_index:old_index])
        source_index = old_index
        if len(output) != new_index:
            raise ValueError("patch hunk output position is inconsistent")
        removed = added = 0
        cursor += 1
        while cursor < len(lines) and not lines[cursor].startswith("@@"):
            line = lines[cursor]
            if not line or line[0] not in (" ", "+", "-"):
                raise ValueError("unsupported unified diff record")
            if line[0] in (" ", "-"):
                if source_index >= len(source) or source[source_index] != line[1:]:
                    raise ValueError("patch context differs from the pinned source")
                source_index += 1
                removed += 1
            if line[0] in (" ", "+"):
                output.append(line[1:])
                added += 1
            cursor += 1
        if (removed, added) != (old_count, new_count):
            raise ValueError("patch hunk line counts are inconsistent")
        hunks += 1
    if not hunks:
        raise ValueError("patch does not contain a hunk")
    output.extend(source[source_index:])
    return "".join(output).encode("utf-8")


def _atomic_write(path: Path, content: bytes, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".sqlite-tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ValueError("refuse existing preparation temporary path: " + str(temporary))
    with temporary.open("xb") as stream:
        stream.write(content)
    temporary.chmod(0o755 if executable else 0o644)
    temporary.replace(path)


def apply_patchset(port_root: str | Path, manifest_path: str | Path, expected_sha256: str,
                   receipt_path: str | Path | None = None) -> dict:
    """Prepare recipes atomically after validating all sources and destinations.

    Call before taking dependency recipe identities, then insert ``sqlite``
    immediately before ``python`` in the build order. Export the returned
    environment marker for every affected dependency invocation. Reapplication
    accepts only the exact already-prepared outputs, never arbitrary recipes.
    """
    prepared = load_patchset(manifest_path, expected_sha256)
    root = Path(port_root).resolve()
    if not root.is_dir():
        raise ValueError("port root must already exist")
    manifest = prepared["manifest"]
    source_root = Path(prepared["manifest_path"]).parent
    patch_entry = manifest["patches"][0]
    target = _safe_path(root, PYTHON_DESTINATION)
    if not target.is_file():
        raise ValueError("original CPython recipe is absent")
    before = target.read_bytes()
    observed = (_sha256(before), len(before))
    pristine = (patch_entry["before_sha256"], patch_entry["before_bytes"])
    final = (patch_entry["after_sha256"], patch_entry["after_bytes"])
    _, patch_bytes = _read_bound(source_root, patch_entry)
    if observed == pristine:
        after = apply_exact_patch(before, patch_bytes, PYTHON_DESTINATION)
        if (_sha256(after), len(after)) != final:
            raise ValueError("CPython patch output differs from its declared exact bytes")
    elif observed == final:
        after = before
    else:
        raise ValueError("CPython recipe is neither the pinned original nor the exact patched result")
    writes = [(target, after, True)]
    for entry in manifest["install_files"]:
        _, content = _read_bound(source_root, entry)
        destination = _safe_path(root, entry["destination"])
        if destination.exists() and (not destination.is_file() or destination.read_bytes() != content):
            raise ValueError("existing dependency helper conflicts with selected patchset: " + str(destination))
        writes.append((destination, content, True))
    lock = _safe_path(root, LOCK_DESTINATION)
    lock_data = Path(prepared["manifest_path"]).read_bytes()
    if lock.exists() and (not lock.is_file() or lock.read_bytes() != lock_data):
        raise ValueError("existing SQLite patchset lock conflicts with selected manifest")
    writes.append((lock, lock_data, False))
    # Reject conflicts for every destination before changing any prepared input.
    for destination, _, _ in writes:
        temporary = destination.with_name(destination.name + ".sqlite-tmp")
        if temporary.exists() or temporary.is_symlink():
            raise ValueError("preparation temporary path already exists: " + str(temporary))
    outputs = []
    for destination, content, executable in writes:
        if not destination.exists() or destination.read_bytes() != content:
            _atomic_write(destination, content, executable=executable)
        outputs.append({"path": destination.relative_to(root).as_posix(), "bytes": len(content), "sha256": _sha256(content)})
    receipt = {"schema": 1, "patchset_id": manifest.get("id"),
               "manifest": {"path": prepared["manifest_path"], "bytes": prepared["manifest_bytes"], "sha256": expected_sha256},
               "inputs": prepared["inputs"], "outputs": outputs,
               "original_python_recipe": {"bytes": pristine[1], "sha256": pristine[0]},
               "dependency_insertion": {"name": "sqlite", "before": "python"},
               "environment": {"BLENDED_SQLITE_PATCHSET_SHA256": expected_sha256},
               "requires_enclosing_driver_source_commit_verification": True,
               "source_tests_modified": False, "browser_tests_executed": False,
               "full_feature_parity": False}
    if receipt_path is not None:
        path = Path(receipt_path)
        content = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
        if path.is_symlink() or (path.exists() and path.read_bytes() != content):
            raise ValueError("refuse replacing a different SQLite preparation receipt")
        if not path.exists():
            _atomic_write(path, content)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    result = apply_patchset(args.port_root, args.manifest, args.manifest_sha256, args.receipt)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
