"""Hydrate and independently verify the exact product-target native library pin."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess


evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
workspace = repo.parent
library = workspace / "runtime/product-native-libs/linux_x64"
commit = "2b5fbb917a1bf7537cb25456fcb9064302d7e168"
source_commit = "94363991e7dcf39e2d70614aa002ab6f67764a5d"
inventory = evidence / "native-library-lfs-inventory.json"
output = evidence / "native-library-hydration.json"
if output.exists():
    raise RuntimeError("hydration evidence already exists; use a new immutable attempt")


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return {"bytes": path.stat().st_size, "sha256": hasher.hexdigest()}


environment = dict(os.environ)
environment.pop("GIT_LFS_SKIP_SMUDGE", None)
expected = json.loads(inventory.read_text())["files"]
record = {"schema": 1, "source_commit": source_commit, "library_commit": commit,
          "repository": "https://projects.blender.org/blender/lib-linux_x64.git",
          "input_inventory": {"path": inventory.name, **identity(inventory)},
          "started_utc": now(), "finished_utc": None, "status": "running", "stages": [],
          "verified_files": [], "tests_executed": 0, "runtime_enumeration_complete": False}


def save():
    output.write_text(json.dumps(record, indent=2) + "\n")


def run(label, command):
    path = evidence / ("native-library-hydration-" + label + ".log")
    if path.exists():
        raise RuntimeError("stage log already exists: " + str(path))
    stage = {"label": label, "command": command, "started_utc": now(), "returncode": None}
    record["stages"].append(stage)
    save()
    with path.open("wb") as stream:
        completed = subprocess.run(command, cwd=library, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    stage.update(returncode=completed.returncode, finished_utc=now(), log={"path": path.name, **identity(path)})
    save()
    if completed.returncode:
        raise RuntimeError("native library stage failed: " + label)
    return path.read_text()


try:
    observed = run("head", ["git", "rev-parse", "HEAD"]).strip()
    if observed != commit:
        raise RuntimeError("native library checkout differs from the source gitlink")
    live = json.loads(run("pointers", ["git", "lfs", "ls-files", "--json"]))["files"]
    keys = lambda rows: sorted((row["name"], row["oid_type"], row["oid"], row["size"]) for row in rows)
    if keys(live) != keys(expected):
        raise RuntimeError("live library pointer inventory differs from the retained exact-pin inventory")
    run("fetch", ["git", "-c", "lfs.concurrenttransfers=8", "lfs", "fetch", "origin", commit])
    run("checkout", ["git", "lfs", "checkout"])
    for row in expected:
        relative = PurePosixPath(row["name"])
        if relative.is_absolute() or ".." in relative.parts or row["oid_type"] != "sha256":
            raise RuntimeError("unsafe or unsupported LFS entry")
        path = library / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("required native library payload is missing: " + str(relative))
        observed = identity(path)
        if observed != {"bytes": row["size"], "sha256": row["oid"]}:
            raise RuntimeError("native library bytes differ from the exact LFS pointer: " + str(relative))
        record["verified_files"].append({"path": str(relative), **observed})
    unique = {row["oid"]: row["size"] for row in expected}
    record.update(status="verified", verified_file_count=len(expected),
                  verified_path_bytes=sum(row["size"] for row in expected),
                  verified_unique_object_count=len(unique), verified_unique_object_bytes=sum(unique.values()))
    run("git-status", ["git", "status", "--short"])
except Exception as error:
    record.update(status="failed", reason=str(error))
    raise
finally:
    record["finished_utc"] = now()
    save()
print(json.dumps({key: record[key] for key in ("status", "verified_file_count", "verified_path_bytes",
                  "verified_unique_object_count", "verified_unique_object_bytes", "tests_executed")}))
