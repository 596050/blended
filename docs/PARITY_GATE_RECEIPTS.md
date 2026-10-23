# Declared-contract gate receipts

`tools/parity_gate.py` checks whether the supplied inventory's obligations have
valid passing execution receipts for every required profile. Its successful
result is `declared_contract_satisfied: true`. `full_feature_parity` remains
`false` even when every declared obligation passes: this gate has no independent
mechanism for proving exhaustive test enumeration or complete feature acceptance.

The strict command returns zero for a satisfied declared contract, one for an
incomplete or non-passing contract, and two for malformed input. `--report-only`
returns zero for any valid report without changing the report's gate status.
Consumers must use `declared_contract_satisfied` when checking this command's
strict exit semantics. The current product inventory remains incomplete.

## Result record and supporting files

A results document retains schema 1 and the existing `target`, `context` and
`records` fields. It also supplies a nonempty `run_id`. A passing record must
reference one typed receipt using `receipt`; optional diagnostic files belong
in the separate `attachments` list:

```json
{
  "case_id": "upstream.mesh.extrude",
  "profile": "chromium-hardware",
  "status": "passed",
  "receipt": {
    "path": "receipts/mesh-extrude.json",
    "sha256": "<SHA-256 of the exact receipt bytes>"
  },
  "attachments": [
    {
      "path": "logs/mesh-extrude.log",
      "sha256": "<SHA-256 of the exact log bytes>"
    }
  ]
}
```

Hashes in this illustrative record must be replaced by 64 lowercase hexadecimal
characters. Files must be regular files beneath `--evidence-root`. Absolute,
non-canonical and parent-traversing paths, symlinks, hash mismatches, missing
files, and duplicate receipt or attachment paths are rejected. No attachment
is required. A log, a screenshot, or the former untyped `evidence` list cannot
substitute for a semantic receipt.

## Typed execution receipt

Every receipt is a UTF-8 JSON object, at most 1 MiB, with these required fields:

| Field | Required meaning |
| --- | --- |
| `schema` | Integer `1`, not a Boolean. |
| `type` | Exactly `blender-case-execution`. |
| `case_id` | Exactly the referring record's canonical case ID. |
| `profile` | Exactly the referring record's required runtime profile. |
| `run_id` | Exactly the enclosing results document's run ID. |
| `target` | Exact required Blender repository and full upstream commit. |
| `context` | All seven independently selected identity fields listed below. |
| `outcome` | Exactly `passed`. Skips, expected failures, missing runs and all other outcomes do not qualify as functional passes. |
| `execution.started` | Boolean `true`. |
| `execution.completed` | Boolean `true`. |
| `execution.exit_code` | Integer `0`, not Boolean `false`. |
| `execution.timed_out` | Boolean `false`. |
| `execution.crashed` | Boolean `false`. |
| `comparison.status` | Exactly `passed`, after applying the original test criteria. |
| `comparison.policy_sha256` | Exact independently selected comparison-policy digest. |

The context fields are `artifact_sha256`, `native_artifact_sha256`, `port_commit`,
`build_config_sha256`, `fixture_manifest_sha256`, `comparison_policy_sha256`,
and `suite_manifest_sha256`. The suite digest is the canonical JSON hash of the
supplied inventory, including its completeness declarations. A receipt cannot
change these identities merely by relabeling an outer result record.

JSON with duplicate field names or non-JSON values such as `NaN` is rejected.
The receipt's file hash is computed from the same bytes that are parsed. A
receipt from a prior run, another case, another profile, or another target does
not qualify. A pass emitted before a later process failure, crash or timeout
does not qualify. Producers must wait for the invocation to complete and record
its actual completion and exit status; they must not infer successful exit from
a partial pass marker.

## Scope and producer responsibilities

This schema binds and checks a producer's structured claims. It does not make
an untrusted producer trustworthy, re-execute Blender, independently re-run an
image comparator, or prove that a declared inventory is exhaustive. Producers
must preserve the upstream assertions, tolerances, fixture identities, invocation
semantics and failure outcomes. Raw evidence should remain available through
attachments and the broader execution ledger.

The denominator and facet completeness declarations remain reviewed inputs to
this gate. A separate enumeration process must reconcile runtime-expanded cases,
build configurations, source registrations and fixture closure before making an
exhaustive test claim. Additional browser interaction, hardware, persistence,
performance and recovery acceptance is necessary for feature claims. Matching
native and browser expected failures may establish outcome agreement in that
broader ledger, but they do not become functional passes here.
