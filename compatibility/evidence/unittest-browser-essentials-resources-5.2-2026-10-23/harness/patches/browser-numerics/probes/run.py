#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blended contributors
# SPDX-License-Identifier: Apache-2.0
"""Run numerical kernel regressions without modifying Blender acceptance tests.

Requires the pinned Emscripten SDK and checksum-verified pinned Eigen headers.
This checks actual WebAssembly under Node, including the pthread libc variant.
It does not execute Blender or award an application facet a passing status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emsdk-root", type=Path, required=True)
    parser.add_argument("--eigen-include", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-libc", choices=("original", "patched"), default="patched")
    args = parser.parse_args()
    sdk, eigen, cache, out = (p.resolve() for p in (
        args.emsdk_root, args.eigen_include, args.cache, args.output,
    ))
    out.mkdir(parents=True, exist_ok=True)
    em = sdk / "upstream/emscripten"
    node = sdk / "node/22.16.0_64bit/bin/node"
    manifest_path = HERE.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest_sha = sha256(manifest_path)
    expected = json.loads((HERE / "expectations.json").read_text())
    sdk_patch = next(p for p in manifest["patches"] if p["component"] == "emscripten")
    expected_source = sdk_patch["after_sha256" if args.expect_libc == "patched" else "before_sha256"]
    if sha256(em / sdk_patch["path"]) != expected_source:
        raise RuntimeError("SDK acosf source does not match the requested manifest state")
    if args.expect_libc == "patched" and manifest_sha not in str(cache):
        raise RuntimeError("Patched EM_CACHE namespace must contain the manifest SHA-256")
    for path, digest in expected["inputs"].items():
        if sha256(HERE / path) != digest:
            raise RuntimeError(f"Regression input changed: {path}")
    for path, digest in expected["eigen_header_checks"].items():
        if sha256(eigen / path) != digest:
            raise RuntimeError(f"Pinned Eigen header changed: {path}")

    env = dict(os.environ, EM_CONFIG=str(sdk / ".emscripten"), EM_CACHE=str(cache))
    env.setdefault("EMCC_CORES", "2")
    env.setdefault("EMCC_USE_NINJA", "0")
    commands = []

    def run(argv, stdin=None):
        start = time.monotonic()
        proc = subprocess.run(
            [str(x) for x in argv], cwd=HERE, env=env, input=stdin,
            text=True, capture_output=True, timeout=240,
        )
        commands.append({
            "argv": [str(x) for x in argv], "returncode": proc.returncode,
            "elapsed_seconds": time.monotonic() - start,
            "stdout": proc.stdout, "stderr": proc.stderr,
        })
        (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if proc.returncode:
            raise RuntimeError(f"Kernel command failed; see {out / 'commands.json'}")
        return proc

    version = run([em / "emcc", "--version"]).stdout
    if expected["emscripten_commit"] not in version or "6.0.5" not in version:
        raise RuntimeError("Unexpected Emscripten compiler identity")
    node_version = run([node, "--version"]).stdout.strip()
    if node_version != "v22.16.0":
        raise RuntimeError("Unexpected Node runtime identity")
    receipt = {
        "schema": 1, "diagnostic_only": True, "actual_wasm_executed": True,
        "acceptance_status": "not_evaluated", "full_parity": False,
        "patchset_id": manifest["id"], "manifest_sha256": manifest_sha,
        "compiler_identity": version, "node_version": node_version,
        "native_oracle_scope": expected["native_oracle_scope"],
        "emscripten_cache": str(cache), "libc_state": args.expect_libc,
        "acosf": {}, "inverse": {},
    }
    cflags = [em / "emcc", "-std=c11", "-O2", "-fno-fast-math",
              "-ffp-contract=off", "-fno-builtin-acosf"]
    csource = ["acos_probe.c", "acosf_reference.c", "acosf_candidate.c"]
    vector_input = (HERE / "acos_inputs.txt").read_text()
    vector_expected = expected["vectors"]["rows"]
    for label, flags in (
        ("normal", []),
        ("pthread", ["-pthread", "-sPROXY_TO_PTHREAD", "-sPTHREAD_POOL_SIZE=1"]),
    ):
        output = out / ("acos-" + label + ".js")
        linked = run(cflags + csource + flags + [
            "-sENVIRONMENT=node", "-sEXIT_RUNTIME=1", "-Wl,--trace-symbol=acosf", "-o", output,
        ])
        library = "libc-mt.a" if label == "pthread" else "libc.a"
        if library + "(acosf.o): definition of acosf" not in linked.stdout:
            raise RuntimeError(f"Missing direct libc symbol provenance for {label}")
        execution = run([node, output], vector_input)
        (out / ("acos-" + label + ".txt")).write_text(execution.stdout)
        rows = [line.split() for line in execution.stdout.splitlines()]
        if len(rows) != expected["vectors"]["count"]:
            raise RuntimeError("Missing or extra vector observations")
        for row, ref in zip(rows, vector_expected):
            if len(row) != 7 or int(row[0]) != ref["index"]:
                raise RuntimeError("Vector observation shape or identity changed")
            desired = ref["native_bits"] if args.expect_libc == "patched" else ref["original_bits"]
            if row[3] != desired or row[4] != ref["original_bits"] or row[5] != ref["native_bits"]:
                raise RuntimeError(f"Unexpected vector bits at {ref['index']}")
        receipt["acosf"][label] = {
            "observations": len(rows),
            "library_matches_requested_state": True,
            "candidate_matches_native_bits": len(rows),
            "original_low_angle_observations": sum(row[4] == "3fc90fda" for row in rows),
            "direct_library_low_angle_observations": sum(row[3] == "3fc90fda" for row in rows),
            "link_trace": linked.stdout,
        }

    cpp = [em / "em++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
           "-fexceptions", "-I", eigen]
    run(cpp + ["-msimd128", "-msse2", "-c", "inverse.cc", "-o", out / "inverse-sse.o"])
    run(cpp + ["-DEIGEN_DONT_VECTORIZE", "-DPROBE_INVERSE_NAME=inverse_scalar",
               "-c", "inverse.cc", "-o", out / "inverse-scalar.o"])
    run(cpp + ["-c", "spin_transform_probe.cc", "-o", out / "spin.o"])
    run([em / "em++", "-O2", "-msimd128", "-ffp-contract=off", "-fexceptions",
         out / "spin.o", out / "inverse-sse.o", out / "inverse-scalar.o",
         "-sENVIRONMENT=node", "-sEXIT_RUNTIME=1", "-o", out / "spin.js"])
    execution = run([node, out / "spin.js"], (HERE / "space_inputs.txt").read_text())
    (out / "spin.txt").write_text(execution.stdout)
    observed = {}
    for line in execution.stdout.splitlines():
        row = line.split()
        if row[0] == "vertex":
            if len(row) != 8:
                raise RuntimeError("Invalid transform observation")
            key = (int(row[1]), int(row[2]))
            observed.setdefault(key, []).append({
                "step": int(row[3]), "seed": int(row[4]), "bits": row[5:],
            })
        elif row[0] != "inverse":
            raise RuntimeError("Unexpected transform output")
    if set(observed) != {(0, 0), (0, 1), (1, 0), (1, 1)}:
        raise RuntimeError("Missing transform variants")
    for (scalar, paired), rows in observed.items():
        desired = expected["spin"]["original_rows" if scalar else "native_rows"]
        if rows != desired:
            raise RuntimeError(f"Transform bit mismatch: scalar={scalar}, paired={paired}")
        receipt["inverse"][f"scalar_{scalar}_paired_{paired}"] = {
            "coordinate_observations": len(rows),
            "exact_reference": "original_browser" if scalar else "official_native",
            "all_coordinate_bits_match": True,
        }
    receipt["source_sha256"] = {
        path.name: sha256(path) for path in sorted(HERE.iterdir()) if path.is_file()
    }
    receipt["wasm_artifacts"] = {
        path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
        for path in sorted(out.glob("*.wasm"))
    }
    receipt["status"] = "kernel_regressions_passed"
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(out / "receipt.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
