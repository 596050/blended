// SPDX-License-Identifier: Apache-2.0
use blended_core::callable_utility_cases as c;
macro_rules! check {($name:ident,$func:ident,$count:expr)=>{#[test]fn $name(){let r=c::$func();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,$count);}}}
check!(function_ref_StatelessLambda,function_ref__StatelessLambda,1);
check!(function_ref_StatefullLambda,function_ref__StatefullLambda,1);
check!(function_ref_StandaloneFunction,function_ref__StandaloneFunction,1);
check!(function_ref_ConstantFunction,function_ref__ConstantFunction,1);
check!(function_ref_MutableStatefullLambda,function_ref__MutableStatefullLambda,3);
check!(function_ref_Null,function_ref__Null,3);
check!(function_ref_CopyDoesNotReferenceFunctionRef,function_ref__CopyDoesNotReferenceFunctionRef,1);
check!(function_ref_CopyDoesNotReferenceFunctionRef2,function_ref__CopyDoesNotReferenceFunctionRef2,1);
check!(function_ref_ReferenceAnotherFunctionRef,function_ref__ReferenceAnotherFunctionRef,2);
check!(function_ref_InitializeWithNull,function_ref__InitializeWithNull,1);
check!(function_ref_OverloadSelection,function_ref__OverloadSelection,2);
check!(function_ref_FalsyStdFunction,function_ref__FalsyStdFunction,4);
check!(function_ref_FalsyFunctionPointer,function_ref__FalsyFunctionPointer,2);
check!(random_access_iterator_mixin_DoublingIterator,random_access_iterator_mixin__DoublingIterator,5);
check!(SessionUID_GenerateBasic,SessionUID__GenerateBasic,2);
