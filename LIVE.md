# Open Blended in your browser

## [Launch the deployed Blended modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This opens the working modeller alpha, not a test dashboard. It is not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Open the deployed 131-case Blender test-port workbench](https://rawcdn.githack.com/596050/blended/959d4ccef446cfcd4f4e82a701fb3c32541a0f9d/index.html)

This separate page runs 131 currently ported Blender runtime cases, representing 1,049 assertion events. It does not open the modelling application. Verified source: `2c7abe637e8eca6ea8937c871f406fa6ac123006`; [original-reference, native, WASM and actual public-URL verification](https://github.com/596050/blended/actions/runs/39918173966).

The native Rust and diagnostic browser assertion transcripts were independently compared with original pinned Blender C++ execution. Both matched. The separately ported signed-zero hash assertion is evaluated by the native and WASM compilers and is not added to the runtime case count.

[Public workbench results](https://github.com/596050/blended/blob/test-port-evidence/result.json) · [Original C++ versus native Rust](https://github.com/596050/blended/blob/assertion-fidelity-evidence/native-comparison.json) · [Original C++ versus browser WASM](https://github.com/596050/blended/blob/assertion-fidelity-evidence/browser-comparison.json) · [Audit methodology](docs/ASSERTION-FIDELITY.md)

**The complete Blender test port remains incomplete.** The full-completeness job remains failed; these passing subset checks are not a complete compatibility certificate. [Remaining requirements](docs/COMPLETE-TEST-PORT.md).

Evidence branches can advance; the immutable URLs above do not. The two applications deliberately use distinct URLs and recorded source revisions.
