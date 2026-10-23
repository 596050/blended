# Original mesh test ledgers

`tools/reconcile_original_mesh.py` makes the retained original bevel and mesh
operator captures independently replayable through the strict parity ledger.
It executes no Blender tests. Its two profiles use the earlier measured
Essentials package, the original native 5.2 reference, and their captured
Chromium launcher. They remain separate from the 829-obligation unittest
ledger and from every newer source-built package.

## Current recorded results

| Original registration | Native runtime obligations | Native passes | Browser observed passes | Browser observed failures | Strict successful pairs |
|---|---:|---:|---:|---:|---:|
| `bmesh_bevel` | 88 | 88 | 88 | 0 | 88 |
| `operators` | 105 | 105 | 103 | 2 | 0 |

The [bevel report](../compatibility/evidence/original-mesh-consumer-validation-2026-10-23/attempt-01/bmesh-bevel-5.2/report.json)
qualifies its complete selected invocation. The
[operators report](../compatibility/evidence/original-mesh-consumer-validation-2026-10-23/attempt-01/operators-5.2/report.json)
retains all 105 obligations and the two original topology failures. Its 103
matching terminal outcomes are diagnostic observations: the original Wasm
process and capture process exit with code 1, so the whole invocation does
not qualify. Neither original failure is an expected failure.

Passing this selected scope does not establish configured CTest execution,
the port's original UI shell, GPU equivalence, another browser or engine
profile, complete upstream test parity, or full application parity.

## Identity and acceptance rules

The successful native runtime supplies the case denominator. Source inspection
verifies each already observed case's original source path, name, line and
specification hash. A static declaration alone never becomes an executed case.

| Boundary | Required evidence |
|---|---|
| Upstream identity | Pinned Blender commit, original CMake declaration and unchanged driver/helper source bytes. |
| Inputs | Exact original fixture payload and its LFS pointer, with source and fixture bytes unchanged across capture. |
| Native invocation | Complete original `--run-all-tests` command, recorded working directory, unchanged selected environment, actual successful native process. |
| Browser artifact | Exact historical archive, individual engine members, source-build receipt, configuration, native executable and Chrome identities. |
| Original oracle | The unchanged mesh helper's `PASSED` marker, `Mesh Comparison : Same` and `Mesh Validation : Valid` for each passing case. |
| Startup | One automatic application main, zero manual main calls, original full argument vector and exact mounted input bytes before main. |
| Environment | `BLENDER_TEST_UPDATE` and `BLENDER_VERBOSE` absent by key presence; an empty or zero-valued key is still forbidden. |
| Completion | All original case results precede the original quit message; immediate input-byte readback precedes exactly one actual final Wasm exit. |
| Process gate | Successful Wasm, Chromium and capture process exits, with no timeout, abort, forced termination or recorded capture error. |
| Preservation | Hash-bound original logs, console events, launcher state, producer bytes, selected contexts and normalization source closure. |

The original `--run-test` debugging path disables mesh comparison and cannot
replace `--run-all-tests`. The file-preservation observer reads at the original
`Blender quit` output boundary while the filesystem is still available. A
browser process exit cannot substitute for an observed Wasm runtime exit.

Malformed or contradictory evidence is rejected. Valid failed or incomplete
execution preserves its obligations and observations with qualification
blockers. The original helper and fixtures are never executed or modified by
this consumer.

## Replaying one profile

Run from the repository root and choose an output directory that does not
already exist. The consumer refuses to overwrite earlier evidence.

```bash
python3 tools/reconcile_original_mesh.py \
  --repo-root . \
  --profile compatibility/mesh-driver-profiles/bmesh-bevel-5.2.json \
  --output /tmp/blended-original-bevel-ledger
```

The bevel consumer returns 0. Substitute the `operators-5.2.json` selector and
a different output directory to inspect the operators scope; its strict
consumer exit is 1. Exit 2 means malformed or mismatched evidence.

For report-producing CI steps, `--report-only` returns 0 for valid blocked
evidence while leaving every blocked gate and original outcome unchanged.
The following independent command then enforces the strict generated contract:

```bash
python3 tools/test_parity_ledger.py \
  --contract /tmp/blended-original-bevel-ledger/contract.json \
  --inventory /tmp/blended-original-bevel-ledger/inventory.json \
  --executions /tmp/blended-original-bevel-ledger/executions.json \
  --evidence-root /tmp/blended-original-bevel-ledger \
  --output /tmp/blended-original-bevel-strict.json
```

The [CI workflow](../.github/workflows/test-parity-ledger.yml) runs both exact
selectors in separate jobs, preserves output after failed gates, and never
adds these observations to a different artifact profile or test denominator.

## Validation and limits

The [captured validation](../compatibility/evidence/original-mesh-consumer-validation-2026-10-23/attempt-01/execution.json)
ran 58 evidence-consumer regressions successfully, then executed each profile's
consumer and the unchanged independent strict ledger. It preserved all 13
implementation, selector and plan inputs and reverified all 95 consumed
historical paths.

The adversarial checks cover altered original commands and environment,
changed source/fixture bytes, incomplete or duplicate cases, missing or repeated
exits, boolean values masquerading as integer exits, inconsistent console and
state streams, changed runtime profiles, unconfined paths and substituted
historical producer files.

The retained measurements remain producer observations. This replay does not
redownload the original runtime binaries, independently rebuild their source,
rerun the original cases or authenticate runtime behavior beyond the captured
evidence. These limitations are recorded in every conversion bundle.
