// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn math_half__half_to_float_scalar(){let r=blended_core::pixel_format_cases::math_half__half_to_float_scalar();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,23);}
#[test]
#[allow(non_snake_case)]
fn math_half__float_to_half_scalar(){let r=blended_core::pixel_format_cases::math_half__float_to_half_scalar();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,32);}
#[test]
#[allow(non_snake_case)]
fn math_half__float_to_half_make_finite_scalar(){let r=blended_core::pixel_format_cases::math_half__float_to_half_make_finite_scalar();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,35);}
#[test]
#[allow(non_snake_case)]
fn math_half__half_to_float_array(){let r=blended_core::pixel_format_cases::math_half__half_to_float_array();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,14);}
#[test]
#[allow(non_snake_case)]
fn math_half__half_to_float_array_flush_to_zero(){let r=blended_core::pixel_format_cases::math_half__half_to_float_array_flush_to_zero();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,8);}
#[test]
#[allow(non_snake_case)]
fn math_half__float_to_half_array(){let r=blended_core::pixel_format_cases::math_half__float_to_half_array();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,14);}
#[test]
#[allow(non_snake_case)]
fn math_half__float_to_half_clamp_array(){let r=blended_core::pixel_format_cases::math_half__float_to_half_clamp_array();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,18);}
#[test]
#[allow(non_snake_case)]
fn math_half__float_to_half_make_finite_array(){let r=blended_core::pixel_format_cases::math_half__float_to_half_make_finite_array();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,18);}
#[test]
#[allow(non_snake_case)]
fn normalized_int__roundtrip(){let r=blended_core::pixel_format_cases::normalized_int__roundtrip();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,7);}
