# Blended

A deployed browser modeller alpha and a test-driven Blender compatibility project. **Not a complete Blender clone.**

[Open the modeller](https://rawcdn.githack.com/596050/blended/a81530a62fcc8222ea57db4c5d8b35869d277963/index.html) · [Run the verified 99-case Rust/WASM test workbench](https://rawcdn.githack.com/596050/blended/16980ee91529017553efca51e7223354137f09be/index.html) · [Completion requirements](docs/COMPLETE-TEST-PORT.md)

## Verified test-port status

99 Blender runtime cases pass natively and in the actual deployed browser, representing 528 runtime assertion checks. The native Rust total is 112 after adding three Cycles cases and ten product/safety tests. This is a small subset of Blender, not full parity. The `full-test-port-completeness` CI job remains failed.

The newest batch ports 54 cases from the complete upstream index-range, binary-search and bounds test files. It preserves 226 assertion sites, 235 runtime checks and a compile-time condition. The older vector port was corrected to collect all 68 nonfatal assertions and match upstream comparison semantics; its signed-zero hash compile-time assertion is still unported.

Blender's original pinned `BLI_test` executable was also built and its 54 corresponding tests passed. Its raw listing contains 1,644 registrations and one ambiguous duplicate label. That is discovery for one configured executable, not a complete Blender runtime inventory and not 1,644 ported or passing tests.

[Native/WASM/deployed conformance run](https://github.com/596050/blended/actions/runs/39859518789) · [Durable public test results](https://github.com/596050/blended/tree/test-port-evidence) · [Original native Blender evidence](https://github.com/596050/blended/tree/07b2fd18d4fb15f83ddadbfb19acbd3a8a977bcb) · [Completion blocker #3](https://github.com/596050/blended/issues/3)

All expected results and tolerances retain upstream provenance. Reviewed source/target hashes and case identities prevent silent drift. Passed, failed, blocked, skipped, unmapped and unexecuted work remain distinct. Source candidates are not a runtime denominator. Full test conformance would still not prove every application feature.

## What the limited modeller does

Three.js WebGL 2 renders a local browser viewport with orbit/pan/zoom and object transforms. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. The application provides selection, numeric transforms, duplicate/delete, bounded undo/redo, basic material controls, scene JSON save/reopen, static OBJ/STL import/export and PNG viewport output.

The original public modeller release passed 28 checks including rendered pixels and editing/interchange workflows. These include infrastructure checks, not 28 Blender features. Its existing test button still uses the compatible 17-case ABI; use the separate workbench for all 99 cases.

There is no full mesh edit/sculpt system, Blender modifier or Geometry Nodes suite, rigging/animation/physics suite, compositor, Python add-on API, native .blend support or Cycles/EEVEE compatibility. The new test ports are core-library work, not new editor features. OBJ export does not include materials; file/geometry/history limits remain.

## Rendering experiments remain separate

The Solarxy-derived Rust/WebGPU studio compiles, but real rendering acceptance failed. Imported geometry produced a blank viewport and some runs lost the GPU device. Existing Solarxy unit tests passing did not prove rendering or Blender parity. [Issue #1](https://github.com/596050/blended/issues/1) remains open; [failure evidence](https://github.com/596050/blended/tree/deployment-evidence) is retained. The working Three.js modeller is not a fix for that failure and does not inherit Solarxy's procedural editor.

## Reproduce and verify

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
node --test modeller/model.test.mjs
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
python3 tools/build_modeller.py --commit "$(git rev-parse HEAD)"
python3 -m http.server 8765 --directory build/modeller
```

Conformance CI fetches pinned Blender sources, reproduces the committed translations, runs native and real WASM cases, publishes an immutable subset workbench, and tests that public URL. Native reference workflows preserve build configuration, raw discovery and original XML output. Details and commands are in [COMPLETE-TEST-PORT.md](docs/COMPLETE-TEST-PORT.md).

The 6,691 LFS assets under pinned `tests/files/**` were downloaded and hash/size-verified. A fresh execution checkout must still materialise required inputs, and other dependencies remain outside that verified scope. Neither an LFS pointer nor a previous download counts as a passed test.

## Hosting, source and licences

Code, built files and durable evidence are stored in this public GitHub repository. Builds use standard free public-repository Actions runners. No paid service or server-side GPU is provisioned. The current application preview uses a free third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied.

Original project code is GPL-3.0-or-later. Translated tests preserve their Apache-2.0 notices; Three.js is MIT-licensed; Solarxy attribution is retained. Deployments contain corresponding sources and licence notices. This is independent of the Blender Foundation and Solarxy's author.

See [implementation status](docs/IMPLEMENTATION-STATUS.md) and [machine-readable test-port status](evidence/TEST-PORT-STATUS.json).
