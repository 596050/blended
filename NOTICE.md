# Copyright, licensing and attribution

Original Blended code is GPL-3.0-or-later unless a file specifies otherwise, and is provided without warranty. Retain full licence texts and component-specific notices supplied with upstream sources.

Translated Blender tests retain Apache-2.0 identifiers and Blender Authors copyright notices in original snapshots and generated Rust files. Expected values, tolerances and provenance remain traceable to the pinned commit. The complete Blender test port remains unfinished.

The heap/priority-queue, deterministic RNG, array, CSV, Murmur2A, disjoint-set, string and search adaptations use GPL-2.0-or-later Blender source. Consult each file's specific copyright year and SPDX identifier. Relevant RNG notices also include Copyright 2001-2002 NaN Holding BV. The supplemental C++ hash oracle compiles original hash_mm2a.cc unchanged with its header; the RNG oracle retains original functions and headers. The string oracle extracts unedited functions from pinned string.cc. Their original licences and attribution remain applicable. Supplemental drivers and product regressions retain their own identifiers.

Solarxy is Copyright Marko Koljancic and contributors, GPL-3.0-or-later at the pinned revision. The initial experimental browser studio compiled Solarxy; those are not newly implemented Blender features. Its rendering blocker remains distinct from the working Three.js modeller. Three.js is MIT-licensed. Blender and Cycles reference checkouts retain individual file licences. No complete Cycles renderer is compiled into the modeller.

Current conformance builds use a freshly compiled single Rust/WebAssembly module with corresponding source and upstream licence files. Earlier preview integrations used separately compiled modules; those historical records do not certify current merged builds. Preserved test-first logs are original CI evidence, not application code or extra upstream test cases.

Blended is independent and is not affiliated with the Blender Foundation or Solarxy's author.
