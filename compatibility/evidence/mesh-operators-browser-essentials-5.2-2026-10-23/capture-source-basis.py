#!/usr/bin/env python3
"""Retain exact original fill and comparison source for bounded failure triage."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARCHIVE = REPO.parent / "runtime/upstream-5.2.tar.gz"
ARCHIVE_SHA = "de0fdadf28015805370d1815facaf9139fbb1e161d8c540d1765484beabb3a99"
SOURCE_PIN = "fbe6228777e7d9afefcd61a413844e790ae75db7"
NEEDED = {
    "source/blender/editors/mesh/editmesh_tools.cc": ["edbm_fill_exec", "void MESH_OT_fill", "triangle_fill edges=%he use_beauty=%b"],
    "source/blender/bmesh/operators/bmo_triangulate.cc": ["void bmo_triangle_fill_exec", "qsort(nors", "BLI_scanfill_calc_ex", "if (use_beauty)"],
    "source/blender/blenlib/intern/scanfill.cc": ["BLI_scanfill_calc_ex", "qsort(", "cross_tri_v2", "float"],
    "source/blender/blenlib/intern/sort_utils.cc": ["BLI_sortutil_cmp_float_reverse"],
    "source/blender/blenkernel/intern/geometry_compare.cc": ["The edge topology is different", "EdgeTopology", "compare_meshes"],
}


def identity(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


archive_id = identity(ARCHIVE)
if archive_id["sha256"] != ARCHIVE_SHA:
    raise ValueError("source archive differs from the frozen original 5.2 source")
files = {}
with tarfile.open(ARCHIVE, "r:gz") as archive:
    for member in archive:
        if not member.isfile() or "/" not in member.name:
            continue
        relative = member.name.split("/", 1)[1]
        if relative not in NEEDED:
            continue
        if relative in files:
            raise ValueError("duplicate original source member")
        path = HERE / "source-basis" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(archive.extractfile(member).read())
        lines = path.read_text().splitlines()
        files[relative] = {**identity(path), "upstream_path": relative, "archive_member": member.name,
                           "official_source_url": "https://github.com/blender/blender/blob/" + SOURCE_PIN + "/" + relative,
                           "marker_lines": {marker: [i for i, line in enumerate(lines, 1) if marker in line]
                                            for marker in NEEDED[relative]}}
if set(files) != set(NEEDED):
    raise ValueError("original source closure was not found")
report = {"schema": 1, "kind": "exact-original-source-basis-for-operators-triage",
          "created_utc": datetime.now(timezone.utc).isoformat(), "source_commit": SOURCE_PIN,
          "source_archive": archive_id, "capture_script": identity(Path(__file__).resolve()),
          "files": list(files.values()), "source_files_modified": False,
          "code_executed": False, "root_cause_reproduced": False,
          "scope": "Original call-path and comparator source only; static inspection does not identify which runtime value or decision diverged."}
with (HERE / "source-basis.json").open("x") as stream:
    stream.write(json.dumps(report, indent=2) + "\n")
print(json.dumps(identity(HERE / "source-basis.json")))
