# Original Blender test parity status

Updated 2026-10-23. **Full one-to-one test parity is not achieved.** The implemented ledger currently qualifies 512 successful native/browser pairs in a selected 829-obligation candidate scope. Unexpanded declarations, failed cases, missing cases, missing subtests, expected failures and unavailable host tools remain visible.

## Exact scope and references

| Scope | Immutable identity | What the evidence establishes |
|---|---|---|
| Candidate upstream | Blender 5.2.0, `fbe6228777e7d9afefcd61a413844e790ae75db7` | Exact source used by the original-script qualification. |
| Browser port source | gessa-ai/blender-web, `0e02e84b2bc5d9b27a6dc6e275443292f781fbad` | Source-derived development build with recorded numerical patches and source/build provenance. |
| Native executable | Official 5.2.0 Linux x64 release, archive SHA-256 `96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48` | Independent native discovery and execution of complete original invocations. |
| Base browser artifact | Archive SHA-256 `5141ef40e3191ce2236fd80e23f26a73b7ac2db88f68755c6f4b23c6b59fe991` | Local Chrome 155.0.8059.39 qualification with software GPU flags; no deployed or hardware profile qualification. |
| Product target | Blender 5.4 alpha, `94363991e7dcf39e2d70614aa002ab6f67764a5d` | Separate source/fixture inventory and actual configuration attempts; no transfer of candidate passes. |

The normalized [report](../compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/report.json) contains every known case pair and its blockers. The [conversion record](../compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/conversion.json) binds the original reports, manifests, context measurements, process logs and superseded attempts. The [contract](../compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/contract.json), inventory and typed receipts are independently replayable after relocating the checkout.

## Current selected matrix

Native resource-complete discovery identifies 31 original invocations from 30 distinct Python source files. Their different invocation and fixture requirements produce 829 obligations and 827 distinct source-qualified case IDs. Two IDs occur in both original font modes and retain both obligations.

| Observation | Native | Base browser artifact |
|---|---:|---:|
| Required case obligations | 829 | 829 |
| Cases discovered and executed | 829 | 817 |
| Observed passes | 828 | 601 |
| Assertion failures | 0 | 210 |
| Errors | 0 | 5 |
| Original expected failures | 1 | 1 |
| Missing outcomes | 0 | 12 |
| Observed subtest events | 71 | 57 |

Fourteen native subtests are missing in the browser. There are no unexpected browser subtests. These subtests are events within parent cases, not 14 additional parent cases.

The strict ledger qualifies **512 successful pairs**. It separately records **597 outcome agreements**, including the original expected failure. Outcome agreement does not prove successful whole-invocation execution. In particular, matching pass callbacks inside a failing invocation, or without required host-tool evidence, do not become strict passes.

The bounded source plan retains all 132 original declaration entries, including 101 not expanded by this adapter. These entries include conditional/generated declarations and function bodies. They are not 101 known leaf tests or a configured CTest denominator. The declared-scope gate, all-upstream gate and full-feature gate all remain false.

### Original invocation results

Browser pass and failure columns below are observed parent outcomes, not strict parity. A failing process or incomplete required context can disqualify passing parents. Missing native subtests additionally block equality.

| Original CTest name | Obligations | Native passes | Browser passes | Browser failures/errors | Expected failures | Missing | Strict successful pairs |
|---|---:|---:|---:|---:|---:|---:|---:|
| script_http_downloader | 8 | 8 | 7 | 1 | 0 | 0 | 0 |
| script_disk_file_hash_service_test | 12 | 12 | 0 | 0 | 0 | 12 | 0 |
| script_pyapi_bpy_app | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| script_pyapi_bpy_app_tempdir | 5 | 5 | 5 | 0 | 0 | 0 | 5 |
| script_pyapi_bpy_path | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| script_pyapi_bpy_utils_units | 2 | 2 | 2 | 0 | 0 | 0 | 2 |
| script_pyapi_mathutils | 180 | 180 | 180 | 0 | 0 | 0 | 180 |
| script_pyapi_bpy_driver_secure_eval | 14 | 14 | 14 | 0 | 0 | 0 | 14 |
| script_pyapi_idprop | 39 | 39 | 39 | 0 | 0 | 0 | 39 |
| script_pyapi_prop | 35 | 35 | 35 | 0 | 0 | 0 | 35 |
| script_pyapi_prop_array | 42 | 42 | 42 | 0 | 0 | 0 | 42 |
| script_pyapi_text | 5 | 5 | 5 | 0 | 0 | 0 | 5 |
| script_pyapi_bmesh | 12 | 12 | 12 | 0 | 0 | 0 | 12 |
| imbuf_py_api | 80 | 80 | 78 | 2 | 0 | 0 | 0 |
| operator_function_py_api | 33 | 33 | 33 | 0 | 0 | 0 | 33 |
| operator_wrap_py_api | 48 | 48 | 48 | 0 | 0 | 0 | 48 |
| script_pyapi_grease_pencil | 26 | 26 | 26 | 0 | 0 | 0 | 26 |
| script_pyapi_annotations | 15 | 15 | 15 | 0 | 0 | 0 | 15 |
| script_pyapi_blf_buffer | 82 | 82 | 2 | 80 | 0 | 0 | 0 |
| script_pyapi_blf_vfont | 129 | 129 | 2 | 127 | 0 | 0 | 0 |
| script_pyapi_doc_gen | 1 | 1 | 0 | 1 | 0 | 0 | 0 |
| id_management | 8 | 8 | 8 | 0 | 0 | 0 | 8 |
| bl_rna_paths | 2 | 2 | 2 | 0 | 0 | 0 | 2 |
| bl_rna_accessors | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| geometry_attributes | 16 | 16 | 16 | 0 | 0 | 0 | 16 |
| bl_animation_bake | 5 | 5 | 5 | 0 | 0 | 0 | 5 |
| bl_animation_rename | 4 | 4 | 4 | 0 | 0 | 0 | 4 |
| bl_animation_nla_strip | 7 | 6 | 6 | 0 | 1 | 0 | 6 |
| bl_animation_pose_slide | 11 | 11 | 11 | 0 | 0 | 0 | 11 |
| bl_brush | 4 | 4 | 0 | 4 | 0 | 0 | 0 |
| compositing_node_group | 1 | 1 | 1 | 0 | 0 | 0 | 1 |

## Repairs and separate diagnostic evidence

### Original brush assets

The base browser package omitted the Essentials brush library required by the original `bl_brush` invocation. A separately identified package augmentation appends the exact original `essentials_brushes-mesh_sculpt.blend` bytes and the required preload metadata before Blender starts. The verifier checks the base archive, every unchanged file, unchanged Wasm, existing data prefix, added LFS object, and the only permitted loader edits. It does not rewrite the source-build receipt to claim the base build contained the asset.

On the augmented archive `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910`, **all four original brush cases pass**, with zero failures or skips. The [new qualification](../compatibility/evidence/brush-package-overlay-5.2-2026-10-23/bl_brush-local-server/qualification.json) remains separate from the four failures in the original base matrix. The other 825 obligations have not been transferred to this different package. A sandbox-denied server-start attempt is retained separately and executed zero Blender cases.

### Font rendering and the original image comparator

Both complete browser font modes now receive the exact original fonts and reference images. Their 207 image tests reach the original image comparison code, then fail because the browser invocation has no executable `IDIFF_BIN`. A read-only observer captures the already-generated output PNGs from the original failure traceback before temporary-file cleanup. It preserves every original failed outcome.

A separate host-assisted diagnostic executes the exact source-derived OpenImageIO `idiff` command, arguments and tolerances against those browser PNGs and original references. **All 207 images satisfy the original acceptance predicate:** 80 BUFFER and 127 VFONT. All 80 BUFFER outputs are byte-identical to their reference PNGs. VFONT has 56 comparator exits of 0 and 71 exits of 1; the pinned original test explicitly accepts both. Exit 2, other exits and timeouts cannot pass.

This establishes the selected image comparisons under that host-assisted diagnostic. It does not make the original browser invocations pass, implement general browser subprocess support, qualify unrelated rendering features, or change the 512 strict base-artifact pairs. See the [per-case oracle evidence](../compatibility/evidence/unittest-font-host-oracle-5.2-2026-10-23/summary.json).

## Remaining demonstrated gaps

| Gap | Exact evidence | Required implementation or qualification |
|---|---|---|
| SQLite | 12 native disk-file hash cases cannot be discovered; browser import fails on `_sqlite3`. The original Python dependency build explicitly disables that module. | Build the embedded Python SQLite extension and its database dependency for the browser, then rerun the complete original 12-case invocation. |
| Background process and socket support | `BackgroundDownloaderProcessTest.test_start_stop` fails through `multiprocessing.Pipe`, `socketpair`, and the unsupported socket syscall. | Implement the needed browser worker/IPC behavior and preserve the original lifecycle assertions. The seven other pass callbacks do not qualify a failing invocation. |
| AVIF | Two imbuf parent cases fail in three AVIF subtests; original OIIO was built with `USE_LIBHEIF=OFF`. | Add the actual required codec/backend and verify original read/write comparisons. |
| Missing image formats | Fourteen CINEON, DPX, JPEG2000 and WEBP subtest events are absent because the original source branches on the browser's reduced format list. | Enable and implement the corresponding compiled features; require the native event identities and outcomes. A passing parent alone is insufficient. |
| Image-comparator execution | 207 font-image assertions fail at the original missing-tool guard, despite the separate successful host image oracle. | Supply a faithful browser-compatible comparator or a clearly declared supported test-helper execution profile; retain exact original command and acceptance semantics. |
| Documentation subprocess | The first original documentation subtest succeeds; `sphinx_stub_gen` fails when spawning the required Python process. | Implement the required execution facility and dependency closure before claiming the full original invocation passes. |
| Native expected failure | One NLA case is already marked expected failure upstream and behaves that way in both environments. | Keep it as expected-failure agreement. It cannot count as a demonstrated working feature. |
| Test denominator | Conditional registrations, C++/GTest binaries, UI, render, simulation and custom test drivers are not fully expanded. | Capture actual configured CTest registrations, native runtime leaf identities, fixtures and each applicable browser profile. |

The [full failure triage](ORIGINAL_TEST_FAILURE_TRIAGE.md) preserves exact case IDs, traceback locations, subtest IDs, source hashes, build configuration evidence and original dependency logs. Assertions, thresholds and references were not relaxed to obtain passes.

## How the implementation prevents false parity

Each obligation binds upstream revision, original registration and invocation, native-discovered leaf ID, input closure, comparison policy, runtime/build context and browser profile. Discovery is independent of browser success. The original scripts run through their unchanged `__main__` entrypoints with original arguments and process isolation. Dynamic test methods, subtests, setup errors, expected failures, skips, original exit behavior and actual process shutdown remain separate observations.

Raw reports are retained before normalization. The normalizer validates their hashes and sizes, source/fixture identities, original argument vectors, host-process command and timestamps, frozen harness snapshots, and the exact execution JSON in the original log. It preserves real exit codes rather than converting a failed invocation into a successful process record. Normalized evidence uses relative, confined paths and survives checkout relocation.

The old facet gate's hash-only evidence acceptance was replaced with typed case-execution receipts that must match the independently selected case, target, profile, run and context. Hash-valid arbitrary or failed JSON is no longer accepted as a feature pass. Both the facet gate and the new test ledger keep `full_feature_parity` false; satisfying a declared test contract would still leave whole-application coverage to be established.

The CI workflow [test-parity-ledger.yml](../.github/workflows/test-parity-ledger.yml) separates infrastructure regressions from the strict original-test gate. Valid blocked reports are generated and uploaded; the subsequent strict gate exits unsuccessfully while obligations remain. A green infrastructure job does not claim Blender parity.

## Product target inventory and configuration

The separate [5.4 source inventory](../compatibility/evidence/source-inventory-2026-10-23/source-inventory-summary.json) retains 10,848 source files, 5,637 heuristic declaration candidates, five unresolved source parses/encodings, and 7,353 candidate fixture paths. The declaration count includes 801 compile-time `static_assert` occurrences and is not a runtime test count. All 30 facet scopes remain incomplete.

Product configuration uses the original source with GTest, GPU render, headed render, GPU backend, GPU draw, GPU compositor and UI test flags enabled, plus strict build options. The first attempt stopped at the unhydrated original startup file. Its exact LFS object was restored and verified; the second then reached the actual GCC minimum check. A local GCC 14.2 toolchain now passes that check. The next actual configuration stopped at missing native dependency libraries. These attempts and the exact dependency submodule pin are retained in [product configuration evidence](../compatibility/evidence/product-configure-2026-10-23/). No test or feature was disabled to make configuration appear complete.

## Reproduce the evidence checks

From the repository root, with Python and CMake installed:

```bash
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -q
python3 tools/test_parity_ledger.py \
  --contract compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/contract.json \
  --inventory compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/inventory.json \
  --executions compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/executions.json \
  --evidence-root compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23 \
  --output /tmp/blended-strict-parity-report.json
```

The strict ledger's expected current exit is **1**, meaning a valid blocked gate. Exit 2 means malformed or mismatched evidence. `--report-only` changes the command's reporting exit behavior; it does not change the recorded gate or parity claims. This replay verifies recorded evidence and does not rerun Blender.

See [original invocation reproduction](ORIGINAL_UNITTEST_COHORTS.md) for actual native/browser execution and [matrix normalization](UNITTEST_MATRIX_LEDGER.md) for rebuilding the normalized record from the complete initial plan and explicit resource retries. Choose fresh output directories and retain earlier attempts.
