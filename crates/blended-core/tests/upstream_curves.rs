// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn length_parameterize__FloatSimple(){let r=blended_core::curve_cases::length_parameterize__FloatSimple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,7);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__Float(){let r=blended_core::curve_cases::length_parameterize__Float();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,39);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__Float2(){let r=blended_core::curve_cases::length_parameterize__Float2();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,24);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__Float2Cyclic(){let r=blended_core::curve_cases::length_parameterize__Float2Cyclic();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,24);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__LineMany(){let r=blended_core::curve_cases::length_parameterize__LineMany();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,20);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__CyclicMany(){let r=blended_core::curve_cases::length_parameterize__CyclicMany();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,40);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__InterpolateColor(){let r=blended_core::curve_cases::length_parameterize__InterpolateColor();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,40);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__ArbitraryFloatSimple(){let r=blended_core::curve_cases::length_parameterize__ArbitraryFloatSimple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn length_parameterize__ArbitraryFloat2(){let r=blended_core::curve_cases::length_parameterize__ArbitraryFloat2();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,24);}
