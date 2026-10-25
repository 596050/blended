# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 596-case Blender test workbench](https://rawcdn.githack.com/596050/blended/4cc3dade093dd7da5899ed995e02ce3689225fb2/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Latest mask-expression verification](docs/MASK-EXPRESSION-PORT-VERIFICATION.md) · [Whole-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modeller and test workbench are separate applications. The modeller remains the earlier object-editing alpha. The workbench was freshly compiled and publicly verified from source `f86fae88ce889175fcaa11dcb982d3bbc4fce5ca`. Documentation-only commits may follow that tested implementation.

## Verified compatibility subset

**596 unique Blender runtime cases pass natively and at the actual deployed Chromium URL.** Independent original-C++ versus native Rust and Chromium WebAssembly comparisons check **3,196,692 ordered assertion events per implementation**. Eight native and nine browser floating differences remain in older colour cases under their original rules. No tolerance was widened; the new mask-expression cases introduce no additional differences.

The full native Rust suite passed **656 runtime tests: 596 Blender ports, three Cycles cases and 57 separate product/safety/regression tests**. **Nineteen compile-time predicates** remain separately mapped and verified on native and wasm32, including deliberate-failure checks. Repeated assertions, supplemental inputs and negative probes are not additional upstream cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40149763130) · [Original-reference evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40149763130) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

## Latest implementation: index-mask expressions

All **15 enabled functional cases** in `BLI_index_mask_expression_test.cc` are ported, adding **321 assertion executions**. Its one disabled `#if 0` benchmark remains explicitly unported. The original 50 randomized iterations, input lengths up to 200,000, seed, chunk generation and nested expressions remain intact.

The Rust core implements selected-index masks, unions, intersections, subtraction, bounded complements and nested expression evaluation. Canonical interval storage keeps large contiguous ranges compact. This is a serial Rust backend, not native arena/segment-layout, TBB, performance or complete IndexMask API parity. These library operations are not new interactive editor tools.

Mask assertion operands encode every selected index reversibly, not just their counts or hashes. A separate original-C++ oracle matches **14,573,457 random Boolean input values**, **147,456 mask results** and **370,176 absolute selected indices** exactly against native Rust and Chromium. Three deliberately wrong set operations fail unchanged original tests while independent controls pass. [Detailed provenance and limits](docs/MASK-EXPRESSION-PORT-VERIFICATION.md)

An initial supplemental probe exceeded the pinned static-range constructor's 2^31 bound and was correctly rejected. That failed run is retained separately. The corrected supplemental corpus stays within the original constructor's domain; no original test inputs, expectations or tolerances changed. Larger Rust-only range capabilities are not claimed as native-C++ parity beyond this limit.

## Accuracy and completion controls

Original snapshots, identities, reviewed target hashes and source-generator reproduction are required. Runtime registries and the required assertion-contract union must agree. Static manifests remain separately required; deleting one cannot shrink accepted coverage. Include-only C++ recording leaves original test/helper bodies unchanged. Rust diagnostics use a separate shadow build. Every assertion event is compared without sampling, and full tapes are preserved losslessly. Production WebAssembly is separately exercised at its public URL. [Fidelity method](docs/ASSERTION-FIDELITY.md)

The whole-suite completeness job remains genuinely failed. The source audit has **5,867 candidates, 615 reviewed mappings and 5,252 unmapped declarations**. Mappings consist of 596 runtime cases and 19 compile-time predicates. These are source declarations, not a complete runtime denominator or feature percentage. Incomplete runtime discovery remains unknown, never zero. [Completion issue #3](https://github.com/596050/blended/issues/3)

## Limited modeller and separate rendering experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object transforms, duplication/deletion, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG output. Rust/WASM generates boxes and planes; Three.js generates spheres. Its legacy test button uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no complete mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. The Solarxy/WebGPU experiment remains independently blocked by blank-viewport/device-loss failures. [Renderer issue #1](https://github.com/596050/blended/issues/1)

## Reproduce and hosting

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

CI additionally fetches pinned Blender, reproduces translations/tables, builds original C++, compares native/browser values and exact inputs, verifies negative controls, publishes the explicitly incomplete subset and tests its public URL. Earlier span, polygon, format, UTF-8, string and collection reports retain their historical revisions and scope.

Source, static builds and durable evidence remain in this public repository. No paid backend or remote GPU was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Component-specific licences apply; consult file SPDX identifiers, [NOTICE.md](NOTICE.md) and `LICENSES/`. Blended is independent of the Blender Foundation and Solarxy's author.
