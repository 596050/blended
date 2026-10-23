# Original Blender test parity status

Updated 2026-10-23. **Full one-to-one test parity is not achieved.** The latest source-built browser package has **528 successful native/browser pairs in the selected 829-obligation candidate scope**. All 12 original disk-file hash cases now pass with the real SQLite extension. The same build aborts during its original ImBuf invocation before emitting the final execution payload, so all 80 ImBuf parents and 57 required subtests remain missing for that profile. Earlier package results remain separate. The separately qualified 88-case bevel profile is also outside this denominator.

## Latest source build and exact qualification

The [source build](https://github.com/596050/blended/actions/runs/39986612484)
at `f25e69ed72fed2d31d7d65e657fd6515da4bd792` completed all 132 stages in
2,771.476395 seconds, approximately 46 minutes 11 seconds. It reused 4,103
individually verified dependency files and three source-derived libpng aliases;
this is not a clean-build timing. The build succeeded and both complete
qualification jobs failed. The [recovered original build receipts](../compatibility/evidence/source-build-recovery-39986612484/README.md)
and [raw qualification files](../compatibility/evidence/source-rebuild-unittest-39986612484/)
preserve those distinctions.

| Qualification profile | Strict successful pairs | Outcome agreements | Missing parents | Missing subtests |
|---|---:|---:|---:|---:|
| Earlier base package | 512 | 597 | 12 | 14 |
| Earlier Essentials package | 516 | 601 | 12 | 14 |
| Source build with codecs, SQLite and Essentials | 528 | 536 | 80 | 57 |

The [current report](../compatibility/evidence/unittest-parity-ledger-source-build-39986612484/report.json)
has SHA-256 `913a5f430f2ea9df35ec2878240a3c3b3b6783062c733a2e9a6f58d3b6c21b0b`.
Its browser observations are 539 passes, 207 assertion failures, two errors and
one original expected failure, totaling 749 recorded parent outcomes. Only 528
meet the strict successful-execution criteria. The 12 new SQLite pairs are
actual original-suite executions on this artifact. Earlier ImBuf observations
cannot fill the 80 missing outcomes. Losing 77 earlier ImBuf agreements while
adding 12 SQLite agreements explains the change from 601 to 536 agreements.

The exact browser archive is
`c2105e12ae93e1804f82f3f49fdec3e0185ce2dd7fe9f26e97f4d3b44308df3c`.
The base archive before resource augmentation is
`0d51a33313902a0331df02d900fc5776fd0855e8b0f2062b46cf0150d859499a`.
The [runtime context](../compatibility/evidence/runtime-context-source-build-39986612484/browser-context.json)
binds the package, real Chrome executable, source producer and CI invocation.
The normalizer accepts this older CI producer only through exact pinned source
identities and complete command checks. Its working directory is source-derived
from the pinned producer, not claimed as an independently observed OS property.

An exact 730-entry path map restores CI absolute paths to verified repository
files. Duplicate paths, changed bytes, noncanonical paths and symlinks fail
validation. Missing execution payloads remain typed missing observations;
malformed or contradictory payloads cannot become empty successful runs.

Workspace maintenance removed the local checkout and some uncommitted files.
The published checkpoint, retained normalized copies and exact CI artifacts
restored the current report, normalizer and complete input closure. A new
normalizer execution reproduced all 858 profile files byte for byte, and the
strict ledger again exited 1 with `gate: blocked`. The [recovery receipts](../compatibility/evidence/parity-recovery-2026-10-23/README.md)
identify the lost older infrastructure and diagnostic receipts explicitly.
No replacement historical execution receipts were synthesized.

### DPX correction awaiting complete application qualification

The [codec patch](../patches/browser-codecs/README.md) now corrects two active
OIIO DPX expressions that lose their negative storage-reuse sentinel on
wasm32. Exact source-level numeric regressions reproduce `4294963200` for
1,024 RGBA8 pixels in the original 32-bit expression and verify the corrected
`-4096` result, including the other affected descriptors and 64-bit behavior.
The production recipe verifies original source, patch and resulting source
hashes before building. These regressions do not qualify image decoding.

The earlier controlled diagnostic compiled the corrected object, but no
corrected runtime result was observed before cleanup. A new complete Blender
browser build must therefore execute the unchanged original ImBuf invocation,
all 80 parent identities, and all 57 native subtest identities before any
additional strict pairs are credited. The declared-scope, all-upstream and
full-feature gates remain false. All 101 unexpanded declarations remain visible.

The [fresh infrastructure execution](../compatibility/evidence/infrastructure-tests-dpx-recovery-2026-10-23/README.md)
passes all 383 tests with zero skips. It includes 31 new normalizer regressions
and six new DPX numeric/recipe regressions. All 145 captured input identities
remain unchanged across execution. The [independent source review](../compatibility/evidence/dpx-production-review-2026-10-23/README.md)
confirms the two-expression scope and exact patch equivalence. Infrastructure
success does not change any original Blender test outcome.

## Earlier reference profiles

| Scope | Immutable identity | What the evidence establishes |
|---|---|---|
| Candidate upstream | Blender 5.2.0, `fbe6228777e7d9afefcd61a413844e790ae75db7` | Exact source used by the original-script qualification. |
| Browser port source | gessa-ai/blender-web, `0e02e84b2bc5d9b27a6dc6e275443292f781fbad` | Source-derived development build with recorded numerical patches and source/build provenance. |
| Native executable | Official 5.2.0 Linux x64 release, archive SHA-256 `96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48` | Independent native discovery and execution of complete original invocations. |
| Base browser artifact | Archive SHA-256 `5141ef40e3191ce2236fd80e23f26a73b7ac2db88f68755c6f4b23c6b59fe991` | Local Chrome 155.0.8059.39 qualification with software GPU flags; no deployed or hardware profile qualification. |
| Earlier Essentials browser package | Archive SHA-256 `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910` | Same Wasm, exact original Essentials brush asset added before application startup, independent package measurement and full selected matrix rerun. |
| Product target | Blender 5.4 alpha, `94363991e7dcf39e2d70614aa002ab6f67764a5d` | Separate source/fixture inventory, successful native configurations and original C++ execution; no transfer of candidate passes. |

The normalized [earlier Essentials report](../compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/report.json) contains every known case pair and its blockers. The [conversion record](../compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/conversion.json) binds the original reports, manifests, context measurements, process logs and superseded attempts. The [contract](../compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/contract.json), inventory and typed receipts are independently replayable after relocating the checkout. The unchanged [base-package report](../compatibility/evidence/unittest-parity-ledger-5.2-2026-10-23-v2/report.json) remains available with its 512 strict successful pairs.

## Earlier Essentials selected matrix

Native resource-complete discovery identifies 31 original invocations from 30 distinct Python source files. Their different invocation and fixture requirements produce 829 obligations and 827 distinct source-qualified case IDs. Two IDs occur in both original font modes and retain both obligations.

| Observation | Native | Earlier Essentials browser package |
|---|---:|---:|
| Required case obligations | 829 | 829 |
| Cases discovered and executed | 829 | 817 |
| Observed passes | 828 | 605 |
| Assertion failures | 0 | 207 |
| Errors | 0 | 4 |
| Original expected failures | 1 | 1 |
| Missing outcomes | 0 | 12 |
| Observed subtest events | 71 | 57 |

Fourteen native subtests are missing in the browser. There are no unexpected browser subtests. These subtests are events within parent cases, not 14 additional parent cases.

The strict ledger qualifies **516 successful pairs**. It separately records **601 outcome agreements**, including the original expected failure. Outcome agreement does not prove successful whole-invocation execution. In particular, matching pass callbacks inside a failing invocation, or without required host-tool evidence, do not become strict passes.

The new package has four more passing cases, all from the original brush invocation. The latest producer also distinguishes non-assertion subtest exceptions as errors. Consequently the historical base report's 210 recorded failures and five errors become 207 assertion failures and four errors after that classification correction and the four brush repairs. Earlier raw observations are retained without rewriting them.

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
| bl_brush | 4 | 4 | 4 | 0 | 0 | 0 | 4 |
| compositing_node_group | 1 | 1 | 1 | 0 | 0 | 0 | 1 |

## Original mesh drivers outside the frozen unittest matrix

The next source-derived original driver is `bmesh_bevel`, declaration 49 in
the pinned 5.2 inventory. Its complete unchanged `--run-all-tests` invocation
passes all **88 original cases** natively and in Chromium using the measured
Essentials package. Every case has the original `PASSED`, `Mesh Comparison :
Same` and `Mesh Validation : Valid` observations. The case identities,
specification hashes, source locations, original arguments, working directory,
fixture and helper bytes agree. No cases are missing, duplicated or unexpected.
Blender's actual Wasm runtime exit, Chromium process exit and capture process
exit are all zero. See the [paired bevel summary](../compatibility/evidence/bmesh-bevel-browser-essentials-5.2-2026-10-23/summary.json).

This uses the explicit
`original-bmesh-bevel-essentials-chromium-custom-launcher-v2` profile, which
mounts the exact original inputs and runs the original automatic application
main. It preserves the original comparison-enabling full-suite argument;
the upstream single-case debugging argument disables comparison and is not
used for qualification. `BLENDER_TEST_UPDATE` is absent by key presence,
because even an empty or zero-valued variable would enable upstream reference
mutation. The file-preservation observer reads bytes at the original
`Blender quit` output boundary before WasmFS teardown, then separately requires
the actual runtime exit. All earlier sandbox, shutdown and observer failures
remain recorded with their original qualification status.

These 88 pairs are outside the frozen 829-obligation unittest ledger. They
establish the selected original CPU mesh comparisons under this new launcher
and software-adapter profile. They do not establish configured CTest execution,
the package's original UI shell, GPU behavior, complete native/browser build
correspondence or whole-application parity. Neither the 829-obligation ledger
nor its 516 strict successful pairs is rewritten to incorporate this result.

The complete original `operators` driver adds a separately recorded
105-case native/browser comparison on the same package. Native passes all
105; the browser observes **103 passes and two failures**. Both
`IcosphereFill` and `IcosphereFillUseBeautyFalse` report the original
`The edge topology is different` result while retaining `Mesh Validation :
Valid`. Their source, helper, fixture, original full-suite arguments and
working directory are unchanged, and all 105 names execute exactly once.
Blender's actual runtime exit is 1, Chromium exits 0, and the capture process
correctly returns 1. The whole-invocation gate therefore qualifies zero
successful pairs for this driver. The [operators summary](../compatibility/evidence/mesh-operators-browser-essentials-5.2-2026-10-23/summary.json)
retains all individual outcomes and exact case identities.

The [bounded failure triage](../compatibility/evidence/mesh-operators-browser-essentials-5.2-2026-10-23/FAILURE_TRIAGE.md)
binds the original fill, triangle-fill, scanfill, sorting and mesh-comparison
source paths to the exact 5.2 archive. Both beauty settings fail, so the shared
initial triangulation and comparison paths are candidates for diagnosis.
No runtime geometry arrays or internal sort decisions were captured in this
qualification, and no numerical, ordering or comparator cause is claimed.
The original tests and reference meshes remain unchanged.

The [independent mesh-driver review](../compatibility/evidence/original-mesh-browser-independent-review-5.2-2026-10-23/report.json)
checks both complete invocations, 78 evidence identities, launcher derivations,
original case/specification mappings, event order, actual process exits and
the retained source triage. It adds zero executions or case passes.

The [next-invocation audit](../compatibility/evidence/original-next-invocations-5.2-2026-10-23/proposed-next-invocations.json)
retains all 101 declarations previously unexpanded by the unittest adapter
and details eight candidates with their original source and fixture
requirements. Static declarations and proposed case counts do not count as
runtime execution or successful cases.

## Repairs and separate diagnostic evidence

### Original brush assets

The base browser package omitted the Essentials brush library required by the original `bl_brush` invocation. A separately identified package augmentation appends the exact original `essentials_brushes-mesh_sculpt.blend` bytes and the required preload metadata before Blender starts. The verifier checks the base archive, every unchanged file, unchanged Wasm, existing data prefix, added LFS object, and the only permitted loader edits. It does not rewrite the source-build receipt to claim the base build contained the asset.

On the augmented archive `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910`, **all four original brush cases pass**, with zero failures or skips. The [first repaired qualification](../compatibility/evidence/brush-package-overlay-5.2-2026-10-23/bl_brush-local-server/qualification.json) remains separate from the four failures in the original base matrix. The complete selected source plan and explicit resource retries were then executed again on this package. Its current 516 strict pairs come from those new observations. A sandbox-denied server-start attempt is retained separately and executed zero Blender cases.

### Font rendering and the original image comparator

Both complete browser font modes now receive the exact original fonts and reference images. Their 207 image tests reach the original image comparison code, then fail because the browser invocation has no executable `IDIFF_BIN`. A read-only observer captures the already-generated output PNGs from the original failure traceback before temporary-file cleanup. It preserves every original failed outcome.

A separate host-assisted diagnostic executes the exact source-derived OpenImageIO `idiff` command, arguments and tolerances against those browser PNGs and original references. **All 207 images satisfy the original acceptance predicate:** 80 BUFFER and 127 VFONT. All 80 BUFFER outputs are byte-identical to their reference PNGs. VFONT has 56 comparator exits of 0 and 71 exits of 1; the pinned original test explicitly accepts both. Exit 2, other exits and timeouts cannot pass.

This establishes the selected image comparisons under that host-assisted diagnostic on the base browser artifact. It does not make the original browser invocations pass, implement general browser subprocess support, qualify unrelated rendering features, or transfer a successful image comparison to a different package. The earlier Essentials package still records all 207 original font assertion failures. See the [per-case oracle evidence](../compatibility/evidence/unittest-font-host-oracle-5.2-2026-10-23/summary.json).

## Remaining demonstrated gaps

### SQLite and codec implementation progress

The optional [SQLite build extension](../patches/browser-sqlite/manifest.json)
now compiles genuine SQLite 3.51.3 and CPython 3.13.13 with `_sqlite3` under the
pinned Emscripten 6.0.5 toolchain. The full CPython dependency recipe completed
at one job in 552.20 seconds. Separate SQLite WebAssembly checks pass in Node
and Chrome, including WAL, concurrent connections, transactions, rollback,
foreign keys and close/reopen behavior. The original disk-hash suite attempted
on standalone CPython still executes zero cases: its unchanged package
initializer requires `bpy`. The later complete Blender rebuild qualifies all 12 original cases, as shown
in the latest source-build section above. Raw attempts are retained in
[database build evidence](../compatibility/evidence/browser-sqlite-build-2026-10-23/).

A separate [Python binding diagnostic](../compatibility/evidence/browser-sqlite-python-validation-2026-10-23/)
also passes with the real `_sqlite3` in Chrome and native Blender's Python.
It exercises parameter binding, callbacks, backup, normal serialization and
the documented rejection of a serialized WAL image. An earlier incorrect
diagnostic precondition failed identically in both environments and remains
preserved. Neither diagnostic supplies original Blender case passes.

The optional [codec build extension](../patches/browser-codecs/manifest.json)
compiles the original pinned WebP, OpenJPEG, AOM and libheif libraries. Its
standalone WebAssembly roundtrip diagnostic observes maximum channel errors of
0 for WebP, 0 for JPEG2000 and 1 for AVIF. These diagnostic criteria are separate
from the original Blender assertions. The complete OIIO dependency recipe also
passes: all 21 dependency recipes exit 0, and its linked Node/Wasm smoke constructs
WebP, JPEG2000, HEIF and DPX readers and writers and confirms AV1 encoder/decoder
availability. OIIO's actual build took 466.232883 seconds at one compile job.
Its [completion evidence](../compatibility/evidence/browser-codecs-5.2-2026-10-23/oiio-build-attempt-6/completion-summary.json)
preserves the generated cache and required options. Blender's own CINEON/DPX
paths, the 80 original ImBuf parent cases and all 57 native ImBuf subtest identities
still require the newly built Blender artifact. Failed attempts and successful
component observations remain separate, with zero additional original Blender
browser case credit from dependency validation.

The source workflow now selects both byte-bound extensions, preserves the
original brush overlay, and reruns the frozen initial invocation matrix plus
resource retries. The later source build raises the strict count from 516 to 528 with its own
original SQLite observations. Its ImBuf invocation remains incomplete.

| Gap | Exact evidence | Required implementation or qualification |
|---|---|---|
| SQLite | All 12 original disk-file hash cases pass on the source-built package. | Preserve this complete invocation on subsequent repaired builds; earlier packages retain their missing cases. |
| Background process and socket support | `BackgroundDownloaderProcessTest.test_start_stop` fails through `multiprocessing.Pipe`, `socketpair`, and the unsupported socket syscall. | Implement the needed browser worker/IPC behavior and preserve the original lifecycle assertions. The seven other pass callbacks do not qualify a failing invocation. |
| AVIF | The earlier Essentials package fails two ImBuf parents in three AVIF subtests. The later source build includes libheif/AOM, but its incomplete ImBuf invocation supplies no final outcomes. | Complete the original invocation on the corrected engine and preserve the exact original AVIF comparisons and tolerance. |
| Missing image formats | The earlier Essentials package lacks 14 conditional format events. The later source build enables the codecs but loses all 57 final subtest observations when ImBuf aborts. | Qualify the signed DPX correction in a complete rebuilt invocation. Require every native parent and subtest identity; component arithmetic checks supply no original test credit. |
| Image-comparator execution | 207 font-image assertions fail at the original missing-tool guard, despite the separate successful host image oracle. | Supply a faithful browser-compatible comparator or a clearly declared supported test-helper execution profile; retain exact original command and acceptance semantics. |
| Documentation subprocess | The first original documentation subtest succeeds; `sphinx_stub_gen` fails when spawning the required Python process. | Implement the required execution facility and dependency closure before claiming the full original invocation passes. |
| Mesh fill topology | Two of 105 original operator cases fail the exact edge-topology comparison on the current package, while all 105 pass natively. | Capture actual evaluated/reference geometry and isolate the divergence in the shared fill or comparator path. Preserve the original topology criterion and rerun the full invocation on any repaired engine. |
| Native expected failure | One NLA case is already marked expected failure upstream and behaves that way in both environments. | Keep it as expected-failure agreement. It cannot count as a demonstrated working feature. |
| Test denominator | Conditional registrations, C++/GTest binaries, UI, render, simulation and custom test drivers are not fully expanded. | Capture actual configured CTest registrations, native runtime leaf identities, fixtures and each applicable browser profile. |

The [full failure triage](ORIGINAL_TEST_FAILURE_TRIAGE.md) preserves exact case IDs, traceback locations, subtest IDs, source hashes, build configuration evidence and original dependency logs. Assertions, thresholds and references were not relaxed to obtain passes.

The [browser worker and IPC contract](../compatibility/evidence/browser-worker-ipc-contract-5.2-2026-10-23/README.md)
now traces the downloader's observed first failure against the actual packaged
Python and original source. Its Pipe/socketpair fallback raises ENOSYS before
any child starts. Later source-inferred blockers include the unavailable
`_posixshmem` and `_posixsubprocess` extensions, the POSIX process launch/reap
path, the missing Python executable, transferable connection handles and real
RX/TX threads in the child. The current semaphore shim recreates local objects
and does not provide shared worker synchronization.

The proposed implementation has three reusable boundaries: an isolated Python
worker spawn backend, ordered synchronous-capable duplex IPC, and actual
child threading/lifecycle handling. The acceptance gate remains the complete
original eight-case downloader invocation, including its unchanged shutdown
limits. The same launch service could support documentation generation only
with the real docutils dependency and coherent RST input and `.pyi` output
visibility. This is a source-bound proposal, with zero new executions or
passes; no process support is claimed as implemented.

## How the implementation prevents false parity

Each obligation binds upstream revision, original registration and invocation, native-discovered leaf ID, input closure, comparison policy, runtime/build context and browser profile. Discovery is independent of browser success. The original scripts run through their unchanged `__main__` entrypoints with original arguments and process isolation. Dynamic test methods, subtests, setup errors, expected failures, skips, original exit behavior and actual process shutdown remain separate observations.

Raw reports are retained before normalization. The normalizer validates their hashes and sizes, source/fixture identities, original argument vectors, host-process command and timestamps, frozen harness snapshots, and the exact execution JSON in the original log. It preserves real exit codes rather than converting a failed invocation into a successful process record. Normalized evidence uses relative, confined paths and survives checkout relocation.

The old facet gate's hash-only evidence acceptance was replaced with typed case-execution receipts that must match the independently selected case, target, profile, run and context. Hash-valid arbitrary or failed JSON is no longer accepted as a feature pass. Both the facet gate and the new test ledger keep `full_feature_parity` false; satisfying a declared test contract would still leave whole-application coverage to be established.

The CI workflow [test-parity-ledger.yml](../.github/workflows/test-parity-ledger.yml) separates infrastructure regressions from the strict original-test gate and independently checks the base, Essentials and source-built codec/SQLite profiles. Valid blocked reports are generated and uploaded; the subsequent strict gate exits unsuccessfully while obligations remain. A green infrastructure job does not claim Blender parity.

The latest local infrastructure run passes **346 tests with zero skips** in 121.485 seconds, including real CMake configuration, dependency integration, patch application, qualification validation and the cache failure regressions. Its prospectively captured [execution receipt](../compatibility/evidence/infrastructure-tests-cache-verified-2026-10-23/execution.json) preserves actual stdout/stderr, process timing, exit status, interpreter and CMake identities. Before/after hashes confirm all 156 selected implementation, workflow and original-preimage files were unchanged during the run. The preceding [337-test run](../compatibility/evidence/infrastructure-tests-codecs-sqlite-2026-10-23/execution.json) and [294-test run](../compatibility/evidence/infrastructure-tests-essentials-2026-10-23/execution.json) remain unchanged. These counts validate the project's testing machinery; they are not added to Blender feature passes.

The published implementation checkpoint is
[`f25e69ed72fed2d31d7d65e657fd6515da4bd792`](https://github.com/596050/blended/commit/f25e69ed72fed2d31d7d65e657fd6515da4bd792).
Its [publication receipt](../compatibility/evidence/checkpoint-publication-f25e69ed72fe-2026-10-23/summary.json)
records independent verification of the exact commit and tree before the
authorized parity branch was advanced. GitHub CI independently passes the
same **346 infrastructure tests with zero skips** in 109.674 seconds.
Both strict original-test gates remain blocked as expected. The Essentials
report has exactly the same bytes and SHA256 as the prior 829-obligation
report, retaining 516 successful pairs and 601 outcome agreements. This
[CI evidence replay](../compatibility/evidence/ci-ledger-f25e69ed72fe-2026-10-23/summary.json)
reexecutes zero original Blender cases.

The new [source-build run](https://github.com/596050/blended/actions/runs/39986612484)
has restored the explicitly selected historical dependency cache and passed
the complete installed-file and source-derived alias verification. Its
reconstruct/build/package step was still running at the last observation on
2026-10-23. The workflow subsequently requires the original brush overlay and
fresh execution of both frozen browser matrices. No completed new engine or
new original-case result is inferred from this running build.

## Product target inventory and configuration

The separate [5.4 source inventory](../compatibility/evidence/source-inventory-2026-10-23/source-inventory-summary.json) retains 10,848 source files, 5,637 heuristic declaration candidates, five unresolved source parses/encodings, and 7,353 candidate fixture paths. The declaration count includes 801 compile-time `static_assert` occurrences and is not a runtime test count. All 30 facet scopes remain incomplete.

Product configuration uses the original source with GTest, GPU render, headed render, GPU backend, GPU draw, GPU compositor and UI test flags enabled, plus strict build options. The startup file, actual GCC minimum, pinned native dependencies, host development packages and required OptiX headers are now resolved. The successful configuration uses GCC 14.2, all 716 original native-library LFS paths, 64 verified Ubuntu packages in an isolated prefix and exact official OptiX 8.0 headers. The original failed attempts and successful configuration remain in [product configuration evidence](../compatibility/evidence/product-configure-2026-10-23/). No feature was disabled to make configuration appear complete.

The first unfiltered CTest capture contains **1,140 registrations** in 212 generated registration files. A separate broader Linux configuration additionally enables mesh-paint tests, Vulkan rendering, Vulkan Storm, Cycles OSL, experimental tests, official Linux release tests and system-Python tests. Its unfiltered capture contains **1,416 registrations**. It shares 1,139 names with the first profile and adds 277 names. One earlier name, `cycles_osl_cpu`, is replaced by the original CMake code's expanded OSL naming; both profiles remain preserved. These counts are commands in two specific configurations, not unique leaf cases or a complete cross-platform denominator. See the [first configured inventory](../compatibility/evidence/product-ctest-configured-2026-10-23/summary.json), [expanded inventory](../compatibility/evidence/product-expanded-config-2026-10-23/summary.json) and [exact name comparison](../compatibility/evidence/product-expanded-config-2026-10-23/configuration-comparison.json).

All **7,353 candidate fixture paths** now pass exact SHA-256 and size verification. This includes 6,715 LFS-backed paths, representing 6,543 unique objects and 880,195,119 unique content bytes, plus 638 regular source-archive files. The downloader retained the original pointer bytes, downloaded duplicate content once, and verified the final files after hydration. The [fixture report](../compatibility/evidence/product-fixture-hydration-2026-10-23/report.json) reports zero unresolved files and zero failed transfers. The [initial source-preservation audit](../compatibility/evidence/product-fixture-hydration-2026-10-23/preserved-source.json) records the unchanged files outside that candidate set before the separately documented asset hydration below.

A [whole-source pointer audit](../compatibility/evidence/product-runtime-asset-audit-2026-10-23/report.json) identified 338 additional original LFS paths outside the fixture candidates, including application datafiles, platform packaging art and the documentation favicon. Those exact paths were subsequently materialized from 297 official LFS objects totaling 8,710,555 unique bytes, with zero failed transfers or replacements. The final [asset and source verification](../compatibility/evidence/product-runtime-asset-hydration-2026-10-23/report.json) rehashes **all 7,053 original source-archive LFS paths** and confirms that **all 13,842 original non-LFS files and the original symlink remain unchanged**. This establishes the original archive's payload availability; dependencies outside that archive and per-invocation runtime resource closure still require verification. No tests, builds or browser passes are inferred from hydration.

The original executables were built through unchanged upstream CMake targets and run through their registered CTest commands, with original GoogleTest entrypoints and leak checks preserved. Across **37 original invocations**, the registered and unfiltered listings and XML agree on **2,016 source-qualified observations: 2,015 passed and one skipped**. No failed, errored, disabled or unexecuted XML cases were observed in this selected batch. These are native reference results, with zero browser cases executed in this product-version batch. The [consolidated native report](../compatibility/evidence/product-native-gtest-2026-10-23/summary.json) binds each listing, original command, executable, source identity and outcome.

| Original target group | CTest invocations | Case observations | Passed | Skipped |
|---|---:|---:|---:|---:|
| `atomic_test` | 1 | 56 | 56 | 0 |
| `guardedalloc_test` | 1 | 6 | 6 | 0 |
| `BLI_test` | 1 | 1,742 | 1,742 | 0 |
| `makesdna_test` | 1 | 5 | 5 | 0 |
| `shader_tool_test` | 1 | 62 | 61 | 1 |
| Original LibMV targets | 32 | 145 | 145 | 0 |
| `cycles_test`, original registered filter | 1 | 216 | 216 | 0 |

The new [Cycles reference](../compatibility/evidence/product-native-cycles-2026-10-23/summary.json)
adds the original `cycles_test` target. Its unchanged build completed in
1,072.17 seconds at one job. The first execution failed to load `libImath.so.30`
and remains preserved with zero executed cases. Staging the exact original
shared-library payloads in the configured runtime directory allowed the
unchanged registered CTest command to pass all 216 selected cases. The prior
batch and this registered result have disjoint source-qualified identities:
38 original invocations now contain 2,232 observations, 2,231 passes and one skip.

The executable's unfiltered listing exposes 242 cases. A separately recorded
whole-executable run passes all 242, including 26 identities omitted by the
upstream registration filter: seven `util_half`, seven `util_half_avx2` and
twelve `util_avx2` cases. The source registration scanner misses tests supplied
through included headers. The exact [case reconciliation](../compatibility/evidence/product-native-cycles-2026-10-23/additional-case-reconciliation.json)
retains those 26 separately from the registered 216. Counting only those
additional identities yields 2,258 distinct native observations, 2,257 passes
and one skip across the selected product references. No browser product cases
are inferred, and the configured registration count is not a complete leaf count.

`shader_tool.MatrixConstructors` retains its original non-Apple platform skip and is not counted as a passing assertion. One of the 32 LibMV invocations, `libmv_resect`, has empty registered and unfiltered listings and zero XML cases because the pinned upstream test body is inside `#if 0`. Its process exit is zero, its empty-listing blocker remains visible, and it contributes zero case passes.

The BLI runtime list contains two different original tests named `stack.Peek`. The inventory now preserves both as ambiguous observations until original GoogleTest XML source locations resolve them. Both file/line identities were checked against the pinned source archive, producing separate source-qualified case IDs. Two original LibMV tests named `KltRegionTracker.Track` are likewise kept distinct by their declaration files. The earlier BLI adapter rejection is retained with zero executed cases. Neither listing order nor a deduplicated name is accepted as a one-to-one case identity.

Independent reviews reconcile the [first five native suites](../compatibility/evidence/product-native-independent-review-2026-10-23/report.json) and [all LibMV captures plus the combined totals](../compatibility/evidence/product-native-libmv-independent-review-2026-10-23/report.json). The combined review checks 707 bound input files and 147 original source files, independently recomputes all 2,016 source-qualified identities and finds no repeated identity or count discrepancy. The reviews execute no additional original tests and add no passes.

The expanded configuration's original `script_validate_on_system_python` driver also passes after its missing `setuptools` dependency was supplied through a verified private package prefix. Its original interpreter, command and test source were retained, as was the first failed attempt. This is [one native CTest driver result](../compatibility/evidence/product-system-python-retry-2026-10-23/system-python-execution.json), with no inferred leaf count and no browser pass; it is not added to the 2,016 C++ observations.

## Reproduce the evidence checks

From the repository root, with Python and CMake installed:

```bash
python3 tools/prepare_site.py
python3 -m unittest discover -s tests -q
python3 tools/test_parity_ledger.py \
  --contract compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/contract.json \
  --inventory compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/inventory.json \
  --executions compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23/executions.json \
  --evidence-root compatibility/evidence/unittest-parity-ledger-essentials-5.2-2026-10-23 \
  --output /tmp/blended-strict-parity-report.json
```

The strict ledger's expected current exit is **1**, meaning a valid blocked gate. Exit 2 means malformed or mismatched evidence. `--report-only` changes the command's reporting exit behavior; it does not change the recorded gate or parity claims. This replay verifies recorded evidence and does not rerun Blender.

See [original invocation reproduction](ORIGINAL_UNITTEST_COHORTS.md) for actual native/browser execution and [matrix normalization](UNITTEST_MATRIX_LEDGER.md) for rebuilding the normalized record from the complete initial plan and explicit resource retries. Choose fresh output directories and retain earlier attempts.
