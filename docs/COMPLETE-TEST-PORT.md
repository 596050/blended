# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not only the implemented subset. Every declaration, parameter expansion, fixture instance, assertion, setup/teardown contract and required configuration needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work remains visible.

[Run 40142038492](https://github.com/596050/blended/actions/runs/40142038492) verifies **541 Blender runtime cases** natively and at the actual deployed Chromium URL. Independent original-C++ versus native Rust/Chromium comparisons check **3,196,218 assertion events per implementation**. Six compile-time assertions separately pass positive builds and deliberate-failure checks on native and wasm32. Repeated stress assertions, oracle configurations and infrastructure tests are not additional upstream cases.

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
| Total | 541 | 3,196,218 |

The full native Rust run passed 587 runtime tests: 541 Blender, three Cycles and 43 separate product/safety/regression tests. Eight native and nine browser floating differences remain within original colour-test comparison rules. No tolerances were widened. Whole-suite completion and arbitrary-input equivalence are not established.

## Preserve source tests and expose coverage gaps

All 29 polygon test identities and original helper loops are retained. The upstream helper cycles/reverses a copy but passes the original polygon; the port preserves this observed behaviour. A separately labelled mandatory oracle tests genuine shifts, reversals and sign flips on all original inputs. Exact index sequences match in native Rust and Node.js WASM for that supplemental corpus. Original cases separately run through the full Chromium comparison and production public URL. Do not claim the supplemental Node execution is a browser test or that diagnostic inputs are extra upstream cases.

Five optional `DO_PERF_TESTS` half-float benchmarks remain explicitly unported, not passing. Their source identities remain in the inventory. Their workloads must not be silently reduced when ported. Native x86_64 hardware FP-mode checks and browser output-only fallback remain distinct capabilities. Other device/compiler/platform configurations, F16C/NEON profiles and further compile-time conditions require their own mapping and execution evidence.

## Source discovery is not a runtime denominator

The updated heuristic scan finds **5,867 source candidates, 547 reviewed mappings and 5,320 unmapped declarations**. Mappings are 541 runtime plus six compile-time cases. The increase of eight source candidates is a discovery correction: GoogleTest permits token-pasted digit-prefixed arguments. The scanner now retains two polygon names and six libmv ArrayND names previously omitted. Discovery alone does not mark a case ported.

Candidates also include conditional, third-party, compile-time and unexpanded declarations. They are not a complete runtime denominator or feature percentage. Missing, partial or stale runtime enumeration reports the remaining runtime count as unknown, never zero. Historical `BLI_test` discovery retained 1,644 registrations and 1,643 distinct labels, including ambiguous duplicate `stack.Peek`; that was one executable/configuration, not the full application. Current reference comparisons execute the mapped subset.

## Evidence, mandatory contracts and reproduction

[Polygon verification](POLYFILL-PORT-VERIFICATION.md) · [Fidelity methodology](ASSERTION-FIDELITY.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed hashes live in the historical `compatibility/assertion-contracts.lock.json` plus explicitly required shards enumerated by `tools/contract_registry.py`. The polygon shard is not optional. Missing, mismatched or duplicated contracts fail closed. Runtime groups are explicitly listed in `tools/port_registry.py`; every consumer reads the same 39-contract union. Original snapshots and case manifests remain committed. Compile-time provenance stays separate in `compatibility/compile-time-ports.json`.

Full assertion transcripts are preserved losslessly and every event is compared, not sampled. Immutable build commits retain production WASM, corresponding source, notices and diagnostic evidence. The latest original test-first log has a durable hash/summary and a linked Actions artifact whose retention limit is explicit, not a fabricated permanent full-log archive.

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

The final command must currently exit nonzero. Do not suppress it, shrink the universe or treat the successful subset as full completion. A test-first missing-module run proves absence of implementation, not execution of failing assertions. Mutation evidence, where present for earlier families, is a separate category.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Per-object metadata is retained at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. The large payloads were not mirrored as repository blobs or retained as large billable artifacts.

Fresh checkouts still need to materialise required inputs. Other dependencies need verification. Historical downloaded bytes are neither current fixtures nor passed tests. The completeness report describes its actual checkout. The current polygon cases use source-embedded coordinate arrays and a separately serialised exact-input corpus, not .blend files.

## Outstanding requirements

1. Discover every required reference configuration and runtime family, preserving CTest/GoogleTest/Python/runner discovery, disabled tests, generated/typed/parameterised instances and build options. Resolve ambiguity and unreadable/template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Extensive mesh/BMesh, modifiers, Geometry Nodes, dependency graph, file I/O, animation, rigging, simulation, rendering, compositing and Python/UI families remain unimplemented, alongside compile-time/performance cases.
3. Execute exact mapped universes natively and in browsers, binding evidence to source/reference revisions, fixtures, hardware capabilities and comparison policies. Rendering requires explicit sampling, colour-management and backend contracts.
4. Materialise all required execution dependencies and retain outputs. Fixture hashes do not establish execution; isolated algorithm conformance does not establish integrated application workflows.
5. Make the whole-suite gate pass legitimately, then assess complete features and performance separately. Complete porting, full conformance and Blender application parity are different milestones.

The workbench tests the compatibility core. It is not the separate modeller alpha, nor a completed Blender editor or renderer.
