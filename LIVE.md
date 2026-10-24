# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the compatibility dashboard. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 541-case Blender test workbench](https://rawcdn.githack.com/596050/blended/c3edd21e2e953d5275768223b869cbbb9a22d42e/index.html)

Source `efc7799e5050f28de66aa7ba11ed9a976165d21a`, static build `c3edd21e2e953d5275768223b869cbbb9a22d42e`, was tested at this actual public URL in [run 40142038492](https://github.com/596050/blended/actions/runs/40142038492). **All 541 registered Blender cases passed**, with 3,196,218 expected assertion executions and no recorded browser errors. This is every implemented case, not every Blender test.

[Original C++/native/Chromium fidelity evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40142038492) · [Exact polygon-permutation oracle](https://github.com/596050/blended/blob/c3edd21e2e953d5275768223b869cbbb9a22d42e/verification/evidence/polyfill-oracle/result.json) · [Detailed polygon report](docs/POLYFILL-PORT-VERIFICATION.md)

The extra polygon corpus runs in native Rust and Node.js WebAssembly; it is distinct from the production Chromium public-URL test and the original assertion-level Chromium comparison. All have their own recorded scope. The whole-suite completeness job remains failed. Immutable links do not advance when branches change. [Current status](evidence/TEST-PORT-STATUS.json) · [Outstanding requirements](docs/COMPLETE-TEST-PORT.md)
