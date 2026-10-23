# Independent checkpoint recovery audit

The completed audit is `verified-recovery/audit.json`; `summary.json` binds it,
the replayed ledger report, and the two retained earlier attempts. Every command
has its actual argument vector, working directory, start/completion timestamps,
exit code, and original stdout/stderr bytes under its `commands/` directory.

The verified checkout began as an empty Git repository. It fetched only the exact
public base commit `b2fa1b96db519d86adb7809ad5f881c26124ac70` and its ancestors
from `https://github.com/596050/blended.git`. It was not cloned from the current
working repository and used no local Git object alternates. Before the public
fetch, `git bundle verify` rejected the missing prerequisite. After fetching the
base, the target checkpoint commit was still absent and bundle verification
succeeded. Fetching the bundle then restored:

| Identity | Value |
| --- | --- |
| Bundle | `blended-0d09949783ff.bundle`, 9,759,413 bytes |
| Bundle SHA256 | `cd2aabcfbfa6a155c7bc14aa10fe0b5bcbaa9714f459e752d50d6bfc756c9c22` |
| Recovered commit | `0d09949783ffd696edc575359a62a662580a8964` |
| Recovered tree | `35f3c632814268a5673ea3b4c1cda7b6e509c7a9` |
| Parent | `b2fa1b96db519d86adb7809ad5f881c26124ac70` |

Commit bytes, full commit identity, and full tree identity match the original
checkpoint. `git fsck --full --no-reflogs` passed. The independent checkout
remained clean before and after replay.

The archived v2 ledger consumer ran from the restored checkout against the
committed v2 contract, inventory, executions, and evidence. Its strict exit code
was **1**, the expected blocked result: **829 obligations, 512 strict successful
pairs, 597 outcome agreements, 132 required declarations, and 101 unresolved
declarations**. Every ledger output field, all registration records, and all 829
pair records match the committed assessment. The converter report additionally
contains four observation diagnostics, so the full report files have different
raw bytes. Neither test parity nor application feature parity is declared.

The first retained attempt stopped when the default execution environment could
not reach its proxy. The second fetched the public base and recovered the bundle,
but exposed an overly strict raw-report equality check in this audit script.
`verified-recovery/` records the complete corrected rerun in a third, initially
empty repository. The original runner bytes for the two earlier attempts are
preserved separately and match the runner hashes in their original audit records.

This is recovery and evidence-consumer verification. It did not rerun Blender,
publish a commit, or change any parity gate input.
