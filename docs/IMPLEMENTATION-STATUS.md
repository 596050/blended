# Implementation status, 23 October 2026

## Verified source

`8bb0e6e43237cc68cf5e3c403dfc0b9419f083ed` consolidates the previously separate numeric, matrix, string, bit, geometry and sampling work. It has been promoted to `main`. Later documentation commits do not change the verified Rust implementation.

Run [40007823640](https://github.com/596050/blended/actions/runs/40007823640) completed the subset's source reproduction, fresh native compilation and execution, original pinned C++ execution, Rust/Chromium assertion comparison, production WebAssembly build and actual public-URL verification. The full-completeness job failed because full-suite coverage is not implemented.

| Measure | Verified result |
| --- | ---: |
| Unique Blender runtime ports | 338 |
| Original assertion executions compared per implementation | 16,804 |
| All native Rust runtime tests | 359 |
| Cycles cases included in that total | 3 |
| Product/safety/regression tests included in that total | 18 |
| Separately tracked compile-time assertions | 6 |
| Full Blender runtime denominator | Unknown |
| Full test port / feature parity | Not achieved |

The original assertion traces contain eight native and nine browser float differences within original tolerances. No tolerance was widened. They occur in earlier colour cases; the new image/curve cases added no such differences in this run.

## Newly implemented sampling

27 image-interpolation cases and nine length-parameterisation cases add 402 assertion executions. Exact original source snapshots, data, comparison kinds, expected values and loop lengths are preserved. CPU implementations include nearest, bilinear, B-spline and Mitchell sampling; border/repeat/extend modes; accumulated curve lengths; endpoint-aware uniform sampling; arbitrary-length sampling; and interpolated scalar/vector/colour values. They are not yet exposed as interactive editor features and do not establish GPU or renderer parity.

## Existing application

The Three.js object modeller remains a distinct alpha. It supports primitives, object transforms, basic appearance, undo/redo and limited interchange. It lacks Blender's comprehensive polygon editing, sculpting, modifiers, procedural nodes, animation, rigging, simulation, compositor, native blend files, Python add-ons and production rendering. The separate Solarxy-derived rendering failure remains unresolved.

## Outstanding whole-suite requirements

The latest heuristic source scan contains 5,859 candidates, of which 344 have reviewed mappings and 5,515 remain unported. These are not exact remaining runtime counts. The current runtime inventory is absent or incomplete, and the gate reports `unported_runtime_cases: null`. All configurations and runtime families, typed/parameterised expansions, Python, UI, render and CTest cases still require reconciliation. Nine vector type/layout compile-time assertions remain unported.

Previous test-asset retrieval verified 6,691 LFS objects under `tests/files/**`, but fresh reference checkouts must materialise the fixtures actually needed for execution. The source inventory retains pointers and does not claim those payloads are available merely because a historical download passed. The new sampling tests use source-embedded data rather than blend-file fixtures.

[Verification details](SAMPLING-PORT-VERIFICATION.md) · [Completeness requirement](COMPLETE-TEST-PORT.md) · [Current status JSON](../evidence/TEST-PORT-STATUS.json) · [Open completion issue](https://github.com/596050/blended/issues/3)
