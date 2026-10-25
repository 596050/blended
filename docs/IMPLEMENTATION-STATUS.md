# Implementation status

The current verified runtime revision is `8952a0ef18a83bb7a56656dd8519095bd0fb2cd2`, checked in [run 40145587317](https://github.com/596050/blended/actions/runs/40145587317). [Open the deployed workbench](https://rawcdn.githack.com/596050/blended/d32122067882b90b631adc1e4f765f708f10fe33/index.html). Subsequent documentation-only commits do not change that implementation.

## Executed scope

581 unique Blender runtime cases pass natively and at the actual public Chromium URL. Original C++ versus native Rust/Chromium comparisons check 3,196,371 ordered assertion events. Eight native and nine browser floating differences remain in older colour cases within original rules; none were added by the span batch and no tolerance was widened.

The full native Rust suite passed **634 runtime tests: 581 Blender, three Cycles and 50 product/safety/regression cases**. **Nineteen compile-time assertions** are separately mapped and verified: the prior six plus all thirteen span predicates. The new static-only conversion case remains a zero-runtime-assertion declaration, with executed case boundaries and independently tested compile-time requirements.

## Latest implementation

The complete `BLI_span_test.cc` source test file is mapped: forty runtime declarations, 153 executed assertions, five constant-value predicates and eight conversion-capability predicates. Rust views borrow backing storage; mutations are observable by existing views. Slicing, iteration, search, copy/fill/reversal, pointer relations and restricted casts are implemented for the tested types.

A compiled unedited original C++ header matches **473,659 supplemental observations** in native Rust and browser WebAssembly. All thirteen new compiler predicates pass positive builds and reject deliberately false forms on both targets. Three implementation mutations fail unchanged original tests with independent controls passing. The original trait/constructor inconsistency is documented instead of silently presented as equivalence. [Full span report](SPAN-PORT-VERIFICATION.md)

## Separate products and remaining work

The compatibility workbench is not the modelling application. The Three.js modeller remains the earlier object-editing alpha, and its legacy test button still exposes seventeen cases. The Solarxy/WebGPU rendering experiment remains separately blocked. New span/library ports are not new editing tools or a completed renderer.

The full-completeness job remains failed. The heuristic audit contains **5,867 source candidates, 600 reviewed mappings and 5,267 unmapped declarations**. The full runtime denominator remains unknown. Extensive application-level families, other compile-time predicates, conditional benchmarks, platform/configuration matrices and fixture-dependent workflows remain unfinished.

There is no full mesh/BMesh editor, sculpting, modifier/Geometry Nodes suite, animation/rigging/simulation system, compositor/video/tracking suite, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. Complete source porting, whole-suite execution, integrated feature parity and competitive performance are different milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Open completion issue #3](https://github.com/596050/blended/issues/3)
