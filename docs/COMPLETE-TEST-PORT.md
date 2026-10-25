# Complete Blender test-port requirement

## Current result: incomplete

The target is the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not only the implemented subset. Every declaration, parameter expansion, fixture instance, assertion, setup/teardown contract and required configuration needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work remains visible.

[Run 40145587317](https://github.com/596050/blended/actions/runs/40145587317) verifies **581 Blender runtime cases**, natively and at the actual public Chromium URL. Original C++ versus native Rust/browser comparisons check **3,196,371 assertion events per implementation**. **Nineteen compile-time assertions** are separately mapped and verified by positive compilation and deliberate-failure checks on native and wasm32. Repeated assertions, diagnostic observations and infrastructure tests are not additional upstream cases.

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
| Polygon triangulation and beautification | 29 | 1,534,672 |
| Span views and conversion contracts | 40 | 153 |
| Total | 581 | 3,196,371 |

The full native Rust run has **634 runtime tests: 581 Blender, three Cycles and 50 separate product/safety/regression cases**. Eight native and nine browser floating differences remain under original colour-test rules. No tolerances were widened. Whole-suite completion and universal bitwise equivalence are not established.

## Runtime and compile-time evidence must remain distinct

The complete `BLI_span_test.cc` contributes forty runtime declarations and thirteen static predicates. The original `span.ImplicitConversions` declaration has zero runtime assertions because its eight requirements are type-level checks. Its executed case boundaries are retained; the predicates are independently compiled and deliberately falsified rather than replaced with runtime Boolean constants. The earlier `bit_span.SetEmpty` assertion-free case retains its own execution probe.

The required static manifest union is `compile-time-ports.json` plus `span-static-ports.json`. It retains the historical six assertions and all thirteen new predicates. Removing, duplicating or changing a required mapping fails validation. Each new deliberately false predicate must fail with the intended compiler diagnostic on both native and wasm32, not just an arbitrary compilation error.

The pinned C++ span header also has a declared type conversion whose constructor fails when actually instantiated. Its original static trait is faithfully ported, but operational parity with that broken constructor is explicitly not claimed. The Rust implementation of the declared capability is documented separately. See [SPAN-PORT-VERIFICATION.md](SPAN-PORT-VERIFICATION.md).

## Conditional and platform-specific tests remain visible

Five half-float benchmarks guarded by `DO_PERF_TESTS` remain unported. They are not counted as passes or removed from the source inventory; their original workloads must not be quietly reduced when ported. Additional vector type/layout assertions and many other compile-time conditions remain outstanding.

Native x86_64 graphics-format verification changes and restores FTZ/DAZ hardware state. WebAssembly cannot access MXCSR and verifies outputs without claiming that hardware perturbation. Scalar/SSE2/SSE4.1, F16C/AVX, ARM NEON and other required configurations are separate coverage targets. Passing a platform fallback does not establish execution of an unavailable hardware capability.

The polygon port retains the original reversal/cycling-loop behaviour, including the pinned source's use of the original polygon rather than its modified copy. A separate required original-C++ oracle checks genuine permutations. This supplementary coverage does not rewrite the upstream source tests or inflate their case count.

## Source discovery is not a complete runtime denominator

The heuristic scanner finds **5,867 source candidates, 600 reviewed mappings and 5,267 unmapped declarations**. Mappings comprise 581 runtime declarations and nineteen compile-time predicates. Numeric-literal, same-line-declaration and digit-prefixed GoogleTest regressions prevent previously observed omissions. Historical totals retain their original source/configuration scope.

Candidates include conditional, third-party, compile-time and unexpanded declarations. They are not a full runtime denominator or feature percentage. Missing, partial or stale runtime discovery reports remaining runtime coverage as unknown, never zero. Historical `BLI_test` discovery retained 1,644 registrations and 1,643 distinct labels, including ambiguous duplicate `stack.Peek`. That was one executable/configuration, not all Blender. Current reference comparisons execute the mapped subset.

## Evidence and reproduction

[Latest span verification](SPAN-PORT-VERIFICATION.md) · [Assertion method](ASSERTION-FIDELITY.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed contracts consist of the historical base lock and explicitly required polygon/span shards. Runtime groups are registered in `tools/port_registry.py`; the separate static union is in `tools/static_port_registry.py`. Original snapshots, case manifests and reviewed target hashes remain committed. Full diagnostic tapes are preserved losslessly and every assertion event is compared without sampling. Immutable build commits contain production WASM, corresponding source, notices and supplemental evidence.

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

The final command must currently exit nonzero. Do not suppress that failure, narrow its universe or equate a passing subset with completion. Missing-module test-first runs demonstrate absent implementation, not executed failing assertions. Separate mutation probes demonstrate detection of particular broken implementations by unchanged tests.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Per-object metadata is retained at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large payloads were not mirrored as repository blobs or retained as large billable artifacts.

A fresh checkout still has pointers until execution materialises the required inputs. Other dependencies require their own verification. A historical verified download is neither a current fixture nor a passed test. The completeness report describes its own checkout. The current span cases use embedded data and independently generated diagnostic inputs, not .blend payloads.

## Outstanding requirements

1. Discover every required reference configuration and runtime family, retaining CTest/GoogleTest/Python/runner discovery, disabled cases, generated/typed/parameterised instances and build options. Resolve ambiguous, unreadable and template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, Geometry Nodes, dependency graphs, file I/O, animation, rigging, simulation, rendering, compositing and Python/UI families remain extensively unimplemented. Other compile-time and performance cases remain.
3. Execute exact mapped universes natively and in browsers, binding evidence to source/reference revisions, fixture hashes, hardware capabilities and comparison policies. Rendering requires explicit sampling, colour-management and backend contracts.
4. Materialise dependencies during execution and retain outputs. Matching fixture hashes is not execution; isolated algorithm conformance is not integrated workflow conformance.
5. Make the whole-suite gate pass legitimately, then assess full features and performance separately. Complete porting, whole-suite conformance and complete Blender application parity are different milestones.

The workbench tests the compatibility core. It is not the separate object-modeller alpha or a completed Blender editor/rendering engine.
