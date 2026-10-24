# Assertion-level fidelity

## Current verified subset

[Run 40065241089](https://github.com/596050/blended/actions/runs/40065241089), source `3969e1fdadae2e11d6f220412f8c32cabf7048d1`, verifies **503 Blender runtime cases and 1,661,377 assertion events per implementation** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium WebAssembly comparisons passed. Eight native and nine browser differences remain within original floating-point rules in earlier colour cases; the UTF-8 batch adds no floating differences. No tolerance was widened. This is not a bitwise-equivalence or complete-suite certificate.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40065241089/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40065241089/browser-comparison.json) · [Full lossless transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40065241089)

## Preservation and comparison

Registered identities map to reviewed source snapshots and target hashes. Generators reproduce committed translations from pinned originals. The runtime registry is a bijection with reviewed contracts. Six compile-time mappings remain separate. Missing work is retained in the completeness audit, never converted into a passing subset result.

Original C++ test bodies remain unchanged. An include-only recorder evaluates operands once, records values and still invokes the pinned GoogleTest assertions. Rust diagnostic recording uses an explicit shadow build, not altered production test bodies. Case boundaries, ordered assertion kinds, operands, outcomes and counts are compared. Assertion-free smoke cases require executed boundaries and negative-execution checks rather than invented assertions.

Exact equality remains exact. Original near tolerances and floating-equality ULP rules are retained. Literal floating expectations are fixed. Numeric representation, symmetric comparison operand order, upstream empty-range equality and cross-process pointer representations have documented normalisations. Ordered comparisons never permit operand reversal. Fatal assertions preserve stop-on-failure behaviour with native/browser mutation evidence. Every permitted numerical difference remains listed in the reports.

## Full-event processing, not sampling

The original UTF-8 stress case adds over 1.6 million assertions. `tools/fidelity_stream.py` indexes complete case boundaries, checks exact event counts and compares **every event** in batches through the existing reviewed comparator. Missing, repeated, reordered, substituted or out-of-case events fail. Global per-case difference ordinals are preserved across chunk boundaries. Whole-file hashes before/after detect changes during comparison; they do not replace operand comparisons.

The browser executes the full diagnostic module. Its entire ASCII tape transfers in bounded chunks rather than a giant DevTools response. The Rust recorder transfers ownership of its buffer rather than cloning it. This is not a claim that all execution memory is constant: the diagnostic module still holds its complete tape. The production workbench has no such recording requirement.

The full C++, native and browser traces are preserved as `.jsonl.gz`. All decompressed bytes and SHA-256 values are verified before duplicate raw copies are removed; `TRACE-STORAGE.json` records raw and compressed hashes/sizes. The verified raw traces are approximately 159 MB each and compress to approximately 3.5 MB each without dropping any event. Fourteen regressions test the streaming and compression boundary cases.

## Inputs and negative controls

Matching outputs does not necessarily prove that fixtures were retained. Independent original-C++ oracles now compare random-generator values and permutations, streaming-hash inputs, natural-order/search offsets and UTF-8 decoder/validator/byte-RNG outputs. The latest corpus checks all single/two-byte sequences and selected longer legacy inputs, plus every original random-buffer length. These are supplemental inputs, not additional upstream test-case counts.

Implementation-only mutation probes retain original test source and expected counts. Compiler errors, panics and browser traps cannot substitute for recorded assertion failures. New UTF-8 controls detect disabled byte substitution/copying and ignored combining marks while independent controls pass. [UTF-8 details](UTF8-PORT-VERIFICATION.md) · [String details](STRING-OPS-PORT-VERIFICATION.md) · [Data details](DATA-PORT-VERIFICATION.md) · [Heap details](HEAP-PORT-VERIFICATION.md)

The diagnostic Chromium checks are local CI execution. The production module is separately built, published and exercised at its **actual immutable public URL**, checking identities, counts, source/reference revisions and the expected WASM digest independently of the dashboard's claims.

## Completion remains separate

Whole-suite completeness still fails. This subset cannot establish unported test-family coverage, every input's correctness, full Blender feature parity or competitive performance. Historical smaller runs retain their own source revision and scope; they are not used as substitutes for the current combined verification.
