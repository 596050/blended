# Pinned Blender source and fixture inventory

This capture inventories the source archive for Blender product commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d`. It records **source candidates and
fixture presence**, not a runtime test denominator or application passes. No
Blender tests were executed and no fixture payloads were hydrated for this
capture. `runtime_enumeration_complete` remains false and no facet is complete.

The exact
[upstream archive](https://codeload.github.com/blender/blender/tar.gz/94363991e7dcf39e2d70614aa002ab6f67764a5d)
was independently checked at **80,900,636 bytes**, SHA256
`e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`.
`source-archive-verification.json` records that verification and
`capture-manifest.json` binds the scanner, test module, facet manifest and captured
artifacts. The initial archive-directory probe found no archive immediately
inside the extraction directory; the verified archive was in its parent.

## Source findings

The conservative scanner inspected **10,848 source files** and found **5,637
candidate declarations**, all marked `not_run`. They include vendored code and
compile-time assertions, so they must not be described as 5,637 Blender runtime
tests.

| Source candidate kind | Count | Unresolved interpretation |
| --- | ---: | --- |
| `TEST` | 2,150 | Build inclusion and concrete native registration |
| `TEST_F` | 1,068 | Fixture, build inclusion and concrete native registration |
| `TEST_P` | 25 | Runtime parameter instantiation and registration |
| `TYPED_TEST` | 4 | Runtime type instantiation and registration |
| `TYPED_TEST_P` | 3 | Runtime type instantiation and registration |
| Python `test_` definitions | 1,586 | Actual loader/driver membership and generated cases |
| `static_assert` | 801 | Compile-time obligations; not executable runtime leaves |
| **Total source candidates** | **5,637** | **All remain unreconciled to product runtime discovery** |

The scanner flags 96 candidates for known dynamic/decorated expansion patterns.
That flag is a hint; the other candidates still require build/runtime or
compile-time reconciliation. Conditional compilation, helper macros, generated
tests and nonstandard drivers can change the concrete test population.

Five source files remain unresolved. Four contain bytes that are not valid
UTF-8, and one Python file does not parse as a standalone module. Their file
hashes and errors are retained, rather than dropping them from the source file
inventory:

- `extern/bullet2/src/BulletCollision/Gimpact/btGImpactShape.h`
- `extern/bullet2/src/BulletSoftBody/btSoftBody.cpp`
- `extern/mantaflow/preprocessed/python/defines.py`
- `extern/quadriflow/3rd/lemon-1.3.1/lemon/soplex.h`
- `extern/quadriflow/src/loader.cpp`

The separate CMake index hashes **437 CMake files** and records **157 lexical
call-shaped candidates** for selected testing commands/helpers: 128
`add_blender_test`, 13 `add_test`, six `gtest_add_tests`, five `add_python_test`,
two `blender_add_ctests`, two `enable_testing`, and one `gtest_discover_tests`.
It deliberately does not evaluate comments, documentation examples, functions,
macros, loops, configuration conditions or calls through other helper names.
These 157 entries are neither confirmed registrations nor a complete source
registration population. Every entry records unresolved runtime resolution and
unevaluated configuration gates.

## Fixture presence findings

`--fixture-root tests/files` includes every discovered regular file under that
declared root, regardless of extension. The scanner also retains its existing
discovery of `.blend` paths outside declared roots.

| Presence measure | Count |
| --- | ---: |
| Fixture candidate paths | 7,353 |
| Paths under `tests/files` | 7,329 |
| Additional `.blend` paths elsewhere | 24 |
| LFS pointer files | 6,715 |
| Regular files with unvalidated bytes | 638 |
| Distinct LFS payload object IDs referenced by those pointers | 6,543 |

The 6,715 pointer files are **paths**, while 6,543 is a deduplicated count of
referenced **content object IDs**. Those distinct objects declare a total of
**880,195,119 bytes**. Pointer files contain identifiers and sizes, not the asset
contents required at those paths. Duplicate references are counted once in the
declared payload byte total. No download or hydration is implied by these counts.

Each fixture record retains its file-byte SHA256. For a pointer, that hash belongs
to the pointer text; `lfs_oid_sha256` separately identifies its intended payload
and `lfs_declared_size` records its declared size. This prevents hashing a small
pointer file and mistakenly accepting it as the full fixture.

The 638 files with bytes include reference metadata, scripts and other files as
well as potential assets. Their contents have not been validated against the
original tests. The legacy `fixtures_available` boolean means only that some
regular file bytes exist; the new explicit description records that limitation.
`fixture_completeness` remains `unknown`.

Facet fixture-glob matches and source-path hints appear in
`source-inventory-summary.json`. These are hints for reconciliation. They do not
resolve dependencies such as linked libraries, textures, fonts, videos, expected
images, caches, external resources or UI workflow data. Every facet still has
unresolved native runtime enumeration, source registration reconciliation,
fixture closure and workflow obligations.

## Files and verification

`product-source-inventory.json` is the full inventory, including source hashes,
candidate identities and all discovered fixture records.
`source-inventory-summary.json` records totals, unresolved obligations and facet
hints. The JSON and text CMake indexes preserve the corresponding candidate
locations without treating them as executed or configured tests.

The fixture extension was developed with six added checks. The recorded red run
executed 22 checks and failed on the missing fixture-root API and missing source
error hashes. The green run passed all **22 source-inventory checks**. Together
they cover non-`.blend` assets, reference outputs, non-`.blend` LFS pointers,
missing roots, path escapes, symlink handling and source errors that must remain
visible. These are infrastructure checks, not Blender feature-parity passes.

Reproduce the source inventory from the unchanged pinned extraction:

```sh
python3 tools/inventory.py \
  --root /absolute/path/to/blender-94363991e7dcf39e2d70614aa002ab6f67764a5d \
  --name blender/blender \
  --commit 94363991e7dcf39e2d70614aa002ab6f67764a5d \
  --fixture-root tests/files \
  --output /absolute/path/to/a-new-source-inventory.json
```

Use a new output path when reproducing evidence. The captured source tree must
stay unchanged if its hashes are to match this snapshot.
