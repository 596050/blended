# Collection test-port verification, 23 October 2026

## Verified result and scope

The compatibility core now contains 131 Blender runtime cases, with 1,049 assertion executions. Run [39918173966](https://github.com/596050/blended/actions/runs/39918173966), source `2c7abe637e8eca6ea8937c871f406fa6ac123006`, passed original C++ execution, native Rust, Chromium WebAssembly, independent ordered-assertion comparisons and actual deployed-URL tests. Its full-suite completeness job remains failed. The current inventory implementation was separately verified at `986ac6ffc6892e5e3738d7e281da9413cf453914`, run [39918761201](https://github.com/596050/blended/actions/runs/39918761201).

Reference: Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. This is an accurately checked subset, not completion of Blender's suite or all application features.

| Complete new source file | Runtime cases | Assertion sites | Executed assertions |
| --- | ---: | ---: | ---: |
| BLI_bit_ref_test.cc | 10 | 63 | 63 |
| BLI_bit_vector_test.cc | 11 | 57 | 408 |
| BLI_index_ranges_builder_test.cc | 4 | 16 | 16 |
| BLI_unique_sorted_indices_test.cc | 7 | 34 | 34 |
| Total added | 32 | 170 | 521 |

The original 99 cases contribute 528 executions. The new total of 144 native Rust runtime tests includes 131 Blender cases, three Cycles cases, six new geometry cases and four safety cases. A separate compile-time mapping must not be counted as another runtime case.

## Translation fidelity

All assertion expressions and original loop bounds are retained. The generator locks complete source-file hashes, preserves source identities and lines, checks assertion-site counts, and reproduces committed Rust files. Expected runtime counts explicitly include loops. Original test snapshots are under `tests/upstream/blender`; the mapping is `compatibility/collection-ports.json`; reviewed contracts are in `compatibility/assertion-contracts.lock.json`.

The bit-reference adapter uses shared `Cell<u64>` storage. A read reference converted from a mutable reference observes later writes, rather than holding a copied Boolean. The packed bit vector preserves independent clones and the empty moved-from state tested upstream. Pointer assertions compare the actual containing-word addresses; cross-process transcripts encode relative word offsets because process addresses differ. C++ const/mutable pointer contexts remain in the case. Fixed-capacity range buffers retain merging and ascending-input rules. Span results are borrowed slices with their original ordered contents and range-versus-span variants.

The pointer-only original array is uninitialised in C++ but initialised in safe Rust; the case never reads its contents. Rust storage does not reproduce Blender's inline-allocation strategy. These documented representation changes preserve the exercised assertions, not all internal implementation details or untested behaviour.

## Independent assertion-level execution

Original C++ test bodies are unchanged. A diagnostic include records evaluated values once and still invokes the pinned bundled GoogleTest assertions. A build-only Rust shadow records corresponding values without editing the committed production tests. Native and Chromium WASM transcripts are compared with the original C++ sequence case by case, including kinds, operands, outcomes, counts and tolerances. All 1,049 events matched under documented normalisations; no floating differences required a tolerance allowance.

The diagnostic browser run is local CI execution. Separately, the production workbench was deployed and tested at its actual public URL. This distinguishes instrumentation checks from deployed-application execution. Invalid or missing cases cannot become successes by changing a dashboard count.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/browser-comparison.json) · [Public results](https://github.com/596050/blended/blob/test-port-evidence/result.json).

## Recovered signed-zero compile-time assertion

The original `BLI_math_vector_test.cc:219` hash comparison is now represented by `compile_time_cases::VECTOR_SIGNED_ZERO_HASH`, using the pinned scalar/vector hash semantics. Both native and wasm32 builds evaluate it during compilation. `tools/verify_static_port.py` checks a positive build and a deliberately broken hash build for each target. Both positive builds succeed; both negative builds must fail specifically with the expected constant-evaluation error and assertion message. A missing compiler, invalid target or unrelated compilation failure does not count as successful failure detection.

Evidence is under `evidence/collection-integration/static-port.json` and in conformance-run artifacts. The earlier embedded index-range compile-time condition is retained as well. No claim is made that all Blender compile-time assertions have been ported.

## Source-inventory defects found and fixed

C++ apostrophes in numeric literals were incorrectly being consumed as character-literal delimiters. This hid `bit_ref.MaskSingleBit` and other source candidates. An integer-only fix also needed extension for floating literals and user-defined numeric suffixes. The final scanner recognises preprocessing-number tokens before handling apostrophes, while earlier strings/comments retain their masking behaviour.

Focused local regressions demonstrated three failures in five initial cases and four failures in seven floating/suffix cases before their respective fixes. The corresponding cases passed after correction; CI independently executed all infrastructure tests. Another guard reconciles every mapped identity and original line against its frozen upstream source. Run 39918761201 verified all 132 mapped source identities against the actual pinned checkout.

The corrected heuristic scan has 5,673 candidates, 132 mappings and 5,541 unmapped candidates. Earlier 5,637-candidate reports are historical and were incomplete even as source scans. These numbers remain distinct from complete runtime enumeration: conditional, typed, generated, external and compile-time work still requires reconciliation. The scanner is not a complete C++ frontend.

## Test-driven evidence and remaining work

Test-first run [39914938956](https://github.com/596050/blended/actions/runs/39914938956) reproduced the new source cases and failed because their implementation/module did not exist. This was not 32 observed assertion failures. Later implementation runs passed, followed by independent original-reference and browser verification.

Whole-suite completion remains blocked. Runtime discovery for all configurations and families, thousands of remaining ports, fixture materialisation in execution jobs, renderer/UI/Python adapters and broader feature compatibility are unfinished. Keep issue #3 open and keep the full-completeness gate genuinely failed until those requirements are fulfilled.
