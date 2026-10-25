# Assertion-level fidelity

## Current verified subset

[Run 40149763130](https://github.com/596050/blended/actions/runs/40149763130), source `f86fae88ce889175fcaa11dcb982d3bbc4fce5ca`, verifies **596 Blender runtime cases and 3,196,692 assertion events per implementation** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Original C++ versus native Rust and Chromium comparisons passed. Eight native and nine browser differences remain in older colour cases under the original rules. The new mask cases add none and no tolerances were widened. This is not full-suite or universal bitwise equivalence.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/browser-comparison.json) · [Complete execution evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40149763130).

## Source and execution contracts

Original identities map to pinned snapshots, body/input provenance and reviewed target hashes. Generators reproduce committed translations. Required assertion-contract shards and the explicit runtime registry form a bijection. Nineteen compile-time predicates remain separately mapped and verified; their required union cannot silently shrink. Disabled or unsupported work remains in the completeness audit, never treated as passing.

Include-only C++ instrumentation leaves original test/helper bodies unchanged, evaluates operands once and invokes the original GoogleTest assertions. Rust recording uses a separate diagnostic shadow, not changed production tests. Executed case boundaries, ordered comparison kinds, operands, outcomes, counts and tolerances are reconciled. The static-only span declaration and earlier assertion-free bit-span case retain zero runtime assertions, with independent compile/execution evidence rather than invented checks.

Exact equality remains exact. Original near tolerances and floating-equality rules are retained. Literal expectations are fixed. Numeric representation, symmetric equality operand order, upstream empty-range equality and cross-process pointer relationships have documented normalisations. Ordered comparisons cannot reverse operands. Fatal assertions retain their stopping behaviour with negative-execution evidence. Every permitted numerical difference stays listed.

## Full masks, not counts or hashes

An index mask's assertion operand includes its entire selected set, losslessly encoded as canonical maximal runs and unsigned LEB128 gap/length bytes. Native adjacent ranges are merged independently of their physical segmentation. Different equal-cardinality masks produce different exact records. This is a reversible representation, not a hash, sample or approximate summary. Tests explicitly reject altered membership and corrupted encodings.

The same original test may generate expected masks from its own randomized inputs, so successful assertions alone do not prove the fixtures were preserved. A required independent original-C++ listener calls the unedited helper and records all 14,573,457 Boolean inputs. A separate corpus records absolute input configurations and 147,456 expression results, including all 370,176 selected-index values. C++, native Rust and Chromium tapes match byte-for-byte. [Oracle report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/mask-comparison.json).

An initial out-of-domain supplemental input was rejected by the pinned static constructor and publication stopped. The corrected supplemental corpus respects the original bound without modifying original tests. Larger Rust-only capabilities are not claimed as parity with that rejected reference path. [Scope and retained failure](MASK-EXPRESSION-PORT-VERIFICATION.md).

## Full-event processing and independent negative evidence

Every assertion event, including millions from earlier UTF-8 and polygon loops, is compared in bounded batches. No event sampling, deduplication or hash-only replacement is used. Missing, extra, reordered, substituted and out-of-case events fail. Hashes before/after guard transcript integrity but do not replace operand comparison.

Chromium runs the full diagnostic module and transfers its complete tape in bounded chunks. Diagnostic memory is not claimed to be universally constant. Full transcripts are preserved losslessly as `.jsonl.gz`, with decompressed sizes and SHA-256 checked before removing duplicate raw files. Independent binary oracle outputs are also retained.

Implementation-only mutation probes retain original test bodies and expected counts. Incorrect union, intersection and subtraction are detected while independent controls pass. Compiler failures, panics and browser traps are not valid assertion-failure evidence. Earlier input, bit-format, hash, string, pointer and compiler-negative checks remain in the pipeline. Supplemental observations and probes are not additional upstream cases.

The production module is separately built, published and tested at its **actual immutable public URL**, verifying case identities, counts, source/reference revisions and WASM digest independently of displayed status. A successful local diagnostic browser run is not substituted for deployed acceptance.

## Completion remains separate

Whole-suite completeness still fails. The verified subset does not establish unported-family coverage, every possible input, all platform behaviours, complete Blender features or competitive performance. Historical reports retain their source/configuration/scope and cannot replace current combined verification.
