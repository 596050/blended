# Implementation status

## Verified source and deployment

The current documented compatibility implementation is `df61b87fa3b2b5a0751100e427eab11d7205ad5a`, verified by [run 40019426923](https://github.com/596050/blended/actions/runs/40019426923). [Open the 367-case workbench](https://rawcdn.githack.com/596050/blended/19abc219cd1ccb7e2dd4090c23710638f30959d8/index.html). Documentation commits can follow the verified source without changing the runtime implementation.

367 unique Blender runtime cases pass natively and at the actual public URL, with 33,104 expected assertion events. Original C++ versus native Rust and Chromium WebAssembly comparisons passed. Eight native and nine browser floating differences remain within original rules; exact equality and original tolerances were not loosened. The native total is 390 tests, comprising 367 Blender, three Cycles and 20 product/safety/regression cases. Six separately tracked compile-time assertions pass positive and negative checks on both targets.

The latest 29-case heap batch adds real implementations for handle-based and simple min-heaps, externally mutable integer priorities and the pinned random generator/shuffle. Independent input verification matched 15,000 values and 3,175 shuffled items. Native/browser negative controls detect broken removal and priority-increase logic using unchanged source tests. See [HEAP-PORT-VERIFICATION.md](HEAP-PORT-VERIFICATION.md).

## Distinct products and evidence

The workbench exercises the compatibility core. The separate Three.js modeller remains an object-editing alpha with transforms, bounded undo/redo, basic materials, scene JSON, static OBJ/STL interchange and PNG output. The new library cases are not new interactive Blender tools. The modeller's legacy test button still uses a 17-case interface. The Solarxy/WebGPU rendering experiment remains independently blocked and does not inherit the modeller's successful acceptance results.

Fresh builds, original-reference comparisons, diagnostic browser checks and actual public-URL tests remain separate evidence categories. Old 99/131/211/272/302/338-case runs retain their historical scope. Deterministic-input and mutation probes are not counted as new upstream test cases.

## Unfinished requirements

The complete Blender test port is not finished. The full-completeness gate remains failed. The latest heuristic source audit contains 5,859 candidates, 373 mappings and 5,486 unmapped declarations; the full runtime denominator remains unknown. Nine previously identified vector type/layout compile-time conditions and extensive application-level families remain outside this verified subset. Fixture verification from a previous run does not materialise fixtures in a fresh checkout.

There is no full mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. A complete test port, successful whole-suite execution, feature compatibility and competitive performance remain separate milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Open completion issue #3](https://github.com/596050/blended/issues/3)
