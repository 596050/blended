# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the compatibility dashboard. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 609-case Blender test workbench](https://rawcdn.githack.com/596050/blended/55479ba6a6249846abc4c36d36440b27bfe106b4/index.html)

This page executes every currently registered Blender runtime port, not all of Blender. Runtime source `7a3dec93c2c02605834330b5de6872d6f1dbe4ad`, static build `55479ba6a6249846abc4c36d36440b27bfe106b4`, was tested at this actual public URL in [run 40209288469](https://github.com/596050/blended/actions/runs/40209288469). **All 609 cases passed**, with 3,196,744 expected assertion executions and no recorded browser errors. Diagnostic local browser comparisons and mutation probes are separate evidence from this production public-URL test.

[Original C++/native/browser fidelity evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40209288469) · [Exact map/view observations](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40209288469/container-comparison.json) · [Negative implementation controls](https://github.com/596050/blended/blob/55479ba6a6249846abc4c36d36440b27bfe106b4/verification/evidence/container-view-sensitivity/result.json)

The whole-suite completeness check remains failed. These immutable links do not advance when branches change. The model editor has not been replaced by the workbench. [Latest status](evidence/TEST-PORT-STATUS.json) · [Map/view implementation details](docs/CONTAINER-VIEW-PORT-VERIFICATION.md) · [Outstanding requirements](docs/COMPLETE-TEST-PORT.md)
