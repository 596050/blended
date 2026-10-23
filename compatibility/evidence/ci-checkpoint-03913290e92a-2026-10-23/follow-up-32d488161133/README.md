# Workflow relocation follow-up: 32d488161133

[Ledger run 40009788126](https://github.com/596050/blended/actions/runs/40009788126) ran commit `32d488161133c5721e8379531b18af65a86e6624`, tree `45c4e8b119149315215a48b7d39fdcd99e48ff34`, with sole parent `03913290e92a98cd9c45fdecf679072587c4dbe7`.

The only changed file is `.github/workflows/test-parity-ledger.yml`. The original-test parity job now checks out and runs within `parity-evidence-checkout`, and its artifact upload path follows that directory. The infrastructure job, normalizer, strict ledger, and historical path map are unchanged. All 730 historical original paths are outside the configured new checkout root.

## Actual completed results

| Profile | Normalizer exit | Strict gate exit | Successful execution pairs | Outcome agreements |
| --- | ---: | ---: | ---: | ---: |
| Base | 0 | 1 | 512 | 597 |
| Essentials | 0 | 1 | 516 | 601 |
| Source build with codecs and SQLite | 0 | 1 | 528 | 536 |

All three normalizers completed successfully. Every strict parity gate remains blocked, so GitHub correctly reports the overall workflow conclusion as failure. The initial current-root collision failure is preserved separately in the parent directory.

The infrastructure job completed successfully: **383 tests in 93.848 seconds, `OK`, exit 0**. The test count and successful result match both the local checkpoint capture and the initial checkpoint CI run.

## Exact output comparisons

The base artifact contains 818 members and the Essentials artifact contains 824 members. Every member is byte-identical to its corresponding artifact from the initial checkpoint CI run. Every one of their 829 case pairs and 132 registration records equals its frozen repository reference. Only the contract and inventory identity fields differ from the older frozen reports, because those identities include normalizer provenance.

The source artifact contains all **858 files** of the frozen source-build profile, plus its new CI strict-gate report. Every one of those 858 files is byte-identical to the frozen profile. Its report remains 780,486 bytes with SHA256:

`913a5f430f2ea9df35ec2878240a3c3b3b6783062c733a2e9a6f58d3b6c21b0b`

The source profile retains 80 missing browser outcomes and 57 missing browser subtest observations. Its 528 successful pairs and 536 agreements describe the prior original observations reproduced by this evidence replay. They do not represent new Blender test executions.

For each profile, all shared fields in the normalizer and strict reports agree. The normalizer adds four diagnostic observation fields.

## Verified artifact identities

All three downloaded ZIPs matched the byte counts and SHA256 values reported by GitHub. All 2,501 members were fully read with CRC validation, checked for unique canonical regular-file names, and preserved exactly.

| Artifact | ID | ZIP bytes | SHA256 |
| --- | ---: | ---: | --- |
| Base | 12526006156 | 3,857,156 | `655c22acb2612c86f12d99d40885d04ad2cc92ca67df8f8907f0cc4a27021e9c` |
| Essentials | 12526355392 | 3,950,834 | `2863223ae4cfd8ccd070c79c625b0b01cc394dc344a08dcb0c347cdd7b77cab9` |
| Source build with codecs and SQLite | 12526365517 | 4,255,831 | `a134c3f8c2079155e0332244cd2200f653e6540808b1d37aad4eb29d67a75f0e` |

[download-receipts.json](download-receipts.json) identifies every preserved member. The unchanged download helper is retained in the parent capture. Signed download URLs are not included in this evidence.

## Audit and scope

[compare_followup.py](compare_followup.py) performs the complete file, case, registration, report, job-status, and infrastructure-summary comparisons. Its result is [analysis.json](analysis.json).

[input-capture.json](input-capture.json) binds the exact published workflow-only change and the unchanged normalizer, strict ledger, and original map. Original API responses, completed-job metadata, connector-decoded job logs, and the copied local relocation check are retained.

The original source-build run `40008805236` is tracked separately. This workflow-only follow-up does not establish results for a new engine or the DPX correction.

The initial capture's files remain unchanged. This directory has its own inventory. `all_upstream_test_parity` and `full_feature_parity` remain false, and new Blender test credit is zero.
