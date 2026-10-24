// SPDX-License-Identifier: Apache-2.0
#[test]
#[allow(non_snake_case)]
fn string__Utf8InvalidBytesStrip(){let r=blended_core::utf8_cases::string__Utf8InvalidBytesStrip();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,156);}
#[test]
#[allow(non_snake_case)]
fn string__Utf8InvalidBytesSubstitute(){let r=blended_core::utf8_cases::string__Utf8InvalidBytesSubstitute();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,234);}
#[test]
#[allow(non_snake_case)]
fn string__Utf8InvalidBytesSubstitutePatterns(){let r=blended_core::utf8_cases::string__Utf8InvalidBytesSubstitutePatterns();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,14);}
#[test]
#[allow(non_snake_case)]
fn string__StringNLenUTF8(){let r=blended_core::utf8_cases::string__StringNLenUTF8();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,3);}
#[test]
#[allow(non_snake_case)]
fn string__StringNLenUTF8_Incomplete(){let r=blended_core::utf8_cases::string__StringNLenUTF8_Incomplete();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,44);}
#[test]
#[allow(non_snake_case)]
fn string__StrCopyUTF8_ASCII(){let r=blended_core::utf8_cases::string__StrCopyUTF8_ASCII();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrCopyUTF8_ASCII_Truncate(){let r=blended_core::utf8_cases::string__StrCopyUTF8_ASCII_Truncate();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrCopyUTF8_TruncateEncoding(){let r=blended_core::utf8_cases::string__StrCopyUTF8_TruncateEncoding();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,24);}
#[test]
#[allow(non_snake_case)]
fn string__StrCopyUTF8_TruncateEncodingMulti(){let r=blended_core::utf8_cases::string__StrCopyUTF8_TruncateEncodingMulti();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,216);}
#[test]
#[allow(non_snake_case)]
fn string__StrCopyUTF8_TerminateEncodingEarly(){let r=blended_core::utf8_cases::string__StrCopyUTF8_TerminateEncodingEarly();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,63);}
#[test]
#[allow(non_snake_case)]
fn string__StrPrintfUTF8_ASCII(){let r=blended_core::utf8_cases::string__StrPrintfUTF8_ASCII();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrPrintfUTF8_TerminateEncodingEarly(){let r=blended_core::utf8_cases::string__StrPrintfUTF8_TerminateEncodingEarly();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,63);}
#[test]
#[allow(non_snake_case)]
fn string__StrPrintfUTF8_TruncateEncodingMulti(){let r=blended_core::utf8_cases::string__StrPrintfUTF8_TruncateEncodingMulti();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,81);}
#[test]
#[allow(non_snake_case)]
fn string__Utf8OffsetFromIndex_ClampedIndex(){let r=blended_core::utf8_cases::string__Utf8OffsetFromIndex_ClampedIndex();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,16);}
#[test]
#[allow(non_snake_case)]
fn string__Utf8AsUnicodeStep(){let r=blended_core::utf8_cases::string__Utf8AsUnicodeStep();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1626112);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf32Empty(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf32Empty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf32Single(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf32Single();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf32Simple(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf32Simple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf32AllCombining(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf32AllCombining();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf32Complex(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf32Complex();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf32Invalid(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf32Invalid();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,9);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf32Empty(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf32Empty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,1);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf32Single(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf32Single();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf32Simple(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf32Simple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf32AllCombining(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf32AllCombining();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf32Complex(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf32Complex();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,6);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf32Invalid(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf32Invalid();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,9);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf8Empty(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf8Empty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf8Single(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf8Single();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf8Simple(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf8Simple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,5);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf8AllCombining(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf8AllCombining();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,7);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf8AllComplex(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf8AllComplex();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,11);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepNextUtf8Invalid(){let r=blended_core::utf8_cases::string__StrCursorStepNextUtf8Invalid();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,9);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf8Empty(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf8Empty();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf8Single(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf8Single();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,2);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf8Simple(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf8Simple();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,4);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf8AllCombining(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf8AllCombining();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,7);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf8Complex(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf8Complex();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,11);}
#[test]
#[allow(non_snake_case)]
fn string__StrCursorStepPrevUtf8Invalid(){let r=blended_core::utf8_cases::string__StrCursorStepPrevUtf8Invalid();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,9);}
