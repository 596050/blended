// SPDX-License-Identifier: GPL-3.0-or-later
use blended_core::{math::*, blended_run_case};
#[test] fn empty_extrema_are_explicit() { assert_eq!(min3(&[]),None); assert_eq!(max3(&[]),None); }
#[test] fn invalid_divisors_are_rejected() { assert_eq!(divide_ceil3([1;3],[1,0,1]),None); }
#[test] fn overflow_is_rejected() { assert_eq!(ceil_multiple3([i32::MAX;3],[2;3]),None); }
#[test] fn invalid_case_is_not_a_pass() { assert_eq!(blended_run_case(u32::MAX),-1); }
