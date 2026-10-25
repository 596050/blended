# Span views and compile-time contract verification

## Verified scope

Reference Blender: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Project runtime revision: `8952a0ef18a83bb7a56656dd8519095bd0fb2cd2`.
Verification: [run 40145587317](https://github.com/596050/blended/actions/runs/40145587317).

The complete `BLI_span_test.cc` source file is mapped: **40 runtime declarations, 153 runtime assertion executions and 13 separate compile-time predicates**. The combined suite contains **581 Blender runtime cases / 3,196,371 assertion events**. All pass in native Rust and at the actual [public Chromium workbench](https://rawcdn.githack.com/596050/blended/d32122067882b90b631adc1e4f765f708f10fe33/index.html), with no recorded browser errors. The full native suite passes 634 runtime tests: 581 Blender, three Cycles and 50 separate product/safety/regression cases.

The compile-time total rises from six to **nineteen**. The original `span.ImplicitConversions` runtime declaration contains only static checks: it is executed and traced with **zero runtime assertions**. Its eight conversion predicates are independently checked by the compiler, not replaced with constant runtime Booleans or added to runtime assertion totals.

## Source fidelity and implementation

Original source Git blob: `9ff9fb5391b81d999a231e6785cb7efa07beaf6a`; SHA-256: `2cf7cfb2188f4181c3f51ef0ab8b0c217ac7e7a7c095e9849651e5f763bba43c`.
Reviewed generated Rust test SHA-256: `2ca5f78a2ea21751394c6f41f7a227acb202158fd5ed2a712f3d38e6510b968c`.

`tools/port_span_tests.py` is a finite reviewed adapter. It checks the complete original file, retains every case identity, source line, original body hash, expected value and helper-expanded count, and reproduces committed runtime and compile-time manifests. Original `EXPECT_EQ_SPAN` helpers retain their length assertion and conditional per-element comparisons. Pointer checks use actual addresses, not equality of pointed-to values. The mutable reverse iterator still updates the original storage.

The Rust implementation borrows its backing memory. Read-only views over Cell-backed storage observe later mutations; mutable views retain shared storage instead of snapshots. The tested operations cover slicing, dropping/taking, search/counting, filling, copying, reversal, iteration, byte lengths, pointer membership and restricted byte-preserving casts. Only sealed numeric-to-numeric or raw-pointer-to-raw-pointer casts are exposed safely; references, bools, padded objects and arbitrary user types are not accepted by that cast API.

This is a behavioural adaptation, not a claim of identical C++ syntax, ownership, allocator or object layout. Rust value access copies individual Copy elements rather than returning unrestricted C++ references. Const-evaluated search helpers are specialised for the i32 conditions actually tested. Oversized empty views are safely clamped instead of manufacturing out-of-allocation pointers. These differences remain explicit.

## All thirteen static predicates are exercised

The original five constant-value predicates check element access, size, sliced size, duplicate detection and first-index evaluation. The eight conversion predicates check five permitted and three forbidden view/pointee-constness conversions. Rust From/Into constraints express the declared capabilities; forbidden conversions use a compile-time ambiguity check rather than a runtime assertion.

The unmodified reviewed library compiles for native and wasm32. `tools/verify_span_static.py` then creates isolated shadows, changing only one predicate's input or operation at a time while preserving its expected value/mechanism. Every deliberately false predicate must be rejected with its intended diagnostic, pointing to the translated source: E0080 for constant evaluation, E0277 for missing conversion capabilities and E0283 for a deliberately violated negative capability check. Missing compilers/modules, unrelated source errors and arbitrary compilation failures do not count.

**All thirteen predicates pass positive compilation on both targets; all 26 negative compilations reject the intended false predicate.** These are compile-time checks, not 26 extra upstream cases. The previous six static checks continue to run separately. Both static manifests and their reviewed contracts are required; removing or duplicating one fails the inventory/verification checks. [Full compiler results and logs](https://github.com/596050/blended/tree/d32122067882b90b631adc1e4f765f708f10fe33/verification/evidence/span-static).

## Independent runtime comparison and input oracle

Original C++ test bodies remain unchanged. Include-only recording invokes original GoogleTest assertions. The separate Rust diagnostic shadow records corresponding case boundaries and ordered values. All 3,196,371 assertion events reconcile with the reviewed rules on native Rust and Chromium. Eight native and nine browser floating differences remain in older colour cases, within original rules; no tolerances were widened and the span batch adds none. [Original-reference transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40145587317).

Pointer transcripts use pair-local alias/null labels across processes, while the actual original/replacement assertions evaluate real pointer equality. A separate oracle additionally compares within-allocation slice offsets and live pointer-slot relationships. The production workbench is separately built and tested at its actual public URL; local diagnostic browser execution is not substituted for deployment verification.

`tools/verify_span_oracle.py` compiles the **unedited original `BLI_span.hh`**, hash `10a4bf1b95358a4f8eafb18a728f3d2131f5a0cbf337648f44d010d11fd9ad60`. Its explicit corpus covers lengths zero through 32, every legal contiguous slice of those arrays, oversized bounded operations, search values, reverse iteration, externally visible mutations, copy/fill/reversal, byte casts and pointer-slot aliases. Underlying C++ storage is large enough for all pointer arithmetic used by that driver. Empty oversized views compare size/content, not an invalid pointer location. Byte-cast observations use memcpy on the C++ side rather than dereferencing an incompatible reference type.

**All 473,659 output words match exactly** between original C++, native Rust and Chromium WebAssembly. Each output is 1,894,636 bytes with SHA-256 `f6cd48aad6a27d9a29cfbeb646dae9e089138900574deafb6d78377bbe6b03a2`. These are supplemental observations, not additional Blender cases. They cover the stated corpus and tested x86_64/wasm32 targets, not all possible types, lifetimes, layouts or inputs. [Inputs/drivers, outputs and report](https://github.com/596050/blended/tree/d32122067882b90b631adc1e4f765f708f10fe33/verification/evidence/span-oracle).

## A pinned-reference trait/constructor discrepancy

The original static trait says `MutableSpan<int*>` is convertible to `MutableSpan<const int*>`. However, actually instantiating that constructor in the unedited pinned header fails at its `static_cast` from `int**` to `const int**`. The oracle retains a separate compiler reproduction proving that the type-trait predicate succeeds while the actual constructor fails.

The original static test is still ported faithfully. Rust implements the declared From capability, and a separate product test checks its live pointer-slot behaviour. That operational implementation is **not** claimed as successful execution of the broken original constructor. The failing original operation is excluded explicitly from the value-equivalence corpus and recorded in `original_conversion_limit`; it is not silently fixed inside the original C++ source.

## Test-first and runtime failure sensitivity

The forty native case runners were committed at `968e8f3b16e410477641f2634c4b497ddd3de1ab` before `span_cases` existed. [Run 40144608696](https://github.com/596050/blended/actions/runs/40144608696) recorded forty E0433 unresolved-module diagnostics. This is missing-implementation compilation evidence, not forty executed failing assertions. The [durable summary](../evidence/span-test-first-summary.json) records source, run, artifact and log hashes; the original complete log remains subject to Actions artifact retention.

Three implementation-only mutations disable filling, reversal or copying. Each causes the intended unchanged original test to report failures while an independent original control still passes, natively and in Chromium WebAssembly. Original assertion counts remain 5, 12 and 5 for the target cases; invalid case indices remain rejected. Compiler errors, panics and browser traps are not accepted as successful detection. [Mutation evidence](https://github.com/596050/blended/tree/d32122067882b90b631adc1e4f765f708f10fe33/verification/evidence/span-sensitivity).

Seven additional native product regressions cover shared views, double-ended iterators, byte casts, safe oversized views, pointer slots, mutable-slice writeback and untouched storage outside copied subviews. Twelve Python checks cover source completeness, all static predicates, required manifests, exact mutation targets and the original constructor limitation. They are not upstream case counts.

## Completion and integration limits

The source audit contains 5,867 candidates, 600 reviewed mappings and 5,267 unmapped declarations. Mappings comprise 581 runtime cases and 19 compile-time assertions. Full runtime discovery remains incomplete, so its remaining denominator is unknown. The whole-suite gate remains failed.

The span tests do not prove all C++ template specialisations, native ABI/allocator equivalence, general memory safety, thread-safety or performance parity. They add core-library operations, not interactive mesh tools or a complete Blender renderer. Remaining compile-time conditions, conditional benchmarks and application-level families remain open under issue #3.
