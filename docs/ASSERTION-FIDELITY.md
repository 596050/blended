# Assertion-level fidelity audit

## Verified scope, not full-suite completion

Run [39863583391](https://github.com/596050/blended/actions/runs/39863583391) independently executed all 99 currently mapped Blender runtime cases against the pinned original C++ implementation, the Rust implementation and Chromium WebAssembly. It compared 528 assertion events per implementation. Both comparisons passed, with no floating-value differences requiring a tolerance allowance after the documented representation normalisations.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/browser-comparison.json) · [Raw transcripts and build evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence)

Reference: Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Initial audited project revision: `ea27fbae46cb12abfaceed5ff4185f90df46b71b`.

**This does not certify the entire Blender test suite.** The remaining source/runtime families, parameter expansions and the vector file's signed-zero hash compile-time assertion are still outside this verified runtime subset. Existing Cycles and product tests are also not counted in the 99-case Blender transcript comparison. The separate full-completeness gate must remain failed until its outstanding requirements are genuinely fulfilled.

## What is compared

The audit reconciles each case's ordered assertion events, not just a successful exit code or a total count. It verifies the assertion kind, operand values, outcome, expected execution count and near-comparison tolerance. Dropped, duplicated, reordered or substituted assertions are errors. Literal floating-point expectations are fixed exactly; computed floating outputs may only differ under the original comparison rule, and every such difference is reported. None occurred in the verified run.

The representations normalise equivalent integer/float values, allow operand reversal for symmetric comparisons, and ignore the start of an empty IndexRange because the upstream equality operator does. They do not relax exact equality, change tolerances or claim bitwise equality of all internal structures.

## Independent reference and diagnostic overlays

The original BLI test executable is built from pinned Blender sources and pinned library submodules. Nine source files receive only an extra recording-header include after source hashes are verified. Their original test bodies remain unchanged. The wrapper evaluates arguments once, records their values and invokes Blender's bundled GoogleTest assertions. Raw original GoogleTest XML, compiler information, binary hashes and overlay metadata are preserved.

Rust assertions are recorded in a separate build-only shadow checkout. The checked-in production tests and implementation are not edited by the audit. The instrumentation patch and input hashes are saved. The same shadow module runs natively and in Chromium WebAssembly. This diagnostic browser run is local CI execution, not a new public deployment. The production workbench is separately built, deployed and exercised at its actual public URL.

The pinned GoogleTest version is the authority. Do not silently change assertions to match newer documentation; even infinity handling in EXPECT_NEAR can differ by version.

## Failure-detection tests and publication

Negative tests exercise missing cases, wrong identities, removed/duplicated/reordered assertions, changed comparison kinds, changed actual or expected values, changed tolerances, false success flags and count-only stubs. These are tests of the audit, not additional Blender features or upstream ports.

The compatibility-workbench publishing job requires both ordinary native/WASM conformance and the independent assertion-fidelity workflow. The full-suite completion job remains a separate, genuinely failing requirement. Publishing a clearly labelled alpha subset is not a full-parity release.

## Reproduction

```sh
python3 -m unittest discover -s tests -p test_assertion_fidelity.py -v
python3 tools/assertion_fidelity.py shadow --output build/fidelity-shadow
(cd build/fidelity-shadow && cargo run --locked --quiet -p blended-core --example assertion_trace) > native.jsonl
python3 tools/assertion_fidelity.py compare --reference reference.jsonl --port native.jsonl --output comparison.json
```

The CI workflow records the full original-reference build and browser commands. Case counts, source hashes and expected assertion counts are taken from the checked-out contracts, not trusted from a served dashboard. Hashes and transcripts provide concrete evidence for the exercised cases; they are not a mathematical proof of every possible behaviour or a substitute for porting the rest of Blender.
