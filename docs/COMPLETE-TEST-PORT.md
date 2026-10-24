# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not only the implemented subset. Every declaration, parameter expansion, fixture instance, assertion, setup/teardown contract and relevant configuration needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work remains visible.

[Run 40065241089](https://github.com/596050/blended/actions/runs/40065241089) verifies **503 Blender runtime cases**, natively and at the actual deployed Chromium URL. Original C++ versus native Rust/Chromium comparisons check **1,661,377 assertion events per implementation**. Six compile-time assertions separately pass positive and deliberate-failure checks on native and WebAssembly targets. Repeated stress assertions, oracle configurations and infrastructure tests are not additional upstream cases.

| Source group | Runtime cases | Executed assertions |
| --- | ---: | ---: |
| Vector maths | 17 | 68 |
| Scalar maths, bits, solvers and time | 28 | 225 |
| Index ranges, binary search and bounds | 54 | 235 |
| Bit references, bit vectors, range building, sorted indices | 32 | 521 |
| String references | 53 | 191 |
| Bit spans, groups and bitmap | 27 | 14,460 |
| Vector and colour types | 40 | 259 |
| Matrix types | 21 | 289 |
| Geometric maths | 30 | 154 |
| Image sampling | 27 | 180 |
| Curve sampling | 9 | 222 |
| Heaps and in-place priority queue | 29 | 16,300 |
| Array operations, CSV, Murmur2A and disjoint sets | 49 | 264 |
| String operations, fuzzy search and unique names | 48 | 846 |
| UTF-8 boundaries, malformed bytes and cursor movement | 39 | 1,627,163 |
| Total | 503 | 1,661,377 |

The native Rust suite has 542 runtime tests: 503 Blender ports, three Cycles and 36 separate product/safety/regression cases. Eight native and nine browser floating differences remain only under the original comparison rules. This is not bitwise equality or full-suite completion.

## Source inventory is not full runtime enumeration

The current heuristic scanner finds **5,859 source candidates**, with **509 reviewed mappings and 5,350 unmapped declarations**. Mappings consist of 503 runtime and six compile-time cases. Numeric-literal and same-line-declaration regression tests prevent previously observed omissions. Older totals retain only historical scope.

Candidates include conditional, third-party, compile-time and unexpanded declarations. They are not a complete runtime denominator or a feature percentage. Missing, partial or stale runtime inventories report the remaining runtime total as unknown, never zero. Historical `BLI_test` discovery retained 1,644 registrations and 1,643 distinct labels, including ambiguous duplicate `stack.Peek`. That was one configured executable, not every Blender runtime family. Current reference comparisons execute the mapped subset.

## Evidence and reproduction

[Latest UTF-8 verification](UTF8-PORT-VERIFICATION.md) · [Fidelity method](ASSERTION-FIDELITY.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed hashes are in `compatibility/assertion-contracts.lock.json`; the explicit runtime registry is `tools/port_registry.py`. Original source snapshots and case manifests remain committed. Compile-time provenance is separate in `compatibility/compile-time-ports.json`. Raw assertion tapes are preserved losslessly on `assertion-fidelity-evidence`, with all events compared rather than sampled. Immutable build commits retain production WASM, corresponding source, full notices and diagnostic evidence.

```sh
cargo test --locked --workspace --all-targets
python3 tools/fetch_upstreams.py blender
python3 tools/generate_utf8_tables.py
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

The final command must currently exit nonzero. Do not suppress that failure, shrink its universe or present a green subset as full completion. Test-first missing-module runs establish absence of implementation, not executed failing assertions. Mutation probes separately establish that unchanged tests detect specific broken implementations.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Per-object metadata is preserved at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large fixture payloads were not mirrored as repository blobs or retained as large billable artifacts.

A fresh checkout still contains pointers until execution materialises the required inputs. Dependencies elsewhere need separate verification. Historical downloads are neither current fixtures nor passed tests. The latest UTF-8 cases use source-embedded data, deterministic byte generators and the pinned width table, not .blend assets. The completeness report honestly describes its own checkout, including unavailable fixture payloads.

## Outstanding work

1. Discover every required reference configuration and runtime family, retaining CTest/GoogleTest/Python/runner discovery, disabled cases, generated/typed/parameterised instances and build options. Resolve ambiguous, unreadable and template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, Geometry Nodes, dependency graphs, file I/O, animation, rigging, simulation, rendering, compositing and Python/UI families remain extensively unimplemented. Additional compile-time conditions also remain.
3. Execute exact mapped universes natively and in browsers. Bind evidence to source/reference revisions, fixture hashes, device configuration and comparison policies. Rendering needs explicit sampling, colour-management, backend and tolerance contracts.
4. Materialise all required dependencies during execution and retain outputs. Matching fixture hashes does not establish execution; passing isolated algorithms does not establish integrated workflows.
5. Make the whole-suite gate pass legitimately, then evaluate feature compatibility and performance separately. Complete porting, full-suite conformance and complete Blender application parity are different milestones.

The workbench tests the Rust compatibility core. It is not a replacement for the separate object-modeller alpha, nor a completed Blender editor or rendering engine.
