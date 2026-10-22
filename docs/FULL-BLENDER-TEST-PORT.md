# Complete Blender test-port requirement

The target is the entire test suite at the Blender commit in `upstream.lock.json`, not a selected sample. The complete browser-executable port is NOT finished. Do not report this requirement as satisfied because the corpus importer or the limited modeller passes.

## What is preserved

`vendor/blender` pins the complete upstream source tree, including dependencies needed by original tests. The `blender-test-corpus` branch keeps original test sources, support files, test assets as Git LFS pointers, CMake registration files, a complete tracked-file hash index, source candidates, compile-time assertions and individual blockers. Original assertions and reference files must not be replaced by simplified stand-ins. The imported byte payloads are checked against upstream Git blob identities and recorded with SHA-256.

The first full source audit found 20,896 ordinary tracked blobs and five external Git submodule references. The import selects 8,780 original files for the test corpus, including helpers and registration files. Its 1,010 source obligations consist of 809 test/support sources and 201 compile-time-only source obligations. These are file counts, not feature or runtime-test counts.

The declaration scan finds 4,836 runtime-test candidates and 801 compile-time assertions. Typed/parameterised tests, generated Python tests, fixture-driven tests, shader variants and conditional platform registrations still require native/runtime expansion. Five source-decoding/template diagnostics are preserved without discarding original bytes.

The main Blender tree contains 7,053 LFS pointer paths referring to 6,840 distinct objects, totalling 888,905,674 declared payload bytes. This includes 6,691 paths under test directories. Every format is accounted for, not just `.blend`. Each CI attempt fetches the full pinned LFS object set from Blender's public LFS endpoint into a separate cache and verifies each actual payload's byte length and SHA-256. Consult `fixture-audit.json`; neither a pointer nor an attempted download is a verified asset. External library submodules and the separate benchmark repository are additional dependencies, not included in these asset totals.

## Separate completion states

1. Source preservation: original files and identities are available.
2. Runtime enumeration: actual registered/expanded tests are known for every profile.
3. Test port: original assertion semantics have reviewed browser adapters, all required cases execute, and compile-time checks are retained.
4. Conformance: both native reference and browser implementation pass those tests.
5. Feature parity: requires additional coverage for functionality not tested upstream; passing the entire existing suite alone is not a proof of exhaustive feature parity.

`test_port_complete`, `conformance_passed` and `feature_parity_proven` are separate fields. An actual failing assertion may demonstrate an executable port without demonstrating conformance. A crash, timeout, missing fixture, missing backend, unexpanded case, disabled test or skip does not demonstrate execution of its assertions.

## Required profiles and source areas

The contract retains CPU, GPU, interactive UI, platform/optional-feature conditions and performance tests. It includes C/C++ GoogleTest and compile-time checks; Python API and embedded Blender tests; operators, mesh/BMesh, modifiers and Geometry Nodes; animation, rigging, sculpting and simulations; file I/O and codecs; Cycles, EEVEE, Workbench and shader tests; compositor and video-sequencer reference comparisons; UI/undo; and performance tooling. An unavailable browser equivalent remains an explicit gap, not an exclusion that improves the pass rate.

The native reference must match the exact upstream commit. Record CMakeCache and enabled build options, use `WITH_GTESTS=ON` and `WITH_TESTS_BATCHED=OFF`, and explicitly enable relevant GPU/UI/system-Python options for the selected profile. Capture CTest JSON, expand actual GoogleTest listings and dynamic Python/fixture test cases, and reconcile them to their original source files. `enumerate-ctest` deliberately does not label raw CTest registration as complete expansion.

## Evidence and CI

The workflow `Complete Blender test-port requirement` has independent jobs for the gate's own regression tests, source/asset import, actual deployed-alpha regressions, persistent corpus publication, and the full-browser-test-port gate. The last job is supposed to FAIL while the port is incomplete. A green infrastructure or alpha job does not override that failure. This adds a CI status check; it does not silently change repository branch-protection settings.

The current 17 Blender maths ports are retained in `existing-partial-ports.json`. The existing app is retested at its real public URL and those results are stored separately in `current-alpha-smoke`. They must not be used as the denominator for the full suite. Zero verified full source-file ports in the new strict ledger does not erase those 17 partial cases; it means no file has yet met the new complete-file, runtime-mapping and native/browser evidence contract.

Reports validate source/adapter hashes and evidence relationships. Hash strings alone are not signatures: before adding completed mappings, the producing CI job must retain and hash the actual logs, compiler configuration, adapter source and result payload. The importer currently creates an empty full-runtime registry/port ledger and the full gate remains red. Integration of the complete native test build and browser execution adapters is still required.

Never enable `BLENDER_TEST_UPDATE`, regenerate golden results from the browser under test, weaken numeric/image thresholds, replace test bodies with capability booleans, or turn unsupported tests into passes. Preserve the upstream expected results and compare topology, attributes, state and image output according to the original assertions. Memory, GPU device-loss, workers and persistence also need browser-specific regression coverage.

## Commands

```sh
python3 tools/fetch_upstreams.py blender
PIN=$(python3 -c "import json;print(json.load(open('upstream.lock.json'))['upstreams']['blender']['commit'])")
python3 tools/blender_suite.py catalogue --root .upstream/blender --pin "$PIN" --policy compatibility/blender-suite-policy.json --output evidence/full-suite
python3 tools/blender_suite.py fixtures --directory evidence/full-suite --cache .upstream/blender/.git/lfs/objects
python3 tools/blender_suite.py enumerate-ctest --build /path/to/reference-build --output evidence/ctest-registration.json
python3 -m unittest discover -s tests -p test_blender_suite.py -v
```

The required next deliverable is not another small green smoke suite: it is a complete, source-reconciled native runtime catalogue and browser execution adapters for every registered case, with the original fixtures and assertions.
