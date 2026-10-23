# Original mesh operators, native Blender 5.2

The original full `operators` invocation completed once with actual process exit **0** in **3.82125 seconds**, within the prospective 180-second limit. Its unchanged driver emitted **105 distinct original passes**, each accompanied by `Mesh Comparison : Same` and `Mesh Validation : Valid`. There were no failed, ambiguous, missing, duplicate or unexpected case observations. The raw log ends with `Blender quit`.

This is a **source-derived original native invocation**. It is not an execution obtained from a configured CTest inventory. It provides **zero browser test passes**, does not change the selected 829 browser obligations, and does not change the separate Blender 5.4 native totals. Full feature parity and a complete Blender test denominator remain unproven.

## Original inputs and invocation

The original source is Blender commit `fbe6228777e7d9afefcd61a413844e790ae75db7`. Source archive SHA256 is `de0fdadf28015805370d1815facaf9139fbb1e161d8c540d1765484beabb3a99`. The staged script, helper and three CMake files were copied byte-for-byte from that archive. The complete declaration catalog identifies this as declaration 74 at `tests/python/CMakeLists.txt:703`, inside the original `if(TEST_SRC_DIR_EXISTS)` condition.

The fixture is the original `tests/files/modeling/operators.blend`, **4,028,858 bytes**, SHA256 `345857f0185fc38799d26e671e88ed06bf7754163c0ea58b4b8475c57908f9cc`. Its exact size and SHA256 match the original 5.2 Git LFS pointer, preserved as `original-fixture-pointer.txt`. An already hydrated payload in the product source tree was reused only after that independent original-pointer check. The newer directory holding the payload is not the source authority for this test.

The native executable is the previously verified official Blender 5.2.0 release, SHA256 `83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27`. The raw log reports build hash `fbe6228777e7`. The prior release checksum and build-hash checks are referenced in the prospective receipt. Those checks do not establish complete native source/build-configuration correspondence; that field remains false.

The exact command and working directory were written to `prospective-command.json` before process creation. They preserve the original CMake base flags and the fixture/script arguments:

```text
blender --background --console-crash-handler --factory-startup
  --debug-memory --debug-exit-on-error --python-exit-code 1
  --python-expr "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'"
  ORIGINAL_STAGED_FIXTURE --python ORIGINAL_STAGED_OPERATORS_SCRIPT
  -- --run-all-tests
```

The actual receipt contains the resolved absolute paths. The original `seed(0)` is unchanged. All original cases execute through the original `RunTest.run_all_tests()` branch with mesh comparison enabled. No selector, failfast mode or shard was added. `BLENDER_TEST_UPDATE` was absent, so the original golden-data update path was unavailable. There is no mutation of assertions, tolerances, source or fixtures.

## Execution and observation

`run-native.py` ran in the explicitly authorized elevated local execution environment that previously allowed Blender to finish its normal shutdown. It imposed the prospective 180-second process bound and a 4 GiB minimum free-disk reserve. Numeric-library environment requests were `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` and `NUMEXPR_NUM_THREADS=1`.

Those requests do not constrain every Blender worker pool. The verified child-process sample observed at most 18 threads and 379,876 KiB resident memory; kernel waited-child accounting reported 379,624 KiB maximum RSS. The sampler checked `/proc` command-line identity before accepting a PID sample.

The capture reads the original driver's stdout without replacing its entry point or adding callbacks. Each observed case preserves its exact name, raw log line, explicit terminal marker, comparison and validation output, original source file SHA256, declaration line, and spec-source SHA256. The 105 static declarations are used to establish identities and detect omissions, never to manufacture passes. All six staged source/fixture inputs have matching before/after hashes.

`summarize.py` rereads the immutable plan, execution and raw log, rederives the original declarations, verifies their exact identity and all actual markers, and binds the resulting `summary.json` to its inputs. It does not rerun Blender.

A separate read-only review by the parity reviewer verified the staged source closure against the original archive, the original pointer/fixture match, the CMake command, the 105 original case identities and actual `Same`/`Valid` markers, and the successful process completion. It found no blocker. No second operators invocation was performed.

## Frozen receipts

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `prospective-command.json` | 38,548 | `c64b5f9e1b4ef9d6eabad71b854b4861baef5fdc7bd185cb8c16b9d993a82600` |
| `execution.json` | 76,950 | `8c6928062436813530f7b02865e828b549170841094606cac6074f63f6a70461` |
| `original-driver.log` | 15,224 | `98bff9b22856dbd2f41f19bd127fc783e820174ed92997ecbf0fa93e3413e8cb` |
| `summary.json` | 76,075 | `fff5cc16a4b72b4913b9c98ce25055eff66c8061417351d3f3c273a1915cb02e` |

The capture refuses to overwrite an existing prospective or execution receipt. Earlier native, browser and failed-attempt evidence remains unchanged.
