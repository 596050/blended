# Implementation status, 22 October 2026

## Current test-port continuation

The Rust compatibility suite contains 99 executed Blender runtime cases, three Cycles cases and ten additional product/safety cases: 112 native Rust tests. Run `39859518789` also verified all 99 Blender cases in browser WebAssembly at the actual public workbench URL. The represented runtime assertion count is 528: vector 68, scalar 225, new structures 235. Repeated test executions do not increase coverage counts.

The new 54 Blender cases cover entire index-range, binary-search and bounds test files, with 226 assertion sites, 235 runtime checks and a preserved compile-time condition. The original vector port now collects all nonfatal assertions and retains the upstream comparison semantics. Its separate signed-zero hash compile-time assertion remains unported.

Actual pinned Blender `BLI_test` was compiled. Its listing has 1,644 registrations, including an unresolved duplicate `stack.Peek` label. The original 54 newly ported cases all passed in that executable and reconcile exactly with the Rust case identities. Raw evidence and the scoped report are preserved at `07b2fd18d4fb15f83ddadbfb19acbd3a8a977bcb`. The limited native build is not the whole Blender test universe.

See `docs/COMPLETE-TEST-PORT.md`, `evidence/TEST-PORT-STATUS.json` and open completion issue #3. Full-completeness CI remains failed: 99 reviewed mappings are only a subset of 5,637 heuristic source candidates. No feature-parity percentage is claimed.

## Previously verified limited modeller

The working modeller is separate from the test workbench. Its initial source was `76044caffe2b69ae5cdceeff1addb56ee61411d9`, deployed at `a81530a62fcc8222ea57db4c5d8b35869d277963`. Run `39830750442` passed 28 public-URL acceptance checks. These cover actual visible Rust-generated cube geometry, deletion/render changes, creation, numeric translation, undo/redo, duplicate/delete, sphere/plane creation, scene save/reopen, OBJ/STL interchange, PNG output, the original 17-case test button and absence of browser errors.

Those checks include infrastructure/provenance checks, so 28 is not a Blender feature count. The modeller's original test button still exercises the compatible 17-case ABI. The separate conformance workbench exercises all 99 cases. Adding core tests does not add a mesh editor, animation system or other missing UI features.

## Failed Solarxy experiment retained

The pinned Solarxy app compiles. Its selected native suites passed 1,002 existing tests and its frontend passed 382 existing tests. Real browser rendering acceptance nevertheless failed: imported geometry was blank, and some runs lost the GPU device and panicked on later buffer allocation. Root cause remains unresolved. The attempted Mesa setup still selected SwiftShader and is not independent-driver verification.

Issue #1 and `deployment-evidence` preserve that failure. The working Three.js modeller is a separate subset, not a fix for Solarxy and not a way to turn failed WebGPU tests green.

## Assets and remaining implementation

The pinned `tests/files/**` LFS assets were downloaded and verified: 6,691 objects, 870,496,042 bytes, including 2,145 .blend files. This scope is not every possible test dependency, and fresh execution jobs still need to materialise their own inputs. Required startup assets were resolved for the limited native BLI build.

Most Blender features remain unimplemented: direct mesh/BMesh editing, modifiers, sculpting, Geometry Nodes, animation/rigging, physics, compositing/video, Python/add-ons, native .blend serialization and Cycles/EEVEE compatibility. Runtime discovery and faithful test ports for these families remain outstanding.

The next compatibility steps are broader native reference discovery and source reconciliation, followed by actual mesh/topology operations and their attribute/normal/undo contracts. Rendering semantics, colour management, scene evaluation, browser/device coverage and memory/performance budgets need separate acceptance evidence.
