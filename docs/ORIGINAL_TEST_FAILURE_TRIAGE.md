# Original Blender test failure triage

## Scope and result

This report diagnoses the immutable first browser matrix completed on 2026-10-23. It compares original Blender **5.2.0 candidate** sources at `fbe6228777e7d9afefcd61a413844e790ae75db7` against the official native release of that same revision. The product target remains `94363991e7dcf39e2d70614aa002ab6f67764a5d`; none of these results establishes product-target parity.

The matrix retained 132 source declarations. Thirty invocations had frozen native inventories containing 700 parent case IDs. Browser execution produced 597 observed passes, 90 failed parent cases, one expected failure, and 12 unexecuted cases. Of the observed passes, 506 belong to the 23 completely passing invocations; 7 HTTP, 78 imbuf, and 6 NLA passes occur in invocations that do not satisfy the strict all-pass gate. The 102 declarations blocked before browser execution remain obligations. These are subset counts, not a complete Blender test denominator.

The exact [matrix receipt](../compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23/matrix.json), [native discovery inventory](../compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23/native-discovery-inventory.json), and [runner snapshot](../compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23/harness-manifest.json) are bound by hashes below. The profile used software WebGPU in Chromium and has no verified hardware GPU result. This report changes no upstream test, assertion, original fixture, runner, or raw receipt.

| Invocation | Native result | Browser result | Diagnosis |
| --- | --- | --- | --- |
| `script_disk_file_hash_service_test` | 12 passed | 12 unexecuted, import failed | Browser Python build omits `_sqlite3` |
| `script_http_downloader` | 8 passed | 7 passed, 1 error | Process communication sockets unavailable |
| `imbuf_py_api` | 80 passed | 78 passed, 2 failed parent cases | AVIF codec dependency disabled; 14 additional native subtests absent |
| `bl_brush` | 4 passed | 4 setup errors | Missing bundled Essentials brush payload |
| `script_pyapi_blf_buffer` | 82 setup errors | 82 setup errors | Original font/reference resources absent from the test environment |
| `script_pyapi_doc_gen` | 1 failed | 1 failed | Original documentation source tree absent from the test environment |
| `bl_animation_nla_strip` | 6 passed, 1 expected failure | 6 passed, 1 expected failure | Matching upstream expected failure, retained as a non-pass |

## Browser failures with a passing native reference

### Essentials brushes: faithful package correction is possible

All four exact IDs fail in `setUp`, before their assertions:

```text
__main__.AssetActivateTest.test_loads_essential_asset
__main__.AssetActivateTest.test_toggle_when_brush_differs_sets_specified_brush
__main__.AssetActivateTest.test_toggle_when_brush_matches_sets_previous_brush
__main__.AssetSaveAsTest.test_saves_asset_locally
```

The original [brush test](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/sculpt_paint/brush_asset_test.py), lines 18-20 and 55-57, activates `Draw` or `Smooth` from `brushes/essentials_brushes-mesh_sculpt.blend`. Every browser error says `No asset found at path ""`. Native execution passes all four cases.

The artifact-bound `shell/boot-windowed.js`, lines 51-54, sets `BLENDER_SYSTEM_RESOURCES=/bw` and `BLENDER_SYSTEM_DATAFILES=/bw/datafiles`. Its SHA256 is `edeb59e47b11db890b8ad4b2ef400164240832cab4e8fb657a540070163f7561`; the browser qualification receipt records the same hash and `modified: false`. The exact [Essentials implementation](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/source/blender/asset_system/intern/library_types/essentials_library.cc) resolves the `assets` subdirectory through `BKE_appdir_folder_id(BLENDER_SYSTEM_DATAFILES, "assets")`. The exact [application path implementation](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/source/blender/blenkernel/intern/appdir.cc), lines 682-692, checks that environment path first.

The engine JavaScript's 3,443 preload file entries contain no `/bw/datafiles/assets/` entry. This count comes from a complete parse of the generated metadata, including minified integer exponents. Its verified SHA256 is `308065bbf93e28f772f09c84a99995fd71f38113fb012f3b45013add05f76c64`, matching the matrix artifact. This is a missing package payload, with no evidence yet of incorrect brush activation behavior after loading the asset.

The official native release already contains the exact required payload:

| Identity | Value |
| --- | --- |
| Source-relative path | `assets/brushes/essentials_brushes-mesh_sculpt.blend` |
| Native package path | `5.2/datafiles/assets/brushes/essentials_brushes-mesh_sculpt.blend` |
| Browser package destination | `/bw/datafiles/assets/brushes/essentials_brushes-mesh_sculpt.blend` |
| Bytes | 2,715,184 |
| SHA256 | `f8b15126658f5a4ac455b0826a7eeae026576ed7c2ac45562d8880383fbf03bf` |

The measured native bytes and hash exactly match the [LFS pointer at the candidate source pin](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/assets/brushes/essentials_brushes-mesh_sculpt.blend). Install these bytes at the normal browser package destination before the first Essentials lookup: `essentials_directory_path()` caches its first result in a static variable. Then rerun all four unchanged original cases in a fresh engine process. A successful result would qualify the augmented package and must bind the added payload hash and destination; it would not change the original artifact's four errors. Future builds should hydrate and package the original Essentials assets as release resources.

**Completed package correction:** the separately identified augmented package now passes all four original cases, with no skips or failures and browser runtime exit code 0. The new archive SHA256 is `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910` (110,053,572 bytes). Its [qualification receipt](../compatibility/evidence/brush-package-overlay-5.2-2026-10-23/bl_brush-local-server/qualification.json) has SHA256 `00845cdb676f151fc21e2589f8b4c6043fca63bd1e54a2530d383f1f2f23ad5e`; its [raw browser log](../compatibility/evidence/brush-package-overlay-5.2-2026-10-23/bl_brush-local-server/browser.log) has SHA256 `7263ecd3eee0af1d1b6219628025cbd7840c3260e9b1690fef680ac9162e45cd`. The [overlay evidence README](../compatibility/evidence/brush-package-overlay-5.2-2026-10-23/README.md) documents actual byte verification, both package identities, the unchanged native-frozen invocation, and a retained host-permission failure before the successful run. Original package failures remain unchanged; other suites have not been requalified on this augmented package.

### AVIF and the image-format denominator

The two failed parent IDs are `__main__.TestImBufFileTypes.test_write_and_detect_all_types` and `__main__.TestImBufPlanes.test_planes_roundtrip`. Their three exact failure events are:

```text
__main__.TestImBufFileTypes.test_write_and_detect_all_types (type_id='AVIF')
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='AVIF', planes=24)
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='AVIF', planes=32)
```

The original [imbuf test](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/bl_imbuf_py_api.py), lines 543 and 886, fails at `imbuf.write`. Images and temporary directories are generated by the test itself; other formats in those loops write successfully. The `No such file or directory` suffix therefore does not establish a missing input fixture.

The actual build log `compatibility/evidence/runtime-context-2026-10-23/131-dependency-openimageio.log` configures `-DUSE_LIBHEIF=OFF` at line 22 and states that the HEIF plugin will not be built at lines 114-115. The original Blender [AVIF implementation](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/source/blender/imbuf/intern/format_avif.cc) uses the OIIO `heif` format for writing. This supports a missing codec dependency as the cause. A faithful fix requires a working browser libheif/AV1 encoding chain and OIIO plugin, followed by the unchanged AVIF roundtrips. It cannot be counted as fixed by hiding AVIF from the capability list.

There is a second, independent completeness issue: native execution records 57 subtest identities while browser execution records 43. The original source loops over advertised `imbuf.file_types`, so absent formats suppress subtests without producing skip outcomes. These 14 native subtests did not execute in the browser:

```text
__main__.TestImBufFileTypes.test_file_types_have_id_and_extensions (type_id='CINEON')
__main__.TestImBufFileTypes.test_file_types_have_id_and_extensions (type_id='DPX')
__main__.TestImBufFileTypes.test_file_types_have_id_and_extensions (type_id='JPEG2000')
__main__.TestImBufFileTypes.test_file_types_have_id_and_extensions (type_id='WEBP')
__main__.TestImBufFileTypes.test_write_and_detect_all_types (type_id='CINEON')
__main__.TestImBufFileTypes.test_write_and_detect_all_types (type_id='DPX')
__main__.TestImBufFileTypes.test_write_and_detect_all_types (type_id='JPEG2000')
__main__.TestImBufFileTypes.test_write_and_detect_all_types (type_id='WEBP')
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='JPEG2000', planes=16)
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='JPEG2000', planes=24)
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='JPEG2000', planes=32)
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='JPEG2000', planes=8)
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='WEBP', planes=24)
__main__.TestImBufPlanes.test_planes_roundtrip (file_type='WEBP', planes=32)
```

The artifact's [CMakeCache](../compatibility/evidence/runtime-context-2026-10-23/CMakeCache.txt), lines 673-679, explicitly disables `WITH_IMAGE_CINEON`, `WITH_IMAGE_OPENJPEG`, and `WITH_IMAGE_WEBP`. Parent case-ID equality cannot establish image-format parity. Preserve native-expanded subtest obligations and rebuild the missing format support. Comparing all 30 corresponding receipts found no other difference in recorded subtest-ID sets, but equal sets do not prove complete execution when both native and browser stop before later subtests, as documentation generation does here.

### HTTP downloader: process and IPC support

The exact failing case is `__main__.BackgroundDownloaderProcessTest.test_start_stop`. The other seven parent cases pass in both environments. At [original source](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/bl_http_downloader.py) line 196, `downloader.start()` reaches `_bpy_internal/http/downloader.py:622`, `multiprocessing.Pipe(duplex=True)`, `socket.socketpair()`, and finally `OSError: [Errno 52] Function not implemented`.

This case tests background process startup and shutdown without performing an HTTP download. Its later assertions check subprocess liveness and shutdown state. The receipt does not identify CORS, an external server, or a missing URL fixture. Changing `PYTHON_BIN` cannot repair the first failed socket operation. The application needs browser-supported process/worker and IPC behavior sufficient for the original lifecycle contract; adding a fake process or bypassing startup would not satisfy the case. Later process limitations may remain after the first socket failure is fixed.

### SQLite-backed hashing: blocked before discovery

The [original hash-service test](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/bl_disk_file_hash_service_test.py), line 18, imports the real SQLite backend. That backend imports `sqlite3`, whose wrapper cannot import the `_sqlite3` extension. The browser raises `ModuleNotFoundError` before `unittest.main`; no case is counted as run or failed. All 12 frozen native IDs remain unexecuted:

The frozen ID normalization removes only the `__main__.` prefix.

```text
DiskFileHashServiceNotOpeningTest.test_closing_unopened_service
DiskFileHashServiceNotOpeningTest.test_doubly_closing
DiskFileHashServiceTest.test_cleanup_on_close
DiskFileHashServiceTest.test_file_matches
DiskFileHashServiceTest.test_get_file_hash
DiskFileHashServiceTest.test_rehash_after_modification
DiskFileHashServiceTest.test_store_hash_callback
SQLiteBackendTest.test_fetch_nonexistent_file
SQLiteBackendTest.test_mark_as_fresh
SQLiteBackendTest.test_remove_older_than
SQLiteBackendTest.test_store_fetch_update_hash
SQLiteBackendTest.test_store_multiple_hashes_and_sizes
```

The actual Python build log `compatibility/evidence/runtime-context-2026-10-23/134-dependency-python.log`, line 1610, passes `py_cv_module__sqlite3=n/a`; line 2357 confirms the extension is unavailable. Python wrapper files alone are insufficient. Build and package the real SQLite extension and its dependency for the browser target, then rerun the original backend and service tests. Removing the import or replacing the backend with an in-memory stub would change the application contract.

## Shared incomplete resource environments

### BLF buffer tests

All 82 browser error outcomes end at the same missing original font, `tests/files/blenfont/noto_fonts/NotoSans-Regular.otf`, in `load_font_blf()` at [original source](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/bl_pyapi_blf.py) line 634. The initial native receipt has the same 82 setup errors. These are resource-environment failures; glyph, shaping, and image-comparison assertions have not established a browser mismatch in this attempt.

Restore the exact source-relative font files, reference images, and required comparison tool before retrying. The resource restoration work is a separate immutable attempt; no pass is inferred here from downloading files. Exact failed IDs are retained in Appendix A and in the hashed raw receipt.

### Documentation generation

The only parent case is `__main__.DocGenTest.test_doc_gen_and_stubs`. Its failed subtest is `__main__.DocGenTest.test_doc_gen_and_stubs [sphinx_doc_gen]`. Both initial environments raise `ModuleNotFoundError: No module named 'sphinx_doc_gen'` at [original source](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/bl_pyapi_doc_gen.py) line 87. Lines 38-39 derive `doc/python_api` from the test's original source-relative location. Restoring the original documentation tree and its dependencies is the faithful next action. The source returns before the stub-generation subtest when this first phase fails, so the one observed subtest is not the full obligation for this parent case. A later retry must still satisfy stub generation and its real subprocess requirements.

## Matching upstream expected failure and observer assessment

`__main__.NlaStripBoundaryTest.test_adjacent` is marked `@unittest.expectedFailure` in the [exact original source](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/tests/python/bl_animation_nla_strip.py), lines 80-89. The browser and native receipts both retain `expected_failure`, with `AssertionError: 1.0 != 4.0`. Both execute six other passing cases. This is matching known upstream behavior, not a new browser regression or a passing case. The strict all-pass invocation gate rejects it by design; preserve the expected-failure status rather than changing the decorator or counting it as a pass.

The seven initial matrix failures above have valid, specific original-test outcomes or a specific pre-loader exception. No observer defect is needed to explain them. Three AVIF subtest failures correctly map to two failed parent cases; 12 SQLite IDs are unexecuted; an upstream expected failure remains distinct. The separately repaired injected-argument marker parsing issue from an earlier attempt must not be used to erase these later receipts. Completeness still requires independent configuration/fixture closure and native-expanded dynamic obligations; accurate recording of a partial run does not prove all-tests parity.

## Separate resource retries

The later resource-restored attempts are retained under `compatibility/evidence/unittest-native-resources-5.2-2026-10-23/` and `compatibility/evidence/unittest-browser-resources-5.2-2026-10-23/`. They do not replace the first matrix. Their original test sources remain unchanged, with exact resources and native tool identities bound by the receipts.

The [machine-readable resource triage](../compatibility/evidence/unittest-resource-triage-5.2-2026-10-23.json) retains every exact retry case ID, subtest, original counter, and resource observation (53,987 bytes; SHA256 `f466a5a2dee9e7bb819131faa0b4c95433da80b2e303a70283cf546b8f1147ae`).

| Original invocation | Native retry | Browser retry | Newly reached blocker |
| --- | --- | --- | --- |
| `script_pyapi_blf_buffer` | 82 passed | 2 passed, 80 failed | Every failure is the original missing-`IDIFF_BIN` assertion at line 1592 |
| `script_pyapi_blf_vfont` | 129 passed | 2 passed, 127 failed | Every failure is the same original missing-`IDIFF_BIN` assertion |
| `script_pyapi_doc_gen` | 1 passed, both subtests passed | 1 failed; documentation subtest passed | Stub-generation subprocess fails on Emscripten |

For both font invocations the two passing parent IDs are `__main__.TestStressInvalidCodepoints.test_embedded_null_raises` and `__main__.TestStressInvalidCodepoints.test_surrogates_raise`. The other recorded parent IDs fail before the external image comparison, so rendered image parity is still unmeasured. All exact identities are in each receipt's `execution.suites[0].discovered_ids`; the failed outcomes are in `execution.suites[0].outcomes`. The first matrix's 82 BLF IDs are listed in Appendix A; the new VFONT inventory expands the known native denominator rather than replacing those 82 IDs.

Documentation generation now records the successful `__main__.DocGenTest.test_doc_gen_and_stubs [sphinx_doc_gen]` subtest and the failed `__main__.DocGenTest.test_doc_gen_and_stubs [sphinx_stub_gen]` subtest. At original line 106, `subprocess.run` reaches Emscripten's `Popen` and raises `OSError: [Errno 138] emscripten does not support processes.` This is a browser process capability gap exposed after the resource fix.

Faithful image qualification needs the exact original image comparator, flags, inputs, reference images, return status, and tolerances. A declared transport to a native comparator can measure browser-produced pixels, but does not establish general browser subprocess parity. The existing missing-comparator outcomes must remain failures until an identified execution mechanism completes the original comparison. Installing a host binary path alone cannot make Emscripten launch it.

The later, explicitly separate [host-assisted image diagnostic](../compatibility/evidence/unittest-font-host-oracle-5.2-2026-10-23/summary.json) captured all 207 expected browser-produced images and compared them using the original native comparator and thresholds. All 80 buffer images were byte-identical to the reference PNGs and passed `idiff`. All 127 VFONT images met the original comparison thresholds; none was a byte-identical PNG file, and 71 used exit status 1, which the original test accepts. This supplies image-comparison evidence without making the original 207 missing-comparator assertions pass or claiming browser subprocess support. The diagnostic summary SHA256 is `420fa307b7120bec342ee0c99f53f46659ca9149c3325f178d908051738a6385`; it binds per-image hashes, comparator invocations, tolerances, and raw output receipts.

| Retry invocation | Native `native_reference.json` SHA256 | Browser `qualification.json` SHA256 | Browser `browser.log` SHA256 |
| --- | --- | --- | --- |
| `script_pyapi_blf_buffer` | `7d32c15270ea2731f8e0ba0d91f5145b749df55586338b87f2857d164b8b7fc6` | `92572adb7bbdb459b732aae5f867ac314d91798cf1b03ab0e07e4f2604a37129` | `3f12d49797c95cdf48467b2ea3c1fb3b4c0e7c01ad0ec95819207d94d1ad401e` |
| `script_pyapi_blf_vfont` | `3949ff905260a09414add8afcaa94bd390e7088cfd1c04776bde643bfd32091b` | `8d8be9c8418c6c4a7fc73e3bfd2fd48cd4a21ffac0fca32b06db89852a85a39e` | `2ed2f7c50a6a7cd58ed4c86f2b5c4514acfc8e5ccc0f749c827cdfe6beb8c744` |
| `script_pyapi_doc_gen` | `0bbcedae5eef4da969c44fb4184b26a1cdfe45f2334280fab34290e6d1dfadba` | `e923d12d79a5edc4c00e202f8169f1b93b225175345b38d2513747a2a351e18e` | `c262dfd7b4cc25545bc024fffc392bef9975b203e6b56f99f1b700ab9349a7d1` |

## Evidence identity

All repository-relative browser receipt paths below are beneath `compatibility/evidence/unittest-browser-matrix-5.2-2026-10-23/`. Native paths are beneath `compatibility/evidence/unittest-native-5.2-2026-10-23/`. Hashes were independently recalculated from the retained files for this report.

| Root receipt | Bytes | SHA256 |
| --- | ---: | --- |
| `matrix.json` | 141,450 | `b31e9cdaa8230877deadb0e4c09ea0976e4502dfddffa0a5d4a9486b8a360362` |
| `harness-manifest.json` | 6,422 | `daa44add7cf7a10eb9a97c690687be5918a2e8c7a17a48895c860092cd96640c` |
| `native-discovery-inventory.json` | 88,447 | `25bc5c5e790461d0c56b64e039fe1e4b1663e2ea120c7bbe8f1ec3efb627a0ef` |

For each invocation, the browser files are `<invocation>/qualification.json` and `<invocation>/browser.log`; the native file is `<invocation>/native_reference.json`.

| Invocation | Browser qualification SHA256 | Browser raw log SHA256 | Native reference SHA256 |
| --- | --- | --- | --- |
| `script_disk_file_hash_service_test` | `0f979afdb9e0df1d5ef186a5fb1389d70d1c47aef2ea73a369d7924bdf167575` | `fab9a1fa89834c595aebde5466e647d4b90200b506c00bcd8dc8327d6c32967c` | `8b3b9e63c0f41e6fa2d5d105c440db240742f0863ec2a39f20f255bcf749fdc3` |
| `script_http_downloader` | `d036d12c098dc64be420036d13ae38c618b66e372ea5102da74374700c17c8e3` | `cdb899d27c999cdd715e6c35588d84327f109ecb70813498040e8ce0a9092072` | `be83bd8c3b7d45eace9f73dd5d228a9a0199cd8fa1c1a1d9fea2afc505b9acc4` |
| `imbuf_py_api` | `168ce784caf8c704a8c0ad8ea51067882eb5f181bc8cdc9850a762e71dcf77f9` | `efe1c723c99d4979a0ce87736ed000be19b6f4a4ee96d38f7f1d899227b081b5` | `f51d22d1352c66633e8425cc69cfb044d6082568c4c987d919f805ca3cfc8eb2` |
| `bl_brush` | `3e6eeb1bcda9498c7f484ac73e97516a8574081964bb49dc43e1fd1500e55085` | `80215c7c6937a4c56154e604f77eefb67d4520090324f797d2068105e8ce4eca` | `2fd6a3a69078ff4d9f2be52c36fc491147ee0be7dd3763829ab47d45aaa7ea63` |
| `script_pyapi_blf_buffer` | `c186548e995d69f5edf24378c0517ff7af4c27e68b5d48682f1938e28a32da84` | `ccb58d92e6685496e90be100dfaa6f3eac401a7b82b50c1a48769e3044dee356` | `0efa05fb469e4521235ad1ca2ab69188a3447a00927df99cea9c31a75efc3824` |
| `script_pyapi_doc_gen` | `41e1ed28d4438154a4c36a901cced3a7510b549b7631152460af8c392f418851` | `ae6c4869428482381b9c35cc441eea88413fcb2f8dc49aa7b7967cc3b926b08d` | `8a34c44236bffbb37090015ce366f806b3c94e7eb8daba4e40c7df12adaf6364` |
| `bl_animation_nla_strip` | `dd69d27e116000264032111b5520dbab55a1ab2514d5a7717e8eb77107d6a17e` | `5cbcc4a7b81c8ce364ee03e674abb4c7131746c13e1fb81b524f792d3b3889e2` | `dc8439ab157f5346ae87801c9afa7ca1f04cfb9bca44b9f046356a140f2e8b83` |

Original test source identities, verified against local exact-pin source bytes and the browser `suite_sources` records:

| Original source path | Bytes | SHA256 |
| --- | ---: | --- |
| `tests/python/bl_disk_file_hash_service_test.py` | 14,875 | `a2517a7c960c01cedbc347ba24a1649bcae81485320cf59b6f052ceb5594a5b4` |
| `tests/python/bl_http_downloader.py` | 11,488 | `c0e9ff0c18aef5209c2903e6a9c24066d4ab64311ec0b2b47de8d67273a33fe1` |
| `tests/python/bl_imbuf_py_api.py` | 33,079 | `cc97ac9e6a3d1854d87f3937dd273765b37a4a11322b947bd33ef43c9b92ff4e` |
| `tests/python/sculpt_paint/brush_asset_test.py` | 3,254 | `f508681973e1d279d61c02628d2b4657fbaa940cb50a0a0a408444bd705c221c` |
| `tests/python/bl_pyapi_blf.py` | 138,030 | `3a0f8e1acaa2ca2949c6b365929f04049896847e99b0759e63b1773a3871e328` |
| `tests/python/bl_pyapi_doc_gen.py` | 5,330 | `658ffbbb8dd5a7c9c9510139b788b3749e39fe4b2c3249154a6e13a1dc3e23ab` |
| `tests/python/bl_animation_nla_strip.py` | 6,735 | `b8605d07c81186a80dc2e970cc83ffa28aa341427dd90f06366ab4605b14b509` |

Supporting artifact and configuration identities:

| Supporting path | Bytes | SHA256 |
| --- | ---: | --- |
| `blended/compatibility/evidence/runtime-context-2026-10-23/131-dependency-openimageio.log` | 34,945 | `077ceb47d2320e4d0a4d94ed47d7861bb0102584968623081b7bb48fe3f578c5` |
| `blended/compatibility/evidence/runtime-context-2026-10-23/134-dependency-python.log` | 792,135 | `a7af5524e53e95f86dc239d8e8c4367a0d1c19a81b1cec6dc597fa68d17ec0b1` |
| `runtime/source/engine/blender-source-development/shell/boot-windowed.js` | 32,881 | `edeb59e47b11db890b8ad4b2ef400164240832cab4e8fb657a540070163f7561` |
| `runtime/source/engine/blender-source-development/bin/blender_browser.js` | 693,917 | `308065bbf93e28f772f09c84a99995fd71f38113fb012f3b45013add05f76c64` |
| `runtime/native/blender-5.2.0-linux-x64/5.2/datafiles/assets/brushes/essentials_brushes-mesh_sculpt.blend` | 2,715,184 | `f8b15126658f5a4ac455b0826a7eeae026576ed7c2ac45562d8880383fbf03bf` |
| `blended/compatibility/evidence/runtime-context-2026-10-23/CMakeCache.txt` | 64,011 | `026c70cc6d3a121258bbf3986c6fea94d823f8e74fdfb6c58227e8ce3eebb773` |
| `blended/compatibility/evidence/runtime-context-2026-10-23/source-build.json` | 165,401 | `5ed2a839fc340d16de08a096be3db74506a4cffdaaa87f40fbd1553810b53ce3` |
| `blended/compatibility/evidence/runtime-context-2026-10-23/native-context.json` | 4,956 | `8d2f79ef00aeb4314466226b04041d37d2f41c0ddddc30131e9d3034ee6e02da` |

The runtime paths in the final table are relative to `/workspace/scratch/d63596d831b2/`. They identify inspected files from the source-build artifact; the engine archive SHA256 is `5141ef40e3191ce2236fd80e23f26a73b7ac2db88f68755c6f4b23c6b59fe991` (107,362,300 bytes). The source-build receipt binds port commit `0e02e84b2bc5d9b27a6dc6e275443292f781fbad` and numerical patchset `blender-5.2.0-web-numerics-v1`. Runtime-context receipts retain independently measured native release options and browser artifact configuration. Neither their presence nor this triage provides configured CTest completeness.

## Appendix A: exact BLF setup-error case IDs

```text
__main__.TestCombiningEdgePositions.test_buffer_combining_after_space
__main__.TestCombiningEdgePositions.test_buffer_combining_at_end
__main__.TestCombiningEdgePositions.test_buffer_combining_first
__main__.TestCombiningEdgePositions.test_buffer_many_combining_no_base
__main__.TestCombiningKerning.test_buffer_Avatar
__main__.TestCombiningKerning.test_buffer_Eve
__main__.TestCombiningKerning.test_buffer_XV
__main__.TestCombiningKerning.test_buffer_Yolanda
__main__.TestCombiningKerning.test_buffer_ro
__main__.TestCombiningPosition.test_buffer_acute_e
__main__.TestCombiningPosition.test_buffer_diaeresis_Y
__main__.TestCombiningPosition.test_buffer_grave_A
__main__.TestCombiningPosition.test_buffer_phrase_combining
__main__.TestCombiningSequences.test_buffer_alternating
__main__.TestCombiningSequences.test_buffer_base_then_burst
__main__.TestCombiningSequences.test_buffer_repeated_mark
__main__.TestCombiningWordWrap.test_buffer_boundary
__main__.TestCombiningWordWrap.test_buffer_combining
__main__.TestCombiningWordWrap.test_buffer_font_size_1
__main__.TestCombiningWordWrap.test_buffer_lorem
__main__.TestCombiningWordWrap.test_buffer_no_break
__main__.TestCombiningWordWrap.test_buffer_stress
__main__.TestCombiningWordWrap.test_buffer_width_1
__main__.TestMultiline.test_buffer_combining
__main__.TestMultiline.test_buffer_combining_after_newline
__main__.TestMultiline.test_buffer_combining_before_newline
__main__.TestMultiline.test_buffer_newline_only
__main__.TestMultiline.test_buffer_plain
__main__.TestStrangeCharacters.test_buffer_ascii_sweep
__main__.TestStrangeCharacters.test_buffer_bom
__main__.TestStrangeCharacters.test_buffer_carriage_return
__main__.TestStrangeCharacters.test_buffer_cr_lf
__main__.TestStrangeCharacters.test_buffer_double_combining
__main__.TestStrangeCharacters.test_buffer_empty_string
__main__.TestStrangeCharacters.test_buffer_line_feed
__main__.TestStrangeCharacters.test_buffer_only_combining
__main__.TestStrangeCharacters.test_buffer_replacement_char
__main__.TestStrangeCharacters.test_buffer_tab
__main__.TestStrangeCharacters.test_buffer_tiny_buffer
__main__.TestStrangeCharacters.test_buffer_zero_width_joiner
__main__.TestStressBidi.test_buffer_lrm_rlm
__main__.TestStressBidi.test_buffer_mixed_script
__main__.TestStressBidi.test_buffer_nested_embed
__main__.TestStressBidi.test_buffer_rtl_override
__main__.TestStressCombining.test_buffer_all_diacriticals
__main__.TestStressCombining.test_buffer_alphabet_above_and_below_combiners
__main__.TestStressCombining.test_buffer_cgj
__main__.TestStressCombining.test_buffer_enclosing
__main__.TestStressCombining.test_buffer_half_marks
__main__.TestStressCombining.test_buffer_zalgo_100
__main__.TestStressComplexScripts.test_buffer_arabic
__main__.TestStressComplexScripts.test_buffer_devanagari
__main__.TestStressComplexScripts.test_buffer_hangul_jamo
__main__.TestStressComplexScripts.test_buffer_thai
__main__.TestStressEdgeParams.test_buffer_font_size_1
__main__.TestStressEdgeParams.test_buffer_font_size_2
__main__.TestStressEdgeParams.test_buffer_negative_pos
__main__.TestStressEdgeParams.test_buffer_wrap_0
__main__.TestStressInvalidCodepoints.test_buffer_max_codepoint
__main__.TestStressInvalidCodepoints.test_buffer_nonchar_fdd0
__main__.TestStressInvalidCodepoints.test_buffer_nonchar_ffff
__main__.TestStressInvalidCodepoints.test_buffer_replacement
__main__.TestStressInvalidCodepoints.test_buffer_specials
__main__.TestStressInvalidCodepoints.test_embedded_null_raises
__main__.TestStressInvalidCodepoints.test_surrogates_raise
__main__.TestStressSupplementary.test_buffer_emoji
__main__.TestStressSupplementary.test_buffer_emoji_zwj
__main__.TestStressSupplementary.test_buffer_math_alpha
__main__.TestStressSupplementary.test_buffer_mixed
__main__.TestStressWidths.test_buffer_cjk
__main__.TestStressWidths.test_buffer_fullwidth_latin
__main__.TestStressWidths.test_buffer_fullwidth_space
__main__.TestStressWidths.test_buffer_halfwidth_kana
__main__.TestStressWidths.test_buffer_mixed
__main__.TestStressWidths.test_buffer_unicode_spaces
__main__.TestStressZeroWidth.test_buffer_bom_start
__main__.TestStressZeroWidth.test_buffer_sequence
__main__.TestStressZeroWidth.test_buffer_soft_hyphen
__main__.TestStressZeroWidth.test_buffer_var_selector
__main__.TestStressZeroWidth.test_buffer_word_joiner
__main__.TestWrapCombiningEdge.test_buffer_at_combining
__main__.TestWrapCombiningEdge.test_buffer_combining_tight
```
