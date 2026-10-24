# Array, CSV, streaming-hash and disjoint-set verification

## Verified implementation

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Verified project implementation: `059bfb9b277e8bc5aefb9834dd671879094a0599`.
[Run 40045600207](https://github.com/596050/blended/actions/runs/40045600207) passed freshly compiled native Rust, original C++ execution, native/Chromium assertion comparisons, the streaming oracle, mutation controls, publication and actual deployed-URL tests. The separate full-completeness job remains failed.

| Complete original runtime test file | Cases | Original assertion executions |
| --- | ---: | ---: |
| BLI_array_utils_test.cc | 35 | 133 |
| BLI_csv_parse_test.cc | 10 | 114 |
| BLI_hash_mm2a_test.cc | 3 | 5 |
| BLI_disjoint_set_test.cc | 1 | 12 |
| Added | 49 | 264 |

The combined subset is **416 unique Blender runtime cases / 33,368 ordered assertion events**. Native Rust totals **444 runtime tests**: 416 Blender, three Cycles and 25 product/safety/regression cases. Six compile-time assertions remain separately tracked and pass positive builds and negative mutations for native and wasm32. None is counted as a runtime pass.

## Faithful source cases

All four complete source files are SHA-256 locked. Original snapshots are under `tests/upstream/blender`; original line, test identity, source hash and test-body hash are retained in `compatibility/data-ports.json`. Reviewed target hashes are in `compatibility/assertion-contracts.lock.json`. `tools/port_data_tests.py` is a deliberately limited reviewed adapter, not a general C++ translator. Unknown revisions or unsupported assertion syntax fail. CI reproduces committed generated tests before execution.

The array tests preserve original data, order and helper expansions. `EXPECT_EQ_ARRAY` produces exactly the original number of per-element assertions, without inventing a length assertion. C-string comparison is recorded as STREQ, not pointer equality. Pointer-search tests still pass actual live pointers. Deduplication is rerun on its own result as upstream requires. The virtual-array function case evaluates a real function-backed adapter rather than substituting a materialised expected result.

Grouping retains both original 100,000-entry inputs, exact dense/sparse formulas, full masks and the `i % 3 != 0` selection. Expected first-occurrence groups are computed independently of the implementation through insertion-index bookkeeping. A whole-span equality is still one assertion event comparing all elements, not a fabricated count of 100,000 new assertions. The production grouping code uses a lookup-table or hash-map strategy and returns the original first-selected indices.

CSV cases preserve the original quoted and escaped bytes, multiline input, incomplete closing quotes, empty/header-only input, blank lines, trailing delimiters, one-byte approximate chunks and unescaping expectations. Parsing retains raw borrowed bytes until explicitly unescaped. The chunk-boundary retry follows the pinned algorithm. Arena-managed test data is represented through borrowed/owned Rust storage; no arena-layout equivalence is claimed.

Murmur2A cases retain original byte lengths, integer inputs, seeds and expected hashes. Streaming updates carry pending bytes across chunks. The finaliser mutates hash, tail and size as the original does; it is not a cached read. Disjoint-set cases preserve joins, membership checks and returned-root behaviour using union by rank and path compression.

## Independent original-reference execution

Original C++ test bodies are unchanged. Include-only instrumentation records evaluated operands and still invokes bundled GoogleTest comparisons. A separate Rust shadow records corresponding case boundaries and assertion events. The production Rust tests are not rewritten by the diagnostic audit. Every registered case is reconciled by identity, assertion kind, order, operands, outcomes, execution count and original tolerance.

All 33,368 events matched under the documented rules. Older colour cases retain eight native and nine browser floating differences within their original tolerances. The new data cases introduce no floating differences. No tolerance was widened. [Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40045600207/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40045600207/browser-comparison.json).

The diagnostic Chromium run is local CI execution. Separately, the production module was published and tested at the actual immutable URL: [416-case workbench](https://rawcdn.githack.com/596050/blended/63655e85d5b56c357645c92e3874af3940fd161e/index.html). All 416 cases passed; no browser errors were recorded.

## Supplemental streaming oracle

`tools/verify_hash_streaming.py` compiles the **complete unedited original hash_mm2a.cc**, with its pinned header, and supplies identical serialised bytes and chunk plans to C++, native Rust and Chromium WebAssembly. The corpus has **10,592 distinct configurations**: four seeds, lengths 0 through 64 inclusive, every two-part split boundary, fixed-width chunk patterns and zero-length updates. Each configuration compares three outputs: first finalisation, repeated finalisation without reset, and a reset followed by a whole-input update.

All **31,776 hash outputs** match exactly on each replacement platform. This covers the stated corpus, not every possible byte string. Native x86_64 and wasm32 here are little-endian; the original hash is endian-sensitive and is not suitable as an architecture-independent persisted hash.

[Immutable oracle report, inputs, drivers and outputs](https://github.com/596050/blended/tree/63655e85d5b56c357645c92e3874af3940fd161e/verification/evidence/hash-streaming). This corpus is supplemental differential evidence, not 10,592 additional Blender test ports.

## Test-first and deliberate failures

[Run 40044605903](https://github.com/596050/blended/actions/runs/40044605903) committed the 49 translated cases and mappings at `72e52d548f4907dd9836fe33981c4a5a0360c1a3` while all four implementation modules were absent. Cargo reported four E0583 missing-module errors plus dependent type-inference errors. This is a genuine compilation failure before implementation, not 49 executed failing assertions. The original artifact is retained as [data-test-first-evidence.zip](../evidence/data-test-first-evidence.zip), with its hash and source metadata in the status record.

Four isolated mutations modify only implementation code, keeping the original ported tests unchanged. Removing trailing-empty-field handling fails `csv_parse.ParseRecordFields`; dropping pending hash tail bytes fails `hash_mm2a.MM2AConcatenateStrings`; reversing dense first-index output fails `array_utils.GroupIdsToIndicesDense`; disabling union fails `disjoint_set.Test`. Each is detected natively and through browser WebAssembly, with unchanged assertion counts and an independent passing control. Compiler errors, panics and traps cannot satisfy these checks.

[Immutable mutation reports and logs](https://github.com/596050/blended/tree/63655e85d5b56c357645c92e3874af3940fd161e/verification/evidence/data-sensitivity). Five additional Rust product regressions cover non-UTF8/custom CSV options, multiline retry, equal-text/distinct-pointer identity, adjacent-only deduplication and root stability. They are not upstream cases.

## Scope and unfinished work

Current C-array adapters cover the tested character, i32 and pointer forms. Their generic Rust equality is not a claim of bytewise `memcmp` equivalence for arbitrary padded structs, NaNs or every type. The virtual-array adapter covers the tested span/function forms, not all native representations, single-value quirks or parallel reduction schedules. CSV callbacks execute sequentially; native parallel scheduling, cancellation ordering and arena allocation are not reproduced. The disjoint-set representation uses checked Rust indices, not native layout parity.

These library additions do not add a full mesh editor or renderer. The complete suite remains unfinished: 5,859 source candidates, 422 reviewed mappings (416 runtime plus six compile-time) and 5,437 unmapped declarations. Full runtime enumeration and the required dependency/configuration matrix are still incomplete. Source counts are not a runtime denominator or feature percentage. Keep completion issue #3 open.
