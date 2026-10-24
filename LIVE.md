# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the compatibility dashboard. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 512-case Blender test workbench](https://rawcdn.githack.com/596050/blended/15a67995bdca8581e9f1e28b9b95af17ea69d51b/index.html)

This page executes every currently registered Blender runtime port, not all of Blender. Source `2990e30077e368c97e3a7af60d45d7a911ceb988`, static build `15a67995bdca8581e9f1e28b9b95af17ea69d51b`, was tested at this actual public URL in [run 40108130160](https://github.com/596050/blended/actions/runs/40108130160). **All 512 cases passed**, with 1,661,546 expected assertion executions and no recorded browser errors. Local diagnostic browser comparisons and mutation probes remain separate from the production public-URL run.

[Original C++/native/browser fidelity evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40108130160) · [Bit-exact format oracle](https://github.com/596050/blended/blob/15a67995bdca8581e9f1e28b9b95af17ea69d51b/verification/evidence/pixel-formats-oracle/result.json) · [Negative implementation controls](https://github.com/596050/blended/blob/15a67995bdca8581e9f1e28b9b95af17ea69d51b/verification/evidence/pixel-formats-sensitivity/result.json)

The browser explicitly reports no hardware FP control; native FTZ/DAZ checks are a different capability. The whole-suite completeness job remains failed. Immutable links do not advance when branches change. [Latest status](evidence/TEST-PORT-STATUS.json) · [Format implementation details](docs/PIXEL-FORMAT-PORT-VERIFICATION.md) · [Outstanding requirements](docs/COMPLETE-TEST-PORT.md)
