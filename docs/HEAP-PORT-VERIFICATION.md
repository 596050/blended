# Heap and priority-queue test-port verification

## Verified implementation

Reference: Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`.
Verified implementation: `df61b87fa3b2b5a0751100e427eab11d7205ad5a`.
[Run 40019426923](https://github.com/596050/blended/actions/runs/40019426923) passed fresh native Rust, original C++ reference execution, independent native/Chromium assertion comparison, deterministic input oracles, negative implementation controls and actual public-URL testing. The separate full-completeness job failed because the whole Blender suite remains unfinished.

| Complete original runtime test file | Cases | Assertion sites, including helpers | Executed assertions |
| --- | ---: | ---: | ---: |
| BLI_heap_test.cc | 15 | 23 | 11,086 |
| BLI_heap_simple_test.cc | 8 | 15 | 3,188 |
| BLI_inplace_priority_queue_test.cc | 6 | 28 | 2,026 |
| Added | 29 | 66 | 16,300 |

The combined implemented suite contains **367 unique Blender runtime cases and 33,104 assertion events**. Its total native Rust suite is **390**: 367 Blender cases, three Cycles integer cases and 20 product/safety/regression tests. The two new product regressions test handle/payload association after priority updates and the distinct equal-key ordering policies; they are not labelled upstream Blender ports. Six compile-time assertions remain separate.

## Source fidelity

The generator locks all three complete original files by SHA-256, preserves upstream case identities and original lines, and reproduces the committed Rust cases and native runners. Original snapshots are under `tests/upstream/blender`. `compatibility/heap-ports.json` records all cases, source hashes, helper sites and original loop-expanded counts. `compatibility/assertion-contracts.lock.json` binds the reviewed targets; these hashes are not automatically refreshed during CI.

Assertions inside original random-test helpers remain assertions in the translated helpers, not copied expected outputs. The 1,024/2,048-item tests, 1,000-element priority tests, original seeds and full loops remain. `EXPECT_LE` retains operand order; it cannot be treated as symmetric equality. Actual pointer payload assertions use actual pointer identity, not text equality. C++ integer-pointer payload tokens use bounded i32 values; safe stable node indices replace allocation addresses that these tests do not inspect. The original pointer-decrement range helper uses a safe reverse slice loop with the same writes and order.

The priority queue retains shared externally mutable `Cell<i32>` storage, so an edit is observable before the corresponding priority notification. Copies of Boolean or priority snapshots would not preserve this contract. MinHeap and SimpleMinHeap have separate implementations because their equal-key insertion policies differ in the pinned sources.

## Independent execution and randomized inputs

Original C++ test bodies remain unchanged. Include-only diagnostic recording evaluates operands once and still invokes the pinned bundled GoogleTest assertions. The explicit Rust shadow records the same case boundaries and ordered events. All 33,104 assertion events reconcile under the documented comparison rules. Eight native and nine browser floating differences remain in older colour tests; no additional difference comes from the heap cases and no tolerance was widened.

Sorted output alone cannot establish that random inputs were preserved. `tools/verify_heap_inputs.py` independently compiles the original BLI_rand.hh with four unedited rand.cc functions. The stack wrapper omits only unused allocator hooks. It compares five 3,000-value sequences (seeds 0, 1234, 4321, 9876, 5321) and permutations of 1, 2, 100, 1,024 and 2,048 items. **All 15,000 values and 3,175 shuffled items match exactly** in newly compiled native Rust and Chromium WebAssembly. The original fixed-full-array-modulus shuffle is retained; substituting a standard shuffle would change the fixtures. The 3,000 seed-zero draws include the original 1,000 initial values and 2,000 subsequent mutation draws.

[Immutable input-oracle results and raw values](https://github.com/596050/blended/tree/19abc219cd1ccb7e2dd4090c23710638f30959d8/verification/evidence/heap-inputs) · [Original C++/native/browser assertion transcripts](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40019426923)

## Test-first and negative evidence

[Run 40017475165](https://github.com/596050/blended/actions/runs/40017475165) generated and committed the original cases at `b81ca35fa1617811220559a2a6fa1cd83d32031b` before `priority_heaps.rs` existed. Cargo reported E0583, the missing implementation module. This is missing-implementation evidence, not 29 executed assertion failures. The later native implementation and integrated verification passed.

`tools/verify_heap_sensitivity.py` copies the unchanged source tests into isolated shadows. Making removal a no-op causes the original `heap.RangeRemove` assertions to fail while `heap.One` still passes. Making priority increase a no-op causes `inplace_priority_queue.IncreasePriority` to fail while `BuildSmall` still passes. Both controls work natively and in real Chromium WebAssembly, with original assertion counts retained and invalid indices rejected. Compiler failures, panics and browser traps are not accepted as successful negative checks. [Immutable sensitivity results and logs](https://github.com/596050/blended/tree/19abc219cd1ccb7e2dd4090c23710638f30959d8/verification/evidence/heap-sensitivity)

These diagnostic browser executions are local CI checks. Separately, the production workbench was published and exercised at its actual immutable public URL: [367-case deployment](https://rawcdn.githack.com/596050/blended/19abc219cd1ccb7e2dd4090c23710638f30959d8/index.html).

## Pinned behaviour and limits

The original `InplacePriorityQueue::pop_index()` decrements its size and swaps/heapifies only when the new size is greater than one. With two remaining entries this can repeat the penultimate index on the final pop. The compatibility implementation retains this pinned behaviour and explicitly comments it; it does not silently repair the reference while claiming identity. The original ordering tests alone do not prove unique exhaustive removal. Treat this as a versioned compatibility component, not a correctness guarantee for all priority-queue applications.

The Rust in-place queue currently covers the i32/default-order behaviour exercised by these original cases, not every generic type or custom comparator. Stable node handles are not allocator-layout parity, and memory/performance parity is not established. These core-library additions do not create mesh-editing tools or a Blender rendering engine.

## Completion accounting

The current heuristic audit contains 5,859 source candidates, 373 reviewed mappings (367 runtime plus six compile-time) and 5,486 unmapped candidates. Runtime enumeration remains incomplete and the remaining runtime count is unknown, not zero. Missing fixtures, unreadable sources and unmapped test families remain blockers. Passing this batch does not complete Blender's tests or establish full application feature parity.
