// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Original runtime identities, including the compile-time-only conversion case.
macro_rules! original_case {
    ($name:ident,$count:expr)=>{
        #[test]
        #[allow(non_snake_case)]
        fn $name(){
            let r=blended_core::span_cases::$name();
            assert!(r.passed(),"{:?}",r.failures);
            assert_eq!(r.assertions,$count);
        }
    };
}
original_case!(span__FromSmallVector,4);
original_case!(span__AddConstToPointer,1);
original_case!(span__IsReferencing,3);
original_case!(span__DropBack,3);
original_case!(span__DropBackAll,1);
original_case!(span__DropFront,4);
original_case!(span__DropFrontLargeN,2);
original_case!(span__DropFrontAll,1);
original_case!(span__TakeFront,3);
original_case!(span__TakeFrontLargeN,2);
original_case!(span__TakeBack,3);
original_case!(span__TakeBackLargeN,2);
original_case!(span__Slice,3);
original_case!(span__SliceEmpty,1);
original_case!(span__SliceRange,3);
original_case!(span__SliceLargeN,6);
original_case!(span__Contains,6);
original_case!(mutable_span__Contains,6);
original_case!(span__Count,5);
original_case!(span__FromInitializerList,5);
original_case!(span__FromVector,5);
original_case!(span__FromArray,3);
original_case!(span__Fill,5);
original_case!(span__FillIndices,5);
original_case!(span__SizeInBytes,2);
original_case!(span__FirstLast,4);
original_case!(span__FirstLast_OneElement,3);
original_case!(span__ContainsPtr,6);
original_case!(span__FirstIndex,3);
original_case!(span__CastSameSize,4);
original_case!(span__CastSmallerSize,2);
original_case!(span__CastLargerSize,2);
original_case!(span__VoidPointerSpan,1);
original_case!(span__CopyFrom,5);
original_case!(span__ReverseIterator,6);
original_case!(span__ReverseMutableSpan,12);
original_case!(span__MutableReverseIterator,11);
original_case!(span__Constexpr,1);
original_case!(span__ImplicitConversions,0);
original_case!(span__Comparison,9);
