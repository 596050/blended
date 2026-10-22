# Compatibility acceptance contract

Blender and Cycles are pinned executable-reference targets. The full application direction is now an existing source-derived Blender browser port, with candidate qualification and facet-by-facet acceptance defined in [BROWSER_PARITY_PROGRAM.md](BROWSER_PARITY_PROGRAM.md). The existing Solarxy and Three.js experiments retain separate results. Reusing upstream source is intentional; its provenance and licences are retained.

## Separate measurements

1. Source discovery: candidate declarations and source fixtures, all initially not_run/not_ported.
2. Runtime enumeration: tests expanded with supported build configurations, dependencies, parameters and external fixture availability. Not yet complete.
3. Port traceability: upstream commit, source file, case identity, assertions, input assets, comparison policy and destination.
4. Execution: distinct native, WebAssembly, GPU and deployed-application results.
5. Feature/workflow coverage: operations not covered by upstream tests still require explicit acceptance checks.

There is no meaningful full-parity percentage until the denominator and feature contract are defined. A passed source scan is not a passed Blender test. A disabled suite, missing fixture, ignored test or unsupported feature never contributes a pass.

## Initial scope

The 17 runtime tests in Blender BLI_math_vector_test.cc are translated with exact expected values, four-ULP float equality and 1e-6 absolute tolerances as applicable. Its signed-zero hash static assertion is unported. Three Cycles util_math_test.cpp cases preserve 23 expected integer outputs. Browser and native integration statuses are separate.

The working limited browser modeller uses Rust geometry and Three.js. The pinned Solarxy experiment separately failed browser rendering acceptance. Neither establishes Blender's modelling, sculpting, modifiers, Geometry Nodes, animation/rigging, simulation, compositing, video, Python API or .blend compatibility. No Cycles-to-Rust renderer has been implemented. The new source-port candidate probe and its exact older Blender reference are recorded separately; no candidate or infrastructure result implies product-target parity.

## Release gates

- Correct expected commit served from the real deployment URL.
- WebAssembly case results obtained by executing the built module, never fabricated JSON.
- Browser engine boot, model import and undo/redo checked through the visible UI.
- Missing geometry, attribute, material, image and scene semantics reported as incompatibilities.
- Stochastic rendering comparisons use explicit controls and justified tolerances, never silently relaxed thresholds.
- Performance and resource use measured independently of correctness.
- Preserve test licences, fixture licences, source notices and corresponding source for browser binaries.

Future work: complete upstream runtime discovery, acquire external fixtures, differential geometry and render harnesses, integrate compatible Rust operations into the actual editor, expand workflow coverage, and port remaining subsystems.
