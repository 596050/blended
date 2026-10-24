# Implementation status

## Current verified implementation

Source `efc7799e5050f28de66aa7ba11ed9a976165d21a` was verified in [run 40142038492](https://github.com/596050/blended/actions/runs/40142038492). [Open its 541-case workbench](https://rawcdn.githack.com/596050/blended/c3edd21e2e953d5275768223b869cbbb9a22d42e/index.html). Subsequent documentation-only commits do not change the tested executable implementation.

541 unique Blender runtime cases pass in native Rust and at the actual deployed Chromium URL, covering 3,196,218 expected assertion events. Independent original-C++ comparisons pass for native Rust and Chromium WebAssembly. Eight native and nine browser floating differences remain in older colour cases under original rules; no tolerances were widened. The polygon cases add no floating differences.

The complete native run passed **587 runtime tests: 541 Blender, three Cycles and 43 separate product/safety/regression tests**. Six compile-time assertions separately pass positive and deliberate-failure checks on native and wasm32. Repeated stress assertions and diagnostic corpus configurations are not extra Blender tests.

## Latest functionality

All 29 runtime cases in `BLI_polyfill_2d_test.cc` now have a Rust implementation and source-locked helpers. Ear clipping, concave-vertex KD-tree pruning, cached ear checks and heap-driven half-edge beautification reproduce the pinned results on the tested inputs. Both the original plain and beautified outputs are checked, preserving the original flags, topology, winding and area assertions.

The upstream rotation/reversal helper modifies a copy but passes the original polygon. That behaviour is explicitly preserved in the port. A separate original-C++ oracle covers 3,064 genuinely transformed configurations and checks 6,128 output triangulations, including index order, exactly against native Rust and Node.js WASM. The original full suite is separately run in Chromium at the deployed URL. [Detailed report](POLYFILL-PORT-VERIFICATION.md)

The new contract shard is explicitly required by all review/execution consumers. The original lock remains unchanged. Inventory scanning now discovers digit-prefixed test arguments, recovering eight declarations previously hidden from the source scan. Newly discovered tests are not automatically considered ported.

## Separate products and limits

The workbench tests the compatibility core. These mesh-library operations are not yet an interactive polygon editor or a complete BMesh system. The Three.js modeller remains the earlier object-editing alpha and its test button still uses the 17-case interface. The Solarxy/WebGPU experiment remains independently blocked.

Fresh native compilation, original assertion comparison, supplemental native/Node differential outputs and actual public Chromium acceptance remain separate evidence categories. Original geometric tests are not secretly strengthened: their known gap is addressed by a separately labelled corpus. No polygon-specific implementation-mutation probe was added in this batch; existing earlier-family probes still run.

The implementation accepts finite single-boundary polygons with checked indices. It does not promise hole support, non-overlapping fills for self-intersections, native allocator/ABI identity or competitive performance on arbitrary inputs.

## Remaining work

The complete Blender test port remains unfinished and the whole-suite gate remains failed. The latest heuristic audit contains **5,867 source candidates, 547 reviewed mappings and 5,320 unmapped declarations**. The mappings are 541 runtime plus six compile-time cases, not a complete runtime denominator. Full runtime discovery remains unknown.

Five conditional half-performance benchmarks remain unported, as do further vector type/layout compile-time conditions, configuration matrices and extensive application-level families. Complete mesh editing, sculpting, modifiers, Geometry Nodes, animation, rigging, simulation, compositing, video/tracking, Python add-ons, native `.blend` support and Cycles/EEVEE compatibility are still outstanding. Full test porting, all-tests-passing, feature parity and performance are different milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirement](COMPLETE-TEST-PORT.md) · [Open completion issue #3](https://github.com/596050/blended/issues/3)
