// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn bit_ref__MaskFirstNBits(){let r=blended_core::collection_cases::bit_ref__MaskFirstNBits();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__MaskLastNBits(){let r=blended_core::collection_cases::bit_ref__MaskLastNBits();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__MaskSingleBit(){let r=blended_core::collection_cases::bit_ref__MaskSingleBit();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__IntContainingBit(){let r=blended_core::collection_cases::bit_ref__IntContainingBit();assert_eq!(r.assertions,16);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__Test(){let r=blended_core::collection_cases::bit_ref__Test();assert_eq!(r.assertions,16);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__Set(){let r=blended_core::collection_cases::bit_ref__Set();assert_eq!(r.assertions,2);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__Reset(){let r=blended_core::collection_cases::bit_ref__Reset();assert_eq!(r.assertions,1);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__SetBranchless(){let r=blended_core::collection_cases::bit_ref__SetBranchless();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__Cast(){let r=blended_core::collection_cases::bit_ref__Cast();assert_eq!(r.assertions,2);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_ref__MaskRangeBits(){let r=blended_core::collection_cases::bit_ref__MaskRangeBits();assert_eq!(r.assertions,8);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__DefaultConstructor(){let r=blended_core::collection_cases::bit_vector__DefaultConstructor();assert_eq!(r.assertions,1);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__CopyConstructorInline(){let r=blended_core::collection_cases::bit_vector__CopyConstructorInline();assert_eq!(r.assertions,8);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__CopyConstructorLarge(){let r=blended_core::collection_cases::bit_vector__CopyConstructorLarge();assert_eq!(r.assertions,6);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__MoveConstructorInline(){let r=blended_core::collection_cases::bit_vector__MoveConstructorInline();assert_eq!(r.assertions,7);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__MoveConstructorLarge(){let r=blended_core::collection_cases::bit_vector__MoveConstructorLarge();assert_eq!(r.assertions,7);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__SizeConstructor(){let r=blended_core::collection_cases::bit_vector__SizeConstructor();assert_eq!(r.assertions,131);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__SizeFillConstructor(){let r=blended_core::collection_cases::bit_vector__SizeFillConstructor();assert_eq!(r.assertions,128);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__IndexAccess(){let r=blended_core::collection_cases::bit_vector__IndexAccess();assert_eq!(r.assertions,9);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__Iterator(){let r=blended_core::collection_cases::bit_vector__Iterator();assert_eq!(r.assertions,100);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__Append(){let r=blended_core::collection_cases::bit_vector__Append();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn bit_vector__AppendMany(){let r=blended_core::collection_cases::bit_vector__AppendMany();assert_eq!(r.assertions,6);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn index_ranges_builder__Empty(){let r=blended_core::collection_cases::index_ranges_builder__Empty();assert_eq!(r.assertions,2);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn index_ranges_builder__Single(){let r=blended_core::collection_cases::index_ranges_builder__Single();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn index_ranges_builder__Multiple(){let r=blended_core::collection_cases::index_ranges_builder__Multiple();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn index_ranges_builder__Full(){let r=blended_core::collection_cases::index_ranges_builder__Full();assert_eq!(r.assertions,6);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__FindRangeEnd(){let r=blended_core::collection_cases::unique_sorted_indices__FindRangeEnd();assert_eq!(r.assertions,3);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__NonEmptyIsRange(){let r=blended_core::collection_cases::unique_sorted_indices__NonEmptyIsRange();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__NonEmptyAsRange(){let r=blended_core::collection_cases::unique_sorted_indices__NonEmptyAsRange();assert_eq!(r.assertions,3);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__FindSizeOfNextRange(){let r=blended_core::collection_cases::unique_sorted_indices__FindSizeOfNextRange();assert_eq!(r.assertions,4);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__FindStartOfNextRange(){let r=blended_core::collection_cases::unique_sorted_indices__FindStartOfNextRange();assert_eq!(r.assertions,5);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__SplitToRangesAndSpans(){let r=blended_core::collection_cases::unique_sorted_indices__SplitToRangesAndSpans();assert_eq!(r.assertions,6);assert!(r.passed(),"{r:?}");}
#[test]
#[allow(non_snake_case)]
fn unique_sorted_indices__FindContentRange(){let r=blended_core::collection_cases::unique_sorted_indices__FindContentRange();assert_eq!(r.assertions,8);assert!(r.passed(),"{r:?}");}
