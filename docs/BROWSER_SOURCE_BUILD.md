# Rebuilding and testing the browser engine

The source programme uses one pinned Blender engine and keeps build success,
runtime test success and full application parity as separate gates. The current
entry point builds a new development artifact. It does not reproduce the
previously downloaded gessa v0.1.1 release.

## Exact inputs

| Input | Identity |
|---|---|
| Blender reference | `fbe6228777e7d9afefcd61a413844e790ae75db7` |
| Port source | `0e02e84b2bc5d9b27a6dc6e275443292f781fbad` |
| Canonical source patch SHA-256 | `04ba2e6ba8a04ef37bdaf879b10a135736f07114597a908bbbdea8bba244193c` |
| Emscripten | 6.0.5, compiler `1db513782be24469589d7cb8a1f1834e9a33f271` |
| Browser build profile | `BLENDER_WEB_WASM_SPLIT_MODE=OFF`, `WITH_BUILDINFO=ON` |
| Explicit numerical patchset | `blender-5.2.0-web-numerics-v1`, recorded separately from the canonical port patch |

The published v0.1.1 artifact uses port source
`cc22090b88da63cc617d48b218f4945175928844`. Its canonical patch has a different
digest. The two artifacts and their results must remain distinguishable.

The final product target remains Blender
`94363991e7dcf39e2d70614aa002ab6f67764a5d`, which identifies as 5.4.0 alpha.
Qualifying this 5.2 development build is a baseline milestone, not the version
migration or application-wide acceptance.

## Build entry point

The [source workflow](../.github/workflows/browser-source-build.yml) uses the
standard Ubuntu 24.04 GitHub Actions runner, Python 3.13.13 and two compilation
jobs. It starts on changes to the build entry point or workflow in a `parity/**`
branch. It has a bounded 350-minute job timeout and retains stage receipts on
failure. No paid runner or external build service is configured.

After installing the host prerequisites specified in the workflow, run:

```sh
python3 tools/rebuild_browser_port.py \
  --work-dir .cache/browser-source \
  --output evidence/browser-source-build \
  --jobs 2 \
  --numeric-patchset patches/browser-numerics/manifest.json
```

The stages are:

1. Fetch the exact port and official Blender commits and verify the canonical
   patch's digest and byte count before applying it.
2. Install the exact Emscripten SDK and hash-verified host Python build tools.
   Verify and apply the explicitly selected numerical patches, then rebuild
   both required libc variants in a cache isolated by the manifest digest.
3. Fetch the pinned Dawn dependency closure and run the port's dependency
   recipes, including Python, NumPy, OpenSubdiv and OpenUSD.
4. Build native code generators and locale files, then configure the browser
   engine with the port's existing feature profile.
5. Generate Blender's build-info header, compile the actual `blender_browser`
   target and package its shell and engine files.

Use `--stop-after source`, `toolchain`, `dependencies` or `configure` to
investigate a stage. These exits produce a `partial` receipt and never a
`built` result. A zero exit from a source-only reconstruction does not mean
the engine compiled.

The runner checks the configured feature cache and refuses to continue if a
required enabled feature disappears. The source port already disables some
desktop features; those remain explicit in the receipt. The runner does not
resolve portability failures by silently disabling additional features.

Omit `--numeric-patchset` to rebuild the original canonical port baseline.
Patched and unpatched build receipts remain distinguishable. CI selects the
reviewed numerical patchset explicitly, and a newer source commit supersedes
an older source build to avoid compiling both full engines unnecessarily.

The OFF development profile avoids the port's hardware-dependent shipping
capture process. CAPTURE/APPLY shipping qualification and real hardware testing
remain separate requirements.

## Build inputs and reproducibility limits

`source-build.json` records the source pins, patch digest, compiler identity,
configuration, dependency recipe identities, stage commands and results, output
artifact digest and current limitations. Supporting files retain package
versions, download hashes, dependency harvest hashes, compile commands and logs.

The source and toolchain commits are pinned. Host Python tools use explicit
versions and wheel hashes. The NumPy recipe's floating host-tool installation
is replaced with that same requirements file, without replacing its embedded
Python or NumPy version. Ninja 1.13.0 is used from a verified wheel; the port's
runbook names 1.13.1. This difference is recorded rather than hidden.

Some dependency recipes provide MD5 checksums. Newly observed SHA-256 values
document the downloaded bytes, but do not constitute an independently approved
SHA-256 lock. Ubuntu package revisions are inventoried instead of frozen into
a hermetic operating-system image. Bitwise reproducibility is not established
by a single build.

The [numerical patch manifest](../patches/browser-numerics/manifest.json) binds
each extra patch to its component, exact source path, original file hash,
resulting file hash and patch-file hash. It corrects the tiny-input `acosf`
rounding branch and selects Eigen's existing SSE2 inverse implementation only
for its matrix translation unit. It preserves the float API and original
Blender test criteria. These changes target the named official Linux x64
reference; they are not a claim about every native architecture.

The independent WebAssembly kernel experiments reproduced the old browser
results and matched the native results after these changes. Fresh `libc` and
`libc-mt` builds were also linked and executed in normal and proxied-thread
WebAssembly. These regressions justify testing the patches in the full engine;
they do not establish that the application has passed its suites.

Caches preserve dependency/compiler progress and are keyed to the entry-point
bytes. A cache hit is an optimization, not acceptance evidence. Each run still
produces a fresh receipt and verifies the inputs it uses.

## Qualify the exact output

On a successful build, a separate CI job downloads that run's artifact and
executes:

```sh
python3 tools/probe_browser_port.py \
  --source-build-receipt source-build/source-build.json \
  --asset source-build/blender-source-development.tar.gz \
  --output evidence/source-development-qualification \
  --timeout 240
```

The probe requires the declared source pins, canonical patch, development
profile, build metadata flag and exact artifact digest/size. It then requires
the running engine to report the expected Blender version and upstream build
hash. A matching receipt alone is not a runtime identity check or an independent
recompile.

For a patched artifact it additionally checks the manifest digest, every patch
identity, the applied flag and the exact compiler identity. Unknown or partial
patch declarations cannot inherit the unpatched baseline's identity.

Both complete upstream files, `bl_pyapi_mathutils.py` and `bl_pyapi_bmesh.py`,
are fetched from the exact reference and verified by digest before execution.
Their assertions and tolerances remain unchanged. The probe preserves missing
tests, failures, errors, skips and subtests. It cannot obtain a pass merely
because a page boots or native Blender passes the same tests.

The current CI browser requests a software GPU. Its observed adapter is recorded
separately, and the probe does not claim real hardware or deployed-URL coverage.
Even a passing selected-suite result does not complete any facet's entire
feature inventory.

Small build and qualification receipts are appended to the
`browser-source-evidence` branch under the source commit and run ID. Failed
stage logs remain identifiable even when a later run succeeds. Binary output
and complete build logs stay in the run artifacts; they are not committed to
the evidence branch.

## Diagnose failures without changing the acceptance tests

The [numeric diagnostic workflow](../.github/workflows/browser-numeric-diagnostics.yml)
runs an identical separate payload on the checksum-verified official native
artifact and the pinned published browser release. It covers all 145 vector
inputs and both complex screw branches, including operations that the original
test does not reach after an earlier assertion fails.

The payload preserves float bit patterns, input parameters, coordinate and
topology observations, and original comparison outcomes as diagnostic data.
The comparison requires matching payload and input identities. Mesh element
comparisons additionally require matching topology signatures.

Every report states `diagnostic_only: true`,
`acceptance_status: "not_evaluated"` and `full_parity: false`. Unknown build
identity and runtime transport errors remain blockers even when useful numeric
observations were recovered. Diagnostics help select an engine fix; only
rerunning the unchanged suites on the rebuilt artifact can qualify that fix.

## Expand one fixed cohort at a time

The opt-in `data52` cohort adds the original ID-management, RNA-accessor and
custom-property modules. Its [native inventory](../compatibility/candidate-suites/data-5.2.json)
requires 48 named cases: 8, 1 and 39 respectively. All five conditional NumPy
cases are mandatory. Browser discovery cannot shrink that denominator.

```sh
python3 tools/probe_native_reference.py \
  --cohort data52 --output evidence/data-native
python3 tools/probe_browser_port.py \
  --cohort data52 --output evidence/data-browser
```

The [data-cohort workflow](../.github/workflows/browser-data-parity.yml) runs
both artifacts independently and preserves their receipts on
`candidate-data-evidence`. Original source bytes and assertions are retained.
The first complete run passed all 48 cases in both engines; the browser's
unknown build hash remains a provenance blocker.
Only the module prefix is normalized when matching test IDs. The adapter calls
unittest's base ID method because Blender's custom-property tests use an `id`
property for the datablock under test. This reporting correction does not
change that property or the tested Blender behavior.

The default remains the original 192 numerical cases. The additional cohort
provides selected `scene_data` and `python_api` evidence; it does not complete
either facet. The separate `.blend` I/O script uses a custom driver and is not
counted among these 48 cases.

### Original blend-file driver and file exchange

The opt-in `blendio52` cohort has its own [four-case native inventory](../compatibility/candidate-suites/blendio-5.2.json).
It transports the complete unchanged `bl_blendfile_io.py` and
`bl_blendfile_utils.py` files and invokes the original `__main__` block. The
adapter observes CPython setup/body/teardown start, return and unwind events.
It does not replace the helper with a unittest loader or infer four passes
from a module exit code.

The original CTest registration supplies `--background` through
[`tests/CMakeLists.txt`](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/CMakeLists.txt).
The browser adapter now passes the same execution mode through the unchanged
shell's `__BW_ARGS` hook and records `bpy.app.background` from inside Blender.
Qualification fails if this required mode is missing or false. This runs
Blender's actual background path; no operator poll or context is overridden.

The [first windowed browser run](https://github.com/596050/blended/actions/runs/39848817344)
is preserved as a failed baseline: 3/4 original methods passed, then
`TestIdRuntimeTag.test_linking` failed at `bpy.ops.wm.link.poll()`.
Both engines transferred six files successfully, but the exchange gate refused
all four comparisons because the browser's original driver had failed.
Upstream `wm_files.cc` deliberately clears the active window after file loading
when `G.background` is false. The native invocation already used background
mode. The existing failure is not reclassified as a pass.

The [background follow-up](https://github.com/596050/blended/actions/runs/39849706149)
observed `bpy.app.background=true`, all four original methods passing and
runtime exit code 0. It then failed file transfer at the first `FS.lstat`:
normal runtime teardown had already removed the temporary WasmFS files.
The adapter now publishes the original test report and waits at most 60 seconds
after the original driver and monitoring have ended. The host copies and hashes
the outputs, atomically writes an acknowledgement bound to the run token and
complete file inventory, then observes normal runtime exit. The acknowledgement
uses the pinned SDK's numeric exclusive-create flags 193 with bounded
`FS.open/write/close/rename`; its WasmFS API does not accept a `wx` mode string
or a flags option on `FS.writeFile`. A failed, altered or missing acknowledgement
cannot qualify. Fresh CI must verify this transport correction.

```sh
python3 tools/probe_native_reference.py \
  --cohort blendio52 --output evidence/io-native
python3 tools/probe_browser_port.py \
  --cohort blendio52 --output evidence/io-browser
python3 tools/probe_blendfile_exchange.py \
  --native-evidence evidence/io-native \
  --browser-evidence evidence/io-browser \
  --output evidence/io-exchange
```

The probes copy generated files into each evidence directory's `blendfiles/`
folder. The browser copy checks file size and uses the engine's exported
`FS.open/read/close` with a bounded read and an extra-byte EOF check. Every copied
file must match the byte count and SHA256 reported inside Blender. The native
adapter has passed all four methods and verified all six transferred outputs.
The selected original assertions, file transfer and native exchange have
separate results.

The [IO workflow](../.github/workflows/browser-io-parity.yml) then opens the four
current `.blend` files from both producers in fresh, checksum-verified native
Blender processes. It compares the full ID/user/dependency tuple from the
unchanged upstream helper, retaining differences instead of normalizing them
away. Individual file hashes identify the tested bytes; native and browser
files are not required to be byte-identical. Missing or altered files cannot
reduce the fixed four-file exchange inventory.

This first exchange gate requires the independently pinned v0.1.1 browser
archive and its declared source revision. A development artifact needs an
explicitly supplied, separately validated build receipt before it can enter
this exchange gate; matching self-declared hashes alone is insufficient.

This exchange covers the final current files only. Two original methods
overwrite the same filename, so it does not preserve both method-end versions.
The current native files contain no live libraries; persistent external-library
resolution requires another explicit workflow. Backups remain output artifacts
and are excluded from the four-file exchange denominator. Unknown browser
provenance continues to block qualification even when execution and semantic
comparisons pass. Small receipts and logs are retained on `candidate-io-evidence`;
generated binary files remain run artifacts.

## Current acceptance boundary

The source reconstruction and native reference have been exercised. The
published browser release still fails two of the 192 selected top-level tests
and reports an unknown source build hash. Source compilation, a verified
development runtime and fixes to those divergences must be established through
their own fresh receipts.

The [parity programme](BROWSER_PARITY_PROGRAM.md) defines the remaining facet,
fixture, workflow, hardware, deployment and version-migration requirements.
The strict application gate remains blocked while its inventory is incomplete.
