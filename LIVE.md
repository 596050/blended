# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the compatibility dashboard. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 503-case Blender test workbench](https://rawcdn.githack.com/596050/blended/a7f55a00388e7b3fb906c307cc52db7968b9a25d/index.html)

This page executes every currently registered Blender runtime port, not all of Blender. Source `3969e1fdadae2e11d6f220412f8c32cabf7048d1`, static build `a7f55a00388e7b3fb906c307cc52db7968b9a25d`, was tested at its actual public URL in [run 40065241089](https://github.com/596050/blended/actions/runs/40065241089). **All 503 cases passed**, including their 1,661,377 expected assertion executions, with no recorded browser errors. Local diagnostic Chromium comparisons and mutation probes are separate evidence from this production public-URL run.

[Original C++/native/browser fidelity evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40065241089) · [Exact UTF-8 and byte-RNG oracle](https://github.com/596050/blended/blob/a7f55a00388e7b3fb906c307cc52db7968b9a25d/verification/evidence/utf8-oracle/result.json) · [Negative implementation controls](https://github.com/596050/blended/blob/a7f55a00388e7b3fb906c307cc52db7968b9a25d/verification/evidence/utf8-sensitivity/result.json)

The whole-suite completeness check remains failed. These immutable application links do not advance when branches change. [Latest status](evidence/TEST-PORT-STATUS.json) · [UTF-8 implementation details](docs/UTF8-PORT-VERIFICATION.md) · [Outstanding requirements](docs/COMPLETE-TEST-PORT.md)
