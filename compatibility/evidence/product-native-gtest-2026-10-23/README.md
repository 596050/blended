# Original native GoogleTest checkpoint

This checkpoint contains **2,016 runtime case observations from the original pinned Blender sources: 2,015 passed and one called the original platform-specific `GTEST_SKIP`**. It covers 37 original CTest process invocations. Of these, 36 contain concrete runtime cases; `libmv_resect` contains zero cases and contributes zero passes. No browser cases were executed by this work, and no whole-application test denominator is claimed.

## Scope and exact inputs

The product source is Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`. The exact official source archive is `https://codeload.github.com/blender/blender/tar.gz/94363991e7dcf39e2d70614aa002ab6f67764a5d`, 80,900,636 bytes, SHA256 `e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`. This product pin is separate from the 5.2 browser candidate pin; native outcomes here do not transfer to that browser artifact.

The successful original configuration is bound by `../product-configure-2026-10-23/configure-with-optix.json`, SHA256 `930cfd1cfecd20f4e091cb1585224615d4b721370e8a4253eb34b9203c6cf508`. Its CMake cache SHA256 is `c5fe942acda64953fd24c9a14ac20fe0a6b1a9df8dcb7e4a875da1ea5364b121`. Every one of the 37 build receipts verifies that this cache was identical before and after compilation. GCC 14.2, the exact product native-library gitlink, isolated authenticated host dependencies, and official OptiX 8 headers are recorded in the configuration evidence. Existing product features and test options were preserved.

The original CMake targets were built with two compiler jobs. Their original [`testing_main.cc`](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/tests/gtests/testing/testing_main.cc) remains in the linked dependency closure, including guarded allocation, leak detection, failure on memory leaks, GoogleTest, gflags, and glog initialization. No replacement test main or assertion changes were introduced.

## Observations and outcomes

The registered and unfiltered runtime listings both contain 2,016 observations. The original XML reports 2,016 cases with `status="run"`, which includes the one test that enters its body and calls `GTEST_SKIP`. Of these, 2,015 complete without failure, error, or skip. There are zero failed, error, disabled, suppressed/not-run, or unknown observations in this selected set. These zeros describe the executed subset only.

All 32 LibMV invocations completed at exit zero, yielding **145 passing cases** across the 31 nonempty executables. A zero process exit for the remaining empty executable is not a passing test case.

| Original CTest name | Listed | XML status run | Passed | Skipped | Failed | Errors |
|---|---:|---:|---:|---:|---:|---:|
| `atomic` | 56 | 56 | 56 | 0 | 0 | 0 |
| `guardedalloc` | 6 | 6 | 6 | 0 | 0 | 0 |
| `BLI` | 1742 | 1742 | 1742 | 0 | 0 | 0 |
| `makesdna` | 5 | 5 | 5 | 0 | 0 | 0 |
| `shader_tool` | 62 | 62 | 61 | 1 | 0 | 0 |
| `libmv_array_nd` | 24 | 24 | 24 | 0 | 0 | 0 |
| `libmv_brute_region_tracker` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_camera_intrinsics` | 7 | 7 | 7 | 0 | 0 | 0 |
| `libmv_convolve` | 7 | 7 | 7 | 0 | 0 | 0 |
| `libmv_detect` | 2 | 2 | 2 | 0 | 0 | 0 |
| `libmv_dogleg` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_euclidean_resection` | 3 | 3 | 3 | 0 | 0 | 0 |
| `libmv_function_derivative` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_fundamental` | 6 | 6 | 6 | 0 | 0 | 0 |
| `libmv_homography` | 7 | 7 | 7 | 0 | 0 | 0 |
| `libmv_image` | 2 | 2 | 2 | 0 | 0 | 0 |
| `libmv_intersect` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_keyframe_selection` | 6 | 6 | 6 | 0 | 0 | 0 |
| `libmv_klt_region_tracker` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_levenberg_marquardt` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_modal_solver` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_numeric` | 29 | 29 | 29 | 0 | 0 | 0 |
| `libmv_nviewtriangulation` | 2 | 2 | 2 | 0 | 0 | 0 |
| `libmv_panography` | 4 | 4 | 4 | 0 | 0 | 0 |
| `libmv_parallel_for` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_poly` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_predict_tracks` | 6 | 6 | 6 | 0 | 0 | 0 |
| `libmv_projection` | 4 | 4 | 4 | 0 | 0 | 0 |
| `libmv_pyramid_region_tracker` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_resect` | 0 | 0 | 0 | 0 | 0 | 0 |
| `libmv_resection` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_sample` | 4 | 4 | 4 | 0 | 0 | 0 |
| `libmv_scoped_ptr` | 5 | 5 | 5 | 0 | 0 | 0 |
| `libmv_tracks` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_triangulation` | 1 | 1 | 1 | 0 | 0 | 0 |
| `libmv_tuple` | 4 | 4 | 4 | 0 | 0 | 0 |
| `libmv_vector` | 10 | 10 | 10 | 0 | 0 | 0 |
| **Total** | **2,016** | **2,016** | **2,015** | **1** | **0** | **0** |

The single skip is `shader_tool.MatrixConstructors`. The original declaration is at `source/blender/gpu/shader_tool/tests/syntax_test.cc:130`; its non-Apple branch calls `GTEST_SKIP` at line 133. This remains a skip requiring the relevant platform coverage, not a pass or a global exemption.

The original `intern/libmv/libmv/simple_pipeline/resect_test.cc` encloses its test declarations in `#if 0`. Both actual runtime listings are empty, and original XML reports zero tests. `libmv_resect/registered-gtest-inventory.json` and its unfiltered counterpart retain `empty_runtime_listing`; `summary.json` carries that blocker and an explicit `parity_qualified: false` classification. The source explains this result without converting it into coverage.

## Original invocation and identity preservation

Each capture retains the actual configured CTest registration, full original argument vector, working directory, environment properties, labels, fixture properties, and original process return code. The execution uses CTest itself to launch that exact registration. `GTEST_OUTPUT=xml:<fresh path>` is the only added test reporting environment setting; inherited `GTEST_*` settings are cleared and recorded. Listing discovery runs are separate from execution and preserve the original registered filter. A second unfiltered listing exposes any additional cases in the same binary.

Raw standard output, standard error, GoogleTest XML, CTest JUnit XML, executable identity, generated build/link rules, build logs, and configuration identities are retained per invocation. The bounded capture recipe is `../product-configure-2026-10-23/capture-native-gtest.py`; each capture has a 600-second CTest test timeout and an outer process-group timeout. The LibMV batch receipt is `libmv-capture-batch.json`.

`source-qualified-observations.json` binds every outcome to the original source commit, declaration file, full file SHA256, line number, and runtime case name. The consolidation independently checks each declaration file against the exact original archive and the current source tree. All 2,016 source-qualified case IDs are distinct. Neither listing order nor a bare GoogleTest name is used as the permanent identity.

Two repeated names required explicit source disambiguation:

| Runtime name | First original declaration | Second original declaration |
|---|---|---|
| `stack.Peek` | `source/blender/blenlib/tests/BLI_stack_cxx_test.cc:172` | `source/blender/blenlib/tests/BLI_stack_test.cc:97` |
| `KltRegionTracker.Track` | `intern/libmv/libmv/tracking/brute_region_tracker_test.cc:29` | `intern/libmv/libmv/tracking/klt_region_tracker_test.cc:28` |

The earlier BLI adapter failure is preserved under `BLI/`; it executed zero cases. The subsequent original execution is under `BLI-source-identities/` and contains all 1,742 original cases. The production inventory fix preserves ambiguous duplicate-name listing observations until original XML provides their independently verified declaration locations. Its focused red/green evidence is in `../registration-inventory-duplicate-names-2026-10-23/`.

The earlier atomic and guarded-allocation raw receipts predate the source-qualified helper fields. Their immutable original XML already records declaration locations. The consolidated observations verify and add canonical identities in a separate derived artifact; those original receipts were not rewritten.

An independent review of BLI and the first four ancillary targets is in `../product-native-independent-review-2026-10-23/report.json`, SHA256 `7ff1aa55c0f57eba41bd7166e22602c74cf75c6427c51bc1b177f90ac7b1d192`. A separate LibMV audit may be present alongside this checkpoint; neither audit re-executes cases or contributes additional passes.

## Configuration and fixture limits

The original base profile has 1,140 actual CTest registrations, captured in `../product-ctest-configured-2026-10-23/`. A separate broader profile has 1,416, captured in `../product-expanded-config-2026-10-23/`. They share 1,139 names; the broader profile adds 277 and replaces the base-only `cycles_osl_cpu` naming according to original CMake. The latter profile enables seven additional existing test options, including Vulkan render/Storm, mesh paint, expanded OSL, experimental, Linux release, and system-Python tests. These are registration observations, not concrete leaf-case denominators or hardware execution results.

The source and configuration reconciliation obligations remain open. Other operating systems, graphics backends, optional features, test filters, and runtime-expanded Python/GoogleTest cases still need explicit coverage. A configured list alone cannot demonstrate that all original tests have been enumerated.

The pinned fixture hydration receipt `../product-fixture-hydration-2026-10-23/report.json` verifies 7,353 selected source paths, including every original `tests/files` entry and 24 outside-root `.blend` candidates. It is SHA256 `55fd3f2bba7150cf73055d1f44b3f4c391694214d8b06f8a2c207b5b03d891ad`. That candidate set is not an assertion of complete runtime dependency closure. General release assets, runtime packaging, hardware, processes and other dependencies must still be verified when their tests are reached.

## Remaining build assessment

`remaining-build-assessment.json` snapshots the generated dependency graph, every referenced generated build rule and link command, present object files, and free resources. At capture, 423 object files occupied 52,249,912 logical bytes; all 37 completed target builds took 823.45 seconds in total with two compiler jobs. The current build tree occupied 258,887,922 logical bytes. Free disk was 17,403,846,656 bytes (about 16.2 GiB), and the cgroup limits were 8 GiB RAM and eight CPU equivalents.

| Target | Dependency targets | Configured object rules | Already built | Remaining | Proposed jobs | Planning time | Additional disk budget |
|---|---:|---:|---:|---:|---:|---|---|
| `cycles_test` | 24 | 219 | 35 | 184 | 1 | 20-90 minutes | 2-4 GiB |
| `blender_test` | 208 | 5,058 | 245 | 4,813 | 2 | 2-6 hours | 4-10 GiB |
| `blender` | 176 | 4,902 | 230 | 4,672 | 2 | 2-6 hours | 4-10 GiB |

These are low-confidence planning ranges, not measured build requirements or completion promises. The simple small-target wall-time proxy is about 6 minutes for the remaining Cycles objects and 2.6 hours for the remaining `blender_test` objects at two jobs. The planning range allows for heavier Cycles kernels, templates, generated assets and linking. A single translation unit or final link may exceed the available memory. The targets share much of their dependency closure, so these ranges should not be added as independent costs.

The exact proposed commands and required environment overrides are in the assessment. The first suggested stage is the unchanged `cycles_test` target with one compiler job, an initial 20-minute bound, and a 4 GiB free-disk reserve. The full `blender` runtime will additionally need packaging and asset verification before its Python, rendering and UI tests can be qualified. **No Cycles, full `blender_test`, or full `blender` build was started at this checkpoint.**

## Verification and recovery

`summary.json` is the stable consolidated index; `source-qualified-observations.json` contains the complete observed case list. The derivation script `../product-configure-2026-10-23/summarize-native-gtests.py` verifies the bound raw file hashes, exact binary and cache identities, original XML outcomes and counters, registered-listing name multiplicities, and pinned declaration contents before producing the summary. It refuses to overwrite an existing summary. Build and execution recipes likewise preserve existing attempts; use a fresh attempt name or directory for later runs.

All native outcomes are separate from the browser parity ledger. `browser_cases_executed` is zero, and `browser_parity`, `runtime_enumeration_complete`, and `all_upstream_tests_enumerated` remain false.
