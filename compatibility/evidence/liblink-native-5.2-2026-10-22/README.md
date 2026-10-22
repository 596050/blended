# Native Blender 5.2 library-linking cohort

The complete unchanged `tests/python/bl_blendfile_liblink.py` at commit `fbe6228777e7d9afefcd61a413844e790ae75db7` passed all 17 original methods on the verified official Blender 5.2.0 Linux x64 executable. All 14 original class drivers returned normally. This evidence establishes the selected native upstream cohort. It does not establish browser execution, cross-engine file exchange, full library dependency closure, browser persistence, or full facet parity.

## Exact original execution

The observer uses `runpy.run_path(original_source, run_name="__main__")`. The original main block parses `--src-test-dir` and `--output-dir`, sets its original preference, constructs the original `TESTS` classes, and calls unchanged `TestHelper.run_all_tests`. The helper enumerates callable `test_*` methods through `dir(self)`, calls `setUp`, then the method, and calls `tearDown` in `finally`. An upstream exception aborts the remaining original driver.

Each of the 17 fixed case IDs has the exact six observed events: setup start/normal return, body start/normal return, and teardown start/normal return. CPython `sys.monitoring` distinguishes normal returns from exceptional unwinds. The observer replaces no test callable, assertion, helper driver, or Blender algorithm. It preserves upstream fail-fast behavior and rethrows exceptions after recording evidence. Module exit alone does not determine a case result.

`native-library-proof.json` records the official archive and executable hashes, input-manifest and observer hashes, exact command, return code, elapsed time, and final generated-file inventory. `execution.json` records all actual phases, class-driver events, unchanged source hashes, and read-only observations of data, libraries, images, and context after each case. `native-library.log` is the exact stdout/stderr stream. `receipt-verification.json` independently checks the fixed case/phase inventory and source, fixture, and output bytes after the run. The observed scripts are retained byte-for-byte; their original paths and workspace layout are recorded in the proof.

The binary reported Blender 5.2.0 LTS, build hash `fbe6228777e7`, and Python 3.13.13. The native process returned zero and ran for about 1.47 seconds. All case-end context observations had background mode enabled, a current window, no edit object, and successful link/append polls. The observer requires Python 3.12 or later for `sys.monitoring`.

## Three pinned fixtures

The suite needs only these external fixture objects for the observed full run:

| Relative path under `--src-test-dir` | Bytes |
|---|---:|
| `imbuf_io/reference/jpeg-rgb-90__from__rgba08.jpg` | 5,165 |
| `libraries_and_linking/libraries/collection_assets.blend` | 103,099 |
| `libraries_and_linking/libraries/animated_assets.blend` | 104,736 |

The 213,000-byte total is verified against the exact Git LFS pointer objects at the upstream pin. The cohort manifest records each pointer's Git blob identity, exact pointer bytes and SHA-256, plus the actual object's size and SHA-256. A pointer file is not a usable fixture. Source and fixture bytes remained unchanged after execution.

`lfs-retrieval-recipe.json` records the tested public endpoint, exact batch body, response handling, and verification requirements. The successful method was a Git LFS download batch POST to Blender's official project server followed by GETs of each returned `actions.download.href`, using any returned download headers. The GitHub media mirror returned HTTP 404 and was not used for the successful downloads. `prepare_inputs_observed.py` is the exact preparation script used for the recorded run. It obtains the source and pointer bytes through `git show` at the exact pin, downloads the objects, verifies their sizes and hashes, and writes the input manifest. The broader source inventory includes two alternative suite files inspected during selection; only the 17-case liblink module was executed.

## Reproduction

Use the exact official archive, extracted executable, the exact main and adjacent helper source, and a fixture tree populated from the three verified LFS objects. Run the retained observer with a fresh output directory:

```sh
/absolute/path/blender-5.2.0-linux-x64/blender \
  --background --factory-startup --threads 1 --disable-autoexec --python-exit-code 1 \
  --python /absolute/path/observe_blendfile_liblink.py -- \
  --source-dir /absolute/path/exact-upstream-sources \
  --fixture-dir /absolute/path/verified-fixtures \
  --output-dir /absolute/path/fresh-generated-files \
  --report /absolute/path/execution.json
```

The original arguments inside the observer remain `--src-test-dir VERIFIED_FIXTURE_ROOT --output-dir FRESH_OUTPUT_ROOT`. The manifest and native proof retain the fully expanded observed arguments. Do not substitute a unittest loader: the classes require an argument namespace and their original custom driver.

## Output and coverage limits

The original run produced 22 final files: 19 `.blend` files and three backups, totaling 9,677,442 bytes. The largest file is 480,936 bytes. The inventory preserves all names, sizes, and hashes; binary fixtures and generated files are not committed. These hashes identify this native run and must not become expected browser output hashes.

Persistent direct and indirect libraries are observed after the original save/reopen cases. An indirect material retains an unpacked JPEG dependency. These are case-end observations, not a separate reopened/relocated bundle audit. A future exchange test must independently inventory and validate the relevant library and texture dependencies and preserve their relative layout. This cohort's pass does not prove that every referenced path remains usable after relocation. Some methods test in-memory states without saving them, and some filenames are intentionally overwritten by later methods or substeps.

This cohort covers only its original assertions for linking, appending, ID reuse, collection-instance regressions, packed linked IDs, library reload/relocate calls, animation checks, and `bpy.data.libraries.load` combinations including overrides. It does not replace `bl_blendfile_library_overrides.py`, legacy proxy conversion, asset browser/catalog tests, or additional file exchange and persistence tests. Methods can contain several substeps, but the fixed denominator remains 17 original methods.

Browser qualification should use the same background execution mode and original arguments, verify the exact main/helper/fixture bytes in the virtual filesystem before execution, and retain every fixed case and any failure. Upstream link/append polling requires a current window and rejects edit mode; upstream file-read behavior differs between background and interactive execution. A passing background test does not establish the corresponding interactive workflow.
