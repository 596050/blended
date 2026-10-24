# Half-precision and normalised-format verification

## Verified scope

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Project revision: `2990e30077e368c97e3a7af60d45d7a911ceb988`.
Verification: [run 40108130160](https://github.com/596050/blended/actions/runs/40108130160).

This batch ports **nine enabled functional cases / 169 assertion executions**: eight cases with 162 assertions from `BLI_math_half_test.cc`, and the complete one-case/seven-assertion `BLI_normalized_int_test.cc`. Five `DO_PERF_TESTS` benchmarks remain explicitly unported. They are not enabled in this reference build, not counted passing, and not removed from the whole-suite inventory. This is not a claim that the entire half-float source file is finished under every configuration.

The combined subset is **512 unique Blender runtime cases / 1,661,546 assertion events**. The native Rust run has 558 runtime tests: 512 Blender, three Cycles and 43 independent product/safety/regression tests. Six compile-time assertions separately pass positive-build and deliberate-failure checks on native and wasm32. The whole-suite completeness job remains failed.

## Original cases and implementation

Original files, case identities, source lines, body hashes and expected results are retained. `tools/port_pixel_format_tests.py` is a finite reviewed adapter. Unknown source revisions fail rather than generating approximations. Runtime registries and reviewed assertion contracts remain bijective. Array helpers perform exactly the original scalar comparisons; normalised-vector equality remains one array-valued assertion rather than inventing component test counts. Original NaN classification, signed inputs, sentinels, array lengths and precision rules are preserved.

The implementation supplies scalar half conversion, finite-result conversion, array operations, clamping, and normalised signed/unsigned 8-bit, 16-bit and 10/10/10/2-bit formats. Half conversion rounds to nearest-even. Normalised encoding retains the original truncation instead of substituting rounded conversion. Integer fields and decoded values match the checked reference, but native C++ bit-field allocation layout is not an ABI promise.

The bit-level profile is explicit: x86_64 scalar conversion and four-lane SSE2 array semantics, with the SSE4.1 clamp path. Rust reproduces those semantics without claiming SIMD performance. The original Blender header permits architecture-dependent NaN payloads; F16C/AVX and ARM NEON are separate profiles, not certified by this run. Upstream half conversion credits Fabian Giesen's public-domain conversion work; original Blender source and notices remain pinned, and the Rust adaptation retains GPL-2.0-or-later attribution.

## Floating-point mode and boundary behaviour

The native x86_64 guard actually sets MXCSR flush-to-zero and denormals-are-zero bits, retains thread ownership and restores the prior register. Original C++ and Rust both execute checked conversions under that mode. Nested restoration has a separate product regression. WebAssembly has no accessible MXCSR register; its guard is a no-op, as in the pinned C++ unsupported-platform fallback. The exported capability and oracle report explicitly say false in the browser. Browser values passing is not represented as hardware-mode perturbation.

Two pinned boundary details are retained: SIMD-prefix versus scalar-tail NaN payload treatment, and NaN clamping order when the clamp interval excludes zero. The original four-lane clamp prefix replaces NaNs before clamping; the scalar tail replaces a remaining NaN afterwards. This can produce different output by array position for positive-only or negative-only bounds. The compatibility implementation documents and tests this instead of silently repairing the reference.

Normalised NaN-to-integer input is rejected instead of claiming to reproduce undefined native conversion. Arbitrary NaN clamp bounds, every CPU rounding mode, other SIMD backends, object layouts and performance parity remain outside this verified profile.

## Independent original-reference comparison

Original C++ test bodies are unchanged; include-only recording still executes the pinned GoogleTest comparisons. A separate Rust shadow records the same ordered events. Every one of the combined 1,661,546 assertion events is compared natively and in Chromium WebAssembly, with complete lossless transcripts retained. Eight native and nine browser floating differences remain in older colour cases under original rules. No additional differences or widened tolerances are introduced by this batch.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40108130160/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40108130160/browser-comparison.json) · [Full original-reference transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40108130160).

The production module is separately compiled, published and tested at its [actual immutable URL](https://rawcdn.githack.com/596050/blended/15a67995bdca8581e9f1e28b9b95af17ea69d51b/index.html). All 512 cases passed, with no recorded browser errors. Diagnostic local Chromium checks and production public-URL acceptance remain distinct evidence.

## Supplemental bit-exact oracle

`tools/verify_pixel_formats_oracle.py` compiles complete unedited `intern/math_half.cc` and uses the original normalised-int and SIMD headers. Source hashes, compiler flags, input bytes and generated drivers are retained. The reference explicitly selects SSE2/SSE4.1 without AVX or F16C, nearest-even rounding and a known denormal baseline.

The corpus checks all **65,536 half encodings**, including both signs, subnormals, infinities and NaN payloads, through scalar and array paths. It also checks **291,054 distinct float32 bit inputs**, including every finite half value, both sides of every positive half-rounding midpoint and their negative counterparts, exponent seams, payload variants and deterministic extra bit patterns. Arrays of lengths 0 through 17 use four rotations, output sentinels and three clamp intervals. This is exhaustive half decoding and an explicit rounding-boundary corpus, not all 2^32 float inputs.

Normalised-format checks use **2,183 finite component inputs** through eight format types and **133,632 raw-component configurations**, covering 8-bit, 16-bit and 10-bit component patterns and two-bit alpha variations. These are not all combinations of every multi-component packed vector. The oracle checks integer components, decoded floating-point bits and explicit canonical field packing, not raw C++ allocation bytes.

All **2,944,570 unsigned 32-bit output words match original C++ bit for bit** in native Rust and Chromium WebAssembly. Signed zero and NaN payloads are checked as bits instead of collapsed by numeric equality. Each output is 11,778,280 bytes, SHA-256 `1bb864de0f0688df82bc46f9506ae55e64463a977c501bcd202c8051b094c1c9`. The complete inputs, outputs and section layout are retained in the [immutable oracle evidence](https://github.com/596050/blended/tree/15a67995bdca8581e9f1e28b9b95af17ea69d51b/verification/evidence/pixel-formats-oracle). These observations are not additional Blender test ports.

## Test-first and failure sensitivity

[Run 40107140243](https://github.com/596050/blended/actions/runs/40107140243) generated and committed the original cases at `c094a5be126ceb6c10178f1a42aac4b4d5b2b1f2` before `pixel_formats.rs` existed. Cargo reported E0583 for that missing module. The [archived log](../evidence/pixel-formats-test-first-evidence.zip) is compilation failure before implementation, not nine executed failing assertions. Archive SHA-256: `1cd22d94fce939c5c2aa4f87fec453ee64cb26b0dfe273306eaf3a59c67b8149`.

Three isolated implementation mutations retain the original test sources: remove the half rounding bias, discard the sign of finite NaN conversion, or flush half subnormals to zero. Each fails its intended original case while an independent control passes, natively and in browser WebAssembly, retaining the original assertion counts. Compiler errors, panics and traps are not accepted as successful detection. [Mutation reports and logs](https://github.com/596050/blended/tree/15a67995bdca8581e9f1e28b9b95af17ea69d51b/verification/evidence/pixel-formats-sensitivity).

Seven additional native product tests cover signed zeros/payloads, ties-to-even, untouched tails, the pinned NaN clamp boundary, normalised truncation/raw signed minimum, two-bit alpha packing and actual nested FP-mode restoration. Nine Python regressions verify original identities, reproduction, active-versus-disabled accounting, boundary corpus inputs, binary-comparison sensitivity and mutation targets. These are not upstream cases.

## Remaining work

The complete Blender port is unfinished. The latest source audit has 5,859 candidates, 518 reviewed mappings and 5,341 unmapped declarations. Mappings comprise 512 runtime and six compile-time cases, not a complete runtime denominator or feature-parity percentage. Five conditional half benchmarks remain unported alongside many application-level families and further compile-time/configuration work. These core-library additions do not create a complete renderer or modelling application.
