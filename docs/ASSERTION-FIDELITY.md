# Assertion-level fidelity

## Current verified subset

[Run 40142038492](https://github.com/596050/blended/actions/runs/40142038492), source `efc7799e5050f28de66aa7ba11ed9a976165d21a`, verifies **541 Blender runtime cases and 3,196,218 ordered assertion events per implementation** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium comparisons passed. Eight native and nine browser differences remain under original floating rules in older colour cases; the polygon cases add none. No tolerances were widened. This is not a complete-suite or universal bitwise-equivalence certificate.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40142038492/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40142038492/browser-comparison.json) · [Complete lossless transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40142038492)

## Provenance, required contracts and execution

Original identities map to source snapshots, original expectations and reviewed target hashes. Generators must reproduce committed translations. `tools/contract_registry.py` reads the historical lock and explicitly enumerated required shards, rejecting missing shards, mismatched references and duplicate source identities. The polygon shard is mandatory, not discovered opportunistically by glob. The combined 39 contracts must form a bijection with the registered runtime tests, excluding separately tracked compile-time identities. The historical lock is unchanged.

Include-only C++ recording leaves original test bodies intact, evaluates operands once and invokes pinned GoogleTest assertions. Rust recording runs in a separate diagnostic shadow, not edited production tests. The comparator checks case boundaries, ordered assertion kinds, actual and expected operands, outcomes, counts and tolerances. NE records its actual operands; a different successful inequality is not automatically equivalent. Assertion-free smoke cases require executed boundaries rather than invented assertions.

Exact comparisons remain exact. Original near tolerances and floating-equality ULP rules remain. Literal expectations are fixed. Numeric representations, symmetric equality order, upstream empty-range equality and cross-process pointer encodings have documented normalisations. Ordered comparisons cannot reverse operands; fatal assertions retain their stopping behaviour. All accepted numerical differences are listed in reports.

## Full-event processing and evidence storage

Every event is compared, including all original UTF-8 stress loops and polygon helper repetitions. Bounded batches use the existing reviewed comparator without sampling, deduplication or hash-only equivalence. Missing, duplicated, reordered, substituted or out-of-case events fail. Whole-file hashes before/after detect changes during comparison; they do not replace operand comparisons.

Chromium executes the full diagnostic module and transfers its complete tape in bounded chunks. Full C++, native and browser tapes are retained as lossless `.jsonl.gz`, with decompressed hashes and byte counts verified before duplicate raw copies are removed. Diagnostic memory is not claimed to be entirely constant. The production workbench is separately built and tested at its actual immutable public URL.

## Preserve original tests, expose their gaps

The pinned polygon helper rotates and reverses a copy but passes the original polygon. The port preserves that observable behaviour, original loop count and assertions. It does not falsely claim those loops test true permutations. A separate mandatory oracle supplies genuinely transformed inputs and compares exact plain/beautified triangle sequences against original C++.

That corpus matches native Rust and Node.js WASM for 3,064 transformed configurations and 6,128 triangulation outputs, including index order. Node differential execution is not conflated with the independently verified original-case Chromium/public-URL layers. No polygon-specific implementation-mutation probe was added. [Detailed polygon report](POLYFILL-PORT-VERIFICATION.md)

Other supplemental original-code oracles continue to cover generators, shuffles, hashes, string offsets, UTF-8 behaviour and explicit graphics-format profiles. Their inputs are not extra upstream case counts. Existing implementation-mutation checks require observed assertion failures with independent controls passing; compiler errors, panics and browser traps cannot substitute for that evidence.

## Completion remains separate

Whole-suite completeness remains failed. This subset does not establish unported-family coverage, arbitrary-input correctness, complete Blender feature parity, allocator/ABI parity or competitive performance. Historical records retain their original source/configuration/scope and are not substitutes for current combined execution.
