#!/usr/bin/env python3
"""Bind the frozen original bevel transport to a distinct original operators invocation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "bmesh-bevel-browser-essentials-5.2-2026-10-23"


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_expected(name, digest):
    path = SOURCE / name
    measured = identity(path)
    if measured["sha256"] != digest:
        raise ValueError("the frozen reviewed bevel observer changed")
    return path.read_text(), measured


def write_new(name, text):
    path = HERE / name
    with path.open("x") as stream:
        stream.write(text)
    return identity(path)


source_ids = []
output_ids = []
edits = {}
for name, digest in (
    ("launcher-v2.js", "e35ca3b593406aa83b27e28197018ad12dfcb5ec278d13507aa69cc893dae84d"),
    ("launcher-v2.html", "b0372c0527cc61f78abb65906b14b0dd82be343a83b43091d5915747c46db6cf"),
    ("run-browser-v2.py", "0253d2d399fa6cc8aac5ccfed775e16427fa5663edd6667d8452324f96f9d487"),
    ("capture-process-v2.py", "344f7269004198d511f32ba15b3c3decfbddc71acb7131c662f356c8579a3fa3"),
):
    text, source_id = read_expected(name, digest)
    source_ids.append(source_id)
    replacements = []
    if name == "run-browser-v2.py":
        replacements.extend([
            ("bmesh-bevel-source-native-elevated-5.2-2026-10-23", "mesh-operators-source-native-5.2-2026-10-23"),
            ("bmesh-bevel-source-native-5.2-2026-10-23", "mesh-operators-source-native-5.2-2026-10-23"),
            ("54b9c3e3bfe5504dc151ed534dd7039fec0d85a15315ac61e0860002b5ee949d", "fff5cc16a4b72b4913b9c98ce25055eff66c8061417351d3f3c273a1915cb02e"),
            ("4e3a34d7bb949b6bd7e4c6a050ea4c62c41958ccdc5b672a8c5b4e004aaee48d", "8c6928062436813530f7b02865e828b549170841094606cac6074f63f6a70461"),
            ("7c3b0da36e5552299dfe97e40c87fafde231e4587525cafa631d799b83734d09", "c64b5f9e1b4ef9d6eabad71b854b4861baef5fdc7bd185cb8c16b9d993a82600"),
            ("98f2ebc9f46b28a0452e4e0dcb37c256d76ec76a24213475ae0d8795eabf1d33", "5bd8f7d04927f420233861416512e68cfdfa5ad115a64d4c8a2716fe7cbbf7df"),
            ('native_summary["observed_original_native_passes_in_completed_invocation"] != 88',
             'native_summary["observed_original_native_passes_in_completed_invocation"] != 105'),
            ('Path(__file__).resolve(), HERE / "launcher-v2.js", HERE / "launcher-v2.html",',
             'Path(__file__).resolve(), HERE / "launcher-v2.js", HERE / "launcher-v2.html",\n        HERE / "prepare-launcher.py", HERE / "launcher-derivation.json",'),
        ])
    replacements.extend([
        ("BEVEL_BROWSER_EVENT", "OPERATORS_BROWSER_EVENT"),
        ("__bevelEvidence", "__operatorsEvidence"),
        ("__bevelModule", "__operatorsModule"),
        ("original-bmesh-bevel", "original-mesh-operators"),
        ("browser-bevel-host", "browser-operators-host"),
        ("bevel-browser-", "operators-browser-"),
        ("frozen_native_bevel_parser", "frozen_native_operators_parser"),
        ("bevel", "operators"),
    ])
    observed_edits = []
    for before, after in replacements:
        count = text.count(before)
        if count:
            text = text.replace(before, after)
            observed_edits.append({"before": before, "after": after, "occurrences": count})
    edits[name] = observed_edits
    output_ids.append(write_new(name, text))

receipt = {
    "schema": 1, "kind": "evidence-only-original-mesh-launcher-derivation",
    "source_launcher": "original-bmesh-bevel-essentials-chromium-custom-launcher-v2",
    "output_launcher": "original-mesh-operators-essentials-chromium-custom-launcher-v2",
    "source_files": source_ids, "output_files": output_ids, "derivation_script": identity(Path(__file__).resolve()),
    "exact_text_edits": edits,
    "scope": "Receipt/source bindings and observer labels only; original Python, helper, reference fixture, argv, and oracles are not edited.",
    "tests_executed_by_derivation": 0, "full_feature_parity": False,
}
write_new("launcher-derivation.json", json.dumps(receipt, indent=2) + "\n")
print(json.dumps(identity(HERE / "launcher-derivation.json")))
