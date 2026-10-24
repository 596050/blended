# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not the implemented subset. Every declaration, parameter expansion, fixture instance, assertion and setup/teardown contract needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work must remain visible.

[Run 40045600207](https://github.com/596050/blended/actions/runs/40045600207) verifies **416 Blender runtime cases** natively and at the actual public URL. Original-C++ versus native Rust and Chromium WebAssembly comparisons check **33,368 ordered assertion events** per implementation. Six separately tracked compile-time assertions pass positive builds and deliberately broken negative checks on both targets. They are not extra runtime passes.

| Source group | Runtime cases | Expected assertion executions |
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
| Array utilities | 35 | 133 |
| CSV parsing | 10 | 114 |
| Murmur2A hashing | 3 | 5 |
| Disjoint sets | 1 | 12 |
| Total | 416 | 33,368 |

The complete native Rust suite has 444 runtime tests: 416 Blender, three Cycles and 25 product/safety/regression cases. The original colour cases retain eight native and nine browser floating differences within their original rules. No tolerance was widened. Supplemental hash configurations and mutation controls are not counted as new Blender cases.

## Source inventory is not full runtime enumeration

The heuristic scan has **5,859 candidates**, with **422 reviewed mappings and 5,437 unmapped declarations**. Mappings comprise 416 runtime and six compile-time cases. Numeric-literal and same-line-declaration regressions prevent previously observed omissions. Older candidate totals remain historical.

Candidates include conditional, third-party, compile-time and unexpanded declarations. They are not a complete runtime denominator or a feature percentage. Missing, partial or stale runtime inventories report the remaining runtime total as unknown, never zero. Historical BLI_test discovery listed 1,644 registrations and 1,643 distinct labels, retaining duplicate `stack.Peek` as ambiguous. That was one executable/configuration, not all Blender. Current assertion-comparison runs execute the mapped subset, not every historical registration.

## Evidence and reproduction

[Assertion methodology](ASSERTION-FIDELITY.md) · [Latest data verification](DATA-PORT-VERIFICATION.md) · [Current status](../evidence/TEST-PORT-STATUS.json) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed source and target hashes are in `compatibility/assertion-contracts.lock.json`. Runtime groups are in `tools/port_registry.py`; original identities and expected counts are in `compatibility/` manifests. Compile-time provenance is separate. Frozen original tests are under `tests/upstream/blender`. Runtime execution evidence is bound to actual source commits and is not inferred from a manifest's declaration status.

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

The last command must currently exit nonzero. Do not use `continue-on-error`, reduce its scope or interpret a passing subset as whole-suite completion. Missing-module test-first runs are compilation failures, not evidence of individually executed assertion failures.

## Fixtures and dependencies

Historical run `39847680248` downloaded and hash/size-verified all 6,691 LFS objects under pinned `tests/files/**`, totalling 870,496,042 bytes including 2,145 .blend files. Durable per-object metadata is at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Payloads were not mirrored as repository blobs.

A fresh checkout still contains pointers until its execution job materialises the required inputs. Other dependencies need separate verification. A historical download is neither a current fixture nor a test pass. The latest audit still reports unavailable inputs in its checkout. The new data cases use source-embedded inputs and a separately recorded supplemental hash corpus; they do not require .blend fixtures.

## Outstanding requirements

1. Discover every required reference configuration and test family, preserving CTest, GoogleTest and Python/runner discovery, disabled cases, generated/typed/parameterised instances and build options. Reconcile ambiguity and unreadable/template sources.
2. Port remaining assertions, fixtures, setup/teardown and failure semantics. Mesh/BMesh, modifiers, nodes, dependency graph, file I/O, animation, rigging, simulation, rendering, compositor, Python and UI families are not covered by this library subset.
3. Execute the exact mapped universe natively and in browsers, binding evidence to reference/source revisions, fixture hashes, device configuration and comparison rules. Handle compile-time assertions separately.
4. Materialise dependencies during execution and retain outputs. Rendering sampling, colour management, tolerances and backend differences require explicit contracts.
5. Make the whole-suite gate pass legitimately, then evaluate feature/workflow compatibility and performance separately. A complete test port, full test conformance and complete application parity are different milestones.

The separate Three.js modeller has not been replaced by this compatibility workbench. The workbench is not a complete Blender application or rendering engine.
