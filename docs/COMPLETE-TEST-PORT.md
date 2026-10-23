# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not the implemented subset. Every declaration, parameter expansion, fixture instance, assertion and setup/teardown contract needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work must remain visible.

As verified in [run 40019426923](https://github.com/596050/blended/actions/runs/40019426923), **367 Blender runtime cases** pass natively and in the actual deployed Chromium browser. Original-C++ versus Rust/Chromium comparisons check **33,104 assertion events**. Six separately tracked compile-time assertions pass positive and negative-mutation checks on native and WASM targets. These are not extra runtime passes.

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
| Total | 367 | 33,104 |

The complete native Rust suite has 390 runtime tests: 367 Blender ports, three Cycles cases and 20 product/safety/regression tests. Eight native and nine browser floating differences are accepted only under the corresponding original comparison rules. This is not bitwise equality or a full-suite certificate.

## Source inventory is not full runtime enumeration

The current heuristic scanner finds **5,859 candidates**, with **373 reviewed mappings and 5,486 unmapped declarations**. Mappings consist of 367 runtime cases and six separately registered compile-time cases. Numeric-literal and same-line-declaration regressions prevent previously observed omissions. Older candidate totals are historical and must not replace the current ledger.

Candidates include conditional, third-party, compile-time and unexpanded declarations. This is not a complete runtime denominator or a feature percentage. Missing, partial or stale runtime inventories report the remaining runtime total as unknown, never zero. Historical `BLI_test` discovery listed 1,644 registrations and 1,643 distinct labels, retaining duplicate `stack.Peek` as ambiguous. That was one executable/configuration, not all Blender. Current comparison runs execute the mapped subset, not every historical registration.

## Evidence and reproduction

[Assertion methodology](ASSERTION-FIDELITY.md) · [Latest heap verification](HEAP-PORT-VERIFICATION.md) · [Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed source/target hashes are in `compatibility/assertion-contracts.lock.json`. Runtime groups are explicitly registered in `tools/port_registry.py`, with corresponding manifests in `compatibility/`. Compile-time provenance is separate in `compatibility/compile-time-ports.json`. Original tests are frozen under `tests/upstream/blender`. Raw reference/Rust/WASM transcripts are retained on `assertion-fidelity-evidence`; immutable `test-port-build` commits preserve production modules, corresponding sources, input probes and native/browser evidence.

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

The last command must currently exit nonzero. Do not wrap this as an expected failure, use `continue-on-error`, reduce its scope or interpret a green subset as full completion. Test-first runs with absent modules are evidence of missing implementations, not evidence that their individual assertions executed and failed.

## Fixture recovery is not execution

Historical run `39847680248` downloaded and hash/size-verified all 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Durable per-object metadata is at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large payloads were not mirrored as repository blobs or retained as large billable artifacts.

A fresh checkout still has pointers until the execution job materialises the needed inputs. Other dependencies require separate verification. A historical verified download is neither a current fixture nor a passed test. The completeness audit reports its own checkout state. Heap tests use source-embedded values and deterministic generators, with a separate exact input oracle; they do not require .blend fixtures.

## Outstanding requirements

1. Discover all required reference configurations and test families. Preserve CTest, GoogleTest, Python/runner discovery, disabled tests, generated/typed/parameterised instances and build options. Reconcile ambiguity and unreadable/template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, nodes, dependency graph, file I/O, animation, rigging, simulation, rendering, compositor, Python and UI families are not covered by this core-library subset.
3. Execute the exact mapped universe natively and in browsers, binding evidence to source/reference revisions, fixture hashes, device configuration and comparison policies. Resolve compile-time conditions separately.
4. Materialise required dependencies during execution and retain outputs. Rendering tolerances, colour management, sampling and backend differences require explicit contracts.
5. Make the whole-suite gate pass legitimately. Evaluate feature/workflow compatibility and performance separately. A complete port, complete test conformance and full application parity are different milestones.

The separate Three.js modeller has not been replaced by the workbench. This workbench tests the Rust compatibility core, not a complete Blender modelling/rendering application.
