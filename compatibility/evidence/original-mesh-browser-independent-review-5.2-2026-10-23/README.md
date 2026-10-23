# Independent review of original mesh browser evidence

This directory records a read-only independent review of the retained original bevel and operators invocations. It adds **zero original application executions, zero infrastructure test executions, and zero new original test passes**. The reported case outcomes belong to the already retained runs. No production code, original test, oracle, fixture, or previous evidence was changed by this review.

## Reviewed outcomes

| Original driver | Native observations | Browser observations | Actual runtime / Chrome / capture exit | Whole-invocation qualified pass pairs |
| --- | --- | --- | --- | ---: |
| `bmesh_bevel` | 88 passed | 88 passed | 0 / 0 / 0 | 88 in the reviewed separate-profile summary |
| `operators` | 105 passed | 103 passed, 2 failed | 1 / 0 / 1 | 0 |

The two original operator failures are `IcosphereFill` and `IcosphereFillUseBeautyFalse`. Both report `The edge topology is different` and `Mesh Validation : Valid`. Both pass against the same original native fixture. All 105 names execute, with no missing, unexpected, or duplicated cases. The 103 browser pass observations remain diagnostics from a failed complete invocation.

## Independent checks

The review compared exact native arguments and working directories, the original comparison-enabling `--run-all-tests` branch, absence of oracle-update environment keys, and original source/helper/fixture identities. Actual mounted bytes agree before main and at the original `Blender quit` boundary. Raw console events, stdout/stderr, case names, original comparison results, browser state, and process exits reconcile.

The bevel evidence has 633 captured events: final case at sequence 627, original quit at 630, byte readback at 631, and the real runtime exit at 632. The operators evidence has 774 events: final case at 752, original quit at 771, byte readback at 772, and the real runtime exit at 773. Byte preservation is observed before Emscripten teardown, not after exit.

The actual pinned Essentials archive and its JavaScript, Wasm, and preload-data members were independently hashed and compared with the receipts. The four operators launcher/capture files were reconstructed exactly from the reviewed bevel v2 files and the retained literal edit manifest. All 105 operators summary rows match their raw outcomes, source/specification identities, and original log locations.

The earlier unqualified bevel v1 receipt remains unchanged. Its post-exit file observation failed after WasmFS destruction; the versioned v2 observer repaired the measurement timing without changing the original tests or converting that earlier attempt into a pass.

All five retained operators triage C++ files match the verified original source archive byte for byte, and the three runtime-context references match their hashes. The triage correctly leaves causation unresolved. The actual result establishes original comparator failures; it does not prove a defect in fill, scanfill, the comparator, sorting, floating-point behavior, or SIMD.

## Scope and audit provenance

The reviewed invocations use explicitly separate custom launcher profiles. They do not qualify the original UI shell, configured CTest execution, complete source-to-binary correspondence, GPU behavior, or whole-application parity. The prior 829-case unittest ledger is unchanged.

`report.json` binds the reviewed summaries, raw receipts, original inputs, launcher derivation, triage sources, and runtime identities. Paths are relative to the repository root; `../runtime` denotes retained sibling runtime inputs. The raw execution receipts remain authoritative for execution times and exits. This derived report summarizes review commands already executed and inspected in the session; it does not fabricate a new subprocess receipt or copy of an unavailable transcript.
