# Original fill failures: bounded source triage

## Observed result

Both failed cases reach the original `MeshTest.compare_object_data()` call, report `The edge topology is different`, and retain `Mesh Validation : Valid`. Native passes both with the same script, helper, fixture, command, and comparison mode. All 105 original names execute in the browser; only these two fail. No input or observation gate fails. The unchanged original driver raises for the two names, and Blender exits 1.

| Original case | Original declaration | Native | Browser | Browser stdout |
| --- | --- | --- | --- | --- |
| `IcosphereFill` | `tests/python/operators.py:340` | Passed, Same, Valid | Failed, edge topology differs, Valid | Start line 282; original failure line 283; comparator line 285 |
| `IcosphereFillUseBeautyFalse` | `tests/python/operators.py:346` | Passed, Same, Valid | Failed, edge topology differs, Valid | Start line 289; original failure line 290; comparator line 292 |

The first case calls the original `fill` edit-mode operator with default options. The second explicitly sets `use_beauty=False`. Both select the original edge indices `{20, 21, 22, 23, 24, 45, 46, 47, 48, 49}` from their respective original fixture objects. No threshold or index-change override is present in either original specification. The full specification hashes and source-qualified case IDs are retained in `summary.json`.

This is a real difference in the original browser test result, not a missing fixture or a replacement observer assertion. The words “edge topology” are the original engine comparator's classification. Actual evaluated mesh arrays have not yet been captured, so this receipt does not independently locate the difference in the fill implementation rather than the comparator.

## Original call path

All C++ files below are byte-exact copies from the verified complete archive of commit `fbe6228777e7d9afefcd61a413844e790ae75db7`. Their paths, hashes, archive members, and official pinned source URLs are bound by `source-basis.json`, SHA256 `99011b8e5dca5e99efcc01cdf6d73db8b02285a62430d47f3065135723423479`. No source from another Blender version is substituted.

| Source | Relevant original behavior |
| --- | --- |
| `tests/python/modules/mesh_test.py:288` | `run_test` applies the original operation, then calls `compare_object_data`; comparison is enabled by the original complete-driver branch. |
| `tests/python/modules/mesh_test.py:424` | The helper calls the expected mesh's original `unit_test_compare` and separately validates the evaluated mesh. The original “Same” result is required; these cases do not allow an index-change fallback. |
| `source/blender/editors/mesh/editmesh_tools.cc:4678` | `edbm_fill_exec` reads the requested beauty option and invokes `triangle_fill edges=%he use_beauty=%b` on selected edges at line 4701. `MESH_OT_fill` registers this callback and defaults beauty to true at line 4758. |
| `source/blender/bmesh/operators/bmo_triangulate.cc:52` | `bmo_triangle_fill_exec` builds scanfill vertices and edges from the original BMesh selection, computes a projection normal if needed, and passes the selected data to `BLI_scanfill_calc_ex` at line 178. |
| `source/blender/bmesh/operators/bmo_triangulate.cc:151` | The original normal calculation sorts squared normal magnitudes, selects an initial normal, aligns and adds normals, then normalizes. This is a source location to observe if a numerical or ordering difference is later investigated; none is measured here. |
| `source/blender/blenlib/intern/scanfill.cc:817` | `BLI_scanfill_calc_ex` constructs the projected scanfill result. The original implementation builds its projection at line 898 and also uses a vertex sort at line 523. |
| `source/blender/bmesh/operators/bmo_triangulate.cc:209` | The original code creates BMesh faces from scanfill triangles. The additional beauty stage is conditional at line 227. |
| `source/blender/blenkernel/intern/geometry_compare.cc:861` | `compare_meshes` checks element counts and attributes, constructs vertex and edge mappings, and has several paths that return `GeoMismatch::EdgeTopology`, including lines 901 and 954 and the helper path at line 822. The original message is selected at line 81. |

Both beauty settings fail. That makes the shared triangle-fill/scanfill path and the shared comparison path sensible places for a later diagnostic. It does not prove a defect in either path, and it does not establish beauty optimization as the cause. The comparator has multiple branches with the same output string; this run does not identify which branch produced it.

## Recorded platform differences and limits

The native reference is the official Linux x86-64 executable SHA256 `83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27`. Its independently observed build flags include `-march=x86-64-v2` and `-ffp-contract=off`. The observation is in `../runtime-context-2026-10-23/native-context.json`, SHA256 `8d2f79ef00aeb4314466226b04041d37d2f41c0ddddc30131e9d3034ee6e02da`.

The browser package's retained source-build receipt declares Emscripten 6.0.5 and a Release configuration. Its retained CMake cache sets release optimization to `-O2 -DNDEBUG` and compiler SIMD to ON. The package also already includes the recorded `blender-5.2.0-web-numerics-v1` changes to Emscripten `acosf` and the Eigen WebAssembly configuration. These are existing package identities, not fixes performed by this test task. The source-build receipt is SHA256 `5ed2a839fc340d16de08a096be3db74506a4cffdaaa87f40fbd1553810b53ce3`; the CMake cache is SHA256 `026c70cc6d3a121258bbf3986c6fea94d823f8e74fdfb6c58227e8ce3eebb773`.

Those records establish different native and browser execution platforms. The CMake cache alone is not a complete per-file compiler command. This bounded triage does not attribute the mismatch to floating-point contraction, SIMD, a library backend, or an already applied numerical patch.

The original `BLI_sortutil_cmp_float_reverse` returns zero for equal float keys (`source/blender/blenlib/intern/sort_utils.cc:41`). The normal and scanfill sorts therefore expose potential ordering decisions worth measuring. The current run does not show whether keys tie, whether sort order differs, or whether any such difference affects these meshes. A causal explanation requires runtime data, not the case names or static source alone.

## Bounded next diagnostic

A later diagnostic can preserve this failed invocation and capture the actual evaluated mesh vertices, edge endpoint pairs, and polygons for the two cases, together with their unchanged expected meshes. It should keep the original full comparison run and failure state, and identify any extra observation as a separate profile. If the arrays diverge, trace the original selected-edge order, projection normal before and after sorting, scanfill projection, and emitted triangles. If the arrays agree, inspect the original comparator's vertex and edge mapping branch. Any proposed production fix should then be tested with the unchanged full 105-case driver and a new package identity.

No such diagnostic, production edit, new oracle, or passing result is claimed by this directory. The failed receipt, original stdout/stderr, and both exact native passing observations remain the controlling evidence.
