# Expected aliases for the selected original dependency cache

This contract permits exactly three libpng aliases. It derives their expected
meaning from the pinned original installer and build recipe. It does not claim
that the historical build recorded these symlinks: its regular-file harvest
explicitly excluded them.

| Required alias | Exact relative link text | Required identified target |
| --- | --- | --- |
| `lib/libpng.a` | `libpng16.a` | `lib/libpng16.a` |
| `bin/libpng-config` | `libpng16-config` | `bin/libpng16-config` |
| `lib/pkgconfig/libpng.pc` | `libpng16.pc` | `lib/pkgconfig/libpng16.pc` |

The verifier rejects missing aliases, additional aliases, redirected targets,
equivalent but different link text, cycles, directory links, and changed target
bytes. Every target must also occur as a regular file in the independently pinned
historical harvest. Verification never repairs or invents an alias. Failure
causes the workflow to discard the installed prefix and rebuild dependencies.

## Preserved primary sources

The port recipe is the exact `scripts/deps/libpng.sh` Git blob
`43d128f1eabb52738220cb2867cb01f98c248fe8` at port commit
`0e02e84b2bc5d9b27a6dc6e275443292f781fbad`. Its 2,952 preserved bytes have SHA-256
`1b807dc8a6866ccafb0589854cd9d33b774692e02972228232be72b9ca0439ce`.
The recipe selects libpng 1.6.58 and a static Release build with installation
under `lib`.

The complete retained original libpng archive was independently rehashed as
1,070,096 bytes, SHA-256
`28eb403f51f0f7405249132cecfe82ea5c0ef97f1b32c5a65828814ae0d34775`, matching the
recipe. The preserved `CMakeLists.txt`, `LICENSE`, and CMake authors file were
extracted directly from that verified archive. `CMakeLists.txt` is 49,235 bytes,
SHA-256 `0de785364c9157b2f1097efe617131ae5f3fadf25ceceea748f389a0d1e45cf5`.
It defines ABI 16 and explicitly creates and installs the three aliases.

`contract.json` retains each source identity, original archive URLs, exact
derivation locations, alias mapping, and target hash from the selected historical
harvest. The verifier independently pins the complete contract at SHA-256
`571377bb80f7d92e5a3d37db8a2b7b82448f8d5859e4cafb91b188904de73afb` and rehashes
every preserved source before accepting its mappings. A conditional minizip
alias is excluded because this selected harvest already identifies
`lib/libminizip.a` as a regular file.

This is a cache-input identity check. It executes no Blender tests and establishes
no feature parity. Changed SQLite and codec recipes still rebuild separately.
