# Original brush tests with a verified package correction

The separately identified resource-augmented browser package passes **all four unchanged original Blender brush cases**. The [successful qualification](bl_brush-local-server/qualification.json) records four discovered, executed, and passing cases, zero skips/failures, and browser runtime exit code 0. Its profile is `chromium-software-webgpu`. This is a four-case Blender 5.2 candidate qualification, not full application, hardware, or Blender 5.4 product-target parity.

The base package's [four setup failures](../unittest-browser-matrix-5.2-2026-10-23/bl_brush/qualification.json) remain unchanged. This correction belongs to a new package identity. Other invocations measured on the old package have not been requalified on this new package and must not be relabelled or summed into a new whole-package result.

## What changed

The base preloader omitted the original `assets/brushes/essentials_brushes-mesh_sculpt.blend` resource. The normal browser startup environment uses `/bw/datafiles`; the original Essentials implementation resolves its `assets` subdirectory and caches the first result. The new package includes the original file at `/bw/datafiles/assets/brushes/essentials_brushes-mesh_sculpt.blend` in the Emscripten preload, before application startup.

The payload was read from the official Blender 5.2 native release and independently checked against the [original LFS pointer at source commit fbe6228777e7d9afefcd61a413844e790ae75db7](https://github.com/blender/blender/blob/fbe6228777e7d9afefcd61a413844e790ae75db7/assets/brushes/essentials_brushes-mesh_sculpt.blend): 2,715,184 bytes, SHA256 `f8b15126658f5a4ac455b0826a7eeae026576ed7c2ac45562d8880383fbf03bf`. The [pinned overlay manifest](overlay-manifest.json) records its original path, destination, identity, and source URL.

The assembler adds those bytes to the end of the original `.data` and makes the corresponding generated JavaScript preload metadata and directory changes. It adds `PACKAGE-OVERLAY.json` to identify the package correction. The verifier opens the actual base and augmented archives, compares all 117 unchanged files, verifies the complete unchanged data prefix, verifies the added payload hash, and reconstructs the only allowed JavaScript change. The Wasm engine and startup shell bytes remain identical. No engine compilation, original source test, assertion, case selection, or test fixture change occurs.

## Artifact and receipt identities

| Item | Bytes | SHA256 |
| --- | ---: | --- |
| Base archive | 107,362,300 | `5141ef40e3191ce2236fd80e23f26a73b7ac2db88f68755c6f4b23c6b59fe991` |
| Augmented archive | 110,053,572 | `3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910` |
| New `.data` | 171,547,054 | `a66c183e1248e08426f28a73c961676b9f8d9bc7df6de4888f74cecc0dcd03a2` |
| New `.js` | 694,154 | `fc6757edf1624671c766a847ffee391b638b90f35874b1b54fbdd1c8cfe95ffb` |
| Unchanged `.wasm` | 119,225,569 | `27b25e78567bc6b95b81ef43fbf255c91b3655a9d4b6b9615296621e5d1fcf23` |
| [Package overlay receipt](package-overlay.json) | 2,547 | `45bbd14b53afe8f4dd466a3d8191d7b43110409f8dc0de7762f983eb09a42cdb` |
| [Frozen original cohort](frozen-cohort.json) | 2,463 | `9f82a905c156ac80df0a689ea0a8c2a7961eb69ea651af68b4a7a5ed1bb24f73` |
| [Harness manifest](harness-manifest.json) | 7,642 | `436d87a478a10c09db022ad72648fb3004c2866f071d27eb88fe01ec0fd8648d` |
| [Successful browser qualification](bl_brush-local-server/qualification.json) | 23,909 | `00845cdb676f151fc21e2589f8b4c6043fca63bd1e54a2530d383f1f2f23ad5e` |
| [Successful browser raw log](bl_brush-local-server/browser.log) | 9,953 | `7263ecd3eee0af1d1b6219628025cbd7840c3260e9b1690fef680ac9162e45cd` |
| [Successful host process receipt](bl_brush-local-server/host-process.json) | 1,890 | `1a3a516ea551ef2280621541ee6dd77bd04dd000230f6d44587da98cfdf18d75` |

The augmented archive is retained at `/workspace/scratch/d63596d831b2/runtime/brush-package-overlay-5.2/blender-source-development-essentials.tar.gz`. The unchanged source-build receipt continues to bind the **base** archive; the explicit overlay receipt binds the new archive. The probe records both identities and marks the candidate `blender-source-development-package-overlay`.

## Exact original cases

```text
__main__.AssetActivateTest.test_loads_essential_asset
__main__.AssetActivateTest.test_toggle_when_brush_differs_sets_specified_brush
__main__.AssetActivateTest.test_toggle_when_brush_matches_sets_previous_brush
__main__.AssetSaveAsTest.test_saves_asset_locally
```

The original source is `tests/python/sculpt_paint/brush_asset_test.py`, 3,254 bytes, SHA256 `f508681973e1d279d61c02628d2b4657fbaa940cb50a0a0a408444bd705c221c`. The frozen cohort retains its original `__main__`, all original CMake invocation flags, and the exact native-discovered case IDs. The native reference receipt SHA256 is `2fd6a3a69078ff4d9f2be52c36fc491147ee0be7dd3763829ab47d45aaa7ea63`.

## Reproduction and limits

From the repository root, use `tools/browser_package_overlay.py` with `--base-archive`, `--source-build-receipt`, `--asset-root` pointing to the original source tree or native `5.2/datafiles` directory, and a new `--output` directory. The assembler refuses changed payload hashes, unsupported generated metadata, duplicate destinations, unsafe archive members, and existing output directories. Its output is an archive plus a distinct `package-overlay.json`; this stage executes zero Blender tests.

Run `tools/probe_browser_port.py` with the new archive, unchanged base source-build receipt, `--package-overlay-receipt`, and `--package-base-asset`. Keep the same frozen original cohort manifest, its hash, original source, and Chromium executable. Use a new result directory. The exact invocation is retained in [run-qualification.py](run-qualification.py) and the host process receipt. The snapshot under `harness/` includes the executed verifier, observer, and pinned manifest bytes.

The [first local attempt](bl_brush/qualification.json) failed before any Blender tests because the default host execution sandbox denied creation of the localhost HTTP server socket. It is retained with SHA256 `c05f33548e4a47b881993a21ec00914f6053279d81bed632ab6a4f4fa071465a`. The successful attempt used the same frozen harness with the required local-server execution permission and a fresh evidence directory. This host permission failure is separate from Blender's browser process/socket limitations.

Sixteen new synthetic overlay integrity checks, together with the existing source-build/probe checks, passed 32 infrastructure tests. They verify rejection of unrelated JavaScript, data, Wasm, and archive member changes even when a claimed archive hash is updated. They are not Blender feature cases. The first real assembly also exposed generated integer offsets such as `39466e3`; the strict parser now handles these exactly, with a regression check, and verifies all 3,443 original preload entries plus the one added resource.

Only the mesh-sculpt Essentials asset needed by these four cases was restored. Other absent package resources and browser capabilities remain open obligations. The tool can apply the same reviewed correction to a future compatible source-build package, but each resulting package needs its own hash-bound qualification.
