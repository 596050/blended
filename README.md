# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 609-case Blender test workbench](https://rawcdn.githack.com/596050/blended/55479ba6a6249846abc4c36d36440b27bfe106b4/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Latest map/view verification](docs/CONTAINER-VIEW-PORT-VERIFICATION.md) · [Whole-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modelling application and compatibility workbench are separate. The modeller remains the earlier object-editing alpha. The workbench was freshly compiled and publicly verified from source `7a3dec93c2c02605834330b5de6872d6f1dbe4ad`. Later documentation-only commits do not change that verified implementation.

## Verified compatibility subset

**609 unique Blender runtime cases pass natively and at the actual deployed Chromium URL.** Independent original-C++ versus native Rust and Chromium WebAssembly comparisons check **3,196,744 ordered assertion events per implementation**. Eight native and nine browser floating differences remain in older colour cases under original rules. No tolerance was widened; the latest map/view cases introduce no additional differences.

The native Rust suite passed **679 runtime tests: 609 Blender ports, three Cycles cases and 67 separate product/safety/regression tests**. Nineteen compile-time predicates are separately verified on native and wasm32, including deliberately false checks. Supplemental observations, repeated assertions and negative probes are not extra Blender runtime cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40209288469) · [Original-reference evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40209288469) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

## Latest implementation: multivalue maps and type-erased borrowed views

Both original source files are completely mapped: **nine cases in `BLI_multi_value_map_test.cc` and four fixture cases in `BLI_generic_span_test.cc`**, adding 52 assertion executions. Suite setup, original values, mutable storage, pointer comparisons and owning-pointer keys retain explicit provenance.

The Rust core preserves insertion order and duplicates within each key's value list. Mutable lookups edit the actual stored values. Owning pointer keys compare allocation identity rather than accidentally merging separate equal-valued boxes. Type-erased views retain their actual backing storage, check exact element types and preserve live read-only aliases during permitted mutation. These are core-library additions, not new interactive modelling tools.

An original-header differential observer matches **107,101 output words exactly** in original C++, native Rust and Chromium, and against an independent Python model. Four implementation-only mutations are detected by unchanged original tests while independent controls pass. [Detailed provenance and limits](docs/CONTAINER-VIEW-PORT-VERIFICATION.md)

The audit exposed an original-header API limitation: `MultiValueMap::clear_and_shrink()` is declared but fails to compile when instantiated because the underlying map lacks that method. The failed build blocked publication and remains recorded. The supplemental corpus now uses the supported `clear()` operation on both targets. No original test or expectation changed, and the Rust shrink helper is not presented as operational equivalence to that broken declaration.

## Accuracy and reproducibility

Original source snapshots, case identities, reviewed hashes and generator reproduction are required. Runtime registries and reviewed contracts must match exactly. Separate required compile-time manifests cannot disappear silently. Include-only C++ recording leaves original test bodies unchanged; Rust diagnostics run in an explicit shadow. Every assertion event is compared, not sampled or replaced by hashes. Full transcripts are preserved losslessly. Production WebAssembly is separately tested at its actual public URL. [Fidelity method](docs/ASSERTION-FIDELITY.md)

The downloadable corresponding-source archive now also includes the workflow files and two small reference-limit fixtures required by its regression tests. A fresh extraction passed **all 304 Python tests** locally. Native Rust, original C++ and browser execution were verified separately in CI, not rerun in that local source-archive check. [Archive verification](evidence/source-archive-verification.json)

The whole-suite completeness job remains genuinely failed. The source audit has **5,867 candidates, 628 reviewed mappings and 5,239 unmapped declarations**. Mappings comprise 609 runtime cases and 19 compile-time predicates. These are source declarations, not a complete runtime denominator or feature percentage. Incomplete runtime discovery remains unknown, never zero. [Completion issue #3](https://github.com/596050/blended/issues/3)

## Limited modeller and separate rendering experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object transforms, duplicate/delete, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG output. Rust/WASM generates boxes and planes; Three.js generates spheres. Its legacy test button uses the 17-case interface; use the separate workbench for the complete implemented subset.

There is no comprehensive mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. The Solarxy/WebGPU experiment remains independently blocked by blank-viewport/device-loss failures. [Renderer issue #1](https://github.com/596050/blended/issues/1)

## Reproduce and hosting

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

CI additionally fetches pinned Blender, reproduces source tests/tables, builds original C++, compares native/browser observations, verifies negative controls, publishes the explicitly incomplete subset and tests its public URL. Earlier reports retain their original revisions and scope.

Source, static builds and durable evidence are in this public repository. No paid backend or remote GPU was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are supplied. Component-specific licences apply; consult file SPDX identifiers, [NOTICE.md](NOTICE.md) and `LICENSES/`. Blended is independent of the Blender Foundation and Solarxy's author.
