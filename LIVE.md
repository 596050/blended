# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This remains the earlier object-editing alpha, not the test dashboard or a complete Blender replacement. Use public sample files on this shared-origin preview and save locally. Source `25e641c0d311f61c473755d1c7ee821289a27d15`; [historical public acceptance run](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 581-case Blender test workbench](https://rawcdn.githack.com/596050/blended/d32122067882b90b631adc1e4f765f708f10fe33/index.html)

Source `8952a0ef18a83bb7a56656dd8519095bd0fb2cd2`, static build `d32122067882b90b631adc1e4f765f708f10fe33`, was tested at this actual public URL in [run 40145587317](https://github.com/596050/blended/actions/runs/40145587317). All **581 cases and 3,196,371 expected runtime assertion events passed**, with no recorded browser errors. Nineteen compile-time predicates are verified separately, not counted as extra runtime cases.

[Original C++/native/browser comparisons](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40145587317) · [Span compiler checks](https://github.com/596050/blended/blob/d32122067882b90b631adc1e4f765f708f10fe33/verification/evidence/span-static/result.json) · [Exact span oracle](https://github.com/596050/blended/blob/d32122067882b90b631adc1e4f765f708f10fe33/verification/evidence/span-oracle/result.json) · [Mutation controls](https://github.com/596050/blended/blob/d32122067882b90b631adc1e4f765f708f10fe33/verification/evidence/span-sensitivity/result.json)

The whole-suite completeness check remains failed. Diagnostic local Chromium execution and production public-URL acceptance are distinct. Immutable links do not change when branches advance. [Current status](evidence/TEST-PORT-STATUS.json) · [Span scope and limitations](docs/SPAN-PORT-VERIFICATION.md)
