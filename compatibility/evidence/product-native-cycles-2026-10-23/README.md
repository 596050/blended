# Original native Cycles unit tests

The original `cycles_test` target built successfully and the unchanged original CTest invocation passed **216 cases**. A separate execution of the same original binary with `--gtest_filter=*` passed **242 cases**, including **26 cases omitted by the original configured CTest filter**. The 216 shared cases must be counted once.

These are native Linux observations for Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`. They are not browser passes, GPU rendering results, or a complete Blender test denominator. No original test, assertion, test entry point, CMake source, configured feature flag, or previous evidence file was changed.

## Execution scopes and retained failure

| Attempt | Listed cases | Executed cases | Passed | Failed | Skipped | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Initial original CTest attempt, `cycles/` | 0 | 0 | 0 | 0 | 0 | Loader failure before GoogleTest; `libImath.so.30` was unavailable |
| Original CTest after verified library staging, `cycles-runtime-libraries/` | 216 | 216 | 216 | 0 | 0 | Original registered command, working directory, filter, and environment properties; exit 0 |
| Supplementary whole binary, `cycles-unfiltered-supplementary/` | 242 | 242 | 242 | 0 | 0 | Original executable and arguments, with the framework filter changed explicitly to `*`; exit 0 |

Both successful listings have zero disabled cases. Their original GoogleTest XML matches the corresponding runtime listing exactly, including name multiplicities. Every observed case has an identity bound to the exact source commit, original declaration file hash, original source line, and complete runtime case name. The original CTest execution verifies 26 declaration files against the pinned source archive; the supplementary execution verifies 28.

The initial listing commands returned 127 and CTest returned 8. Its zero cases are a runtime prerequisite failure, not a successful empty test run. Its raw logs and receipt remain unchanged. The successful retry used the same executable hash and CMake cache.

## Build and configuration

The actual build command was:

```text
/workspace/scratch/d63596d831b2/runtime/browser-python/bin/cmake \
  --build /workspace/scratch/d63596d831b2/runtime/product-native-configure-optix \
  --target cycles_test --parallel 1
```

It returned 0 after **1,072.171867319 seconds**, within the initial 1,200-second bound. `build.json` preserves the exact command, environment, original configuration receipt, build rules, resource samples, and raw log identity. The resulting executable is 21,512,408 bytes with SHA256 `11ea54beed6f6fc365348bfe03118eece0f01fbf2d67310a6103f23529737c61`.

The original Release configuration, supported GCC 14 compiler, and current feature/test flags were preserved. CMake cache SHA256 remained `c5fe942acda64953fd24c9a14ac20fe0a6b1a9df8dcb7e4a875da1ea5364b121`. The original `tests/gtests/testing/testing_main.cc`, including its guarded allocator checks, was used and verified against the archive.

### Memory observation qualification

The existing kernel cgroup limit was 8 GiB. Time, free-disk, cgroup memory, non-file-memory, and OOM-event observations are retained. There were no OOM or OOM-kill events; sampled free disk during the build remained at least 13,771,886,592 bytes, above the 4 GiB reserve.

The first wrapper contained a process-namespace observation defect: it compared a namespace-local process ID with outer `/proc` process-group IDs. Its process-group RSS fields and associated RSS guard are **invalid** and must not be used as memory evidence. The raw script, receipt, and samples are preserved with this explicit qualification.

A separate read-only observer resolved the actual CMake process group using its original argv, parent, namespace IDs, and start time. Its 419 samples recorded a peak group RSS of 2,017,017,856 bytes over the remaining observation window. This is a sampled partial-duration peak, not a full-build maximum or an enforcement guard. Cgroup `memory.current` includes file cache and briefly sampled 110,592 bytes above the configured limit during reclaim; no OOM was reported. `procfs-memory-observation.json` and `summary.json` distinguish these observations.

## Verified runtime library packaging

The original configured CTest environment points to `product-native-configure-optix/bin/lib`, which was empty after building the target alone. The original creator install rules populate that directory with bundled shared libraries. An executable RUNPATH did not resolve the missing indirect Imath dependency in the first attempt.

`stage-runtime-libraries.py` extracted the single known shared-library block from the original generated creator install script. It verified its selected inputs against native library commit `2b5fbb917a1bf7537cb25456fcb9064302d7e168`, including exact original Git blobs, LFS OIDs and sizes, and symlink targets. It then used CMake's original `file(INSTALL)` operation at the configured normal destination.

The staged selection contains **53 regular files and 85 symlinks**, totaling **429,185,408 regular-file bytes**. All destination bytes and symlink targets were reverified. The generated glob also contained two untracked temporary files; their exclusion and identities are recorded. They were never represented as original upstream payloads. The source tree, test arguments, environment properties, executable, and configuration were not edited. This tracked subset of one install block is not a claim to complete application runtime dependency closure.

The full staging receipt, original generated block, verified input and destination manifests, exact install command, and stdout/stderr are under `runtime-library-staging/`.

## Why 26 original cases were absent from CTest

The original `build_files/cmake/Modules/GTest.cmake` reads the explicit source-file list and finds literal test declarations with a regular expression. The affected Cycles `.cpp` wrappers define `TEST_CATEGORY_NAME` and include the actual declaration headers. That scanner does not preprocess the includes or expand those macro-defined suite names.

| Additional runtime suite | Additional cases | Original declaration header |
| --- | ---: | --- |
| `util_half` | 7 | `intern/cycles/test/util_half_test.h` |
| `util_half_avx2` | 7 | `intern/cycles/test/util_half_test.h` |
| `util_avx2` | 12 | `intern/cycles/test/util_float8_test.h` |

`additional-case-reconciliation.json` retains all 26 exact source-qualified IDs and outcomes. `source-registration-reconciliation.json` binds the original registration scanner, source list, wrappers, declaration headers, CPU gating, and test entry point to the pinned archive. The native AVX2 configuration and original runtime CPU guards were preserved. The host observation records the available CPU flags; the original half-precision AVX2 tests reported passes rather than their original unsupported-CPU skip.

The supplementary receipt explicitly records the `*` filter change. It does not retroactively alter the original 216-case CTest receipt or its registration.

## Relation to the preceding native checkpoint

The earlier frozen native checkpoint contains 2,016 source-qualified observations, with 2,015 passes and one original skip. Its source IDs are disjoint from the new Cycles IDs.

- Including the **216 original registered Cycles cases** gives **2,232 distinct source identities: 2,231 passed and one skipped**, across 38 distinct original CTest registrations. The original empty `libmv_resect` invocation remains an explicit zero-case blocker.
- Including the **26 supplementary-only Cycles cases** gives **2,258 distinct source identities: 2,257 passed and one skipped**. These additional cases retain their supplementary invocation scope.

No browser or separate system-Python outcomes are added to those counts. Larger Blender test targets remain unbuilt. The read-only post-build assessment finds 4,658 missing generated object files for `blender_test` and 4,517 for `blender`; object counts are planning data, not test counts or proof that existing objects are current. No further build was started.

## Key receipt identities

| File | SHA256 |
| --- | --- |
| `summary.json` | `ffe16e95f8bfc76c6b287a7848bd82a8a0c4b8c52bfa68abee5f51cf1ab5a7a8` |
| `cycles-runtime-libraries/native-reference.json` | `381785ba1afd7a6296f89fc11c3ae490f2d6a17f6753f51d66c6f4c1243b55e9` |
| `cycles-unfiltered-supplementary/native-reference.json` | `115335612f547df4da69b41d5f08cd2ff113886fc50ea1b6e75f923565632f87` |
| `additional-case-reconciliation.json` | `676ed61c4c66d35481c6c9199a8c70738e604701ae6935e1f71af54614b9bbfd` |
| `runtime-library-staging/report.json` | `d742380e45f5da9232e53c60bb5d6ea2436285133914f9ad6d1acb6afbbbe9f8` |

The exact product source archive is bound throughout by SHA256 `e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`. Its official source URL is <https://codeload.github.com/blender/blender/tar.gz/94363991e7dcf39e2d70614aa002ab6f67764a5d>. Required configuration variants, remaining executable expansion, whole-application behavior, actual rendering devices, and browser counterparts remain separate obligations.
