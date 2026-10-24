// SPDX-License-Identifier: GPL-3.0-or-later
// Supplemental product regressions, not translated Blender runtime cases.
use blended_core::{string_ops as s,string_search as search};
#[test]fn word_limit_preserves_unwritten_sentinel(){let mut words=[[-1,-1];3];assert_eq!(s::find_split_words(b" one two three",14,b' ',&mut words,2),2);assert_eq!(words,[[1,3],[5,3],[-1,-1]]);}
#[test]fn bounded_search_returns_original_storage_and_honours_needle_length(){let text=b"SEARCH here\0";assert_eq!(s::ncasestr(text,b"earcq",4),text.as_ptr().wrapping_add(1));assert!(s::ncasestr(text,b"earcq",5).is_null());assert_eq!(s::ncasestr(text,b"h",0),text.as_ptr().wrapping_add(5));}
#[test]fn valid_utf8_distance_counts_codepoints_and_transpositions(){assert_eq!(search::damerau_levenshtein_distance("a☯".as_bytes(),"☯a".as_bytes()),1);assert_eq!(search::damerau_levenshtein_distance("ñ".as_bytes(),b""),1);}
#[test]fn unique_name_truncation_does_not_split_valid_utf8(){let mut name=s::buffer("☯☯".as_bytes(),9);s::unique_name_into(&|v|v=="☯☯".as_bytes(),b"Name",b'.',&mut name);assert_eq!(s::c_string(&name),"☯.001".as_bytes());}
#[test]fn original_utf8_reverse_partition_first_codepoint_boundary_is_explicit(){let text="☯name\0".as_bytes();let part=s::partition(text,None,&[0x262f,0],true,true);assert_eq!(part.prefix_len,7);assert!(part.separator_ptr().is_null());let forward=s::partition(text,None,&[0x262f,0],true,false);assert_eq!(forward.prefix_len,0);assert_eq!(forward.suffix_bytes(),Some(b"name".as_slice()));}
