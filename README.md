# Blended

**A deployed, tested browser modeller alpha. Not a complete Blender clone. The complete Blender test port is still unfinished.**

[Open the verified modeller](https://rawcdn.githack.com/596050/blended/a81530a62fcc8222ea57db4c5d8b35869d277963/index.html) · [Modeller public-URL results](https://github.com/596050/blended/blob/modeller-evidence/result.json) · [Complete-test-port requirement](docs/COMPLETE-TEST-PORT.md)

[Open the 45-case Rust/WASM test workbench](https://rawcdn.githack.com/596050/blended/950ea85b0f4438bc5e082a0f9a402973f01d4de3/index.html) · [Latest public test-port evidence](https://github.com/596050/blended/blob/test-port-evidence/result.json) · [Full-port completion blocker #3](https://github.com/596050/blended/issues/3)

The modeller and conformance workbench are different deployments. The linked modeller uses source `76044caffe2b69ae5cdceeff1addb56ee61411d9`. The linked workbench uses source `006fdfb8fc48e5fa22fadbd8e822337a0c83274c`; newer workbenches record their own exact source revision and test evidence. Neither deployment establishes whole-application Blender parity.

## Working initial modeller

- Actual Three.js WebGL 2 rendering, orbit/pan/zoom and transform controls.
- Rust/WebAssembly-generated boxes and planes; Three.js spheres.
- Object selection, numeric transforms, duplication/deletion and bounded undo/redo.
- Basic colour, roughness, metalness, wireframe and grid controls.
- Save/reopen `.blended.json` scenes; static OBJ/STL geometry import/export and PNG viewport output.
- The original modeller's compatibility button executes its 17 original mathematical cases. The separate workbench executes all 45 currently ported Blender cases.

Its public-URL acceptance run `39830750442` passed 28 checks, including rendered pixels, geometry edits, undo/redo, file round trips and outputs. This is not a count of 28 Blender features. Hardware-GPU performance has not been benchmarked.

## Test-port status

| Scope | Verified or recorded result |
| --- | --- |
| Blender runtime cases | 45 ported cases pass natively and in actual browser WebAssembly |
| New complete source-file ports | 28 cases, preserving 225 assertions from five files |
| Original vector-maths file | 17 runtime cases ported; separate signed-zero hash static assertion unported |
| Cycles native cases | 3 integer-maths tests; no renderer parity established |
| Additional Rust product/safety tests | 6 geometry and 4 safety tests |
| Total native Rust tests | 58, not 58 Blender ports |
| JavaScript modeller tests | 10 scene/history cases |
| Source accounting | 5,637 Blender candidates, 45 reviewed mappings, 5,592 unmapped candidates |
| Fixture payload verification | 6,691 of 6,691 LFS objects in `tests/files/**` verified by SHA-256 and size |
| Complete Blender test port | **Not complete; dedicated CI job fails** |

The five additional files cover base/safe maths, bit operations, tridiagonal solvers and time decomposition. These are executable Rust tests, not success placeholders. Inputs, expected values, comparison policies and original tolerances are preserved; source/target hash locks detect subsequent assertion-code drift. Generated tests and frozen upstream originals are committed, and CI checks reproducibility.

Source candidates include compile-time assertions, third-party and conditional declarations, and unexpanded parameterised tests. They are NOT a complete runtime denominator. Do not derive a parity percentage from them. CTest/GoogleTest/Python/render/UI/runtime enumeration and most test ports remain outstanding.

The fixture verification run `39847680248` downloaded 870,496,042 bytes, including 2,145 `.blend` files. Its object-by-object evidence is permanently retained [here](https://github.com/596050/blended/blob/950ea85b0f4438bc5e082a0f9a402973f01d4de3/fixture-evidence/fixture-verification.json). The older scan's 2,169 `.blend` pointers included 24 outside this verified directory. Other dependencies still need verification; downloading fixtures does not execute tests, and fresh checkouts still require LFS materialisation.

Test-first evidence: additional Blender tests failed before their implementation in run `39846695564`; native and browser execution passed in `39848464324`; actual public-URL execution passed in `39849051906`. The full-completeness gate in that last run remained failed. See [acceptance criteria and remaining work](docs/COMPLETE-TEST-PORT.md), `compatibility/assertion-contracts.lock.json` and `evidence/TEST-PORT-STATUS.json`.

## Important application limits

**Full Blender and Cycles functionality are NOT implemented.** The modeller has no Blender-compatible mesh edit mode, sculpting, animation/rigging, physics, compositor, Python add-on API, `.blend` support or Cycles/EEVEE renderer. OBJ export does not include materials. Import and history are bounded and are not designed for Blender-scale scenes.

The free preview is a third-party shared-origin CDN serving GitHub files. Use public sample models only and save work locally. No paid service or server-side GPU was provisioned. A GitHub Pages workflow is available for a dedicated site once Pages is enabled.

The separately built Solarxy/WebGPU experiment compiled and passed selected native/frontend tests but failed real browser rendering acceptance. It remains a [diagnostic preview](https://rawcdn.githack.com/596050/blended/5782100e39cff4325983f4be9949b651d488417c/index.html), with [blocker #1](https://github.com/596050/blended/issues/1). The Three.js modeller does not fix that failure or inherit Solarxy's procedural node system.

## Reproduce checks

With the pinned Rust toolchain, Node.js 22+, Python 3.12+ and Git:

```sh
cargo test --locked --workspace --all-targets
node --test modeller/model.test.mjs
python3 -m unittest discover -s tests -v
python3 tools/build_modeller.py --commit "$(git rev-parse HEAD)"
python3 -m http.server 8765 --directory build/modeller
```

The full port audit is a separate command documented in `docs/COMPLETE-TEST-PORT.md`. It must currently exit nonzero. Do not remove unported cases or use `continue-on-error` to label it complete. Passing the full test suite would still be separate from whole-application feature/workflow compatibility.

## Layout and evidence

- `crates/blended-core`: Rust maths, conformance cases, product geometry and WASM ABI.
- `modeller`: limited Three.js application and scene/history tests.
- `tests/upstream/blender`: pinned originals for the new ports.
- `compatibility`: source identities and reviewed assertion contracts.
- `tools`: fetch/build, source inventory, completeness audit and real browser execution.
- `modeller-build` / `modeller-evidence`: application deployment and test evidence branches.
- `test-port-build` / `test-port-evidence`: conformance deployment, full candidate audit, fixture metadata and public execution evidence.
- `compatibility-index`: original cross-project source inventory; not runtime completeness.

Original project code is GPL-3.0-or-later; adapted components and translated tests retain their upstream notices. Built workbenches include corresponding source. This project is independent of the Blender Foundation and Solarxy's author.
