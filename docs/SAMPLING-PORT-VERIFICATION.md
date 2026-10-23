# Image and curve sampling port verification

## Verified source and scope

Project source `8bb0e6e43237cc68cf5e3c403dfc0b9419f083ed` contains 338 unique Blender runtime cases. Original reference: `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Run [40007823640](https://github.com/596050/blended/actions/runs/40007823640) passed fresh native execution, the original C++ comparison, diagnostic Chromium execution and the production workbench at its actual public URL. The full-suite completeness job remains failed.

| Newly ported complete source file | Runtime cases | Original assertion executions |
| --- | ---: | ---: |
| BLI_math_interp_test.cc | 27 | 180 |
| BLI_length_parameterize_test.cc | 9 | 222 |
| Total added | 36 | 402 |

These extend the previous 302 cases and 16,402 assertion executions to 338 cases and 16,804 executions. The 359-test native Rust suite also contains three Cycles cases and 18 product/safety/regression cases. Counts are not a feature-parity percentage.

## Test-driven development and fidelity

The source-locked translator and test-first workflow were committed before the implementations. Run [40005538302](https://github.com/596050/blended/actions/runs/40005538302) generated the original test cases and failed on missing Rust modules. This is missing-implementation evidence, not 36 observed assertion failures.

The initial implementation compilation caught a translator bug: matching `int4` inside `uint4` produced an invalid call. The corrected translation retains the unsigned constructor as `u32`, with explicit signed/unsigned regression tests and a newly reviewed generated-target hash. Original expectations and tolerances were not edited. Fresh native compilation, all 359 runtime tests and the infrastructure checks subsequently passed before registration.

The image cases preserve all original image channels, coordinates, wrap modes, expected values and scalar/vector comparisons. Original EXPECT_V4_NEAR expands into four nonfatal scalar comparisons, not one Boolean shortcut. The byte constructor casts remain explicit. The curve tests retain their complete expected arrays, helper assertions, cyclic/noncyclic choices and both 5,007-sample workloads. No loop was reduced to make testing faster.

## Implementation boundaries

The Rust image kernel provides nearest-border, bilinear and cubic B-spline/Mitchell sampling with extend, border and repeat handling. It retains the exercised scalar/SSE accumulation ordering without claiming identical machine instructions or GPU throughput. Buffer dimensions are validated before indexing. Original implementation attribution and SPDX notices are preserved.

The curve kernel accumulates source lengths and produces segment indices and interpolation factors for uniform or arbitrary lengths. The include-last convention, cyclic segment interpolation and scalar/vector/colour interpolation remain observable. The implementation is serial; native Blender task scheduling and parallel performance are not reproduced by these assertions.

Array/vector storage is represented by safe Rust arrays and slices. No renderer, scene-graph or interactive editor parity follows merely from these CPU kernels passing their tests. Unasserted results, including exact infinity-output bytes, are not certified.

## Independent original-C++ comparisons

All 338 original test cases execute in the pinned BLI reference executable. The include-only recorder leaves original test bodies unchanged. Case boundaries and all 16,804 ordered assertion events are compared with the Rust diagnostic builds. Eight native and nine browser float differences remain in earlier colour tests, within their original rules; the new image and curve comparisons added none. No tolerance was broadened.

The public test workbench uses the unmodified production module. Its immutable build is `a5fc4aa4074e556431c8e7fd1bb1185f130b3be0`. It passed all 338 cases with no recorded browser errors. Production WebAssembly SHA-256: `2480612838fa88c7546bcc2a3cdb419ba70a9b75132e525cc26763730ea0b30a`.

[Public workbench](https://rawcdn.githack.com/596050/blended/a5fc4aa4074e556431c8e7fd1bb1185f130b3be0/index.html) · [Immutable-run trace evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40007823640)

## Implementation sensitivity, not manufactured successes

Run [40007823637](https://github.com/596050/blended/actions/runs/40007823637) first executes all 36 unmodified new cases, then changes only implementation code in an isolated diagnostic copy. Test-body hashes stay unchanged.

The byte border sampler is deliberately changed to extend edge pixels. Its original three assertions fail while an independent nearest-sampling control passes. Uniform curve spacing is deliberately changed to ignore include-last. The original seven-assertion scalar case fails. Both behaviours are verified natively and in Chromium WebAssembly; a compiler error or browser trap would fail the diagnostic rather than count as detection.

A separate counter observes the original infinity-coordinate smoke call once, while that unchanged test still passes. This establishes that the translated source reaches the operation; it does not invent an expected pixel value for a source test that never asserted one. The counter and mutations are absent from the production build.

[Preserved sensitivity result](../evidence/sampling-338/sensitivity.json)

## Remaining coverage

The corrected source scan has 5,859 candidates, 344 reviewed mappings and 5,515 unmapped candidates. Six mappings are compile-time assertions. A complete runtime denominator remains unknown. Python/UI/render/CTest families and most mesh, animation, simulation, file and renderer functionality remain unfinished. Keep completion issue #3 open. Passing this batch must never be relabelled as a complete Blender port.
