# Complete Blender test-port requirement

## Current result: incomplete

The target is the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not only the implemented subset. Every declaration, parameter expansion, fixture instance, assertion, setup/teardown contract and required configuration needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work remains visible.

[Run 40108130160](https://github.com/596050/blended/actions/runs/40108130160) verifies **512 Blender runtime cases**, natively and at the actual public Chromium URL. Original C++ versus native Rust/browser comparisons check **1,661,546 assertion events per implementation**. Six compile-time assertions separately pass positive-build and deliberate-failure checks on native and wasm32. Repeated assertions, diagnostic corpus inputs and infrastructure tests are not additional upstream cases.

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
| Half floats and normalised integer formats, enabled functional cases | 9 | 169 |
| Total | 512 | 1,661,546 |

The full native Rust run has 558 runtime tests: 512 Blender, three Cycles and 43 separate product/safety/regression tests. Eight native and nine browser floating differences remain under original colour-test rules. No tolerances were widened. Whole-suite completion and universal bitwise parity are not established.

## Conditional and platform-specific tests remain visible

The latest half-float batch ports its eight enabled functional cases plus the one normalised-int case. Five `math_half_perf` benchmarks guarded by `DO_PERF_TESTS` remain unported. They are not considered passes or removed from the source inventory. Their original 100-million-item workloads must not be quietly reduced when ported. The source manifest preserves all five identities and their disabled-in-this-build condition.

Native x86_64 verification truly changes/restores FTZ/DAZ. Browser WASM has no accessible MXCSR register and verifies outputs without claiming that hardware perturbation. The new bit-level oracle targets scalar/SSE2/SSE4.1 behaviour; F16C/NEON and other required build/device profiles remain separate work. A case passing with a platform's no-op fallback is not proof that a missing hardware capability was exercised.

## Source discovery is not a runtime denominator

The heuristic scanner finds **5,859 source candidates, 518 reviewed mappings and 5,341 unmapped declarations**. Mappings comprise 512 runtime and six compile-time cases. Numeric-literal and same-line-declaration regressions prevent previously observed omissions. Historical totals retain their original scope.

Candidates include conditional, third-party, compile-time and unexpanded declarations. They are not a complete runtime denominator or feature percentage. Missing, partial or stale discovery reports the remaining runtime total as unknown, never zero. Historical `BLI_test` discovery retained 1,644 registrations and 1,643 distinct labels, including ambiguous duplicate `stack.Peek`. That was one executable/configuration, not all Blender. Current reference comparisons execute the mapped subset.

## Evidence and reproduction

[Latest format verification](PIXEL-FORMAT-PORT-VERIFICATION.md) · [Assertion method](ASSERTION-FIDELITY.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed hashes remain in `compatibility/assertion-contracts.lock.json`; explicit groups are in `tools/port_registry.py`. Original snapshots and case manifests are committed. Compile-time provenance is separate in `compatibility/compile-time-ports.json`. Full assertion tapes are preserved losslessly and every event compared, not sampled. Immutable build commits contain production WASM, corresponding source, notices and diagnostic evidence.

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

The final command must currently exit nonzero. Do not suppress its failure, narrow its universe or equate a successful subset with completion. A missing-module test-first run proves absence of implementation, not executed failing assertions. Separate mutation probes establish detection of specific broken implementations by unchanged tests.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes, including 2,145 .blend files. Per-object metadata is at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large payloads were not mirrored as repository blobs or retained as large billable artifacts.

Fresh checkouts still contain pointers until execution materialises inputs. Other dependencies require verification. A historical verified download is neither a current fixture nor a passed test. The completeness report describes its own checkout. The current format cases use embedded data and a separately serialised bit corpus, not .blend payloads.

## Outstanding requirements

1. Discover every required reference configuration and runtime family, retaining CTest/GoogleTest/Python/runner discovery, disabled cases, generated/typed/parameterised instances and build options. Resolve ambiguous, unreadable and template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, Geometry Nodes, dependency graphs, file I/O, animation, rigging, simulation, rendering, compositing and Python/UI families remain extensively unimplemented. Additional compile-time and performance cases remain.
3. Execute exact mapped universes natively and in browsers, binding evidence to source/reference revisions, fixture hashes, hardware capabilities and comparison policies. Rendering requires explicit sampling, colour-management and backend contracts.
4. Materialise dependencies during execution and retain outputs. Matching fixture hashes is not execution; isolated algorithm conformance is not integrated workflow conformance.
5. Make the whole-suite gate pass legitimately, then assess full features and performance separately. Complete porting, all-tests-passing and complete Blender application parity are different milestones.

The workbench tests the compatibility core. It is not the separate object-modeller alpha, nor a completed Blender editor or rendering engine.
