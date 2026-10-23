# Original product fixture hydration

All **7,353 candidate fixture paths** are verified and materialized for original
Blender commit `94363991e7dcf39e2d70614aa002ab6f67764a5d`. The operation completed
on 2026-10-23 in 229 seconds. It executed no Blender tests and added no test passes.

## Measured result

| Measure | Observed result |
| --- | ---: |
| Original candidate paths, reconciled against the complete source archive | 7,353 |
| Original LFS pointer paths | 6,715 |
| Pointer paths hydrated in this operation | 6,714 |
| Previously hydrated payload verified and reused | 1 |
| Regular original candidate files verified against archive bytes | 638 |
| Unique LFS object identities | 6,543 |
| Unique LFS payload bytes | 880,195,119 |
| Unique objects downloaded in this operation | 6,542 |
| Total materialized candidate bytes, counting each original path | 899,886,860 |
| Failed download attempts | 0 |
| Failed batch requests | 0 |
| Unresolved candidate paths after final rehash | 0 |

The previously available payload is `release/datafiles/startup.blend`; its bytes
were verified against its original LFS pointer before reuse. Duplicate OIDs were
downloaded once and copied to every distinct original path. The selection covers
all 7,329 files under `tests/files` and the 24 additional `.blend` resources in the
original candidate inventory, including the Essentials assets and application
template startup files.

The 638 regular candidate files contain 11,517,351 bytes. Their original archive
hashes and Git blob identities are retained. The complete source archive is
80,900,636 bytes, SHA-256
`e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7`,
from the commit-specific official GitHub mirror URL:

`https://codeload.github.com/blender/blender/tar.gz/94363991e7dcf39e2d70614aa002ab6f67764a5d`

## Source preservation

An independent post-operation archive comparison checked every original entry
outside the candidate fixture selection. All **13,542 regular files**, totaling
**296,771,667 bytes**, and the **one original symbolic link** matched. This includes
the original test source, assertions, and application code. No difference was
found. See `preserved-source.json` and `verify-preserved-source.py`.

## Evidence and transport

`inventory.json` freezes all original inventory rows, complete pointer text,
pointer SHA-256 and Git blob SHA-1 identities, source archive member paths, expected
payload sizes and SHA-256 identities, and the observed initial state at each path.
Its candidate set was independently reconciled against every original regular
file under `tests/files` and every `.blend` file in the pinned archive, with the
same explicit non-source directory exclusions as the original inventory.

`attempts.jsonl` preserves the successful batch identity checks and each individual
object transfer. There were no transfer failures in this run. The implementation
retains failed attempts and their incomplete bytes separately if a future run
encounters them. Temporary action URLs and headers are not stored.

All download actions came from the fixed official Blender Git LFS batch endpoint:

`https://projects.blender.org/blender/blender.git/info/lfs/objects/batch`

Downloads and redirects are restricted to HTTPS on `projects.blender.org`. The
transport used batches of at most 64 objects and eight workers. Each payload was
bounded by its original declared size and verified before cache promotion or
source-tree replacement. Existing source files were replaced only if they still
matched their exact original pointer; already correct payloads were retained.
All final candidate paths were rehashed after materialization.

The authoritative operation result is `report.json`, with the host process exit
and exact argv in `host-process.json`. `host.log` records batch progress. The
executed tool and launcher are preserved as `hydrate_product_fixtures.py` and
`run-hydration.py`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `report.json` | 3,095,278 | `55fd3f2bba7150cf73055d1f44b3f4c391694214d8b06f8a2c207b5b03d891ad` |
| `inventory.json` | 10,890,515 | `3fadfc6ee21686ae4ceed0ce3e3a776c4bbcd5f481b0fd1a6582b2fd2031c4f5` |
| `attempts.jsonl` | 2,953,500 | `2d092d4920c106bb86f9dcbef56498b83f3f71e42926642f946526e55a70a675` |
| `host-process.json` | 1,279 | `7e36cc9e27ac44e3f133e0a5a6da36dc94db3f5b73884a372588ee6d92b753e0` |

## Reproduction

Run the repository's `tools/hydrate_product_fixtures.py` with the original source
inventory, exact source archive and hash, target source tree, a content-addressed
object cache, and a **new** evidence directory. The exact invocation used here is
retained in `host-process.json`. Source and cache paths may be relocated when
reproducing; the source commit, archive identity, pointer bytes, and payload
identities must remain unchanged. Evidence directories are never overwritten.

Six focused infrastructure regressions cover archive completeness, changed
regular files and symlinks, guarded pointer replacement, official-host action
validation, duplicate-object reuse, and preservation of corrupt transfers.

## Scope

This closes every path in the original **candidate fixture inventory**. Runtime
tests can still identify tools, services, system resources, or additional inputs
outside that selection. The receipt therefore keeps
`runtime_fixture_dependency_closure_complete` false. Hydration is resource
availability evidence, separate from native test execution, browser execution,
test outcome agreement, and full application parity.
