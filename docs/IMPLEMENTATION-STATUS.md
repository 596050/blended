# Implementation status

## Verified implementation and deployment

Source `059bfb9b277e8bc5aefb9834dd671879094a0599` passed [run 40045600207](https://github.com/596050/blended/actions/runs/40045600207). [Open the 416-case workbench](https://rawcdn.githack.com/596050/blended/63655e85d5b56c357645c92e3874af3940fd161e/index.html). Documentation commits may follow without changing this verified runtime implementation.

416 unique Blender runtime cases pass in native Rust and at the actual public URL. Original-C++ comparisons check 33,368 assertion events in native Rust and Chromium WebAssembly. Eight native and nine browser colour differences stay within original rules; no tolerances were loosened. Native Rust totals 444 tests: 416 Blender, three Cycles and 25 product/safety/regression cases. Six compile-time assertions pass positive and negative checks on both targets.

The newest batch adds 49 cases from four complete original runtime test files: array utilities, CSV parsing, Murmur2A and disjoint sets. Their implementations retain the exercised input and assertion semantics, including 100,000-element grouping cases. A separate streaming oracle matches 31,776 outputs exactly across 10,592 configurations. Four native/browser mutation controls detect deliberately broken code using unchanged source tests. [Detailed evidence and limits](DATA-PORT-VERIFICATION.md)

## Separate products and evidence layers

The compatibility workbench is not the modeller. The Three.js modeller remains an object-editing alpha with transforms, bounded undo/redo, basic materials, scene JSON, static OBJ/STL interchange and PNG output. Its legacy test button still uses the 17-case ABI. These library ports do not add corresponding interactive tools. The Solarxy/WebGPU experiment remains independently blocked by rendering failures.

Fresh builds, original-reference comparisons, diagnostic browser probes and actual public-URL tests remain separate evidence categories. Supplemental corpora, mutated implementations and product regressions are not counted as upstream Blender cases. Historical evidence retains its own source revisions and scope.

## Still unfinished

The full Blender test port and whole-suite execution are unfinished; the completeness gate remains failed. The heuristic scan has 5,859 candidates, 422 mappings and 5,437 unmapped declarations. A complete runtime denominator is still unknown. Additional compile-time conditions and extensive mesh/BMesh, modifier, node, animation, simulation, rendering, file-format, Python and UI families remain unported. Historical fixture verification does not materialise data in fresh execution checkouts.

There is no complete Blender modelling/rendering application, native .blend support or Cycles/EEVEE parity. Full tests, feature/workflow compatibility, broad browser coverage and performance remain distinct requirements.

[Current status JSON](../evidence/TEST-PORT-STATUS.json) · [Complete-suite requirements](COMPLETE-TEST-PORT.md) · [Completion issue #3](https://github.com/596050/blended/issues/3)
