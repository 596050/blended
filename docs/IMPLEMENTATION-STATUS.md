# Implementation status

## Current verified implementation

Source `f86fae88ce889175fcaa11dcb982d3bbc4fce5ca` was verified in [run 40149763130](https://github.com/596050/blended/actions/runs/40149763130). [Open its 596-case public workbench](https://rawcdn.githack.com/596050/blended/4cc3dade093dd7da5899ed995e02ce3689225fb2/index.html). Later documentation-only commits do not change the tested runtime.

596 unique Blender runtime cases pass natively and at the actual deployed URL, covering 3,196,692 expected assertion executions. Original-C++ versus native Rust and Chromium comparisons passed. Eight native and nine browser differences remain in earlier colour cases under original rules; no tolerance was widened. The new mask-expression cases add no floating differences.

The native total is **656 runtime tests: 596 Blender, three Cycles and 57 product/safety/regression tests**. Nineteen compile-time predicates remain separately verified with positive builds and deliberate-failure checks on native and wasm32. Repeated stress assertions, supplemental oracle inputs and negative probes are not extra upstream cases.

## Latest functionality

Fifteen enabled original index-mask expression cases now cover set unions/intersections/differences, complements, range terms, sparse and large masks, and nested expressions. They retain all original randomized iterations and add 321 runtime assertions. One disabled benchmark remains unported.

The Rust implementation stores canonical intervals and evaluates expressions without expanding every index of a large contiguous range. Original arena allocation, native segment representation, TBB scheduling, complete IndexMask API and performance parity are not established. Small segment-count observations in the original cases are preserved without claiming general internal-layout identity.

A separate original-C++ probe matches all 14,573,457 random Boolean inputs and 147,456 supplemental mask results, including 370,176 absolute selected indices, against native Rust and Chromium. The first supplemental attempt exceeded a pinned constructor's 2^31 static range and failed; the corrected probe respects that domain without editing original tests. Three implementation-only mutations fail unchanged source cases while controls pass. [Detailed report](MASK-EXPRESSION-PORT-VERIFICATION.md)

## Separate products and evidence

The workbench tests the compatibility core. The Three.js modeller remains the earlier object-editing alpha; these library additions are not new interactive tools or a complete renderer. Its legacy test button still uses the 17-case ABI. The Solarxy/WebGPU experiment remains independently blocked.

Fresh native compilation, original-reference comparison, local diagnostic browser execution and actual deployed-URL acceptance are separate verification layers. Earlier smaller runs retain their original revisions and scope. Every current assertion event is compared without sampling and full diagnostic tapes are retained losslessly.

## Unfinished requirements

The complete Blender test port is unfinished and the whole-suite gate remains failed. The latest heuristic scan has **5,867 source candidates, 615 reviewed mappings and 5,252 unmapped declarations**. Complete runtime discovery and its remaining count are unknown. Conditional benchmarks, further compile-time checks, platform/configuration matrices and extensive application-level families remain outstanding.

There is no complete mesh/BMesh editor, sculpting, modifier/Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. Complete test porting, whole-suite conformance, integrated feature compatibility and competitive performance remain distinct milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Completion blocker #3](https://github.com/596050/blended/issues/3)
