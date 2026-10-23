# Independent LibMV and combined native evidence review

**Verified: 145 original GoogleTest passes across 32 LibMV CTest invocations.**
The combined selected native evidence contains **2,016 distinct source-qualified
observations: 2,015 passes and one original skip**, across 37 CTest invocations.
The separately measured system-Python driver contributes no GoogleTest cases.

| Scope | Original CTest invocations | GoogleTest observations | Passes | Skips |
| --- | ---: | ---: | ---: | ---: |
| Previously reviewed BLI, atomic, guardedalloc, makesdna, shader tool | 5 | 1,871 | 1,870 | 1 |
| New LibMV captures | 32 | 145 | 145 | 0 |
| Combined selected native evidence | 37 | 2,016 | 2,015 | 1 |

All 37 CTest processes completed with exit 0. One LibMV invocation contains zero
runtime cases, so there are 36 nonempty invocations. A successful empty driver
contributes zero case passes.

## Evidence reconciliation

The standard-library verifier independently re-read all 37 original GoogleTest
XML reports, registered and unfiltered listings, actual CTest logs, preserved
CTest registrations, binary/build receipts, generated build rules, and source
bindings. It imported no production inventory or summary adapter and executed
no compiler, original test binary, CTest, or production tests.

For every invocation, original XML names and multiplicities match both runtime
listings and the original run/pass log callbacks. Registered and unfiltered
listing bytes match. Every summary observation and outcome exactly matches the
original XML. All 2,016 source-qualified IDs were independently recomputed from
the pinned commit, original source-file path and hash, reported declaration line,
and test name. No source-qualified identity is counted twice.

The native summary and case-list files are unchanged:

- `../product-native-gtest-2026-10-23/summary.json`, SHA256
  `49fa3a4710cd5e192044c0aed8a50ea1460761caeb04909e2be30b987ba6f492`.
- `../product-native-gtest-2026-10-23/source-qualified-observations.json`, SHA256
  `59f7d27a5edffbf4602e54d242967816dbe984e0cfa6d44ecd0e92be93c30268`.

## Zero-case resect invocation

`libmv_resect` has zero cases in both runtime listings and its original XML.
The actual CTest log explicitly reports zero tests run and zero test passes.
Its pinned source file,
`intern/libmv/libmv/simple_pipeline/resect_test.cc`, is byte-identical to the
original commit archive. An original outer `#if 0` at line 25 ends at line 234;
all three test declarations at lines 67, 101, and 170 are inside that disabled
block. The nested disabled block at lines 156-166 is also preserved.

The summary retains `empty_runtime_listing`, its discovery blocker, zero native
case passes, and `parity_qualified: false`. These disabled source declarations
have not been invented as runtime outcomes, skips, or passing tests.

## Equal tracker names remain distinct source cases

| Original display name | Original declaration | Native invocation |
| --- | --- | --- |
| KltRegionTracker.Track | `intern/libmv/libmv/tracking/brute_region_tracker_test.cc:29` | libmv_brute_region_tracker |
| KltRegionTracker.Track | `intern/libmv/libmv/tracking/klt_region_tracker_test.cc:28` | libmv_klt_region_tracker |

Both original lines declare `TEST(KltRegionTracker, Track)`. Each XML source
location was verified against the pinned archive, and each produced its own
source-qualified ID. Their shared display name does not merge their outcomes.
The previously verified two `stack.Peek` cases also remain distinct. The only
skip in the aggregate remains the original non-Apple
`shader_tool.MatrixConstructors` skip.

## Scope and artifacts

This is one selected Linux Release configuration of source commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d`. It does not establish the full Blender
test denominator, another platform or configuration, or any browser pass.
All reviewed completeness and browser-parity flags remain false. The review
adds no execution outcomes and modifies no earlier receipts or original source.

- `audit.py`: reproducible evidence-only verifier, refusing to overwrite its report.
- `report.json`: per-invocation reconciliation, exact checked input hashes,
  original source hashes, zero-case source guards, tracker identities, and totals.

The verifier completed with exit 0. The report is 212,296 bytes with SHA256
`9fe5f5c6a8ebeda2f99d313a87a50501fedbd73ffc7097e7539340613bb61388`.
Reproduction requires the preserved evidence, exact source archive, and native
runtime artifacts. Run a copied review directory to retain this report.
