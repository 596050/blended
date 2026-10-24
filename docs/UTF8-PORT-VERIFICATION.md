# UTF-8 boundaries, malformed bytes and cursor verification

## Pinned scope

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Project source: `3969e1fdadae2e11d6f220412f8c32cabf7048d1`.
Verification run: [40065241089](https://github.com/596050/blended/actions/runs/40065241089).

The run passed fresh native Rust execution, original C++ reference execution, independent native/Chromium assertion comparisons, input oracles, mutation controls, publication and actual public-URL testing. All 503 Blender runtime cases passed at the [immutable workbench](https://rawcdn.githack.com/596050/blended/a7f55a00388e7b3fb906c307cc52db7968b9a25d/index.html), with no recorded browser errors. The native Rust total is **542 runtime tests: 503 Blender, three Cycles and 36 separate product/safety/regression tests**. Six compile-time assertions separately passed positive builds and deliberate-failure checks on native and wasm32.

Every runtime case in `BLI_string_utf8_test.cc` is mapped: **39 cases and 1,627,163 original assertion executions**. The combined implementation contains **503 unique Blender runtime cases and 1,661,377 assertion events**. Repeated assertions are not counted as additional test cases. The full-suite completeness requirement remains failed and is separate from publishing an explicitly incomplete subset.

| Original test group | Cases | Assertion executions |
| --- | ---: | ---: |
| Invalid-byte removal and substitution | 3 | 404 |
| UTF-8 length and incomplete sequences | 2 | 47 |
| Copy and truncation | 5 | 311 |
| Tested UTF-8 formatting form | 3 | 148 |
| Index-to-byte-offset conversion | 1 | 16 |
| Original decoder stress test | 1 | 1,626,112 |
| UTF-8/UTF-32 cursor movement | 24 | 125 |
| Added | 39 | 1,627,163 |

## Original source and inputs

The original source SHA-256 is `0821a446fa0de157022ec8d27ffbd5b50ae50d6f9889bb67a9cf7ac0d269b572`. Its complete snapshot, original case names/lines/body hashes and reviewed generated target hashes are retained. `tools/port_utf8_tests.py` is a finite reviewed adapter, not a general C++ translator. CI reproduces the committed cases from the pinned checkout. Registration and runtime execution remain separate facts.

The 78 invalid-input fixture rows retain all original 80-byte buffers, including embedded NULs, expected repaired strings and error counts. Markus Kuhn's upstream CC BY 4.0 fixture attribution remains in the snapshot and translated source. Buffer capacities, untouched sentinels, C-string comparison semantics, original helper assertions and cursor inputs are preserved.

The original stress helper still covers buffer sizes **1 through 12**, all **256 byte values**, each original ascending/descending multiplier pattern, and **256 original random-byte fills per size**. Comparisons keep both original padding lengths and explicit unpadded versus padded bounds. Every helper assertion is executed; loops are not reduced to representative samples. The decoder's result and consumed-byte offset remain separate observations.

`utf8_compat.rs` implements validation, removal/substitution, safe stepping, bounded length/copy, the tested formatting form, index conversion and UTF-8/UTF-32 cursor stepping. Its random-byte fixture generator preserves the unusual original rule that short blocks do not advance the 48-bit state. This is distinct from the existing integer generator.

Cursor zero-width decisions use the exact pinned `extern/wcwidth/wcwidth.c` combining table, not the host's Unicode database. `tools/generate_utf8_tables.py` checks Git blob `1d337ec47f24e04f427937deeedcd773cc3ea474`, parses every interval, rejects unexpected syntax/order and reproduces the committed table. The full upstream notice is in `LICENSES/wcwidth-original-notice.txt` and is included in the downloadable corresponding source archive.

## Assertion-level comparison at stress-test scale

Original C++ test bodies remain unchanged. An include-only recorder evaluates operands once and invokes pinned GoogleTest assertions. A separate Rust diagnostic shadow records the corresponding case boundaries, values and assertion results without modifying the production test source. All **1,661,377 assertion events** passed the native and browser comparisons. Eight native and nine browser floating differences remain in the earlier colour cases, within the original rules; no tolerances were widened and this UTF-8 batch introduces no floating differences. [Native report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40065241089/native-comparison.json) · [Browser report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40065241089/browser-comparison.json).

The larger stress transcript is compared **event by event**, in bounded batches using the same reviewed comparison rules. `tools/fidelity_stream.py` validates all case boundaries and counts, preserves per-case event order, and rejects missing, duplicated, substituted or out-of-case events. It does not sample, deduplicate repetitive events, compare only totals or replace value comparisons with hashes.

Chromium executes the complete diagnostic module, then transfers its entire ASCII transcript in bounded chunks. The diagnostic Rust recorder relinquishes its buffer instead of cloning the whole transcript. These changes reduce transfer/comparison memory overhead, not the test scope. The production workbench remains separately built and tested at its actual immutable public URL.

Every raw C++, native Rust and browser transcript is retained losslessly as `.jsonl.gz` in [immutable-run evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40065241089). Full decompressed SHA-256 and byte counts are verified before removing duplicate uncompressed files. `TRACE-STORAGE.json` records both representations. Hashes establish stored-byte integrity; assertion correctness is established by the preceding event-by-event comparison, not the hashes alone.

Fourteen streaming regressions verify events at chunk boundaries and the last event, missing/extra/reordered assertions, missing or failed case boundaries, duplicate assertion-free cases, exact global difference ordinals and lossless compression. They are audit infrastructure tests, not additional Blender ports.

## Supplemental original-C++ oracle

`tools/verify_utf8_oracle.py` compiles seven **unedited functions** from pinned `string_utf8.cc` and `rand.cc`, using pinned headers and the original unsigned-char contract. Identical serialised bytes are supplied to original C++, native Rust and Chromium WebAssembly.

The corpus includes an empty input, every single-byte input, **all 65,536 two-byte inputs**, and 2,480 explicit legacy/truncated/invalid-continuation sequences of three through seven bytes: **68,273 byte sequences**. It compares the validator's first invalid-byte offset and every decoded value/next-offset pair produced before the original NUL stopping condition.

A separate output row checks **4,096 random-byte blocks and 48,640 bytes**, using seed 1 and 256 fills for each size 1 through 12 plus 16, 31, 32 and 33. This independently confirms all original stress-test random-buffer lengths; matching padding invariance alone would not prove identical random inputs.

All **68,273 validator results, 137,426 decoded-codepoint/next-offset pairs and 48,640 generated bytes match exactly** on both replacement targets. Raw inputs, original function hashes, compiled binary hashes and outputs are retained with the [oracle report](https://github.com/596050/blended/tree/a7f55a00388e7b3fb906c307cc52db7968b9a25d/verification/evidence/utf8-oracle).

This corpus is supplemental differential evidence, not 68,273 extra Blender test ports. The byte generator remains endian-sensitive; the verified native x86_64 and wasm32 targets here are little-endian. Longer arbitrary inputs and every possible caller precondition are not exhaustively certified.

## Test-first and negative controls

[Run 40064003518](https://github.com/596050/blended/actions/runs/40064003518) generated and committed the original cases at `d563dbeb1e9246e2242c57082ccbf0dc2bde10eb` before `utf8_compat.rs` existed. Cargo reported E0583 for the missing implementation module. This is compilation failure before implementation, not 39 executed assertion failures. The original ZIP is retained as [utf8-test-first-evidence.zip](../evidence/utf8-test-first-evidence.zip), SHA-256 `f5f343bff34e296fc2e451091cf8b30e31f1dba5b1330e357acc8145361f1390`.

Three isolated mutations keep original test bodies unchanged: disabled invalid-byte substitution, disabled bounded copying and ignored zero-width combining characters. Each must fail its intended original case while an independent original control passes, with expected assertion counts retained. Compiler errors, panics and traps are not acceptable evidence of assertion detection. All three [probes](https://github.com/596050/blended/tree/a7f55a00388e7b3fb906c307cc52db7968b9a25d/verification/evidence/utf8-sensitivity) passed on native Rust and Chromium WebAssembly. The original target cases retained 234, 216 and 7 assertion executions respectively; control cases passed and invalid case indices were rejected.

Six additional Rust product regressions exercise legacy decoder/validator distinctions, one-byte progress on truncated input, untouched buffer sentinels, short random-block state, combining movement and an explicit safe malformed-prefix boundary. They are not upstream cases.

## Compatibility boundaries and unfinished work

This module reproduces the **pinned legacy behaviour**, not a strict modern Unicode validator. Some five/six-byte sequences and selective invalid-code checks are deliberately preserved because the original tests require them. Validation and permissive decoding are different operations. The formatting adapter covers the exact single-`%s` form tested here, not the complete C varargs formatting API. Cursor code uses the original zero-width predicate, not a claim of full display-width, grapheme segmentation or locale support.

Safe Rust slices replace native pointer arithmetic. An all-continuation malformed prefix is explicitly clamped at the buffer start; this is a documented safety policy, not a claim of reproducing an out-of-buffer native pointer. Allocation layouts and undefined behaviour are not compatibility guarantees. The previously introduced `string_ops::utf8_step` remains a separate valid-Unicode adapter; this batch does not silently certify all older string/search callers for malformed inputs.

These core-library additions do not implement a Blender editor or renderer. The complete application test port is still unfinished. The current heuristic scan has **5,859 source candidates, 509 reviewed mappings and 5,350 unmapped declarations**. Mappings comprise 503 runtime cases and six compile-time cases. Full runtime discovery remains incomplete, so the remaining runtime denominator is unknown, not zero. Issue #3 stays open.
