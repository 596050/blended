// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn span__FromSmallVector(){let r=blended_core::span_cases::span__FromSmallVector();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn span__AddConstToPointer(){let r=blended_core::span_cases::span__AddConstToPointer();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn span__IsReferencing(){let r=blended_core::span_cases::span__IsReferencing();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__DropBack(){let r=blended_core::span_cases::span__DropBack();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__DropBackAll(){let r=blended_core::span_cases::span__DropBackAll();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn span__DropFront(){let r=blended_core::span_cases::span__DropFront();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn span__DropFrontLargeN(){let r=blended_core::span_cases::span__DropFrontLargeN();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn span__DropFrontAll(){let r=blended_core::span_cases::span__DropFrontAll();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn span__TakeFront(){let r=blended_core::span_cases::span__TakeFront();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__TakeFrontLargeN(){let r=blended_core::span_cases::span__TakeFrontLargeN();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn span__TakeBack(){let r=blended_core::span_cases::span__TakeBack();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__TakeBackLargeN(){let r=blended_core::span_cases::span__TakeBackLargeN();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn span__Slice(){let r=blended_core::span_cases::span__Slice();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__SliceEmpty(){let r=blended_core::span_cases::span__SliceEmpty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn span__SliceRange(){let r=blended_core::span_cases::span__SliceRange();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__SliceLargeN(){let r=blended_core::span_cases::span__SliceLargeN();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn span__Contains(){let r=blended_core::span_cases::span__Contains();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn mutable_span__Contains(){let r=blended_core::span_cases::mutable_span__Contains();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn span__Count(){let r=blended_core::span_cases::span__Count();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn span__FromInitializerList(){let r=blended_core::span_cases::span__FromInitializerList();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn span__FromVector(){let r=blended_core::span_cases::span__FromVector();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn span__FromArray(){let r=blended_core::span_cases::span__FromArray();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__Fill(){let r=blended_core::span_cases::span__Fill();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn span__FillIndices(){let r=blended_core::span_cases::span__FillIndices();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn span__SizeInBytes(){let r=blended_core::span_cases::span__SizeInBytes();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn span__FirstLast(){let r=blended_core::span_cases::span__FirstLast();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn span__FirstLast_OneElement(){let r=blended_core::span_cases::span__FirstLast_OneElement();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__ContainsPtr(){let r=blended_core::span_cases::span__ContainsPtr();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn span__FirstIndex(){let r=blended_core::span_cases::span__FirstIndex();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn span__CastSameSize(){let r=blended_core::span_cases::span__CastSameSize();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn span__CastSmallerSize(){let r=blended_core::span_cases::span__CastSmallerSize();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn span__CastLargerSize(){let r=blended_core::span_cases::span__CastLargerSize();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn span__VoidPointerSpan(){let r=blended_core::span_cases::span__VoidPointerSpan();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn span__CopyFrom(){let r=blended_core::span_cases::span__CopyFrom();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn span__ReverseIterator(){let r=blended_core::span_cases::span__ReverseIterator();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn span__ReverseMutableSpan(){let r=blended_core::span_cases::span__ReverseMutableSpan();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,12);}
#[test]
#[allow(non_snake_case)]
fn span__MutableReverseIterator(){let r=blended_core::span_cases::span__MutableReverseIterator();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,11);}
#[test]
#[allow(non_snake_case)]
fn span__Constexpr(){let r=blended_core::span_cases::span__Constexpr();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn span__ImplicitConversions(){let r=blended_core::span_cases::span__ImplicitConversions();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,0);}
#[test]
#[allow(non_snake_case)]
fn span__Comparison(){let r=blended_core::span_cases::span__Comparison();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,9);}
