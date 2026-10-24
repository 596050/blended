# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 416-case Blender test workbench](https://rawcdn.githack.com/596050/blended/63655e85d5b56c357645c92e3874af3940fd161e/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [Latest data-test verification](docs/DATA-PORT-VERIFICATION.md) · [Complete-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modelling application and compatibility workbench are separate. The modeller is the earlier object-editing alpha. The linked workbench was freshly compiled and publicly verified from source `059bfb9b277e8bc5aefb9834dd671879094a0599`. Documentation-only commits may follow that verified implementation revision.

## Verified compatibility subset

**416 unique Blender runtime cases pass natively and in the actual deployed Chromium browser.** Independent original-C++ versus native Rust and Chromium WebAssembly comparisons check **33,368 ordered assertion events** per implementation. Eight native and nine browser floating differences remain within the original comparison rules; no tolerance was widened. The newest data cases introduce no floating differences.

The native Rust total is **444 runtime tests**: 416 Blender ports, three Cycles integer-maths cases and 25 product/safety/regression tests. Six separately tracked compile-time assertions pass positive builds and deliberately broken negative checks on native and wasm32. They are not additional runtime passes.

[Combined verification run](https://github.com/596050/blended/actions/runs/40045600207) · [Immutable-run assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40045600207) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

The latest batch adds every runtime case from `BLI_array_utils_test.cc` (35), `BLI_csv_parse_test.cc` (10), `BLI_hash_mm2a_test.cc` (3) and `BLI_disjoint_set_test.cc` (1): **49 cases and 264 original assertion executions**. Implementations include typed array operations and grouping, byte-oriented CSV parsing with chunk fallback, streaming Murmur2A and union-by-rank disjoint sets. Original 100,000-element grouping inputs, masks, helper assertions, quoted/multiline fields, empty trailing fields, streaming updates and root behaviour are retained. These are core-library additions, not new interactive modelling tools.

An independent oracle compiles the unedited original hash implementation and compares **31,776 hash results across 10,592 explicit streaming configurations**. Native Rust and browser WebAssembly match exactly, including repeated finalisation and reset. Four deliberate implementation mutations are detected by unchanged original tests while independent controls still pass. These supplemental probes are not counted as extra Blender cases. [Detailed evidence and scope](docs/DATA-PORT-VERIFICATION.md)

## Accuracy controls and limits

Pinned source snapshots, original identities, reviewed target hashes and generator reproduction are required. The executable registry must match the reviewed case contracts exactly. Include-only C++ diagnostic recording leaves original test bodies unchanged. A separate Rust shadow records corresponding values and case boundaries. Comparison checks preserve assertion kind, operands, order, outcomes, counts and tolerances, including C-string and array-helper semantics. Production WebAssembly is separately tested at its actual public URL.

Failure-detection probes reject changed expectations, dropped assertions and broken implementations. Compiler errors, panics or browser traps are not accepted as successful negative assertion checks. Test-first missing-module failures are recorded as compilation failures, not fictional executed assertion failures.

The whole-suite completeness job remains genuinely failed. The current heuristic scan contains **5,859 source candidates, 422 reviewed mappings and 5,437 unmapped declarations**. The mappings are 416 runtime cases plus six compile-time cases. This is not a complete runtime denominator or feature percentage. Missing or stale runtime enumeration remains unknown, never zero. [Completion blocker #3](https://github.com/596050/blended/issues/3)

Representation limits are documented. Current array wrappers cover the tested character, integer and pointer forms, not arbitrary raw-byte comparison or all virtual-array reduction schedules. CSV processing is sequential and does not reproduce native parallel callback scheduling or allocator layout. The original hash is endian-sensitive. Passing these source tests is not a proof of every possible input or generic type.

## Limited modeller

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection and transforms, duplicate/delete, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL import/export and PNG output. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. Its legacy test button uses the original 17-case interface; use the separate workbench for the complete implemented subset.

There is no comprehensive mesh editor, sculpting, Blender modifier or Geometry Nodes suite, animation/rigging/physics suite, compositor, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. A separate Solarxy/WebGPU experiment remains blocked by rendering failures and does not inherit the modeller's successful acceptance results. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI also fetches pinned Blender sources, reproduces registered translations, builds the original reference, compares native/browser traces, checks deterministic inputs and negative controls, publishes the explicitly incomplete subset and tests its public URL. Historical sampling and heap evidence remains in [SAMPLING-PORT-VERIFICATION.md](docs/SAMPLING-PORT-VERIFICATION.md) and [HEAP-PORT-VERIFICATION.md](docs/HEAP-PORT-VERIFICATION.md).

## Hosting and notices

Source, static builds and durable evidence are in this public repository. No paid backend or remote GPU service was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are also supplied. Consult component SPDX identifiers and [NOTICE.md](NOTICE.md). This project is independent of the Blender Foundation and Solarxy's author.
