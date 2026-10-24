# Blended

## [Launch the deployed browser modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

### [Run the verified 464-case Blender test workbench](https://rawcdn.githack.com/596050/blended/51d30f5a549da822a9dc0945d353ef6414938092/index.html)

[Deployment details](LIVE.md) · [Implementation status](docs/IMPLEMENTATION-STATUS.md) · [String-test verification](docs/STRING-OPS-PORT-VERIFICATION.md) · [Complete-suite requirements](docs/COMPLETE-TEST-PORT.md)

**A browser modeller alpha and test-driven Blender compatibility project, not a complete Blender clone. The complete Blender test port remains unfinished.**

The modeller and compatibility workbench are separate applications. The modeller remains the earlier object-editing alpha. The linked workbench was freshly compiled and publicly verified from source `ab692209e9eb98248054ae90ead9b0258f1ab4da`. Documentation/comment-only commits may follow the verified implementation revision.

## Verified compatibility subset

**464 unique Blender runtime cases pass natively and at the actual deployed Chromium URL.** Independent original-C++ versus native Rust and Chromium WebAssembly comparisons check **34,214 ordered assertion events** per implementation. Eight native and nine browser floating differences remain within the original comparison rules; no tolerance was widened. The newest string cases introduce no floating differences.

The complete native Rust run passed **497 runtime tests**: 464 Blender ports, three Cycles integer-maths cases and 30 separate product/safety/regression tests. Six separately tracked compile-time assertions pass positive builds and deliberate-failure checks on native and wasm32. These are not additional runtime cases.

[Combined verification run](https://github.com/596050/blended/actions/runs/40049834310) · [Immutable-run original assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40049834310) · [Machine-readable status](evidence/TEST-PORT-STATUS.json)

The latest batch ports every runtime case from `BLI_string_test.cc` (43), `BLI_string_search_test.cc` (3) and `BLI_string_utils_test.cc` (2): **48 cases and 846 assertion executions**. Original TEST/TEST_F fixtures, helper expansions, byte literals, pointer comparisons, buffer limits and loops are retained. Implementations cover bounded strings, natural ordering, formatting, word splitting, escaping, unique names and the tested fuzzy-search operations. These are core-library additions, not new interactive modelling tools or a complete search/ranking system.

A separately compiled original-C++ oracle checks **3,136 natural-order results and 21,952 bounded-search pointer offsets** exactly against native Rust and browser WebAssembly. Four deliberate implementation mutations fail unchanged original tests while independent controls pass. These supplemental checks do not inflate the Blender test count. [Evidence and verified scope](docs/STRING-OPS-PORT-VERIFICATION.md)

## Accuracy controls and limits

Pinned source snapshots, original case identities, reviewed target hashes and generator reproduction are required. The executable registry must exactly match reviewed contracts. Include-only C++ instrumentation leaves original test bodies unchanged; an explicit Rust shadow records corresponding values and case boundaries. Comparisons preserve assertion kind, operands, order, outcomes, counts, helper semantics and original tolerance. Production WebAssembly is separately tested at its real public URL.

Pointers are real returned addresses, not substituted string comparisons. New string-fixture transcript values use pair-local alias labels because unrelated static literals have different allocation layouts across implementations; actual pointer equality/nullness is still asserted, and the supplemental search oracle checks numeric offsets independently. C-locale comparison and valid-Unicode decoding are verified only within the documented scope. Invalid-byte decoding, every locale, arbitrary native memory layouts and all search-ranking features are not certified.

The whole-suite completeness gate remains genuinely failed: **5,859 source candidates, 470 reviewed mappings and 5,389 unmapped declarations**. Mappings comprise 464 runtime and six compile-time cases. These are heuristic source counts, not a complete runtime denominator or feature percentage. Missing runtime enumeration is unknown, never zero. [Completion blocker #3](https://github.com/596050/blended/issues/3)

## Limited modeller and separate renderer experiment

The Three.js WebGL 2 alpha provides orbit/pan/zoom, object selection and transforms, duplicate/delete, bounded undo/redo, basic materials, scene JSON save/reopen, static OBJ/STL interchange and PNG viewport output. Rust/WebAssembly generates boxes and planes; Three.js generates spheres. Its legacy test button retains the earlier 17-case interface; use the separate workbench for all implemented compatibility cases.

There is no comprehensive mesh editor, sculpting, Blender modifier or Geometry Nodes suite, animation/rigging/physics suite, compositor, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity. OBJ export does not include materials. The Solarxy/WebGPU experiment remains separately blocked by rendering/device-loss failures. This modeller does not inherit that editor's procedural features. [Renderer blocker #1](https://github.com/596050/blended/issues/1)

## Reproduce

Use the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
cargo build --locked --release --target wasm32-unknown-unknown -p blended-core
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -v
node --test modeller/model.test.mjs
```

Conformance CI additionally fetches pinned Blender sources, reproduces all translations, builds the original reference, compares native/browser transcripts, exercises supplemental oracles and negative controls, publishes the explicitly incomplete subset and tests its actual public URL. Whole-suite completion is a separate requirement. Earlier data, heap and sampling reports retain their historical scope.

## Hosting and attribution

Source, static builds and durable evidence are stored in this public repository. No paid backend or remote GPU service was provisioned. The preview uses a third-party shared-origin CDN: use public sample models only and save work locally. GitHub Pages workflows are supplied. Preserve each component's SPDX identifier, copyright and licence notices; see [NOTICE.md](NOTICE.md). Blended is independent of the Blender Foundation and Solarxy's author.
