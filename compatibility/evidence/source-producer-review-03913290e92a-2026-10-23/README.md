# Exact source producer review for the DPX checkpoint

This review preserves the exact workflow, matrix runner and browser probe from
Git commit `03913290e92a98cd9c45fdecf679072587c4dbe7`, whose tree is
`a3fbe996e97c8e872ca4d94a1c0f7283e9cb86ad`. It compares them with the previously
reviewed producer at `f25e69ed72fed2d31d7d65e657fd6515da4bd792`.

The workflow and matrix runner are byte-identical. The probe differs only in
one 64-character codec-manifest digest. The new exact digest binds the reviewed
DPX production patch. `capture.py` read both commits' Git objects, checked all
expected hashes and sizes, preserved the new source bytes, and wrote
`review.json`. It executed zero Blender tests.

`tools/reconcile_unittest_matrix.py` retains the original producer entry and
adds the separate rule `original-unittest-downloaded-sources-03913290e92a-v1`.
It still requires the exact source commit, all reviewed producer bytes, a
completed matching workflow run, exact matrices, unchanged source downloads
and complete original command expansion. The checkout and child working
directory remain source-derived and are never described as OS-observed.

## Newly captured infrastructure verification

`run_regressions.py` executed both test commands and captured their actual
process exits and logs under `regressions/`:

| Test command pattern | Tests | Result | Unittest elapsed time |
|---|---:|---|---:|
| `test_reconcile_unittest_matrix.py` | 68 | Passed, exit 0 | 151.349 s |
| `test_source_producer_profiles.py` | 9 | Passed, exit 0 | 0.057 s |

The complete capture elapsed 151.630825946 seconds. All selected implementation,
configuration and immutable reviewed-source input identities remain unchanged
before and after both executions. The exact lists, actual commands, timestamps
and log hashes are bound by `regressions/execution.json`.

The new tests reject cross-profile probe substitution even after self-consistent
repinning, changed reviewed source, relabelled source commits, unreviewed or
non-string rules, incomplete or mismatched workflow runs, and different harness
bytes. They also verify that the selected rule is propagated to matrix context.
Temporary unit-test run metadata is explicitly synthetic and is never saved as
an actual CI or Blender execution observation.

No completed DPX source build or image-decoding result is established here.
Actual new build and qualification artifacts must independently supply those
observations before any original case receives parity credit.

## Independent source review

A separate read-only review found no blocking issue. AST comparison with
published `32d488161133` identified only the new profile registry and changes to
`read_producer_compatibility` and `check_producer_matrix`; every other function
and class is unchanged. The old f25 constants, command expansion, artifact,
source, timing and outcome checks remain intact. All three saved 039 producer
sources were independently matched to their exact Git objects.

The reviewed normalizer is 84,840 bytes with SHA256
`0accf71173c8a5d6e281757c659851e6e6803e5bcb0dd1fa4aaff08ca0998036`.
The new regression file is 9,985 bytes with SHA256
`e7edf35b4cc371bc83156083027841e422a3fb84e778939d64cd2f2bb9c6962e`.
The reviewer inspected the captured 68+9 test result without rerunning it.
