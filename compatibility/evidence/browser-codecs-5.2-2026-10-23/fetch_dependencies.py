#!/usr/bin/env python3
"""Fetch the original Blender 5.2 codec archives and retain their identities."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent
PACKAGES = [
    ("webp", "1.6.0", "libwebp-1.6.0.tar.gz", "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0.tar.gz", "md5", "cceb6447180f961473b181c9ef38b630"),
    ("openjpeg", "2.5.3", "openjpeg-v2.5.3.tar.gz", "https://github.com/uclouvain/openjpeg/archive/v2.5.3.tar.gz", "sha256", "368fe0468228e767433c9ebdea82ad9d801a3ad1e4234421f352c8b06e7aa707"),
    ("aom", "3.13.1", "libaom-3.13.1.tar.gz", "https://storage.googleapis.com/aom-releases/libaom-3.13.1.tar.gz", "sha256", "19e45a5a7192d690565229983dad900e76b513a02306c12053fb9a262cbeca7d"),
    ("libheif", "1.20.2", "libheif-1.20.2.tar.gz", "https://github.com/strukturag/libheif/releases/download/v1.20.2/libheif-1.20.2.tar.gz", "sha256", "68ac9084243004e0ef3633f184eeae85d615fe7e4444373a0a21cebccae9d12a"),
    ("openimageio", "3.1.13.1", "OpenImageIO-3.1.13.1.tar.gz", "https://github.com/AcademySoftwareFoundation/OpenImageIO/archive/refs/tags/v3.1.13.1.tar.gz", "md5", "9f6f083900680b79ca4a136270103844"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True, type=Path)
    args = parser.parse_args()
    cache = args.cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)

    def one(spec):
        name, version, filename, url, algo, expected = spec
        destination = cache / filename
        row = {"name": name, "version": version, "url": url,
               "upstream_archive_hash": {"algorithm": algo, "value": expected},
               "started_at": datetime.now(timezone.utc).isoformat()}
        if not destination.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "blended-codec-source-audit"})
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = response.read()
            assert hashlib.new(algo, raw).hexdigest() == expected, name
            destination.write_bytes(raw)
        else:
            raw = destination.read_bytes()
        assert hashlib.new(algo, raw).hexdigest() == expected, name
        row.update(path=str(destination), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                   upstream_hash_verified=True, completed_at=datetime.now(timezone.utc).isoformat())
        selection = []
        with tarfile.open(destination) as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                relative = Path(*Path(member.name).parts[1:])
                path = relative.as_posix()
                selected = (path in ("CMakeLists.txt", "README.md", "README", "COPYING", "LICENSE", "PATENTS")
                            or path.startswith("cmake/") and path.endswith(".cmake")
                            or path.startswith("build/cmake/") and path.endswith(".cmake")
                            or name == "libheif" and path.startswith(("libheif/plugins/", "libheif/api/")) and path.endswith((".cc", ".h", ".cmake", "CMakeLists.txt"))
                            or name == "openimageio" and path.startswith(("src/heif.imageio/", "src/webp.imageio/", "src/jpeg2000.imageio/", "src/dpx.imageio/", "src/cmake/")) and path.endswith((".cpp", ".h", ".cmake", "CMakeLists.txt")))
                if not selected:
                    continue
                assert not relative.is_absolute() and ".." not in relative.parts
                assert member.size < 4 * 1024 * 1024
                data = archive.extractfile(member).read()
                local = ROOT / "dependency-sources" / name / relative
                local.parent.mkdir(parents=True, exist_ok=True)
                if local.exists():
                    assert local.read_bytes() == data
                else:
                    local.write_bytes(data)
                selection.append({"archive_path": member.name, "path": local.relative_to(ROOT).as_posix(),
                                  "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        row["selected_source_files"] = selection
        return row

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(one, PACKAGES))
    output = ROOT / "dependency-inputs.json"
    assert not output.exists()
    output.write_text(json.dumps({"schema": 1, "kind": "original-codec-dependency-archives", "archives": rows,
        "pin_source": "sources/blender/build_files/build_environment/cmake/versions.cmake",
        "new_sha256_observations_for_upstream_md5_archives": ["webp", "openimageio"],
        "blender_cases_executed": 0}, indent=2) + "\n")
    print(json.dumps([{key: row[key] for key in ("name", "bytes", "sha256")} for row in rows]))


if __name__ == "__main__":
    main()
