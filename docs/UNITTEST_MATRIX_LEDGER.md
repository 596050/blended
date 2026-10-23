# Reconcile original unittest executions

`tools/reconcile_unittest_matrix.py` converts immutable original-script native
and browser observations into the typed contract consumed by
`tools/test_parity_ledger.py`. It executes no Blender tests and makes no claim
that a source plan is a complete configured CTest inventory.

The base plan must retain all 132 declarations from the independently pinned
CMake source catalog, including their exact text, line numbers and contexts.
Dropping an unresolved declaration or changing both an invocation's arguments
and its claimed declaration is rejected. Explicit retry plans may contain a
subset only when they bind and preserve that complete base plan. Concrete
case IDs come only from the frozen native unittest loader inventory. A browser
import failure, incomplete execution, missing outcome, conditional subtest, or
missing external comparison program cannot reduce that denominator.

## Reproducible command

Run from the repository root, choosing a new output directory:

```sh
python3 tools/reconcile_unittest_matrix.py \
  --source-plan compatibility/evidence/unittest-native-5.2-2026-10-23/discovery-inventory.json \
  --native-retry-plan compatibility/evidence/unittest-native-resources-5.2-2026-10-23/resource-retry-inventory.json \
  --browser-matrix compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23/matrix.json \
  --browser-matrix compatibility/evidence/unittest-browser-resources-5.2-2026-10-23/matrix.json \
  --native-context compatibility/evidence/runtime-context-2026-10-23/native-context.json \
  --browser-context compatibility/evidence/runtime-context-2026-10-23/browser-context.json \
  --output compatibility/evidence/unittest-paired-5.2-2026-10-23 \
  --report-only
```

Omit the retry plan and its browser matrix to reproduce the initial selection.
A retry must bind a supplied base plan, preserve the exact original source
declaration, and explicitly identify the attempt it supersedes. The selected
browser receipt must bind the new frozen manifest. An old browser run cannot be
paired with a resource-corrected native invocation merely because the CTest
name stayed the same. Previous raw attempts remain immutable and are referenced
in the conversion record.

Exit status is `0` for a passing declared scope, `1` for a valid but blocked
scope, and `2` for invalid or inconsistent evidence. `--report-only` changes
only the exit status of a valid blocked report; it does not change its result.
Existing output directories are never overwritten.

`--repo-root` explicitly identifies a relocated checkout. Historical absolute
paths inside `compatibility/` are resolved beneath that root and checked against
their recorded hashes. Paths to original runtime archives and executables remain
measurement metadata; the converter does not follow those external paths or
pretend to remeasure an unavailable executable. Symlink inputs and paths escaping
the checkout are rejected.

## Generated evidence

| File | Meaning |
| --- | --- |
| `contract.json` | Every supplied source obligation, exact invocation/input/policy hashes, measured artifact contexts, and explicit coverage limits. |
| `inventory.json` | Fixed native case identities for expanded declarations; unresolved declarations remain blocked. |
| `executions.json` | Selected native/browser run references, bound to the contract and inventory. |
| `receipts/` | Typed native discovery and execution receipts with exact case and subtest outcomes, actual process status, and validation blockers. |
| `report.json` | Paired assessment, separate observed callback totals, and missing/unexpected subtest counts. |
| `conversion.json` | Per-registration diagnostics, raw exceptions, original input locations, and explicit superseded attempts. |
| `raw/` | Content-addressed copies of the exact input evidence bytes, logs, archived inputs, context measurements, and browser harness snapshots. |
| `normalizer/` | The converter and its validation dependencies as used for this conversion. |

All generated receipt references are relative to the output directory. The
normalized output can be copied on its own and reassessed without the original
runtime installation:

```sh
python3 NORMALIZED/normalizer/test_parity_ledger.py \
  --contract NORMALIZED/contract.json \
  --inventory NORMALIZED/inventory.json \
  --executions NORMALIZED/executions.json \
  --evidence-root NORMALIZED \
  --output reassessed.json \
  --report-only
```

The generic ledger reproduces the paired assessment. The converter additionally
computes the observation totals and subtest-difference diagnostics.

## What is checked

The original CMake invocation is authenticated against both complete upstream
CMake texts in `tools/upstream_invocations_5_2.json`; their bytes and reconstructed
declarations are checked against fixed hashes. The source and support-file identities, resource and
fixture manifests, native frozen IDs, actual Blender build identity, browser
engine files, independent runtime context, original script arguments, browser
host command, and harness snapshot must agree. A receipt parsed by the converter
is the same byte sequence whose hash was checked. Its execution observation must
also equal the single original result event in the corresponding raw log.

The browser report must fall within the recorded host process interval and must
bind the selected frozen manifest. A stale receipt for the same script cannot
substitute for the current run. The host command must identify the measured
harness and may not introduce an additional cohort selector or other unreviewed
argument.

Native completion comes from the recorded subprocess return code. Browser
completion comes from the recorded engine `runtime_exit_code`, together with
the outer host process completion. Host exit zero or a printed pass marker alone
cannot supply a missing engine exit. A legitimate boolean payload from the
original script's `SystemExit` is preserved separately; an actual process return
code must be an integer. An original `unittest.main(exit=False)` invocation can
complete without an original `SystemExit` payload.

The `adapter_sha256` context field identifies this evidence normalization
program. It is explicitly not an independent verification of the execution
adapter. Each execution receipt separately retains its actual producer's
`runner_sha256` and, for browser runs, the immutable harness snapshot. Context
measurements bind the official native artifact and the browser source artifact
to observed build/runtime configuration. They do not recover an unavailable
native CMake cache or prove independent source-to-binary reproduction.

Receipt producers remain a trust boundary. Hashes and internal consistency
checks establish which observations are being assessed; they do not independently
re-execute the machine that produced them.

## Case and subtest semantics

Case identity is `upstream_path::unittest_id`, removing only the `__main__.`
prefix. Imported class module names, parameter values, and complete subtest
descriptions are preserved. Repeated subtest identities are rejected because the
recorded evidence cannot distinguish those events one to one.

A nonpassing subtest can establish a derived nonpassing parent when upstream
unittest emits no parent success callback. Passing subtests alone never imply a
passing parent. Historical producer versions classified all failing subtests as
`failed`, including exceptions that unittest counted as `errors`. The converter
preserves that historical event label and the original failure/error counter
split; it does not silently rewrite old evidence. New producer versions distinguish
those categories. Contradictory callback and original unittest counter totals
block qualification.

The failure-detail fingerprint replaces only the observed temporary source-root
prefix. Assertion values, line numbers, exception text, and all other details
remain unchanged. Native/browser nonpassing outcomes must have matching details
to establish agreement. An expected failure can agree and still never count as
a successful functional test.

Every native subtest identity must also appear in the browser result. This catches
tests that silently omit format-specific subtests when a browser build disables
codecs: a passing parent with fewer subtests does not establish one-to-one
agreement. Missing and unexpected subtest IDs appear in `conversion.json`, and
their totals appear in `report.json`.

`validation_blockers` preserves an accurate process exit and actual callback
outcome when a required original-driver or host-tool observation is absent. The
paired ledger honors those blockers for both agreement and successful execution.
For example, a passing callback within a font invocation lacking the bound
`IDIFF_BIN` identity does not qualify the original image-comparison contract.

## Reading counts and limits

Observed callback counts, outcome agreement, and successful paired execution are
different quantities. A suite can record some passing parents and still exit
with a failure. Strict successful execution requires a successful whole-process
exit in both profiles, passing original criteria, matching complete subtests,
and no discovery or driver validation blocker.

`paired_obligation_count` distinguishes an identical source-qualified case under
different original invocations or input manifests. `known_case_count` counts
unique source-qualified identities. For example, the two font modes have some
shared case names but different original arguments; those are separate required
invocation/case obligations.

The selected source plan retains unresolved declarations, so this evidence cannot
close the declared scope until those obligations receive concrete configured
registrations and independent discovery. The converter always leaves
`all_upstream_test_parity` and `full_feature_parity` false. Passing all presently
known tests would still require a separate upstream coverage and feature
acceptance mechanism before either broader claim could be justified.
