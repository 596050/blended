// SPDX-License-Identifier: GPL-3.0-or-later
// Additional adapter safety checks. These are not counted as upstream Blender cases.
use blended_core::{bit_spans as b,string_refs as s};
use core::cell::Cell;
#[test]fn bit_view_rejects_storage_overrun(){let words=[Cell::new(0)];assert!(std::panic::catch_unwind(std::panic::AssertUnwindSafe(||b::BitSpan::new(&words,b::IndexRange::new(63,2)))).is_err());}
#[test]fn slice_keeps_alias_and_original_bit_offset(){let words=[Cell::new(0),Cell::new(0)];let parent=b::MutableBitSpan::new(&words,b::IndexRange::from_size(128));let child=parent.slice(b::IndexRange::new(60,10));child.bit(5).set(true);assert_eq!(words[1].get(),2);assert!(parent.bit(65).test());}
#[test]fn trailing_word_padding_is_not_an_extra_zero_bit(){let v=b::BitVector::with_fill(65,true);assert_eq!(b::find_first_0_index(&v),None);}
#[test]fn grouped_clone_has_independent_backing(){let a=b::BitGroupVector::new(3,65);a.group(1).bit(64).set(true);let copy=a.clone();copy.group(1).bit(64).set(false);assert!(a.group(1).bit(64).test());assert!(!copy.group(1).bit(64).test());}
#[test]fn byte_view_preserves_embedded_nul(){let v=s::StringRef::from_bytes(b"a\0b");assert_eq!(v.size(),3);assert_eq!(v.substr(1,2).as_bytes(),b"\0b");}
#[test]fn nul_terminated_view_rejects_missing_terminator(){assert!(std::panic::catch_unwind(||s::StringRefNull::from_cstr(b"missing")).is_err());}
#[test]fn utf8_truncation_preserves_complete_character(){let mut out=[255;5];s::StringRef::from_bytes("a€b".as_bytes()).copy_utf8_truncated(&mut out);assert_eq!(&out,b"a\xe2\x82\xac\0");}
#[test]fn string_slice_keeps_the_backing_address(){let bytes=b"abcde";let s=s::StringRef::from_bytes(bytes).substr(2,2);assert_eq!(s.data(),bytes.as_ptr().wrapping_add(2));assert_eq!(s.as_bytes(),b"cd");}
