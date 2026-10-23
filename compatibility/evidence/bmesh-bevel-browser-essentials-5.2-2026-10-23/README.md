# Original bevel driver in the browser

The completed `attempt-03-v2-elevated` invocation passes all **88 original `bmesh_bevel` cases**, paired to the same 88 cases in the successful native reference. Each browser case prints the original `PASSED` result together with `Mesh Comparison : Same` and `Mesh Validation : Valid`. Blender's actual Emscripten runtime exit, the Chromium process exit, and the capture process exit are all zero. No missing, duplicated, or unexpected original case names remain.

This is a separately identified custom mesh-driver execution. It is outside the frozen 829-case unittest matrix and its ledger. The retained original CMake declaration is source-derived; this directory does not claim a configured CTest execution or whole-application parity.

## Exact input and launcher scope

The original source commit is `fbe6228777e7d9afefcd61a413844e790ae75db7`. The unchanged declaration is `tests/python/CMakeLists.txt:517`, catalog index 49. The original Python driver, `modules/mesh_test.py` helper, and `bevel_regression.blend` input/reference fixture are retained in the adjacent native evidence directory. Their exact identities are included in every attempt. The browser fixture is 2,387,547 bytes with SHA256 `dad2aa2c02cb6ceb9e025b729e1886a95b3d744c10dce56503adbd15ec312771`.

The browser uses the verified Essentials package with SHA256 `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910`. The runner independently verifies its actual archive against the base artifact and original package-overlay contract before extracting it. The JavaScript, Wasm, and preload data are unchanged extracted package members. The existing engine is not rebuilt.

`launcher-v2.html` and `launcher-v2.js` form a new evidence-only launcher, identified as `original-bmesh-bevel-essentials-chromium-custom-launcher-v2`. They replace the package's UI entry point for this invocation. The original automatic application main is retained. The launcher supplies the original native executable name through Emscripten `thisProgram` and the remaining original argument array through `Module.arguments`. Thus the full observed argument vector matches the native command, while the executable code is explicitly the measured Wasm engine, not the native executable named in `argv[0]`.

The launcher mounts the three original files at their original absolute paths through the engine's preload APIs before main. It verifies each download with SHA256, compares every mounted byte with that verified input before main, changes to the exact original native working directory, and leaves the complete `--run-all-tests` tail intact. That branch enables the original mesh comparison oracle. `BLENDER_TEST_UPDATE` and `BLENDER_VERBOSE` are absent by key presence; an empty or zero-valued update variable would fail the gate. No Python wrapper, altered assertion, custom tolerance, case filter, reference replacement, or test update is used.

The browser environment includes the original package's `/bw` resource paths and `/projects` user resource paths, plus the same four numeric-library thread-limit environment requests as the native invocation. Browser and native platform environments remain distinct and are recorded. Chromium 155.0.8059.39 runs headlessly with the retained software GPU flags; these CPU mesh results do not qualify GPU hardware or UI behavior.

## Preserved attempts

| Attempt | Original observed passes | Whole invocation qualification | Reason |
| --- | ---: | --- | --- |
| `attempt-01` | 0 | Blocked | Restricted sandbox denied creation of the local loopback socket before browser launch. |
| `attempt-02-elevated` | 88 | Unqualified observer attempt | All original oracles and runtime exit passed, but the extra file readback was attempted after Emscripten destroyed WasmFS. Its failed receipt and original observer files are preserved. |
| `attempt-03-v2-elevated` | 88 | Passed | Versioned observer captures unchanged file bytes at the original `Blender quit` stdout boundary, after all original case results and before runtime teardown; actual runtime, Chromium, and capture process exits are zero. |

The v2 file-preservation observation is explicitly at the original quit boundary, not at `onExit`. The runner verifies its event sequence follows every original case/result event and precedes the one real runtime exit. This repairs observation timing without changing test execution or weakening any original oracle. `prepare-observer-v2.py` records the exact derivation of the versioned observer files. V1 sources and receipts were not overwritten.

## Reviewable evidence

- `summary.json` pairs every runtime-observed case with its native result, original source path and line, source hash, and original specification hash. Names alone are not the global identity.
- `attempt-03-v2-elevated/execution.json` binds all input, artifact, launcher, browser, argument, environment, file-observation, event-stream, and runtime results. SHA256: `0391eb0a049f23c5f636799abf2328ed4a64a850add6f1f793778444a0f8c217`.
- `attempt-03-v2-elevated-host/execution.json` binds the actual capture process exit to that exact child receipt. SHA256: `b5fc1c46c311d90db13f340c16b650d802395e2c013d55ec3f9a0c782da381ed`.
- `original-stdout.log` and `original-stderr.log` retain the engine's original print callback strings as UTF-8 lines. `launcher-events.jsonl` and `browser-console.jsonl` preserve the complete corresponding event and console streams. Chromium's original process byte logs are separate.
- The successful native summary remains at `../bmesh-bevel-source-native-elevated-5.2-2026-10-23/summary.json`, SHA256 `54b9c3e3bfe5504dc151ed534dd7039fec0d85a15315ac61e0860002b5ee949d`.

The completed browser interval, including application loading, is 10.138022 seconds. Its 180-second limit was not reached. This single invocation is not a performance benchmark.

The original browser warning that an external Python executable is unavailable and Chromium's software presentation diagnostics remain in the logs. The original mesh comparisons pass despite those diagnostics. They do not establish subprocess, rendering, or whole-application support. Both native and browser source-build correspondence remain explicitly unverified beyond the retained release/package identities and observed build information.

For another independent attempt, use `capture-process-v2.py` with a new, unused attempt directory name. It fails if evidence would be overwritten. The original source closure and exact package inputs must remain available at their recorded paths.
