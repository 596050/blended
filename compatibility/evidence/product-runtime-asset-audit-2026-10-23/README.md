# Remaining original product LFS assets

The read-only audit found **338 original LFS pointer paths outside the 7,353
verified fixture candidates** at product source commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d`. All 338 live files still contain
their original pointer bytes. None contains its verified payload.

These paths declare **8,791,719 bytes**. Deduplicating identical object IDs gives
**297 objects and 8,710,555 bytes**. The complete path, object ID, expected size,
original pointer identity, and observed live-file identity for each asset are in
`report.json`.

| Directory | Pointer paths | Declared payload bytes by path |
| --- | ---: | ---: |
| `doc/python_api/static` | 1 | 5,703 |
| `release/darwin` | 1 | 143,624 |
| `release/darwin/Blender.app/Contents/Resources` | 3 | 2,237,083 |
| `release/darwin/buildbot` | 1 | 220,950 |
| `release/datafiles` | 2 | 908,268 |
| `release/datafiles/colormanagement/icc` | 5 | 2,484 |
| `release/datafiles/icons` | 153 | 311,796 |
| `release/datafiles/studiolights/matcap` | 27 | 2,167,175 |
| `release/datafiles/studiolights/world` | 8 | 1,863,061 |
| `release/windows/installer_wix` | 2 | 206,889 |
| `release/windows/msix/Assets` | 45 | 321,524 |
| `release/windows/msix/Assets/contrast-black` | 45 | 255,522 |
| `release/windows/msix/Assets/contrast-white` | 45 | 147,640 |

The `release/datafiles` subtree accounts for 195 paths and 5,252,784 bytes. Its
unmaterialized assets include ICC profiles, icons, matcaps, world studio lights,
`splash.png`, and `DejaVuSans-Lite.sfd.bz2`. Other paths include platform packaging
art and the documentation favicon. This inventory does not assert that every
platform-specific asset must be included in a browser package.

## Verification boundary

The source archive is 80,900,636 bytes with SHA256
`e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`.
The audit checked that identity against the prior fixture inventory, successful
hydration report, and unchanged-source receipt. It scanned all 22,278 archive
entries and found 7,053 original LFS pointer paths in total. Of those, 6,715 are
within the exact fixture candidate set. All 7,353 excluded original archive
files were matched against that byte-bound inventory before exclusion.

Every remaining pointer-like entry was parsed. The live scan encountered no
missing files, mismatches, symlink paths, or read-bound exclusions. It hashed
43,620 bytes of live pointer files, and did not download, extract, hydrate, or
modify the source tree. The archive was hashed again after scanning.

This is resource availability evidence. It records **zero test executions and
zero test passes**. The audit does not discover all runtime dependencies or
establish whole-application resource closure or feature parity. The excluded
live fixture payloads were not rehashed by this audit; their previous successful
verification and exact original archive identities were checked.

## Reproduce

Run from the repository root and select a new output filename:

```sh
python3 compatibility/evidence/product-runtime-asset-audit-2026-10-23/audit.py \
  --source-archive /workspace/scratch/d63596d831b2/runtime/blender-product-94363991.tar.gz \
  --source-root /workspace/scratch/d63596d831b2/runtime/upstream-product/blender-94363991e7dcf39e2d70614aa002ab6f67764a5d \
  --fixture-inventory compatibility/evidence/product-fixture-hydration-2026-10-23/inventory.json \
  --fixture-report compatibility/evidence/product-fixture-hydration-2026-10-23/report.json \
  --preserved-source-receipt compatibility/evidence/product-fixture-hydration-2026-10-23/preserved-source.json \
  --output /tmp/product-runtime-asset-audit-recheck.json
```

Runtime paths are explicit inputs and can be changed after relocation. Expected
archive identity and source commit remain pinned. Existing output is never
overwritten. The script has no network operations or source mutation path.
