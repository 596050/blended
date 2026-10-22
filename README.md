# Blended

**A deployed, tested browser modeller alpha. Not a complete Blender clone.**

[Open the verified modeller](https://rawcdn.githack.com/596050/blended/a81530a62fcc8222ea57db4c5d8b35869d277963/index.html) · [Actual public-URL test results](https://github.com/596050/blended/blob/modeller-evidence/result.json) · [Screenshots and exported test files](https://github.com/596050/blended/tree/modeller-evidence) · [Verified CI run](https://github.com/596050/blended/actions/runs/39830750442)

The linked immutable build uses source commit `76044caffe2b69ae5cdceeff1addb56ee61411d9`. New successful builds are published on `modeller-build`; their exact source commit is recorded in `build.json` and the acceptance report.

## Source-derived Blender parity programme

The full application direction is to reuse existing source-derived Blender browser ports and close compatibility facet by facet. See the [implementation and acceptance programme](docs/BROWSER_PARITY_PROGRAM.md), [30-facet source/test map](compatibility/facets.json), and [pinned browser-port candidates](compatibility/browser-ports.lock.json).

The current product reference is Blender 5.4.0 alpha at the existing immutable pin. Candidate ports based on Blender 5.2 or 5.3 are first qualified against their own exact native reference; their results do not transfer to the product target. `tools/probe_browser_port.py` independently attempts the complete original mathutils and BMesh Python suites on a hash-pinned browser release. `tools/parity_gate.py` rejects incomplete coverage, skipped requirements, stale evidence and native/browser substitutions. The initial inventory is explicitly incomplete and does not report full feature parity.

The browser-port workflow records qualification results separately from the working limited modeller. Its receipts are preserved on `browser-port-evidence`; a failed or blocked qualification remains visible. Infrastructure tests validate reporting and test transport and are not Blender feature passes.

Selected original Blender 5.2 cohorts now include 192 numerical cases, 48 data/API cases, four blend-file IO methods and 17 library-linking methods. Native and browser pass all 48 data cases and all four IO methods. The IO workflow also transfers the actual browser-generated files and matches all four current file pairs in the same verified native reader. The released browser artifact still reports an unknown build identity, and two numerical parent tests still fail in that release. Narrow source fixes have passed actual WebAssembly kernel probes; the complete source rebuild and unchanged 192-case qualification remain separate gates. The library cohort has a passing native baseline with exact external fixtures; its browser and persistent-library results are recorded independently. See the programme for immutable receipts, remaining blockers and the distinction from full Blender 5.4 parity.

## What works in the initial modeller

- Actual Three.js WebGL 2 rendering, orbit/pan/zoom and transform controls.
- Rust/WebAssembly-generated boxes and planes; Three.js spheres.
- Object selection, numeric location/rotation/scale, duplicate/delete and bounded undo/redo.
- Basic colour, roughness, metalness, wireframe and grid controls.
- Save/reopen the application's `.blended.json` scene format.
- Static OBJ/STL import and geometry export; PNG viewport output.
- An in-browser button executes the 17 ported Blender mathematical tests against the actual Rust WASM module.

The public-URL test executed 28 checks successfully, including rendered cube pixels, geometry changes, numeric translation, undo/redo, duplication/deletion, scene-file round trips, OBJ/STL import/export, PNG output and the 17 WASM cases. These checks do not establish every interaction or Blender feature. Hardware-GPU performance has not been benchmarked.

## Important limits

**Full Blender and Cycles functionality and test parity are NOT implemented.** There is no mesh edit mode, sculpt mode, rigging/animation suite, simulation, compositor, Python add-on API, native `.blend` support or Cycles renderer compatibility. OBJ export does not include materials. Import is limited to 20 MB and bounded geometry sizes. History snapshots are bounded but are not designed for Blender-scale scenes.

This free preview uses a third-party shared-origin CDN serving files from GitHub. Use public sample files only and download your work locally. No paid service or server-side GPU has been provisioned. GitHub Pages is the preferred dedicated site once enabled in the repository settings; a manual build/deploy/test workflow is supplied.

## Two rendering paths, with separate results

1. **Working limited modeller:** `modeller/`, Rust box/plane geometry and Three.js rendering. It has passing end-to-end public-URL checks.
2. **Solarxy/WebGPU experiment:** a full pinned Solarxy source build. It compiled and its selected native/frontend tests passed, but real browser rendering acceptance failed. It remains an explicitly labelled [diagnostic preview](https://rawcdn.githack.com/596050/blended/5782100e39cff4325983f4be9949b651d488417c/index.html), not a production release. See [blocker #1](https://github.com/596050/blended/issues/1) and [preserved failure evidence](https://github.com/596050/blended/tree/deployment-evidence).

The Three.js modeller is not a fix for the Solarxy rendering fault and does not inherit Solarxy's procedural node functionality. The Rust mathematical core is shared with the new modeller; the Solarxy engine remains separately built.

## Test-driven work and honest coverage

| Scope | Implemented / observed |
|---|---|
| Blender upstream ports | 17 runtime cases from `BLI_math_vector_test.cc`; the signed-zero hash static assertion is unported |
| Cycles upstream ports | 3 integer-maths cases with 23 expected outputs; no renderer port |
| New Rust product tests | 6 geometry contracts and 4 safety checks |
| New JavaScript product tests | 10 scene-validation/history cases |
| Browser compatibility | 17 actual Rust WASM cases executed in the deployed browser |
| Public application workflow | 28 checks passed in the linked release run |
| Source discovery | 5,637 Blender, 543 Cycles and 1,596 Solarxy candidate declarations; not complete runtime enumeration |

The raw discovery reports and separate port mappings are retained on [`compatibility-index`](https://github.com/596050/blended/tree/compatibility-index). Source candidates include parameterised declarations and compile-time assertions. Blender and Cycles overlap. Do not sum them into a unique test total or derive a parity percentage. The Blender checkout contained 2,169 `.blend` LFS pointers whose fixture payloads were unavailable; they are not silently counted as executed tests.

Observed red-to-green sequences:

- Cycles maths: failing run `39819487607`, implemented/passing run `39819811245`.
- New modeller contracts: failing run `39829905501`, implemented/passing run `39830750120`.

See `docs/COMPATIBILITY.md`, `compatibility/`, `evidence/` and the matching CI results. Unported, blocked, unexecuted, failing and passed work remain distinct. Passing existing tests alone would not prove complete feature parity.

## Build from a clean checkout

Install the pinned Rust toolchain from `rust-toolchain.toml`, Node.js 22+, Python 3.12+ and Git, then:

```sh
cargo test --locked --workspace --all-targets
node --test modeller/model.test.mjs
python3 tools/build_modeller.py --commit "$(git rev-parse HEAD)"
python3 -m http.server 8765 --directory build/modeller
```

Open `http://localhost:8765/index.html`. The builder expects a clean `build/` output area and downloads the exact Three.js package version. Native and browser tests are distinct. The full browser workflow runner is `tools/test_modeller.py`.

## Project layout

- `crates/blended-core`: ported mathematical cases, new Rust geometry, WASM ABI.
- `modeller`: the limited browser modeller, document model and state-history tests.
- `tools`: pinned upstream fetching, conservative test discovery, builds and real browser tests.
- `upstream.lock.json`: immutable Blender, Cycles and Solarxy source references.
- `compatibility-index`: generated discovery and port ledger branch.
- `modeller-build` / `modeller-evidence`: published app and durable public-URL evidence.
- `web-build` / `deployment-evidence`: failed Solarxy diagnostic app and failure evidence.

Original code is GPL-3.0-or-later. Translated upstream tests retain their Apache-2.0 notices. Solarxy attribution is retained; Three.js is MIT-licensed. Built deployments include licence texts and corresponding source archives. This project is independent of the Blender Foundation and Solarxy's author.
