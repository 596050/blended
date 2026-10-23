# Recovered source build: run 39986612484

This directory preserves 153 exact original files from the successful source-build artifact for [GitHub Actions run 39986612484](https://github.com/596050/blended/actions/runs/39986612484). The files were recovered after workspace maintenance. The original build receipt and stage logs are unchanged. `recovery.json`, `artifact-members.json`, and `summary.json` are newly created recovery records.

## What the original build established

The [original source-build receipt](build/source-build.json) records a successful development build of checkout `f25e69ed72fed2d31d7d65e657fd6515da4bd792`, using port commit `0e02e84b2bc5d9b27a6dc6e275443292f781fbad` and Blender source commit `fbe6228777e7d9afefcd61a413844e790ae75db7`.

| Observation | Original recorded result |
| --- | --- |
| Total duration | 2,771.476395 seconds, approximately 46 minutes 11 seconds |
| Build stages | 132 passed, all with exit code 0 |
| Engine compilation | 1,645.898 seconds with two jobs |
| OpenImageIO dependency stage | 221.007 seconds |
| SQLite dependency stage | 22.115 seconds |
| Python dependency stage | 349.593 seconds |
| Packaging mode | `OFF` development build with build metadata enabled |
| Image feature configuration | CINEON, OPENJPEG, and WEBP enabled |
| Original Blender tests within the build receipt | `tests_executed: false` |

The receipt retains the original build timestamps in explicit UTC. Recovery timestamps are recorded separately in [recovery.json](recovery.json). The original build reports `deployed: false`, `shipping_profile: false`, `hardware_verified: false`, and `bitwise_reproducibility_verified: false`.

The [cache reuse receipt](build/dependency-cache-reuse.json) reports verification of 4,103 existing regular files, totaling 391,934,030 bytes, and three required aliases derived from the pinned libpng source. Changed dependency recipes ran separately. The observed 46-minute duration includes this cache reuse.

The [new harvest manifest](build/dependency-harvest.jsonl) records 4,184 distinct file identities. Recovery checked and preserved the manifest bytes. The dependency payloads described by that manifest are outside this evidence copy, so recovery does not claim a new verification of all 4,184 payloads.

## Exact artifact recovery

The source artifact is `browser-source-development-39986612484`, artifact ID `12518531963`. Its complete ZIP is 222,636,519 bytes, SHA256:

`c19e2f15d1d5bf07dd5bd80b72a0a7514c71cb4884bc50ca576f4562ba85878f`

The capture script independently checked that ZIP identity, all 155 unique canonical regular-file names, full member CRC reads, and every extracted member's byte count and SHA256. All 153 preserved files were checked again after copying. Every one of the 132 stage-log identities matched the original source-build receipt.

The exact original source-build receipt is 172,975 bytes, SHA256:

`44bdb061bcd22a7a2b7756e93fe406a9eabfd2dd9e9f8fd4b63947ff31e2503f`

[artifact-members.json](artifact-members.json) inventories all 155 members. Only the two generated engine archives are excluded from the repository evidence copy. Their complete bytes were hashed during recovery and matched their original receipts. They remain separately identifiable runtime artifacts:

| Archive | Bytes | SHA256 |
| --- | ---: | --- |
| `blender-source-development.tar.gz` | 109,564,486 | `0d51a33313902a0331df02d900fc5776fd0855e8b0f2062b46cf0150d859499a` |
| `essentials/blender-source-development-essentials.tar.gz` | 112,253,979 | `c2105e12ae93e1804f82f3f49fdec3e0185ce2dd7fe9f26e97f4d3b44308df3c` |

The [Essentials overlay receipt](build/essentials/package-overlay.json) records resource augmentation, `engine_recompiled: false`, and zero tests executed during assembly.

## Separate original test results

The later qualification jobs have their own original observations and [recovered normalized report](../unittest-parity-ledger-source-build-39986612484/report.json). Recovery of that report and a fresh normalizer evaluation are recorded in [parity-recovery-2026-10-23](../parity-recovery-2026-10-23/README.md).

The bounded source profile contains 31 selected invocations, 829 obligations, and 827 distinct case IDs. It reports:

| Measure | Native | Browser |
| --- | ---: | ---: |
| Observed terminal outcomes | 829 | 749 |
| Passes | 828 | 539 |
| Assertion failures | 0 | 207 |
| Errors | 0 | 2 |
| Original expected failures | 1 | 1 |
| Missing outcomes | 0 | 80 |

The strict result is **528 successful execution pairs and 536 outcome agreements**. There are 57 missing browser subtest observations, no unexpected browser subtests, and 101 unresolved source declarations. The gate remains **blocked**. Callback pass counts do not establish complete successful execution pairs, and results from other engine profiles do not fill missing observations in this profile.

`all_upstream_test_parity` and `full_feature_parity` remain false.

## DPX correction boundary

This artifact used codec manifest SHA256 `b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708`. It predates the proposed signed-size DPX correction. None of the build or qualification results here establish that the new correction has been built or passed original Blender tests. That correction requires its own source build and original test execution.

## Reproduction and loss accounting

[capture_recovery.py](capture_recovery.py) contains the expected original ZIP, source-build receipt, and engine archive identities. It accepts the verified ZIP, extracted artifact directory, recovered parity report and conversion, and a new output directory. It refuses an existing output `build` directory to avoid overwriting evidence.

This recovery does not recreate the lost earlier build summary or freeze manifest. Its new summary is derived directly from the preserved original receipt and logs. It does not add original test credit or imply new build execution.
