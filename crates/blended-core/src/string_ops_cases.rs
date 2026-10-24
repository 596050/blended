// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked test adapters; see compatibility/string-ops-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::string_ops as s;
use crate::string_search as search;
use crate::string_refs::Bytes;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{let a:*const u8=$a;let b:*const u8=$b;$r.check(a==b,stringify!($a pointer-equals $b),line!());}};}
macro_rules! le {($r:expr,$a:expr,$b:expr)=>{{$r.check($a<=$b,stringify!($a <= $b),line!());}};}
macro_rules! lt {($r:expr,$a:expr,$b:expr)=>{{$r.check($a<$b,stringify!($a < $b),line!());}};}
macro_rules! gt {($r:expr,$a:expr,$b:expr)=>{{$r.check($a>$b,stringify!($a > $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(c_string($a)==c_string($b),stringify!($a C-string-equals $b),line!());}};}
fn c_string(a:&[u8])->&[u8]{&a[..a.iter().position(|&v|v==0).unwrap_or(a.len())]}
// Preserve EXPECT_EQ_VECTOR's length assertion and conditional element checks.
fn words_test(r:&mut Report,text:&[u8],max_length:usize,expected:&[[i32;2]],max_words:Option<usize>){
 if let Some(n)=max_words{assert!(n<=expected.len()-1,"Original CHECK_LE fixture condition");}
 let effective=max_words.unwrap_or(expected.len());
 let mut actual=vec![[-1_i32,-1_i32];effective+1];
 let n=s::find_split_words(text,max_length,b' ',&mut actual,effective);
 le!(r,n,actual.len()-1);
 actual.resize(n+1,[-1,-1]);
 eq!(r,actual.len(),expected.len());
 if actual.len()==expected.len(){for i in 0..actual.len(){eq!(r,actual[i],expected[i]);}}
}
fn natural_test(r:&mut Report,pairs:&[(&[u8],&[u8])],kind:i32){
 for &(a,b) in pairs{let result=s::casecmp_natural(a,b);match kind{0=>eq!(r,result,0),-1=>lt!(r,result,0),1=>gt!(r,result,0),_=>unreachable!()}}
}
fn escape_test(r:&mut Report,pairs:&[(&[u8],&[u8])]){
 let mut dst=[0_u8;64];
 for &(a,b) in pairs{
  lt!(r,c_string(a).len()*2+1,dst.len());
  let n=s::escape_into(&mut dst,a,64);
  streq!(r,&dst,b);eq!(r,n,c_string(&dst).len());
  let n=s::unescape_into(&mut dst,b,c_string(b).len());
  streq!(r,&dst,a);eq!(r,n,c_string(&dst).len());
 }
}
fn join_test(r:&mut Report,parts:&[&[u8]],n:usize,buffer:&mut[u8;128],sep:Option<u8>){
 let len=s::join_into(buffer,128,&parts[..n],sep);
 let alloc=s::join_owned(&parts[..n],sep);
 streq!(r,&alloc,buffer);
 for size in (1..=len+1).rev(){let mut dst=[0_u8;128];let actual=s::join_into(&mut dst,size,&parts[..n],sep);eq!(r,actual+1,size);eq!(r,s::strncmp(&dst,buffer,actual),0);}
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:32 (TEST)
pub fn string__StrCat()->Report{let mut r=Report::default();
{let mut dst=s::buffer(b"",1+1);dst[1]=0xff;s::ncat(&mut dst,b"",1);streq!(r,&dst,b"");eq!(r,dst[1],0xff_u8);}
{let mut dst=s::buffer(b"",1+1);dst[1]=0xff;s::ncat(&mut dst,b"Y",1);streq!(r,&dst,b"");eq!(r,dst[1],0xff_u8);}
{let mut dst=s::buffer(b"",2+1);dst[2]=0xff;s::ncat(&mut dst,b"Y",2);streq!(r,&dst,b"Y");eq!(r,dst[2],0xff_u8);}
{let mut dst=s::buffer(b"",2+1);dst[2]=0xff;s::ncat(&mut dst,b"YZ",2);streq!(r,&dst,b"Y");eq!(r,dst[2],0xff_u8);}
{let mut dst=s::buffer(b"X",2+1);dst[2]=0xff;s::ncat(&mut dst,b"YZ",2);streq!(r,&dst,b"X");eq!(r,dst[2],0xff_u8);}
{let mut dst=s::buffer(b"ABC",4+1);dst[4]=0xff;s::ncat(&mut dst,b"XYZ",4);streq!(r,&dst,b"ABC");eq!(r,dst[4],0xff_u8);}
{let mut dst=s::buffer(b"ABC",7+1);dst[7]=0xff;s::ncat(&mut dst,b"XYZ",7);streq!(r,&dst,b"ABCXYZ");eq!(r,dst[7],0xff_u8);}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:59 (TEST)
pub fn string__StrReplaceRange()->Report{let mut r=Report::default();
{let mut text=s::buffer(b"a ",5);s::replace_range(&mut text,2,2,b"b!");streq!(r,&text,b"a b!");}
{let mut text=s::buffer(b"a ",4);s::replace_range(&mut text,2,2,b"b!");streq!(r,&text,b"a b");}
{let mut text=s::buffer(b"a ",5);s::replace_range(&mut text,1,2,b"b!");streq!(r,&text,b"ab!");}
{let mut text=s::buffer(b"XYZ",5);s::replace_range(&mut text,1,1,b"A");streq!(r,&text,b"XAYZ");}
{let mut text=s::buffer(b"XYZ",5);s::replace_range(&mut text,1,1,b"AB");streq!(r,&text,b"XABY");}
{let mut text=s::buffer(b"XYZ",5);s::replace_range(&mut text,1,1,b"ABC");streq!(r,&text,b"XABC");}
{let mut text=s::buffer(b"XYZA",5);s::replace_range(&mut text,4,4,b"?");streq!(r,&text,b"XYZA");}
{let mut text=s::buffer(b"XYZ",4);s::replace_range(&mut text,0,0,b"ABC");streq!(r,&text,b"ABC");}
{let mut text=s::buffer(b"XYZ",7);s::replace_range(&mut text,0,0,b"ABC");streq!(r,&text,b"ABCXYZ");}
{let mut text=s::buffer(b"XYZ",4);s::replace_range(&mut text,1,3,b"");streq!(r,&text,b"X");}
{let mut text=s::buffer(b"XYZ",4);s::replace_range(&mut text,0,2,b"");streq!(r,&text,b"Z");}
{let mut text=s::buffer(b"XYZ",4);s::replace_range(&mut text,0,3,b"");streq!(r,&text,b"");}
{let mut text=s::buffer(b"",4);s::replace_range(&mut text,0,0,b"XYZ");streq!(r,&text,b"XYZ");}
{let mut text=s::buffer(b"",4);s::replace_range(&mut text,0,0,b"XYZ?");streq!(r,&text,b"XYZ");}
{let mut text=s::buffer(b"",1);s::replace_range(&mut text,0,0,b"?");streq!(r,&text,b"");}
{let mut text=s::buffer(b"",1);s::replace_range(&mut text,0,0,b"");streq!(r,&text,b"");}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:101 (TEST)
pub fn string__StrPartition()->Report{let mut r=Report::default();

{let text=b"mat.e-r_ial\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,false);
eq!(r,part.prefix_len,3_usize);
peq!(r,text.as_ptr().wrapping_add(3),part.separator_ptr());
streq!(r,b"e-r_ial",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b".mate-rial--\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,false);
eq!(r,part.prefix_len,0_usize);
peq!(r,text.as_ptr().wrapping_add(0),part.separator_ptr());
streq!(r,b"mate-rial--",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b".__.--_\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,false);
eq!(r,part.prefix_len,0_usize);
peq!(r,text.as_ptr().wrapping_add(0),part.separator_ptr());
streq!(r,b"__.--_",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,false);
eq!(r,part.prefix_len,0_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

{let text=b"material\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,false);
eq!(r,part.prefix_len,8_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:160 (TEST)
pub fn string__StrRPartition()->Report{let mut r=Report::default();

{let text=b"mat.e-r_ial\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,7_usize);
peq!(r,text.as_ptr().wrapping_add(7),part.separator_ptr());
streq!(r,b"ial",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b".mate-rial--\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,11_usize);
peq!(r,text.as_ptr().wrapping_add(11),part.separator_ptr());
streq!(r,b"",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b".__.--_\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,6_usize);
peq!(r,text.as_ptr().wrapping_add(6),part.separator_ptr());
streq!(r,b"",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,0_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

{let text=b"material\x00";
let part=s::partition(text,None,&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,8_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:219 (TEST)
pub fn string__StrPartitionEx()->Report{let mut r=Report::default();

{let text=b"mat.e-r_ia.l\x00";
let part=s::partition(text,Some(6),&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,5_usize);
peq!(r,text.as_ptr().wrapping_add(5),part.separator_ptr());
streq!(r,b"r_ia.l",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"mate.rial\x00";
let part=s::partition(text,Some(4),&[45_u32,46,95,126,92,0],false,true);
eq!(r,part.prefix_len,4_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:250 (TEST)
pub fn string__StrPartitionUtf8()->Report{let mut r=Report::default();

{let text=b"ma\xc3\xb1te-r\xe2\x98\xafial\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,false);
eq!(r,part.prefix_len,2_usize);
peq!(r,text.as_ptr().wrapping_add(2),part.separator_ptr());
streq!(r,b"te-r\xe2\x98\xafial",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\xe2\x98\xafmate-rial-\xc3\xb1\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,false);
eq!(r,part.prefix_len,0_usize);
peq!(r,text.as_ptr().wrapping_add(0),part.separator_ptr());
streq!(r,b"mate-rial-\xc3\xb1",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\xe2\x98\xaf.\xc3\xb1_.--\xc3\xb1\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,false);
eq!(r,part.prefix_len,0_usize);
peq!(r,text.as_ptr().wrapping_add(0),part.separator_ptr());
streq!(r,b".\xc3\xb1_.--\xc3\xb1",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,false);
eq!(r,part.prefix_len,0_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

{let text=b"material\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,false);
eq!(r,part.prefix_len,8_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:309 (TEST)
pub fn string__StrRPartitionUtf8()->Report{let mut r=Report::default();

{let text=b"ma\xc3\xb1te-r\xe2\x98\xafial\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,8_usize);
peq!(r,text.as_ptr().wrapping_add(8),part.separator_ptr());
streq!(r,b"ial",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\xe2\x98\xafmate-rial-\xc3\xb1\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,13_usize);
peq!(r,text.as_ptr().wrapping_add(13),part.separator_ptr());
streq!(r,b"",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\xe2\x98\xaf.\xc3\xb1_.--\xc3\xb1\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,10_usize);
peq!(r,text.as_ptr().wrapping_add(10),part.separator_ptr());
streq!(r,b"",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,0_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

{let text=b"material\x00";
let part=s::partition(text,None,&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,8_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:368 (TEST)
pub fn string__StrPartitionExUtf8()->Report{let mut r=Report::default();

{let text=b"ma\xc3\xb1te-r\xe2\x98\xafial\x00";
let part=s::partition(text,Some(6),&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,2_usize);
peq!(r,text.as_ptr().wrapping_add(2),part.separator_ptr());
streq!(r,b"te-r\xe2\x98\xafial",part.suffix_bytes().expect("Original non-null suffix"));
}

{let text=b"mate\xe2\x98\xafrial\x00";
let part=s::partition(text,Some(4),&[45_u32,46,95,241,9775,0],true,true);
eq!(r,part.prefix_len,4_usize);
peq!(r,part.separator_ptr(),core::ptr::null());
peq!(r,part.suffix_ptr(),core::ptr::null());
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:406 (TEST)
pub fn string__StrFormatIntGrouped()->Report{let mut r=Report::default();
let mut number_str=[0_u8;15];
s::format_i32(&mut number_str, 0);
streq!(r,b"0",&number_str);
s::format_i32(&mut number_str, 1);
streq!(r,b"1",&number_str);
s::format_i32(&mut number_str, -1);
streq!(r,b"-1",&number_str);
s::format_i32(&mut number_str, 1000);
streq!(r,b"1,000",&number_str);
s::format_i32(&mut number_str, -1000);
streq!(r,b"-1,000",&number_str);
s::format_i32(&mut number_str, 999);
streq!(r,b"999",&number_str);
s::format_i32(&mut number_str, -999);
streq!(r,b"-999",&number_str);
s::format_i32(&mut number_str, 2147483647);
streq!(r,b"2,147,483,647",&number_str);
s::format_i32(&mut number_str, -2147483648);
streq!(r,b"-2,147,483,648",&number_str);
eq!(r,number_str.len(),c_string(&number_str).len()+1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:442 (TEST)
pub fn string__StrFormatUint64Grouped()->Report{let mut r=Report::default();
let mut number_str=[0_u8;27];
s::format_u64(&mut number_str, 0);
streq!(r,b"0",&number_str);
s::format_u64(&mut number_str, 1);
streq!(r,b"1",&number_str);
s::format_u64(&mut number_str, 999);
streq!(r,b"999",&number_str);
s::format_u64(&mut number_str, 1000);
streq!(r,b"1,000",&number_str);
s::format_u64(&mut number_str, 18446744073709551615_u64);
streq!(r,b"18,446,744,073,709,551,615",&number_str);
eq!(r,number_str.len(),c_string(&number_str).len()+1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:472 (TEST)
pub fn string__StrFormatByteUnits()->Report{let mut r=Report::default();
let mut size_str=[0_u8;15];
s::format_bytes(&mut size_str, 0, true);
streq!(r,b"0 B",&size_str);
s::format_bytes(&mut size_str, -0, true);
streq!(r,b"0 B",&size_str);
s::format_bytes(&mut size_str, 1, true);
streq!(r,b"1 B",&size_str);
s::format_bytes(&mut size_str, -1, true);
streq!(r,b"-1 B",&size_str);
s::format_bytes(&mut size_str, 1000, true);
streq!(r,b"1 KB",&size_str);
s::format_bytes(&mut size_str, -1000, true);
streq!(r,b"-1 KB",&size_str);
s::format_bytes(&mut size_str, 1024, true);
streq!(r,b"1 KB",&size_str);
s::format_bytes(&mut size_str, -1024, true);
streq!(r,b"-1 KB",&size_str);
s::format_bytes(&mut size_str, 9223372036854775807, true);
streq!(r,b"9223.372 PB",&size_str);
s::format_bytes(&mut size_str, -9223372036854775807, true);
streq!(r,b"-9223.372 PB",&size_str);
s::format_bytes(&mut size_str, 0, false);
streq!(r,b"0 B",&size_str);
s::format_bytes(&mut size_str, -0, false);
streq!(r,b"0 B",&size_str);
s::format_bytes(&mut size_str, 1, false);
streq!(r,b"1 B",&size_str);
s::format_bytes(&mut size_str, -1, false);
streq!(r,b"-1 B",&size_str);
s::format_bytes(&mut size_str, 1000, false);
streq!(r,b"1000 B",&size_str);
s::format_bytes(&mut size_str, -1000, false);
streq!(r,b"-1000 B",&size_str);
s::format_bytes(&mut size_str, 1024, false);
streq!(r,b"1 KiB",&size_str);
s::format_bytes(&mut size_str, -1024, false);
streq!(r,b"-1 KiB",&size_str);
s::format_bytes(&mut size_str, 9223372036854775807, false);
streq!(r,b"8192.0 PiB",&size_str);
s::format_bytes(&mut size_str, -9223372036854775807, false);
streq!(r,b"-8192.0 PiB",&size_str);
s::format_bytes(&mut size_str, -9223200000000000000, false);
streq!(r,b"-8191.8472 PiB",&size_str);
eq!(r,size_str.len(),c_string(&size_str).len()+1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:545 (TEST)
pub fn string__StrFormatDecimalUnits()->Report{let mut r=Report::default();
let mut size_str=[0_u8;7];
s::format_decimal(&mut size_str, 0);
streq!(r,b"0",&size_str);
s::format_decimal(&mut size_str, 1);
streq!(r,b"1",&size_str);
s::format_decimal(&mut size_str, 10);
streq!(r,b"10",&size_str);
s::format_decimal(&mut size_str, 15);
streq!(r,b"15",&size_str);
s::format_decimal(&mut size_str, 100);
streq!(r,b"100",&size_str);
s::format_decimal(&mut size_str, 155);
streq!(r,b"155",&size_str);
s::format_decimal(&mut size_str, 1000);
streq!(r,b"1.0K",&size_str);
s::format_decimal(&mut size_str, 1555);
streq!(r,b"1.6K",&size_str);
s::format_decimal(&mut size_str, 10000);
streq!(r,b"10.0K",&size_str);
s::format_decimal(&mut size_str, 15555);
streq!(r,b"15.6K",&size_str);
s::format_decimal(&mut size_str, 100000);
streq!(r,b"100K",&size_str);
s::format_decimal(&mut size_str, 100000);
streq!(r,b"100K",&size_str);
s::format_decimal(&mut size_str, 155555);
streq!(r,b"156K",&size_str);
s::format_decimal(&mut size_str, 1000000);
streq!(r,b"1.0M",&size_str);
s::format_decimal(&mut size_str, 1555555);
streq!(r,b"1.6M",&size_str);
s::format_decimal(&mut size_str, 10000000);
streq!(r,b"10.0M",&size_str);
s::format_decimal(&mut size_str, 15555555);
streq!(r,b"15.6M",&size_str);
s::format_decimal(&mut size_str, 100000000);
streq!(r,b"100M",&size_str);
s::format_decimal(&mut size_str, 155555555);
streq!(r,b"156M",&size_str);
s::format_decimal(&mut size_str, 1000000000);
streq!(r,b"1.0B",&size_str);
s::format_decimal(&mut size_str, i32::MAX);
streq!(r,b"2.1B",&size_str);
s::format_decimal(&mut size_str, -0);
streq!(r,b"0",&size_str);
s::format_decimal(&mut size_str, -1);
streq!(r,b"-1",&size_str);
s::format_decimal(&mut size_str, -10);
streq!(r,b"-10",&size_str);
s::format_decimal(&mut size_str, -15);
streq!(r,b"-15",&size_str);
s::format_decimal(&mut size_str, -100);
streq!(r,b"-100",&size_str);
s::format_decimal(&mut size_str, -155);
streq!(r,b"-155",&size_str);
s::format_decimal(&mut size_str, -1000);
streq!(r,b"-1.0K",&size_str);
s::format_decimal(&mut size_str, -1555);
streq!(r,b"-1.6K",&size_str);
s::format_decimal(&mut size_str, -10000);
streq!(r,b"-10.0K",&size_str);
s::format_decimal(&mut size_str, -15555);
streq!(r,b"-15.6K",&size_str);
s::format_decimal(&mut size_str, -100000);
streq!(r,b"-100K",&size_str);
s::format_decimal(&mut size_str, -155555);
streq!(r,b"-156K",&size_str);
s::format_decimal(&mut size_str, -1000000);
streq!(r,b"-1.0M",&size_str);
s::format_decimal(&mut size_str, -1555555);
streq!(r,b"-1.6M",&size_str);
s::format_decimal(&mut size_str, -10000000);
streq!(r,b"-10.0M",&size_str);
s::format_decimal(&mut size_str, -15555555);
streq!(r,b"-15.6M",&size_str);
s::format_decimal(&mut size_str, -100000000);
streq!(r,b"-100M",&size_str);
s::format_decimal(&mut size_str, -155555555);
streq!(r,b"-156M",&size_str);
s::format_decimal(&mut size_str, -1000000000);
streq!(r,b"-1.0B",&size_str);
s::format_decimal(&mut size_str, i32::MIN);
streq!(r,b"-2.1B",&size_str);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:640 (TEST)
pub fn string__StrFormatIntegerUnits()->Report{let mut r=Report::default();
let mut size_str=[0_u8;5];
s::format_integer(&mut size_str, 0);
streq!(r,b"0",&size_str);
s::format_integer(&mut size_str, 1);
streq!(r,b"1",&size_str);
s::format_integer(&mut size_str, 10);
streq!(r,b"10",&size_str);
s::format_integer(&mut size_str, 15);
streq!(r,b"15",&size_str);
s::format_integer(&mut size_str, 100);
streq!(r,b"100",&size_str);
s::format_integer(&mut size_str, 155);
streq!(r,b"155",&size_str);
s::format_integer(&mut size_str, 1000);
streq!(r,b"1K",&size_str);
s::format_integer(&mut size_str, 1555);
streq!(r,b"1K",&size_str);
s::format_integer(&mut size_str, 10000);
streq!(r,b"10K",&size_str);
s::format_integer(&mut size_str, 15555);
streq!(r,b"15K",&size_str);
s::format_integer(&mut size_str, 100000);
streq!(r,b".1M",&size_str);
s::format_integer(&mut size_str, 155555);
streq!(r,b".1M",&size_str);
s::format_integer(&mut size_str, 1000000);
streq!(r,b"1M",&size_str);
s::format_integer(&mut size_str, 1555555);
streq!(r,b"1M",&size_str);
s::format_integer(&mut size_str, 2555555);
streq!(r,b"2M",&size_str);
s::format_integer(&mut size_str, 10000000);
streq!(r,b"10M",&size_str);
s::format_integer(&mut size_str, 15555555);
streq!(r,b"15M",&size_str);
s::format_integer(&mut size_str, 100000000);
streq!(r,b".1B",&size_str);
s::format_integer(&mut size_str, 155555555);
streq!(r,b".1B",&size_str);
s::format_integer(&mut size_str, 255555555);
streq!(r,b".2B",&size_str);
s::format_integer(&mut size_str, 1000000000);
streq!(r,b"1B",&size_str);
s::format_integer(&mut size_str, i32::MAX);
streq!(r,b"2B",&size_str);
s::format_integer(&mut size_str, -0);
streq!(r,b"0",&size_str);
s::format_integer(&mut size_str, -1);
streq!(r,b"-1",&size_str);
s::format_integer(&mut size_str, -10);
streq!(r,b"-10",&size_str);
s::format_integer(&mut size_str, -15);
streq!(r,b"-15",&size_str);
s::format_integer(&mut size_str, -100);
streq!(r,b"-100",&size_str);
s::format_integer(&mut size_str, -155);
streq!(r,b"-155",&size_str);
s::format_integer(&mut size_str, -1000);
streq!(r,b"-1K",&size_str);
s::format_integer(&mut size_str, -1555);
streq!(r,b"-1K",&size_str);
s::format_integer(&mut size_str, -10000);
streq!(r,b"-10K",&size_str);
s::format_integer(&mut size_str, -15555);
streq!(r,b"-15K",&size_str);
s::format_integer(&mut size_str, -100000);
streq!(r,b"-.1M",&size_str);
s::format_integer(&mut size_str, -155555);
streq!(r,b"-.1M",&size_str);
s::format_integer(&mut size_str, -1000000);
streq!(r,b"-1M",&size_str);
s::format_integer(&mut size_str, -1555555);
streq!(r,b"-1M",&size_str);
s::format_integer(&mut size_str, -10000000);
streq!(r,b"-10M",&size_str);
s::format_integer(&mut size_str, -15555555);
streq!(r,b"-15M",&size_str);
s::format_integer(&mut size_str, -100000000);
streq!(r,b"-.1B",&size_str);
s::format_integer(&mut size_str, -155555555);
streq!(r,b"-.1B",&size_str);
s::format_integer(&mut size_str, -1000000000);
streq!(r,b"-1B",&size_str);
s::format_integer(&mut size_str, i32::MIN);
streq!(r,b"-2B",&size_str);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:742 (TEST)
pub fn string__StringNLen()->Report{let mut r=Report::default();
eq!(r,0, s::nlen(b"", 0));
eq!(r,0, s::nlen(b"", 1));
eq!(r,0, s::nlen(b"", 100));
eq!(r,0, s::nlen(b"x", 0));
eq!(r,1, s::nlen(b"x", 1));
eq!(r,1, s::nlen(b"x", 100));
eq!(r,2, s::nlen(b"\xc3\xbc", 100));
eq!(r,0, s::nlen(b"this is a longer string", 0));
eq!(r,1, s::nlen(b"this is a longer string", 1));
eq!(r,5, s::nlen(b"this is a longer string", 5));
eq!(r,47, s::nlen(b"This string writes about an agent without name.", 100));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:811 (TEST)
pub fn string__StrJoin_Truncate()->Report{let mut r=Report::default();
let mut buffer=[0_u8;128];
{let parts:&[&[u8]]=&[b"a",b"b",b"c",b"d",b"e",b"f"];
join_test(&mut r,parts,6,&mut buffer,None);
streq!(r,&buffer,b"abcdef");
join_test(&mut r,parts,6,&mut buffer,Some(b'|'));
streq!(r,&buffer,b"a|b|c|d|e|f");
}
{let parts:&[&[u8]]=&[b"aa",b"bb",b"cc",b"dd",b"ee",b"ff"];
join_test(&mut r,parts,6,&mut buffer,None);
streq!(r,&buffer,b"aabbccddeeff");
join_test(&mut r,parts,6,&mut buffer,Some(b'|'));
streq!(r,&buffer,b"aa|bb|cc|dd|ee|ff");
}
{let parts:&[&[u8]]=&[b"",b"",b"",b"",b"",b""];
join_test(&mut r,parts,6,&mut buffer,None);
streq!(r,&buffer,b"");
join_test(&mut r,parts,6,&mut buffer,Some(b'|'));
streq!(r,&buffer,b"|||||");
}
{let parts:&[&[u8]]=&[b"test"];
join_test(&mut r,parts,1,&mut buffer,None);
streq!(r,&buffer,b"test");
join_test(&mut r,parts,1,&mut buffer,Some(b'|'));
streq!(r,&buffer,b"test");
}
{let parts:&[&[u8]]=&[b""];
join_test(&mut r,parts,1,&mut buffer,None);
streq!(r,&buffer,b"");
join_test(&mut r,parts,1,&mut buffer,Some(b'|'));
streq!(r,&buffer,b"");
}
{let parts:&[&[u8]]=&[b"a"];
join_test(&mut r,parts,0,&mut buffer,None);
streq!(r,&buffer,b"");
join_test(&mut r,parts,0,&mut buffer,Some(b'|'));
streq!(r,&buffer,b"");
}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:926 (TEST_F)
pub fn StringFindSplitWords__Simple()->Report{let mut r=Report::default();
words_test(&mut r,b"t",b"t".len(),&[[0,1],[-1,-1]],None);
words_test(&mut r,b"test",b"test".len(),&[[0,4],[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:931 (TEST_F)
pub fn StringFindSplitWords__Triple()->Report{let mut r=Report::default();
words_test(&mut r,b"f t w",b"f t w".len(),&[[0,1],[2,1],[4,1],[-1,-1]],None);
words_test(&mut r,b"find three words",b"find three words".len(),&[[0,4],[5,5],[11,5],[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:936 (TEST_F)
pub fn StringFindSplitWords__Spacing()->Report{let mut r=Report::default();
words_test(&mut r,b"# ## ### ####",b"# ## ### ####".len(),&[[0,1],[2,2],[5,3],[9,4],[-1,-1]],None);
words_test(&mut r,b"#  #   #    #",b"#  #   #    #".len(),&[[0,1],[3,1],[7,1],[12,1],[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:941 (TEST_F)
pub fn StringFindSplitWords__Trailing_Left()->Report{let mut r=Report::default();
words_test(&mut r,b"   t",b"   t".len(),&[[3,1],[-1,-1]],None);
words_test(&mut r,b"   test",b"   test".len(),&[[3,4],[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:946 (TEST_F)
pub fn StringFindSplitWords__Trailing_Right()->Report{let mut r=Report::default();
words_test(&mut r,b"t   ",b"t   ".len(),&[[0,1],[-1,-1]],None);
words_test(&mut r,b"test   ",b"test   ".len(),&[[0,4],[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:951 (TEST_F)
pub fn StringFindSplitWords__Trailing_LeftRight()->Report{let mut r=Report::default();
words_test(&mut r,b"   surrounding space test   123   ",b"   surrounding space test   123   ".len(),&[[3,11],[15,5],[21,4],[28,3],[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:956 (TEST_F)
pub fn StringFindSplitWords__Blank()->Report{let mut r=Report::default();
words_test(&mut r,b"",b"".len(),&[[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:960 (TEST_F)
pub fn StringFindSplitWords__Whitespace()->Report{let mut r=Report::default();
words_test(&mut r,b" ",b" ".len(),&[[-1,-1]],None);
words_test(&mut r,b"    ",b"    ".len(),&[[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:965 (TEST_F)
pub fn StringFindSplitWords__LimitWords()->Report{let mut r=Report::default();
let words=b"too many chars";let words_len=words.len();
words_test(&mut r,words,words_len,&[[0,3],[4,4],[9,5],[-1,-1]],Some(3));
words_test(&mut r,words,words_len,&[[0,3],[4,4],[-1,-1]],Some(2));
words_test(&mut r,words,words_len,&[[0,3],[-1,-1]],Some(1));
words_test(&mut r,words,words_len,&[[-1,-1]],Some(0));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:974 (TEST_F)
pub fn StringFindSplitWords__LimitChars()->Report{let mut r=Report::default();
let words=b"too many chars";let words_len=words.len();
words_test(&mut r,words,words_len,&[[0,3],[4,4],[9,5],[-1,-1]],None);
words_test(&mut r,words,words_len - 1,&[[0,3],[4,4],[9,4],[-1,-1]],None);
words_test(&mut r,words,words_len - 5,&[[0,3],[4,4],[-1,-1]],None);
words_test(&mut r,words,1,&[[0,1],[-1,-1]],None);
words_test(&mut r,words,0,&[[-1,-1]],None);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:993 (TEST)
pub fn string__StringElemEmpty()->Report{let mut r=Report::default();
no!(r,s::element_in_delimited(b"A", b':', b""));
yes!(r,s::element_in_delimited(b"", b':', b""));
yes!(r,s::element_in_delimited(b":", b':', b""));
yes!(r,s::element_in_delimited(b"::", b':', b""));
yes!(r,s::element_in_delimited(b"A:", b':', b""));
yes!(r,s::element_in_delimited(b":A", b':', b""));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1004 (TEST)
pub fn string__StringElemSingle()->Report{let mut r=Report::default();
yes!(r,s::element_in_delimited(b"A", b':', b"A"));
no!(r,s::element_in_delimited(b"A", b':', b"B"));
yes!(r,s::element_in_delimited(b"B", b'A', b"B"));
no!(r,s::element_in_delimited(b"A", b'A', b"A"));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1013 (TEST)
pub fn string__StringElemComplex()->Report{let mut r=Report::default();
yes!(r,s::element_in_delimited(b"TEST", b':', b"TEST"));
yes!(r,s::element_in_delimited(b":TEST", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"TEST:", b':', b"TEST"));
yes!(r,s::element_in_delimited(b":TEST:", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"::TEST", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"TEST::", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"::TEST::", b':', b"TEST"));
no!(r,s::element_in_delimited(b":TEST ", b':', b"TEST"));
no!(r,s::element_in_delimited(b" TEST:", b':', b"TEST"));
no!(r,s::element_in_delimited(b": TEST :", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"A:B:TEST", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"TEST:A:B", b':', b"TEST"));
yes!(r,s::element_in_delimited(b"A:TEST:B", b':', b"TEST"));
yes!(r,s::element_in_delimited(b":A:TEST:B:", b':', b"TEST"));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1042 (TEST)
pub fn string__StringStrncasestr()->Report{let mut r=Report::default();
let text=b"search here\0";
{let res=s::ncasestr(text,b"",0);peq!(r,res,text.as_ptr().wrapping_add(0));}
{let res=s::ncasestr(text,b" ",1);peq!(r,res,text.as_ptr().wrapping_add(6));}
{let res=s::ncasestr(text,b"her",3);peq!(r,res,text.as_ptr().wrapping_add(7));}
{let res=s::ncasestr(text,b"ARCh",4);peq!(r,res,text.as_ptr().wrapping_add(2));}
{let res=s::ncasestr(text,b"earcq",4);peq!(r,res,text.as_ptr().wrapping_add(1));}
{let res=s::ncasestr(text,b"not there",9);peq!(r,res,core::ptr::null());}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1073 (TEST)
pub fn string__StringMaxPossibleWordCount()->Report{let mut r=Report::default();
eq!(r,s::max_possible_words(0), 1);
eq!(r,s::max_possible_words(1), 1);
eq!(r,s::max_possible_words(2), 2);
eq!(r,s::max_possible_words(3), 2);
eq!(r,s::max_possible_words(10), 6);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1089 (TEST)
pub fn string__StrIsDecimal()->Report{let mut r=Report::default();
no!(r,s::is_decimal(b""));
no!(r,s::is_decimal(b"je moeder"));
no!(r,s::is_decimal(b"je m\xc3\xb8der"));
no!(r,s::is_decimal(b"Agent 327"));
no!(r,s::is_decimal(b"Agent\x00327"));
no!(r,s::is_decimal(b"\x00327"));
no!(r,s::is_decimal(b"0x16"));
no!(r,s::is_decimal(b"16.4"));
no!(r,s::is_decimal(b"-1"));
yes!(r,s::is_decimal(b"0"));
yes!(r,s::is_decimal(b"1"));
yes!(r,s::is_decimal(b"001"));
yes!(r,s::is_decimal(b"11342908713948713498745980171334059871345098713405981734"));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1163 (TEST_F)
pub fn StringCasecmpNatural__Empty()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b"",b"")];
let negative:&[(&[u8],&[u8])]=&[(b"",b"a"),(b"",b"A")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1179 (TEST_F)
pub fn StringCasecmpNatural__Whitespace()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b" ",b" "),(b" a",b" a"),(b" a ",b" a ")];
let negative:&[(&[u8],&[u8])]=&[(b"",b" "),(b"",b" a"),(b"",b" a "),(b" ",b" a")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1199 (TEST_F)
pub fn StringCasecmpNatural__TextOnlyLowerCase()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b"a",b"a"),(b"aa",b"aa"),(b"ab",b"ab"),(b"ba",b"ba"),(b"je m\xc3\xb8der",b"je m\xc3\xb8der")];
let negative:&[(&[u8],&[u8])]=&[(b"a",b"b"),(b"a",b"aa"),(b"a",b"ab"),(b"aa",b"b"),(b"je m\xc3\xb8da",b"je m\xc3\xb8der")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1222 (TEST_F)
pub fn StringCasecmpNatural__TextMixedCase()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b"A",b"A"),(b"AA",b"AA"),(b"AB",b"AB"),(b"Ab",b"Ab"),(b"aB",b"aB")];
let negative:&[(&[u8],&[u8])]=&[(b"A",b"a"),(b"A",b"B"),(b"A",b"b"),(b"a",b"B"),(b"AA",b"aA"),(b"AA",b"aA"),(b"Ab",b"ab"),(b"AB",b"Ab"),(b"A",b"ab"),(b"Aa",b"b"),(b"aA",b"b"),(b"AA",b"b"),(b"A",b"Ab"),(b"A",b"aB"),(b"Aa",b"B"),(b"aA",b"B"),(b"AA",b"B")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1258 (TEST_F)
pub fn StringCasecmpNatural__Period()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b".",b"."),(b". ",b". "),(b" .",b" ."),(b" . ",b" . ")];
let negative:&[(&[u8],&[u8])]=&[(b".",b". "),(b" .",b" . "),(b"foo.bar",b"foo 1.bar")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1278 (TEST_F)
pub fn StringCasecmpNatural__OnlyNumbers()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b"0",b"0"),(b"0001",b"0001"),(b"42",b"42"),(b"0042",b"0042")];
let negative:&[(&[u8],&[u8])]=&[(b"1",b"0001"),(b"01",b"001"),(b"0042",b"0043"),(b"0042",b"43")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1300 (TEST_F)
pub fn StringCasecmpNatural__TextAndNumbers()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b"00je m\xc3\xb8der1",b"00je m\xc3\xb8der1"),(b".0 ",b".0 "),(b" 1.",b" 1."),(b" .0 ",b" .0 ")];
let negative:&[(&[u8],&[u8])]=&[(b"00je m\xc3\xb8der0",b"00je m\xc3\xb8der1"),(b"05je m\xc3\xb8der0",b"06je m\xc3\xb8der1"),(b"Cube",b"Cube.001"),(b"Cube.001",b"Cube.002"),(b"CUbe.001",b"Cube.002"),(b"CUbe.002",b"Cube.002")];
let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();
natural_test(&mut r,&equal,0);
natural_test(&mut r,&negative,-1);
natural_test(&mut r,&positive,1);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1356 (TEST_F)
pub fn StringEscape__Simple()->Report{let mut r=Report::default();
let equal:&[(&[u8],&[u8])]=&[(b"",b""),(b"/",b"/"),(b"'",b"'"),(b"?",b"?")];
let escaped:&[(&[u8],&[u8])]=&[(b"\x5c",b"\x5c\x5c"),(b"A\x5c",b"A\x5c\x5c"),(b"\x5cA",b"\x5c\x5cA"),(b"A\x5cB",b"A\x5c\x5cB"),(b"?",b"?"),(b"\x22\x5c",b"\x5c\x22\x5c\x5c"),(b"\x5c\x22",b"\x5c\x5c\x5c\x22"),(b"\x22\x5c\x22",b"\x5c\x22\x5c\x5c\x5c\x22"),(b"\x22\x22\x22",b"\x5c\x22\x5c\x22\x5c\x22"),(b"\x5c\x5c\x5c",b"\x5c\x5c\x5c\x5c\x5c\x5c")];
escape_test(&mut r,equal);
escape_test(&mut r,escaped);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1391 (TEST_F)
pub fn StringEscape__Control()->Report{let mut r=Report::default();
let escaped:&[(&[u8],&[u8])]=&[(b"\x0a",b"\x5cn"),(b"\x0d",b"\x5cr"),(b"\x09",b"\x5ct"),(b"\x07",b"\x5ca"),(b"\x08",b"\x5cb"),(b"\x0c",b"\x5cf"),(b"A\x0a",b"A\x5cn"),(b"\x0aA",b"\x5cnA"),(b"\x0a\x0d\x09\x07\x08\x0c",b"\x5cn\x5cr\x5ct\x5ca\x5cb\x5cf"),(b"\x0a_\x0d_\x09_\x07_\x08_\x0c",b"\x5cn_\x5cr_\x5ct_\x5ca_\x5cb_\x5cf"),(b"\x0a\x5c\x0d\x5c\x09\x5c\x07\x5c\x08\x5c\x0c",b"\x5cn\x5c\x5c\x5cr\x5c\x5c\x5ct\x5c\x5c\x5ca\x5c\x5c\x5cb\x5c\x5c\x5cf")];
escape_test(&mut r,escaped);

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1415 (TEST)
pub fn BLI_string__bounded_strcpy()->Report{let mut r=Report::default();
{let mut text=[0_u8;8];s::copy_into(&mut text,b"Hello",8);streq!(r,&text,b"Hello");}
{let mut text=[0_u8;8];s::copy_into(&mut text,b"Hello, World!",8);streq!(r,&text,b"Hello, ");}

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1430 (TEST)
pub fn BLI_string__StartsWith()->Report{let mut r=Report::default();
yes!(r,s::starts_with(b"ab", b"a"));
no!(r,s::starts_with(b"ab", b"b"));
yes!(r,s::starts_with(b"ab", b"ab"));
yes!(r,s::starts_with(b"ab", b""));
yes!(r,s::starts_with(b"", b""));

r
}

// Original source/blender/blenlib/tests/BLI_string_test.cc:1439 (TEST)
pub fn BLI_string__EndsWith()->Report{let mut r=Report::default();
yes!(r,s::ends_with(b"ab", b"b"));
no!(r,s::ends_with(b"ab", b"a"));
yes!(r,s::ends_with(b"ab", b"ab"));
yes!(r,s::ends_with(b"ab", b""));
yes!(r,s::ends_with(b"", b""));

r
}

// Original source/blender/blenlib/tests/BLI_string_search_test.cc:16 (TEST)
pub fn string_search__damerau_levenshtein_distance()->Report{let mut r=Report::default();
eq!(r,search::damerau_levenshtein_distance(b"test",b"test"),0);
eq!(r,search::damerau_levenshtein_distance(b"hello",b"ell"),2);
eq!(r,search::damerau_levenshtein_distance(b"hello",b"hel"),2);
eq!(r,search::damerau_levenshtein_distance(b"ell",b"hello"),2);
eq!(r,search::damerau_levenshtein_distance(b"hell",b"hello"),1);
eq!(r,search::damerau_levenshtein_distance(b"hello",b"hallo"),1);
eq!(r,search::damerau_levenshtein_distance(b"test",b""),4);
eq!(r,search::damerau_levenshtein_distance(b"",b"hello"),5);
eq!(r,search::damerau_levenshtein_distance(b"Test",b"test"),1);
eq!(r,search::damerau_levenshtein_distance(b"ab",b"ba"),1);
eq!(r,search::damerau_levenshtein_distance(b"what",b"waht"),1);
eq!(r,search::damerau_levenshtein_distance(b"what",b"ahwt"),2);

r
}

// Original source/blender/blenlib/tests/BLI_string_search_test.cc:32 (TEST)
pub fn string_search__get_fuzzy_match_errors()->Report{let mut r=Report::default();
eq!(r,search::fuzzy_errors(b"a",b"b"),-1);
eq!(r,search::fuzzy_errors(b"",b"abc"),0);
eq!(r,search::fuzzy_errors(b"hello",b"hallo"),1);
eq!(r,search::fuzzy_errors(b"hap",b"hello"),-1);
eq!(r,search::fuzzy_errors(b"armature",b"\xe2\x96\xb8restore"),-1);
eq!(r,search::fuzzy_errors(b"bluir",b"blur"),search::fuzzy_errors(b"blur",b"bluir"));

r
}

// Original source/blender/blenlib/tests/BLI_string_search_test.cc:42 (TEST)
pub fn string_search__extract_normalized_words()->Report{let mut r=Report::default();
let (words,ids)=search::normalized_words(b"hello world\xe2\x96\xb8test   another test\xe2\x96\xb8 3");
eq!(r,words.len(),6_usize);
eq!(r,Bytes::from_slice(&words[0]),Bytes::from_slice(b"hello"));
eq!(r,ids[0],0_i32);
eq!(r,Bytes::from_slice(&words[1]),Bytes::from_slice(b"world"));
eq!(r,ids[1],0_i32);
eq!(r,Bytes::from_slice(&words[2]),Bytes::from_slice(b"test"));
eq!(r,ids[2],1_i32);
eq!(r,Bytes::from_slice(&words[3]),Bytes::from_slice(b"another"));
eq!(r,ids[3],1_i32);
eq!(r,Bytes::from_slice(&words[4]),Bytes::from_slice(b"test"));
eq!(r,ids[4],1_i32);
eq!(r,Bytes::from_slice(&words[5]),Bytes::from_slice(b"3"));
eq!(r,ids[5],2_i32);

r
}

// Original source/blender/blenlib/tests/BLI_string_utils_test.cc:15 (TEST)
pub fn BLI_string_utils__BLI_string_replace()->Report{let mut r=Report::default();
{let mut text=b"foo bar baz".to_vec();s::replace_all(&mut text,b"bar",b"hello");eq!(r,Bytes::from_slice(&text),Bytes::from_slice(b"foo hello baz"));}
{let mut text=b"foo bar baz world bar".to_vec();s::replace_all(&mut text,b"bar",b"hello");eq!(r,Bytes::from_slice(&text),Bytes::from_slice(b"foo hello baz world hello"));}

r
}

// Original source/blender/blenlib/tests/BLI_string_utils_test.cc:30 (TEST)
pub fn BLI_string_utils__BLI_uniquename_cb()->Report{let mut r=Report::default();
let names:&[&[u8]]=&[b"Foo",b"Bar",b"Bar.003",b"Baz.001",b"Big.999"];
let exists=|v:&[u8]|names.contains(&v);
{let mut name=s::buffer(b"",64);s::unique_name_into(&exists,b"Default Name",b'.',&mut name);streq!(r,&name,b"Default Name");}
{let mut name=s::buffer(b"Baz",64);s::unique_name_into(&exists,b"Default Name",b'.',&mut name);streq!(r,&name,b"Baz");}
{let mut name=s::buffer(b"Foo",64);s::unique_name_into(&exists,b"Default Name",b'.',&mut name);streq!(r,&name,b"Foo.001");}
{let mut name=s::buffer(b"Baz.001",64);s::unique_name_into(&exists,b"Default Name",b'.',&mut name);streq!(r,&name,b"Baz.002");}
{let mut name=s::buffer(b"Bar.003",64);s::unique_name_into(&exists,b"Default Name",b'.',&mut name);streq!(r,&name,b"Bar.004");}
{let mut name=s::buffer(b"Big.999",64);s::unique_name_into(&exists,b"Default Name",b'.',&mut name);streq!(r,&name,b"Big.1000");}
eq!(r,Bytes::from_slice(&s::unique_name(&exists,b'.',b"")),Bytes::from_slice(b""));
eq!(r,Bytes::from_slice(&s::unique_name(&exists,b'.',b"Baz")),Bytes::from_slice(b"Baz"));
eq!(r,Bytes::from_slice(&s::unique_name(&exists,b'.',b"Foo")),Bytes::from_slice(b"Foo.001"));
eq!(r,Bytes::from_slice(&s::unique_name(&exists,b'.',b"Baz.001")),Bytes::from_slice(b"Baz.002"));
eq!(r,Bytes::from_slice(&s::unique_name(&exists,b'.',b"Bar.003")),Bytes::from_slice(b"Bar.004"));
eq!(r,Bytes::from_slice(&s::unique_name(&exists,b'.',b"Big.999")),Bytes::from_slice(b"Big.1000"));

r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("string.StrCat",string__StrCat,14),
("string.StrReplaceRange",string__StrReplaceRange,16),
("string.StrPartition",string__StrPartition,15),
("string.StrRPartition",string__StrRPartition,15),
("string.StrPartitionEx",string__StrPartitionEx,6),
("string.StrPartitionUtf8",string__StrPartitionUtf8,15),
("string.StrRPartitionUtf8",string__StrRPartitionUtf8,15),
("string.StrPartitionExUtf8",string__StrPartitionExUtf8,6),
("string.StrFormatIntGrouped",string__StrFormatIntGrouped,10),
("string.StrFormatUint64Grouped",string__StrFormatUint64Grouped,6),
("string.StrFormatByteUnits",string__StrFormatByteUnits,22),
("string.StrFormatDecimalUnits",string__StrFormatDecimalUnits,41),
("string.StrFormatIntegerUnits",string__StrFormatIntegerUnits,42),
("string.StringNLen",string__StringNLen,11),
("string.StrJoin_Truncate",string__StrJoin_Truncate,166),
("StringFindSplitWords.Simple",StringFindSplitWords__Simple,8),
("StringFindSplitWords.Triple",StringFindSplitWords__Triple,12),
("StringFindSplitWords.Spacing",StringFindSplitWords__Spacing,14),
("StringFindSplitWords.Trailing_Left",StringFindSplitWords__Trailing_Left,8),
("StringFindSplitWords.Trailing_Right",StringFindSplitWords__Trailing_Right,8),
("StringFindSplitWords.Trailing_LeftRight",StringFindSplitWords__Trailing_LeftRight,7),
("StringFindSplitWords.Blank",StringFindSplitWords__Blank,3),
("StringFindSplitWords.Whitespace",StringFindSplitWords__Whitespace,6),
("StringFindSplitWords.LimitWords",StringFindSplitWords__LimitWords,18),
("StringFindSplitWords.LimitChars",StringFindSplitWords__LimitChars,24),
("string.StringElemEmpty",string__StringElemEmpty,6),
("string.StringElemSingle",string__StringElemSingle,4),
("string.StringElemComplex",string__StringElemComplex,14),
("string.StringStrncasestr",string__StringStrncasestr,6),
("string.StringMaxPossibleWordCount",string__StringMaxPossibleWordCount,5),
("string.StrIsDecimal",string__StrIsDecimal,13),
("StringCasecmpNatural.Empty",StringCasecmpNatural__Empty,5),
("StringCasecmpNatural.Whitespace",StringCasecmpNatural__Whitespace,11),
("StringCasecmpNatural.TextOnlyLowerCase",StringCasecmpNatural__TextOnlyLowerCase,15),
("StringCasecmpNatural.TextMixedCase",StringCasecmpNatural__TextMixedCase,39),
("StringCasecmpNatural.Period",StringCasecmpNatural__Period,10),
("StringCasecmpNatural.OnlyNumbers",StringCasecmpNatural__OnlyNumbers,12),
("StringCasecmpNatural.TextAndNumbers",StringCasecmpNatural__TextAndNumbers,16),
("StringEscape.Simple",StringEscape__Simple,70),
("StringEscape.Control",StringEscape__Control,55),
("BLI_string.bounded_strcpy",BLI_string__bounded_strcpy,2),
("BLI_string.StartsWith",BLI_string__StartsWith,5),
("BLI_string.EndsWith",BLI_string__EndsWith,5),
("string_search.damerau_levenshtein_distance",string_search__damerau_levenshtein_distance,12),
("string_search.get_fuzzy_match_errors",string_search__get_fuzzy_match_errors,6),
("string_search.extract_normalized_words",string_search__extract_normalized_words,13),
("BLI_string_utils.BLI_string_replace",BLI_string_utils__BLI_string_replace,2),
("BLI_string_utils.BLI_uniquename_cb",BLI_string_utils__BLI_uniquename_cb,12),
];
