# Exact product configuration attempts

These receipts describe actual configuration of Blender product commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d`. The final recorded attempt,
`configure-with-optix.json`, succeeds with the original requested test flags and
strict build options intact. No application feature or existing test flag was
disabled to bypass a dependency error.

| Attempt | Actual result |
| --- | --- |
| `configure-attempt.json` / `configure.log` | Original startup asset was still an LFS pointer |
| `configure-after-startup-hydration.json` | Exact startup bytes restored; compiler requirement then blocked configuration |
| `configure-with-gcc14.json` | Isolated official GCC 14.2 passes the compiler requirement; native dependency libraries absent |
| `configure-with-native-libs.json` | Exact library gitlink hydrated; host audio and desktop development dependencies absent |
| `configure-with-host-deps.json` | Verified isolated host dependencies resolve those errors; OptiX headers absent |
| `configure-with-optix.json` | Official pinned OptiX headers supplied; CMake configuration and generation exit 0 |

Each attempt has a new build directory and separate original log. The scripts,
commands, environment overrides, hashes and generated cache/configuration logs
are retained. `tests_executed: 0` in a configuration receipt means exactly that;
configuration is not an execution result.

## Dependency receipts

`native-library-pin.json`, `native-library-lfs-inventory.json` and
`native-library-hydration.json` bind the original product gitlink
`2b5fbb917a1bf7537cb25456fcb9064302d7e168`. All 716 declared LFS paths match their
actual SHA-256 values and lengths. Path bytes total 2,223,963,905; deduplicating
708 unique content IDs gives 2,139,616,293 bytes. Verification of the expected
tracked payloads is distinct from the retained worktree-status observation.

`host-package-index.json` binds the official Ubuntu package indices and archive
keyring used by the isolated APT state. `host-dependency-packages.json` records
all 64 packages, their exact versions and authenticated SHA-256 values. Packages
were downloaded and extracted into the workspace; no maintainer scripts or
system package installations ran. The host package-status file has the same
hash before and after. Original plan, URI and download logs remain separate.

`optix-headers.json` binds NVIDIA's official `optix-dev` v8.0.0 header commit
`f60c1e44f18426f426a2ed948f28515b3cf67b8a` and every file's hash. It keeps the
default enabled OptiX backend without asserting that this host has an NVIDIA
GPU or that OptiX rendering tests ran.

The resulting actual unfiltered CTest registrations are documented in
[the configured inventory](../product-ctest-configured-2026-10-23/README.md).
Original native test builds, runtime listings and execution results are in
[the native GTest evidence](../product-native-gtest-2026-10-23/).

Successful configuration covers one explicit Linux Release configuration.
Source reconciliation, other test options, platform/backend variants, complete
fixture closure and runtime expansion remain obligations. All application and
whole-upstream parity gates remain false.
