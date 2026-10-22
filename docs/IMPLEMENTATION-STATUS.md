# Implementation status, 22 October 2026

## Complete Blender test port: unfinished

The latest test-port work is documented in [COMPLETE-TEST-PORT.md](COMPLETE-TEST-PORT.md), `evidence/TEST-PORT-STATUS.json`, and issue #3. The complete-suite acceptance job must still fail.

45 Blender runtime cases now pass natively and through real browser WebAssembly, including the original 17 vector cases and 28 additional cases preserving 225 assertions from five complete source files. The separate signed-zero hash static assertion in the original vector file is still unported. There are also 3 Cycles native cases, 6 product geometry tests and 4 safety tests, giving 58 native Rust tests overall.

Actual public-URL subset verification: run `39849051906`, source `006fdfb8fc48e5fa22fadbd8e822337a0c83274c`, static commit `950ea85b0f4438bc5e082a0f9a402973f01d4de3`. Latest published evidence is on `test-port-evidence`; every report identifies the specific build tested. The workbench is distinct from the modeller application.

Fixture run `39847680248` downloaded all 6,691 LFS objects under pinned `tests/files/**`, independently verifying every SHA-256 and size. This is 870,496,042 bytes and includes 2,145 .blend files. It does not establish all external dependencies or test execution. The original source scan also found 24 .blend pointers outside this verified tree. Fresh checkouts must still resolve LFS payloads before executing fixture-based tests.

The source ledger retains 5,637 candidates, including conditional, parameterised, compile-time and third-party declarations. 45 have reviewed mappings and 5,592 do not. This is not a complete runtime count. The exact native reference build and runtime enumeration remain unfinished. No parity percentage is claimed.

## Previously verified limited modeller

Source: `76044caffe2b69ae5cdceeff1addb56ee61411d9`.
Published static commit: `a81530a62fcc8222ea57db4c5d8b35869d277963` on `modeller-build`.
Actual public-URL acceptance: run `39830750442`, report `modeller-evidence/result.json`.

Its 28 acceptance checks passed against the public URL. They cover rendered cube pixels, geometry edits, object transforms, undo/redo, duplication/deletion, sphere/plane creation, scene-file round trips, OBJ/STL interchange, PNG output and its original 17 WASM mathematical cases. The 28 includes infrastructure checks, so it is not a count of Blender features. This historical immutable modeller build has not been replaced by the conformance workbench.

## Failed Solarxy experiment retained

The pinned Solarxy build compiled and passed 1,002 selected native and 382 frontend tests, but real browser rendering acceptance failed. Some runs lost the GPU device and later panicked on a mapped-buffer allocation. Root cause remains unresolved. The attempted Mesa configuration still selected SwiftShader and did not verify an independent driver.

The diagnostic deployment and failures remain on `web-build` / `deployment-evidence` and issue #1. The working Three.js modeller is a separate limited implementation, not a fix for the Solarxy failure, and does not inherit its node system.

## Functional gaps

Blender-compatible mesh/BMesh editing, modifiers, sculpting, full Geometry Nodes, animation, rigging, physics, compositing, video editing, Python/add-ons, .blend serialisation and Cycles/EEVEE parity remain unfinished.

Full test-port completion requires exact runtime discovery, assertion-preserving translations/adapters, test dependency verification and native/browser execution evidence. Full application compatibility additionally requires a feature/workflow catalogue and end-to-end, device, performance and large-scene checks. A green subset, a complete source scan or even full test conformance must not be substituted for those separate requirements.
