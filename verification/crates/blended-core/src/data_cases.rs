// SPDX-FileCopyrightText: 2023-2025 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Complete source-locked translations; see compatibility/data-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::array_ops as a;
use crate::csv_fields as csv;
use crate::hash_mm2a::Murmur2A;
use crate::disjoint_set::DisjointSet;
use crate::data_structures::IndexRange;
use std::collections::BTreeMap;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(c_string($a)==c_string($b),stringify!($a C-string-equals $b),line!());}};}
fn c_string(s:&[u8])->&[u8]{&s[..s.iter().position(|&b|b==0).unwrap_or(s.len())]}
// EXPECT_EQ_ARRAY expands to exactly N element assertions, with no extra length assertion.
macro_rules! array_eq {($r:expr,$a:expr,$b:expr,$n:expr)=>{{let expected=&$a;let actual=&$b;for i in 0..$n{eq!($r,expected[i],actual[i]);}}};}
fn dedup_test(r:&mut Report,data:&mut [i32],expected:&[i32]){
 let original_len=data.len();let new_len=a::deduplicate_ordered(data,original_len);
 eq!(r,new_len,expected.len());array_eq!(r,data,expected,new_len);
 let test_len=a::deduplicate_ordered(data,new_len);
 eq!(r,test_len,expected.len());array_eq!(r,data,expected,new_len);
}
fn ranges_test(r:&mut Report,data:&[bool],expected:&[IndexRange]){
 let ranges=a::find_all_ranges(data,true);
 eq!(r,ranges.len(),expected.len());array_eq!(r,expected,ranges,expected.len());
}
fn max_test(r:&mut Report,values:a::VirtualInts<'_>,expected:Option<usize>){
 let result=a::max_element_index(&values);
 yes!(r,result.is_some()==expected.is_some());
 if let (Some(result),Some(expected))=(result,expected){eq!(r,result,expected);}
}
fn groups_test(r:&mut Report,ids:&[i32],mask:&[usize]){
 // Independent insertion-ordered VectorSet adapter: BTreeMap only finds the
 // stored insertion index; its sorted traversal is never used for expectations.
 let mut expected_ids=BTreeMap::new();let mut first=Vec::<i32>::new();let mut groups=Vec::<i32>::new();
 for &i in mask{
  if !expected_ids.contains_key(&ids[i]){let index=expected_ids.len() as i32;expected_ids.insert(ids[i],index);first.push(i as i32);}
  groups.push(expected_ids[&ids[i]]);
 }
 let mut group_indices=vec![0_i32;mask.len()];let mut first_indices=Vec::new();
 let count=a::group_ids_to_indices(ids,mask,&mut group_indices,Some(&mut first_indices));
 eq!(r,count,expected_ids.len());eq!(r,first_indices,first);
 let mut only=vec![0_i32;mask.len()];
 eq!(r,a::group_ids_to_indices(ids,mask,&mut only,None),count);
 eq!(r,only,groups);eq!(r,group_indices,groups);
}
#[derive(Default)]struct StrParseResult{success:bool,column_names:Vec<String>,records:Vec<Vec<String>>}
fn strings(fields:&[&[u8]])->Vec<String>{fields.iter().map(|f|String::from_utf8(f.to_vec()).expect("Original fixture is UTF-8")).collect()}
fn record_fields(s:&str)->Option<Vec<String>>{csv::parse_record_fields(s.as_bytes(),0,&csv::Options::default()).map(|(_,f)|strings(&f))}
fn csv_fields(s:&str,options:&csv::Options)->StrParseResult{
 let mut result=StrParseResult::default();
 let chunks=csv::parse_csv_in_chunks(s.as_bytes(),options,|header|{result.column_names=strings(header);},|records|{records.iter().map(|r|strings(r)).collect::<Vec<_>>()});
 if let Some(chunks)=chunks{result.success=true;for chunk in chunks{result.records.extend(chunk);}}
 result
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:20
pub fn array_utils__ReverseStringEmpty()->Report{let mut r=Report::default();
let mut data=*b"\0";a::reverse_prefix(&mut data,0);streq!(r,b"",&data);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:27
pub fn array_utils__ReverseStringSingle()->Report{let mut r=Report::default();
let mut data=*b"0\0";a::reverse_prefix(&mut data,1);streq!(r,b"0",&data);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:34
pub fn array_utils__ReverseString4()->Report{let mut r=Report::default();
let mut data=*b"0123\0";a::reverse_prefix(&mut data,4);streq!(r,b"3210",&data);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:41
pub fn array_utils__ReverseInt4()->Report{let mut r=Report::default();
let expected=[3_i32,2,1,0];let mut data=[0_i32,1,2,3];a::reverse_prefix(&mut data,4);array_eq!(r,expected,data,4);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:50
pub fn array_utils__FindIndexStringEmpty()->Report{let mut r=Report::default();
let data=*b"\0";let find=b'0';eq!(r,a::find_index(&data,0,&find),-1);eq!(r,a::rfind_index(&data,0,&find),-1);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:57
pub fn array_utils__FindIndexStringSingle()->Report{let mut r=Report::default();
let data=*b"0\0";let find=b'0';eq!(r,a::find_index(&data,1,&find),0);eq!(r,a::rfind_index(&data,1,&find),0);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:64
pub fn array_utils__FindIndexStringSingleMissing()->Report{let mut r=Report::default();
let data=*b"1\0";let find=b'0';eq!(r,a::find_index(&data,1,&find),-1);eq!(r,a::rfind_index(&data,1,&find),-1);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:71
pub fn array_utils__FindIndexString4()->Report{let mut r=Report::default();
let data=*b"0123\0";let find=b'3';eq!(r,a::find_index(&data,4,&find),3);eq!(r,a::rfind_index(&data,4,&find),3);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:78
pub fn array_utils__FindIndexInt4()->Report{let mut r=Report::default();
let data=[0_i32,1,2,3];let find=3;eq!(r,a::find_index(&data,4,&find),3);eq!(r,a::rfind_index(&data,4,&find),3);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:85
pub fn array_utils__FindIndexInt4_DupeEnd()->Report{let mut r=Report::default();
let data=[0_i32,1,2,0];let find=0;eq!(r,a::find_index(&data,4,&find),0);eq!(r,a::rfind_index(&data,4,&find),3);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:92
pub fn array_utils__FindIndexInt4_DupeMid()->Report{let mut r=Report::default();
let data=[1_i32,0,0,3];let find=0;eq!(r,a::find_index(&data,4,&find),1);eq!(r,a::rfind_index(&data,4,&find),2);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:99
pub fn array_utils__FindIndexPointer()->Report{let mut r=Report::default();
let mut data=[core::ptr::null::<u8>();4];let mut size=0_usize;
let a=b"a\0".as_ptr();let b=b"b\0".as_ptr();let c=b"c\0".as_ptr();let d=b"d\0".as_ptr();
macro_rules! both{($v:expr,$i:expr)=>{{data[size]=$v;size+=1;eq!(r,a::find_index(&data,size,&$v),$i);eq!(r,a::rfind_index(&data,size,&$v),$i);}};}
macro_rules! backward{($v:expr,$i:expr)=>{{data[size]=$v;size+=1;eq!(r,a::rfind_index(&data,size,&$v),$i);}};}
macro_rules! forward{($v:expr,$i:expr)=>{{data[size]=$v;size+=1;eq!(r,a::find_index(&data,size,&$v),$i);}};}
both!(a,0);both!(b,1);both!(c,2);both!(d,3);
size-=1;backward!(a,3);size-=1;forward!(a,0);size-=1;size-=1;backward!(b,2);backward!(a,3);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:160
pub fn array_utils__BinaryAndInt4Zero()->Report{let mut r=Report::default();
let expected=[0,0,0,0];let left=[0,1,0,1];let right=[1,0,1,0];let mut out=[0_i32;4];a::binary_and(&mut out,&left,&right,4);array_eq!(r,expected,out,4);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:168
pub fn array_utils__BinaryAndInt4Mix()->Report{let mut r=Report::default();
let expected=[1,0,1,0];let left=[1,1,1,1];let right=[1,0,1,0];let mut out=[0_i32;4];a::binary_and(&mut out,&left,&right,4);array_eq!(r,expected,out,4);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:185
pub fn array_utils__BinaryOrInt4Alternate()->Report{let mut r=Report::default();
let left=[0,1,0,1];let right=[1,0,1,0];let expected=[1,1,1,1];let mut out=[0_i32;4];a::binary_or(&mut out,&left,&right,4);array_eq!(r,out,expected,4);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:192
pub fn array_utils__BinaryOrInt4Mix()->Report{let mut r=Report::default();
let left=[1,1,0,0];let right=[0,0,1,0];let expected=[1,1,1,0];let mut out=[0_i32;4];a::binary_or(&mut out,&left,&right,4);array_eq!(r,out,expected,4);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:213
pub fn array_utils__DeduplicateOrdered1()->Report{let mut r=Report::default();
let mut data=[0];let expected=[0];dedup_test(&mut r,&mut data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:220
pub fn array_utils__DeduplicateOrdered2()->Report{let mut r=Report::default();
let mut data=[1,2];let expected=[1,2];dedup_test(&mut r,&mut data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:227
pub fn array_utils__DeduplicateOrdered2Same()->Report{let mut r=Report::default();
let mut data=[1,1];let expected=[1];dedup_test(&mut r,&mut data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:234
pub fn array_utils__DeduplicateOrdered3Same()->Report{let mut r=Report::default();
let mut data=[1,1,1];let expected=[1];dedup_test(&mut r,&mut data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:241
pub fn array_utils__DeduplicateOrdered3()->Report{let mut r=Report::default();
let mut data=[3,3,2,2,1,1];let expected=[3,2,1];dedup_test(&mut r,&mut data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:257
pub fn array_utils__FindAllRanges1()->Report{let mut r=Report::default();
let data=[false];let ranges=a::find_all_ranges(&data,true);eq!(r,ranges.len(),0);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:264
pub fn array_utils__FindAllRanges2()->Report{let mut r=Report::default();
let data=[true,true,true];let expected=[IndexRange::new(0,3)];ranges_test(&mut r,&data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:271
pub fn array_utils__FindAllRanges3()->Report{let mut r=Report::default();
let data=[true,false];let expected=[IndexRange::new(0,1)];ranges_test(&mut r,&data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:278
pub fn array_utils__FindAllRanges4()->Report{let mut r=Report::default();
let data=[false,true];let expected=[IndexRange::new(1,1)];ranges_test(&mut r,&data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:285
pub fn array_utils__FindAllRanges5()->Report{let mut r=Report::default();
let data=[true,false,false,true,true,false,true];let expected=[IndexRange::new(0,1),IndexRange::new(3,2),IndexRange::new(6,1)];ranges_test(&mut r,&data,&expected);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:302
pub fn array_utils__FindMaxElement1()->Report{let mut r=Report::default();
max_test(&mut r,a::VirtualInts::from_slice(&[]),None);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:307
pub fn array_utils__FindMaxElement2()->Report{let mut r=Report::default();
let data=[1];max_test(&mut r,a::VirtualInts::from_slice(&data),Some(0));
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:313
pub fn array_utils__FindMaxElement3()->Report{let mut r=Report::default();
let data=[1,2,2,1];max_test(&mut r,a::VirtualInts::from_slice(&data),Some(1));
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:319
pub fn array_utils__FindMaxElement4()->Report{let mut r=Report::default();
max_test(&mut r,a::VirtualInts::from_fn(10,|x|{let x=x as i32;-x*x+9*x}),Some(4));
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:350
pub fn array_utils__GroupIdsToIndicesEmpty()->Report{let mut r=Report::default();
groups_test(&mut r,&[],&[]);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:355
pub fn array_utils__GroupIdsToIndicesDense()->Report{let mut r=Report::default();
let ids=[5,3,5,-2,3,3,0,-2];groups_test(&mut r,&ids,&(0..ids.len()).collect::<Vec<_>>());
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:361
pub fn array_utils__GroupIdsToIndicesSparse()->Report{let mut r=Report::default();
let ids=[1000000,3,1000000,-2000000,3,7];groups_test(&mut r,&ids,&(0..ids.len()).collect::<Vec<_>>());
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:367
pub fn array_utils__GroupIdsToIndicesMask()->Report{let mut r=Report::default();
let ids=[4,1,4,2,1,2,4,3];let mask=[1_usize,2,5,6,7];groups_test(&mut r,&ids,&mask);
r
}

// Original source/blender/blenlib/tests/BLI_array_utils_test.cc:374
pub fn array_utils__GroupIdsToIndicesLarge()->Report{let mut r=Report::default();
let mut dense_ids=vec![0_i32;100000];let mut sparse_ids=vec![0_i32;100000];for i in 0..dense_ids.len(){let x=i as i32;dense_ids[i]=(x*7919)%20011;sparse_ids[i]=((x*7919)%1009)*1000003;}let mask=(0..dense_ids.len()).filter(|i|i%3!=0).collect::<Vec<_>>();let full=(0..dense_ids.len()).collect::<Vec<_>>();groups_test(&mut r,&dense_ids,&full);groups_test(&mut r,&dense_ids,&mask);groups_test(&mut r,&sparse_ids,&full);groups_test(&mut r,&sparse_ids,&mask);
r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:92
pub fn csv_parse__FindEndOfSimpleField()->Report{let mut r=Report::default();

  eq!(r, Some(csv::find_end_of_simple_field("123".as_bytes(), 0, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("123".as_bytes(), 1, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("123".as_bytes(), 2, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("123".as_bytes(), 3, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("1'3".as_bytes(), 3, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("123,".as_bytes(), 0, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("123,456".as_bytes(), 0, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("123,456,789".as_bytes(), 0, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field(" 23".as_bytes(), 0, b',')), Some(3));
  eq!(r, Some(csv::find_end_of_simple_field("".as_bytes(), 0, b',')), Some(0));
  eq!(r, Some(csv::find_end_of_simple_field("\n".as_bytes(), 0, b',')), Some(0));
  eq!(r, Some(csv::find_end_of_simple_field("12\n".as_bytes(), 0, b',')), Some(2));
  eq!(r, Some(csv::find_end_of_simple_field("0,12\n".as_bytes(), 0, b',')), Some(1));
  eq!(r, Some(csv::find_end_of_simple_field("0,12\n".as_bytes(), 2, b',')), Some(4));
  eq!(r, Some(csv::find_end_of_simple_field("\r\n".as_bytes(), 0, b',')), Some(0));
  eq!(r, Some(csv::find_end_of_simple_field("12\r\n".as_bytes(), 0, b',')), Some(2));
  eq!(r, Some(csv::find_end_of_simple_field("0,12\r\n".as_bytes(), 0, b',')), Some(1));
  eq!(r, Some(csv::find_end_of_simple_field("0,12\r\n".as_bytes(), 2, b',')), Some(4));
  eq!(r, Some(csv::find_end_of_simple_field("0,\t12\r\n".as_bytes(), 2, b',')), Some(5));
  eq!(r, Some(csv::find_end_of_simple_field("0,\t12\r\n".as_bytes(), 2, b'\t')), Some(2));

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:116
pub fn csv_parse__FindEndOfQuotedField()->Report{let mut r=Report::default();

  eq!(r, csv::find_end_of_quoted_field("".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("123".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("123\n".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("123\r\n".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("123\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(3));
  eq!(r, csv::find_end_of_quoted_field("\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(0));
  eq!(r, csv::find_end_of_quoted_field("\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(2));
  eq!(r, csv::find_end_of_quoted_field("123\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("123\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(5));
  eq!(r, csv::find_end_of_quoted_field("123\"\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("123\"\"\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(7));
  eq!(r, csv::find_end_of_quoted_field("123\"\"0\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(8));
  eq!(r, csv::find_end_of_quoted_field(",".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field(",\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(1));
  eq!(r, csv::find_end_of_quoted_field("0,1\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(3));
  eq!(r, csv::find_end_of_quoted_field("0,1\n".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("0,1\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("0,1\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(5));
  eq!(r, csv::find_end_of_quoted_field("0\n1\n\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(4));
  eq!(r, csv::find_end_of_quoted_field("\n\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(1));
  eq!(r, csv::find_end_of_quoted_field("\\\"".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("\\\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(2));
  eq!(r, csv::find_end_of_quoted_field("\\\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), None);
  eq!(r, csv::find_end_of_quoted_field("\\\"\"\"\"".as_bytes(), 0, b'"', &[b'"',b'\\']), Some(4));

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:145
pub fn csv_parse__ParseRecordFields()->Report{let mut r=Report::default();

  
  eq!(r, record_fields(""), Some(Vec::<String>::new()));
  eq!(r, record_fields("1"), Some(vec!["1".to_owned()]));
  eq!(r, record_fields("1,2"), Some(vec!["1".to_owned(), "2".to_owned()]));
  eq!(r, record_fields("1,2,3"), Some(vec!["1".to_owned(), "2".to_owned(), "3".to_owned()]));
  eq!(r, record_fields("1\n,2,3"), Some(vec!["1".to_owned()]));
  eq!(r, record_fields("1, 2\n,3"), Some(vec!["1".to_owned(), " 2".to_owned()]));
  eq!(r, record_fields("1, 2\r\n,3"), Some(vec!["1".to_owned(), " 2".to_owned()]));
  eq!(r, record_fields("\"1,2,3\""), Some(vec!["1,2,3".to_owned()]));
  eq!(r, record_fields("\"1,2,3"), None);
  eq!(r, record_fields("\"1,\n2\t\r\n,3\""), Some(vec!["1,\n2\t\r\n,3".to_owned()]));
  eq!(r, record_fields("\"1,2,3\",\"4,5\""), Some(vec!["1,2,3".to_owned(), "4,5".to_owned()]));
  eq!(r, record_fields(","), Some(vec!["".to_owned(), "".to_owned()]));
  eq!(r, record_fields(",,"), Some(vec!["".to_owned(), "".to_owned(), "".to_owned()]));
  eq!(r, record_fields(",,\n"), Some(vec!["".to_owned(), "".to_owned(), "".to_owned()]));
  eq!(r, record_fields("\r\n,,"), Some(Vec::<String>::new()));
  eq!(r, record_fields("\"a\"\"b\""), Some(vec!["a\"\"b".to_owned()]));
  eq!(r, record_fields("\"a\\\"b\""), Some(vec!["a\\\"b".to_owned()]));
  eq!(r, record_fields("\"a\"\nb"), Some(vec!["a".to_owned()]));
  eq!(r, record_fields("\"a\"  \nb"), Some(vec!["a".to_owned()]));

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:169
pub fn csv_parse__ParseCsvBasic()->Report{let mut r=Report::default();

  let mut options=csv::Options::default();
  options.chunk_size_bytes = 1;
  let result=csv_fields("a,b,c\n1,2,3,4\n4\n77,88,99\n", &options);

  yes!(r, result.success);

  eq!(r, result.column_names.len(), 3);
  eq!(r, result.column_names[0], "a".to_owned());
  eq!(r, result.column_names[1], "b".to_owned());
  eq!(r, result.column_names[2], "c".to_owned());

  eq!(r, result.records.len(), 3);
  eq!(r, result.records[0].len(), 4);
  eq!(r, result.records[1].len(), 1);
  eq!(r, result.records[2].len(), 3);

  eq!(r, result.records[0][0], "1".to_owned());
  eq!(r, result.records[0][1], "2".to_owned());
  eq!(r, result.records[0][2], "3".to_owned());
  eq!(r, result.records[0][3], "4".to_owned());

  eq!(r, result.records[1][0], "4".to_owned());

  eq!(r, result.records[2][0], "77".to_owned());
  eq!(r, result.records[2][1], "88".to_owned());
  eq!(r, result.records[2][2], "99".to_owned());

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:199
pub fn csv_parse__ParseCsvMissingEnd()->Report{let mut r=Report::default();

  let mut options=csv::Options::default();
  options.chunk_size_bytes = 1;
  let result=csv_fields("a,b,c\n1,\"2", &options);
  no!(r, result.success);

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:207
pub fn csv_parse__ParseCsvMultiLine()->Report{let mut r=Report::default();

  let mut options=csv::Options::default();
  options.chunk_size_bytes = 1;
  let result=csv_fields("a,b,c\n1,\"2\n\n\",3,4", &options);
  yes!(r, result.success);
  eq!(r, result.records.len(), 1);
  eq!(r, result.records[0].len(), 4);
  eq!(r, result.records[0][0], "1".to_owned());
  eq!(r, result.records[0][1], "2\n\n".to_owned());
  eq!(r, result.records[0][2], "3".to_owned());
  eq!(r, result.records[0][3], "4".to_owned());

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:221
pub fn csv_parse__ParseCsvEmpty()->Report{let mut r=Report::default();

  let mut options=csv::Options::default();
  options.chunk_size_bytes = 1;
  let result=csv_fields("", &options);
  yes!(r, result.success);
  eq!(r, result.column_names.len(), 0);
  eq!(r, result.records.len(), 0);

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:231
pub fn csv_parse__ParseCsvTitlesOnly()->Report{let mut r=Report::default();

  let mut options=csv::Options::default();
  options.chunk_size_bytes = 1;
  let result=csv_fields("a,b,c", &options);
  yes!(r, result.success);
  eq!(r, result.column_names.len(), 3);
  eq!(r, result.column_names[0], "a".to_owned());
  eq!(r, result.column_names[1], "b".to_owned());
  eq!(r, result.column_names[2], "c".to_owned());
  yes!(r, result.records.is_empty());

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:244
pub fn csv_parse__ParseCsvTrailingNewline()->Report{let mut r=Report::default();

  let mut options=csv::Options::default();
  options.chunk_size_bytes = 1;
  let result=csv_fields("a\n1\n2\n", &options);
  yes!(r, result.success);
  eq!(r, result.column_names.len(), 1);
  eq!(r, result.column_names[0], "a".to_owned());
  eq!(r, result.records.len(), 2);
  eq!(r, result.records[0].len(), 1);
  eq!(r, result.records[0][0], "1".to_owned());
  eq!(r, result.records[1].len(), 1);
  eq!(r, result.records[1][0], "2".to_owned());

r
}

// Original source/blender/blenlib/tests/BLI_csv_parse_test.cc:259
pub fn csv_parse__UnescapeField()->Report{let mut r=Report::default();

  // Owned/Cow byte results replace test-only arena storage.
  let mut options=csv::Options::default();
  eq!(r, String::from_utf8(csv::unescape_field("".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("a".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "a".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("abcd".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "abcd".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("ab\\cd".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "ab\\cd".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("ab\\\"cd".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "ab\"cd".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("ab\"\"cd".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "ab\"cd".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("ab\"\"\"\"cd".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "ab\"\"cd".to_owned());
  eq!(r, String::from_utf8(csv::unescape_field("ab\"\"\\\"cd".as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8"), "ab\"\"cd".to_owned());

r
}

// Original source/blender/blenlib/tests/BLI_hash_mm2a_test.cc:16
pub fn hash_mm2a__MM2ABasic()->Report{let mut r=Report::default();

  let mut mm2=Murmur2A::default();

  let data="Blender".as_bytes();

  mm2.reset(0);
  mm2.add(data);
                                           
                                                             
  eq!(r, mm2.end(), 1633988145);

r
}

// Original source/blender/blenlib/tests/BLI_hash_mm2a_test.cc:29
pub fn hash_mm2a__MM2AConcatenateStrings()->Report{let mut r=Report::default();

  let mut mm2=Murmur2A::default();
  let hash:u32;

  let data1="Blender".as_bytes();
  let data2=" is ".as_bytes();
  let data3="FaNtAsTiC".as_bytes();
  let data123="Blender is FaNtAsTiC".as_bytes();

  mm2.reset(0);
  mm2.add(data1);
  mm2.add(data2);
  mm2.add(data3);
  hash = mm2.end();
  mm2.reset(0);
  mm2.add(data123);
                                           
                                                              
  eq!(r, hash, 1545105348);
  eq!(r, mm2.end(), hash);

r
}

// Original source/blender/blenlib/tests/BLI_hash_mm2a_test.cc:52
pub fn hash_mm2a__MM2AIntegers()->Report{let mut r=Report::default();

  let mut mm2=Murmur2A::default();
  let hash:u32;

  let ints:[i32;4]=[1,2,3,4];

  mm2.reset(0);
  mm2.add_int(ints[0]);
  mm2.add_int(ints[1]);
  mm2.add_int(ints[2]);
  mm2.add_int(ints[3]);
  hash = mm2.end();
  mm2.reset(0);
  mm2.add(&ints.iter().flat_map(|v|v.to_ne_bytes()).collect::<Vec<_>>());
                                           
                                                          
  eq!(r, hash, 405493096);
  eq!(r, mm2.end(), hash);

r
}

// Original source/blender/blenlib/tests/BLI_disjoint_set_test.cc:13
pub fn disjoint_set__Test()->Report{let mut r=Report::default();

  let mut disjoint_set=DisjointSet::new(6);
  no!(r, disjoint_set.in_same_set(1, 2));
  no!(r, disjoint_set.in_same_set(5, 3));
  yes!(r, disjoint_set.in_same_set(2, 2));
  eq!(r, disjoint_set.find_root(3), 3);

  disjoint_set.join(1, 2);

  yes!(r, disjoint_set.in_same_set(1, 2));
  no!(r, disjoint_set.in_same_set(0, 1));

  disjoint_set.join(3, 4);

  no!(r, disjoint_set.in_same_set(2, 3));
  yes!(r, disjoint_set.in_same_set(3, 4));

  disjoint_set.join(1, 4);

  yes!(r, disjoint_set.in_same_set(1, 4));
  yes!(r, disjoint_set.in_same_set(1, 3));
  yes!(r, disjoint_set.in_same_set(2, 4));
  no!(r, disjoint_set.in_same_set(0, 4));

r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("array_utils.ReverseStringEmpty",array_utils__ReverseStringEmpty,1),
("array_utils.ReverseStringSingle",array_utils__ReverseStringSingle,1),
("array_utils.ReverseString4",array_utils__ReverseString4,1),
("array_utils.ReverseInt4",array_utils__ReverseInt4,4),
("array_utils.FindIndexStringEmpty",array_utils__FindIndexStringEmpty,2),
("array_utils.FindIndexStringSingle",array_utils__FindIndexStringSingle,2),
("array_utils.FindIndexStringSingleMissing",array_utils__FindIndexStringSingleMissing,2),
("array_utils.FindIndexString4",array_utils__FindIndexString4,2),
("array_utils.FindIndexInt4",array_utils__FindIndexInt4,2),
("array_utils.FindIndexInt4_DupeEnd",array_utils__FindIndexInt4_DupeEnd,2),
("array_utils.FindIndexInt4_DupeMid",array_utils__FindIndexInt4_DupeMid,2),
("array_utils.FindIndexPointer",array_utils__FindIndexPointer,12),
("array_utils.BinaryAndInt4Zero",array_utils__BinaryAndInt4Zero,4),
("array_utils.BinaryAndInt4Mix",array_utils__BinaryAndInt4Mix,4),
("array_utils.BinaryOrInt4Alternate",array_utils__BinaryOrInt4Alternate,4),
("array_utils.BinaryOrInt4Mix",array_utils__BinaryOrInt4Mix,4),
("array_utils.DeduplicateOrdered1",array_utils__DeduplicateOrdered1,4),
("array_utils.DeduplicateOrdered2",array_utils__DeduplicateOrdered2,6),
("array_utils.DeduplicateOrdered2Same",array_utils__DeduplicateOrdered2Same,4),
("array_utils.DeduplicateOrdered3Same",array_utils__DeduplicateOrdered3Same,4),
("array_utils.DeduplicateOrdered3",array_utils__DeduplicateOrdered3,8),
("array_utils.FindAllRanges1",array_utils__FindAllRanges1,1),
("array_utils.FindAllRanges2",array_utils__FindAllRanges2,2),
("array_utils.FindAllRanges3",array_utils__FindAllRanges3,2),
("array_utils.FindAllRanges4",array_utils__FindAllRanges4,2),
("array_utils.FindAllRanges5",array_utils__FindAllRanges5,4),
("array_utils.FindMaxElement1",array_utils__FindMaxElement1,1),
("array_utils.FindMaxElement2",array_utils__FindMaxElement2,2),
("array_utils.FindMaxElement3",array_utils__FindMaxElement3,2),
("array_utils.FindMaxElement4",array_utils__FindMaxElement4,2),
("array_utils.GroupIdsToIndicesEmpty",array_utils__GroupIdsToIndicesEmpty,5),
("array_utils.GroupIdsToIndicesDense",array_utils__GroupIdsToIndicesDense,5),
("array_utils.GroupIdsToIndicesSparse",array_utils__GroupIdsToIndicesSparse,5),
("array_utils.GroupIdsToIndicesMask",array_utils__GroupIdsToIndicesMask,5),
("array_utils.GroupIdsToIndicesLarge",array_utils__GroupIdsToIndicesLarge,20),
("csv_parse.FindEndOfSimpleField",csv_parse__FindEndOfSimpleField,20),
("csv_parse.FindEndOfQuotedField",csv_parse__FindEndOfQuotedField,25),
("csv_parse.ParseRecordFields",csv_parse__ParseRecordFields,19),
("csv_parse.ParseCsvBasic",csv_parse__ParseCsvBasic,17),
("csv_parse.ParseCsvMissingEnd",csv_parse__ParseCsvMissingEnd,1),
("csv_parse.ParseCsvMultiLine",csv_parse__ParseCsvMultiLine,7),
("csv_parse.ParseCsvEmpty",csv_parse__ParseCsvEmpty,3),
("csv_parse.ParseCsvTitlesOnly",csv_parse__ParseCsvTitlesOnly,6),
("csv_parse.ParseCsvTrailingNewline",csv_parse__ParseCsvTrailingNewline,8),
("csv_parse.UnescapeField",csv_parse__UnescapeField,8),
("hash_mm2a.MM2ABasic",hash_mm2a__MM2ABasic,1),
("hash_mm2a.MM2AConcatenateStrings",hash_mm2a__MM2AConcatenateStrings,2),
("hash_mm2a.MM2AIntegers",hash_mm2a__MM2AIntegers,2),
("disjoint_set.Test",disjoint_set__Test,12),
];
