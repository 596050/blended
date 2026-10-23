// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn heap__Empty(){let r=blended_core::heap_cases::heap__Empty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn heap__One(){let r=blended_core::heap_cases::heap__One();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn heap__Range(){let r=blended_core::heap_cases::heap__Range();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__RangeReverse(){let r=blended_core::heap_cases::heap__RangeReverse();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__RangeRemove(){let r=blended_core::heap_cases::heap__RangeRemove();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,513);}
#[test]
#[allow(non_snake_case)]
fn heap__Duplicates(){let r=blended_core::heap_cases::heap__Duplicates();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__Rand1(){let r=blended_core::heap_cases::heap__Rand1();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn heap__Rand2(){let r=blended_core::heap_cases::heap__Rand2();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn heap__Rand100(){let r=blended_core::heap_cases::heap__Rand100();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,101);}
#[test]
#[allow(non_snake_case)]
fn heap__ReInsertSimple(){let r=blended_core::heap_cases::heap__ReInsertSimple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__ReInsertRandom1(){let r=blended_core::heap_cases::heap__ReInsertRandom1();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn heap__ReInsertRandom2(){let r=blended_core::heap_cases::heap__ReInsertRandom2();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn heap__ReInsertRandom100(){let r=blended_core::heap_cases::heap__ReInsertRandom100();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,202);}
#[test]
#[allow(non_snake_case)]
fn heap__ReInsertRandom1024(){let r=blended_core::heap_cases::heap__ReInsertRandom1024();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2050);}
#[test]
#[allow(non_snake_case)]
fn heap__ReInsertRandom2048(){let r=blended_core::heap_cases::heap__ReInsertRandom2048();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4098);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleEmpty(){let r=blended_core::heap_cases::heap__SimpleEmpty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleOne(){let r=blended_core::heap_cases::heap__SimpleOne();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleRange(){let r=blended_core::heap_cases::heap__SimpleRange();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleRangeReverse(){let r=blended_core::heap_cases::heap__SimpleRangeReverse();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleDuplicates(){let r=blended_core::heap_cases::heap__SimpleDuplicates();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1025);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleRand1(){let r=blended_core::heap_cases::heap__SimpleRand1();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleRand2(){let r=blended_core::heap_cases::heap__SimpleRand2();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn heap__SimpleRand100(){let r=blended_core::heap_cases::heap__SimpleRand100();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,101);}
#[test]
#[allow(non_snake_case)]
fn inplace_priority_queue__BuildSmall(){let r=blended_core::heap_cases::inplace_priority_queue__BuildSmall();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,7);}
#[test]
#[allow(non_snake_case)]
fn inplace_priority_queue__DecreasePriority(){let r=blended_core::heap_cases::inplace_priority_queue__DecreasePriority();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn inplace_priority_queue__IncreasePriority(){let r=blended_core::heap_cases::inplace_priority_queue__IncreasePriority();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn inplace_priority_queue__PopAll(){let r=blended_core::heap_cases::inplace_priority_queue__PopAll();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1000);}
#[test]
#[allow(non_snake_case)]
fn inplace_priority_queue__ManyPriorityChanges(){let r=blended_core::heap_cases::inplace_priority_queue__ManyPriorityChanges();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1000);}
#[test]
#[allow(non_snake_case)]
fn inplace_priority_queue__IndicesAccess(){let r=blended_core::heap_cases::inplace_priority_queue__IndicesAccess();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,13);}
