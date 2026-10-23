# Original mesh operators invocation in the browser

The complete original `operators` invocation executes all **105 original cases** on the existing Essentials browser package. **103 cases pass and two fail**. `IcosphereFill` and `IcosphereFillUseBeautyFalse` both report the original comparator message **`The edge topology is different`**, while their original mesh validation result is `Valid`. The corresponding unchanged native invocation passes all 105 cases.

Blender returns the original expected Python-failure exit code 1. Chromium exits zero, and the capture process returns 1 because the whole original invocation failed. Consequently this directory contributes **zero qualified passes under the whole-invocation gate**. Its 103 individual pass observations remain visible. The existing 829-case unittest matrix and ledger are unchanged.

## Scope and preserved inputs

This is a custom original mesh driver, not a unittest discovery result. Its original source-derived CMake declaration is `tests/python/CMakeLists.txt:703`, catalog index 74, at commit `fbe6228777e7d9afefcd61a413844e790ae75db7`. No configured CTest execution is claimed.

The successful native source closure and runtime reference are in `../mesh-operators-source-native-5.2-2026-10-23`. Original input identities are:

| Input | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/python/operators.py` | 39,415 | `a9e934a9281b8a7746d414e868b42a9dd93bf163b99b8add98ace8bd1fa4983f` |
| `tests/python/modules/mesh_test.py` | 40,007 | `fd764b05f86479f45eb52731eb2009b7321dfa74a258c4886c4c73083bf3ee5e` |
| `tests/files/modeling/operators.blend` | 4,028,858 | `345857f0185fc38799d26e671e88ed06bf7754163c0ea58b4b8475c57908f9cc` |

The fixture bytes independently match the exact 5.2 source archive's original LFS pointer. The browser verifies all three downloads with SHA256 and every mounted byte before main and at the original `Blender quit` stdout boundary. That boundary follows all original case results and precedes Emscripten runtime teardown. The original host input files also remain unchanged.

The exact native argument vector and working directory are preserved in WasmFS, including the original `--run-all-tests` tail that enables comparisons. `BLENDER_TEST_UPDATE` and `BLENDER_VERBOSE` are absent by key presence. The original `seed(0)` call is unchanged. No custom tolerance, index-order relaxation, case filter, oracle update, Python wrapper, or replacement assertion is used.

## Separate launcher and package identity

The engine archive is the existing verified Essentials package, SHA256 `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910`. The runner revalidates its original package augmentation and actual engine members. This execution does not recompile the engine.

The new profile is `original-mesh-operators-essentials-chromium-custom-launcher-v2`. Its HTML and JavaScript launcher are distinct from the package's UI shell. It uses the reviewed bevel v2 transport with only frozen native-input bindings and observer labels changed. `prepare-launcher.py` and `launcher-derivation.json` record and bind every exact source-file edit; the original upstream test files are not edited.

The launcher provides the original executable-name string through Emscripten `thisProgram` and the original remaining arguments through `Module.arguments`. The observed complete argument vector is identical to native, while the actual executed code is explicitly the measured Wasm engine. The original module's automatic main is used once. The browser environment and actual Chromium process command are retained in the prospective receipt. The requested software GPU profile does not qualify rendering hardware.

## Evidence and outcome

- `summary.json` reconciles each of the 105 runtime names to the native observation and exact source path, line, source hash, and specification hash. It preserves both failed original cases and the zero whole-invocation qualification count.
- `attempt-01-elevated/execution.json`: 284,744 bytes, SHA256 `81690d892a6fd3f5323ddb3d5666323fdfcce54c4b276c0566688cafe20770bb`.
- `attempt-01-elevated-host/execution.json`: SHA256 `cef8c30ac2898489afd8dfeff3122e74357932519f0e3a5560a6eb915b4350de`.
- `attempt-01-elevated/original-stdout.log`: SHA256 `fdf9ccc223a331256de21e13d7ad96f827d760a7ce67d4438637d849b75b2706`.
- `attempt-01-elevated/original-stderr.log`: SHA256 `5c8b8e83e01c222f23b7deae790190ac68632e1f1d1861c11d546d3a9442e25b`.
- `FAILURE_TRIAGE.md` maps the failures to the original test, fill, scanfill, and comparator sources. `source-basis.json` binds byte-exact source copies to the complete pinned archive.

The browser interval, including loading, is 12.855256 seconds. The 180-second limit is not reached. Every transport, input, source-preservation, argument, event-stream, and process observation gate passes. The two failing checks are the original mesh-oracle success requirement and the required zero Blender exit. The original `RunTest.run_all_tests()` exception and Python exit are retained in stderr.

The current evidence establishes the two original comparison failures. It does not yet establish a causal source defect, a floating-point explanation, or whether the divergence lies in generated mesh topology, the comparator, or both. Neither expected meshes nor tests were changed to make the result pass. No production patch is made.
