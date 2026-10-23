// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from four complete, hash-locked Blender test files.
// See compatibility/collection-ports.json for API adaptations and provenance.
#![allow(non_snake_case, unused_mut, unused_parens)]
use crate::collections as m;
use core::cell::Cell;
#[derive(Debug,Default)]
pub struct Report { pub assertions: u32, pub failures: Vec<String> }
impl Report {
    fn check(&mut self, condition:bool, expression:&str, line:u32) {
        self.assertions+=1;
        if !condition {self.failures.push(format!("line {line}: {expression}"));}
    }
    pub fn passed(&self)->bool {self.assertions>0 && self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:13
pub fn bit_ref__MaskFirstNBits()->Report {
let mut r=Report::default();

  eq!(r, m::mask_first_n_bits(0), 0);
  eq!(r, m::mask_first_n_bits(1), 0b0000000000000000000000000000000000000000000000000000000000000001);
  eq!(r, m::mask_first_n_bits(5), 0b0000000000000000000000000000000000000000000000000000000000011111);
  eq!(r, m::mask_first_n_bits(63), 0b0111111111111111111111111111111111111111111111111111111111111111);
  eq!(r, m::mask_first_n_bits(64), 0b1111111111111111111111111111111111111111111111111111111111111111);

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:26
pub fn bit_ref__MaskLastNBits()->Report {
let mut r=Report::default();

  eq!(r, m::mask_last_n_bits(0), 0b0000000000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_last_n_bits(1), 0b1000000000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_last_n_bits(5), 0b1111100000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_last_n_bits(63), 0b1111111111111111111111111111111111111111111111111111111111111110);
  eq!(r, m::mask_last_n_bits(64), 0b1111111111111111111111111111111111111111111111111111111111111111);

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:40
pub fn bit_ref__MaskSingleBit()->Report {
let mut r=Report::default();

  eq!(r, m::mask_single_bit(0), 1);
  eq!(r, m::mask_single_bit(1), 0b0000000000000000000000000000000000000000000000000000000000000010);
  eq!(r, m::mask_single_bit(5), 0b0000000000000000000000000000000000000000000000000000000000100000);
  eq!(r, m::mask_single_bit(63), 0b1000000000000000000000000000000000000000000000000000000000000000);

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:51
pub fn bit_ref__IntContainingBit()->Report {
let mut r=Report::default();

  let array: [Cell<u64>;5] = core::array::from_fn(|_|Cell::new(0));
  let data = array.as_ptr();
  eq!(r, m::word_ptr(&array, 0), data);
  eq!(r, m::word_ptr(&array, 1), data);
  eq!(r, m::word_ptr(&array, 63), data);
  eq!(r, m::word_ptr(&array, 64), data.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 65), data.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 100), data.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 127), data.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 128), data.wrapping_add(2));
  let data_const = data;
  eq!(r, m::word_ptr(&array, 0), data_const);
  eq!(r, m::word_ptr(&array, 1), data_const);
  eq!(r, m::word_ptr(&array, 63), data_const);
  eq!(r, m::word_ptr(&array, 64), data_const.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 65), data_const.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 100), data_const.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 127), data_const.wrapping_add(1));
  eq!(r, m::word_ptr(&array, 128), data_const.wrapping_add(2));

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:74
pub fn bit_ref__Test()->Report {
let mut r=Report::default();

  let data = Cell::new(((1 << 3) | (1 << 7)) as u64);
  no!(r, m::BitRef::new(&data, 0).test());
  no!(r, m::BitRef::new(&data, 1).test());
  no!(r, m::BitRef::new(&data, 2).test());
  yes!(r, m::BitRef::new(&data, 3).test());
  no!(r, m::BitRef::new(&data, 4).test());
  no!(r, m::BitRef::new(&data, 5).test());
  no!(r, m::BitRef::new(&data, 6).test());
  yes!(r, m::BitRef::new(&data, 7).test());

  no!(r, m::MutableBitRef::new(&data, 0).test());
  no!(r, m::MutableBitRef::new(&data, 1).test());
  no!(r, m::MutableBitRef::new(&data, 2).test());
  yes!(r, m::MutableBitRef::new(&data, 3).test());
  no!(r, m::MutableBitRef::new(&data, 4).test());
  no!(r, m::MutableBitRef::new(&data, 5).test());
  no!(r, m::MutableBitRef::new(&data, 6).test());
  yes!(r, m::MutableBitRef::new(&data, 7).test());

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:96
pub fn bit_ref__Set()->Report {
let mut r=Report::default();

  let data = Cell::new((0) as u64);
  m::MutableBitRef::new(&data, 0).set(true);
  m::MutableBitRef::new(&data, 1).set(true);
  m::MutableBitRef::new(&data, 1).set(true);
  m::MutableBitRef::new(&data, 4).set(true);
  eq!(r, data.get(), (1 << 0) | (1 << 1) | (1 << 4));
  m::MutableBitRef::new(&data, 5).set(true);
  m::MutableBitRef::new(&data, 1).set(false);
  eq!(r, data.get(), (1 << 0) | (1 << 4) | (1 << 5));

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:109
pub fn bit_ref__Reset()->Report {
let mut r=Report::default();

  let data = Cell::new(u64::MAX);
  m::MutableBitRef::new(&data, 0).reset();
  m::MutableBitRef::new(&data, 2).reset();
  eq!(r, data.get(), u64::MAX & !(1 << 0) & !(1 << 2));

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:117
pub fn bit_ref__SetBranchless()->Report {
let mut r=Report::default();

  let data = Cell::new((0) as u64);
  m::MutableBitRef::new(&data, 0).set_branchless(true);
  eq!(r, data.get(), 1);
  m::MutableBitRef::new(&data, 0).set_branchless(false);
  eq!(r, data.get(), 0);
  m::MutableBitRef::new(&data, 3).set_branchless(false);
  m::MutableBitRef::new(&data, 4).set_branchless(true);
  eq!(r, data.get(), 16);
  m::MutableBitRef::new(&data, 3).set_branchless(true);
  m::MutableBitRef::new(&data, 4).set_branchless(true);
  eq!(r, data.get(), 24);

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:132
pub fn bit_ref__Cast()->Report {
let mut r=Report::default();

  let data = Cell::new((0) as u64);
  let mutable_ref = m::MutableBitRef::new(&data, 3);
  let read_ref = mutable_ref.as_read();
  no!(r, read_ref.test());
  mutable_ref.set(true);
  yes!(r, read_ref.test());

r
}

// source/blender/blenlib/tests/BLI_bit_ref_test.cc:142
pub fn bit_ref__MaskRangeBits()->Report {
let mut r=Report::default();

  eq!(r, m::mask_range_bits(0, 0), 0b0000000000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_range_bits(0, 1), 0b0000000000000000000000000000000000000000000000000000000000000001);
  eq!(r, m::mask_range_bits(0, 5), 0b0000000000000000000000000000000000000000000000000000000000011111);
  eq!(r, m::mask_range_bits(64, 0), 0b0000000000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_range_bits(63, 1), 0b1000000000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_range_bits(59, 5), 0b1111100000000000000000000000000000000000000000000000000000000000);
  eq!(r, m::mask_range_bits(8, 3), 0b0000000000000000000000000000000000000000000000000000011100000000);
  eq!(r, m::mask_range_bits(0, 64), 0b1111111111111111111111111111111111111111111111111111111111111111);

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:14
pub fn bit_vector__DefaultConstructor()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::default();
  eq!(r, vec.size(), 0);

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:20
pub fn bit_vector__CopyConstructorInline()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::from_values(&[false, false, true, true, false]);
  let mut vec2 = vec.clone();

  eq!(r, vec.size(), 5);
  eq!(r, vec2.size(), 5);

  vec2.bit_mut(1).set(true);
  no!(r, vec.get(1));

  no!(r, vec2.get(0));
  yes!(r, vec2.get(1));
  yes!(r, vec2.get(2));
  yes!(r, vec2.get(3));
  no!(r, vec2.get(4));

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:38
pub fn bit_vector__CopyConstructorLarge()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::with_fill(500, false);
  vec.bit_mut(1).set(true);

  let mut vec2 = vec.clone();

  eq!(r, vec.size(), 500);
  eq!(r, vec2.size(), 500);

  vec2.bit_mut(2).set(true);
  no!(r, vec.get(2));

  no!(r, vec2.get(0));
  yes!(r, vec2.get(1));
  yes!(r, vec2.get(2));

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:56
pub fn bit_vector__MoveConstructorInline()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::from_values(&[false, false, true, true, false]);
  let mut vec2 = core::mem::take(&mut vec);

  eq!(r, vec.size(), 0);
  eq!(r, vec2.size(), 5);

  no!(r, vec2.get(0));
  no!(r, vec2.get(1));
  yes!(r, vec2.get(2));
  yes!(r, vec2.get(3));
  no!(r, vec2.get(4));

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:71
pub fn bit_vector__MoveConstructorLarge()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::with_fill(500, false);
  vec.bit_mut(3).set(true);

  let mut vec2 = core::mem::take(&mut vec);

  eq!(r, vec.size(), 0);
  eq!(r, vec2.size(), 500);

  no!(r, vec2.get(0));
  no!(r, vec2.get(1));
  no!(r, vec2.get(2));
  yes!(r, vec2.get(3));
  no!(r, vec2.get(4));

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:88
pub fn bit_vector__SizeConstructor()->Report {
let mut r=Report::default();

  {
    let mut vec = m::BitVector::with_fill(0, false);
    eq!(r, vec.size(), 0);
  }
  {
    let mut vec = m::BitVector::with_fill(5, false);
    eq!(r, vec.size(), 5);
    for bit in vec.iter() {
      no!(r, bit.test());
    }
  }
  {
    let mut vec = m::BitVector::with_fill(123, false);
    eq!(r, vec.size(), 123);
    for bit in vec.iter() {
      no!(r, bit.test());
    }
  }

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:110
pub fn bit_vector__SizeFillConstructor()->Report {
let mut r=Report::default();

  {
    let mut vec = m::BitVector::with_fill(5, false);
    for i in 0_i64..5 {
      no!(r, vec.get(i));
    }
  }
  {
    let mut vec = m::BitVector::with_fill(123, true);
    for i in 0_i64..123 {
      yes!(r, vec.get(i));
    }
  }

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:126
pub fn bit_vector__IndexAccess()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::with_fill(100, false);
  vec.bit_mut(55).set(true);
  no!(r, vec.get(50));
  no!(r, vec.get(51));
  no!(r, vec.get(52));
  no!(r, vec.get(53));
  no!(r, vec.get(54));
  yes!(r, vec.get(55));
  no!(r, vec.get(56));
  no!(r, vec.get(57));
  no!(r, vec.get(58));

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:141
pub fn bit_vector__Iterator()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::with_fill(100, false);
  {
    let mut index: i64 = 0;
    for bit in vec.iter_mut() {
      bit.set(matches!(index, 0 | 4 | 7 | 10 | 11));
      index+=1;
    }
  }
  {
    let mut index: i64 = 0;
    for bit in vec.iter() {
      eq!(r, bit.test(), matches!(index, 0 | 4 | 7 | 10 | 11));
      index+=1;
    }
  }

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:160
pub fn bit_vector__Append()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::default();
  vec.append(false);
  vec.append(true);
  vec.append(true);
  vec.append(false);

  eq!(r, vec.size(), 4);
  no!(r, vec.get(0));
  yes!(r, vec.get(1));
  yes!(r, vec.get(2));
  no!(r, vec.get(3));

r
}

// source/blender/blenlib/tests/BLI_bit_vector_test.cc:175
pub fn bit_vector__AppendMany()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::default();
  for i in 0_i64..1000 {
    vec.append(i % 2);
  }
  no!(r, vec.get(0));
  yes!(r, vec.get(1));
  no!(r, vec.get(2));
  yes!(r, vec.get(3));
  no!(r, vec.get(4));
  yes!(r, vec.get(5));

r
}

// source/blender/blenlib/tests/BLI_index_ranges_builder_test.cc:11
pub fn index_ranges_builder__Empty()->Report {
let mut r=Report::default();

  let mut builder = m::IndexRangesBuilder::<10>::new();
  eq!(r, builder.size(), 0);
  yes!(r, builder.is_empty());

r
}

// source/blender/blenlib/tests/BLI_index_ranges_builder_test.cc:19
pub fn index_ranges_builder__Single()->Report {
let mut r=Report::default();

  {
    let mut builder = m::IndexRangesBuilder::<10>::new();
    builder.add(0);
    eq!(r, builder.size(), 1);
    eq!(r, builder.get(0), m::IndexRange::from_begin_size(0, 1));
  }
  {
    let mut builder = m::IndexRangesBuilder::<10>::new();
    builder.add(10);
    eq!(r, builder.size(), 1);
    eq!(r, builder.get(0), m::IndexRange::from_begin_size(10, 1));
  }

r
}

// source/blender/blenlib/tests/BLI_index_ranges_builder_test.cc:37
pub fn index_ranges_builder__Multiple()->Report {
let mut r=Report::default();

  let mut builder = m::IndexRangesBuilder::<10>::new();
  builder.add(3);
  builder.add(4);
  builder.add(5);
  builder.add(8);
  builder.add(9);
  builder.add_range(20, 100);
  builder.add_range(100, 130);

  eq!(r, builder.size(), 3);
  eq!(r, builder.get(0), m::IndexRange::from_begin_end_inclusive(3, 5));
  eq!(r, builder.get(1), m::IndexRange::from_begin_end_inclusive(8, 9));
  eq!(r, builder.get(2), m::IndexRange::from_begin_end(20, 130));

r
}

// source/blender/blenlib/tests/BLI_index_ranges_builder_test.cc:55
pub fn index_ranges_builder__Full()->Report {
let mut r=Report::default();

  {
    let mut builder = m::IndexRangesBuilder::<1>::new();
    builder.add(10);
    builder.add(11);
    builder.add(12);

    eq!(r, builder.size(), 1);
    eq!(r, builder.get(0), m::IndexRange::from_begin_end_inclusive(10, 12));
  }
  {
    let mut builder = m::IndexRangesBuilder::<3>::new();
    builder.add(100);
    builder.add(200);
    builder.add(300);
    eq!(r, builder.size(), 3);
    eq!(r, builder.get(0), m::IndexRange::from_begin_size(100, 1));
    eq!(r, builder.get(1), m::IndexRange::from_begin_size(200, 1));
    eq!(r, builder.get(2), m::IndexRange::from_begin_size(300, 1));
  }

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:12
pub fn unique_sorted_indices__FindRangeEnd()->Report {
let mut r=Report::default();

  eq!(r, m::find_size_of_next_range(&[4]), 1);
  eq!(r, m::find_size_of_next_range(&[4, 5, 6, 7]), 4);
  eq!(r, m::find_size_of_next_range(&[4, 5, 6, 8, 9]), 3);

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:19
pub fn unique_sorted_indices__NonEmptyIsRange()->Report {
let mut r=Report::default();

  yes!(r, m::non_empty_is_range(&[0, 1, 2]));
  yes!(r, m::non_empty_is_range(&[5]));
  yes!(r, m::non_empty_is_range(&[7, 8, 9, 10]));
  no!(r, m::non_empty_is_range(&[3, 5]));
  no!(r, m::non_empty_is_range(&[3, 4, 5, 6, 8, 9]));

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:28
pub fn unique_sorted_indices__NonEmptyAsRange()->Report {
let mut r=Report::default();

  eq!(r, m::non_empty_as_range(&[0, 1, 2]), m::IndexRange::new(0, 3));
  eq!(r, m::non_empty_as_range(&[5]), m::IndexRange::new(5, 1));
  eq!(r, m::non_empty_as_range(&[10, 11]), m::IndexRange::new(10, 2));

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:35
pub fn unique_sorted_indices__FindSizeOfNextRange()->Report {
let mut r=Report::default();

  eq!(r, m::find_size_of_next_range(&[0, 3, 4]), 1);
  eq!(r, m::find_size_of_next_range(&[4, 5, 6, 7]), 4);
  eq!(r, m::find_size_of_next_range(&[4]), 1);
  eq!(r, m::find_size_of_next_range(&[5, 6, 7, 10, 11, 100]), 3);

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:43
pub fn unique_sorted_indices__FindStartOfNextRange()->Report {
let mut r=Report::default();

  eq!(r, m::find_size_until_next_range(&[4], 3), 1);
  eq!(r, m::find_size_until_next_range(&[4, 5], 3), 2);
  eq!(r, m::find_size_until_next_range(&[4, 5, 6], 3), 0);
  eq!(r, m::find_size_until_next_range(&[4, 5, 6, 7], 3), 0);
  eq!(r, m::find_size_until_next_range(&[0, 1, 3, 5, 10, 11, 12, 20], 3), 4);

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:52
pub fn unique_sorted_indices__SplitToRangesAndSpans()->Report {
let mut r=Report::default();

  let data: Vec<i32> = vec![1, 2, 3, 4, 7, 9, 10, 13, 14, 15, 20, 21, 22, 23, 24];
  let mut parts = Vec::new();
  let parts_num = m::split_to_ranges_and_spans(&data, 3, &mut parts);

  eq!(r, parts_num, 4);
  eq!(r, (parts.len() as i64), 4);
  eq!(r, parts[0].as_range(), m::IndexRange::new(1, 4));
  eq!(r, parts[1].as_slice(), &[7, 9, 10][..]);
  eq!(r, parts[2].as_range(), m::IndexRange::new(13, 3));
  eq!(r, parts[3].as_range(), m::IndexRange::new(20, 5));

r
}

// source/blender/blenlib/tests/BLI_unique_sorted_indices_test.cc:66
pub fn unique_sorted_indices__FindContentRange()->Report {
let mut r=Report::default();

  {
    let data: Vec<i32> = vec![1, 2, 3, 4, 5];
    eq!(r, m::find_content_range(&data, m::IndexRange::empty()), m::IndexRange::empty());
    eq!(r, m::find_content_range(&data, m::IndexRange::from_begin_end_inclusive(2, 3)), m::IndexRange::from_begin_end_inclusive(1, 2));
    eq!(r, m::find_content_range(&data, m::IndexRange::from_size(100)), m::IndexRange::from_size(data.len() as i64));
  }
  {
    let data: Vec<i32> = vec![5, 100, 101, 1000];
    eq!(r, m::find_content_range(&data, m::IndexRange::from_begin_end_inclusive(0, 4)), m::IndexRange::empty());
    eq!(r, m::find_content_range(&data, m::IndexRange::from_begin_end_inclusive(0, 5)), m::IndexRange::from_begin_end_inclusive(0, 0));
    eq!(r, m::find_content_range(&data, m::IndexRange::from_begin_end_inclusive(5, 100)), m::IndexRange::from_begin_end_inclusive(0, 1));
    eq!(r, m::find_content_range(&data, m::IndexRange::from_begin_end_inclusive(101, 1000)), m::IndexRange::from_begin_end_inclusive(2, 3));
    eq!(r, m::find_content_range(&data, m::IndexRange::new(10000, 5)), m::IndexRange::empty());
  }

r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("bit_ref.MaskFirstNBits",bit_ref__MaskFirstNBits,5),
("bit_ref.MaskLastNBits",bit_ref__MaskLastNBits,5),
("bit_ref.MaskSingleBit",bit_ref__MaskSingleBit,4),
("bit_ref.IntContainingBit",bit_ref__IntContainingBit,16),
("bit_ref.Test",bit_ref__Test,16),
("bit_ref.Set",bit_ref__Set,2),
("bit_ref.Reset",bit_ref__Reset,1),
("bit_ref.SetBranchless",bit_ref__SetBranchless,4),
("bit_ref.Cast",bit_ref__Cast,2),
("bit_ref.MaskRangeBits",bit_ref__MaskRangeBits,8),
("bit_vector.DefaultConstructor",bit_vector__DefaultConstructor,1),
("bit_vector.CopyConstructorInline",bit_vector__CopyConstructorInline,8),
("bit_vector.CopyConstructorLarge",bit_vector__CopyConstructorLarge,6),
("bit_vector.MoveConstructorInline",bit_vector__MoveConstructorInline,7),
("bit_vector.MoveConstructorLarge",bit_vector__MoveConstructorLarge,7),
("bit_vector.SizeConstructor",bit_vector__SizeConstructor,131),
("bit_vector.SizeFillConstructor",bit_vector__SizeFillConstructor,128),
("bit_vector.IndexAccess",bit_vector__IndexAccess,9),
("bit_vector.Iterator",bit_vector__Iterator,100),
("bit_vector.Append",bit_vector__Append,5),
("bit_vector.AppendMany",bit_vector__AppendMany,6),
("index_ranges_builder.Empty",index_ranges_builder__Empty,2),
("index_ranges_builder.Single",index_ranges_builder__Single,4),
("index_ranges_builder.Multiple",index_ranges_builder__Multiple,4),
("index_ranges_builder.Full",index_ranges_builder__Full,6),
("unique_sorted_indices.FindRangeEnd",unique_sorted_indices__FindRangeEnd,3),
("unique_sorted_indices.NonEmptyIsRange",unique_sorted_indices__NonEmptyIsRange,5),
("unique_sorted_indices.NonEmptyAsRange",unique_sorted_indices__NonEmptyAsRange,3),
("unique_sorted_indices.FindSizeOfNextRange",unique_sorted_indices__FindSizeOfNextRange,4),
("unique_sorted_indices.FindStartOfNextRange",unique_sorted_indices__FindStartOfNextRange,5),
("unique_sorted_indices.SplitToRangesAndSpans",unique_sorted_indices__SplitToRangesAndSpans,6),
("unique_sorted_indices.FindContentRange",unique_sorted_indices__FindContentRange,8),
];
