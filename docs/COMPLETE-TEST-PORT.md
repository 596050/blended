# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not only the implemented subset. Every declaration, parameter expansion, fixture instance, assertion, setup/teardown contract and required configuration needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work must remain visible.

[Run 40149763130](https://github.com/596050/blended/actions/runs/40149763130) verifies **596 Blender runtime cases**, natively and at the actual deployed Chromium URL. Original-C++ versus native Rust and browser comparisons check **3,196,692 assertion events per implementation**. **Nineteen compile-time predicates** remain separately mapped and verified with positive compilation and deliberate-failure checks on native and wasm32. Repeated assertions, diagnostic observations and infrastructure tests are not additional upstream cases.

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
| Index-mask expressions, enabled functional cases | 15 | 321 |
| Total | 596 | 3,196,692 |

The full native Rust run passed **656 runtime tests: 596 Blender, three Cycles and 57 separate product/safety/regression cases**. Eight native and nine browser floating differences remain in earlier colour tests under their original rules. No tolerances were widened. Whole-suite completion and universal bitwise parity are not established.

## Runtime, static, disabled and platform coverage remain distinct

The complete span source contributes forty runtime declarations and thirteen static predicates. `span.ImplicitConversions` contains zero runtime assertions because its eight requirements are type-level checks. Its executed boundaries remain recorded; the predicates are independently compiled and deliberately falsified. The earlier assertion-free bit-span case retains its own execution probe.

The required static union is `compile-time-ports.json` plus `span-static-ports.json`. It retains the original six mappings and all thirteen span predicates. Removing, duplicating or changing a required mapping fails verification. A deliberately false predicate must fail with its intended compiler diagnostic, not just any build error. The pinned span conversion declared by a type trait but failing when instantiated remains an explicitly documented reference limitation, not a false operational-equivalence claim.

The latest index-mask expression file has fifteen enabled cases plus **one unported `#if 0` benchmark**. The benchmark remains in the source inventory and is not counted passing. Five earlier half-float benchmarks guarded by `DO_PERF_TESTS` remain unported too. Their original workloads must not be quietly reduced when they are ported. Further vector-layout and other compile-time requirements remain outstanding.

Native x86_64 graphics-format verification changes and restores FTZ/DAZ hardware state. Browser WebAssembly cannot access MXCSR and checks outputs without claiming that hardware perturbation. Scalar/SSE2/SSE4.1, F16C/AVX, ARM NEON and other configurations remain distinct targets. A platform fallback passing does not prove an unavailable capability was exercised.

The polygon port preserves the original cycling/reversal-loop behaviour, including the pinned source's mistaken use of the original polygon rather than its modified copy. Its separate genuine-permutation oracle remains distinct supplemental evidence. The mask port retains every original randomized test input; a separate exact-input probe verifies generated data and absolute selected indices. Its first out-of-domain supplemental attempt failed, was retained, and was not relabelled passing. Original tests did not change when that supplemental corpus was corrected to the reference constructor's domain.

## Source discovery is not a complete runtime denominator

The scanner finds **5,867 source candidates, 615 reviewed mappings and 5,252 unmapped declarations**. Mappings comprise 596 runtime declarations and nineteen compile-time predicates. Numeric-literal, same-line-declaration and digit-prefixed GoogleTest regressions prevent previously observed omissions. Historical totals retain their source/configuration scope.

Candidates include conditional, third-party, compile-time and unexpanded declarations. They are not a complete runtime denominator or feature percentage. Missing, partial or stale runtime discovery reports remaining runtime coverage as unknown, never zero. Historical `BLI_test` discovery retained 1,644 registrations and 1,643 distinct labels, including ambiguous duplicate `stack.Peek`. That was one executable/configuration, not all Blender. Current reference comparisons execute the mapped subset.

## Evidence and reproduction

[Latest mask verification](MASK-EXPRESSION-PORT-VERIFICATION.md) · [Assertion method](ASSERTION-FIDELITY.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed runtime contracts comprise the historical base lock and explicitly required polygon, span and mask-expression shards. Runtime groups are registered in `tools/port_registry.py`; the static union is in `tools/static_port_registry.py`. Original snapshots, manifests and fixed reviewed target hashes remain committed. Full tapes are retained losslessly and every assertion event is compared without sampling. Mask operands retain every selected index through reversible encoding, never a count/hash-only surrogate. Immutable builds contain production WASM, corresponding source, notices and supplemental evidence.

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

The final command must currently exit nonzero. Do not suppress its failure, shrink its universe or equate a passing subset with completion. Missing-module test-first runs demonstrate absent implementation, not executed failing assertions. Separate mutation probes demonstrate unchanged tests detecting particular broken implementations.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Metadata is retained at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large payloads were not mirrored as repository blobs or retained as large billable artifacts.

Fresh checkouts still contain pointers until execution materialises required inputs. Other dependencies need separate verification. A historical download is neither a current fixture nor a passed test. The completeness report describes its own checkout. Current mask tests use embedded data and the original deterministic random helper, not .blend payloads; all generated random inputs are separately compared with original C++.

## Outstanding requirements

1. Discover every required reference configuration and runtime family, retaining CTest/GoogleTest/Python/runner discovery, disabled cases, generated/typed/parameterised instances and build options. Resolve ambiguous, unreadable and template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, Geometry Nodes, dependency graphs, file I/O, animation, rigging, simulation, rendering, compositing and Python/UI families remain extensively unimplemented. Other compile-time and performance cases remain.
3. Execute exact mapped universes natively and in browsers, binding evidence to source/reference revisions, fixture hashes, hardware capabilities and comparison policies. Rendering needs explicit sampling, colour-management and backend contracts.
4. Materialise dependencies during execution and retain outputs. Matching fixture hashes is not execution; isolated algorithm conformance is not integrated workflow conformance. Serial semantic results are not parallel execution or performance parity.
5. Make the whole-suite gate pass legitimately, then assess full features and performance separately. Complete porting, all-tests-passing and complete Blender application parity remain different milestones.

The workbench tests the Rust compatibility core. It is not the separate object-modeller alpha or a completed Blender editor/rendering engine.
