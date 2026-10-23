# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 338-case Blender test workbench](https://rawcdn.githack.com/596050/blended/a5fc4aa4074e556431c8e7fd1bb1185f130b3be0/index.html)

[Deployment details](LIVE.md) · [Current implementation status](docs/IMPLEMENTATION-STATUS.md) · [Sampling verification](docs/SAMPLING-PORT-VERIFICATION.md) · [Complete-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modeller and test workbench are different applications. The linked modeller is the previously verified object-editing alpha. The linked workbench was compiled and publicly verified from source `8bb0e6e43237cc68cf5e3c403dfc0b9419f083ed`. The source implementation, including the previously unmerged integration, is now on `main`; documentation-only commits may follow the verified source revision.

## Verified compatibility subset

**338 unique Blender runtime cases pass natively and in the actual deployed browser**, with **16,804 assertion executions**. Independent original-C++ versus Rust and Chromium WebAssembly comparisons passed. Eight native and nine browser floating-point differences remain within the original comparison rules; no tolerance was widened. The new sampling families introduced no additional floating differences in those comparisons.

The native Rust total is **359 runtime tests**: 338 Blender ports, three Cycles integer-maths cases and 18 product, safety and regression tests. Six separately tracked compile-time assertions pass positive builds and deliberately broken negative checks on native and wasm32. They are not included in the 338 runtime total.

[Original C++ / Rust / WASM / deployed verification](https://github.com/596050/blended/actions/runs/40007823640) · [Immutable-run assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40007823640) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

The latest implementation adds all **27 image-interpolation cases** in `BLI_math_interp_test.cc` and all **nine curve-sampling cases** in `BLI_length_parameterize_test.cc`. Their 402 assertion executions retain the original images, expected results, tolerances, helper checks, wrapping modes and 5,007-sample loops. The CPU kernels provide nearest/bilinear/cubic sampling, length accumulation, uniform and arbitrary-length resampling, and interpolation. These library additions are not a complete browser renderer or interactive curve editor.

## Accuracy controls

Every registered case has pinned source identity, source snapshots and reviewed target hashes. Generators must reproduce committed tests. The registry and reviewed contracts must match exactly. Ordered assertion traces compare kinds, operands, outcomes, counts and tolerances against the pinned original Blender executable. Original C++ test bodies remain unchanged; diagnostic instrumentation and raw evidence are retained. Production WebAssembly is separately tested at its actual public URL.

Negative controls confirm that broken border handling and wrong endpoint spacing fail the unchanged tests, while independent controls continue to pass. A diagnostic counter verifies that the original infinity-input smoke call is still executed. These checks are not extra upstream test ports. [Sensitivity evidence](evidence/sampling-338/sensitivity.json)

The full-completeness CI job remains genuinely failed. The current heuristic source scan has **5,859 candidates, 344 reviewed mappings and 5,515 unmapped candidates**. The mappings are 338 runtime cases and six compile-time cases. These are source declarations, not a complete runtime denominator. Missing or stale runtime enumeration is reported as unknown, never zero. Conditional, generated, typed, external and platform-specific work still needs reconciliation. [Completion blocker #3](https://github.com/596050/blended/issues/3)

## Limited modeller

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection and transforms, duplicate/delete, bounded undo/redo, basic material controls, scene JSON save/reopen, static OBJ/STL import/export and PNG viewport output. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. Its historical public acceptance run checked rendered pixels and editing/interchange workflows. The modeller's legacy test button still uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no comprehensive mesh editor, sculpting, Blender modifiers or Geometry Nodes system, animation/rigging/physics suite, compositor, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. OBJ export does not include materials. A separate Solarxy/WebGPU rendering experiment remains blocked by blank-viewport/device-loss failures; this modeller does not inherit that editor's procedural features. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI additionally fetches pinned Blender sources, reproduces the source-locked translations, builds the original reference, compares native/browser traces, publishes the explicitly incomplete subset and tests its public URL. The whole-suite completeness gate is independent of subset publication.

## Hosting, source and notices

Source, static builds and durable evidence are stored in this public repository. No paid backend or remote GPU service was provisioned. The current preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Original test and implementation licences and attributions are retained; consult each file's SPDX identifier and NOTICE.md. This project is independent of the Blender Foundation and Solarxy's author.
