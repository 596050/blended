# Original Blender 5.2 browser codec preparation

This evidence supports an optional source/build patch for the original CINEON, DPX, JPEG2000, WebP and AVIF implementations. It records **zero new Blender executions or application passes**. The next application acceptance step is a newly rebuilt browser running the unchanged original ImBuf invocation, including its complete native subtest inventory.

The immutable completed result is [completed-summary.json](completed-summary.json), generated from the retained raw receipts by [freeze_completed_summary.py](freeze_completed_summary.py). The selected patchset is [manifest.json](../../../patches/browser-codecs/manifest.json), SHA256 `b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708`.

## What is established

| Check | Recorded result | Evidence |
|---|---|---|
| Original source selection | Exact port commit `0e02e84b2bc5d9b27a6dc6e275443292f781fbad`, Blender commit `fbe6228777e7d9afefcd61a413844e790ae75db7`; source files verified against their Git blob inventories | [source-inputs.json](source-inputs.json), [port-tree.json](port-tree.json), [blender-tree.json](blender-tree.json) |
| Original dependency archives | WebP 1.6.0, OpenJPEG 2.5.3, AOM 3.13.1, libheif 1.20.2 and OIIO 3.1.13.1; original upstream hashes checked, observed SHA256 retained | [dependency-inputs.json](dependency-inputs.json) |
| Codec compilation | Real Emscripten 6.0.5 compilation of WebP, OpenJPEG and AOM; libheif succeeded after the bounded standalone-Embind guard correction | [build-attempt-3/execution.json](build-attempt-3/execution.json), [build-attempt-4/execution.json](build-attempt-4/execution.json) |
| Static package integration | A real CMake consumer imported the codec packages and unchanged Blender Find modules, then linked the Wasm diagnostic | [validation-attempt-1/execution.json](validation-attempt-1/execution.json) |
| Standalone runtime behavior | Node/Wasm WebP and JPEG2000 lossless RGBA round trips had maximum channel error 0; libheif/AOM AVIF encode/decode had observed maximum error 1 | [validation-attempt-1/runtime.log](validation-attempt-1/runtime.log) |
| Patch integrity regressions | Nine regressions passed on the retained earlier `44e3f3` patch snapshot; root infrastructure discovery also includes these tests for the final patch | [validation-attempt-1/patch-regressions.log](validation-attempt-1/patch-regressions.log) |
| Final patch application | Final `b2881d` manifest and all ten exact postimages verified, child process exit 0 | [oiio-build-attempt-5/patch-application.json](oiio-build-attempt-5/patch-application.json), [oiio-build-attempt-5/execution.json](oiio-build-attempt-5/execution.json) |

The standalone runtime receipt remains bound to the earlier manifest. Comparing its retained manifest with the selected final manifest shows that only `scripts/deps/openimageio.sh` changed: the final version validates and preserves OIIO's generated CMake cache after a successful smoke check. All four codec recipes and the package-discovery fragment are unchanged between those manifests.

The successful libheif build used the retained full-context guard patch. The final recipe uses an equivalent zero-context diff to make nested patch whitespace strict. Both require the exact same source postimage SHA256 `12b0d0fe77f06d4fa4861469638c2bb832c22edea9c63e9055567ec7cabb6ff3`. The earlier compile is not relabeled as execution of the final recipe bytes.

## Original application criteria

The [baseline gap](baseline-gap.json) binds the original suite source, native receipt, browser receipt and frozen case manifest. Both runtimes discover 80 parent IDs, but native execution observes 57 subtests while the previous browser artifact observes 43. The missing 14 events cover CINEON, DPX, JPEG2000 and WebP. Three AVIF errors affect two parent cases.

Rebuilt application acceptance requires all 80 original parent IDs and all 57 native subtest IDs, the original invocation, and the unchanged assertions and tolerances. In particular, WebP and JPEG2000 retain zero pixel tolerance, and AVIF retains tolerance 1. The unchanged original test SHA256 is `cc97ac9e6a3d1854d87f3937dd273765b37a4a11322b947bd33ef43c9b92ff4e`. No test selector, assertion, expected outcome or tolerance was changed by this patchset.

## Genuine failures and scope limits

The failed attempts are preserved. Initial codec builds exposed missing host CMake and an SDK environment overriding the caller's isolated cache; those attempts do not qualify the libraries. The subsequent libheif compiler failure involved unused standalone JavaScript binding wrappers, which the static C API recipe now disables through a narrowly checked source guard.

Completed full OIIO attempts failed before reaching OIIO: unavailable download access, a missing Ninja binary, and an SDK cache symlink incompatible with Emscripten's relative system-library paths. Attempt 3 failed during host preflight and has only its actual runner snapshot, not a fabricated child-process receipt. The corrected host tools and real private cache are documented in [oiio-host-tools/measurement.json](oiio-host-tools/measurement.json) and [oiio-sdk-cache-correction.json](oiio-sdk-cache-correction.json).

The active bounded retry is isolated in `oiio-build-attempt-6/`. **Exclude that entire directory from the checkpoint containing this completed summary.** It is the only directory still written by the running validation process. The completed summary deliberately records `oiio_build_qualified: false`; a later checkpoint can append the finished attempt without rewriting this result. The runtime source/build tree is outside this repository.

Full application feature parity remains false. The unchanged original Blender tests against a newly built browser artifact remain the decisive evidence for this application facet.
