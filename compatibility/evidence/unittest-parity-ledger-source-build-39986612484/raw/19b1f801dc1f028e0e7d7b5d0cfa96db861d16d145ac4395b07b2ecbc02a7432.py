#!/usr/bin/env python3
"""Verify restored dependency bytes before reusing one pinned public build cache.

This verifies prior regular-file identities and an independently sourced alias
contract. It does not recompile dependencies or establish Blender test parity.
Changed SQLite and codec recipes still rebuild.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath


MANIFEST_SHA256 = "cfad6076a3160b1ded9f742a7e046beb911a1f720c2700f6e9480d181974c812"
CACHE_KEY = "blender-source-ubuntu24-x64-ebd6a49b6f17d26d0800c172eb40348041eb5fb37f5c7d4c67e5857f6dc8abd6-39841653080"
ALIAS_CONTRACT = (Path(__file__).resolve().parents[1] / "compatibility/build-caches"
                  / "source-39841653080-alias-contract/contract.json")
ALIAS_CONTRACT_SHA256 = "571377bb80f7d92e5a3d37db8a2b7b82448f8d5859e4cafb91b188904de73afb"


def identity(path):
    with path.open("rb") as stream:
        value = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": value}


def relative_path(name):
    if (not isinstance(name, str) or not name or "\\" in name
            or PurePosixPath(name).is_absolute()
            or any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError("invalid relative cache path")
    return PurePosixPath(name)


def load_alias_contract(path, expected_sha256):
    """Verify the fixed derivation receipt and each preserved primary source."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("alias contract must be a regular local file")
    observed = identity(path)
    if observed["sha256"] != expected_sha256:
        raise ValueError("alias contract differs from its independently selected digest")
    record = json.loads(path.read_text())
    if (record.get("schema") != 1
            or record.get("kind") != "upstream-derived-dependency-cache-alias-contract"
            or record.get("cache_key") != CACHE_KEY):
        raise ValueError("unrecognized alias contract")
    sources = []
    for row in record["sources"]:
        source = path.parent
        for part in relative_path(row["path"]).parts:
            source /= part
            if source.is_symlink():
                raise ValueError("alias source path crosses a symlink")
        if not source.is_file() or identity(source) != {key: row[key] for key in ("bytes", "sha256")}:
            raise ValueError("alias derivation source differs from its pinned identity: " + row["path"])
        sources.append({"path": row["path"], **identity(source)})
    aliases = {row["path"]: row for row in record["aliases"]}
    if not sources or not aliases or len(aliases) != len(record["aliases"]):
        raise ValueError("empty or duplicate alias contract inventory")
    return {"aliases": aliases, "receipt": {"path": str(path.resolve()), **observed},
            "scope": record["scope"], "sources": sources}


def verify(prefix, manifest, expected_sha256, *, aliases=None):
    prefix = Path(prefix)
    manifest = Path(manifest)
    if prefix.is_symlink() or not prefix.is_dir() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError("cache prefix and manifest must be real local paths")
    prefix = prefix.resolve()
    manifest_identity = identity(manifest)
    if manifest_identity["sha256"] != expected_sha256:
        raise ValueError("cache manifest differs from the selected original output receipt")
    expected = {}
    for line in manifest.read_text().splitlines():
        row = json.loads(line)
        name = row["path"]
        relative_path(name)
        if (name in expected or type(row.get("bytes")) is not int
                or row["bytes"] < 0 or not isinstance(row.get("sha256"), str)
                or len(row["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in row["sha256"])):
            raise ValueError("invalid or duplicate original cache record")
        expected[name] = {key: row[key] for key in ("bytes", "sha256")}
    if not expected:
        raise ValueError("empty dependency manifest cannot qualify a restored cache")
    aliases = {} if aliases is None else aliases
    for name, row in aliases.items():
        alias = relative_path(name)
        link = relative_path(row["link_text"])
        target = relative_path(row["target_path"])
        if (name in expected or row.get("path") != name
                or (alias.parent / link) != target
                or expected.get(target.as_posix()) != row["target_identity"]):
            raise ValueError("alias contract target lacks its exact original file identity: " + name)
    actual, links = set(), []
    for file in sorted(prefix.rglob("*")):
        if file.is_symlink():
            name = file.relative_to(prefix).as_posix()
            row = aliases.get(name)
            if row is None:
                raise ValueError("unrecognized cache alias: " + name)
            if os.readlink(file) != row["link_text"]:
                raise ValueError("cache alias text differs from its source-derived contract: " + name)
            target = file.resolve(strict=True)
            if target != prefix / row["target_path"] or not target.is_file():
                raise ValueError("cache alias target differs from its source-derived contract: " + name)
            links.append({"path": name, "link_text": row["link_text"], "target": row["target_path"]})
        elif file.is_file():
            name = file.relative_to(prefix).as_posix()
            if name not in expected or identity(file) != expected[name]:
                raise ValueError("restored dependency bytes differ from the original cache: " + name)
            actual.add(name)
        elif not file.is_dir():
            raise ValueError("unsupported entry in restored dependency cache")
    if actual != set(expected):
        raise ValueError("restored dependency cache is missing original files: " +
                         ", ".join(sorted(set(expected) - actual)[:10]))
    if {row["path"] for row in links} != set(aliases):
        raise ValueError("restored dependency cache is missing required source-derived aliases")
    return {"manifest": {"path": str(manifest.resolve()), **manifest_identity},
            "verified_files": len(actual), "verified_bytes": sum(row["bytes"] for row in expected.values()),
            "verified_aliases": len(links), "links": links,
            "link_scope": "Exact source-derived alias contract; historical link metadata was not inventoried."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--cache-key", default=CACHE_KEY)
    args = parser.parse_args(argv)
    if args.receipt.exists() or args.receipt.is_symlink():
        parser.error("choose a new receipt path")
    report = {"schema": 1, "kind": "verified-original-dependency-cache-reuse",
              "cache_key": args.cache_key, "expected_cache_key": CACHE_KEY, "status": "running",
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "blender_tests_executed": 0, "full_feature_parity": False,
              "scope": "Prior regular-file output identity plus independently source-derived expected aliases. Changed dependency recipes rebuild separately."}
    try:
        if args.cache_key != CACHE_KEY:
            raise ValueError("restored cache key differs from the explicitly selected original cache")
        contract = load_alias_contract(ALIAS_CONTRACT, ALIAS_CONTRACT_SHA256)
        report["alias_contract"] = {key: value for key, value in contract.items() if key != "aliases"}
        report.update(verify(args.prefix, args.manifest, MANIFEST_SHA256, aliases=contract["aliases"]), status="verified")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        report.update(status="failed", reason=str(error))
        return 1
    finally:
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


if __name__ == "__main__":
    raise SystemExit(main())
