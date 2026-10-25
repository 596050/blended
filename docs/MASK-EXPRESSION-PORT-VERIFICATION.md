# Index-mask expression verification

## Verified scope

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Project runtime: `f86fae88ce889175fcaa11dcb982d3bbc4fce5ca`.
Verification: [run 40149763130](https://github.com/596050/blended/actions/runs/40149763130).

All **15 enabled functional cases** in `source/blender/blenlib/tests/BLI_index_mask_expression_test.cc` are ported. Their 27 original assertion sites execute **321 runtime checks**, including 300 inside the original randomized test. The disabled `index_mask_expression.Benchmark`, guarded by `#if 0`, remains explicitly unported. This is not complete source-file coverage under every possible configuration.

The combined subset now contains **596 unique Blender runtime cases and 3,196,692 assertion events per implementation**. All pass natively and at the actual [public Chromium URL](https://rawcdn.githack.com/596050/blended/4cc3dade093dd7da5899ed995e02ce3689225fb2/index.html), with no recorded browser errors. The complete native Rust run passes **656 runtime tests: 596 Blender, three Cycles and 57 separate product/safety/regression cases**. Nineteen compile-time predicates separately pass positive builds and deliberate-failure checks on native and wasm32. Whole-suite completeness remains failed.

## Original source and faithful inputs

Original Git blob: `2d266c4d5312e4c9ddc28cddec657e0253134af3`.
Original SHA-256: `2e502225bf3f5214261404bb8c0e5f8a4e8877491db1d07479caead1eaa8ddd4`.
Reviewed generated Rust case SHA-256: `84f8039f2797880492b283ab58f9f455cd30ef9b7e97d18b0275813d8a596a23`.
Original random-helper SHA-256: `9dbe650537009cdd9ddb01366c32f92631bb7574aef5fba9f9dc10294126d7b9`.

`tools/port_mask_expression_tests.py` is a finite reviewed adapter, not a general C++ translator. It verifies the pinned complete file and preserves active case identities, source lines, body hashes, helper provenance, expected masks and execution counts. The fixed target hash is required in `compatibility/mask-expression-assertion-contract.lock.json`; deleting that shard cannot reduce the accepted test universe. Historical base, polygon and span contracts remain unchanged.

The original `Fuzzy` test retains **all 50 iterations**, lengths from one up to 200,000, three Boolean arrays per iteration, seed zero and original chunk type/size/density generation. Random draws are consumed in the original order, including the density draw for constant chunks. Six original comparisons execute per iteration. Expected masks are still generated independently from Boolean predicates, not copied from the expression result.

The other cases preserve unions/intersections/subtractions of multiple masks, FizzBuzz-style striding, complements, overlapping large ranges, nested range terms, identity/self-subtraction and the small-mask segment-count expectations. The union of two large ranges remains an operation, not a hard-coded expected mask. No original loops, input sizes or numerical tolerances were reduced.

## Implementation and value-level recording

`mask_expressions.rs` implements immutable selected-index sets as canonical maximal half-open intervals with shared ownership. It provides range, index, Boolean, predicate and stride constructors; cardinality, membership, iteration and optional contiguous-range views; set union/intersection/difference; bounded complements; and nested expression evaluation with an explicit post-order stack. Large contiguous intervals are not expanded element by element for set operations.

This is a serial Rust implementation, not native arena, segmented allocation, TBB scheduling, ABI or performance parity. The virtual segment-count method preserves the observations in these small original cases, not arbitrary native allocation choices for every possible mask. Constructors and ownership are Rust adaptations. The broader IndexMask API is not thereby certified, and these operations are not new interactive editor features.

Original C++ test/helper bodies remain unchanged. An include-only recorder evaluates original operands and still invokes the pinned GoogleTest assertions. A separate Rust diagnostic shadow records corresponding events. A mask operand is represented by **every selected index**, reversibly encoded as canonical maximal runs, unsigned LEB128 gap/length pairs and exact hexadecimal bytes. Adjacent native ranges are merged in the recorder so physical segment boundaries do not alter the logical set. This is not a count, hash, sample or Bloom filter; different same-cardinality masks remain different values.

All combined assertion events compare successfully in native Rust and Chromium WebAssembly. Eight native and nine browser floating differences remain in earlier colour cases under their original rules; the mask cases add none and no tolerance is widened. [Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/browser-comparison.json). Complete lossless transcripts are retained rather than sampled.

## Independent exact-input and absolute-index oracle

Passing comparisons against generated expectations alone would not prove that random inputs remained identical. The original executable therefore runs an additional listener that calls the **unedited original random helper** for the same 50 iterations. The Rust probe calls the actual translated helper in a separate diagnostic build. Every input Boolean and length is written to a raw binary tape, independent of the assertion run codec.

All **14,573,457 generated Boolean values** match original C++ exactly in native Rust and Chromium WebAssembly. No input sampling is used. These inputs are supplemental evidence, not millions of extra upstream test cases.

The same tape covers **24,576 set configurations**: every pair of six-position masks at three absolute origins and two strides. The third mask is deterministically derived, so this is not exhaustive coverage of all triples. The origins are 0, 16,380 and 2,147,483,520; strides are 1 and 17. The second origin exercises a native segment boundary, and the third approaches the pinned static constructor's upper domain.

Each configuration records its absolute inputs and six original expression outputs: multi-union, intersection, multi-subtraction, two bounded complements and a nested union-minus-intersection. Python independently checks Boolean truth-table results, membership, cardinality and every ordered absolute selected index. The complete C++ tape is then compared byte-for-byte with native Rust and Chromium outputs, not merely by digest.

All **147,456 mask results and 370,176 absolute selected-index values match exactly**. The tape includes 122,880 input-configuration words and 294,912 size/membership words in addition to the selected values and original random inputs. Each complete output is **20,877,625 bytes**, SHA-256 `10bafb42170b49107e338cee3fee7b109fbb007a338467e41eb8386356725339`. Raw C++, native and browser tapes, diagnostic wrappers and the [comparison report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/mask-comparison.json) are preserved under the immutable run directory.

These local diagnostic browser checks are distinct from the production workbench's actual public-URL test. Both layers passed on the verified source revision.

## A rejected supplemental input remains visible

The first supplemental attempt, [run 40148762471](https://github.com/596050/blended/actions/runs/40148762471), used an absolute origin of 2^40. All 596 original runtime tests passed before that extra probe hit the pinned static-range constructor's `min_size <= 2^31` assertion in `intern/index_mask.cc`. The reference job failed and publication was blocked. That run is not relabelled as a successful verification.

The corrected supplemental corpus uses `(1 << 31) - 128`, keeping all its indices inside the original constructor's domain. The original fifteen test bodies, helper, expectations, loops and reviewed target hash remain unchanged. The failed attempt is recorded in [mask-oracle-domain-failure.json](../evidence/mask-oracle-domain-failure.json); the full historical Actions artifact remains subject to retention.

This is a limit of the exercised original constructor path, not a statement that every native IndexMask operation rejects all larger indices. A separate Rust product test demonstrates compact larger 64-bit intervals, but is explicitly not original-C++ equivalence beyond the reference domain. Absolute-input/iterator checks prevent a relative membership representation from concealing a wrong offset.

## Test-first and failure sensitivity

The fifteen native case runners were committed at `0edb0121cf958119b8a5ff90f83d8393e7ede000` before the replacement module existed. [Run 40147788998](https://github.com/596050/blended/actions/runs/40147788998) produced fifteen E0433 unresolved-module diagnostics. This is missing-implementation evidence, not fifteen executed assertion failures. [Durable test-first summary](../evidence/mask-expression-test-first-summary.json) records original archive/log hashes and the retention limit.

Three isolated implementation mutations keep the original cases unchanged: union ignores its other operand, intersection wrongly uses union, or subtraction returns its input unchanged. Each fails its intended original test while an independent original control passes, in native Rust and Chromium WebAssembly. Original assertion counts and invalid-index rejection are retained. Compiler errors, panics and traps cannot substitute for recorded assertion failures. [Full mutation evidence](https://github.com/596050/blended/tree/4cc3dade093dd7da5899ed995e02ce3689225fb2/verification/evidence/mask-expression-sensitivity).

Seven separate Rust product regressions cover canonical storage, compact 64-bit intervals, sparse complement direction, predicate visits, stride counts, all six-bit subset pairs, nested expressions and empty/boundary behaviour. Eighteen Python tests cover source identities/hashes, all original loops, required contract shards, lossless recording, complete binary comparison and reference-domain/absolute-index guards. None is counted as a new upstream case.

## Remaining scope

The complete Blender test port is unfinished. The source audit has **5,867 candidates, 615 reviewed mappings and 5,252 unmapped declarations**. Mappings comprise 596 runtime and nineteen compile-time requirements, not a complete runtime denominator or feature percentage. This file's disabled benchmark, earlier optional benchmarks, many application-level families and further platform/compile-time work remain outstanding. Complete test porting, all-tests-passing and full Blender application parity remain separate milestones.
