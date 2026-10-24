# Implementation status

## Current verified implementation

Source `2990e30077e368c97e3a7af60d45d7a911ceb988` was verified in [run 40108130160](https://github.com/596050/blended/actions/runs/40108130160). [Open the 512-case public workbench](https://rawcdn.githack.com/596050/blended/15a67995bdca8581e9f1e28b9b95af17ea69d51b/index.html). Later documentation-only commits do not change that implementation.

512 unique Blender runtime cases pass in native Rust and at the actual deployed URL, covering 1,661,546 expected assertion executions. Independent original-C++ versus native Rust and Chromium comparisons passed. Eight native and nine browser floating differences remain in earlier colour cases under original rules; no tolerance was widened. The new format tests add no additional differences.

The native total is **558 runtime tests: 512 Blender, three Cycles and 43 separate product/safety/regression tests**. Six compile-time assertions pass positive builds and deliberate-failure checks separately on native and wasm32. Repeated stress assertions, supplemental oracle inputs and mutation probes are not extra upstream cases.

## Latest functionality

Nine enabled original cases now cover half-float scalar/array conversion and normalised integer formats, with 169 original assertions. Five conditional half-performance benchmarks remain explicitly unported and not passing. The Rust implementation retains round-to-nearest-even, finite-result conversion, output sentinels, original normalised truncation and the selected scalar/SSE2 array boundary semantics.

The independent oracle exactly matches 2,944,570 output words against unedited original C++, including every half encoding, all selected half-rounding boundaries, signed zero, NaN payloads, raw normalised components and array tails. Three deliberately broken implementations fail unchanged original tests with independent controls passing. Native x86_64 tests actually set and restore FTZ/DAZ; browser checks do not claim that inaccessible hardware perturbation. F16C/NEON profiles, ABI layout and SIMD speed remain outside the certification. [Detailed report](PIXEL-FORMAT-PORT-VERIFICATION.md)

## Separate products and evidence

The workbench tests the compatibility core. The Three.js modeller remains the earlier object-editing alpha; these additions are not new interactive tools or a complete renderer. Its legacy test button still uses the 17-case ABI. The Solarxy/WebGPU experiment remains independently blocked.

Fresh compilation, original-reference comparisons, diagnostic browser checks and public-URL acceptance are separate evidence categories. Historical smaller records retain their source revisions and scope. Full-event transcripts remain lossless and are compared without sampling, including the earlier 1.6-million-assertion UTF-8 stress case.

## Unfinished requirements

The complete Blender test port remains unfinished and its whole-suite gate remains failed. The latest heuristic scan has **5,859 source candidates, 518 reviewed mappings and 5,341 unmapped declarations**. Full runtime discovery and the remaining runtime count are unknown. Additional vector type/layout compile-time checks, opt-in benchmarks, required configuration matrices and extensive application-level families remain outstanding.

There is no complete mesh/BMesh editor, sculpting, modifier/Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. Full test porting, whole-suite conformance, integrated feature compatibility and competitive performance remain separate milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Completion blocker #3](https://github.com/596050/blended/issues/3)
