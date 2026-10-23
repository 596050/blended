# Fresh infrastructure verification after recovery and DPX integration

This is a newly captured execution over the restored normalizer, newly authored
normalizer regressions, and signed DPX source correction. It does not recreate
the lost earlier 369-test execution receipt.

The full repository infrastructure suite completed with exit 0:

```text
Ran 383 tests in 155.557s
OK
```

The capture measured 155.873591 seconds including process overhead. There were
no failures, errors or skips. All 145 captured source/configuration inputs had
the same byte counts and SHA-256 values before and after execution.

The command was the real `python3 -m unittest discover -s tests -q`, with
`BLENDED_INVENTORY_CMAKE` set to the installed CMake 4.4.4 executable. The receipt
binds the actual Python, CMake and C++ executables, full command, UTC timestamps,
stdout, stderr and input inventories. `capture.py` is the executed capture
program and refuses to overwrite an existing execution receipt.

Coverage includes the 31 newly written normalizer regressions and six DPX
numeric/recipe regressions, alongside existing infrastructure tests. The DPX
checks compile the actual pinned helper body and descriptor enum under
explicit unsigned 32-bit and 64-bit type aliases. They exercise the actual
dependency-patching block and reject changed source or patch bytes before
mutation. These are host-compiler arithmetic and recipe checks.

This execution runs zero original Blender cases. It establishes no successful
Wasm DPX decode, original ImBuf completion, browser UI parity or full application
parity. A new source-built browser artifact must still run the unchanged
original invocation and supply every required parent and subtest observation.
