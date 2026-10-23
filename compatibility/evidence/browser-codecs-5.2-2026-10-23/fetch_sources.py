#!/usr/bin/env python3
"""Retrieve pinned primary codec/build sources and verify their Git blob IDs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
PORT = "0e02e84b2bc5d9b27a6dc6e275443292f781fbad"
BLENDER = "fbe6228777e7d9afefcd61a413844e790ae75db7"


def retrieve(url):
    req = urllib.request.Request(url, headers={"User-Agent": "blended-codec-source-audit"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def main():
    rows = []
    requested = []
    for name, repo, commit in (("port", "gessa-ai/blender-web", PORT), ("blender", "blender/blender", BLENDER)):
        tree_path = ROOT / (name + "-tree.json")
        url = f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1"
        if tree_path.exists():
            raw = tree_path.read_bytes()
        else:
            raw = retrieve(url)
            tree_path.write_bytes(raw)
        tree = json.loads(raw)
        assert tree["sha"] == commit and tree.get("truncated") is False
        index = {row["path"]: row for row in tree["tree"] if row["type"] == "blob"}
        if name == "port":
            selected = [path for path in index if path in ("patches/blender_web.cmake", "patches/platform_wasm.cmake", "patches/PREVIEW_SNAPSHOT.patch")
                        or path.startswith("scripts/") and path.count("/") == 1 and path.endswith(".sh")
                        or path.startswith("scripts/deps/") and path.endswith(".sh")]
        else:
            selected = [path for path in index if path in (
                "CMakeLists.txt", "tests/python/bl_imbuf_py_api.py", "build_files/cmake/Modules/FindWebP.cmake",
                "build_files/cmake/Modules/FindOpenJPEG.cmake", "build_files/cmake/platform/platform_unix.cmake",
                "source/blender/imbuf/CMakeLists.txt")
                or path.startswith("source/blender/imbuf/intern/") and ("/cineon/" in path or path.endswith((".cc", ".h", ".c", "CMakeLists.txt")))
                or path.startswith("build_files/build_environment/") and any(word in path.lower() for word in ("webp", "openjpeg", "heif", "aom", "avif", "dav1d"))
                or path in ("build_files/build_environment/cmake/versions.cmake", "build_files/build_environment/cmake/openimageio.cmake")]
        rows.append({"repository": repo, "commit": commit, "tree_url": url,
                     "tree_receipt": {"path": tree_path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
                     "requested_sources": len(selected)})
        for path in sorted(selected):
            requested.append((name, repo, commit, path, index[path]))

    def one(item):
        name, repo, commit, path, entry = item
        url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
        destination = ROOT / "sources" / name / path
        raw = destination.read_bytes() if destination.exists() else retrieve(url)
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        assert actual == entry["sha"] and len(raw) == entry["size"], path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(raw)
        return {"repository": repo, "commit": commit, "upstream_path": path, "url": url,
                "path": destination.relative_to(ROOT).as_posix(), "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(), "git_blob": actual}

    with ThreadPoolExecutor(max_workers=6) as pool:
        sources = list(pool.map(one, requested))
    report = {"schema": 1, "kind": "pinned-codec-source-review-inputs", "completed_at": datetime.now(timezone.utc).isoformat(),
              "repositories": rows, "sources": sources, "blender_cases_executed": 0, "full_feature_parity": False}
    output = ROOT / "source-inputs.json"
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"sources": len(sources), "bytes": sum(row["bytes"] for row in sources)}))


if __name__ == "__main__":
    main()
