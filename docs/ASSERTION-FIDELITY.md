# Assertion-level fidelity

## Current verified subset

[Run 40049834310](https://github.com/596050/blended/actions/runs/40049834310), source `ab692209e9eb98248054ae90ead9b0258f1ab4da`, verifies **464 Blender runtime cases and 34,214 assertion events** against Blender `94363991e7dcf39e2d70614aa002ab6f67764a5d`. Native Rust and Chromium WebAssembly comparisons pass. Eight native and nine browser differences remain explicitly recorded within the corresponding original floating rules. The new string cases introduce no floating differences. No tolerance was widened.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40049834310/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/runs/40049834310/browser-comparison.json) · [Raw transcripts/build metadata](https://github.com/596050/blended/tree/assertion-fidelity-evidence/runs/40049834310)

## Preservation and comparison

Source snapshots and reviewed target hashes bind the registered identities. Generators must reproduce committed tests. Executable registries form an exact bijection with reviewed runtime contracts. Six compile-time mappings remain separate; unsupported/unported work remains visible to the completeness audit.

Original C++ test bodies are unchanged. An include-only recording overlay evaluates operands once and invokes pinned GoogleTest assertions. Rust recording runs in an explicit shadow checkout, not by altering production tests. Both record case boundaries and ordered assertion kinds, operands, outcomes and counts. Assertion-free smoke cases require boundary and negative-execution evidence, not invented assertions.

Exact equality stays exact. Original near tolerances and floating-equality rules are retained. Literal floating expectations are fixed. Equivalent numeric representations, symmetric equality operand order and upstream empty-range equality have documented normalisations. Ordered comparisons never permit operand reversal. Original vector-helper size checks and conditional element assertions remain. C-string comparisons are not converted into pointer comparisons, or vice versa. Fatal assertions preserve stop-on-failure behaviour with separate negative evidence.

## Pointer identity and additional original-reference oracles

New string tests compare actual returned storage pointers against original offsets. Their recorded addresses use pair-local alias/null labels for the string fixture because separate static literals have unrelated allocation layouts across implementations. This preserves the original equality assertion, not global allocation-layout parity. Older pointer-offset encodings remain unchanged. A wrong-address mutation fails the unchanged original test in native Rust and browser WebAssembly.

The independent original-C++ string oracle additionally compares exact relative offsets for 21,952 bounded searches and exact natural-order return values for 3,136 ordered pairs. All 25,088 results match in native Rust and browser WASM. The corpus is explicitly ASCII and C-locale scoped. [Current string details](STRING-OPS-PORT-VERIFICATION.md)

Earlier oracles retain their own scope: 15,000 exact random values/3,175 shuffle items and 31,776 streaming-hash outputs. These are supplemental differential inputs, not extra Blender ports. Likewise, deliberately broken implementations and infrastructure regressions do not increase upstream case totals.

The diagnostic browser runs are local CI checks. The production workbench is separately built, published and tested at its immutable public URL, verifying independent identities/counts and the WASM hash rather than trusting displayed totals.

## Failures and completion

Infrastructure regressions reject removed/extra/reordered/substituted assertions, changed kinds, loosened tolerances, false success flags, stale references, changed hashes and fabricated runtime denominators. Implementation mutations must produce the intended assertion failures while controls pass; compiler errors, panics and traps cannot substitute for detection.

Whole-suite completeness still fails. The implemented subset does not certify missing test-family coverage, arbitrary malformed inputs, every locale, full feature parity or competitive performance. Historical smaller runs retain their original scope and are not substituted for the latest combined execution.
