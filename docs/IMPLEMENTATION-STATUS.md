# Implementation status

## Verified source and deployment

The currently documented runtime implementation is `ab692209e9eb98248054ae90ead9b0258f1ab4da`, verified by [run 40049834310](https://github.com/596050/blended/actions/runs/40049834310). [Open the 464-case workbench](https://rawcdn.githack.com/596050/blended/51d30f5a549da822a9dc0945d353ef6414938092/index.html). Documentation and source-comment-only corrections may follow that tested runtime revision.

464 unique Blender runtime cases pass natively and at the actual public URL, with 34,214 expected assertion events. Original C++ versus native Rust and Chromium WebAssembly comparisons passed. Eight native and nine browser floating differences remain within original rules; no original tolerance or exact-equality rule was loosened. The full native Rust run passed 497 tests: 464 Blender, three Cycles and 30 product/safety/regression cases. Six compile-time assertions remain separate and pass positive/negative checks on both targets.

The latest 48-case batch ports the complete runtime declarations in BLI_string_test.cc, BLI_string_search_test.cc and BLI_string_utils_test.cc. Actual implementations cover bounded byte strings, natural comparison, formatting, splitting, escaping, naming and tested fuzzy-search operations. Original TEST_F fixture/helper behaviour is retained. An independent original-C++ oracle matched 3,136 natural-order results and 21,952 search offsets exactly. Four native/browser mutations fail unchanged tests while independent controls pass. [Details](STRING-OPS-PORT-VERIFICATION.md).

## Separate products and evidence layers

The compatibility workbench is not the modeller. The Three.js application remains an object-editing alpha with transforms, bounded undo/redo, basic materials, scene JSON, static OBJ/STL interchange and PNG output. Its legacy test button retains 17 cases. The new library tests do not add corresponding interactive Blender tools. The Solarxy/WebGPU renderer experiment remains independently blocked.

Fresh production builds, original-reference comparisons, local diagnostic browser checks and actual public-URL acceptance are distinct evidence categories. Historical 99/131/211/272/302/338/367/416-case records retain their original scope. Supplemental oracle inputs, mutation controls and infrastructure tests are not counted as extra upstream ports.

## Unfinished requirements

The complete Blender test port is not finished. The whole-suite completeness gate remains failed. The latest heuristic source audit contains 5,859 candidates, 470 mappings and 5,389 unmapped declarations. The complete runtime denominator is unknown. Previously identified vector type/layout compile-time conditions and extensive application-level families remain unported. Historical fixture downloads do not materialise payloads in a fresh checkout.

There is no full mesh/BMesh editor, sculpting, modifier or Geometry Nodes system, animation/rigging/simulation suite, compositor/video/tracking suite, Python add-on API compatibility, native `.blend` support or Cycles/EEVEE parity. The string batch does not implement the whole native search/ranking or UTF-8 subsystem, all locales or arbitrary invalid-input behaviour.

A complete port, complete-suite execution, application/workflow compatibility and competitive performance remain separate milestones.

[Machine-readable status](../evidence/TEST-PORT-STATUS.json) · [Whole-suite requirements](COMPLETE-TEST-PORT.md) · [Open completion issue #3](https://github.com/596050/blended/issues/3)
