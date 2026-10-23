# Implementation status, 23 October 2026

## Current original-Blender work

The active parity branch now builds the pinned Blender 5.2 browser port and
runs unchanged original Blender invocations. The selected unittest scope has
829 obligations and 516 strict successful native/browser pairs on the
separately qualified Essentials package. A separate original mesh-driver
profile qualifies all 88 bevel cases. These counts have distinct scopes and
are not combined into a whole-application percentage. The complete results,
remaining failures, exact source/package identities and ongoing source build
are recorded in [original test parity status](TEST_PARITY_STATUS.md).

The new implementation integrates real SQLite with CPython `_sqlite3` and the
WebP, OpenJPEG, AOM, libheif and OIIO dependency closure. Actual component
builds and diagnostics pass; original application qualification on the new
complete engine is still pending. The published implementation is
`f25e69ed72fed2d31d7d65e657fd6515da4bd792`, with 346 infrastructure tests passing
both locally and in GitHub CI. Infrastructure checks do not count as original
Blender feature passes.

The following limited modeller and Solarxy results are historical,
separately scoped experiments from 22 October. They remain available and do
not supply parity evidence for the pinned original-Blender engine.

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

The separate Blender 5.4 product-source scanner identified 5,637 candidate declarations, including compile-time assertions and unexpanded parameterised tests. It is not the complete set of runtime tests. All 7,353 candidate fixture paths and all 7,053 original source-archive LFS paths are now verified and hydrated. Two native configurations expose 1,140 and 1,416 original CTest registrations. Selected original C++ executions provide 2,258 distinct native observations, comprising 2,257 passes and one original platform skip. The complete native build, cross-platform runtime enumeration and product-version browser qualification remain unfinished. These product-source results do not transfer passes to the separate 5.2 browser candidate.

The historical Rust modeller has 17 ported Blender and 3 ported Cycles cases. The active browser-port work runs additional unchanged original Blender cases as described above. Neither experiment establishes complete Blender mesh editing, BMesh, modifiers, sculpting, geometry nodes, animation, rigging, physics, compositor, video editor, Python API, `.blend` serialization or Cycles/EEVEE parity. No percentage of full parity is claimed.

## Next test-driven milestones

1. Reference fixtures and runtime test enumeration, with exact provenance and external-data availability.
2. Direct mesh editing: component selection, topology edits, extrusion and normal/attribute preservation, compared against the pinned Blender reference.
3. Geometry operations and modifier compatibility with topology-aware differential tests.
4. Explicit material, colour-management and render-scene contracts before extending renderer comparisons.
5. Browser/device matrix, stable-host deployment, performance budgets and large-scene memory tests.

Every batch must preserve upstream expected values and assertion semantics, prove an intended failure before a new implementation where applicable, and run native/WASM/deployed browser checks separately. Unsupported or unavailable tests must never become passes by omission.
