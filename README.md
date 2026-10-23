# Blended

## [Launch Blended: open the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the deployed 131-case Blender test-port workbench](https://rawcdn.githack.com/596050/blended/959d4ccef446cfcd4f4e82a701fb3c32541a0f9d/index.html)

[Deployment links and verification evidence](LIVE.md) · [Assertion accuracy](docs/ASSERTION-FIDELITY.md) · [Complete-suite requirement](docs/COMPLETE-TEST-PORT.md)

The first link opens the modelling application; the second is a separate compatibility-test workbench. The linked modeller was verified at source `25e641c0d311f61c473755d1c7ee821289a27d15`; the linked workbench at `2c7abe637e8eca6ea8937c871f406fa6ac123006`.

**A browser modeller alpha and test-driven compatibility project, not a complete Blender clone.**

## Verified test-port status

**131 Blender runtime cases now pass natively and in the actual deployed browser.** An independent comparison against the pinned original C++ tests matched **1,049 ordered assertion events** in both native Rust and Chromium WebAssembly. No floating-point differences required a tolerance allowance after the documented representation normalisations. The native Rust suite has **144 runtime tests**: 131 Blender, three Cycles, six product geometry and four safety tests. These are distinct counts, not a feature-parity percentage.

The latest batch adds 32 cases from all four of `BLI_bit_ref_test.cc`, `BLI_bit_vector_test.cc`, `BLI_index_ranges_builder_test.cc` and `BLI_unique_sorted_indices_test.cc`, preserving 170 assertion sites and 521 executions including loops. Shared bit-reference aliasing, copy/move state, word-address identity, range merging and borrowed-slice outcomes are explicitly checked. See [collection-port verification](docs/COLLECTION-PORT-VERIFICATION.md).

The previously missing vector signed-zero hash **compile-time assertion is now ported**. It compiles natively and for WebAssembly; deliberately removing signed-zero canonicalisation is rejected by the expected constant-evaluation error on both targets. This is not an additional runtime case. The earlier index-range test also retains its embedded compile-time condition.

**The complete Blender test port remains unfinished.** The separate `full-test-port-completeness` job still fails. After fixing numeric-literal handling in source discovery, the heuristic source ledger contains 5,673 candidates, with 132 reviewed mappings and 5,541 unmapped candidates. The mappings are 131 runtime cases plus one separately registered compile-time case. Source candidates include conditional, third-party, compile-time and unexpanded declarations, so they are not a complete runtime denominator.

[Original C++/Rust/WASM and deployed verification run](https://github.com/596050/blended/actions/runs/39918173966) · [Inventory-integrity run](https://github.com/596050/blended/actions/runs/39918761201) · [Durable assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence) · [Completion blocker #3](https://github.com/596050/blended/issues/3)

## Accuracy and publication requirements

The test workbench is published only after ordinary native/WASM conformance and independent original-Blender assertion fidelity pass. Each case's identity, ordered assertion kinds, operands, outcomes, execution counts and tolerances are compared. The original C++ test bodies are unchanged; diagnostic overlays and raw transcripts are preserved. The Rust diagnostic shadow is separate from unmodified production tests. Actual public-URL checks are also separate from local diagnostic browser execution.

Pinned source/target hashes and reproduction checks detect drift. Negative tests reject missing, changed, reordered or fabricated assertions. Source-inventory regression tests ensure C++ numeric separators do not hide real test declarations. Passed, failed, blocked, unported and unexecuted work remain distinct. Even complete conformance to the eventual suite would not prove every possible Blender workflow.

## What the limited modeller does

Three.js WebGL 2 renders a browser viewport with orbit/pan/zoom and object transforms. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. It provides object selection, numeric transforms, duplicate/delete, bounded undo/redo, basic material controls, scene JSON save/reopen, static OBJ/STL import/export and PNG viewport output. Its acceptance workflow previously passed 28 public-URL checks, including rendered geometry and editing/interchange; that is not 28 Blender features.

The modeller's existing test button retains the compatible 17-case ABI. Use the separate workbench for all 131 current runtime ports. These library ports do not add a complete mesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/physics suite, compositor, Python add-on API, native .blend support or Cycles/EEVEE compatibility. OBJ export does not include materials; file/geometry/history limits remain.

## Separate rendering experiment

The Solarxy-derived Rust/WebGPU studio compiled and selected existing tests passed, but actual browser rendering acceptance failed. That remains [issue #1](https://github.com/596050/blended/issues/1), with [failure evidence](https://github.com/596050/blended/tree/deployment-evidence). The working Three.js modeller does not fix that fault or inherit Solarxy's procedural editor.

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
node --test modeller/model.test.mjs
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
python3 tools/verify_static_port.py --output build/static-port.json
python3 tools/build_modeller.py --commit "$(git rev-parse HEAD)"
python3 -m http.server 8765 --directory build/modeller
```

Conformance CI fetches pinned original tests, reproduces committed translations, executes native/WASM checks and independent C++ assertion comparisons, publishes a labelled subset, and tests the actual public URL. The native reference's earlier BLI listing has 1,644 registrations with one ambiguous duplicate label; this is not full application discovery. All 6,691 LFS assets under pinned `tests/files/**` were downloaded and hash/size-verified in a separate run. Fresh fixture-based jobs must still materialise their required inputs; other dependencies remain outside that scope.

## Hosting and licences

Code, built files and durable evidence are stored in GitHub. Standard free public-repository Actions runners are used, with no paid service or server-side GPU provisioned. The current preview uses a free third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are supplied separately.

Original project code is GPL-3.0-or-later; translated tests preserve their upstream Apache-2.0 notices; Three.js is MIT-licensed; Solarxy attribution is retained. Deployments contain corresponding sources and notices. This is independent of the Blender Foundation and Solarxy's author.

[Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Machine-readable test-port status](evidence/TEST-PORT-STATUS.json)
