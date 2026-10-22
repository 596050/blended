# Complete Blender test-port requirement

## Current result: incomplete, with 99 executable Blender cases

The acceptance target is the complete suite at Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`, not a green subset or a similar-looking browser modeller. Source declarations, parameter expansions, fixture instances, assertions, setup/teardown and comparison semantics need traceable destinations. Missing, unsupported, unreviewed, skipped and unexecuted work remain visible.

## Latest verified continuation, 22 October 2026

Source `5c348145f0739a3a7999ef2f69314b7a43c24785` passed 112 native Rust tests and 99 Blender cases in browser WASM. The same 99 cases passed against the actual immutable deployed URL in run `39859518789`, after one navigation attempt failed with `ERR_CONNECTION_RESET`. The failed attempt is retained in workflow history; no assertion was relaxed for the retry.

[Open the verified 99-case workbench](https://rawcdn.githack.com/596050/blended/16980ee91529017553efca51e7223354137f09be/index.html)

| Newly ported complete upstream file | Cases | Assertion sites | Runtime assertion checks |
|---|---:|---:|---:|
| BLI_index_range_test.cc | 32 | 120 | 123 |
| BLI_binary_search_test.cc | 3 | 20 | 20 |
| BLI_bounds_test.cc | 19 | 86 | 92 |
| Total added | 54 | 226 | 235 |

The different site/execution totals preserve repeated assertions inside the original loops. The index-range constexpr test also retains its compile-time array-size check and `BLI_STATIC_ASSERT` equivalent. This additional compile-time condition is not counted as another runtime test.

The previous 45 Blender cases are retained: 17 vector cases and 28 scalar/bits/solver/time cases. Their runtime assertion checks are now explicitly counted as 68 and 225 respectively. Together, the 99 cases represent 528 runtime assertion checks. The runner invokes cases again to obtain counters; repeated invocations do not increase coverage counts.

The native total is 112: 99 Blender, three Cycles integer-maths cases, six product geometry cases and four safety cases. Tooling tests and existing Solarxy tests are separate and are not counted as Blender ports.

## Assertion-fidelity correction

The earlier vector port short-circuited Boolean expressions after a failed comparison and used exact integer equality in three cases whose upstream assertions were `EXPECT_FLOAT_EQ`. Its passing results were valid for the exercised inputs, but its failure-collection and comparison semantics were not a literal match.

The corrected vector port collects all 68 nonfatal assertions and preserves four-ULP floating-point comparisons, original near tolerances, exact comparisons and NaN/infinity expectations as applicable. Its frozen source and per-case counter contract are committed. The separate vector signed-zero hash `static_assert` is still unported; this is not described as a complete port of that file.

## Actual upstream runtime reference

The pinned native `BLI_test` executable was built using Clang 18.1.3 and pinned Linux libraries `2b5fbb917a1bf7537cb25456fcb9064302d7e168`. Its CMake configuration, executable hash, library resolution, raw GoogleTest listing, CTest registrations and original XML output are preserved.

Run `39858339699` executed the original 54 range/search/bounds cases successfully. Its initial report-processing step failed because the full upstream listing contains two registrations named `stack.Peek`. A regression-tested parser correction preserves both occurrences and reports the ambiguity instead of silently discarding either. Run `39860100156` reconciled the unchanged raw evidence successfully.

Durable evidence: [`07b2fd18d4fb15f83ddadbfb19acbd3a8a977bcb`](https://github.com/596050/blended/tree/07b2fd18d4fb15f83ddadbfb19acbd3a8a977bcb).

The listing contains 1,644 registrations and 1,643 distinct labels. This is discovery for one configured executable, not 1,644 passing or ported tests. Only the selected 54 were executed in that reference run. Their identities exactly match the new Rust port, without omitted or unexpected cases. The 26 CTest registrations do not establish that every registered executable was built or tested.

The configuration is explicitly limited: headless/lite, Python and renderer features disabled. Other modules, feature configurations, typed/parameterised instantiations, Python, UI, rendering and data-dependent test families still require discovery and reconciliation. The duplicate `stack.Peek` identity remains a full-inventory reconciliation issue outside the selected families.

## Coverage ledger and publication gates

The source scanner still reports 5,637 candidates. There are 99 reviewed runtime mappings and 5,538 unmapped source candidates. This heuristic set includes compile-time assertions, third-party code and unexpanded declarations, and misses some macro-based constructs. It is not a runtime denominator or a feature-parity percentage.

`full-test-port-completeness` remains a real failed job. Do not convert it into an expected failure, use `continue-on-error`, remove unavailable cases or present a green subset as complete.

The separate passing-subset gate checks pinned source hashes, regenerated test bodies, reviewed target hashes and the exact identities in the executable registry. Browser acceptance derives its expected universe from the checked-out source rather than trusting the served page's count. Missing/substituted identities, changed assertion counts, source/reference mismatches and a WASM/manifest hash mismatch fail verification.

The workbench is not the modeller. It exercises the Rust compatibility core; it does not implement or validate Blender's complete interactive application or Cycles/EEVEE.

## Commands and evidence

```sh
cargo test --locked --workspace --all-targets
python3 tools/fetch_upstreams.py blender
python3 tools/port_scalar_tests.py
python3 tools/port_structure_tests.py
python3 tools/inventory.py --root .upstream/blender --name blender --commit 94363991e7dcf39e2d70614aa002ab6f67764a5d --output build/blender-inventory.json
python3 tools/test_port_audit.py --inventory build/blender-inventory.json --output evidence/complete-test-port.json --require-complete
```

The last command must currently exit nonzero. Source-locked mappings are in `compatibility/`, frozen originals in `tests/upstream/blender/`, and executable tests in `crates/blended-core/tests/`. Use `tools/reference_inventory.py` on preserved raw native evidence, or the manual `native-reference.yml` workflow for a fresh native build/run. The structure test-first run was `39856003373`: failure was missing implementation/module compilation, not 54 observed assertion failures. Native implementation run `39856502278` passed.

## Fixture recovery

Run `39847680248` downloaded and hash/size-verified all 6,691 LFS assets under pinned `tests/files/**`: 870,496,042 bytes, including 2,145 `.blend` files. Durable metadata is at commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`, under `fixture-evidence/`. Large payloads were not committed or retained as large billable artifacts.

This establishes availability and integrity for that scope and run, not execution. Fresh checkouts contain pointers until materialised. Other dependencies, including 24 `.blend` pointers outside `tests/files`, still need separate verification. The new reference build also fetched required startup assets, but does not establish all application test dependencies.

## Remaining completion requirements

1. Extend actual runtime discovery beyond the configured BLI executable; reconcile conditional, generated, typed/parameterised, Python, render, UI and compile-time families and ambiguous identities.
2. Port all remaining assertions and setup/teardown faithfully. Mesh/BMesh, modifiers, Geometry Nodes, dependency graph, animation, rigging, simulation, file I/O, rendering, compositing and Python/UI workflows are not covered by this maths/data-structure slice.
3. Bind execution to exact implementation/reference revisions, fixture hashes and environments. Resolve dependencies in the jobs that execute each case, not only in an earlier download audit.
4. Verify complete native and browser test discovery, all mapped cases and broader end-to-end/device/performance behaviour. Complete test translation and complete conformance are different milestones; neither proves every application feature.

Completion blocker [#3](https://github.com/596050/blended/issues/3) remains open.
