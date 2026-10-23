# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 367-case Blender test workbench](https://rawcdn.githack.com/596050/blended/19abc219cd1ccb7e2dd4090c23710638f30959d8/index.html)

[Deployment details](LIVE.md) · [Current implementation status](docs/IMPLEMENTATION-STATUS.md) · [Heap verification](docs/HEAP-PORT-VERIFICATION.md) · [Complete-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modeller and test workbench are different applications. The linked modeller is the previously verified object-editing alpha. The linked workbench was freshly compiled and publicly verified from source `df61b87fa3b2b5a0751100e427eab11d7205ad5a`. Documentation-only commits can follow that verified implementation revision.

## Verified compatibility subset

**367 unique Blender runtime cases pass natively and in the actual deployed Chromium browser**, with **33,104 assertion executions**. Independent original-C++ versus Rust and Chromium WebAssembly comparisons passed. Eight native and nine browser floating-point differences remain within the original comparison rules; no tolerance was widened. The new heap tests introduced no additional floating differences.

The native Rust total is **390 runtime tests**: 367 Blender ports, three Cycles integer-maths cases and 20 product, safety and regression tests. Six separately tracked compile-time assertions pass positive builds and deliberately broken negative checks on native and wasm32. They are not part of the 367 runtime total.

[Original C++ / Rust / WASM / deployed verification](https://github.com/596050/blended/actions/runs/40019426923) · [Immutable-run assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40019426923) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

The latest batch adds all **29 runtime cases** from `BLI_heap_test.cc`, `BLI_heap_simple_test.cc` and `BLI_inplace_priority_queue_test.cc`. Their 66 assertion sites execute 16,300 checks, including the original random seeds, large loops, helpers, removals, priority changes, pointer payload checks and index views. The Rust implementations provide handle-based and simple min-heaps, an externally mutable integer priority queue and the pinned deterministic generator/shuffle. These are compatibility-library additions, not new interactive editor features.

A separate original-C++ input oracle matched all **15,000 random values and 3,175 shuffled items** exactly in native Rust and WebAssembly. Negative controls confirmed that deliberately broken removal and priority-increase implementations fail the unchanged original tests while independent controls still pass. These diagnostic checks are not additional upstream test cases. [Input and sensitivity results](docs/HEAP-PORT-VERIFICATION.md)

## Accuracy controls and limits

Every registered case has pinned source identity, source snapshots and reviewed target hashes. Generators must reproduce committed tests. The executable registry and reviewed contracts must match exactly. Ordered assertion traces compare kinds, operands, outcomes, counts and tolerances with the pinned original Blender executable. Original C++ test bodies are unchanged; recording overlays and raw evidence are retained. Production WebAssembly is separately tested at its actual public URL.

The heap port documents representation differences and an existing pinned-reference queue boundary behaviour rather than silently changing its semantics. Passing a source test family does not certify untested generic types, custom comparators, allocator layouts or every possible input. [Detailed scope](docs/HEAP-PORT-VERIFICATION.md)

The whole-suite completeness job remains genuinely failed. The current heuristic scan has **5,859 source candidates, 373 reviewed mappings and 5,486 unmapped candidates**. Mappings comprise 367 runtime cases and six compile-time cases. These are source declarations, not a complete runtime denominator. Missing or stale runtime enumeration is unknown, never zero. Conditional, generated, typed, external, unreadable and platform-specific work still requires reconciliation. [Completion blocker #3](https://github.com/596050/blended/issues/3)

## Limited modeller

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection and transforms, duplicate/delete, bounded undo/redo, basic material controls, scene JSON save/reopen, static OBJ/STL import/export and PNG viewport output. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. Its historical public acceptance run checked rendered pixels and editing/interchange workflows. Its legacy test button still uses the 17-case interface; use the separate workbench for the full implemented subset.

There is no comprehensive mesh editor, sculpting, Blender modifier or Geometry Nodes suite, animation/rigging/physics suite, compositor, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. OBJ export does not include materials. A separate Solarxy/WebGPU experiment remains blocked by blank-viewport/device-loss failures; this modeller does not inherit that editor's procedural features. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI also fetches pinned Blender sources, reproduces all registered translations, builds the original reference, compares native/browser traces, checks input and negative controls, publishes the explicitly incomplete subset and tests the public URL. Whole-suite completeness remains a separate requirement. Historical sampling verification is retained in [SAMPLING-PORT-VERIFICATION.md](docs/SAMPLING-PORT-VERIFICATION.md).

## Hosting, source and notices

Source, static builds and durable evidence are in this public repository. No paid backend or remote GPU service was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Upstream licences and attributions apply; consult each file's SPDX identifier and [NOTICE.md](NOTICE.md). This project is independent of the Blender Foundation and Solarxy's author.
