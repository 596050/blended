# Copyright, licensing and attribution

Original Blended code is GPL-3.0-or-later unless an individual file specifies otherwise, and is provided without warranty. Retain full licence texts and component-specific notices supplied with upstream sources.

Translated Blender tests retain Apache-2.0 identifiers and Blender Authors copyright notices in original snapshots and generated Rust files. Expected values, tolerances and provenance remain traceable to the pinned commit. The complete Blender test port remains unfinished.

The UTF-8 invalid-input fixture is derived upstream from Markus Kuhn's UTF-8 decoder stress test, dated 2015-08-28, under CC BY 4.0. Its attribution and original source links remain in `tests/upstream/blender/BLI_string_utf8_test.cc`, and the translated fixture identifies the derivation. Do not remove that attribution when redistributing the test data.

The combining-character interval table is derived from the pinned `extern/wcwidth/wcwidth.c`. Its Markus Kuhn permission and warranty notice is preserved in full at `LICENSES/wcwidth-original-notice.txt`; generated Rust data identifies the original Git blob. `LICENSES/` is included in downloadable corresponding source. This is the original pinned table, not data copied from an untracked host Unicode package.

The heap/priority-queue, deterministic RNG, array, CSV, Murmur2A, disjoint-set, string/search and UTF-8 adaptations use GPL-2.0-or-later Blender source. Consult each file's exact year, authors and SPDX identifier. Relevant notices include Tom Tromey, Red Hat and NaN Holding BV where retained by upstream. Supplemental C++ oracles compile unedited original functions or complete implementations with pinned headers; their upstream notices remain applicable. Supplemental drivers and product-regression files have their own identifiers.

Solarxy is Copyright Marko Koljancic and contributors, GPL-3.0-or-later at the pinned revision. The initial experimental browser studio compiled Solarxy; its features are not newly implemented Blender features. Its rendering blocker remains distinct from the working Three.js modeller. Three.js is MIT-licensed. Blender and Cycles reference checkouts retain individual file licences. No complete Cycles renderer is compiled into the modeller.

Current conformance builds use a freshly compiled single Rust/WebAssembly module with corresponding source and upstream licence files. Earlier integrations used separately compiled modules; their historical evidence does not certify current merged builds. Test-first archives and losslessly compressed assertion transcripts are execution evidence, not extra upstream cases.

Blended is independent and is not affiliated with the Blender Foundation or Solarxy's author.
