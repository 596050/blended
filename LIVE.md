# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the test workbench. It is an object-editing alpha, not a complete Blender replacement. This historical immutable build was verified from source `25e641c0d311f61c473755d1c7ee821289a27d15`. Use public sample models on the shared-origin preview and save work locally.

## [Run the verified 338-case Blender test workbench](https://rawcdn.githack.com/596050/blended/a5fc4aa4074e556431c8e7fd1bb1185f130b3be0/index.html)

This separate page executes every currently registered Blender runtime port. Source: `8bb0e6e43237cc68cf5e3c403dfc0b9419f083ed`. Static build: `a5fc4aa4074e556431c8e7fd1bb1185f130b3be0`. Original reference: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.

All 338 cases passed at the actual public URL, with no browser errors. The ordered original-C++ comparisons cover 16,804 assertion executions in both native Rust and Chromium WebAssembly. The six separately tracked compile-time assertions are not browser runtime cases. Diagnostic runs and production-URL tests remain separate.

[Build and public verification run](https://github.com/596050/blended/actions/runs/40007823640) · [Durable assertion evidence for that run](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40007823640) · [Static build source and audit](https://github.com/596050/blended/tree/a5fc4aa4074e556431c8e7fd1bb1185f130b3be0) · [Sampling verification](docs/SAMPLING-PORT-VERIFICATION.md)

The full Blender test port remains incomplete and its completeness gate remains failed. Passing the implemented subset does not establish all Blender features, renderer compatibility or performance parity. Evidence branches can advance; the immutable URLs above do not.
