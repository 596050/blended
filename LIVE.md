# Open Blended

## [Launch the browser modeller alpha](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the modelling application, not the compatibility workbench. It remains the earlier verified object-editing alpha, not a complete Blender replacement. Use public sample files on this shared-origin preview and save work locally. Verified source: `25e641c0d311f61c473755d1c7ee821289a27d15`; [public build/deployment test](https://github.com/596050/blended/actions/runs/39860686907).

## [Run the deployed 596-case Blender test workbench](https://rawcdn.githack.com/596050/blended/4cc3dade093dd7da5899ed995e02ce3689225fb2/index.html)

This page executes every currently registered Blender runtime port, not all Blender tests. Source `f86fae88ce889175fcaa11dcb982d3bbc4fce5ca`, static build `4cc3dade093dd7da5899ed995e02ce3689225fb2`, was tested at this actual public URL in [run 40149763130](https://github.com/596050/blended/actions/runs/40149763130). **All 596 cases passed**, with 3,196,692 expected assertion executions and no recorded browser errors. Local diagnostic comparisons and mutation probes are separate evidence, not substitutes for public-URL execution.

[Original C++/native/browser assertion reports](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40149763130) · [Exact mask/input oracle](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40149763130/mask-comparison.json) · [Negative set-operation controls](https://github.com/596050/blended/blob/4cc3dade093dd7da5899ed995e02ce3689225fb2/verification/evidence/mask-expression-sensitivity/result.json)

The complete Blender test port is unfinished and its whole-suite gate remains failed. Immutable application URLs do not advance when branches change. [Latest status](evidence/TEST-PORT-STATUS.json) · [Mask-expression scope](docs/MASK-EXPRESSION-PORT-VERIFICATION.md) · [Outstanding requirements](docs/COMPLETE-TEST-PORT.md)
