# Original Blender unittest invocations

This adapter executes complete, unchanged upstream Python scripts through their original `__main__` entrypoint. It obtains the case inventory from the suite that native Blender's unittest runner actually receives, including dynamic methods and `load_tests`. Browser discovery cannot shrink that inventory.

The pinned candidate reference is Blender 5.2.0, commit `fbe6228777e7d9afefcd61a413844e790ae75db7`. This is separate from the Blender 5.4 product target. Passing these selected invocations does not establish a complete configured CTest denominator, all Blender features, all browser platforms, or product parity.

## Evidence available

The source invocation plan in `compatibility/evidence/unittest-native-5.2-2026-10-23/discovery-inventory.json` retains 132 `add_blender_test*` declarations. It attempted 31 unconditional, supported unittest invocations and explicitly retained 101 conditional, generated, UI, fixture-dependent, or unsupported declarations. Source declarations are not a count of configured CTests or unittest cases.

The initial native run froze 700 leaf cases in 30 invocations. It retained 83 resource-related case failures, one original expected failure, and one font invocation that failed before discovery. None of these failures was changed into a pass.

The resource-complete reruns restored the original font files, reference images, image comparator, documentation sources, and documented Python dependency. The revised selected inventory contains **31 original invocations across 30 distinct source files, with 829 leaf cases: 828 native passes and one upstream expected failure**. The NLA expected failure remains an expected failure. There are no omitted case outcomes in that revised selected inventory.

The authoritative index is `compatibility/evidence/unittest-native-resources-5.2-2026-10-23/revised-native-inventory.json`. It binds each selected manifest and raw native report by byte count and SHA-256. All initial failed attempts remain available. Browser results must be compared separately against these exact native cases and contexts.

## Contract and execution

Each schema-2 manifest represents one original CTest invocation and one fresh process. The same source file can have more than one manifest when CMake registers different original modes, as with BLF BUFFER and VFONT.

The contract records the upstream source commit, exact script and helper bytes, original CMake registration, original script arguments, CMake source identities, and execution context. The adapter preserves the standard background, startup, crash/debug, Python exit-code, and thumbnail-disable flags from the pinned CMake sources. Script arguments must match the recorded original registration. Test filtering, fail-fast operation, reference regeneration, and omitted documentation subtests are not accepted.

Registration text is independently authenticated by `tools/upstream_invocations.py`. Its checksum-bound catalog retains the complete bytes of both original CMake files and all 132 declarations, including their source lines and conditional/function/loop contexts. The verifier reconstructs the declarations from those source bytes. Editing both a manifest's arguments and its declaration cannot authorize a new invocation. Attached `-kPATTERN`, `--keyword=PATTERN`, and positional case-selection attempts are covered by regression tests. Conditional or generated declarations remain visible and require configured CTest evidence.

The observer materializes the unchanged source under its original relative path, reconstructs the original script argument vector, and invokes it with `runpy.run_path(..., run_name="__main__")`. It observes the standard unittest runner without changing test assertions or selecting cases. It records class/module setup errors, skips, expected failures, unexpected successes, and subtests separately. The original `SystemExit` is preserved; scripts that use `unittest.main(exit=False)` retain their own exit behavior.

Native qualification requires actual subprocess completion. Browser background qualification requires the unchanged shell's observed Emscripten exit code. A printed result does not establish successful shutdown. Original test-main exit status, process exit status, source identity, and case outcomes are distinct observations.

Native discovery freezes exact case IDs even when an original case fails or is expected to fail. This preserves the denominator for diagnosis. A frozen inventory does not mean its cases passed. The browser loader requires the manifest checksum, the complete native receipt bytes, matching native artifact/build identity and invocation, and the same exact case inventory. Only the injected `__main__.` prefix is normalized for this driver; imported classes retain their qualified module names.

## Resource closure

The unchanged BLF tests derive fixture paths from `__file__`. The resource manifests mount the original files at `tests/files/blenfont` within the materialized source tree. They retain the four Noto fonts and all original reference PNGs for each selected mode. The BUFFER invocation requires 84 files; VFONT requires 131 files. Shared content hashes at distinct original paths are downloaded once and materialized at every path.

LFS metadata retains the original pointer text, Git blob identity, object SHA-256, byte count, source commit and path. Downloaded bytes must match the pointer. The count bound is 256 files per fixture inventory; the 32 MiB per-file and 128 MiB total byte bounds remain unchanged.

Image comparisons use the original `idiff` executable from OpenImageIO 3.1.13.0. The original test determines comparator arguments and tolerances. No reference images are regenerated, no thresholds are relaxed, and no replacement image comparison is used.

The documentation invocation retains 156 original source resources: the complete `doc/python_api` tree, its referenced Python templates, and `source/blender/bmesh/intern/bmesh_opdefines.cc`. Its original subprocess uses the documented `PYTHON_BIN` override with `docutils==0.22.4`, as pinned in upstream `doc/python_api/requirements.txt`. Source resources retain original repository paths, SHA-256 and Git blob identities; the favicon's LFS object is resolved to its original bytes.

Required native host tools are recorded by environment key, executable hash, and byte count. Their actual resolved identities are observed during native execution. A browser port still needs equivalent subprocess and filesystem behavior to pass these original invocations. Merely staging the resource bytes does not implement that capability.

## Resource-complete browser results

The resource retry matrix is preserved in `compatibility/evidence/unittest-browser-resources-5.2-2026-10-23/matrix.json`; its hash-bound diagnosis is `compatibility/evidence/unittest-resource-triage-5.2-2026-10-23.json`. The original browser results remain:

| Invocation | Original cases executed | Original result | Remaining obstacle |
|---|---:|---|---|
| BLF BUFFER | 82 | 2 passed; 80 assertion failures | The exact fonts and references load, and rendered PNGs are written. The original missing-`idiff` assertion fails before image comparison. |
| BLF VFONT | 129 | 2 passed; 127 assertion failures | The exact fonts and references load, and rendered PNGs are written. The same original comparator guard fails. |
| API documentation | 1 | 1 case with a subtest error | The original RST-generation subtest passes using all 156 source resources. Strict stub generation reaches `subprocess.run`, which Emscripten rejects with `ENOTSUP`. |

Each font mode also retains three passing subtest callbacks. The documentation case retains one passing and one failing/error subtest callback. Subtests do not increase the top-level case denominator. The historical documentation observer recorded its exception callback as `failed`, while original unittest recorded `errors=1, failures=0`; the current observer preserves the original error category. That historical receipt was not rewritten.

### Separate host-assisted font image oracle

`tools/probe_font_image_oracle.py` adds a read-only observation at the original missing-comparator failure. The traceback still holds `_compare_image`'s original image paths and per-case thresholds. The observer exports the PNG Blender has already written before the original temporary-directory cleanup, without changing the failure, test selection, assertions, source, references, or invocation arguments.

The diagnostic decodes and verifies those bytes on the host, reads the comparator argument expression directly from the pinned original source, and runs the exact native-observed OpenImageIO `idiff` executable. Only the executable and filesystem paths are mapped to host locations. Every case retains the observed thresholds as both JSON values and exact float hex strings, executed argument vector, source/reference/image/diff hashes, stdout/stderr, and actual process return code. Export bounds are 256 images, 8 MiB per image, and 16 MiB total per invocation. Image names, modes and derived diff paths must agree and remain within their output directory.

The complete result is bound by `compatibility/evidence/unittest-font-host-oracle-5.2-2026-10-23/summary.json`:

| Original image pipeline | Images captured | Accepted by original `idiff` criteria | Exact PNG byte matches | Original comparator return codes |
|---|---:|---:|---:|---|
| BUFFER | 80 | 80 | 80 | 80 returned 0. |
| VFONT | 127 | 127 | 0 | 56 returned 0; 71 returned 1. |
| Total | 207 | 207 | 80 | No mismatch return code 2, comparator error, or timeout. |

The upstream test explicitly accepts return codes 0 and 1. Its observed thresholds were `-fail 0.0040 -failpercent 0.0000` for BUFFER and `-fail 0.0100 -failpercent 0.1100` for VFONT. VFONT therefore meets the original image acceptance criteria; this does not assert byte-for-byte output identity. All 207 original browser missing-comparator failures remain failures in their separate browser receipts and in the strict parity ledger. This diagnostic does not implement browser subprocesses or establish a passing original browser font suite.

## Reproduction

The reusable entry points are:

| Tool | Purpose |
|---|---|
| `tools/discover_unittest_cohorts.py` | Build the bounded source plan, run supported original invocations in isolated native processes, and retain unsupported declarations. |
| `tools/probe_native_reference.py` | Run one named or external invocation against the checksum-verified official native archive. |
| `tools/probe_browser_port.py` | Run one frozen invocation against the pinned browser artifact, retaining exact IDs and outcomes. |
| `tools/prepare_unittest_resources.py` | Resolve the original font and documentation resource closure into new discovery proposals and verified local caches. |
| `tools/unittest_cohort.py` | Validate external manifests, observe original unittest execution, and freeze native-discovered IDs. |
| `tools/upstream_resources.py` | Verify and materialize additional original source resources without modifying their contents. |
| `tools/upstream_invocations.py` | Authenticate all original declarations and complete pinned CMake source bytes. |
| `tools/probe_font_image_oracle.py` | Preserve the original browser font failures while exporting their images for the separately reported original host comparator. |

An initial source discovery uses the exact upstream source tree and official native archive:

```bash
python tools/discover_unittest_cohorts.py \
  --source-root /absolute/path/to/pinned-source \
  --native-asset /absolute/path/to/blender-5.2.0-linux-x64.tar.xz \
  --output /new/native-evidence-directory \
  --manifest-output /new/frozen-manifest-directory
```

Use a fresh output directory. The source planning command does not evaluate arbitrary CMake conditions or claim configured test completeness. For actual registered CTests and GTest leaves, use the separate runtime inventory tools.

One external discovery invocation uses `--suite-manifest`, its explicitly supplied `--suite-manifest-sha256`, `--discover`, and `--freeze-manifest`. The frozen manifest references the completed native report. Browser execution accepts the frozen manifest and checksum without `--discover`.

Supply `--suite` for every unchanged script/helper in the invocation. Supply `--fixture-root` for verified original fixture objects beneath their `tests/files` relative paths and `--resource-root` for the verified original source resource tree. Resource-complete native retries use `IDIFF_BIN` and `PYTHON_BIN` to select the recorded original host tools. Their values and executable identities must match the new manifest.

Keep the original failed report when fixing resources or infrastructure. Create a new proposal, native receipt, frozen manifest, and browser receipt, then update the selected evidence index explicitly. Historical outcomes must remain distinguishable from current ones.

All 34 schema-2 frozen manifests available at this checkpoint use relative native-receipt paths. Copying each unchanged manifest and receipt into an unrelated directory with the same repository layout passed the manifest loader. The relocation receipt is `compatibility/evidence/unittest-manifest-relocation-2026-10-23.json`. Absolute paths inside raw argv/log records remain historical runtime observations; they are not rewritten or needed to locate the frozen native receipt.

## Limits that remain explicit

The source planner supports ordinary unconditional Python registrations with the standard unittest runner. Conditional build registrations, C++/GTest binaries, UI event tests, render/image families, platform-specific facilities, and custom drivers require their own configured inventory and reviewed execution adapters. Unsupported declarations remain unresolved instead of disappearing from the program.

The generic observer does not convert a skip or expected failure into a feature pass, infer successful shutdown from test output, count subtests as additional top-level cases, or claim a complete denominator from a method-name scan. A one-to-one candidate comparison requires the same invocation, source, resources, native-discovered IDs, complete outcomes, and applicable runtime context on both sides.

The selected-script control audit found no source-defined environment sharding in these 30 files. Relevant environment reads include original host-tool selection, temporary-directory behavior, optional stronger VFONT bounds checks, and GPU-unavailability skip handling. Skips still fail the strict feature-pass gate; the selected VFONT registration uses the original Cycles render mode. Historical receipts are not retroactively represented as complete environment snapshots. Build configurations, platform variants and the unresolved registrations still require their own independently defined invocation and environment criteria.
