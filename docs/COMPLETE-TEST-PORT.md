# Complete Blender test-port requirement

## Current result: incomplete

The target remains the complete suite at Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not the implemented subset. Every declaration, parameter expansion, fixture instance, assertion and setup/teardown contract needs a traceable destination. Unsupported, ignored, unavailable, unreviewed and unexecuted work must remain visible.

As verified in [run 39918173966](https://github.com/596050/blended/actions/runs/39918173966), **131 Blender runtime cases** pass natively and in the actual deployed browser. Independent original-C++ versus Rust/Chromium execution matched **1,049 assertion events**. There is also a separately registered signed-zero hash compile-time port, checked on native and WASM targets with negative mutations. The earlier index-range embedded compile-time condition is retained. These must not be misreported as extra runtime passes.

| Source group | Runtime cases | Runtime assertions |
| --- | ---: | ---: |
| Vector maths | 17 | 68 |
| Scalar maths, bits, solvers and time | 28 | 225 |
| Index ranges, binary search and bounds | 54 | 235 |
| Bit references, bit vectors, range building and sorted indices | 32 | 521 |
| Total | 131 | 1,049 |

The complete native Rust suite has 144 runtime tests after adding three Cycles cases and ten product/safety tests. This is not a count of 144 ported Blender tests.

## Corrected inventory, still not full runtime enumeration

The current source scanner found **5,673 candidates**, including **132 reviewed mappings and 5,541 unmapped candidates**. Run [39918761201](https://github.com/596050/blended/actions/runs/39918761201) reconciled every mapped identity and original line with the pinned source checkout. Mappings consist of 131 runtime cases and one standalone compile-time case. Earlier 5,637-candidate reports are historical: C++ numeric separators incorrectly hid some declarations. Integer, floating and suffix cases now have regression coverage.

This remains a heuristic candidate count containing conditional, third-party, compile-time and unexpanded declarations. It is not the complete runtime denominator or a feature percentage. Blender's original configured `BLI_test` executable previously listed 1,644 registrations and 1,643 distinct labels, with duplicate `stack.Peek` retained as ambiguous. That is one executable/configuration, not all of Blender. Current assertion verification executes the selected mapped subset, not all 1,644 registrations.

## Evidence and reproduction

[Assertion methodology](ASSERTION-FIDELITY.md) · [New collection/static verification](COLLECTION-PORT-VERIFICATION.md) · [Completion issue #3](https://github.com/596050/blended/issues/3).

Reviewed source/target hashes are in `compatibility/assertion-contracts.lock.json`. Runtime provenance is in the vector, additional, structure and collection manifests; standalone compile-time provenance is in `compatibility/compile-time-ports.json`. Frozen original tests are under `tests/upstream/blender`. Raw C++/Rust/WASM transcripts are on `assertion-fidelity-evidence`, public results on `test-port-evidence`, and corrected inventory evidence under `evidence/collection-integration/INVENTORY-VERIFIED.json`.

```sh
cargo test --locked --workspace --all-targets
python3 tools/fetch_upstreams.py blender
python3 tools/port_scalar_tests.py
python3 tools/port_structure_tests.py
python3 tools/port_collection_tests.py
python3 tools/inventory.py --root .upstream/blender --name blender --commit 94363991e7dcf39e2d70614aa002ab6f67764a5d --output build/blender-inventory.json
python3 tools/test_port_audit.py --inventory build/blender-inventory.json --output evidence/complete-test-port.json --require-complete
```

The last command MUST currently exit nonzero. Do not wrap it as an expected failure, use `continue-on-error`, reduce its scope or treat passing subset checks as complete.

The collection batch's test-first run `39914938956` failed because its implementation/module was missing, not because 32 assertions had run and failed. Later runs established native, original-reference and deployed success. Historic failed runs remain preserved.

## Fixture recovery is not execution

Run `39847680248` downloaded and SHA-256/size-verified all 6,691 LFS objects under pinned `tests/files/**`: 870,496,042 bytes including 2,145 .blend files. Durable per-object metadata is at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, `fixture-evidence/`. Large payloads were not committed as repository blobs or retained as large billable artifacts.

A fresh checkout still has pointers until the actual execution job materialises the required inputs. Other dependencies, including 24 .blend pointers outside tests/files, need separate verification. A previous hash-verified download is neither a current fixture nor a passed test. The completeness audit intentionally reports the state of its own checkout, so historical download success does not override unresolved current dependencies.

## Outstanding requirements

1. Build/discover all required native reference configurations and test families. Preserve CTest, GoogleTest, Python/runner-specific discovery, disabled tests, generated/typed/parameterised instances and build options. Reconcile ambiguity and unreadable/template sources explicitly.
2. Port every remaining assertion, fixture, setup/teardown and failure semantic. Mesh/BMesh, modifiers, nodes, dependency graph, file I/O, animation, rigging, simulation, render, compositor, Python and UI cases are not covered by this library subset.
3. Execute the exact mapped universe natively and in browsers, binding evidence to implementation/reference revisions, fixture hashes, browser/device configuration and comparison policies. Resolve compile-time requirements separately rather than fabricating runtime passes.
4. Materialise required dependencies in the execution jobs and retain relevant output evidence. Rendering tolerances, colour management, sampling and backend differences need explicit contracts.
5. Make the whole-suite gate pass legitimately. Separately evaluate feature/workflow compatibility, browser/device behaviour and performance. A complete test port, complete test conformance and full application feature parity are different milestones.

The working Three.js modeller has not been replaced by the test workbench. This workbench exercises the Rust compatibility core, not a complete Blender modelling/rendering application.
