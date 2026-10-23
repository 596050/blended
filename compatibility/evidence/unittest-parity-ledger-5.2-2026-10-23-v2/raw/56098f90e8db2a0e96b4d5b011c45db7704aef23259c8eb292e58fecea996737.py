#!/usr/bin/env python3
"""Prepare exact original BLF and documentation resources for native rediscovery.

This creates new proposals and preserves prior failed evidence. Test scripts,
reference images, original comparator arguments, and tolerances are unchanged.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil

try:
    from .probe_blender_fixtures import LFS_BATCH_URL, prepare_fixture_payloads
    from .upstream_resources import prepare_resources, preserve_resources
    from .unittest_cohort import UPSTREAM_SHA, validate_manifest
except ImportError:
    from probe_blender_fixtures import LFS_BATCH_URL, prepare_fixture_payloads
    from upstream_resources import prepare_resources, preserve_resources
    from unittest_cohort import UPSTREAM_SHA, validate_manifest


def source_metadata(path, root):
    data = path.read_bytes()
    relative = path.relative_to(root).as_posix()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    row = {"upstream_path": relative, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
           "git_blob_sha1": blob, "upstream_url": "https://github.com/blender/blender/blob/" + UPSTREAM_SHA + "/" + relative}
    match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n", data)
    if match:
        row["lfs_pointer"] = {"text": data.decode(), "bytes": len(data), "sha256": row["sha256"], "git_blob_sha1": blob}
        row.update(sha256=match.group(1).decode(), bytes=int(match.group(2)))
        row["lfs_object"] = {"oid": "sha256:" + row["sha256"], "sha256": row["sha256"], "bytes": row["bytes"]}
        row["lfs_batch_url"] = LFS_BATCH_URL
    return row


def documentation_paths(root):
    directory = root / "doc/python_api"
    paths = {path for path in directory.rglob("*") if path.is_file() and "__pycache__" not in path.parts}
    tree = ast.parse((directory / "sphinx_doc_gen.py").read_bytes())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EXTRA_SOURCE_FILES" for t in node.targets):
            for item in node.value.elts:
                relative = ast.literal_eval(item.args[0])
                path = (directory / "rst" / relative).resolve()
                if not path.is_relative_to(root):
                    raise ValueError("documentation helper path escapes original source")
                paths.add(path)
    paths.add(root / "source/blender/bmesh/intern/bmesh_opdefines.cc")
    return sorted(paths)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--initial-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--idiff", type=Path, required=True)
    parser.add_argument("--python-executable", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.source_root.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    base = root / "tests/files/blenfont"
    font_paths = sorted((base / "noto_fonts").glob("*.otf"))
    all_fixture_paths = font_paths + sorted((base / "buffer_renders").glob("*.png")) + sorted((base / "vfont_renders").glob("*.png"))
    fixtures = []
    for path in all_fixture_paths:
        row = source_metadata(path, root)
        if "lfs_pointer" not in row:
            raise ValueError("original BLF resource is not a pinned LFS object")
        row["relative_path"] = path.relative_to(root / "tests/files").as_posix()
        fixtures.append(row)
    fixture_cache = args.cache / "fixtures"
    prepare_fixture_payloads(fixtures, UPSTREAM_SHA, fixture_cache,
                             local_root=fixture_cache if all((fixture_cache / row["relative_path"]).is_file() for row in fixtures) else None)
    resources = [source_metadata(path, root) for path in documentation_paths(root)]
    resource_cache = args.cache / "source"
    ordinary_cache = args.cache / "original-source"
    for row in resources:
        if "lfs_pointer" in row:
            continue
        source = root / row["upstream_path"]
        target = ordinary_cache / row["upstream_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for row in resources:
        local = resource_cache if (resource_cache / row["upstream_path"]).is_file() else (None if "lfs_pointer" in row else ordinary_cache)
        payloads = prepare_resources([row], UPSTREAM_SHA, args.cache / "staged", local_root=local)
        preserve_resources(payloads, resource_cache)
    def tool(environment, path):
        data = path.read_bytes()
        return {"environment": environment, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    prepared = []
    for name in ("script_pyapi_blf_buffer", "script_pyapi_blf_vfont", "script_pyapi_doc_gen"):
        path = args.initial_evidence / name / "discovery-proposal.json"
        value = json.loads(path.read_text())
        value["cohort_id"] += "-resources"
        row = value["suites"][0]
        if name == "script_pyapi_doc_gen":
            row["resource_files"] = resources
            value["execution"]["host_tools"] = [tool("PYTHON_BIN", args.python_executable)]
            value["resource_requirements"] = {"docutils": "0.22.4", "source": "doc/python_api/requirements.txt"}
        else:
            folder = "/buffer_renders/" if name.endswith("buffer") else "/vfont_renders/"
            row["fixture_files"] = [item for item in fixtures if "/noto_fonts/" in item["upstream_path"] or folder in item["upstream_path"]]
            value["execution"].update(fixture_mount="original-tests-files", host_tools=[tool("IDIFF_BIN", args.idiff)])
            value["resource_requirements"] = {"OpenImageIO": "3.1.13.0", "comparator": "original idiff executable and original script arguments"}
        validate_manifest(value, allow_discovery=True)
        destination = args.output / (name + ".json")
        with destination.open("x") as stream:
            stream.write(json.dumps(value, indent=2) + "\n")
        prepared.append({"ctest_name": name, "proposal": str(destination), "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                         "fixtures": len(row.get("fixture_files", [])), "resources": len(row.get("resource_files", []))})
    print(json.dumps({"prepared": prepared, "fixture_cache": str(fixture_cache), "source_resource_cache": str(resource_cache)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
