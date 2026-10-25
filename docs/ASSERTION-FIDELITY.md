# Assertion-level fidelity

[Run 40145587317](https://github.com/596050/blended/actions/runs/40145587317), runtime source `8952a0ef18a83bb7a56656dd8519095bd0fb2cd2`, verifies **581 Blender runtime cases and 3,196,371 assertion events per implementation** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium comparisons passed. Eight native and nine browser floating differences remain in older colour tests under their original rules; no tolerance was widened and the span cases add none.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40145587317/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40145587317/browser-comparison.json) · [Full lossless transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40145587317).

## Required identity and source contracts

Original identities, paths, source/body hashes and reviewed target hashes are preserved. Generators must reproduce committed test bodies. Runtime registries form an exact bijection with the reviewed runtime contracts. Required polygon and span contract shards augment, rather than overwrite, the historical base lock.

Nineteen compile-time predicates are independently mapped by the required union of `compile-time-ports.json` and `span-static-ports.json`. Positive/negative compiler checks execute for both native and wasm32. The original static-only `span.ImplicitConversions` case retains zero runtime assertions; its case boundaries are executed, and its eight actual conversion constraints are compiled. No runtime Boolean replaces those type properties. The earlier assertion-free `bit_span.SetEmpty` retains its own execution probe.

## What is compared

Original C++ bodies remain unchanged. Include-only recording evaluates operands once and invokes pinned GoogleTest assertions. Rust diagnostic recording uses a separate shadow build. Case boundaries, ordered assertion kinds, operands, results, counts and tolerances are reconciled. Fatal assertions preserve their stop-on-failure semantics.

Exact comparisons remain exact, literal expectations are fixed, and original near/ULP rules remain unchanged. Documented representation normalisations handle symmetric equality order, empty-range equality and cross-process pointer identities. Ordered comparisons never permit operand reversal. Actual pointer equality is tested before recording pair-local alias labels; supplementary oracles compare numeric offsets and live aliasing separately.

Every event is compared in bounded batches, including the full UTF-8 and polygon stress loops. No sampling, repetition removal or hash-only equivalence is used. Complete transcripts are stored losslessly as `.jsonl.gz`, with decompressed hashes and sizes verified. These integrity hashes do not replace the actual value comparisons.

## Independent evidence beyond original examples

Pinned original-C++ oracles separately check random inputs, streaming hashes, string/search offsets, UTF-8 operations, graphics formats, polygon index sequences and span aliasing. The latest span corpus matches all 473,659 observations exactly on native Rust and Chromium. Supplemental observations and mutation probes are not additional upstream cases.

The span oracle exposes an original type-trait/constructor discrepancy: a declared mutable pointer-span conversion cannot actually instantiate in the pinned C++ header. The declared predicate is ported, but the broken constructor is explicitly excluded from executable-equivalence claims. The Rust implementation of that capability is documented separately. [Span details](SPAN-PORT-VERIFICATION.md).

Implementation-only mutation checks keep original test bodies/counts intact, require intended assertion failures and passing independent controls, and reject compiler errors/panics/traps as substitutes. Separately, deliberately false static predicates must be rejected by the intended compiler diagnostic, not an arbitrary build failure.

Production WASM is built independently of diagnostic instrumentation and tested at its actual immutable public URL, checking identities, counts, source/reference revisions and module digest. Local diagnostic Chromium execution does not replace deployed-site verification.

## Completion remains separate

The complete Blender test port, all-input correctness, every platform/configuration, full application features and performance parity are not established. The whole-suite completeness job remains failed. Earlier evidence retains its historical revision and scope rather than being substituted for the latest combined run.
