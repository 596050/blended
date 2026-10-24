# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not the passing subset. Every declaration, parameter expansion, fixture instance, assertion and setup/teardown contract needs a traceable destination. Unsupported, unavailable, unreviewed, ignored and unexecuted work remains visible.

[Run 40049834310](https://github.com/596050/blended/actions/runs/40049834310) verifies **464 unique Blender runtime cases** in native Rust and at the actual deployed Chromium URL. Independent original-C++ comparisons check **34,214 assertion events** in each replacement implementation. Six separately tracked compile-time cases pass positive builds and deliberate-failure checks on native and WebAssembly. They are not extra runtime passes.

| Source group | Runtime cases | Executed assertions |
| --- | ---: | ---: |
| Vector maths | 17 | 68 |
| Scalar maths, bits, solvers and time | 28 | 225 |
| Index ranges, binary search and bounds | 54 | 235 |
| Bit references/vectors, range building, sorted indices | 32 | 521 |
| String references | 53 | 191 |
| Bit spans, groups and bitmap | 27 | 14,460 |
| Vector and colour types | 40 | 259 |
| Matrix types | 21 | 289 |
| Geometric maths | 30 | 154 |
| Image sampling | 27 | 180 |
| Curve sampling | 9 | 222 |
| Heaps and in-place priority queue | 29 | 16,300 |
| Array, CSV, Murmur2A and disjoint sets | 49 | 264 |
| String operations, fuzzy search and naming | 48 | 846 |
| Total | 464 | 34,214 |

The full native Rust run passed 497 runtime tests: 464 Blender, three Cycles and 30 separate product/safety/regression tests. Eight native and nine browser floating differences remain only under original rules. No tolerance was widened. This is not bitwise equality or a complete-suite certificate.

## Source inventory versus runtime discovery

The current heuristic scanner finds **5,859 candidates, 470 reviewed mappings and 5,389 unmapped declarations**. Mappings are 464 runtime plus six compile-time cases. Numeric-literal and same-line-declaration regressions prevent previously observed omissions. Historical totals must not replace the current ledger.

Source candidates include conditional, external, compile-time and unexpanded declarations, so they are not a complete runtime denominator or a feature percentage. Missing, partial or stale runtime discovery reports the remaining runtime total as unknown, never zero. Historical BLI_test discovery retained 1,644 registrations/1,643 distinct labels and an ambiguous duplicate stack.Peek label. That was one executable/configuration, not all Blender. Current original-reference comparisons execute the mapped subset rather than every historical registration.

## Evidence and reproduction

[Accuracy methodology](ASSERTION-FIDELITY.md) · [Current string verification](STRING-OPS-PORT-VERIFICATION.md) · [Status JSON](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3)

Reviewed source and target hashes are in `compatibility/assertion-contracts.lock.json`. Runtime groups are explicitly registered in `tools/port_registry.py`; per-group manifests retain identities/counts/provenance. Compile-time provenance remains in `compatibility/compile-time-ports.json`. Original snapshots are under `tests/upstream/blender`. Durable run-specific C++/Rust/WASM transcripts are on `assertion-fidelity-evidence`, and immutable `test-port-build` commits retain the production module, corresponding source, oracles, mutation probes and native/browser results.

```sh
cargo test --locked --workspace --all-targets
python3 tools/fetch_upstreams.py blender
python3 - <<'PY'
import subprocess, sys
sys.path.insert(0, 'tools')
from port_registry import GROUPS
for generator in dict.fromkeys(group.generator for group in GROUPS):
    subprocess.run([sys.executable, 'tools/' + generator], check=True)
PY
python3 tools/inventory.py --root .upstream/blender --name blender --commit 94363991e7dcf39e2d70614aa002ab6f67764a5d --output build/blender-inventory.json
python3 tools/test_port_audit.py --inventory build/blender-inventory.json --output evidence/complete-test-port.json --require-complete
```

The last command must currently exit nonzero. Do not convert this to an expected pass, use continue-on-error, reduce its scope or interpret green subset publication as complete coverage. Test-first missing-module errors are compilation evidence, not executed assertion failures.

## Fixture recovery is not execution

Historical run 39847680248 downloaded and hash/size-verified all 6,691 LFS objects under pinned tests/files/**: 870,496,042 bytes, including 2,145 .blend files. Durable object metadata is in commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, fixture-evidence/. Large payloads were not mirrored as repository blobs or retained as large billable artifacts.

A fresh checkout still has pointers until execution materialises needed assets. Other dependencies need separate verification. A historical successful download is neither a current fixture nor a passed test. Current string cases use source-embedded data; their supplemental oracle preserves explicit input bytes separately. They do not require .blend payloads.

## Outstanding requirements

1. Discover and reconcile all required reference configurations and test families, including CTest, GoogleTest, Python/runner discovery, disabled tests, generated/typed/parameterised instances, platform options and unreadable/template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, nodes, dependency graph, file I/O, animation, rigging, simulation, rendering, compositor, Python and UI families remain outside this core-library subset.
3. Execute the exact mapped universe natively and in browsers, binding evidence to source/reference revisions, assets, device configuration and comparison policy. Reconcile compile-time assertions separately, including unported type/layout conditions.
4. Materialise dependencies in execution jobs and retain outputs. Rendering requires explicit colour-management, sampling, tolerance and backend contracts.
5. Make whole-suite completeness pass legitimately. Assess application/workflow compatibility and performance as separate milestones; complete test translation, complete conformance and full feature parity are not interchangeable.

The Three.js modeller remains separate from this compatibility workbench. No larger passing library subset can by itself establish a complete Blender modelling/rendering application.
