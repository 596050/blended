# Original Blender 5.2 image codecs for the browser build

This optional patchset enables the original pinned CINEON, DPX, JPEG2000, WebP and AVIF implementations in the selected browser build. It changes dependency recipes and platform configuration. It does not alter Blender's test source, assertions, selectors, expected results or image tolerances.

The selected port is `gessa-ai/blender-web@0e02e84b2bc5d9b27a6dc6e275443292f781fbad`, based on Blender `fbe6228777e7d9afefcd61a413844e790ae75db7`, with Emscripten 6.0.5. The exact source preimages, patch and resulting files are bound by [manifest.json](manifest.json).

## Build integration

Apply the explicitly reviewed manifest before the outer driver captures its dependency recipe identities:

```sh
python3 patches/browser-codecs/apply.py \
  --port-root /path/to/pinned/blender-web \
  --receipt /path/to/new/codec-application.json \
  --expected-manifest-sha256 REVIEWED_MANIFEST_SHA256
```

The caller verifies the Git source commits and toolchain separately. The helper checks the selected manifest digest, its own identity, the diff, every affected preimage and every resulting file. It accepts an exact already-applied result and rejects mixed, modified or symlinked targets. Its receipt qualifies source preparation only.

Insert `webp`, `openjpeg`, `aom`, and `libheif`, in that order, immediately before `openimageio`. Export a writable build-specific `EM_CACHE`. Set `BLENDED_BUILD_JOBS` to 1 through 4 and bound `EMCC_CORES` in the outer driver. The four new recipes and patched OIIO recipe reconstruct their source/build directories and rebuild unconditionally. Include the selected manifest SHA-256 in the outer dependency cache identity.

After Blender configuration, require all three cache values to be `ON`:

- `WITH_IMAGE_CINEON`
- `WITH_IMAGE_OPENJPEG`
- `WITH_IMAGE_WEBP`

The patched OIIO recipe requires its WebP, OpenJPEG and Libheif packages, embeds the plugins statically, and checks plugin construction plus AV1 encoder/decoder availability in its smoke executable. Before removing its scratch directory, it verifies and preserves the exact generated cache at `lib/wasm/share/blended/openimageio-codecs-CMakeCache.txt`, relative to the port root. Required values are `USE_WEBP=ON`, `USE_OPENJPEG=ON`, `USE_LIBHEIF=ON`, `EMBEDPLUGINS=ON` and `BUILD_SHARED_LIBS=OFF`.

The platform fragment loads the actual WebP, OpenJPEG and libheif config packages before OIIO. OIIO 3.1.13.1's exported static package references those optional codec targets without finding them itself. The fragment also populates Blender's unchanged FindWebP and FindOpenJPEG modules and requires every needed archive, including WebP's component libraries and the HEIF/AOM chain.

## Dependency choices

| Component | Original pinned version | Browser adaptation |
|---|---|---|
| WebP | 1.6.0 | Static libraries, pthreads, portable scalar implementation |
| OpenJPEG | 2.5.3 | Static library with original encoder, decoder and thread support |
| AOM | 3.13.1 | Generic CPU target, original AV1 encoder/decoder and high bit depth; original Blender patch retained |
| libheif | 1.20.2 | Original AOM encoder and decoder embedded statically; dynamic plugin loading disabled |
| OpenImageIO | 3.1.13.1 | Original WebP, JPEG2000, HEIF/AVIF and DPX plugins enabled |

libheif automatically includes standalone JavaScript Embind wrappers when compiling for Emscripten. Those unused wrappers fail under the pinned SDK's raw-pointer binding rules. The small [dependency patch](dependency-patches/libheif-static-c-api.patch) adds an opt-out guard, enabled only by the embedded static C API recipe. It leaves the codec algorithms and C API unchanged. The recipe checks both the original and patched file digest.

## Validation and acceptance boundary

Run the patch integrity regressions with:

```sh
python3 patches/browser-codecs/test_patch.py
```

All four codec libraries have been compiled with the pinned Emscripten compiler. A real CMake consumer resolves their static targets and Blender's unchanged Find modules. The standalone Node/Wasm diagnostic has exercised WebP and JPEG2000 exact RGBA round trips and libheif/AOM AVIF encode/decode. Those checks establish dependency behavior, not Blender application conformance.

The recorded original ImBuf suite has 80 parent cases and 57 native subtest events. The previous browser artifact executed the 80 parents but observed only 43 subtests, silently losing 14 conditional codec events. It also recorded three AVIF errors affecting two parents. The [bound baseline gap](../../compatibility/evidence/browser-codecs-5.2-2026-10-23/baseline-gap.json) preserves the exact IDs and raw receipt identities.

The application acceptance step is a newly rebuilt browser artifact executing the unchanged original invocation, all 80 parent IDs, and all 57 native subtest IDs. Preserve the original zero pixel tolerance for WebP/JPEG2000 and tolerance 1 for AVIF. Successful dependency builds or parent callback counts do not satisfy that obligation. Full application feature parity remains false.

See the [evidence directory](../../compatibility/evidence/browser-codecs-5.2-2026-10-23/) for exact source inputs, genuine build failures, successful dependency compilation, runtime observations, and the full OIIO build attempt.
