# Multivalue maps and type-erased views: verification

## Verified scope

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Runtime project source: `7a3dec93c2c02605834330b5de6872d6f1dbe4ad`.
Verification: [run 40209288469](https://github.com/596050/blended/actions/runs/40209288469).

Both original source files are completely mapped:

| Original file | Runtime cases | Assertion executions |
| --- | ---: | ---: |
| BLI_multi_value_map_test.cc | 9 | 34 |
| BLI_generic_span_test.cc | 4 fixture cases | 18 |
| Added | 13 | 52 |

The combined suite contains **609 unique Blender runtime cases / 3,196,744 ordered assertion events**. Fresh native Rust, original C++ comparisons and Chromium WebAssembly comparisons passed. The production module also passed every mapped case at its [actual public URL](https://rawcdn.githack.com/596050/blended/55479ba6a6249846abc4c36d36440b27bfe106b4/index.html), with no recorded browser errors. Its WASM SHA-256 is `41757bbfe2e5a6811be1e3a0271585a6780ad54004fe7bf1ca83f82357df0a7b`.

The native Rust total is **679 runtime tests: 609 Blender, three Cycles and 67 separate product/safety/regression tests**. Nineteen compile-time predicates pass positive and deliberately false checks separately on native and wasm32. The whole-suite completeness job remains genuinely failed.

## Original assertions and implementation

Original file hashes are preserved in the required `compatibility/container-view-assertion-contract.lock.json` and source snapshots. The multivalue-map source SHA-256 is `858a23ba5f319ca69f0c675e1bce0a22cb1886bdd377115f79e8dbaed95ade26`; the generic-span source is `82a5c3d10cdc7a7665df1b0900ef50fcbbea4bfd538be90f6c1ea761ecf92b16`. The reviewed Rust test SHA-256 is `81c2e6de279b3fdb9e70259f59b6f9762dba75686103356461935c9dc9737c8c`.

`tools/port_container_view_tests.py` is a finite reviewed adapter, not a general translator. It requires the complete pinned source, preserves all identities, source lines, body hashes and expected values, and reproduces the committed test bodies. The original spelling `LookupNotExistant` is retained. All 52 nonfatal assertions remain. Four `TEST_F` cases retain once-per-suite registration, not extra runtime assertions.

The map implementation stores a value list per key. It preserves within-key insertion order and duplicates, creates real empty buckets for empty additions, and does not insert on a missing lookup. Mutable lookups and mutable iteration expose actual stored values, not detached copies. Clones own independent lists. Owning pointer keys use address identity: two separately allocated integers with the same value remain different keys, unlike the default pointee-value equality of Rust Box.

Generic views carry an exact runtime type descriptor, size and alignment. Typed access rejects a different type even if its byte size matches. Read-only views over permitted mutable backing storage observe subsequent writes. Original pointer assertions use actual addresses; diagnostic records use relative byte offsets rather than pointed-to values. Raw constructors retain explicit unsafe allocation/lifetime/aliasing preconditions. Safe adapters use Copy elements and Cell-compatible or exclusive storage without returning unrestricted shared references to mutable data.

## Independent original-reference execution

Include-only C++ recording preserves original test bodies and still invokes pinned GoogleTest assertions. Rust diagnostic recording uses a separate shadow build. Every ordered event is compared using the established rules, without sampling or replacing operands with summary hashes. Full raw transcripts remain available losslessly.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40209288469/native-comparison.json) · [Chromium comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40209288469/browser-comparison.json) · [All retained evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40209288469).

Eight native and nine browser floating differences remain only in older colour cases under their original rules. This batch introduces no numerical differences or tolerance changes. Diagnostic local Chromium checks are separate from testing the actual published production module.

## Supplemental values, aliasing and ownership observer

An observer compiled with the unedited original headers runs after the reference tests pass. It is not an extra GoogleTest case and does not change their assertions. The matching Rust probe and independent Python dictionary/bit model use the same explicit operation corpus.

The corpus includes **16 sequences of 64 map operations**, mutable lookup/item edits, duplicates, empty buckets, missing lookups, independent clones and clearing. Integer view lengths are 0 through 64; floating view lengths are 0 through 16. It observes byte offsets, raw and typed writes, read-only aliases, externally modified backing storage and selected floating-point bit patterns. Owning keys include separate equal-valued allocations and null keys.

Unordered key traversal is canonicalised for comparison. **Order within a key's value list is never sorted away.** The observer does not claim native hash-table iteration order or physical storage equivalence.

All **107,101 unsigned 32-bit words / 428,404 bytes** match exactly across original C++, native Rust, Chromium WebAssembly and the independent Python model. Complete outputs have SHA-256 `3f34c070d7abcbd62e81025361335b3f47395b59a8d727ed2c70fb98fbd1e6b4`. The comparator checks all bytes and independently reconstructs the expected observations; this is not hash-only equivalence. [Comparison record](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40209288469/container-comparison.json).

## Original API limitation retained, not hidden

The first supplemental C++ build, [run 40207913645](https://github.com/596050/blended/actions/runs/40207913645), tried to instantiate `MultiValueMap<int,int>::clear_and_shrink()`. The pinned header declares that method but forwards to an underlying Map method that no longer exists. The original compiler rejected the call at `BLI_multi_value_map.hh:183:10` with `no member named 'clear_and_shrink'`.

This reference compilation failure correctly blocked publication. No original reference cases executed in that failed job. The failure is retained in [container-oracle-reference-limit.json](../evidence/container-oracle-reference-limit.json), with source/artifact hashes and the exact diagnostic.

The supplemental corpus was corrected to use supported `clear()` at both clearing points on **both** C++ and Rust targets. Original source tests, expectations, tolerances and the replacement implementation were unchanged. The final run verified that corrected explicit corpus. Rust's separate shrink helper remains a product capability, **not certified operational parity with the broken C++ declaration**. Removing this failing supplemental call is not represented as fixing upstream Blender.

## Test-first and deliberate failures

[Run 40206586218](https://github.com/596050/blended/actions/runs/40206586218), source `52765f932a6c6853f7a9aa194dc82adbc666a36a`, committed all thirteen native test declarations before their replacement module existed. It failed with thirteen E0433 unresolved-module diagnostics. This is absent-implementation evidence, not thirteen executed failing assertions. The source and artifact hashes are preserved in [the test-first summary](../evidence/container-view-test-first-summary.json); the original Actions artifact remains subject to retention.

Four isolated implementation-only mutations preserve the reviewed test source: reversing multi-add values, prepending instead of appending, ignoring typed writes and returning the wrong byte offset. Each must cause the intended original assertions to fail while an independent original control passes. All four probes passed natively and in Chromium, retaining original assertion counts and rejecting invalid case indices. Compiler errors, panics and browser traps cannot satisfy these checks. [Reports and logs](https://github.com/596050/blended/tree/55479ba6a6249846abc4c36d36440b27bfe106b4/verification/evidence/container-view-sensitivity).

Ten additional native product regressions cover empty-key semantics, insertion order, ownership/destruction, distinct pointer identity, type rejection, live aliases, alignment, clone independence and registration. Seventeen Python source, contract, observer and archive regressions are also separate from upstream case counts.

## Corresponding-source reproducibility

The source archive previously omitted workflow files and small failure-record fixtures referenced by regression tests. It now includes `.github/` and the two named JSON fixtures without bundling large ephemeral evidence. A fresh extraction of the final downloaded archive passed **all 304 Python regression tests** after `prepare_site.py`.

Archive SHA-256: `f4de919ab78b09ccc5ee72d199e7b9f5af2768f0bdf5dd14ef3bae885e9b02a5`. The [reproduction record](../evidence/source-archive-verification.json) distinguishes this local Python-only check from native Rust, original C++ and Chromium execution in CI. Those compilers were not rerun in the local extracted copy.

## Limits and remaining work

This is a behavioural adaptation, not every C++ template instantiation, native ABI, allocator, iteration order, concurrency model or performance guarantee. Primitive registration covers the original fixture's required types, not Blender's entire CPPType lifecycle/registry. Checked extents do not prove arbitrary raw-pointer safety. The supplemental corpus is explicit and finite, not every possible input or allocation behaviour.

The full source audit remains **5,867 candidates / 628 reviewed mappings / 5,239 unmapped declarations**. Mappings comprise 609 runtime and 19 compile-time cases, not a complete runtime denominator or feature percentage. Extensive application-level families, conditional benchmarks, more compile-time predicates and platform configurations remain unfinished. These library additions do not implement a complete editor or rendering engine. Completion issue #3 remains open.
