# Real duplicate GoogleTest names

The actual product BLI binary at Blender commit
`94363991e7dcf39e2d70614aa002ab6f67764a5d` lists `stack.Peek` twice. These are two
original registrations in different C++ namespaces:

| Runtime display name | Original declaration | Namespace |
| --- | --- | --- |
| `stack.Peek` | [`BLI_stack_cxx_test.cc:172`](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/source/blender/blenlib/tests/BLI_stack_cxx_test.cc#L172) | `blender::tests` |
| `stack.Peek` | [`BLI_stack_test.cc:97`](https://github.com/blender/blender/blob/94363991e7dcf39e2d70614aa002ab6f67764a5d/source/blender/blenlib/tests/BLI_stack_test.cc#L97) | `blender` |

The old inventory adapter rejected the duplicate and stopped before CTest
execution. That original failed capture is retained under
[`product-native-gtest-2026-10-23/BLI`](../product-native-gtest-2026-10-23/BLI/),
including both raw listings, its original capture script and an explicit
zero-execution failure receipt. No original assertion was edited.

## Regression and correction

`01-red.stderr.txt` records the focused regression failure: the adapter discarded
the actual capture by rejecting `stack.Peek`, and the source-location identity
helper did not yet exist. `02-green.stderr.txt` records all **31 infrastructure
checks passing** after the correction, including the real standalone CTest
configuration fixture. These infrastructure checks are not Blender feature
tests.

The corrected parser preserves each repeated name as a
`gtest_runtime_observation` with `identity_status: ambiguous_duplicate_name` and
an unresolved expansion obligation. It retains every raw listing line and adds
an explicit `ambiguous_duplicate_case_names` blocker. Its observation ID binds
the specific capture and line; it is not a permanent case identity. Unique-name
IDs retain their previous semantics. A repeated suite header is still rejected
as an ambiguous capture structure.

`gtest_source_case_id` provides a separate original-source identifier from the
source commit, verified repository-relative file path, original file SHA-256,
declaration line and runtime name. It does not use list order, artifact identity
or timestamps. Callers must verify the source file and reject any source-qualified
collision that remains. Missing source-location data remains unresolved.

## Actual original execution

The separate
[`BLI-source-identities` capture](../product-native-gtest-2026-10-23/BLI-source-identities/native-reference.json)
executes the unchanged original CTest invocation after the exact fixture
candidate set was hydrated. Its native GTest XML records **1,742 passed cases**
from 104 suites, including both `stack.Peek` declarations, with CTest exit 0 and
no skips. Registered and unfiltered listings contain the same 1,742 name
observations, including both repeated names. XML name multiplicities match
those observations exactly.

Every declaration file reported by the original XML was compared byte-for-byte
with the exact pinned source archive, and every reported line lies within that
file. Both `stack.Peek` cases therefore have distinct source-qualified IDs. The
native receipt SHA-256 is
`251cf1a315b0014d29eaca2cd5078a4adec375b637957bf9d7b4ef2944663dfe`.

This resolves the observed identity collision for the native capture. It does
not turn an anonymous duplicate listing into a fully identified inventory, and
it does not establish browser parity or whole-upstream completeness.
