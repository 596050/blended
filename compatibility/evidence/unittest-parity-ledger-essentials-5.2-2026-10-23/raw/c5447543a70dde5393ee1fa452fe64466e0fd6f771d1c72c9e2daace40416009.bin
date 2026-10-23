# Blender 5.2 browser numerical corrections

This patchset targets the Gessa source reconstruction at the exact Blender
5.2.0 commit recorded in `manifest.json`. Its native reference is the official
Linux x64 release compiled for x86-64-v2. It does not establish equivalence with
other native architectures or the separate Blender 5.4 product target.

## Changes

| Patch | Change | Scope |
| --- | --- | --- |
| `0001-emscripten-acosf-small-angle.patch` | Correct the existing `acosf` branch for `abs(x) <= 2^-26` to return the nearest binary32 value of pi/2. | The pinned Emscripten libc source. Float arguments, clamping callers and float results remain intact. Other branches, including the negative-one endpoint, are unchanged. |
| `0002-eigen-matrix-wasm-sse2.patch` | Compile `intern/eigen/intern/matrix.cc` with `-msimd128 -msse2`, selecting Eigen's existing block-adjugate inverse kernel. | This translation unit only. The library propagates `-msimd128` to the final link. No inverse implementation is copied and no BMesh operation is changed. |

The manifest binds both source files before and after patching, each patch's
bytes, the native and port commits, and the compiler identity. Apply these
patches separately from the upstream port's canonical patch. Record both patch
identities in the source-build receipt.

## Cache requirements

Changing Emscripten's `acosf.c` alone does not replace an already-built libc.
Apply the SDK patch before compiling dependencies. Select an `EM_CACHE` directory
whose name includes the SHA-256 of `manifest.json`, and force these variants to
rebuild in that namespace:

```sh
embuilder --force build libc libc-mt
```

Keep that same `EM_CACHE` for dependency builds, Blender compilation and the
final link. The source-build receipt must record the cache namespace and patch
hashes. The demonstrated configuration uses wasm32, ordinary optimized libc and
the pthread libc. Size-optimized libc, LTO, wasm64 and sanitizer variants need
their own build and regression evidence.

The SDK integration experiment rebuilt both archives and traced the direct
`acosf` symbol to the new `libc.a(acosf.o)` and `libc-mt.a(acosf.o)`. Its pthread
program also used `PROXY_TO_PTHREAD`. This verifies the library replacement
mechanism; it does not replace Blender's original tests.

## Reproduce the kernel regressions

Activate the manifest's exact Emscripten SDK and provide Eigen headers from the
manifest's pinned Blender dependency. The probe checks the relevant Eigen
header hashes as well as the compiler and SDK math-source identity.

```sh
python patches/browser-numerics/probes/run.py \
  --emsdk-root /path/to/emsdk \
  --eigen-include /path/to/eigen/include \
  --cache /path/to/cache-containing-manifest-sha256 \
  --output /path/to/numeric-probe-results \
  --expect-libc patched
```

For an original SDK and separate original cache, use `--expect-libc original`.
The probe retains the original imported math function alongside the candidate
and the actual libc call. It records complete commands, link provenance, output,
source hashes and generated WebAssembly hashes. No Blender source tests,
assertions, tolerances or reference files are changed.

The checked observations are:

- All 144 nonzero vector inputs from the original orthogonal test. The original
  Wasm libc produces the observed lower angle for 136 inputs. The corrected
  actual libc, in both normal and pthread configurations, matches the native
  angle bits for all 144 inputs. These are numerical observations inside one
  upstream parent test, not 144 acceptance tests.
- All 49 constructed screw vertex positions. The original scalar inverse
  reproduces the browser coordinates. Selecting the existing Eigen SIMD inverse
  reproduces the native coordinate bits for all 49 positions, with both tested
  matrix-product association orders.

The transform probe isolates arithmetic and does not construct BMesh topology.
The independently observed mesh has matching edge connectivity and oriented
face cycles after exact construction-based matching, while element iteration
order can differ. The conservative transport still refuses index-based edge
pairing when its topology signatures differ.

## Acceptance status

Kernel regressions support rebuilding the actual engine with these patches.
They do not make the two original failing Blender parent tests pass. A rebuilt,
identified browser engine must run the unchanged complete mathutils and BMesh
suites, followed by the remaining facet suites. The released browser artifact's
unknown build identity and observed WebGPU errors remain independent gaps.
