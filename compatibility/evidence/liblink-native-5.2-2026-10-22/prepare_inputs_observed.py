#!/usr/bin/env python3
"""Materialize only exact upstream source and the three liblink fixture objects."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2] / "research_ports/native-gessa"
PIN = "fbe6228777e7d9afefcd61a413844e790ae75db7"
SOURCES = (
    "tests/python/bl_blendfile_liblink.py",
    "tests/python/bl_blendfile_library_overrides.py",
    "tests/python/bl_blendfile_relationships.py",
    "tests/python/bl_blendfile_utils.py",
    "tests/python/CMakeLists.txt",
)
ASSETS = (
    "tests/files/imbuf_io/reference/jpeg-rgb-90__from__rgba08.jpg",
    "tests/files/libraries_and_linking/libraries/collection_assets.blend",
    "tests/files/libraries_and_linking/libraries/animated_assets.blend",
)
LFS_BATCH_URL = "https://projects.blender.org/blender/blender.git/info/lfs/objects/batch"


def original(path):
    return subprocess.check_output(["git", "show", PIN + ":" + path], cwd=REPO)


def main():
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip() != PIN:
        raise RuntimeError("source checkout has a different pin")
    report = {"schema": 1, "upstream": {"repository": "blender/blender", "commit": PIN},
              "sources": [], "assets": [], "selected_suite": "tests/python/bl_blendfile_liblink.py"}
    for name in SOURCES:
        raw = original(name)
        dest = ROOT / "sources" / Path(name).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        row = {"upstream_path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
               "git_blob": subprocess.check_output(["git", "rev-parse", PIN + ":" + name], cwd=REPO, text=True).strip(),
               "url": f"https://raw.githubusercontent.com/blender/blender/{PIN}/{name}",
               "local_path": str(dest.relative_to(ROOT))}
        if name.endswith(".py"):
            tree = ast.parse(raw)
            classes = {node.name: [member.name for member in node.body if isinstance(member, ast.FunctionDef)
                                  and member.name.startswith("test_")]
                       for node in tree.body if isinstance(node, ast.ClassDef)}
            order = next(([value.id for value in node.value.elts] for node in tree.body
                          if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                          target.id == "TESTS" for target in node.targets)), [])
            row["class_order"] = order
            row["case_ids"] = [cls + "." + method for cls in order for method in sorted(classes[cls])]
            row["expected_cases"] = len(row["case_ids"])
        report["sources"].append(row)
    asset_rows = []
    for name in ASSETS:
        pointer = original(name)
        fields = dict(line.split(" ", 1) for line in pointer.decode("ascii").splitlines())
        if fields.get("version") != "https://git-lfs.github.com/spec/v1":
            raise RuntimeError("asset is not the expected LFS pointer")
        size, sha = int(fields["size"]), fields["oid"].removeprefix("sha256:")
        asset_rows.append((name, pointer, size, sha))
    body = {"operation": "download", "transfers": ["basic"],
            "objects": [{"oid": sha, "size": size} for _, _, size, sha in asset_rows]}
    request = urllib.request.Request(LFS_BATCH_URL, data=json.dumps(body).encode(), method="POST",
                                     headers={"Accept": "application/vnd.git-lfs+json",
                                              "Content-Type": "application/vnd.git-lfs+json"})
    with urllib.request.urlopen(request, timeout=40) as response:
        batch = json.load(response)
    actions = {row["oid"]: row["actions"]["download"] for row in batch["objects"]}
    for name, pointer, size, sha in asset_rows:
        action = actions[sha]
        url = action["href"]
        dest = ROOT / "fixtures" / Path(name).relative_to("tests/files")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file():
            data = dest.read_bytes()
        else:
            request = urllib.request.Request(url, headers=action.get("header", {}))
            with urllib.request.urlopen(request, timeout=40) as response:
                data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha:
            raise RuntimeError("fixture size/hash differs from pinned LFS pointer: " + name)
        dest.write_bytes(data)
        parsed_url = urllib.parse.urlsplit(url)
        report["assets"].append({"upstream_path": name, "bytes": size, "sha256": sha,
                                 "lfs_batch_url": LFS_BATCH_URL,
                                 "download_url_without_query": urllib.parse.urlunsplit((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "")),
                                 "lfs_pointer_sha256": hashlib.sha256(pointer).hexdigest(),
                                 "git_blob": subprocess.check_output(["git", "rev-parse", PIN + ":" + name], cwd=REPO, text=True).strip(),
                                 "local_path": str(dest.relative_to(ROOT))})
    report["fixture_bytes"] = sum(row["bytes"] for row in report["assets"])
    (ROOT / "input-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"input_manifest": str(ROOT / "input-manifest.json"),
                      "fixture_count": len(report["assets"]), "fixture_bytes": report["fixture_bytes"],
                      "selected_cases": report["sources"][0]["expected_cases"]}))


if __name__ == "__main__":
    main()
