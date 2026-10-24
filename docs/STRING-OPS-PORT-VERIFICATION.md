# String operations, fuzzy search and unique-name verification

## Verified implementation

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Verified implementation: `ab692209e9eb98248054ae90ead9b0258f1ab4da`.
[Run 40049834310](https://github.com/596050/blended/actions/runs/40049834310) passed fresh native Rust, original C++ execution, native/Chromium assertion comparisons, the supplemental exact-value oracle, mutation controls, publication and the actual deployed-URL test. The separate whole-suite completeness job failed because the complete Blender test port remains unfinished.

| Complete original runtime source file | Cases | Assertion executions |
| --- | ---: | ---: |
| BLI_string_test.cc | 43 | 801 |
| BLI_string_search_test.cc | 3 | 31 |
| BLI_string_utils_test.cc | 2 | 14 |
| Added | 48 | 846 |

The combined subset contains **464 unique Blender runtime cases / 34,214 assertion events**. The complete native Rust run passed **497 runtime tests**: 464 Blender, three Cycles and 30 separate product/safety/regression tests. Six compile-time assertions remain separate and pass positive builds and deliberate-failure checks for native and wasm32.

## Original fixtures and assertion semantics

All three source files are SHA-256 locked. `tests/upstream/blender` preserves originals. `compatibility/string-ops-ports.json` records original paths, lines, test kinds, test-body hashes and assertion counts. Reviewed target hashes remain in `compatibility/assertion-contracts.lock.json`. The finite reviewed adapter `tools/port_string_ops_tests.py` reproduces committed cases; it is not a general C++ transpiler. CI does not silently refresh reviewed hashes.

All **29 TEST and 19 TEST_F declarations** are mapped. Fixture data, original helpers and loop bounds remain. Original C literals retain raw UTF-8, hexadecimal, octal, embedded-NUL and control bytes; the adapter does not decode byte escapes as Unicode and then double-encode them. Natural comparison retains original leading-zero tie breakers and comparison sign/magnitude. Search operates with the original needle-comparison length, not an invented haystack bound. Unique-name suffixes use the actual callback fixture rather than canned expected names.

Buffer capacities, sentinels, bounded copies/appends and range-replacement expectations remain. Join tests exercise every original truncated capacity, preserving 166 assertions in that case. Word-split helpers retain the EXPECT_EQ_VECTOR size assertion and conditional element checks. Control-character escape helpers retain their original assertion sequences. Formatting keeps source precision, thresholds and expected strings.

Pointer checks compare actual returned addresses with original input offsets; equality is not replaced with text comparison. Separate allocations of static literals have different layouts in C++ and Rust, so string-fixture transcript pointers use pair-local alias/null labels. The original assertion still evaluates real pointer equality. Existing older pointer-offset encodings are unchanged. A separate original-C++ search oracle verifies numeric offsets independently, and a wrong-address mutation is detected by unchanged tests.

Strict EXPECT_LT comparisons retain order; symmetric operand normalisation applies only where the original comparison is symmetric. Original C++ test bodies are unchanged by include-only recording. The Rust diagnostic shadow is separate from production tests. Case boundaries, ordered kinds, operands, outcomes, execution counts and tolerances are reconciled with original reference execution.

All 34,214 events passed those rules. Eight native and nine browser floating differences remain in older colour tests, within their original comparisons; no tolerances were widened and the new string cases add no floating differences. [Native report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40049834310/native-comparison.json) · [Browser report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40049834310/browser-comparison.json).

## Additional exact-value original-C++ oracle

`tools/verify_string_ops_oracle.py` extracts four **unedited** functions from SHA-locked original `intern/string.cc`: BLI_strncasecmp, BLI_strncasestr, left_number_strcmp and BLI_strcasecmp_natural. Its standalone driver supplies original ELEM semantics, explicit serialised inputs and the C locale. It does not substitute an expected-value implementation.

The corpus contains 56 distinct ASCII byte strings, including empty inputs, whitespace/control characters, mixed case, periods, numeric prefixes and leading zeros. All 3,136 ordered pairs produce exact natural-order return values. Every pair is also searched with comparison lengths 0, 1, 2, 3, 4, 8 and 32, producing 21,952 returned-pointer offsets or null sentinels.

**All 25,088 results match exactly** in native Rust and Chromium WebAssembly. This covers the stated corpus, not every byte string or locale. It is supplemental differential verification, not 25,088 additional Blender ports. [Immutable oracle report, inputs, original driver and outputs](https://github.com/596050/blended/tree/51d30f5a549da822a9dc0945d353ef6414938092/verification/evidence/string-oracle).

## Test-first and negative execution evidence

[Run 40049137734](https://github.com/596050/blended/actions/runs/40049137734) generated and committed the 48 source cases at `719f4db5f7011cae3e540e1d9c348fa5fc44cf39` before the two implementation modules existed. Cargo reported two E0583 missing-module errors and a dependent E0282 inference error. This is missing-implementation compilation evidence, not 48 executed failing assertions. The original ZIP is preserved at [string-ops-test-first-evidence.zip](../evidence/string-ops-test-first-evidence.zip); its SHA-256 and source revision are recorded in the status JSON.

Four isolated mutations alter only implementation code while preserving the original translated test source. Disabling append fails `string.StrCat`; returning the wrong storage address fails `string.StringStrncasestr`; disabling adjacent transposition fails `string_search.damerau_levenshtein_distance`; disabling name collision handling fails `BLI_string_utils.BLI_uniquename_cb`.

Each failure is observed natively and in Chromium WebAssembly, with the original assertion count retained and an independent control case passing. Invalid case indices remain rejected. Compiler failures, panics and traps are not accepted as successful mutation detection. [Immutable sensitivity reports and logs](https://github.com/596050/blended/tree/51d30f5a549da822a9dc0945d353ef6414938092/verification/evidence/string-sensitivity).

Five additional Rust product tests cover untouched word sentinels, pointer/length semantics, Unicode codepoint/transposition behaviour, UTF-8-safe name truncation and the pinned reverse-partition boundary. They are not counted as upstream cases. Ten additional Python tests cover original-file identities, all TEST_F declarations, source reproduction, byte-literal decoding, assertion accounting, pointer/ordered-comparison failures and probe targets.

The production module was separately published and exercised at its actual immutable URL: [464-case workbench](https://rawcdn.githack.com/596050/blended/51d30f5a549da822a9dc0945d353ef6414938092/index.html). All 464 cases passed with no browser errors. This public run is distinct from local diagnostic oracle and mutation execution.

## Verified scope and remaining work

The byte adapters preserve tested C-string behaviour without reproducing native allocations. The UTF-8 adapter covers the valid Unicode inputs exercised here. Invalid-byte return values, obsolete five/six-byte encodings, overlong/surrogate acceptance and the remaining UTF-8 suite are outside this verified scope. A source comment is clarified after the verified runtime revision to remove an overly broad invalid-byte-fallback claim; no implementation or test body changes with that documentation correction.

The pinned UTF-8 reverse-partition routine does not inspect a delimiter in the first codepoint. That behaviour is retained and explicitly tested, not silently repaired while claiming identity. Bounded escape output reserves space for a terminator instead of reproducing native out-of-bounds behaviour on invalid capacity inputs. Natural ordering and lowercasing are scoped to the tested C-locale behaviour. The full Search/initials/ranking system, all locales, every malformed byte input and allocation/performance parity are not implemented by this batch.

These are core-library additions, not a complete modeller or renderer. The current heuristic audit contains 5,859 source candidates, 470 reviewed mappings (464 runtime plus six compile-time) and 5,389 unmapped declarations. Full runtime enumeration, required dependency/configuration coverage and extensive application-level families remain unfinished. The runtime denominator is unknown, not zero, and completion issue #3 remains open.
