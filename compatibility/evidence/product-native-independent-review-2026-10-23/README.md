# Independent native product test evidence review

**Result: verified for the five preserved Linux Release test executables below.**
This review executed no original tests, changed no production code, tests,
assertions, source files, or earlier receipts, and inferred zero browser passes.

Source commit: `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
The original source archive is 80,900,636 bytes with SHA256
`e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`.

| Preserved native capture | Runtime observations | Passed | Skipped | Failed/error/missing |
| --- | ---: | ---: | ---: | ---: |
| BLI-source-identities | 1,742 | 1,742 | 0 | 0 |
| atomic | 56 | 56 | 0 | 0 |
| guardedalloc | 6 | 6 | 0 | 0 |
| makesdna | 5 | 5 | 0 | 0 |
| shader_tool | 62 | 61 | 1 | 0 |

These are original GoogleTest outcomes inside five CTest drivers. The review
does not add another set of outcomes to the native denominator.

## BLI identity and execution findings

The independently parsed original GoogleTest XML contains **1,742 testcase
elements and 1,742 passes**. Its names, including multiplicity, exactly match
both original runtime listings. The registered and unfiltered listings are
byte-identical. They contain 1,741 distinct display names because `stack.Peek`
occurs twice. No listing observation, XML outcome, or original run/pass log
callback was missing or added.

The two equal names resolve through the original XML's file and line metadata:

| Display name | Original declaration | C++ namespace | Outcome |
| --- | --- | --- | --- |
| stack.Peek | `source/blender/blenlib/tests/BLI_stack_cxx_test.cc:172` | `blender::tests` | Passed |
| stack.Peek | `source/blender/blenlib/tests/BLI_stack_test.cc:97` | `blender` | Passed |

Both original lines are `TEST(stack, Peek)`. The review compared every one of
BLI's 97 reported declaration files byte-for-byte with the pinned archive and
checked their presence in the captured build rules. All 1,742 source identities
were independently recomputed from the source commit, original file path and
SHA256, declaration line, and test name. They are unique and equal the receipt's
identities. Reversing traversal order produces the same identity set. No list
ordinal, runtime binary hash, or timestamp enters the source identity.

The original CTest JSON registration, actual verbose CTest command, working
directory, environment properties, binary SHA256, configuration cache, build
receipt, and generated target rules agree. CTest returned 0 without a timeout;
its JUnit report contains one successful BLI driver. Its log contains every
original GoogleTest run and pass callback. The wrapper preserves the registered
filter and adds only the upstream XML-report environment setting, `GTEST_OUTPUT`.
The bound capture code removes inherited `GTEST_*` variables before discovery
and execution. Neither a hidden filter nor sharding nor early termination is
supported by the reconciled evidence: every unfiltered listed observation has
an original outcome. No disabled or skipped BLI cases are recorded.

The first failed BLI inventory attempt remains in `../product-native-gtest-2026-10-23/BLI/`.
Its duplicate-name adapter failure happened before test execution. The review
verified its saved file identities and zero-execution receipt; it was not
overwritten or recast as a product test failure or pass.

## Ancillary results and limits

The same independent listing, XML, log, build, and source-byte checks confirm
the four ancillary rows above. `shader_tool.MatrixConstructors` is explicitly
skipped by the original `#ifndef __APPLE__` guard at
`source/blender/gpu/shader_tool/tests/syntax_test.cc:132-134`, with the original
message explaining that its processing is for Metal compatibility. That skip
remains a skip.

The earlier atomic and guardedalloc receipts lack the later capture-script and
source-identity fields. Their original raw XML still records file and line;
this review independently verifies those locations and the preserved build and
execution evidence without rewriting their historical receipts. The full
inherited non-GoogleTest environment was not archived. Original explicit
environment properties and the configured overrides were preserved.

Equality of registered and unfiltered runtime listings proves coverage of these
compiled binaries. It does not enumerate platform-conditional source cases,
other configurations, unbuilt binaries, or the whole application. These native
5.4-alpha results establish no browser execution or browser feature parity.
All reviewed receipts retain their false whole-product completeness flags.

## Audit artifacts

- `audit.py`: standalone standard-library verifier; it imports no production
  inventory adapter and refuses to overwrite its completed report.
- `report.json`: exact input file bindings, independently verified source-file
  hashes, duplicate-case identities, suite findings, and explicit limitations.

The verifier completed with process exit 0. Its report is 59,060 bytes with
SHA256 `7ff1aa55c0f57eba41bd7166e22602c74cf75c6427c51bc1b177f90ac7b1d192`.
Reproduction requires the preserved raw evidence and the exact native runtime
artifacts and source archive; run a copied review directory to retain this
immutable report.
