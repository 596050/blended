# Runtime registration inventory adapter

This evidence verifies `tools/test_registration_inventory.py`, a bounded adapter
for CTest JSON-v1 registrations and GoogleTest runtime listing output. It does
not execute Blender tests or establish application parity. The standalone CMake
fixture executed **zero Blender tests**.

## What was verified

The focused suite has **29 passing infrastructure checks**, including a real
CMake 4.4.4 / CTest configuration and listing integration. The initial test-first
run failed because the new module did not exist. A later regression run exercised
all 29 checks and failed two assertions: raw-input hash encoding was mislabeled,
and an overflowing JSON exponent was accepted as infinity. Both were corrected
before the recorded green run.

| Evidence | Result |
| --- | --- |
| `01-red.stderr.txt` | New module absent; one failed test-module import |
| `02-regression-red.stderr.txt` | 29 checks executed; two assertion failures |
| `03-green.stderr.txt` | 29 checks passed; no skips |
| `07-debug-ctest.stdout.txt` | Six actual CTest registrations in Debug |
| `08-release-ctest.stdout.txt` | Five actual CTest registrations in Release |
| `09-infrastructure-manifest.json` | Capture commands, return codes, hashes and explicit infrastructure scope |

The fixture contains setup, aggregate-driver, cleanup, disabled, unavailable
executable and Debug-only registrations. Its CTest setup/required/cleanup names
are retained as scheduling dependencies. They do not establish that Blender's
asset files, textures, libraries or reference outputs are available.

The all-zero source key in the generated fixture inventories is reserved here
for this synthetic infrastructure context. It is not a Blender commit and must
not enter a Blender parity denominator. Every discovered record remains
`execution: not_run`. Both configuration listings retain
`registration_enumeration_complete: false` and
`runtime_enumeration_complete: false`.

## Why configured CTest output is insufficient

The following behavior was checked at both exact Blender commits:

- Product target: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
- Candidate 5.2 source: `fbe6228777e7d9afefcd61a413844e790ae75db7`.

`blender_add_ctests` returns without registering tests when
`tests/files/render` is absent. A successful, empty CTest listing can therefore
be caused by missing assets. The guard is in
[the product source](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/build_files/cmake/testing.cmake#L130)
and [the candidate source](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/build_files/cmake/testing.cmake#L130).

Blender's custom `gtest_add_tests` collects suite filters into an aggregate
CTest command. Its `DISCOVER_TESTS` path therefore does not enumerate all
concrete GoogleTest cases. The custom module also removes
`gtest_discover_tests`. See
[the product module](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/build_files/cmake/Modules/GTest.cmake#L383)
and [the candidate module](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/build_files/cmake/Modules/GTest.cmake#L383).

The vendored GoogleTest listing honors `matches_filter_`, preserves instantiated
names, and limits displayed type/value parameter annotations to 250 characters.
Its disabled-name pattern is `DISABLED_*:*/DISABLED_*`, applied separately to
suite and test names. The adapter follows those behaviors, including disabled
segments inside instantiated names. See
[the product GoogleTest source](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/extern/gtest/src/gtest.cc#L6220)
and [the candidate GoogleTest source](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/extern/gtest/src/gtest.cc#L6220).

`upstream-findings.json` records exact paths, commits and relevant line locations.
These are findings about registration semantics, not a complete source inventory.
The public format references are the
[CTest JSON object model](https://cmake.org/cmake/help/latest/manual/ctest.1.html#show-as-json-object-model)
and [GoogleTest listing documentation](https://google.github.io/googletest/advanced.html#listing-test-names).

## Integration contract

`inventory_ctest(document, *, source_commit, build_config_sha256, configuration,
provenance)` accepts a parsed object or the original JSON text. Text ingestion
hashes the original UTF-8 bytes; object ingestion uses canonical JSON and labels
that encoding explicitly. Duplicate keys, duplicate registration/property names,
non-finite numbers, invalid backtraces and configuration mismatches are rejected.

The result contains `scope`, `provenance`, `input_sha256`, `registrations` and
explicit blockers. Each registration retains its exact name, raw command,
properties, labels, configuration, backtrace and fixture dependencies. Missing
commands and unknown property representations remain unresolved. A disabled test
is retained. CTest registration IDs bind exact name, source commit, build hash
and configuration; input order and source line numbers do not define identity.

`inventory_gtest(text, *, source_commit, build_config_sha256, artifact_sha256,
registration_id, provenance)` preserves the complete runtime suite/test names,
including all typed and value-parameter suffixes. Displayed parameter annotations
are retained as possibly truncated display metadata, not parameter identities.
Unexpected lines are retained and make `listing_parse_complete` false. Duplicate
suite or case identities are rejected. Empty listings remain an unresolved
denominator.

GoogleTest execution IDs bind source, build, artifact and the exact suite/name
pair. They deliberately exclude the parent registration so overlapping CTest
filters cannot count one concrete case twice. `registration_ids` preserves that
relationship for a caller to merge. The native test identity can carry multiple
facet memberships in the central ledger without duplicating an execution.

| `expansion_obligation.status` | Meaning |
| --- | --- |
| `required` | CTest command exists in the listing; inner test cases still need discovery |
| `unresolved` | Command or relevant registration metadata is unavailable/unknown |
| `expanded` | A concrete GoogleTest runtime identity was parsed; this does not attest the completeness of the listing |

Neither API attests caller-supplied hashes, capture arguments, environment,
successful provenance, or source/build ownership. The central runner must verify
those against captured files and the actual artifact. A passing adapter check is
infrastructure evidence and cannot become an upstream test pass.

## Remaining work for a complete denominator

For each required configuration, capture the real native CTest listing and expand
every aggregate command inside its pinned native runtime. Python `unittest`,
custom Python drivers, rendering loops, fixture-generated cases and UI workflows
need their own accurate runtime adapters. Do not substitute this tool's source
scanner or GoogleTest parser for those other test systems.

Reconcile those runtime identities against source registrations and conditional
build flags, including tests suppressed by missing assets. Verify full fixture
closure and reference outputs. Bind browser execution to the frozen native
identities and original assertions. Disabled, skipped, unavailable, unexpanded or
unmapped obligations stay visible until resolved; they cannot be removed to
increase a pass percentage.

## Reproduce the focused checks

From the repository root, with CMake/CTest installed together:

```sh
BLENDED_INVENTORY_CMAKE=/absolute/path/to/cmake \
  python3 -m unittest discover -s tests -p test_test_registration_inventory.py -v
```

If CMake is on `PATH`, the environment variable may be omitted. Without CMake,
the integration check is explicitly skipped and the remaining 28 checks still
run. Such a run does not reproduce the recorded integration evidence.

The adapter's CLI exposes `ctest` and `gtest` modes and writes separate derived
JSON inventories. `--help` lists the context and provenance arguments. It refuses
to write an output over its raw input listing.
