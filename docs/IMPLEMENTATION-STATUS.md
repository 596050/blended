# Implementation status

## Current verified implementation

Source `3969e1fdadae2e11d6f220412f8c32cabf7048d1` was verified by [run 40065241089](https://github.com/596050/blended/actions/runs/40065241089). [Open its 503-case public workbench](https://rawcdn.githack.com/596050/blended/a7f55a00388e7b3fb906c307cc52db7968b9a25d/index.html). Later documentation-only commits do not change that runtime implementation.

503 unique Blender runtime cases pass natively and at the actual deployed URL, covering 1,661,377 expected assertion executions. Original C++ versus native Rust and Chromium WebAssembly comparisons passed. Eight native and nine browser floating differences remain in the earlier colour cases within original rules; no tolerance was widened. No additional floating difference comes from the new UTF-8 tests.

The native Rust total is **542 runtime tests: 503 Blender, three Cycles and 36 product/safety/regression tests**. Six separately tracked compile-time assertions pass positive builds and deliberate-failure checks on both native and wasm32. Repeated stress assertions, extra oracle inputs and mutation probes are not additional upstream cases.

## Latest functionality and verification

All 39 cases in `BLI_string_utf8_test.cc` are now ported with original stress loops, malformed-byte fixtures, bounds, formatting expectations and cursor inputs. They add 1,627,163 assertion executions. The corresponding implementation covers pinned legacy validation/repair, decoding, length/copying, the tested formatting form and UTF-8/UTF-32 cursor movement.

The independent original-C++ oracle exactly matches 68,273 validator results, 137,426 decoded-value/next-offset pairs and 48,640 generated random bytes on both Rust targets. Three implementation-only mutations fail unchanged original cases while controls pass. The exact pinned zero-width interval table is regenerated and its full notice is included in downloadable source. [Detailed UTF-8 report](UTF8-PORT-VERIFICATION.md)

Every original-reference assertion event is still compared. Large transcripts are processed in bounded batches and preserved losslessly as gzip with verified decompressed hashes and sizes. This is an execution/transport improvement, not reduced test scope or a performance-parity claim.

## Separate products and evidence

The workbench tests the compatibility core. The Three.js modeller remains the earlier object-editing alpha; new core tests are not new interactive Blender tools. Its legacy test button still uses the 17-case ABI. The separate Solarxy/WebGPU rendering experiment remains independently blocked.

Fresh native compilation, original-reference comparisons, diagnostic browser checks and actual public-URL tests are separate evidence categories. Historical 99/131/211/272/302/338/367/416/464-case records retain their original scope and are not substituted for the new combined build.

## Remaining requirements

The complete Blender test port is unfinished and the full-completeness gate remains failed. The current heuristic scan contains **5,859 source candidates, 509 reviewed mappings and 5,350 unmapped declarations**. The runtime denominator remains unknown. Nine previously identified vector type/layout compile-time conditions and extensive application-level families remain outside the verified subset. A historical fixture download does not materialise fixtures for a fresh execution checkout.

There is no complete mesh/BMesh editor, sculpting, modifier/Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. Full test porting, full-suite execution, feature compatibility and competitive performance remain different milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Completion blocker #3](https://github.com/596050/blended/issues/3)
