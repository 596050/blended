# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 581-case Blender test workbench](https://rawcdn.githack.com/596050/blended/d32122067882b90b631adc1e4f765f708f10fe33/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Latest span verification](docs/SPAN-PORT-VERIFICATION.md) · [Whole-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modelling application and test workbench are separate. The modeller remains the earlier object-editing alpha. The workbench was freshly compiled and publicly verified from source `8952a0ef18a83bb7a56656dd8519095bd0fb2cd2`. Documentation-only commits may follow that verified implementation.

## Verified compatibility subset

**581 unique Blender runtime cases pass natively and at the actual deployed Chromium URL.** Original-C++ versus native Rust and Chromium WebAssembly comparisons check **3,196,371 ordered assertion events per implementation**. Eight native and nine browser floating differences remain in older colour cases under the original comparison rules. No tolerance was widened; the latest span cases introduce no additional differences.

The full native Rust suite passed **634 runtime tests: 581 Blender ports, three Cycles cases and 50 separate product/safety/regression tests**. **Nineteen compile-time assertions** are separately mapped and verified on native and wasm32, including deliberately false checks. Supplemental observations, repeated assertions and negative probes are not extra Blender runtime cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40145587317) · [Original-reference evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40145587317) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

## Latest implementation: borrowed array views and compile-time contracts

All **40 runtime declarations and 13 compile-time predicates in `BLI_span_test.cc`** are now mapped. They add 153 runtime assertion executions. One original case contains only static conversion checks; it remains an executed zero-runtime-assertion case, not a fabricated assertion count.

The Rust core provides borrowed read-only/mutable views, slicing, bounded dropping/taking, element search, filling/copying/reversal, reverse iteration, pointer relationships and restricted byte-preserving casts. Cell-backed storage preserves live aliasing rather than snapshotting the original array. Compile-time constant evaluation and allowed/forbidden conversion capabilities are checked as compiler properties, not runtime Boolean substitutes.

All 13 new predicates compile on both targets. Each deliberately false predicate is separately rejected with the expected diagnostic: **26 negative compilations**, not 26 additional tests. An independent original-C++ oracle matches **473,659 observations exactly** in native Rust and Chromium. Three implementation-only mutations are detected by unchanged original cases while controls pass. [Detailed provenance and limits](docs/SPAN-PORT-VERIFICATION.md)

The oracle also exposes a pinned-source limitation: a mutable pointer-span conversion is declared convertible by the original type trait, but its C++ constructor fails when instantiated. That discrepancy is recorded explicitly, not claimed as successful operational equivalence. The Rust adapter implements the declared capability; this is not a claim that the original constructor worked.

## Accuracy and completion controls

Original source snapshots, case identities, reviewed hashes and source-generator reproduction are required. Runtime registries and reviewed contracts must match exactly. Compile-time manifests are a separate required union; deleting one cannot silently shrink the accepted scope. Include-only C++ recording leaves original test bodies unchanged. Rust diagnostics run in a separate shadow build. Every assertion event is compared, not sampled or replaced by hashes. Full transcripts are retained losslessly. Production WebAssembly is separately tested at its public URL. [Fidelity method](docs/ASSERTION-FIDELITY.md)

The whole-suite completeness job remains genuinely failed. The source audit has **5,867 candidates, 600 reviewed mappings and 5,267 unmapped declarations**. Mappings consist of 581 runtime cases and 19 compile-time assertions. These are source declarations, not a full runtime denominator or feature percentage. Incomplete runtime discovery remains unknown, never zero. [Completion issue #3](https://github.com/596050/blended/issues/3)

## Limited modeller and separate rendering experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object transforms, duplication/deletion, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG output. Rust/WASM generates boxes and planes; Three.js generates spheres. Its legacy test button uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no complete mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. New library ports are not new interactive tools. The Solarxy/WebGPU experiment remains independently blocked by blank-viewport/device-loss failures. [Renderer issue #1](https://github.com/596050/blended/issues/1)

## Reproduce and hosting

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

CI additionally fetches pinned Blender, reproduces source tests/tables, builds original C++, compares native/browser results, verifies negative controls, publishes the explicitly incomplete subset and tests its public URL. Earlier polygon, format, UTF-8, string and collection reports retain their historical revisions and scope.

Source, static builds and durable evidence are stored in this public repository. No paid backend or remote GPU was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Component-specific licences apply; consult file SPDX identifiers, [NOTICE.md](NOTICE.md) and `LICENSES/`. Blended is independent of the Blender Foundation and Solarxy's author.
