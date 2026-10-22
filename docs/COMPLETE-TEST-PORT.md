# Complete Blender test-port requirement

## Current result: incomplete

The acceptance target is the complete test suite at Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`. A passing subset is not an acceptable substitute. Upstream declarations, parameter expansions, fixture instances, assertions and their semantics all need traceable destinations. Unsupported, unavailable, ignored, unreviewed and unexecuted work must remain visible.

As verified in run `39849051906`, 45 Blender runtime cases execute successfully natively and in actual browser WebAssembly. The 28 new cases preserve all 225 explicit assertions from five complete upstream files:

| Source file | Cases |
| --- | ---: |
| BLI_math_base_test.cc | 17 |
| BLI_math_base_safe_test.cc | 3 |
| BLI_math_bits_test.cc | 2 |
| BLI_math_solvers_test.cc | 5 |
| BLI_math_time_test.cc | 1 |

The original vector-maths slice contributes 17 more runtime cases. Its separate signed-zero hash static assertion is still unported. There are also 3 Cycles native cases, 6 product geometry cases and 4 safety cases. The native total is therefore 58; it is not a count of 58 ported Blender cases.

The source audit retains 5,637 candidate declarations, of which 45 have reviewed mappings and 5,592 do not. This candidate set contains static assertions, third-party code and unexpanded parameterised declarations. It is NOT a complete runtime denominator or a feature-parity percentage. The full native reference build and runtime enumeration remain unfinished.

## Evidence and commands

- Test-first red run: `39846695564`. The newly generated integration tests failed to compile because the corresponding module was not yet implemented. This was a missing-implementation failure, not 28 observed assertion failures.
- Initial passing native/WASM run: `39848464324`.
- Passing deployed subset and explicitly failing full-completeness gate: `39849051906`.
- Actual public test results: branch `test-port-evidence`, `result.json`.
- Reviewed hashes: `compatibility/assertion-contracts.lock.json`.
- New case provenance: `compatibility/additional-ports.json`.
- Frozen source tests: `tests/upstream/blender/`.
- Full source-candidate ledger: `evidence/test-port/source-audit.json` and the `audit.json` in each published test-port build. Older reports are historical and keep their recorded schema.

```sh
cargo test --locked --workspace --all-targets
python3 tools/fetch_upstreams.py blender
python3 tools/port_scalar_tests.py
python3 tools/inventory.py --root .upstream/blender --name blender --commit 94363991e7dcf39e2d70614aa002ab6f67764a5d --output build/blender-inventory.json
python3 tools/test_port_audit.py --inventory build/blender-inventory.json --output evidence/complete-test-port.json --require-complete
```

The last command MUST currently exit nonzero. Do not replace it with an expected-failure wrapper, `continue-on-error`, a reduced denominator or success based only on the implemented subset.

## Assertion fidelity

The five-file generator is deliberately source-hash locked and narrowly scoped. It refuses changed inputs and compares source assertion counts with generated assertion counts. It preserves literal values, exact comparisons, GoogleTest four-ULP float comparisons, original near-comparison tolerances and nonfatal assertion collection. Optional C output pointers in the time test are represented by an explicit mask; solver output arrays use checked Rust slices. Unsigned C++ hex constants retain their unsigned value in Rust.

Every assertion-code change invalidates its reviewed target hash and blocks subset publication until reviewed. Hashes and assertion counts detect drift; they are not an automatic proof that an arbitrary translation is semantically equivalent. New test families require appropriate reviewed adapters, not generated placeholders that merely share upstream names.

## Fixture recovery

Run `39847680248` fetched all 6,691 LFS objects under the pinned `tests/files/**` tree and verified each SHA-256 and byte count. Total verified payload: 870,496,042 bytes. This includes 2,145 `.blend` files, image references, interchange files and simulation caches.

Durable object-by-object evidence is committed at `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, under `fixture-evidence/`. The publishing workflow reads that immutable commit, not an expiring Actions artifact. The large payloads were not committed to this repository or retained as billable large artifacts.

This verification establishes availability and integrity for that scope and run. It does not execute the tests. A fresh source checkout still contains pointers until the fixture-resolution workflow is run; the audit reports the state of its own checkout. Other required assets, including 24 `.blend` pointers found outside `tests/files`, need separate dependency verification. Do not label all possible test dependencies resolved from the `tests/files` result alone.

## Required remaining work before completion

1. Build the exact native Blender reference with the required test configuration. Preserve build options and raw `ctest --show-only=json-v1`, GoogleTest listings and runner-specific discovery outputs.
2. Reconcile every enabled/disabled/conditional, typed, parameterised, Python-generated, render-scene, UI and compile-time test with source discovery. Record configurations and instantiated fixture identities. Explicitly review the source scanner's unreadable/template files rather than losing them.
3. Port all remaining assertions and setup/teardown semantics. Mesh/BMesh, modifiers, geometry nodes, animation, armatures, constraints, simulation, file I/O, dependency graph, rendering, compositor and Python workflows are not covered by the current maths slice.
4. Compile and discover the replacement tests natively and in the browser. Bind execution evidence to exact implementation and reference revisions, fixture hashes, environments and comparison policies. Missing implementations are failed/blocked work, never success.
5. Resolve the relevant fixture dependencies in the actual execution jobs. Keep render tolerances, colour management, sampling and backend assumptions explicit.
6. Execute the complete suite and additional end-to-end/browser/device/performance checks. A complete test port and complete test conformance are separate milestones. Neither alone proves that every Blender feature is reproduced; the broader feature/workflow catalogue remains a separate acceptance requirement.

The working Three.js modeller deployment has not been replaced by the conformance workbench. This workbench tests the Rust compatibility core, not Blender's complete modelling or rendering application.
