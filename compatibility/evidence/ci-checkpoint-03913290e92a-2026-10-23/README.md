# Checkpoint 03913290e92a: publication and CI evidence

This capture covers checkpoint `03913290e92a98cd9c45fdecf679072587c4dbe7`, tree `a3fbe996e97c8e872ca4d94a1c0f7283e9cb86ad`, with sole parent `9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c`.

It preserves both publication attempts and [ledger run 40008805411](https://github.com/596050/blended/actions/runs/40008805411). The source build is tracked separately. No Blender test credit is added by publication verification or evidence replay.

## Observed CI results

| Job | Normalizer exit | Strict gate exit | Result |
| --- | ---: | ---: | --- |
| Base profile | 0 | 1 | 512 successful execution pairs, 597 outcome agreements; blocked |
| Essentials profile | 0 | 1 | 516 successful execution pairs, 601 outcome agreements; blocked |
| Source build with codecs and SQLite | 2 | Not run | Normalizer rejected a current-root path collision; no CI report |
| Infrastructure regressions | Not applicable | Not applicable | 383 tests, `OK`, 162.436 seconds; exit 0 |

The base and Essentials artifacts contain all 829 case pairs and all 132 registration records. Each pair and registration equals its frozen repository reference. Every report field matches except `contract_sha256` and `inventory_sha256`, whose identities incorporate newer normalizer provenance. The normalizer report adds four observation fields to the strict report; all shared fields agree.

The infrastructure count and successful outcome match the separately captured local 383-test run. This is infrastructure validation, with zero original Blender test credit.

### Source-profile replay failure

The source normalizer logged:

`exact evidence map cannot shadow a current repository path`

Its actual exit code was 2, and GitHub skipped the strict-gate step. The uploaded artifact contains only the exact captured path-map file. It contains no report, contract, inventory, or execution ledger. The prior frozen source profile remains 528 successful pairs and 536 agreements, but those figures are not substituted for this absent CI result.

The preserved workflow checked out the repository at `/home/runner/work/blended/blended`, the same root used by the original historical CI producer. Historical absolute paths therefore fell under the current root and were rejected by the unchanged shadowing guard. This is a replay-placement failure, separate from original Blender execution failures. The exact checkpoint workflow and normalizer source are retained under `inputs/checkpoint/`.

A subsequent workflow-only checkout relocation is captured, if available, in the separate `follow-up-32d488161133/` directory. The initial failure here remains unchanged.

## Publication attempts

[Publication run 40008313085](https://github.com/596050/blended/actions/runs/40008313085) has two preserved attempts.

The first attempt passed bundle, commit, tree, sole-parent, ancestry, Git object, ledger, and LFS checks. The LFS upload returned 0. GitHub then rejected the branch push because the workflow token lacked `workflows` permission for the workflow-file change. The push returned 1, and the verified branch remained at `9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c`. Its failed receipt and all 38 artifact members are preserved.

The authorized connected-account publication subsequently fast-forwarded the exact verified object and parity branch. The copied publication observation records that operation and the unchanged independent `main` ref.

The second CI attempt completed successfully. Its receipt records the target commit before and after verification. All 16 commands returned 0, and it attempted neither a branch push nor an LFS upload because the exact target already existed. Its `published: true` status describes verification of that existing target, not a new push during the rerun. All 33 artifact members are preserved.

## Exact downloaded artifact identities

Each ZIP's byte count and SHA256 matched GitHub's reported values. Every member was checked for a unique canonical regular-file name, fully read with CRC validation, and preserved with byte-count and SHA256 identities.

| Artifact | ID | ZIP bytes | SHA256 |
| --- | ---: | ---: | --- |
| Publication attempt 1 | 12524803345 | 27,328 | `eb6cf6855fa35d7c51a0e9c62c36eec9fee1ad278e2d039a668b81a0902d5601` |
| Publication attempt 2 | 12526010099 | 25,631 | `637082111f1104544e693259a28598d933511ee9ea8c895bc8c24d8e90772fbe` |
| Base ledger | 12525630992 | 3,857,156 | `7e318238888b3d4f71bbf5a072b6871c69ca2a6dcd2c4470d110f29ae00cf8f5` |
| Essentials ledger | 12524893261 | 3,950,834 | `7cd975e8b133e3e2d10684e838f2aff2c3f4fe17e07f923e41cfb626d6f2033b` |
| Failed source-profile replay | 12525471626 | 41,434 | `a559573404962a01a79d940c11c486c4ce72a0286cc9d1550f79ef14bcc47be0` |

The 1,714 extracted artifact members retain their original bytes. API metadata and connector-decoded job logs are preserved separately. Public API responses include both publication attempts and the completed run states.

## Audit files

- `analysis.json` contains the actual status and report comparisons.
- `compare_ci.py` implements the case, registration, metadata, and publication-receipt comparisons.
- `download-receipts.json` and `publication/attempt-01/preservation.json` inventory downloaded ZIPs and every retained member.
- `capture_api.py` and `api-capture.json` record the completed primary API observations.
- `checkpoint-source-inputs.json` binds the exact checkpoint workflow and normalizer sources.
- `publication/copied-inputs.json` identifies the copied original publication inputs and connected-account observation.

`file-inventory.json` freezes the explicit files of this initial capture. Any follow-up directory has its own inventory and does not alter these initial files. `all_upstream_test_parity` and `full_feature_parity` remain false.
