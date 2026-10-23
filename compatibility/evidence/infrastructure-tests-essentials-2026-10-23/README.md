# Infrastructure regression execution and base-package replay

`execution.json` records the actual subprocess that ran the complete repository
infrastructure suite. Original stdout and stderr bytes are retained separately,
along with command arguments, start/end times, process exit, Python and CMake
identities, and before/after source-file manifests.

The command was:

```sh
env BLENDED_INVENTORY_CMAKE=/workspace/scratch/d63596d831b2/runtime/browser-python/bin/cmake python3 -m unittest discover -s tests -q
```

Unittest reported **294 tests in 106.474 seconds, OK, zero skips**. The actual
process returned **0**. The tool, test, patch, and reviewed package-plan file
identities remained unchanged during execution. The source manifests and Git
status identify the tested changes; the recorded Git HEAD alone predates those
uncommitted changes and is not presented as their complete identity.

Any failed/blocked JSON records in stdout belong to expected negative
infrastructure fixtures. They are separate from the top-level unittest result.
This run checks test infrastructure, receipt validation, inventory handling,
package binding, and related tooling. It does not count as all upstream Blender
tests passing or prove application feature parity.

`base-normalization-recheck.json` records a separate full conversion of the
original base-package matrices through the updated converter. Every pair,
registration assessment, and observation diagnostic matches the preserved v2
assessment: **829 obligations, 512 strict successes, 597 outcome agreements,
132 required declarations, and 101 unresolved declarations**. The conversion
used `--report-only`, so its process returned 0 while its parity gate correctly
remained blocked. Original v2 evidence was not changed. The temporary generated
files were hashed and are reproducible from the recorded command and immutable
versioned inputs; stdout and stderr from the actual conversion are retained.
