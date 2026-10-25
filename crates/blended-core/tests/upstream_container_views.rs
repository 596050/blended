// SPDX-License-Identifier: Apache-2.0
// Every runtime declaration in the two pinned original files; no stub passes.
macro_rules! original_case {($name:ident,$count:expr)=>{
 #[test] #[allow(non_snake_case)] fn $name(){
  let r=blended_core::container_view_cases::$name();
  assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,$count);
 }
};}
original_case!(multi_value_map__LookupNotExistant,2);
original_case!(multi_value_map__LookupExistant,5);
original_case!(multi_value_map__LookupMutable,5);
original_case!(multi_value_map__AddMultiple,10);
original_case!(multi_value_map__Keys,3);
original_case!(multi_value_map__Values,1);
original_case!(multi_value_map__Items,5);
original_case!(multi_value_map__UniquePtr,1);
original_case!(multi_value_map__MutableItems,2);
original_case!(GenericSpanTest__TypeConstructor,3);
original_case!(GenericSpanTest__BufferAndSizeConstructor,7);
original_case!(GenericSpanTest__MutableTypeConstructor,2);
original_case!(GenericSpanTest__MutableBufferAndSizeConstructor,6);
