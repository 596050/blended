# Copyright, licensing and attribution

Original Blended code is licensed under GNU GPL version 3 or later (SPDX: GPL-3.0-or-later). It is provided without warranty. The build includes the full GPL text from the pinned Solarxy source with its source distribution.

`crates/blended-core/src/compat_cases.rs` and `tests/upstream_math_vector.rs` translate tests from Blender, Copyright 2023 Blender Authors, licensed Apache-2.0. Their expected values and tolerances are retained, with Rust array/function adaptations. See the upstream file and licence at the commit in `upstream.lock.json`. The signed-zero hash static assertion now has a separate compile-time port. The complete Blender test suite remains unfinished.

Solarxy is Copyright Marko Koljancic and contributors, GPL-3.0-or-later at the pinned revision. The initial browser studio compiles Solarxy; its capabilities are not represented as newly implemented Blender features. Source attribution and third-party notices are retained. The build publishes the complete modified source snapshot alongside the WASM binary.

Blender and Cycles reference checkouts retain their own individual file licences. No Cycles renderer is compiled into this initial browser application.

Blended is independent and is not affiliated with the Blender Foundation or Solarxy's author.

The integration preview contains two unchanged, separately compiled conformance modules, not the merged candidate build. Their exact corresponding source archives and original notices are distributed alongside each module. Historical execution records are labelled separately from new local checks.
