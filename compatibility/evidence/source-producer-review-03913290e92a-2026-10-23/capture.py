#!/usr/bin/env python3
"""Preserve and compare exact Git producer bytes; execute no Blender tests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
OLD = "f25e69ed72fed2d31d7d65e657fd6515da4bd792"
NEW = "03913290e92a98cd9c45fdecf679072587c4dbe7"
FILES = {
    ".github/workflows/browser-source-build.yml": (16666, "cf330f75ff2ea44c7cf9090950269033ca19de9b0c281e64a87caabfab29fcff"),
    "tools/run_unittest_browser_matrix.py": (12682, "7e9830db4f6bb378c8bf0d5ea36e13e0ac164c609633fe368026b8a75e10c0e3"),
    "tools/probe_browser_port.py": (75480, "bd975ec99e30c5d33496fc94a3d0f00837e181a5b5ea543431829fcbb71c1887"),
}


def record(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    if (OUTPUT / "review.json").exists() or (OUTPUT / "sources").exists():
        raise SystemExit("Refusing to overwrite an existing review or source snapshot")
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    for name, (size, digest) in FILES.items():
        before = git("show", OLD + ":" + name)
        after = git("show", NEW + ":" + name)
        assert record(after) == {"bytes": size, "sha256": digest}
        if name.endswith("probe_browser_port.py"):
            old_pin = b"b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708"
            new_pin = b"1c98842c68dc7706630ce31132cdab20649ea61b860dd05b88722dc1a79b0bcf"
            assert before.count(old_pin) == 1 and before.replace(old_pin, new_pin) == after
            comparison = "Exactly one codec-manifest digest replacement; all other bytes identical."
        else:
            assert before == after
            comparison = "All bytes identical."
        destination = OUTPUT / "sources" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(after)
        rows.append({"upstream_path": name, "old": record(before), "reviewed": record(after),
                     "saved_path": destination.relative_to(OUTPUT).as_posix(), "comparison": comparison})
    result = {
        "schema": 1, "kind": "exact-git-producer-source-review", "status": "verified",
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "previous_commit": OLD, "reviewed_commit": NEW,
        "reviewed_tree": git("rev-parse", NEW + "^{tree}").decode().strip(),
        "source_root": str(ROOT), "files": rows,
        "capture_script": {"path": "capture.py", **record(Path(__file__).read_bytes())},
        "tests_executed": 0, "full_feature_parity": False,
        "limitations": ["This review establishes exact producer source bytes and their diff only.",
                        "No completed workflow run, browser execution or original test outcome is claimed.",
                        "The workflow checkout and child cwd are source-derived, not OS-observed."],
    }
    with (OUTPUT / "review.json").open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "verified", "commit": NEW, "source_files": len(rows), "tests_executed": 0}))


if __name__ == "__main__":
    main()
