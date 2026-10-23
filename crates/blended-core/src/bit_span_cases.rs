// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from three complete hash-locked Blender bit test files.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::bit_spans as m;
use core::cell::Cell;
#[derive(Debug,Default)]
pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
    fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
    // SetEmpty has no EXPECT statements upstream. Completion is verified by
    // explicit start/end events, native test discovery and a negative mutation.
    pub fn passed(&self)->bool{self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let(a,b)=(&$a,&$b);$r.check(a==b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! seq_eq {($r:expr,$a:expr,$b:expr)=>{{let(a,b)=($a,$b);eq!($r,a.len() as i64,b.len() as i64);if a.len()==b.len(){for i in 0..a.len(){eq!($r,a[i],b[i]);}}}};}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:18
pub fn bit_span__DefaultConstructor()->Report {
let mut r=Report::default();

    // Preserve placement construction over deliberately poisoned storage. Do not
    // inspect the invalid representation until write() has fully constructed it.
    {
        let mut storage=core::mem::MaybeUninit::<m::BitSpan<'static>>::uninit();
        unsafe{core::ptr::write_bytes(storage.as_mut_ptr().cast::<u8>(),0xff,core::mem::size_of::<m::BitSpan<'static>>());}
        let span=storage.write(m::BitSpan::empty());
        yes!(r,span.is_empty());eq!(r,span.size(),0);
    }
    {
        let mut storage=core::mem::MaybeUninit::<m::MutableBitSpan<'static>>::uninit();
        unsafe{core::ptr::write_bytes(storage.as_mut_ptr().cast::<u8>(),0xff,core::mem::size_of::<m::MutableBitSpan<'static>>());}
        let span=storage.write(m::MutableBitSpan::empty());
        yes!(r,span.is_empty());eq!(r,span.size(),0);
    }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:36
pub fn bit_span__Iteration()->Report {
let mut r=Report::default();

  let data = Cell::new(((1 << 2) | (1 << 3)) as u64);
  let mut span = m::BitSpan::new(core::slice::from_ref(&data), m::IndexRange::from_size(30));
  eq!(r, span.size(), 30);
  let mut index: i32 = 0;
  for bit in span.iter() {
    eq!(r, bit.test(), matches!(index,2|3));
    index+=1;
  }

  {
    let expect: Vec<i32> = vec![2, 3];
    let mut result: Vec<i32> = Vec::new();
    for bit_index in m::iter_1_indices(data.get()) {
      result.push(bit_index);
    }
    seq_eq!(r,expect.as_slice(), result.as_slice());
  }
  {
    let data2 = Cell::new((0xFB_u64) as u64);
    let expect: Vec<i32> = vec![0, 1, 3, 4, 5, 6, 7];
    let mut result: Vec<i32> = Vec::new();
    for bit_index in m::iter_1_indices(data2.get()) {
      result.push(bit_index);
    }
    seq_eq!(r,expect.as_slice(), result.as_slice());
  }
  {
    let data2 = Cell::new((u64::MAX) as u64);
    let mut i: i32 = 0;
    for bit_index in m::iter_1_indices(data2.get()) {
      eq!(r, i, bit_index);
      i+=1;
    }
    eq!(r, i, 64);
  }
  {
    let data2 = Cell::new((0) as u64);
    let mut i: i32 = 0;
    for bit_index in m::iter_1_indices(data2.get()) {
      i+=1;
    }
    eq!(r, i, 0);
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:83
pub fn bit_span__MutableIteration()->Report {
let mut r=Report::default();

  let data = Cell::new((0) as u64);
  let mut span = m::MutableBitSpan::new(core::slice::from_ref(&data), m::IndexRange::from_size(40));
  eq!(r, span.size(), 40);
  let mut index: i32 = 0;
  for bit in span.iter() {
    bit.set(index % 4 == 0);
    index+=1;
  }
  eq!(r, data.get(), 0b0000000000000000000000000001000100010001000100010001000100010001);

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:97
pub fn bit_span__SubscriptOperator()->Report {
let mut r=Report::default();

  let data: [Cell<u64>;2] = [0, 0].map(Cell::new);
  let mut mutable_span = m::MutableBitSpan::new(&data, m::IndexRange::from_size(128));
  let span = mutable_span.as_read();

  eq!(r, mutable_span.data(), data.as_ptr());
  eq!(r, mutable_span.bit_range(), m::IndexRange::from_size(128));
  eq!(r, span.data(), data.as_ptr());
  eq!(r, span.bit_range(), m::IndexRange::from_size(128));

  no!(r, mutable_span.bit(5).test());
  no!(r, span.bit(5).test());
  mutable_span.bit(5).set(true);
  yes!(r, mutable_span.bit(5).test());
  yes!(r, span.bit(5).test());

  no!(r, mutable_span.bit(120).test());
  no!(r, span.bit(120).test());
  mutable_span.bit(120).set(true);
  yes!(r, mutable_span.bit(120).test());
  yes!(r, span.bit(120).test());

  eq!(r, data[0].get(), 0b0000000000000000000000000000000000000000000000000000000000100000);
  eq!(r, data[1].get(), 0b0000000100000000000000000000000000000000000000000000000000000000);

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:126
pub fn bit_span__RangeConstructor()->Report {
let mut r=Report::default();

  let data = Cell::new((0) as u64);
  let mut mutable_span = m::MutableBitSpan::new(core::slice::from_ref(&data), m::IndexRange::new(4, 3));
  let span = mutable_span.as_read();

  no!(r, mutable_span.bit(1).test());
  no!(r, span.bit(1).test());
  mutable_span.bit(0).set(true);
  mutable_span.bit(1).set(true);
  mutable_span.bit(2).set(true);
  mutable_span.bit(0).set(false);
  mutable_span.bit(2).set(false);
  yes!(r, mutable_span.bit(1).test());
  yes!(r, span.bit(1).test());

  eq!(r, data.get(), 0b0000000000000000000000000000000000000000000000000000000000100000);

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:146
pub fn bit_span__Set()->Report {
let mut r=Report::default();

  let data = Cell::new((0) as u64);
  m::MutableBitSpan::new(core::slice::from_ref(&data), m::IndexRange::from_size(64)).set_all(true);
  eq!(r, data.get(), u64::MAX);
  m::MutableBitSpan::new(core::slice::from_ref(&data), m::IndexRange::from_size(64)).set_all(false);
  eq!(r, data.get(), 0_u64);

  m::MutableBitSpan::new(core::slice::from_ref(&data), m::IndexRange::new(4, 8)).set_all(true);
  eq!(r, data.get(), 0b0000000000000000000000000000000000000000000000000000111111110000);
  m::MutableBitSpan::new(core::slice::from_ref(&data), m::IndexRange::new(8, 30)).set_all(false);

  eq!(r, data.get(), 0b0000000000000000000000000000000000000000000000000000000011110000);

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:163
pub fn bit_span__SetEmpty()->Report {
let mut r=Report::default();

  m::MutableBitSpan::empty().set_all(true);
  m::MutableBitSpan::empty().set_all(false);

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:169
pub fn bit_span__SetSliced()->Report {
let mut r=Report::default();

  let data: [Cell<u64>;10] = core::array::from_fn(|_|Cell::new(0));
  for word in &data {word.set(0);}
  let mut span = m::MutableBitSpan::new(&data, m::IndexRange::from_size(640));
  span.slice(m::IndexRange::new(5, 500)).set_all(true);

  for i in 0_i64..640 {
    eq!(r, span.bit(i).test(), i >= 5 && i < 505);
  }

  span.slice(m::IndexRange::new(10, 190)).set_all(false);

  for i in 0_i64..640 {
    eq!(r, span.bit(i).test(), (i >= 5 && i < 10) || (i >= 200 && i < 505));
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:187
pub fn bit_span__IsBounded()->Report {
let mut r=Report::default();

  let data: [Cell<u64>;10] = core::array::from_fn(|_|Cell::new(0));

  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(0)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(1)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(50)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(63)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(64)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(65)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(100)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::from_size(400)))));

  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(0, 3)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(1, 3)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(10, 20)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(63, 1)))));
  yes!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(10, 54)))));

  no!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(1, 64)))));
  no!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(10, 64)))));
  no!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(10, 200)))));
  no!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(60, 5)))));
  no!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(64, 0)))));
  no!(r, m::is_bounded_span(&(m::BitSpan::new(&data, m::IndexRange::new(70, 5)))));

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:214
pub fn bit_span__CopyFrom()->Report {
let mut r=Report::default();

  let src_data: [Cell<u64>;30] = core::array::from_fn(|_|Cell::new(0));
  let mut i: u64 = 0;
  for value in &src_data {
    value.set(i);
    i += 234589766883;
  }
  let mut src = m::BitSpan::new(&src_data, m::IndexRange::from_size((src_data.len() as i64) * 64_i64));

  let dst_data: [Cell<u64>;4] = core::array::from_fn(|_|Cell::new(0));
  for word in &dst_data {word.set(u64::MAX);}
  let mut dst = m::MutableBitSpan::new(&dst_data, m::IndexRange::from_size(100));
  dst.copy_from(src.slice(m::IndexRange::new(401, 100)));

  for i in 0..dst.size() {
    yes!(r, dst.bit(i).test() == src.bit(401 + i).test());
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:234
pub fn bit_span__InPlaceOr()->Report {
let mut r=Report::default();

  let data_1: [Cell<u64>;100] = core::array::from_fn(|_|Cell::new(0));
  let mut span_1 = m::MutableBitSpan::new(&data_1, m::IndexRange::from_size((data_1.len() as i64) * 64_i64));
  for i in 0..span_1.size() {
    span_1.bit(i).set(i % 2 == 0);
  }

  let data_2: [Cell<u64>;100] = core::array::from_fn(|_|Cell::new(0));
  let mut span_2 = m::MutableBitSpan::new(&data_2, m::IndexRange::from_size((data_2.len() as i64) * 64_i64));
  for i in 0..span_2.size() {
    span_2.bit(i).set(i % 2 != 0);
  }

  span_1.or_assign(span_2);
  for i in 0..span_1.size() {
    yes!(r, span_1.bit(i).test());
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:254
pub fn bit_span__InPlaceAnd()->Report {
let mut r=Report::default();

  let data_1: [Cell<u64>;100] = core::array::from_fn(|_|Cell::new(0));
  let mut span_1 = m::MutableBitSpan::new(&data_1, m::IndexRange::from_size((data_1.len() as i64) * 64_i64));
  for i in 0..span_1.size() {
    span_1.bit(i).set(i % 2 == 0);
  }

  let data_2: [Cell<u64>;100] = core::array::from_fn(|_|Cell::new(0));
  let mut span_2 = m::MutableBitSpan::new(&data_2, m::IndexRange::from_size((data_2.len() as i64) * 64_i64));
  for i in 0..span_2.size() {
    span_2.bit(i).set(i % 2 != 0);
  }

  span_1.and_assign(span_2);
  for i in 0..span_1.size() {
    no!(r, span_1.bit(i).test());
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:274
pub fn bit_span__ForEach1()->Report {
let mut r=Report::default();

  let data: [Cell<u64>;2] = core::array::from_fn(|_|Cell::new(0));
  let mut span = m::MutableBitSpan::new(&data, m::IndexRange::from_size((data.len() as i64) * 64_i64));
  for i in [1, 28, 37, 86] {
    span.bit(i).set(true);
  }

  let mut indices_test: Vec<i32> = Vec::new();
  m::foreach_1_index(&(span.slice(m::IndexRange::new(4, span.size() - 4))), |i| { indices_test.push(i);  true });

  eq!(r, indices_test.as_slice(), &[24, 33, 82][..]);

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:288
pub fn bit_span__ForEach1Cancel()->Report {
let mut r=Report::default();

  let mut vec = m::BitVector::with_fill(100, false);
  vec.bit_mut(4).set(true);
  vec.bit_mut(10).set(true);
  vec.bit_mut(20).set(true);
  {
    let mut indices: Vec<i32> = Vec::new();
    m::foreach_1_index(&(vec), |i| {
      indices.push(i);
      i < 5 });
    eq!(r, indices.as_slice(), &[4, 10][..]);
  }
  {
    let mut indices: Vec<i32> = Vec::new();
    m::foreach_1_index(&(vec), |i| {
      indices.push(i);
      i < 15 });
    eq!(r, indices.as_slice(), &[4, 10, 20][..]);
  }
  {
    let mut indices: Vec<i32> = Vec::new();
    m::foreach_1_index(&(vec), |i| {
      indices.push(i);
      false });
    eq!(r, indices.as_slice(), &[4][..]);
  }
  {
    let mut indices: Vec<i32> = Vec::new();
    m::foreach_1_index(&(vec), |i| {
      indices.push(i);
      true });
    eq!(r, indices.as_slice(), &[4, 10, 20][..]);
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:328
pub fn bit_span__FindFirst1Index()->Report {
let mut r=Report::default();

  {
    let mut vec = m::BitVector::with_fill(0, false);
    eq!(r, m::find_first_1_index(&(vec)), None);
  }
  {
    let mut vec = m::BitVector::with_fill(10000, false);
    eq!(r, m::find_first_1_index(&(vec)), None);
  }
  {
    let mut vec = m::BitVector::with_fill(10000, true);
    eq!(r, m::find_first_1_index(&(vec)), Some(0));
  }
  {
    let mut vec = m::BitVector::with_fill(10, false);
    vec.bit_mut(6).set(true);
    eq!(r, m::find_first_1_index(&(vec)), Some(6));
  }
  {
    let mut vec = m::BitVector::with_fill(10000, false);
    vec.bit_mut(2500).set(true);
    eq!(r, m::find_first_1_index(&(vec)), Some(2500));
    eq!(r, m::find_first_1_index(&(m::BitSpan::from_vector(&vec).drop_front(100))), Some(2400));
  }
  {
    let mut vec_a = m::BitVector::with_fill(10000, false);
    let mut vec_b = m::BitVector::with_fill(10000, false);
    vec_a.bit_mut(2000).set(true);
    vec_a.bit_mut(2400).set(true);
    vec_a.bit_mut(2500).set(true);
    vec_b.bit_mut(2000).set(true);
    vec_b.bit_mut(2400).set(true);
    vec_b.bit_mut(2600).set(true);
                                                                         
    eq!(r, m::find_first_1_index_expr(&vec_a, &vec_b, |a,b| a ^ b), Some(2500));
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:369
pub fn bit_span__FindFirst0Index()->Report {
let mut r=Report::default();

  {
    let mut vec = m::BitVector::with_fill(0, false);
    eq!(r, m::find_first_0_index(&(vec)), None);
  }
  {
    let mut vec = m::BitVector::with_fill(10000, true);
    eq!(r, m::find_first_0_index(&(vec)), None);
  }
  {
    let mut vec = m::BitVector::with_fill(10000, false);
    eq!(r, m::find_first_0_index(&(vec)), Some(0));
  }
  {
    let mut vec = m::BitVector::with_fill(10000, true);
    vec.bit_mut(2500).reset();
    eq!(r, m::find_first_0_index(&(vec)), Some(2500));
    eq!(r, m::find_first_0_index(&(m::BitSpan::from_vector(&vec).drop_front(100))), Some(2400));
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:391
pub fn bit_span__or_bools_into_bits()->Report {
let mut r=Report::default();

  {
    let mut bools: Vec<bool> = vec![false;5];
    bools[2] = true;
    let mut bits = m::BitVector::with_fill(bools.len() as i64, false);
    bits.bit_mut(0).set(true);
    m::or_bools_into_bits(&bools, &(bits));
    yes!(r, bits.bit_mut(0).test());
    no!(r, bits.bit_mut(1).test());
    yes!(r, bits.bit_mut(2).test());
    no!(r, bits.bit_mut(3).test());
    no!(r, bits.bit_mut(4).test());
  }
  {
    let mut bools: Vec<bool> = vec![true;100];
    let mut bits = m::BitVector::with_fill(1000, false);
    m::or_bools_into_bits(&bools, &(m::MutableBitSpan::from_vector(&bits).slice(m::IndexRange::from_begin_size(100, 500))));
    no!(r, bits.bit_mut(99).test());
    yes!(r, bits.bit_mut(100).test());
    yes!(r, bits.bit_mut(101).test());
    yes!(r, bits.bit_mut(199).test());
    no!(r, bits.bit_mut(200).test());
  }

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:418
pub fn bit_span__to_index_ranges_small()->Report {
let mut r=Report::default();

  let mut bits = m::BitVector::with_fill(10, false);
  bits.bit_mut(2).set(true);
  bits.bit_mut(3).set(true);
  bits.bit_mut(4).set(true);
  bits.bit_mut(6).set(true);
  bits.bit_mut(7).set(true);

  let mut builder = m::IndexRangesBuilder::<10>::new();
  m::bits_to_index_ranges(&(bits), &mut builder);

  eq!(r, builder.size(), 2);
  eq!(r, builder.get(0), m::IndexRange::from_begin_end_inclusive(2, 4));
  eq!(r, builder.get(1), m::IndexRange::from_begin_end_inclusive(6, 7));

r
}

// source/blender/blenlib/tests/BLI_bit_span_test.cc:436
pub fn bit_span__to_index_ranges_all_ones()->Report {
let mut r=Report::default();

  let mut bits = m::BitVector::with_fill(10000, true);

  let mut builder = m::IndexRangesBuilder::<10>::new();
  m::bits_to_index_ranges(&(m::BitSpan::from_vector(&bits).take_back(8765)), &mut builder);

  eq!(r, builder.size(), 1);
  eq!(r, builder.get(0), m::IndexRange::from_size(8765));

r
}

// source/blender/blenlib/tests/BLI_bit_group_vector_test.cc:13
pub fn bit_group_vector__DefaultConstruct()->Report {
let mut r=Report::default();

  let groups = m::BitGroupVector::default();
  eq!(r, groups.size(), 0);

r
}

// source/blender/blenlib/tests/BLI_bit_group_vector_test.cc:19
pub fn bit_group_vector__Construct()->Report {
let mut r=Report::default();

  let groups = m::BitGroupVector::new(12,5);

  eq!(r, groups.size(), 12);
  eq!(r, groups.group(0).size(), 5);
  eq!(r, groups.group(4).size(), 5);

r
}

// source/blender/blenlib/tests/BLI_bit_group_vector_test.cc:28
pub fn bit_group_vector__CopyConstruct()->Report {
let mut r=Report::default();

  let groups = m::BitGroupVector::new(12,5);
  for i in 0..groups.size() {
    let span = groups.group(i);
    for j in 0..span.size() {
      span.bit(j).set(j % 2 == 0);
    }
  }

  let copy = groups.clone();

  eq!(r, groups.size(), copy.size());
  eq!(r, groups.group_size(), copy.group_size());
  for i in 0..groups.size() {
    let span = groups.group(i).as_read();
    let copy_span = copy.group(i).as_read();
    for j in 0..span.size() {
      eq!(r, span.bit(j).test(), copy_span.bit(j).test());
    }
  }

r
}

// source/blender/blenlib/tests/BLI_bit_group_vector_test.cc:51
pub fn bit_group_vector__foreachAnd()->Report {
let mut r=Report::default();

  let groups = m::BitGroupVector::new(3,4);
  groups.all_bits().set_all(true);

  let mut mask = m::BitVector::from_values(&[false, false, true, false]);
  groups.foreach_and(&mask);

  no!(r, groups.group(0).bit(0).test());
  no!(r, groups.group(0).bit(1).test());
  yes!(r, groups.group(0).bit(2).test());
  no!(r, groups.group(0).bit(3).test());

  no!(r, groups.group(1).bit(0).test());
  no!(r, groups.group(1).bit(1).test());
  yes!(r, groups.group(1).bit(2).test());
  no!(r, groups.group(1).bit(3).test());

  no!(r, groups.group(2).bit(0).test());
  no!(r, groups.group(2).bit(1).test());
  yes!(r, groups.group(2).bit(2).test());
  no!(r, groups.group(2).bit(3).test());

r
}

// source/blender/blenlib/tests/BLI_bitmap_test.cc:10
pub fn bitmap__empty_is_all_unset()->Report {
let mut r=Report::default();

  let mut bitmap = m::Bitmap::new(10);
  for i in 0..10 {
    no!(r, bitmap.get(i));
  }

r
}

// source/blender/blenlib/tests/BLI_bitmap_test.cc:18
pub fn bitmap__find_first_unset_empty()->Report {
let mut r=Report::default();

  let mut bitmap = m::Bitmap::new(10);
  eq!(r, 0, bitmap.find_first_unset(10));

r
}

// source/blender/blenlib/tests/BLI_bitmap_test.cc:24
pub fn bitmap__find_first_unset_full()->Report {
let mut r=Report::default();

  let mut bitmap = m::Bitmap::new(10);
  bitmap.flip_all(10);
  eq!(r, -1, bitmap.find_first_unset(10));

r
}

// source/blender/blenlib/tests/BLI_bitmap_test.cc:31
pub fn bitmap__find_first_unset_middle()->Report {
let mut r=Report::default();

  let mut bitmap = m::Bitmap::new(100);
  bitmap.flip_all(100);
                          
  bitmap.set(53,false);
  bitmap.set(81,false);
  bitmap.set(85,false);
  bitmap.set(86,false);

                                          
  eq!(r, 53, bitmap.find_first_unset(100));
  bitmap.set(53,true);
                                            
  eq!(r, 81, bitmap.find_first_unset(100));

r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("bit_span.DefaultConstructor",bit_span__DefaultConstructor,4),
("bit_span.Iteration",bit_span__Iteration,108),
("bit_span.MutableIteration",bit_span__MutableIteration,2),
("bit_span.SubscriptOperator",bit_span__SubscriptOperator,14),
("bit_span.RangeConstructor",bit_span__RangeConstructor,5),
("bit_span.Set",bit_span__Set,4),
("bit_span.SetEmpty",bit_span__SetEmpty,0),
("bit_span.SetSliced",bit_span__SetSliced,1280),
("bit_span.IsBounded",bit_span__IsBounded,19),
("bit_span.CopyFrom",bit_span__CopyFrom,100),
("bit_span.InPlaceOr",bit_span__InPlaceOr,6400),
("bit_span.InPlaceAnd",bit_span__InPlaceAnd,6400),
("bit_span.ForEach1",bit_span__ForEach1,1),
("bit_span.ForEach1Cancel",bit_span__ForEach1Cancel,4),
("bit_span.FindFirst1Index",bit_span__FindFirst1Index,7),
("bit_span.FindFirst0Index",bit_span__FindFirst0Index,5),
("bit_span.or_bools_into_bits",bit_span__or_bools_into_bits,10),
("bit_span.to_index_ranges_small",bit_span__to_index_ranges_small,3),
("bit_span.to_index_ranges_all_ones",bit_span__to_index_ranges_all_ones,2),
("bit_group_vector.DefaultConstruct",bit_group_vector__DefaultConstruct,1),
("bit_group_vector.Construct",bit_group_vector__Construct,3),
("bit_group_vector.CopyConstruct",bit_group_vector__CopyConstruct,62),
("bit_group_vector.foreachAnd",bit_group_vector__foreachAnd,12),
("bitmap.empty_is_all_unset",bitmap__empty_is_all_unset,10),
("bitmap.find_first_unset_empty",bitmap__find_first_unset_empty,1),
("bitmap.find_first_unset_full",bitmap__find_first_unset_full,1),
("bitmap.find_first_unset_middle",bitmap__find_first_unset_middle,2),
];
