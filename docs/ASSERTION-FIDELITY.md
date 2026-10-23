# Assertion-level fidelity

## Current verified subset

Run [40007823640](https://github.com/596050/blended/actions/runs/40007823640), source `8bb0e6e43237cc68cf5e3c403dfc0b9419f083ed`, verifies **338 Blender runtime cases and 16,804 assertion executions** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Both native Rust and Chromium WebAssembly comparisons pass. Eight native and nine browser differences are explicitly recorded within original floating-point comparison rules. This is not a bitwise-equivalence or full-suite certificate.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40007823640/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40007823640/browser-comparison.json) · [All raw evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40007823640)

## Preservation and comparison rules

Each registered upstream identity maps to a reviewed source snapshot and Rust target hash. The generators must reproduce the committed translations from pinned originals. The executable registries must form an exact bijection with the reviewed runtime contracts. Six tracked compile-time assertions remain separate from runtime counts; missing compile-time and runtime work is retained by the completeness audit.

The original C++ test bodies are unchanged. An include-only diagnostic overlay records evaluated operands once and still invokes the bundled pinned GoogleTest machinery. Rust recording occurs in an explicit shadow build; production tests and implementations are tested separately. Both sides record case boundaries and ordered assertion kinds, operands, outcomes and counts. An assertion-free original smoke case has explicit boundary and negative-execution checks rather than fabricated assertions.

Exact equality remains exact. Original scalar near tolerances and floating-equality ULP rules are preserved. Literal floating expectations are fixed. Numeric representation, symmetric equality operand order, upstream empty-range equality and cross-process relative pointers have documented normalisations. All accepted numeric differences are listed, not hidden. Fatal assertions retain their stop-on-failure behaviour, with native/WASM mutation evidence.

The diagnostic Chromium run is not a deployed-site test. The production workbench is separately built, published and executed at its immutable public URL, with expected identities, assertion counts and WebAssembly SHA-256 checked independently of its displayed status.

## Negative controls

Infrastructure regressions reject omitted/extra/reordered cases, changed assertions, broadened tolerances, fake pass flags, stale pins, altered source hashes and fabricated runtime denominators. Implementation-level probes additionally show that wrong image borders and wrong curve endpoint spacing fail unchanged upstream assertions, and that the original nonfinite-coordinate smoke call still executes. [Sampling details and evidence](SAMPLING-PORT-VERIFICATION.md)

## Completion is separate

The full-completeness gate is still failed. A verified subset cannot establish coverage of unported Blender test families or prove complete feature or performance parity. Historical 99-, 131-, 211-, 272- and 302-case results are evidence of those earlier scopes, not substitutes for the current combined run.
