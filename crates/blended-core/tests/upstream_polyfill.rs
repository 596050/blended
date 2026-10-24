// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source identities and original loop-expanded counts. Implementation follows.
macro_rules! original {($name:ident,$n:expr)=>{#[test] #[allow(non_snake_case)] fn $name(){let r=blended_core::polyfill_cases::$name();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,$n);}};}
original!(polyfill2d__TriangleCCW,1008);
original!(polyfill2d__SquareCCW,2048);
original!(polyfill2d__SquareCW,2048);
original!(polyfill2d__Starfleet,2048);
original!(polyfill2d__StarfleetDegenerate,3440);
original!(polyfill2d__3Colinear,1008);
original!(polyfill2d__4Colinear,2048);
original!(polyfill2d__UnorderedColinear,3440);
original!(polyfill2d__PlusShape,23040);
original!(polyfill2d__StarShape,9728);
original!(polyfill2d__UShape,15680);
original!(polyfill2d__Spiral,41984);
original!(polyfill2d__TestFlipCode,36720);
original!(polyfill2d__SelfIntersect,3280);
original!(polyfill2d__SelfTouch,23040);
original!(polyfill2d__SelfOverlap,22656);
original!(polyfill2d__TestDavData,105200);
original!(polyfill2d__Issue815,9728);
original!(polyfill2d__Issue207_1,18832);
original!(polyfill2d__Issue207_11,208880);
original!(polyfill2d__Issue1407,2048);
original!(polyfill2d__Issue1407_pt,3440);
original!(polyfill2d__IssueT40777_colinear,66560);
original!(polyfill2d__IssueT41986_axis_align,208880);
original!(polyfill2d__IssueT52834_axis_align_co_linear,396288);
original!(polyfill2d__IssueT67109_axis_align_co_linear_a,15680);
original!(polyfill2d__IssueT67109_axis_align_co_linear_b,15680);
original!(polyfill2d__IssueT67109_axis_align_co_linear_c,15680);
original!(polyfill2d__Issue103913_axis_align_co_linear_no_zero_area_tri,274560);
