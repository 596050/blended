# Actual product CTest registrations

The exact product source, Blender commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d`, successfully configured with the
original requested GTest, GPU render, headed render, GPU backend, GPU draw,
GPU compositor and UI test flags enabled. `WITH_STRICT_BUILD_OPTIONS=ON`
remained enabled. No application feature or existing test flag was disabled.

The unfiltered CTest 4.4.4 JSON-v1 listing contains **1,140 registrations** in
this specific Linux Release configuration. These are original test driver
invocations, not 1,140 individual test cases and not a whole-Blender denominator.
This capture executed **zero tests**. Runtime GTest discovery and original test
execution are recorded separately in
[the native GTest evidence](../product-native-gtest-2026-10-23/).

## Capture and binding

| File | Meaning |
| --- | --- |
| `ctest.json` | Original stdout from `ctest --show-only=json-v1 --build-config Release`, without a test selection filter |
| `ctest.stderr.txt` | Original stderr and its exit-status binding in the summary |
| `ctest-registration-inventory.json` | All 1,140 registrations, exact properties, backtraces, commands when available, and unresolved expansion obligations |
| `generated-ctest-files.json` | Byte-hashed content of all 212 generated `CTestTestfile.cmake` files, including commands for unbuilt executables |
| `summary.json` | Source pin, successful configuration receipt, CMake-cache hash, capture command, file hashes, configuration options and explicit limits |
| `native-build-assessment.json` | Generated Makefile dependency/object-rule counts for build planning; these are not test counts |

At this pre-build capture, CTest omitted 741 command vectors because their
executables did not exist yet. The remaining 399 commands identify the pinned
Python interpreter used as the original driver. Availability of that interpreter
does not establish availability of Blender or any other program invoked by the
driver. The generated CTest files retain the original commands in both cases.

One registration is explicitly disabled upstream:
`ui_opengl_test_editor_types.test_open_editor_types`. Its disabled property is
preserved. None of these registrations declares CTest setup/required/cleanup
fixture properties; that does not establish Blender asset availability.

The adapter deliberately retains `registration_enumeration_complete: false`,
`runtime_enumeration_complete: false`, `fixture_completeness: unknown`, and
`execution: not_run` for every entry. Its hashes bind this precise configuration
and its runtime paths. They do not certify a different build or browser package.

## Dependencies required to reach an actual configuration

The successful configuration is
[`configure-with-optix.json`](../product-configure-2026-10-23/configure-with-optix.json),
SHA-256 `930cfd1cfecd20f4e091cb1585224615d4b721370e8a4253eb34b9203c6cf508`.
Earlier failed attempts remain unchanged beside it.

- The original startup asset was hydrated from its exact LFS object.
- An isolated GCC 14.2 toolchain satisfies the product's real compiler minimum.
- The product's exact `lib/linux_x64` gitlink,
  `2b5fbb917a1bf7537cb25456fcb9064302d7e168`, was hydrated. All 716 LFS paths
  were checked against their declared content IDs and lengths. They represent
  708 unique objects: 2,223,963,905 bytes by path and 2,139,616,293 bytes by
  unique content ID.
- Sixty-four authenticated official Ubuntu packages, 14,122,060 downloaded
  bytes, supply the host development dependencies in an isolated prefix. The
  system package database was not changed. PipeWire 1.4.7 and its required
  additional libraries come from official Questing packages, whose actual ELF
  dependencies were independently checked on this Noble host. The independent
  [ABI receipt](../pipewire-abi-review-2026-10-23/report.json) confirms the
  unchanged minimum-version check and successful library loading. This is
  dependency verification, not an audio feature test.
- NVIDIA's original OptiX 8.0.0 headers, commit
  `f60c1e44f18426f426a2ed948f28515b3cf67b8a` in
  [the official repository](https://github.com/NVIDIA/optix-dev/tree/f60c1e44f18426f426a2ed948f28515b3cf67b8a),
  satisfy the source's minimum while keeping `WITH_CYCLES_DEVICE_OPTIX=ON`.
  This does not establish access to a compatible GPU or driver.

## Outstanding coverage obligations

The original requested flags are only one configuration. Upstream defaults in
this capture still leave mesh-paint, Vulkan render, Storm Vulkan, Cycles OSL,
experimental, Linux release-package and system-Python test switches disabled.
`CYCLES_TEST_DEVICES=CPU`. UI Vulkan is enabled as an option but its required
Vulkan render test option is disabled. Separate configuration captures must
retain those additional registrations and their runtime requirements.

All supported configurations must still be reconciled with the source. Blender's
[test registration helper](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/build_files/cmake/testing.cmake#L130)
can return without registering tests if `tests/files/render` is absent. Its
[custom GTest helper](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/build_files/cmake/Modules/GTest.cmake)
creates suite-filtered invocations using source scanning. The concrete runtime
names, including disabled and instantiated names, must come from the built test
binaries. Capturing both the original registered filter and the unfiltered
binary listing can expose omissions by that scanner.

The source's test directories existed during this capture, but their LFS
payloads were not yet all materialized. Independent fixture hydration is a
separate receipt and must not retroactively change this snapshot. Asset presence
also does not prove complete per-invocation dependency closure: linked data,
textures, references, fonts, helper executables and backend availability remain
part of each execution contract.

No candidate 5.2 browser passes transfer to this product 5.4-alpha source pin.
No configured registration or native-only pass establishes browser parity.
