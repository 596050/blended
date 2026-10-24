// SPDX-License-Identifier: GPL-3.0-or-later
// Supplementary product regressions, not translated Blender runtime cases.
use blended_core::{array_ops as a, csv_fields as csv, disjoint_set::DisjointSet};
use std::cell::Cell;

#[test]
fn csv_custom_delimiter_quote_and_non_utf8_bytes_are_retained() {
    let options=csv::Options{delimiter:b';',quote:b'\'',quote_escape_chars:vec![b'\'',b'\\'],..Default::default()};
    let input=b"'a;b';\xff;\n";
    let (end,fields)=csv::parse_record_fields(input,0,&options).unwrap();
    assert_eq!(end,input.len());
    assert_eq!(fields,vec![&b"a;b"[..],&b"\xff"[..],&b""[..]]);
}

#[test]
fn csv_multiline_retry_preserves_data_and_header_precedes_callbacks() {
    let options=csv::Options{chunk_size_bytes:1,..Default::default()};
    let seen=Cell::new(false);let mut header=Vec::new();
    let chunks=csv::parse_csv_in_chunks(b"a,b\n1,\"two\nlines\"\n3,4\n",&options,|fields|{
        assert!(!seen.get());seen.set(true);header=fields.iter().map(|f|f.to_vec()).collect();
    },|records|{assert!(seen.get());records.iter().map(|r|r.iter().map(|f|f.to_vec()).collect::<Vec<_>>()).collect::<Vec<_>>()}).unwrap();
    assert_eq!(header,vec![b"a".to_vec(),b"b".to_vec()]);
    let records:Vec<_>=chunks.into_iter().flatten().collect();
    assert_eq!(records,vec![vec![b"1".to_vec(),b"two\nlines".to_vec()],vec![b"3".to_vec(),b"4".to_vec()]]);
}

#[test]
fn pointer_search_uses_identity_even_for_equal_text() {
    let first=vec![b'a',0];let second=vec![b'a',0];
    let a=first.as_ptr();let b=second.as_ptr();assert_ne!(a,b);
    let storage=[a,b,a];assert_eq!(a::find_index(&storage,3,&b),1);assert_eq!(a::rfind_index(&storage,3,&a),2);
}

#[test]
fn adjacent_dedup_retains_nonconsecutive_duplicates_and_storage_tail() {
    let mut data=[1,1,2,1,1,99];
    let n=a::deduplicate_ordered(&mut data,5);assert_eq!(n,3);assert_eq!(&data[..n],&[1,2,1]);assert_eq!(data[5],99);
}

#[test]
fn union_rank_root_identity_and_repeated_join_remain_stable() {
    let mut set=DisjointSet::new(8);
    assert_eq!(set.join(2,3),2);assert_eq!(set.join(4,5),4);assert_eq!(set.join(2,4),2);
    assert_eq!(set.find_root_readonly(5),2);assert_eq!(set.find_root(5),2);assert_eq!(set.join(5,3),2);
    assert!(!set.in_same_set(0,5));assert_eq!(set.join(0,5),2);assert!(set.in_same_set(0,3));
}
