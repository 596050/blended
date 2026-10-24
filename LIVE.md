# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the test workbench. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample models on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 464-case Blender test workbench](https://rawcdn.githack.com/596050/blended/51d30f5a549da822a9dc0945d353ef6414938092/index.html)

This separate page executes all currently registered Blender runtime ports, not all Blender tests. Source `ab692209e9eb98248054ae90ead9b0258f1ab4da`, static build `51d30f5a549da822a9dc0945d353ef6414938092`, was tested at this actual public URL in [run 40049834310](https://github.com/596050/blended/actions/runs/40049834310). All 464 cases and their 34,214 expected assertion executions passed, with no recorded browser errors.

[Original C++/Rust/browser transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40049834310) · [Published string oracle](https://github.com/596050/blended/blob/51d30f5a549da822a9dc0945d353ef6414938092/verification/evidence/string-oracle/result.json) · [Published mutation controls](https://github.com/596050/blended/blob/51d30f5a549da822a9dc0945d353ef6414938092/verification/evidence/string-sensitivity/result.json)

Diagnostic local Chromium execution and public-URL acceptance are separate verification layers. The whole-suite completeness gate remains failed. Immutable application URLs do not advance with documentation commits or evidence branches.

[Current machine-readable status](evidence/TEST-PORT-STATUS.json) · [Accuracy and scope](docs/STRING-OPS-PORT-VERIFICATION.md) · [Unfinished full-suite requirements](docs/COMPLETE-TEST-PORT.md)
