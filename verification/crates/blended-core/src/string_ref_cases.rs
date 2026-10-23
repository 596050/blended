// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from the complete pinned BLI_string_ref_test.cc. Do not edit generated tests.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::string_refs as m;
#[derive(Debug,Default)]
pub struct Report { pub assertions:u32, pub failures:Vec<String> }
impl Report {
    fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
    pub fn passed(&self)->bool{self.assertions>0 && self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let (a,b)=(&$a,&$b);$r.check(a==b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$v:expr)=>{{$r.check($v,stringify!($v),line!());}};}
macro_rules! no {($r:expr,$v:expr)=>{{$r.check(!$v,stringify!(!$v),line!());}};}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:15
pub fn string_ref_null__DefaultConstructor()->Report {
let mut r=Report::default();

let sref = m::StringRefNull::empty();
  eq!(r, sref.size(), 0);
  eq!(r, sref[0], 0_u8);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:22
pub fn string_ref_null__CStringConstructor()->Report {
let mut r=Report::default();

  let str = b"Hello\x00";
  let sref = m::StringRefNull::from_cstr(str.as_ref());
  eq!(r, sref.size(), 5);
  eq!(r, sref.data(), str.as_ptr());

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:30
pub fn string_ref_null__CStringLengthConstructor()->Report {
let mut r=Report::default();

  let str = b"Hello\x00";
  let sref = m::StringRefNull::from_cstr_len(str, 5);
  eq!(r, sref.size(), 5);
  eq!(r, sref.data(), str.as_ptr());

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:38
pub fn string_ref_null__CompareEqual()->Report {
let mut r=Report::default();

  let ref1 = m::StringRefNull::from_cstr(b"test\x00");
  let ref2 = m::StringRefNull::from_cstr(b"test\x00");
  let ref3 = m::StringRefNull::from_cstr(b"other\x00");
  yes!(r, ref1 == ref2);
  no!(r, ref1 == ref3);
  yes!(r, ref1 != ref3);
  no!(r, ref1 != ref2);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:49
pub fn string_ref_null__CompareEqualCharPtr1()->Report {
let mut r=Report::default();

  let sref = m::StringRefNull::from_cstr(b"test\x00");
  yes!(r, sref == m::StringRef::from_bytes(b"test"));
  no!(r, sref == m::StringRef::from_bytes(b"other"));
  yes!(r, sref != m::StringRef::from_bytes(b"other"));
  no!(r, sref != m::StringRef::from_bytes(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:58
pub fn string_ref_null__CompareEqualCharPtr2()->Report {
let mut r=Report::default();

  let sref = m::StringRefNull::from_cstr(b"test\x00");
  yes!(r, m::StringRef::from_bytes(b"test") == sref);
  no!(r, m::StringRef::from_bytes(b"other") == sref);
  yes!(r, sref != m::StringRef::from_bytes(b"other"));
  no!(r, sref != m::StringRef::from_bytes(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:67
pub fn string_ref_null__CompareEqualString1()->Report {
let mut r=Report::default();

  let sref = m::StringRefNull::from_cstr(b"test\x00");
  yes!(r, sref == m::Bytes::from_slice(b"test"));
  no!(r, sref == m::Bytes::from_slice(b"other"));
  yes!(r, sref != m::Bytes::from_slice(b"other"));
  no!(r, sref != m::Bytes::from_slice(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:76
pub fn string_ref_null__CompareEqualString2()->Report {
let mut r=Report::default();

  let sref = m::StringRefNull::from_cstr(b"test\x00");
  yes!(r, m::Bytes::from_slice(b"test") == sref);
  no!(r, m::Bytes::from_slice(b"other") == sref);
  yes!(r, m::Bytes::from_slice(b"other") != sref);
  no!(r, m::Bytes::from_slice(b"test") != sref);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:85
pub fn string_ref_null__CompareEqualStringRef1()->Report {
let mut r=Report::default();

  let sref = m::StringRefNull::from_cstr(b"test\x00");
  yes!(r, sref == m::StringRef::from_cstr(b"test\x00"));
  no!(r, sref == m::StringRef::from_cstr(b"other\x00"));
  yes!(r, sref != m::StringRef::from_cstr(b"other\x00"));
  no!(r, sref != m::StringRef::from_cstr(b"test\x00"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:94
pub fn string_ref_null__CompareEqualStringRef2()->Report {
let mut r=Report::default();

  let sref = m::StringRefNull::from_cstr(b"test\x00");
  yes!(r, m::StringRef::from_cstr(b"test\x00") == sref);
  no!(r, m::StringRef::from_cstr(b"other\x00") == sref);
  yes!(r, m::StringRef::from_cstr(b"other\x00") != sref);
  no!(r, m::StringRef::from_cstr(b"test\x00") != sref);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:103
pub fn string_ref_null__Constexpr()->Report {
let mut r=Report::default();

  const SREF: m::StringRefNull<'static> = m::StringRefNull::from_cstr_len(b"World\x00", 5);
  const _: () = assert!(SREF.at(2) == b'r');
  const _: () = assert!(SREF.size() == 5);
  const COMP_LEN: usize = SREF.find_first_of(b'o') as usize;
const COMPILES: [i32;COMP_LEN] = m::array_with_first(1);
let compiles = COMPILES;
  eq!(r, compiles[0], 1);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:112
pub fn string_ref__DefaultConstructor()->Report {
let mut r=Report::default();

let sref = m::StringRef::empty();
  eq!(r, sref.size(), 0);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:118
pub fn string_ref__StartEndConstructor()->Report {
let mut r=Report::default();

  let text = b"hello world\x00";
  let sref = m::StringRef::from_bounds(text,0,5);
  eq!(r, sref.size(), 5);
  yes!(r, sref == m::StringRef::from_bytes(b"hello"));
  no!(r, sref == m::StringRef::from_bytes(b"hello "));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:127
pub fn string_ref__StartEndConstructorNullptr()->Report {
let mut r=Report::default();

  let sref = m::StringRef::empty();
  eq!(r, sref.size(), 0);
  yes!(r, sref == m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:134
pub fn string_ref__StartEndConstructorSame()->Report {
let mut r=Report::default();

  let text = b"hello world\x00";
  let sref = m::StringRef::from_bounds(text,0,0);
  eq!(r, sref.size(), 0);
  yes!(r, sref == m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:142
pub fn string_ref__CStringConstructor()->Report {
let mut r=Report::default();

  let str = b"Test\x00";
  let sref = m::StringRef::from_cstr(str.as_ref());
  eq!(r, sref.size(), 4);
  eq!(r, sref.data(), str.as_ptr());

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:150
pub fn string_ref__PointerWithLengthConstructor()->Report {
let mut r=Report::default();

  let str = b"Test\x00";
  let sref = m::StringRef::from_cstr_len(str, 2);
  eq!(r, sref.size(), 2);
  eq!(r, sref.data(), str.as_ptr());

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:158
pub fn string_ref__StdStringConstructor()->Report {
let mut r=Report::default();

  let str = m::Bytes::from_slice(b"Test");
  let sref = m::StringRef::from_cstr(str.as_ref());
  eq!(r, sref.size(), 4);
  eq!(r, sref.data(), str.data());

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:166
pub fn string_ref__SpanConstructor()->Report {
let mut r=Report::default();

  eq!(r, m::StringRef::from_cstr_len(b"hello\x00", 5), m::StringRef::from_bytes(b"hello"));
  eq!(r, m::StringRef::from_cstr_len(b"hello\x00", 2), m::StringRef::from_bytes(b"he"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:172
pub fn string_ref__SubscriptOperator()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"hello\x00");
  eq!(r, sref.size(), 5);
  eq!(r, sref[0], b'h');
  eq!(r, sref[1], b'e');
  eq!(r, sref[2], b'l');
  eq!(r, sref[3], b'l');
  eq!(r, sref[4], b'o');

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:183
pub fn string_ref__ToStdString()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let str = sref.to_owned_bytes();
  eq!(r, str.size(), 4);
  eq!(r, str, m::StringRef::from_bytes(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:191
pub fn string_ref__Print()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let mut ss: Vec<u8> = Vec::new();
  sref.write_to(&mut ss).expect("memory stream write");
  sref.write_to(&mut ss).expect("memory stream write");
  let str = m::Bytes::from_slice(&ss);
  eq!(r, str.size(), 8);
  eq!(r, str, m::StringRef::from_bytes(b"testtest"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:202
pub fn string_ref__Add()->Report {
let mut r=Report::default();

  let a = m::StringRef::from_cstr(b"qwe\x00");
  let b = m::StringRef::from_cstr(b"asd\x00");
  let result = m::concat(&(a), &(b));
  eq!(r, result, m::StringRef::from_bytes(b"qweasd"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:210
pub fn string_ref__AddCharPtr1()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let result = m::concat(&(sref), &(m::StringRef::from_bytes(b"qwe")));
  eq!(r, result, m::StringRef::from_bytes(b"testqwe"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:217
pub fn string_ref__AddCharPtr2()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let result = m::concat(&(m::StringRef::from_bytes(b"qwe")), &(sref));
  eq!(r, result, m::StringRef::from_bytes(b"qwetest"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:224
pub fn string_ref__AddString1()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let result = m::concat(&(sref), &(m::Bytes::from_slice(b"asd")));
  eq!(r, result, m::StringRef::from_bytes(b"testasd"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:231
pub fn string_ref__AddString2()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let result = m::concat(&(m::Bytes::from_slice(b"asd")), &(sref));
  eq!(r, result, m::StringRef::from_bytes(b"asdtest"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:238
pub fn string_ref__CompareEqual()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"test\x00");
  let ref3 = m::StringRef::from_cstr(b"other\x00");
  yes!(r, ref1 == ref2);
  no!(r, ref1 == ref3);
  yes!(r, ref1 != ref3);
  no!(r, ref1 != ref2);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:249
pub fn string_ref__CompareEqualCharPtr1()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  yes!(r, sref == m::StringRef::from_bytes(b"test"));
  no!(r, sref == m::StringRef::from_bytes(b"other"));
  yes!(r, sref != m::StringRef::from_bytes(b"other"));
  no!(r, sref != m::StringRef::from_bytes(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:258
pub fn string_ref__CompareEqualCharPtr2()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  yes!(r, m::StringRef::from_bytes(b"test") == sref);
  no!(r, m::StringRef::from_bytes(b"other") == sref);
  yes!(r, sref != m::StringRef::from_bytes(b"other"));
  no!(r, sref != m::StringRef::from_bytes(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:267
pub fn string_ref__CompareEqualString1()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  yes!(r, sref == m::Bytes::from_slice(b"test"));
  no!(r, sref == m::Bytes::from_slice(b"other"));
  yes!(r, sref != m::Bytes::from_slice(b"other"));
  no!(r, sref != m::Bytes::from_slice(b"test"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:276
pub fn string_ref__CompareEqualString2()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  yes!(r, m::Bytes::from_slice(b"test") == sref);
  no!(r, m::Bytes::from_slice(b"other") == sref);
  yes!(r, m::Bytes::from_slice(b"other") != sref);
  no!(r, m::Bytes::from_slice(b"test") != sref);

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:285
pub fn string_ref__Iterate()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let mut chars: Vec<u8> = Vec::new();
  for c in sref.iter() {
    chars.push(c);
  }
  eq!(r, (chars.len() as i64), 4);
  eq!(r, chars[0], b't');
  eq!(r, chars[1], b'e');
  eq!(r, chars[2], b's');
  eq!(r, chars[3], b't');

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:299
pub fn string_ref__StartsWith()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  yes!(r, sref.startswith(b""));
  yes!(r, sref.startswith(b"t"));
  yes!(r, sref.startswith(b"te"));
  yes!(r, sref.startswith(b"tes"));
  yes!(r, sref.startswith(b"test"));
  no!(r, sref.startswith(b"test "));
  no!(r, sref.startswith(b"a"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:311
pub fn string_ref__EndsWith()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  yes!(r, sref.endswith(b""));
  yes!(r, sref.endswith(b"t"));
  yes!(r, sref.endswith(b"st"));
  yes!(r, sref.endswith(b"est"));
  yes!(r, sref.endswith(b"test"));
  no!(r, sref.endswith(b" test"));
  no!(r, sref.endswith(b"a"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:323
pub fn string_ref__DropPrefixN()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let ref2 = sref.drop_prefix(2);
  let ref3 = ref2.drop_prefix(2);
  eq!(r, ref2.size(), 2);
  eq!(r, ref3.size(), 0);
  eq!(r, ref2, m::StringRef::from_bytes(b"st"));
  eq!(r, ref3, m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:334
pub fn string_ref__DropPrefixLargeN()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let ref2 = sref.drop_prefix(100);
  eq!(r, ref2.size(), 0);
  eq!(r, ref2, m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:342
pub fn string_ref__DropKnownPrefix()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let ref2 = sref.drop_known_prefix(b"tes");
  eq!(r, ref2.size(), 1);
  eq!(r, ref2, m::StringRef::from_bytes(b"t"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:350
pub fn string_ref__DropSuffix()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let ref2 = sref.drop_suffix(1);
  eq!(r, ref2.size(), 3);
  eq!(r, ref2, m::StringRef::from_bytes(b"tes"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:358
pub fn string_ref__DropSuffixLargeN()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"test\x00");
  let ref2 = sref.drop_suffix(100);
  eq!(r, ref2.size(), 0);
  eq!(r, ref2, m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:366
pub fn string_ref__TrimArbitrary()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b" \x09  Uro\xc5\xbe with spaces \x00");
  let ref4 = m::StringRef::from_cstr(b"\xc5\xbe\xc5\xbe\xc5\xbe\xc5\xbeleepy\xc5\xbe\xc5\xbe\xc5\xbe\x00");
  eq!(r, ref1.trim_bytes(b"t"), m::StringRef::from_bytes(b"es"));
  eq!(r, ref1.trim_bytes(b"te"), m::StringRef::from_bytes(b"s"));
  eq!(r, ref1.trim_bytes(b"test"), m::StringRef::from_bytes(b""));
  eq!(r, ref2.trim_bytes(b"t"), m::StringRef::from_bytes(b"   test "));
  eq!(r, ref2.trim_bytes(b""), m::StringRef::from_bytes(b"   test "));
  eq!(r, ref3.trim_bytes(b" "), m::StringRef::from_bytes(b"\x09  Uro\xc5\xbe with spaces"));                          
  eq!(r, ref4.trim_bytes(b"\xc5\xbe"), m::StringRef::from_bytes(b"leepy"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:381
pub fn string_ref__TrimWhitespace()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b" \x09  Uro\xc5\xbe with spaces \x00");
  let ref4 = m::StringRef::from_cstr(b" \x09 \x0a\x0d  \x09 \x00");
  eq!(r, ref1.trim_whitespace(), m::StringRef::from_bytes(b"test"));
  eq!(r, ref2.trim_whitespace(), m::StringRef::from_bytes(b"test"));
  eq!(r, ref3.trim_whitespace(), m::StringRef::from_bytes(b"Uro\xc5\xbe with spaces"));
  eq!(r, ref4.trim_whitespace(), m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:393
pub fn string_ref__TrimCharacter()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b"does this work?\x00");
  eq!(r, ref1.trim_bytes(&[b't']), m::StringRef::from_bytes(b"es"));
  eq!(r, ref1.trim_bytes(&[b'p']), m::StringRef::from_bytes(b"test"));
  eq!(r, ref2.trim_bytes(&[b' ']), m::StringRef::from_bytes(b"test"));
  eq!(r, ref3.trim_bytes(&[0_u8]), m::StringRef::from_bytes(b"does this work?"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:404
pub fn string_ref__TrimLeftArbitrary()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b" \x09  Uro\xc5\xbe with spaces \x00");
  let ref4 = m::StringRef::from_cstr(b"\xc5\xbe\xc5\xbe\xc5\xbe\xc5\xbeleepy\xc5\xbe\xc5\xbe\xc5\xbe\x00");
  eq!(r, ref1.trim_left_bytes(b"t"), m::StringRef::from_bytes(b"est"));
  eq!(r, ref1.trim_left_bytes(b"te"), m::StringRef::from_bytes(b"st"));
  eq!(r, ref1.trim_left_bytes(b"et"), m::StringRef::from_bytes(b"st"));
  eq!(r, ref1.trim_left_bytes(b"tes"), m::StringRef::from_bytes(b""));
  eq!(r, ref1.trim_left_bytes(b"est"), m::StringRef::from_bytes(b""));
  eq!(r, ref2.trim_left_bytes(b"t"), m::StringRef::from_bytes(b"   test "));
  eq!(r, ref2.trim_left_bytes(b""), m::StringRef::from_bytes(b"   test "));
  eq!(r, ref3.trim_left_bytes(b" "), m::StringRef::from_bytes(b"\x09  Uro\xc5\xbe with spaces "));
  eq!(r, ref4.trim_left_bytes(b"\xc5\xbe"), m::StringRef::from_bytes(b"leepy\xc5\xbe\xc5\xbe\xc5\xbe"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:421
pub fn string_ref__TrimLeftWhitespace()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b" \x09  Uro\xc5\xbe with spaces \x00");
  let ref4 = m::StringRef::from_cstr(b" \x09 \x0a\x0d  \x09 \x00");
  eq!(r, ref1.trim_left_whitespace(), m::StringRef::from_bytes(b"test"));
  eq!(r, ref2.trim_left_whitespace(), m::StringRef::from_bytes(b"test "));
  eq!(r, ref3.trim_left_whitespace(), m::StringRef::from_bytes(b"Uro\xc5\xbe with spaces "));
  eq!(r, ref4.trim_left_whitespace(), m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:433
pub fn string_ref__TrimRightArbitrary()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b" \x09  Uro\xc5\xbe with spaces \x00");
  let ref4 = m::StringRef::from_cstr(b"\xc5\xbe\xc5\xbe\xc5\xbe\xc5\xbeleepy\xc5\xbe\xc5\xbe\xc5\xbe\x00");
  eq!(r, ref1.trim_right_bytes(b"t"), m::StringRef::from_bytes(b"tes"));
  eq!(r, ref1.trim_right_bytes(b"te"), m::StringRef::from_bytes(b"tes"));
  eq!(r, ref1.trim_right_bytes(b"et"), m::StringRef::from_bytes(b"tes"));
  eq!(r, ref1.trim_right_bytes(b"test"), m::StringRef::from_bytes(b""));
  eq!(r, ref1.trim_right_bytes(b"est"), m::StringRef::from_bytes(b""));
  eq!(r, ref2.trim_right_bytes(b"t"), m::StringRef::from_bytes(b"   test "));
  eq!(r, ref2.trim_right_bytes(b""), m::StringRef::from_bytes(b"   test "));
  eq!(r, ref3.trim_right_bytes(b" "), m::StringRef::from_bytes(b" \x09  Uro\xc5\xbe with spaces"));
  eq!(r, ref4.trim_right_bytes(b"\xc5\xbe"), m::StringRef::from_bytes(b"\xc5\xbe\xc5\xbe\xc5\xbe\xc5\xbeleepy"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:450
pub fn string_ref__TrimRightWhitespace()->Report {
let mut r=Report::default();

  let ref1 = m::StringRef::from_cstr(b"test\x00");
  let ref2 = m::StringRef::from_cstr(b"   test \x00");
  let ref3 = m::StringRef::from_cstr(b" \x09  Uro\xc5\xbe with spaces \x00");
  let ref4 = m::StringRef::from_cstr(b" \x09 \x0a\x0d  \x09 \x00");
  eq!(r, ref1.trim_right_whitespace(), m::StringRef::from_bytes(b"test"));
  eq!(r, ref2.trim_right_whitespace(), m::StringRef::from_bytes(b"   test"));
  eq!(r, ref3.trim_right_whitespace(), m::StringRef::from_bytes(b" \x09  Uro\xc5\xbe with spaces"));
  eq!(r, ref4.trim_right_whitespace(), m::StringRef::from_bytes(b""));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:462
pub fn string_ref__Substr()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"hello world\x00");
  eq!(r, sref.substr(0, 5), m::StringRef::from_bytes(b"hello"));
  eq!(r, sref.substr(4, 0), m::StringRef::from_bytes(b""));
  eq!(r, sref.substr(3, 4), m::StringRef::from_bytes(b"lo w"));
  eq!(r, sref.substr(6, 5), m::StringRef::from_bytes(b"world"));
  eq!(r, sref.substr_to_end(8), m::StringRef::from_bytes(b"rld"));
  eq!(r, sref.substr(8, 100), m::StringRef::from_bytes(b"rld"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:473
pub fn string_ref__CopyUtf8Truncated()->Report {
let mut r=Report::default();

  {
    let sref = m::StringRef::from_cstr(b"hello\x00");
    let mut dst: [u8;10] = [0;10];
    dst.fill(0xFF);
    sref.copy_utf8_truncated(&mut dst);
    eq!(r, dst[5], 0_u8);
    eq!(r, dst[6], 0xFF);
    eq!(r, sref, m::StringRef::from_cstr(&dst));
  }
  {
    let sref = m::StringRef::from_cstr(b"0123456789\x00");
    let mut dst: [u8;4] = [0;4];
    dst.fill(0xFF);
    sref.copy_utf8_truncated(&mut dst);
    eq!(r, dst[0], b'0');
    eq!(r, dst[1], b'1');
    eq!(r, dst[2], b'2');
    eq!(r, dst[3], 0_u8);
  }
  {
                                                               
    let sref = m::StringRef::from_cstr(b"\xc2\xb2\xc2\xb2\x00");
    {
      let mut dst: [u8;1] = [0;1];
      sref.copy_utf8_truncated(&mut dst);
      eq!(r, dst[0], 0_u8);
    }
    {
      let mut dst: [u8;2] = [0;2];
      sref.copy_utf8_truncated(&mut dst);
      eq!(r, dst[0], 0_u8);
    }
    {
      let mut dst: [u8;3] = [0;3];
      sref.copy_utf8_truncated(&mut dst);
      eq!(r, m::StringRef::from_cstr(&dst), m::StringRef::from_bytes(b"\xc2\xb2"));
    }
    {
      let mut dst: [u8;4] = [0;4];
      sref.copy_utf8_truncated(&mut dst);
      eq!(r, m::StringRef::from_cstr(&dst), m::StringRef::from_bytes(b"\xc2\xb2"));
    }
    {
      let mut dst: [u8;5] = [0;5];
      sref.copy_utf8_truncated(&mut dst);
      eq!(r, m::StringRef::from_cstr(&dst), m::StringRef::from_bytes(b"\xc2\xb2\xc2\xb2"));
    }
  }

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:525
pub fn string_ref__CopyBytesTruncated()->Report {
let mut r=Report::default();

  {
    let sref = m::StringRef::from_cstr(b"hello\x00");
    let mut dst: [u8;10] = [0;10];
    dst.fill(0xFF);
    sref.copy_bytes_truncated(&mut dst);
    eq!(r, dst[5], 0_u8);
    eq!(r, dst[6], 0xFF);
    eq!(r, sref, m::StringRef::from_cstr(&dst));
  }
  {
    let sref = m::StringRef::from_cstr(b"0123456789\x00");
    let mut dst: [u8;4] = [0;4];
    dst.fill(0xFF);
    sref.copy_bytes_truncated(&mut dst);
    eq!(r, dst[0], b'0');
    eq!(r, dst[1], b'1');
    eq!(r, dst[2], b'2');
    eq!(r, dst[3], 0_u8);
  }
  {
                               
    let sref = m::StringRef::from_cstr(b"01234\x00");
    {
      let mut dst: [u8;1] = [0;1];
      sref.copy_bytes_truncated(&mut dst);
      eq!(r, dst[0], 0_u8);
    }
    {
      let mut dst: [u8;2] = [0;2];
      sref.copy_bytes_truncated(&mut dst);
      eq!(r, dst[0], b'0');
    }
    {
      let mut dst: [u8;3] = [0;3];
      sref.copy_bytes_truncated(&mut dst);
      eq!(r, m::StringRef::from_cstr(&dst), m::StringRef::from_bytes(b"01"));
    }
    {
      let mut dst: [u8;4] = [0;4];
      sref.copy_bytes_truncated(&mut dst);
      eq!(r, m::StringRef::from_cstr(&dst), m::StringRef::from_bytes(b"012"));
    }
    {
      let mut dst: [u8;5] = [0;5];
      sref.copy_bytes_truncated(&mut dst);
      eq!(r, m::StringRef::from_cstr(&dst), m::StringRef::from_bytes(b"0123"));
    }
  }

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:577
pub fn string_ref__FromStringView()->Report {
let mut r=Report::default();

  let view: &[u8] = b"hello";
  let sref = m::StringRef::from_bytes(view);
  eq!(r, sref, m::StringRef::from_bytes(b"hello"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:584
pub fn string_ref__ToStringView()->Report {
let mut r=Report::default();

  let sref = m::StringRef::from_cstr(b"hello\x00");
  let view = sref.as_bytes();
  eq!(r, m::StringRef::from_bytes(view), m::StringRef::from_bytes(b"hello"));

r
}

// source/blender/blenlib/tests/BLI_string_ref_test.cc:591
pub fn string_ref__Constexpr()->Report {
let mut r=Report::default();

  const SREF: m::StringRef<'static> = m::StringRef::from_cstr(b"World\x00");
  const _: () = assert!(SREF.at(2) == b'r');
  const _: () = assert!(SREF.size() == 5);
  const COMP_LEN: usize = SREF.find_first_of(b'o') as usize;
const COMPILES: [i32;COMP_LEN] = m::array_with_first(1);
let compiles = COMPILES;
  eq!(r, compiles[0], 1);

r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("string_ref_null.DefaultConstructor",string_ref_null__DefaultConstructor,2),
("string_ref_null.CStringConstructor",string_ref_null__CStringConstructor,2),
("string_ref_null.CStringLengthConstructor",string_ref_null__CStringLengthConstructor,2),
("string_ref_null.CompareEqual",string_ref_null__CompareEqual,4),
("string_ref_null.CompareEqualCharPtr1",string_ref_null__CompareEqualCharPtr1,4),
("string_ref_null.CompareEqualCharPtr2",string_ref_null__CompareEqualCharPtr2,4),
("string_ref_null.CompareEqualString1",string_ref_null__CompareEqualString1,4),
("string_ref_null.CompareEqualString2",string_ref_null__CompareEqualString2,4),
("string_ref_null.CompareEqualStringRef1",string_ref_null__CompareEqualStringRef1,4),
("string_ref_null.CompareEqualStringRef2",string_ref_null__CompareEqualStringRef2,4),
("string_ref_null.Constexpr",string_ref_null__Constexpr,1),
("string_ref.DefaultConstructor",string_ref__DefaultConstructor,1),
("string_ref.StartEndConstructor",string_ref__StartEndConstructor,3),
("string_ref.StartEndConstructorNullptr",string_ref__StartEndConstructorNullptr,2),
("string_ref.StartEndConstructorSame",string_ref__StartEndConstructorSame,2),
("string_ref.CStringConstructor",string_ref__CStringConstructor,2),
("string_ref.PointerWithLengthConstructor",string_ref__PointerWithLengthConstructor,2),
("string_ref.StdStringConstructor",string_ref__StdStringConstructor,2),
("string_ref.SpanConstructor",string_ref__SpanConstructor,2),
("string_ref.SubscriptOperator",string_ref__SubscriptOperator,6),
("string_ref.ToStdString",string_ref__ToStdString,2),
("string_ref.Print",string_ref__Print,2),
("string_ref.Add",string_ref__Add,1),
("string_ref.AddCharPtr1",string_ref__AddCharPtr1,1),
("string_ref.AddCharPtr2",string_ref__AddCharPtr2,1),
("string_ref.AddString1",string_ref__AddString1,1),
("string_ref.AddString2",string_ref__AddString2,1),
("string_ref.CompareEqual",string_ref__CompareEqual,4),
("string_ref.CompareEqualCharPtr1",string_ref__CompareEqualCharPtr1,4),
("string_ref.CompareEqualCharPtr2",string_ref__CompareEqualCharPtr2,4),
("string_ref.CompareEqualString1",string_ref__CompareEqualString1,4),
("string_ref.CompareEqualString2",string_ref__CompareEqualString2,4),
("string_ref.Iterate",string_ref__Iterate,5),
("string_ref.StartsWith",string_ref__StartsWith,7),
("string_ref.EndsWith",string_ref__EndsWith,7),
("string_ref.DropPrefixN",string_ref__DropPrefixN,4),
("string_ref.DropPrefixLargeN",string_ref__DropPrefixLargeN,2),
("string_ref.DropKnownPrefix",string_ref__DropKnownPrefix,2),
("string_ref.DropSuffix",string_ref__DropSuffix,2),
("string_ref.DropSuffixLargeN",string_ref__DropSuffixLargeN,2),
("string_ref.TrimArbitrary",string_ref__TrimArbitrary,7),
("string_ref.TrimWhitespace",string_ref__TrimWhitespace,4),
("string_ref.TrimCharacter",string_ref__TrimCharacter,4),
("string_ref.TrimLeftArbitrary",string_ref__TrimLeftArbitrary,9),
("string_ref.TrimLeftWhitespace",string_ref__TrimLeftWhitespace,4),
("string_ref.TrimRightArbitrary",string_ref__TrimRightArbitrary,9),
("string_ref.TrimRightWhitespace",string_ref__TrimRightWhitespace,4),
("string_ref.Substr",string_ref__Substr,6),
("string_ref.CopyUtf8Truncated",string_ref__CopyUtf8Truncated,12),
("string_ref.CopyBytesTruncated",string_ref__CopyBytesTruncated,12),
("string_ref.FromStringView",string_ref__FromStringView,1),
("string_ref.ToStringView",string_ref__ToStringView,1),
("string_ref.Constexpr",string_ref__Constexpr,1),
];
