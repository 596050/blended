// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
#![allow(non_snake_case)]
use blended_core::compat_cases::{CASES,REPORTS,ASSERTION_COUNTS};
macro_rules! case { ($name:ident, $index:expr) => {
    #[test] fn $name() { let (upstream, run) = CASES[$index]; let report=REPORTS[$index](); assert_eq!(report.assertions,ASSERTION_COUNTS[$index],"{upstream}: assertion count"); assert!(report.passed(),"{upstream}: {report:?}"); assert!(run(), "{upstream}: ABI adapter"); }
}; }
case!(ClampVecWithFloats, 0);
case!(test_invert_v3_safe, 1);
case!(Clamp, 2);
case!(MinList, 3);
case!(MaxList, 4);
case!(InterpolateInt, 5);
case!(InterpolateFloat, 6);
case!(CeilToMultiple, 7);
case!(DivideCeil, 8);
case!(Sign, 9);
case!(sqrt, 10);
case!(safe_sqrt, 11);
case!(rcp, 12);
case!(safe_rcp, 13);
case!(exp, 14);
case!(log, 15);
case!(square, 16);
