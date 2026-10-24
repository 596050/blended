# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 541-case Blender test workbench](https://rawcdn.githack.com/596050/blended/c3edd21e2e953d5275768223b869cbbb9a22d42e/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Polygon verification](docs/POLYFILL-PORT-VERIFICATION.md) · [Whole-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modeller and test workbench are separate applications. The modeller remains the earlier object-editing alpha. The workbench was freshly compiled and publicly verified from source `efc7799e5050f28de66aa7ba11ed9a976165d21a`. Documentation-only commits may follow that runtime revision.

## Verified compatibility subset

**541 unique Blender runtime cases pass natively and in the actual deployed Chromium browser.** Independent comparisons against original Blender C++ execution check **3,196,218 ordered assertion events per implementation**. Eight native and nine browser floating differences remain in earlier colour cases within their original comparison rules. No tolerances were widened, and the new polygon cases add no floating differences.

The native Rust run passed **587 runtime tests**: 541 Blender ports, three Cycles integer-maths cases and 43 separate product/safety/regression tests. Six compile-time assertions separately pass positive builds and deliberate-failure checks on native and wasm32. Repeated assertions and supplemental diagnostic inputs are not extra Blender cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40142038492) · [Original-reference evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40142038492) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

## Latest implementation: polygon triangulation

All **29 runtime cases in `BLI_polyfill_2d_test.cc`** are ported, preserving **1,534,672 assertion executions** across the original loops, sign flips, topology/area checks and pre/post-beautification results. The Rust core implements ear clipping with concave-vertex KD-tree pruning and the original heap-driven half-edge beautification algorithm. It retains checked index storage rather than native pointer/arena layouts. These are mesh-library operations, not yet interactive mesh-editing tools.

The pinned upstream helper has a coverage gap: it rotates/reverses a copy but tests the original polygon. The port preserves that observable behaviour rather than silently changing upstream tests. A separate mandatory oracle genuinely exercises all cyclic shifts, both reversals and four coordinate-sign combinations for all original polygons: **3,064 configurations / 6,128 triangulation results / 133,968 triangle triplets**. Native Rust and Node.js WebAssembly match original C++ exactly, including triangle index order. The ordinary 541-case suite is separately tested in Chromium at its actual public URL. [Scope and evidence](docs/POLYFILL-PORT-VERIFICATION.md)

Degenerate/self-intersecting inputs retain the pinned index-topology behaviour, not a promise of a non-overlapping geometric fill. Holes, complete BMesh operations, allocator parity and performance parity are outside this batch.

## Accuracy and completion controls

Source snapshots, original identities, reviewed target hashes and generator reproduction are required. The executable registry must match all mandatory reviewed contracts. The historical lock file is unchanged; the polygon family uses an explicitly required contract shard, not an optional file discovered by a glob. Missing, duplicate or mismatched contracts fail rather than reducing scope.

Original C++ test bodies remain unchanged under include-only recording; Rust diagnostics run in a separate shadow build. Every assertion event is compared, not sampled or replaced by a summary hash. Complete transcripts are retained losslessly with verified decompressed hashes and sizes. Production WASM is separately tested at its immutable public URL. [Methodology](docs/ASSERTION-FIDELITY.md)

The scanner now retains digit-prefixed GoogleTest arguments such as `3Colinear`, recovering eight previously missed declarations. The latest heuristic audit has **5,867 source candidates, 547 reviewed mappings and 5,320 unmapped declarations**. The mappings comprise 541 runtime and six compile-time cases. These are not a complete runtime denominator or feature percentage. The whole-suite completeness job remains failed, and incomplete runtime discovery is unknown, never zero. [Completion issue #3](https://github.com/596050/blended/issues/3)

## Separate modeller and rendering experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection/transforms, duplication/deletion, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG output. Rust/WASM generates boxes and planes; Three.js generates spheres. Its legacy test button still uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no complete mesh/BMesh editor, sculpting, modifier/Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. The Solarxy/WebGPU experiment remains independently blocked by blank-viewport/device-loss failures. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI additionally fetches pinned Blender, reproduces translations/tables, builds original C++, executes exact-reference and diagnostic checks, publishes the explicitly incomplete subset and tests its public URL. The workbench build now requires the genuine polygon-permutation oracle before publication. Existing workflows were not changed for this batch. Earlier verification reports retain their historical source and scope.

## Hosting and notices

Source, static builds and durable evidence remain in this public repository. No paid backend or remote GPU was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Component-specific licences and attribution apply; consult source SPDX identifiers, [NOTICE.md](NOTICE.md) and `LICENSES/`. Original polygon source retains the LIBGDX ear-clipping attribution. Blended is independent of the Blender Foundation and Solarxy's author.
