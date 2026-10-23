# Assertion-level fidelity

## Current verified subset

[Run 40019426923](https://github.com/596050/blended/actions/runs/40019426923), source `df61b87fa3b2b5a0751100e427eab11d7205ad5a`, verifies **367 Blender runtime cases and 33,104 assertion events** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium WebAssembly comparisons pass. Eight native and nine browser differences are explicitly recorded within original floating-point rules; the heap cases add no floating difference. This is not a bitwise-equivalence or complete-suite certificate.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40019426923/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40019426923/browser-comparison.json) · [Raw transcripts and build metadata](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40019426923)

## Preservation and comparison

Registered identities map to reviewed source snapshots and target hashes. Generators reproduce committed translations from pinned originals. Runtime registries form an exact bijection with reviewed contracts. Six compile-time mappings are separate; missing work remains visible to the completeness audit.

Original C++ test bodies are unchanged. An include-only diagnostic overlay records evaluated operands once and invokes pinned GoogleTest assertions. Rust recording occurs in an explicit shadow build, separate from production tests and implementations. Both record case boundaries and ordered assertion kinds, operands, outcomes and counts. Assertion-free smoke cases have boundary and negative-execution checks rather than fabricated assertions.

Exact equality stays exact. Original near tolerances and floating-equality ULP rules are retained. Literal floating expectations are fixed. Numeric representation, symmetric equality operand order, upstream empty-range equality and cross-process relative pointers have documented normalisations. Ordered comparisons such as EXPECT_LE never permit operand reversal. Fatal assertions retain stop-on-failure behaviour with native/browser mutation evidence. Accepted differences remain listed in the reports.

The diagnostic Chromium run is not a deployed-site test. The production module is separately built, published and exercised at its immutable URL, checking identities, counts and WASM SHA-256 independently of the displayed status.

## Input preservation and negative controls

Matching sorted outputs does not establish identical randomized inputs. An independently compiled original-C++ oracle now verifies all 15,000 random draws and 3,175 shuffled items exactly against native Rust and browser WebAssembly. Original shuffle rules and seeds are retained, not replaced by a standard algorithm.

Infrastructure regressions reject omitted/extra/reordered cases, changed assertions, broadened tolerances, fake pass flags, stale references, changed hashes and fabricated runtime denominators. New implementation-level probes make removal and priority increase fail unchanged source tests while controls pass. Compilation errors, panics and traps are not accepted as assertion-failure evidence. [Heap details and immutable results](HEAP-PORT-VERIFICATION.md)

Historical sampling probes check border handling, endpoint spacing and execution of the original infinity-input smoke call. [Sampling verification](SAMPLING-PORT-VERIFICATION.md)

## Completion remains separate

Whole-suite completeness still fails. This subset cannot establish unported test-family coverage, full feature parity or competitive performance. Older 99/131/211/272/302/338-case evidence retains its original scope and is not substituted for the latest combined run.
