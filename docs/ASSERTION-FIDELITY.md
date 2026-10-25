# Assertion-level fidelity

## Current verified subset

[Run 40209288469](https://github.com/596050/blended/actions/runs/40209288469), source `7a3dec93c2c02605834330b5de6872d6f1dbe4ad`, verifies **609 Blender runtime cases / 3,196,744 ordered assertion events per implementation** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Original-C++ versus native Rust and Chromium comparisons passed. Eight native and nine browser differences remain in older colour cases within original rules. The new map/view tests add no differences; no tolerance was widened. This is not whole-suite or universal bitwise equivalence.

[Native report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40209288469/native-comparison.json) · [Browser report](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40209288469/browser-comparison.json) · [Full evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40209288469).

## Preservation and execution

Pinned original identities, source snapshots, body hashes and reviewed target contracts are required. Generators reproduce committed translations. The runtime registry is a bijection with reviewed contracts; deleting a required contract shard cannot silently reduce coverage. Nineteen static predicates are separately mapped and verified by native/WASM compilers and deliberately false checks. Assertion-free runtime declarations retain real executed boundaries, not invented Boolean assertions.

C++ diagnostic instrumentation adds includes without editing original test bodies, evaluates operands once and still invokes pinned GoogleTest assertions. Rust recording uses an explicit shadow build. Case boundaries, ordered assertion kinds, operands, outcomes and counts are compared. Exact equality remains exact; original near/ULP rules remain. Literal expectations are fixed and permitted differences are reported. Ordered comparisons cannot reverse operands, and fatal assertions retain stopping behaviour.

Representation normalisations remain explicit: numeric encodings, symmetric equality operand order, upstream empty-range equality and relative pointer identities. Mask contents are recorded reversibly, not replaced by counts or hashes. New generic-span pointer comparisons still compare addresses, with within-allocation byte offsets recorded independently of pointee values. Original suite registration is once-only and not counted as runtime assertions.

## Full-event processing

Every stress-test assertion is compared in bounded batches using the reviewed comparator. Missing, duplicated, reordered, substituted and out-of-case events fail. Neither the earlier UTF-8 nor polygon loops are sampled or shortened. Whole-file hashes check transcript integrity, not semantic equivalence by themselves.

Chromium executes the full diagnostic module and transfers its complete tape in chunks. All original-C++, native and browser events are preserved losslessly as `.jsonl.gz`, with decompressed SHA-256 and byte counts verified. The diagnostic module still holds its tape; this is not a universal constant-memory claim. Production WASM is separately built and tested at its actual immutable public URL, validating source/reference identity, case counts and binary digest.

## Supplemental observations and negative controls

Original-code oracles separately verify random inputs, selected indices, geometric results, bit formats, string offsets and backing-storage behaviour that passing assertions alone may not fully distinguish. The latest original-header observer matches 107,101 words exactly against Rust, Chromium and an independent Python model. Only unordered key traversal is canonicalised; within-key value order, actual mutation and pointer offsets remain observable.

The first supplemental observer uncovered an upstream `clear_and_shrink()` declaration that fails to instantiate. That compile failure blocked publication. The final explicit corpus uses working `clear()` on both targets; original tests are unchanged and operational equivalence for the broken method is not claimed. [Scope and failure record](CONTAINER-VIEW-PORT-VERIFICATION.md).

Four new implementation-only mutations fail unchanged original tests while controls pass. Compiler errors, panics and traps are not substitutes for recorded assertion failures. Test-first missing-module logs are accurately distinguished from executed failing assertions. Supplemental observers, negative probes and product regressions are not additional Blender case counts.

## Reproduction and unfinished scope

The corresponding-source archive includes workflow and small JSON dependencies used by its tests. A fresh extraction passed all 304 Python regressions, separately from the Rust/C++/browser verification in CI. Larger evidence remains on immutable deployment commits and the run-specific assertion-evidence branch.

Whole-suite completeness still fails. The implemented subset does not certify unported families, every input, all platform capabilities, full Blender features or competitive performance. Historical runs retain their original revision and scope and are not substituted for current combined execution.
