# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the test workbench. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 416-case Blender test workbench](https://rawcdn.githack.com/596050/blended/63655e85d5b56c357645c92e3874af3940fd161e/index.html)

This page executes all currently registered Blender runtime ports, not all of Blender. Source `059bfb9b277e8bc5aefb9834dd671879094a0599`, static build `63655e85d5b56c357645c92e3874af3940fd161e`, was tested at this actual public URL in [run 40045600207](https://github.com/596050/blended/actions/runs/40045600207). All 416 cases passed with no recorded browser errors. The original-C++ comparisons cover 33,368 ordered assertion events per implementation.

[Original C++/native/browser comparison records](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40045600207) · [Streaming-hash oracle](https://github.com/596050/blended/blob/63655e85d5b56c357645c92e3874af3940fd161e/verification/evidence/hash-streaming/result.json) · [Negative implementation controls](https://github.com/596050/blended/blob/63655e85d5b56c357645c92e3874af3940fd161e/verification/evidence/data-sensitivity/result.json)

Production public-URL execution is distinct from local diagnostic Chromium comparisons. The complete Blender test port is unfinished and its whole-suite gate remains failed. Both application links are immutable builds. [Current status](evidence/TEST-PORT-STATUS.json) · [Latest scope and limitations](docs/DATA-PORT-VERIFICATION.md)
