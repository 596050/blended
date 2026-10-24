# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 512-case Blender test workbench](https://rawcdn.githack.com/596050/blended/15a67995bdca8581e9f1e28b9b95af17ea69d51b/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Latest graphics-format verification](docs/PIXEL-FORMAT-PORT-VERIFICATION.md) · [Whole-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modeller and compatibility workbench are separate applications. The modeller remains the earlier object-editing alpha. The workbench was freshly compiled and publicly verified from source `2990e30077e368c97e3a7af60d45d7a911ceb988`. Documentation-only commits may follow that runtime revision.

## Verified compatibility subset

**512 unique Blender runtime cases pass natively and in the actual deployed Chromium browser.** Original-C++ versus native Rust and Chromium WebAssembly comparisons check **1,661,546 ordered assertion events per implementation**. Eight native and nine browser floating differences remain in older colour cases within their original rules. No tolerance was widened; the new graphics-format cases introduce no additional floating differences.

The native Rust run passed **558 runtime tests**: 512 Blender ports, three Cycles integer-maths cases and 43 separate product/safety/regression tests. Six compile-time assertions separately pass positive builds and deliberate-failure checks on native and wasm32. Repeated assertions and supplemental oracle inputs are not extra Blender test cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40108130160) · [Original-reference evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40108130160) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

## Latest implementation: half floats and normalised integer formats

This batch adds all eight enabled functional cases in `BLI_math_half_test.cc` and the one case in `BLI_normalized_int_test.cc`: **nine cases / 169 assertion executions**. The five opt-in `DO_PERF_TESTS` benchmarks remain explicitly unported, not counted passing or removed from the overall inventory.

The Rust core now implements half-precision conversion, finite conversion, array tails/clamping and normalised signed/unsigned 8-bit, 16-bit and 10/10/10/2-bit formats. Original rounding rules, NaN checks, signed zero, subnormal cases, vector equality and untouched output sentinels are retained. These are graphics-library additions, not a new rendering engine or interactive modelling feature.

A separately compiled original-C++ oracle verifies all **65,536 half encodings**, **291,054 distinct float32 bit inputs**, explicit array-tail lengths and normalised-format corpora. All **2,944,570 output words match bit for bit** in native Rust and browser WebAssembly under the named x86_64 scalar/SSE2/SSE4.1 reference profile. The full corpus, drivers and outputs are preserved. Three deliberately broken implementations fail unchanged original tests while controls pass. [Detailed scope and evidence](docs/PIXEL-FORMAT-PORT-VERIFICATION.md)

Native x86_64 verification actually changes and restores FTZ/DAZ floating-point control bits. WebAssembly has no accessible MXCSR register: the browser checks conversion values without claiming a hardware-mode perturbation. F16C/AVX, ARM NEON, native object-layout parity and SIMD performance parity are not certified by this profile. Architecture-dependent NaN payload behaviour is documented rather than hidden.

## Accuracy and completion controls

Pinned source snapshots, original identities, reviewed target hashes and generator reproduction are required. Executable and reviewed-case registries must match exactly. Include-only C++ instrumentation leaves original test bodies unchanged; diagnostic Rust recording uses a separate shadow build. Every assertion event is compared, not sampled or replaced by a summary hash. Complete transcripts are preserved losslessly with verified decompressed hashes and sizes. Production WASM is separately tested at its actual immutable public URL. [Methodology](docs/ASSERTION-FIDELITY.md)

The whole-suite completeness job remains genuinely failed. The latest heuristic scan has **5,859 source candidates, 518 reviewed mappings and 5,341 unmapped declarations**. Mappings comprise 512 runtime cases and six compile-time cases. These are not a full runtime denominator or a feature percentage. Missing or incomplete runtime discovery remains unknown, never zero. [Completion issue #3](https://github.com/596050/blended/issues/3)

## Limited modeller and separate rendering experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection/transforms, duplication/deletion, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG viewport output. Rust/WASM generates boxes and planes; Three.js generates spheres. Its historical acceptance run checked rendered pixels and editing workflows. Its legacy test button uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no complete mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. The Solarxy/WebGPU experiment remains independently blocked by blank-viewport/device-loss failures. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI additionally fetches pinned Blender, reproduces source translations/tables, builds the original reference, executes native/browser comparisons and diagnostic controls, publishes the explicitly incomplete subset and tests its public URL. Whole-suite completion remains separate. Earlier [UTF-8](docs/UTF8-PORT-VERIFICATION.md), [string](docs/STRING-OPS-PORT-VERIFICATION.md), [data](docs/DATA-PORT-VERIFICATION.md), [heap](docs/HEAP-PORT-VERIFICATION.md) and [sampling](docs/SAMPLING-PORT-VERIFICATION.md) records retain their historical scope.

## Hosting and notices

Source, static builds and durable evidence remain in this public repository. No paid backend or remote GPU service was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Component-specific licences and attribution apply; consult each file's SPDX identifier, [NOTICE.md](NOTICE.md) and `LICENSES/`. Blended is independent of the Blender Foundation and Solarxy's author.
