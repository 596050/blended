# Assertion-level fidelity audit

## Current verified scope

Run [39918173966](https://github.com/596050/blended/actions/runs/39918173966) verified **131 Blender runtime cases and 1,049 ordered assertion events per implementation** against the pinned original C++ code, native Rust and Chromium WebAssembly. The original reference is `94363991e7dcf39e2d70614aa002ab6f67764a5d`; the audited project source is `2c7abe637e8eca6ea8937c871f406fa6ac123006`. No floating-value differences required a tolerance allowance after documented representation normalisations. The production workbench also passed separate actual public-URL tests.

[Native comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/native-comparison.json) · [Browser comparison](https://github.com/596050/blended/blob/assertion-fidelity-evidence/browser-comparison.json) · [Raw build and assertion evidence](https://github.com/596050/blended/tree/assertion-fidelity-evidence).

**This is not the entire Blender suite.** Remaining runtime families and parameter expansions are not certified. Cycles/product tests are not counted in these 131 Blender cases. The previously missing vector signed-zero hash assertion has now been ported and checked separately at compile time, with deliberate failing mutations on native and WASM targets. See [collection-port verification](COLLECTION-PORT-VERIFICATION.md).

## Comparison contract

The audit checks each case's ordered assertion kinds, operand values, outcome, execution count and comparison tolerance. Dropped, duplicated, reordered and substituted assertions fail. Literal floating expectations remain fixed; computed floating outputs may differ only within the original assertion rule, and every such difference is reported. The verified run had none.

Equivalent integer/float values are normalised; symmetric comparisons permit operand reversal; empty IndexRange equality ignores its irrelevant start just as upstream does. Pointer addresses are encoded as offsets in words within each test, while original C++ and Rust equality assertions still compare actual pointers. No tolerance is widened and no bitwise equality of all internal structures is claimed.

## Independent recording

Original BLI tests are built from the exact pinned Blender source and its pinned library submodule. Thirteen unique source files receive an added recording-header include after their hashes are verified. The original test bodies are unchanged. Arguments are evaluated once, recorded, and passed through Blender's bundled GoogleTest assertions. Raw XML, compiler information, binary hashes and overlay metadata are preserved.

Rust recording happens in a separate build-only shadow checkout. The checked-in production tests and implementation are not changed by that diagnostic overlay. Its patch and input hashes are retained. The same shadow core runs natively and in Chromium WebAssembly. This browser run is local CI instrumentation, not a deployment. Unmodified production tests and real public-URL execution are separate acceptance layers.

The pinned GoogleTest version is authoritative. Newer documentation must not silently change a test's comparison semantics, including nonfinite-value behaviour.

## Failure detection and publication

Negative infrastructure tests cover changed actual or expected values, changed tolerances, missing/duplicate/reordered cases and assertions, changed kinds, false success values, count-only stubs and wrong pointer offsets. Additional checks retain original loops, shared-reference aliasing, moved-from state, source hashes and exact runtime identities. The signed-zero compile-time guard is mutation-tested rather than represented by a runtime success stub.

The compatibility-workbench publishing job depends on ordinary native/WASM conformance and this original-reference fidelity audit. The separate whole-suite completeness job remains failed while coverage is missing. Publishing a clearly labelled alpha subset does not certify whole-suite completion.

## Reproduce

```sh
python3 -m unittest discover -s tests -p test_assertion_fidelity.py -v
python3 tools/assertion_fidelity.py shadow --output build/fidelity-shadow
(cd build/fidelity-shadow && cargo run --locked --quiet -p blended-core --example assertion_trace) > native.jsonl
python3 tools/assertion_fidelity.py compare --reference reference.jsonl --port native.jsonl --output comparison.json
python3 tools/verify_static_port.py --output build/static-port.json
```

CI records the full C++ build and Chromium commands. Trusted case identities and counts come from checked-out manifests/contracts, not a served success banner. Hashes and transcripts establish concrete evidence for exercised cases; they are not a proof of every possible behaviour or a substitute for porting the remaining suite.
