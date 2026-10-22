# Implementation status, 22 October 2026

## Verified limited release

Source: `76044caffe2b69ae5cdceeff1addb56ee61411d9`.
Published static commit: `a81530a62fcc8222ea57db4c5d8b35869d277963` on `modeller-build`.
Actual deployed-URL acceptance: workflow run `39830750442`, report on `modeller-evidence/result.json`.

The 28 checks passed against the actual public URL. They exercise default Rust-generated cube geometry and visible rendered pixels; deletion and visual output changes; undo; another Rust cube; numeric translation and undo/redo; duplicate/delete; sphere; scene save; Rust plane; scene reopening; OBJ import/export; STL export/import; 17 runtime WASM compatibility cases; PNG output; and absence of browser errors. HTTP/provenance/scope checks are included in the 28, so it is not a count of 28 Blender features.

Core native results: 30 Rust tests, comprising 20 ported upstream cases, 6 new product geometry tests and 4 safety tests. Scene/history tests: 10 JavaScript cases. The pre-existing inventory/manifest infrastructure has 20 Python tests, separate from feature coverage.

## Failed experiment retained

The Solarxy-derived browser app compiles. Its selected `solarxy-core`, `solarxy-kernel` and `solarxy-graph` unit suites passed 1,002 tests, and its frontend passed 382 tests. These are existing Solarxy tests, not evidence of Blender parity.

Actual browser tests failed to render imported geometry. Some runs lost the GPU device and panicked on a later mapped-buffer allocation. The cause remains unresolved. The attempted Mesa setup still selected SwiftShader in the recorded browser, so it did not establish successful execution on an independent driver.

The diagnostic publication is clearly labelled as failing rendering acceptance. Its public URL was actually tested; the test remained failed. See issue #1 and `deployment-evidence`. The primary working modeller uses Three.js instead and is a separate feature subset, not a silent conversion of the failed test into a pass.

## Full-parity work is not done

The source scanner identified 5,637 Blender candidate declarations, but this includes compile-time assertions and unexpanded parameterised tests. It is not the complete set of runtime tests. Blender reference fixtures include 2,169 unresolved `.blend` LFS pointers. The full native reference build, complete fixture collection and complete runtime enumeration remain unfinished.

Only 17 Blender and 3 Cycles cases have been faithfully ported so far. There is no completed clone of Blender's mesh editing, BMesh, modifiers, sculpting, geometry-node suite, animation, rigging, physics, compositor, video editor, Python API, .blend serialization or Cycles/EEVEE engines. No percentage of full parity is claimed.

## Next test-driven milestones

1. Reference fixtures and runtime test enumeration, with exact provenance and external-data availability.
2. Direct mesh editing: component selection, topology edits, extrusion and normal/attribute preservation, compared against the pinned Blender reference.
3. Geometry operations and modifier compatibility with topology-aware differential tests.
4. Explicit material, colour-management and render-scene contracts before extending renderer comparisons.
5. Browser/device matrix, stable-host deployment, performance budgets and large-scene memory tests.

Every batch must preserve upstream expected values and assertion semantics, prove an intended failure before a new implementation where applicable, and run native/WASM/deployed browser checks separately. Unsupported or unavailable tests must never become passes by omission.
