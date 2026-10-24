# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 503-case Blender test workbench](https://rawcdn.githack.com/596050/blended/a7f55a00388e7b3fb906c307cc52db7968b9a25d/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Latest UTF-8 verification](docs/UTF8-PORT-VERIFICATION.md) · [Complete-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modelling application and compatibility workbench are separate. The modeller remains the earlier object-editing alpha. The workbench was freshly compiled and publicly verified from source `3969e1fdadae2e11d6f220412f8c32cabf7048d1`. Documentation-only commits may follow that verified implementation revision.

## Verified compatibility subset

**503 unique Blender runtime cases pass natively and in the actual deployed Chromium browser.** Independent original-C++ versus native Rust and Chromium WebAssembly comparisons check **1,661,377 ordered assertion events per implementation**. Eight native and nine browser floating differences remain in older colour cases within their original rules. No tolerance was widened and the new UTF-8 cases add no floating differences.

The native Rust run passed **542 runtime tests**: 503 Blender ports, three Cycles integer-maths cases and 36 separate product/safety/regression tests. Six compile-time assertions separately pass positive builds and deliberate-failure checks on native and wasm32. Repeated assertions and supplemental oracle inputs are not extra Blender test cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40065241089) · [Original-reference assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40065241089) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

## Latest implementation: full UTF-8 test file

Every runtime case in `BLI_string_utf8_test.cc` is ported: **39 cases / 1,627,163 assertion executions**. The Rust implementation covers malformed-byte detection/removal/substitution, bounded length/copying, the tested formatting form, decoding and consumed-byte offsets, and UTF-8/UTF-32 cursor movement. The 78 malformed fixtures, original helper expansions, all 256 byte values, buffer sizes 1 through 12 and original random stress loops remain intact. These are core-library additions, not new interactive editor tools.

An independent original-C++ oracle checks **68,273 byte sequences**, including every single-byte and two-byte input, plus explicit longer legacy/truncated sequences. All **68,273 validator results, 137,426 decoded-value/next-offset pairs and 48,640 random bytes** match native Rust and browser WebAssembly exactly. Three deliberately broken implementations are detected by unchanged original tests while controls pass. [Detailed scope, provenance and evidence](docs/UTF8-PORT-VERIFICATION.md)

The pinned legacy behaviour intentionally differs from strict modern Unicode validation. It retains tested five/six-byte sequences and original selective validity rules. The formatting adapter is the tested single-`%s` form, not a complete C varargs formatter. Cursor width decisions use the exact pinned combining table, with full original notices included in corresponding source. Safe Rust boundary policies and limits are documented explicitly.

## Accuracy at stress-test scale

Pinned source snapshots, original identities, reviewed target hashes and source-generator reproduction are required. Executable and reviewed-case registries must match exactly. Include-only C++ instrumentation leaves original test bodies unchanged; Rust diagnostic recording uses a separate shadow build. Every event is compared with the same reviewed assertion rules, not sampled or replaced by a summary hash. Case boundaries, order, operands, outcomes, counts and tolerances remain checked.

The comparison now processes large traces in bounded batches. Chromium transfers the complete diagnostic trace in chunks rather than one giant response. All C++/Rust/browser raw events are stored losslessly as `.jsonl.gz`, with decompressed SHA-256 and byte counts verified before removing duplicate raw copies. Production WebAssembly is separately tested at its actual public URL. [Fidelity methodology](docs/ASSERTION-FIDELITY.md)

The whole-suite completeness job remains genuinely failed. The latest heuristic scan has **5,859 source candidates, 509 reviewed mappings and 5,350 unmapped declarations**. The mappings comprise 503 runtime cases and six compile-time cases. These are not a full runtime denominator or a feature percentage. Missing or incomplete runtime discovery remains unknown, never zero. [Completion issue #3](https://github.com/596050/blended/issues/3)

## Limited modeller and separate rendering experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection/transforms, duplication/deletion, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG viewport output. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. Its historical public acceptance run checked rendered pixels and editing workflows. Its legacy test button still uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no complete mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. The Solarxy/WebGPU rendering experiment remains independently blocked by blank-viewport/device-loss failures; the successful Three.js modeller is not a fix for that experiment. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI additionally fetches pinned Blender, reproduces source translations and tables, builds the original reference, executes native/browser comparisons and diagnostic controls, publishes the explicitly incomplete subset, and tests its public URL. Whole-suite completion is a separate requirement. Earlier [string](docs/STRING-OPS-PORT-VERIFICATION.md), [data](docs/DATA-PORT-VERIFICATION.md), [heap](docs/HEAP-PORT-VERIFICATION.md) and [sampling](docs/SAMPLING-PORT-VERIFICATION.md) evidence retains its historical scope.

## Hosting and notices

Source, static builds and durable evidence remain in this public repository. No paid backend or remote GPU service was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Component-specific licences and attribution apply; consult each file's SPDX identifier, [NOTICE.md](NOTICE.md) and `LICENSES/`. Blended is independent of the Blender Foundation and Solarxy's author.
