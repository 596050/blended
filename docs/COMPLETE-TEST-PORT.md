# Complete Blender test-port requirement

## Current result: incomplete

The target is the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not only the implemented subset. Every declaration, parameter expansion, fixture instance, assertion, setup/teardown contract and required configuration needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work remains visible.

[Run 40209288469](https://github.com/596050/blended/actions/runs/40209288469) verifies **609 Blender runtime cases**, natively and at the actual public Chromium URL. Original-C++ versus native Rust/browser comparisons check **3,196,744 assertion events per implementation**. Nineteen compile-time predicates are separately verified with positive compilation and deliberate-failure checks on native and wasm32. Repeated assertions, diagnostic observations and infrastructure tests are not additional upstream cases.

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
| Half floats and normalised formats, enabled functional cases | 9 | 169 |
| Polygon triangulation and improvement | 29 | 1,534,672 |
| Span views and conversion contracts | 40 | 153 |
| Index-mask expressions, enabled functional cases | 15 | 321 |
| Multivalue maps and generic spans | 13 | 52 |
| Total | 609 | 3,196,744 |

The full native run passes **679 runtime tests: 609 Blender, three Cycles and 67 separate product/safety/regression cases**. Eight native and nine browser floating differences remain under original colour-test rules. No tolerances were widened. Whole-suite completion and universal bitwise equivalence are not established.

## Runtime, compile-time and original-source limitations

The complete span source contributes forty runtime declarations and thirteen static predicates. `span.ImplicitConversions` has zero runtime assertions because its eight requirements are type-level checks. Its executed boundaries remain, while the predicates are independently compiled and falsified rather than replaced by constant runtime Booleans. `bit_span.SetEmpty` retains its separate execution probe.

The required static union is `compile-time-ports.json` plus `span-static-ports.json`. The historical six and thirteen newer predicates remain separately mapped. Missing, duplicated or modified requirements fail validation. An unrelated compiler failure cannot satisfy a deliberately false predicate check.

The current map/view batch retains all thirteen original runtime cases, four fixture setups and fifty-two assertions. Its supplemental original-header observer uncovered a declared `MultiValueMap::clear_and_shrink()` API that fails to instantiate. The failure is retained, and operational parity for the replacement's helper is not claimed. The working `clear()` call is used on both targets in the corrected supplemental corpus; no original case was altered. The earlier span trait/constructor discrepancy remains separately documented. Source-level declarations, executable behaviour and test assertions must not be conflated.

## Conditional and platform-specific work

Five half-float `DO_PERF_TESTS` benchmarks and the index-mask expression `#if 0` benchmark remain unported. They are neither counted passing nor removed from discovery. Their original workloads must not be silently reduced. Additional vector layout/type conditions and many other compile-time cases remain outstanding.

Native x86_64 format checks genuinely modify and restore FTZ/DAZ. WebAssembly cannot access MXCSR and verifies outputs without claiming that hardware perturbation. Scalar/SSE2/SSE4.1, F16C/AVX, ARM NEON and other required profiles remain distinct targets. Passing an unsupported-platform fallback is not evidence of exercising a missing capability.

The polygon port retains the original permutation-loop behaviour; an independent mandatory original-C++ oracle checks genuine transformed polygons. Mask expressions retain all original random inputs and compare full selected-index membership. Supplemental checks strengthen coverage without rewriting upstream expectations or inflating runtime case counts.

## Source discovery is not a complete runtime denominator

The heuristic scan has **5,867 source candidates, 628 reviewed mappings and 5,239 unmapped declarations**. Mappings comprise 609 runtime and nineteen compile-time cases. Numeric-literal, same-line and digit-prefixed test-name regressions prevent known omissions. Historical counts retain their original revision and scope.

Candidates include conditional, third-party, compile-time and unexpanded declarations. They are not a complete runtime denominator or feature percentage. Missing, partial or stale runtime discovery means the remaining runtime count is unknown, never zero. Historical `BLI_test` enumeration retained 1,644 registrations and 1,643 distinct labels, including ambiguous duplicate `stack.Peek`. That was one configured executable, not every Blender test family. Current reference comparisons execute the mapped subset.

## Evidence and reproduction

[Latest map/view verification](CONTAINER-VIEW-PORT-VERIFICATION.md) · [Assertion method](ASSERTION-FIDELITY.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

The reviewed contract union includes the historical base lock and required polygon/span/mask/container shards, totalling 43 source contracts. New shards do not rewrite historical approval hashes. Runtime groups are in `tools/port_registry.py`; static requirements are separately registered. Complete originals, case manifests and target hashes are committed. Every diagnostic event is compared and preserved losslessly. Immutable builds contain production WASM, corresponding source, notices and supplemental results.

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

The last command must currently exit nonzero. Do not suppress its failure, narrow its universe or equate a passing subset with full completion. Missing-module test-first logs show absence of implementation, not executed assertion failures. Mutation probes separately establish detection of particular broken implementations.

Corresponding-source archives now include workflow sources and small reference-limit JSON fixtures required by regression tests. The final archive was freshly extracted and all 304 Python tests rerun successfully. Native/C++/browser results remain separately evidenced by CI, not by that Python-only local check.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Per-object metadata is preserved at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large payloads were not mirrored as repository blobs or retained as large billable artifacts.

Fresh checkouts still have pointers until execution materialises required inputs. Other dependencies require verification. Historical downloads are neither current fixtures nor passed tests. The completeness report describes its own checkout. These map/view tests use embedded inputs and a separate deterministic observer corpus, not .blend fixtures.

## Outstanding requirements

1. Discover every required reference configuration and test family, preserving CTest/GoogleTest/Python/runner discovery, disabled cases, typed/generated/parameterised instances and build options. Resolve unreadable and ambiguous sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, Geometry Nodes, dependency graphs, file I/O, animation, rigging, simulation, rendering, compositing and Python/UI families remain extensively unfinished. More static and performance cases remain.
3. Execute exact mapped universes natively and in browsers, binding evidence to source/reference revisions, fixture hashes, hardware capabilities and comparison policies. Rendering requires explicit sampling, colour-management and backend contracts.
4. Materialise dependencies at execution and retain outputs. Matching fixture hashes is not execution; isolated algorithm tests do not establish integrated workflows.
5. Make the complete-suite gate pass legitimately, then assess full features and performance separately. Complete porting, whole-suite conformance and complete Blender application parity are distinct milestones.

The workbench tests the compatibility core. It is not the separate object-modeller alpha or a completed Blender editor/rendering engine.
