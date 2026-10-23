# Parity evidence recovery

This directory records new recovery and verification work after workspace maintenance removed the local checkout and uncommitted files. It does not recreate historical execution receipts and does not claim new Blender test executions.

## Exact recovered identities

The published checkout was restored at commit `9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c`. Temporary normalizer outputs survived outside that checkout. Two separately retained outputs of the source-build profile contained the same 858 files, with zero byte differences.

| Item | Bytes | SHA256 |
| --- | ---: | --- |
| Recovered normalizer | 83,881 | `6675c3f1604ef92f3aa139e0d0cc9a91f0a59487b46e0cb5f9685676cd5caa5c` |
| Recovered source-build report | 780,486 | `913a5f430f2ea9df35ec2878240a3c3b3b6783062c733a2e9a6f58d3b6c21b0b` |
| Original exact path map | 319,425 | `49f721772bf1022dea2b74c083e0f2406f4e099220c1b285af929a9ddeff125e` |
| Fresh source normalizer execution receipt | 202,917 | `4c52930edae24ef015e24f71c489010e1c80c640cac9066a15d11a1347a49edd` |

The normalizer source is restored at `tools/reconcile_unittest_matrix.py`. The 858-file profile is restored at `compatibility/evidence/unittest-parity-ledger-source-build-39986612484`.

`recovery-manifest.json` records exact copies from retained files, with source paths and SHA256 values. It covers 866 original-path snapshots and all three retained replay profiles. Its initial count of 52 missing path-map entries describes that recovery stage, before the subsequent CI artifact completion step.

`restoration.json` records the initial repository restoration. All 535 pre-existing copied files matched the published Git blob identities. The only changed pre-existing source was the exact recovered newer normalizer. The restoration added 1,560 evidence files. It did not modify original Blender tests or expected outcomes.

## Complete CI artifact closure

`ci-artifact-file-recovery.json` records the next step. Every one of the 730 original path-map entries was checked against re-downloaded artifact members from run `39986612484`: 260 main members and 470 resource members. The first 678 matched files recovered from temporary normalizer snapshots. The remaining 52 were restored from the exact artifact members. This includes the screenshot, bytecode, log, and JSON files absent from the initial snapshots.

The path-map file is unchanged. Its original absolute paths, exact repository targets, byte counts, and SHA256 values are preserved. Artifact restoration adds no test credit.

## Fresh verification after recovery

`fresh-source-normalization-execution.json` records actual new commands over the recovered evidence:

- The normalizer returned 0 with `--report-only`.
- The strict ledger returned 1 with `gate: blocked`.
- All 858 generated files were byte-identical to the retained source profile.
- The nine observed normalizer source and configuration files were unchanged before and after execution.
- Every shared field between the normalizer report and strict report agreed. The normalizer adds four diagnostic observation fields.

The actual source-build observations remain 829 native obligations and 749 browser terminal outcomes. The browser outcomes comprise 539 passes, 207 assertion failures, two errors, and one original expected failure. There are 80 missing browser outcomes and 57 missing browser subtest observations. These callback totals are different from complete successful execution pairs.

`recovery-validation.json` separately records new strict-ledger evaluations for all three retained profiles. Each output was byte-identical to its retained strict report:

| Profile | Successful execution pairs | Outcome agreements | Strict exit | Gate |
| --- | ---: | ---: | ---: | --- |
| Base | 512 | 597 | 1 | blocked |
| Essentials | 516 | 601 | 1 | blocked |
| Source build with codecs and SQLite | 528 | 536 | 1 | blocked |

The 528 successful pairs belong only to the source-build profile. Results from other profiles are not combined to fill its missing observations. The source profile still has 101 unresolved source declarations.

## Material losses and limits

The earlier 369-test infrastructure execution receipt and the exact source of the 23 newer infrastructure regressions were not found in the retained temporary directories. This recovery does not synthesize either file. Any reconstructed regressions and subsequent infrastructure test execution require their own new source identities and capture.

DPX diagnostic execution receipts, curve execution receipts, and independent review notes are outside this recovery. Their earlier observations must not be represented as recovered evidence solely from conversational summaries.

The recovery and verification receipts here have new execution identities. Their timestamps are the UTC values observed by the Python process during recovery. Commands and source paths retain their actual captured values. `all_upstream_test_parity` and `full_feature_parity` remain false.
