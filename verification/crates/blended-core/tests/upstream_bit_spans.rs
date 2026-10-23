// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn bit_span__DefaultConstructor(){let r=blended_core::bit_span_cases::bit_span__DefaultConstructor();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__Iteration(){let r=blended_core::bit_span_cases::bit_span__Iteration();assert_eq!(r.assertions,108);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__MutableIteration(){let r=blended_core::bit_span_cases::bit_span__MutableIteration();assert_eq!(r.assertions,2);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__SubscriptOperator(){let r=blended_core::bit_span_cases::bit_span__SubscriptOperator();assert_eq!(r.assertions,14);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__RangeConstructor(){let r=blended_core::bit_span_cases::bit_span__RangeConstructor();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__Set(){let r=blended_core::bit_span_cases::bit_span__Set();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__SetEmpty(){let r=blended_core::bit_span_cases::bit_span__SetEmpty();assert_eq!(r.assertions,0);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__SetSliced(){let r=blended_core::bit_span_cases::bit_span__SetSliced();assert_eq!(r.assertions,1280);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__IsBounded(){let r=blended_core::bit_span_cases::bit_span__IsBounded();assert_eq!(r.assertions,19);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__CopyFrom(){let r=blended_core::bit_span_cases::bit_span__CopyFrom();assert_eq!(r.assertions,100);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__InPlaceOr(){let r=blended_core::bit_span_cases::bit_span__InPlaceOr();assert_eq!(r.assertions,6400);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__InPlaceAnd(){let r=blended_core::bit_span_cases::bit_span__InPlaceAnd();assert_eq!(r.assertions,6400);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__ForEach1(){let r=blended_core::bit_span_cases::bit_span__ForEach1();assert_eq!(r.assertions,1);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__ForEach1Cancel(){let r=blended_core::bit_span_cases::bit_span__ForEach1Cancel();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__FindFirst1Index(){let r=blended_core::bit_span_cases::bit_span__FindFirst1Index();assert_eq!(r.assertions,7);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__FindFirst0Index(){let r=blended_core::bit_span_cases::bit_span__FindFirst0Index();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__or_bools_into_bits(){let r=blended_core::bit_span_cases::bit_span__or_bools_into_bits();assert_eq!(r.assertions,10);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__to_index_ranges_small(){let r=blended_core::bit_span_cases::bit_span__to_index_ranges_small();assert_eq!(r.assertions,3);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_span__to_index_ranges_all_ones(){let r=blended_core::bit_span_cases::bit_span__to_index_ranges_all_ones();assert_eq!(r.assertions,2);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_group_vector__DefaultConstruct(){let r=blended_core::bit_span_cases::bit_group_vector__DefaultConstruct();assert_eq!(r.assertions,1);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_group_vector__Construct(){let r=blended_core::bit_span_cases::bit_group_vector__Construct();assert_eq!(r.assertions,3);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_group_vector__CopyConstruct(){let r=blended_core::bit_span_cases::bit_group_vector__CopyConstruct();assert_eq!(r.assertions,62);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_group_vector__foreachAnd(){let r=blended_core::bit_span_cases::bit_group_vector__foreachAnd();assert_eq!(r.assertions,12);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bitmap__empty_is_all_unset(){let r=blended_core::bit_span_cases::bitmap__empty_is_all_unset();assert_eq!(r.assertions,10);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bitmap__find_first_unset_empty(){let r=blended_core::bit_span_cases::bitmap__find_first_unset_empty();assert_eq!(r.assertions,1);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bitmap__find_first_unset_full(){let r=blended_core::bit_span_cases::bitmap__find_first_unset_full();assert_eq!(r.assertions,1);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bitmap__find_first_unset_middle(){let r=blended_core::bit_span_cases::bitmap__find_first_unset_middle();assert_eq!(r.assertions,2);assert!(r.passed(),"{r:?}");}
