# Open Blended in your browser

## [Launch the deployed Blended modeller](https://rawcdn.githack.com/596050/blended/15752e8b7c31cc1ea3aa4ec32ab7457b0736ab38/index.html)

This is the working browser modeller alpha, not the test dashboard. It is not a complete Blender replacement. Use public sample models on this shared-origin preview and save work locally.

## [Open the deployed Blender test-port workbench](https://rawcdn.githack.com/596050/blended/7e739cb44988dbbae353272b1ac1bfe809a5cf8a/index.html)

This separate page executes the 99 currently ported Blender runtime cases. It is not the modelling application. Passing this subset does not establish a complete test port or full feature parity.

Both immutable builds above were verified from source commit `25e641c0d311f61c473755d1c7ee821289a27d15`.

| Evidence | Link |
| --- | --- |
| Modeller build, deployment and actual public-URL test | [Actions run 39860686907](https://github.com/596050/blended/actions/runs/39860686907) |
| Modeller public results | [modeller-evidence/result.json](https://github.com/596050/blended/blob/modeller-evidence/result.json) |
| Test workbench build and actual public-URL verification | [Actions run 39860686893](https://github.com/596050/blended/actions/runs/39860686893) |
| Workbench public results | [test-port-evidence/result.json](https://github.com/596050/blended/blob/test-port-evidence/result.json) |
| Complete-suite requirements and outstanding work | [Complete test-port requirement](docs/COMPLETE-TEST-PORT.md) |

The full-completeness job remains failed while tests are missing. The successful subset deployment must not be interpreted as full-suite completion. Evidence branches can advance; the immutable application URLs above do not change.
