# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the test workbench. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 367-case Blender test workbench](https://rawcdn.githack.com/596050/blended/19abc219cd1ccb7e2dd4090c23710638f30959d8/index.html)

This page executes all currently registered Blender runtime ports, not all of Blender. Source `df61b87fa3b2b5a0751100e427eab11d7205ad5a`, static build `19abc219cd1ccb7e2dd4090c23710638f30959d8`, was tested at this actual public URL in [run 40019426923](https://github.com/596050/blended/actions/runs/40019426923). All 367 cases and their 33,104 expected assertion executions passed, with no recorded browser errors. Production public-URL execution is distinct from diagnostic local Chromium comparisons and mutation probes.

[Original C++/Rust/browser assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40019426923) · [Published input-verification evidence](https://github.com/596050/blended/blob/19abc219cd1ccb7e2dd4090c23710638f30959d8/verification/evidence/heap-inputs/result.json) · [Published negative controls](https://github.com/596050/blended/blob/19abc219cd1ccb7e2dd4090c23710638f30959d8/verification/evidence/heap-sensitivity/result.json)

The complete Blender test port remains unfinished and its whole-suite gate remains failed. The modeller and workbench links are immutable builds. [Current machine-readable status](evidence/TEST-PORT-STATUS.json) · [Outstanding requirements](docs/COMPLETE-TEST-PORT.md)
