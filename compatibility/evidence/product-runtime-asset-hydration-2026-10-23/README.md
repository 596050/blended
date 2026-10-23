# Original runtime asset hydration

The exact **338 original LFS pointer paths** identified by the independent runtime asset audit are now materialized and verified. They represent **297 unique content objects / 8,710,555 bytes**, or **8,791,719 payload bytes counted by path**. Every download, size and SHA256 check succeeded. The bounded host process completed at exit zero in 18.01 seconds.

This is source asset preparation. It executed no tests, started no builds, and establishes no browser passes, whole-application runtime dependency closure, or feature parity.

## Exact selection and provenance

The product source commit is `94363991e7dcf39e2d70614aa002ab6f67764a5d`.

The selection authority is the unchanged read-only audit at `../product-runtime-asset-audit-2026-10-23/report.json`, SHA256 `afa1183fd17b9b21e07e0da7eba18a8c41508ba33c5704ae2ab86f57d6e2901f`. Only its 338 explicitly listed paths were written. These include original icons, studio lights, color profiles, platform packaging images, and other remaining original assets outside the earlier verified fixture set.

Before any download or replacement, the recipe independently checked every selected pointer's exact bytes, Git blob identity, OID and declared size against the pinned official source archive. The archive is `https://codeload.github.com/blender/blender/tar.gz/94363991e7dcf39e2d70614aa002ab6f67764a5d`, 80,900,636 bytes, SHA256 `e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`. Each live path also had to match its exact original pointer and the independent audit's observed identity before it could be replaced.

All objects came from the official Blender repository LFS batch endpoint, `https://projects.blender.org/blender/blender.git/info/lfs/objects/batch`. The immutable transport helper validates HTTPS actions and redirects on `projects.blender.org`, verifies each returned object identity, bounds response and payload sizes, and requires the exact pinned SHA256 and byte count before placing any file. A fresh isolated object cache was used. File permissions were preserved across each atomic replacement.

## Retained evidence

| Artifact | Contents |
|---|---|
| `report.json` | Final selection result, source bindings, all 338 before/after identities, counts and limits |
| `inventory.json` | Frozen audit rows, original pointer text and Git blob identities, expected payload OIDs and sizes |
| `attempts.jsonl` | All five batch requests, 297 verified object downloads, and 338 per-path before/after identities and modes |
| `source-preservation-manifest.json` | Exact archive-derived expectations for all original non-LFS files, LFS paths, and the original symlink |
| `host-process.json`, `host.log` | Actual command, recipe hashes, process timing, resource bounds, exit code and raw output |
| `hydrate-assets.py`, `run-hydration.py` | Exact executed selection, preservation, hydration and bounded process recipes |
| `hydration_transport.py` | Immutable byte-identical snapshot of the already tested fixture transport helper |

The final report is 179,140 bytes, SHA256 **`47047c9cfb30fa917da21c00f9440de88b99e7ea0c3335dce960d802e4369d3f`**. It binds all preceding machine-readable evidence by byte count and SHA256. There were zero failed batch requests, zero failed object download attempts and zero failed materializations.

The host process had a 600-second limit and retained a 4 GiB minimum free-disk reserve. The recipe refuses to reuse an existing attempt or cache. No production harness, test, assertion or native configuration file was changed.

## Source preservation

The recipe checked every original non-LFS regular file against the exact archive before hydration and again after hydration. The final verification found:

| Exact archive population | Verified final state |
|---|---:|
| Original non-LFS regular files | 13,842 unchanged |
| Original symlinks | 1 unchanged |
| Original LFS paths, including previously hydrated fixtures | 7,053 pinned payloads verified |
| Newly selected asset paths | 338 of 338 verified |

The 7,053-path check includes the earlier fixture payloads without rewriting them. The only source-tree mutations were the 338 originally audited pointers, replaced with their exact original payloads. The read-only audit, all prior fixture evidence, and the completed native test evidence remain unchanged.

These checks cover the original pinned source archive entries. Dependencies expressed through separate repositories, native libraries, runtime services, hardware, generated outputs or application packaging can still require additional work. The report therefore keeps `whole_application_resource_closure_complete` and `full_feature_parity` false, with `tests_executed`, `test_passes` and `builds_started` all zero.
