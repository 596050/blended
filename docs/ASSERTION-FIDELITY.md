# Assertion-level fidelity

## Current verified subset

[Run 40108130160](https://github.com/596050/blended/actions/runs/40108130160), source `2990e30077e368c97e3a7af60d45d7a911ceb988`, verifies **512 Blender runtime cases / 1,661,546 assertion events per implementation** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium comparisons passed. Eight native and nine browser differences remain within original floating rules in older colour cases. The latest format cases introduce no additional differences and no tolerances were widened. This is not full-suite or universal bitwise equivalence.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40108130160/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40108130160/browser-comparison.json) · [Complete lossless transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40108130160)

## Preservation and execution

Original identities map to reviewed source snapshots and target hashes. Generators reproduce committed translations from pinned originals. Runtime registries and reviewed contracts are bijective. Six compile-time mappings remain separate, and conditional/performance cases outside the configured subset remain explicitly unported. Missing work never becomes a passing subset result.

Include-only C++ recording leaves original test bodies unchanged, evaluates arguments once and invokes pinned GoogleTest assertions. Rust recording uses a separate diagnostic shadow, not altered production tests. Case boundaries, ordered assertion kinds, operands, outcomes and counts are compared. Assertion-free smoke cases require executed boundaries and negative checks rather than fabricated assertions.

Exact equality stays exact; original near tolerances and floating-equality ULP rules remain. Literal expectations are fixed. Numeric representation, symmetric equality order, upstream empty-range equality and cross-process pointer identities have documented normalisations. Ordered comparisons cannot reverse operands. Fatal assertions retain stop-on-failure behaviour with negative-execution evidence. Every accepted numerical difference remains listed.

## Full-event processing

The earlier UTF-8 stress case contributes over 1.6 million events. Every event is compared in bounded batches using the reviewed comparator, without sampling, deduplication or hash-only equivalence. Missing, duplicated, reordered, substituted and out-of-case events fail. Whole-file hashes before/after detect changes during comparison but do not replace operand comparisons.

Chromium executes the full diagnostic module and transfers its complete ASCII tape in bounded chunks. The Rust recorder transfers buffer ownership rather than cloning it; this is not a claim that all diagnostic memory is constant. Full C++, Rust and browser tapes are retained as `.jsonl.gz`, with complete decompressed hashes and sizes verified before removing duplicate raw files. `TRACE-STORAGE.json` records both representations.

## Supplemental input and bit-level evidence

Matching outputs may conceal altered inputs. Original-C++ oracles separately check the pinned generators/shuffles, streaming hashes, string/search offsets and UTF-8 decoding/validation. The new graphics-format oracle compiles unedited original code and compares every half encoding plus explicit rounding, raw-component and array-tail corpora. All 2,944,570 output words are identical on native Rust and browser WASM for the named scalar/SSE2/SSE4.1 profile.

This supplemental bitwise check preserves signed zero and NaN payloads that numeric equality does not distinguish. It does not imply all platform-specific payloads must be identical: F16C/NEON are separate configurations, and upstream permits NaN-payload differences. Native x86_64 tests genuinely set/restore FTZ/DAZ control; WebAssembly explicitly reports that hardware control unavailable and checks outputs only. [Detailed profile and limits](PIXEL-FORMAT-PORT-VERIFICATION.md)

Implementation-only mutations keep original test bodies and assertion counts unchanged while making specific operations fail. Compiler errors, panics and browser traps do not substitute for observed assertion failures. Independent controls must still pass. Supplemental corpora and mutation checks are not extra upstream cases.

The diagnostic browser checks run locally in CI. The production module is separately built, published and exercised at its **actual immutable public URL**, validating identities, counts, source/reference revisions and WASM digest independently of the dashboard's status.

## Completion remains separate

Whole-suite completeness still fails. This subset does not establish unported-family coverage, every possible input, complete Blender features or competitive performance. Historical runs retain their source/configuration/scope and are not substituted for current combined verification.
