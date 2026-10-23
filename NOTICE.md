# Copyright, licensing and attribution

Original Blended code is GPL-3.0-or-later unless a file specifies otherwise, and is provided without warranty. Retain the full licence texts and component-specific notices supplied with upstream source distributions.

Translated Blender tests retain their Apache-2.0 identifiers and Blender Authors copyright notices in source snapshots and generated Rust files. Expected results, tolerances and provenance remain traceable to the commit in `upstream.lock.json`. The complete Blender test port remains unfinished.

The heap/priority-queue implementation and deterministic RNG/shuffle adaptation use GPL-2.0-or-later Blender source. Relevant notices include Copyright 2023 Blender Authors and Copyright 2001-2002 NaN Holding BV. All rights reserved. The supplemental C++ input oracle extracts original rand.cc functions and includes original BLI_rand.hh; these retain their upstream licence and attribution. Consult individual source-file identifiers rather than assuming all source or test files have one licence.

Solarxy is Copyright Marko Koljancic and contributors, GPL-3.0-or-later at the pinned revision. The initial experimental browser studio compiled Solarxy; its features are not newly implemented Blender features. Its rendering blocker remains separate from the working Three.js modeller. Three.js is MIT-licensed. Blender and Cycles reference checkouts retain their individual file licences. No complete Cycles renderer is compiled into this modeller.

The current conformance workbench uses a freshly compiled single combined Rust/WebAssembly module, with the corresponding source archive and upstream licence files. Earlier integration-preview archives used two unchanged separately compiled modules; their historical results and source archives must not be represented as current merged-build verification.

Blended is independent and is not affiliated with the Blender Foundation or Solarxy's author.
