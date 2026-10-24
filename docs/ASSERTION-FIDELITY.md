# Assertion-level fidelity

## Current verified subset

[Run 40045600207](https://github.com/596050/blended/actions/runs/40045600207), source `059bfb9b277e8bc5aefb9834dd671879094a0599`, checks **416 Blender runtime cases and 33,368 assertion events** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium WebAssembly comparisons pass. Eight native and nine browser colour differences are explicitly retained within original floating rules. No tolerance was widened. This is not bitwise equality or a complete-suite certificate.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40045600207/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40045600207/browser-comparison.json) · [Raw transcripts and build metadata](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40045600207)

## Preservation and comparison

Registered identities map to pinned source snapshots and reviewed target hashes. Generators reproduce committed translations from original sources. The executable registry must match the reviewed contracts exactly. Six compile-time mappings remain separate. Missing work stays visible to the completeness audit.

Original C++ bodies are unchanged. An include-only diagnostic overlay records evaluated operands once and invokes pinned GoogleTest assertions. Rust instrumentation uses an explicit shadow build; production tests and implementations are not edited. Case boundaries, assertion order, kinds, operands, results and counts are compared. Assertion-free smoke cases have boundary and negative-execution checks rather than fabricated assertions.

Exact equality remains exact. Original near tolerances and floating-equality ULP rules are preserved. Numeric representation, symmetric equality operand order, upstream empty-range equality and relative pointer encodings have documented normalisations. Ordered comparisons do not allow operand reversal. Fatal assertions retain stop-on-failure behaviour. New C-string assertions use the explicit STREQ kind; original array helpers expand to the same number of individual assertions. Whole-span equality remains one event containing all compared values.

The diagnostic Chromium run is separate from deployment. Production WebAssembly is freshly built, published and tested at the actual immutable URL, with independent case identities, counts and binary SHA-256 checks.

## Supplemental evidence, not inflated upstream counts

The latest data batch retains the original 100,000-element group inputs and masks. An unedited original-C++ hash oracle matches 31,776 results across 10,592 explicit streaming configurations exactly in Rust and browser WebAssembly. Four deliberately broken implementations are detected by unchanged source tests while controls pass. Compilation failures, panics and traps do not satisfy negative assertion checks. [Data verification](DATA-PORT-VERIFICATION.md)

Prior heap verification checks exact original random inputs and mutations; prior sampling verification checks borders, endpoints and execution of the original infinity-input smoke call. Their evidence remains separately scoped in [HEAP-PORT-VERIFICATION.md](HEAP-PORT-VERIFICATION.md) and [SAMPLING-PORT-VERIFICATION.md](SAMPLING-PORT-VERIFICATION.md).

Infrastructure regressions reject missing/extra/reordered cases, changed assertions, widened tolerances, false success flags, stale references, altered hashes and fabricated runtime denominators. Hashes and transcripts establish the exercised contracts, not every possible input or native implementation detail.

## Completion remains separate

The whole-suite completeness job still fails. This subset does not establish unported-family coverage, full Blender feature parity, cross-browser parity or competitive performance. Historical verification runs retain their original scope and are not substituted for current combined-build evidence.
