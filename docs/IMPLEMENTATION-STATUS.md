# Implementation status

## Current verified implementation

Runtime source `7a3dec93c2c02605834330b5de6872d6f1dbe4ad` was verified by [run 40209288469](https://github.com/596050/blended/actions/runs/40209288469). [Open the 609-case public workbench](https://rawcdn.githack.com/596050/blended/55479ba6a6249846abc4c36d36440b27bfe106b4/index.html). Later documentation-only commits do not change that runtime implementation.

609 unique Blender cases pass natively and at the actual deployed Chromium URL, with 3,196,744 assertion executions. Independent original-C++ versus native Rust and browser comparisons passed. Eight native and nine browser floating differences remain in older colour cases under original rules; no tolerance was widened. The latest map/view cases add no differences.

The full native suite passes **679 runtime tests: 609 Blender, three Cycles and 67 separate product/safety/regression tests**. Nineteen compile-time predicates remain separately verified on both targets with deliberately false checks. Repeated assertions, diagnostic observations and mutation probes are not extra upstream cases.

## Latest implementation and evidence

The complete multivalue-map and generic-span test files add 13 runtime cases and 52 assertions. The implementation retains bucket insertion order, duplicates, live mutable lookups, owning-pointer key identity, exact type descriptors, pointer offsets and type-erased aliases to actual backing memory. Original fixture setup and all original comparisons are preserved. Ten supplemental product tests and seventeen Python source/audit regressions remain separate from the Blender count.

An original-header oracle matches 107,101 output words against native Rust, Chromium and an independent Python model, covering 1,024 map operations and integer/floating view lengths. Four deliberate implementation mutations fail unchanged original tests while controls pass. The first original-header build exposed a broken `clear_and_shrink()` declaration; that failure blocked publication and is retained. The supplemental corpus now uses supported `clear()` on both targets, with no original test changes and no claim of parity for the broken method. [Detailed verification](CONTAINER-VIEW-PORT-VERIFICATION.md)

Corresponding-source downloads now include workflow files and small reference-limit fixtures required by existing regression tests. A fresh extraction passed all 304 Python tests. That local archive check did not rerun Rust/C++; those are separately verified in the cited CI run.

## Remaining requirements and limits

The complete Blender test port remains unfinished and the whole-suite gate remains failed. The current heuristic source audit has **5,867 candidates, 628 mappings and 5,239 unmapped declarations**. Mappings comprise 609 runtime and 19 compile-time cases. The complete runtime denominator remains unknown. Conditional benchmarks, additional compile-time predicates, required platform/configuration coverage and extensive application-level families remain outstanding.

This batch does not certify all template types, arbitrary C++ lifecycle operations, native hash iteration, ABI, allocators, parallel scheduling, every input's memory safety or performance parity. Type-erased safe adapters cover Copy values and checked descriptors; raw constructors retain explicit unsafe preconditions. Primitive registration is the subset used by the original fixture, not the whole CPPType registry.

The workbench remains separate from the Three.js object-modeller alpha. New library tests are not new interactive tools or a rendering engine. The editor's legacy test button uses a 17-case ABI. The Solarxy/WebGPU experiment remains independently blocked. There is still no full mesh/BMesh editor, sculpting, modifiers/Geometry Nodes, animation/rigging/simulation, compositor/video/tracking, Python add-on compatibility, native `.blend` support or Cycles/EEVEE parity.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Completion issue #3](https://github.com/596050/blended/issues/3)
