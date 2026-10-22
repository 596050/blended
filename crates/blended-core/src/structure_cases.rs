// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from complete pinned test files. Values and assertion sites are retained.
// Rust slice/vector APIs replace C++ Span/Array/Vector; see structure-ports.json.
#![allow(non_snake_case, unused_mut, unused_parens)]
use crate::data_structures as m;
#[derive(Debug,Default)]
pub struct Report { pub assertions: u32, pub failures: Vec<String> }
impl Report {
    fn check(&mut self, condition: bool, expression: &str, line: u32) {
        self.assertions += 1;
        if !condition { self.failures.push(format!("line {line}: {expression}")); }
    }
    pub fn passed(&self) -> bool { self.assertions > 0 && self.failures.is_empty() }
}
macro_rules! eq { ($r:expr,$a:expr,$b:expr) => {{ $r.check($a == $b,stringify!($a == $b),line!()); }}; }
macro_rules! gt { ($r:expr,$a:expr,$b:expr) => {{ $r.check($a > $b,stringify!($a > $b),line!()); }}; }
macro_rules! yes { ($r:expr,$a:expr) => {{ $r.check($a,stringify!($a),line!()); }}; }
macro_rules! no { ($r:expr,$a:expr) => {{ $r.check(!$a,stringify!(!$a),line!()); }}; }

// source/blender/blenlib/tests/BLI_index_range_test.cc:14
pub fn index_range__DefaultConstructor() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::empty();
  eq!(r, range.size(), 0);

  let mut vector: Vec<i64> = Vec::new();
  for value in range.iter() {
    vector.push(value);
  }
  eq!(r, (vector.len() as i64), 0);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:26
pub fn index_range__FromBeginSize() -> Report {
let mut r = Report::default();

  {
    let range = m::IndexRange::from_begin_size(0, 0);
    yes!(r, range.is_empty());
  }
  {
    let range = m::IndexRange::from_begin_size(0, 10);
    eq!(r, range.size(), 10);
    eq!(r, range.first(), 0);
  }
  {
    let range = m::IndexRange::from_begin_size(4, 10);
    eq!(r, range.size(), 10);
    eq!(r, range.first(), 4);
    eq!(r, range.last(), 13);
  }

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:45
pub fn index_range__FromBeginEnd() -> Report {
let mut r = Report::default();

  {
    let range = m::IndexRange::from_begin_end(0, 0);
    yes!(r, range.is_empty());
  }
  {
    let range = m::IndexRange::from_begin_end(0, 10);
    eq!(r, range.size(), 10);
    eq!(r, range.first(), 0);
  }
  {
    let range = m::IndexRange::from_begin_end(4, 10);
    eq!(r, range.size(), 6);
    eq!(r, range.first(), 4);
    eq!(r, range.last(), 9);
  }

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:64
pub fn index_range__FromBeginEndInclusive() -> Report {
let mut r = Report::default();

  {
    let range = m::IndexRange::from_begin_end_inclusive(0, 0);
    eq!(r, range.size(), 1);
    eq!(r, range.first(), 0);
  }
  {
    let range = m::IndexRange::from_begin_end_inclusive(100, 200);
    eq!(r, range.size(), 101);
    eq!(r, range.first(), 100);
    eq!(r, range.last(), 200);
  }

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:79
pub fn index_range__FromEndSize() -> Report {
let mut r = Report::default();

  {
    let range = m::IndexRange::from_end_size(0, 0);
    yes!(r, range.is_empty());
  }
  {
    let range = m::IndexRange::from_end_size(100, 20);
    eq!(r, range.first(), 80);
    eq!(r, range.last(), 99);
  }

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:92
pub fn index_range__FromSingle() -> Report {
let mut r = Report::default();

  {
    let range = m::IndexRange::from_single(0);
    eq!(r, range.size(), 1);
    eq!(r, range.first(), 0);
  }
  {
    let range = m::IndexRange::from_single(100);
    eq!(r, range.size(), 1);
    eq!(r, range.first(), 100);
  }

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:106
pub fn index_range__SingleElementRange() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(4, 1);
  eq!(r, range.size(), 1);
  eq!(r, range.iter().next().unwrap(), 4);

  let mut vector: Vec<i64> = Vec::new();
  for value in range.iter() {
    vector.push(value);
  }

  eq!(r, (vector.len() as i64), 1);
  eq!(r, vector[0], 4);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:121
pub fn index_range__MultipleElementRange() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(6, 4);
  eq!(r, range.size(), 4);

  let mut vector: Vec<i64> = Vec::new();
  for value in range.iter() {
    vector.push(value);
  }

  eq!(r, (vector.len() as i64), 4);
  for i in 0..4_usize {
    eq!(r, vector[i], (i + 6) as i64);
  }

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:137
pub fn index_range__SubscriptOperator() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 5);
  eq!(r, range.get(0), 5);
  eq!(r, range.get(1), 6);
  eq!(r, range.get(2), 7);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:145
pub fn index_range__Before() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 5).before(3);
  eq!(r, range.get(0), 2);
  eq!(r, range.get(1), 3);
  eq!(r, range.get(2), 4);
  eq!(r, range.size(), 3);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:154
pub fn index_range__After() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 5).after(4);
  eq!(r, range.get(0), 10);
  eq!(r, range.get(1), 11);
  eq!(r, range.get(2), 12);
  eq!(r, range.get(3), 13);
  eq!(r, range.size(), 4);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:164
pub fn index_range__Contains() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 3);
  yes!(r, range.contains(5));
  yes!(r, range.contains(6));
  yes!(r, range.contains(7));
  no!(r, range.contains(4));
  no!(r, range.contains(8));

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:174
pub fn index_range__First() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 3);
  eq!(r, range.first(), 5);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:180
pub fn index_range__Last() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 3);
  eq!(r, range.last(), 7);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:186
pub fn index_range__OneAfterEnd() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 3);
  eq!(r, range.one_after_last(), 8);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:192
pub fn index_range__OneBeforeStart() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 3);
  eq!(r, range.one_before_start(), 4);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:198
pub fn index_range__Start() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(6, 2);
  eq!(r, range.start(), 6);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:204
pub fn index_range__Slice() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 15);
  let slice = range.slice(2, 6);
  eq!(r, slice.size(), 6);
  eq!(r, slice.first(), 7);
  eq!(r, slice.last(), 12);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:213
pub fn index_range__Intersect() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 15);
  eq!(r, range.intersect(m::IndexRange::new(2, 2)), m::IndexRange::new(5, 0));
  eq!(r, range.intersect(m::IndexRange::new(4, 2)), m::IndexRange::new(5, 1));
  eq!(r, range.intersect(m::IndexRange::new(3, 20)), m::IndexRange::new(5, 15));
  eq!(r, range.intersect(m::IndexRange::new(5, 15)), m::IndexRange::new(5, 15));
  eq!(r, range.intersect(m::IndexRange::new(15, 10)), m::IndexRange::new(15, 5));
  eq!(r, range.intersect(m::IndexRange::new(22, 2)), m::IndexRange::new(20, 0));

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:224
pub fn index_range__SliceRange() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(5, 15);
  let slice = range.slice_range(m::IndexRange::new(3, 5));
  eq!(r, slice.size(), 5);
  eq!(r, slice.first(), 8);
  eq!(r, slice.last(), 12);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:233
pub fn index_range__DropBack() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(4, 4);
  let slice = a.drop_back(2);
  eq!(r, slice.size(), 2);
  eq!(r, slice.start(), 4);
  eq!(r, slice.get(1), 5);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:242
pub fn index_range__DropBackAll() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(4, 4);
  let slice = a.drop_back(a.size());
  yes!(r, slice.is_empty());

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:249
pub fn index_range__DropFront() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(4, 4);
  let slice = a.drop_front(1);
  eq!(r, slice.size(), 3);
  eq!(r, slice.get(0), 5);
  eq!(r, slice.get(1), 6);
  eq!(r, slice.last(), 7);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:259
pub fn index_range__DropFrontLargeN() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(1, 5);
  let slice = a.drop_front(100);
  yes!(r, slice.is_empty());

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:266
pub fn index_range__DropFrontAll() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::from_size(50);
  let slice = a.drop_front(a.size());
  yes!(r, slice.is_empty());

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:273
pub fn index_range__TakeFront() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(4, 4);
  let slice = a.take_front(2);
  eq!(r, slice.size(), 2);
  eq!(r, slice.get(0), 4);
  eq!(r, slice.get(1), 5);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:282
pub fn index_range__TakeFrontLargeN() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(4, 4);
  let slice = a.take_front(100);
  eq!(r, slice.size(), 4);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:289
pub fn index_range__TakeBack() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(4, 4);
  let slice = a.take_back(2);
  eq!(r, slice.size(), 2);
  eq!(r, slice.get(0), 6);
  eq!(r, slice.get(1), 7);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:298
pub fn index_range__TakeBackLargeN() -> Report {
let mut r = Report::default();

  let a = m::IndexRange::new(3, 4);
  let slice = a.take_back(100);
  eq!(r, slice.size(), 4);
  eq!(r, slice.size(), 4);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:306
pub fn index_range__constexpr_() -> Report {
let mut r = Report::default();
const RANGE: m::IndexRange = m::IndexRange::new(1,1);
let compiles: [i32; RANGE.get(0) as usize] = [1];
const _: () = assert!(RANGE.size() == 1);
eq!(r, compiles[0], 1);
r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:314
pub fn index_range__GenericAlgorithms() -> Report {
let mut r = Report::default();

  let range = m::IndexRange::new(4, 10);
  yes!(r, range.iter().any(|v| v == 6));
  no!(r, range.iter().any(|v| v == 20));
  eq!(r, range.iter().filter(|&v| v < 7).count(), 3);

r
}

// source/blender/blenlib/tests/BLI_index_range_test.cc:322
pub fn index_range__SplitByAlignment() -> Report {
let mut r = Report::default();

  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(0, 0), 16);
    eq!(r, ranges.prefix, m::IndexRange::empty());
    eq!(r, ranges.aligned, m::IndexRange::empty());
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(0, 24), 8);
    eq!(r, ranges.prefix, m::IndexRange::empty());
    eq!(r, ranges.aligned, m::IndexRange::new(0, 24));
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(1, 2), 4);
    eq!(r, ranges.prefix, m::IndexRange::new(1, 2));
    eq!(r, ranges.aligned, m::IndexRange::empty());
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(3, 50), 8);
    eq!(r, ranges.prefix, m::IndexRange::new(3, 5));
    eq!(r, ranges.aligned, m::IndexRange::new(8, 40));
    eq!(r, ranges.suffix, m::IndexRange::new(48, 5));
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(3, 50), 1);
    eq!(r, ranges.prefix, m::IndexRange::empty());
    eq!(r, ranges.aligned, m::IndexRange::new(3, 50));
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(64, 16), 16);
    eq!(r, ranges.prefix, m::IndexRange::empty());
    eq!(r, ranges.aligned, m::IndexRange::new(64, 16));
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(3, 5), 8);
    eq!(r, ranges.prefix, m::IndexRange::new(3, 5));
    eq!(r, ranges.aligned, m::IndexRange::empty());
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::from_size(64), 64);
    eq!(r, ranges.prefix, m::IndexRange::empty());
    eq!(r, ranges.aligned, m::IndexRange::from_size(64));
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(64, 64), 64);
    eq!(r, ranges.prefix, m::IndexRange::empty());
    eq!(r, ranges.aligned, m::IndexRange::new(64, 64));
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }
  {
    let ranges = m::split_index_range_by_alignment(m::IndexRange::new(4, 8), 64);
    eq!(r, ranges.prefix, m::IndexRange::new(4, 8));
    eq!(r, ranges.aligned, m::IndexRange::empty());
    eq!(r, ranges.suffix, m::IndexRange::empty());
  }

r
}

// source/blender/blenlib/tests/BLI_binary_search_test.cc:18
pub fn binary_search__Empty() -> Report {
let mut r = Report::default();

  eq!(r, m::first_if(&[], |v: &bool| *v), 0);
  eq!(r, m::last_if(&[], |v: &bool| *v), -1);

r
}

// source/blender/blenlib/tests/BLI_binary_search_test.cc:24
pub fn binary_search__One() -> Report {
let mut r = Report::default();

  eq!(r, m::first_if(&[true], |v: &bool| *v), 0);
  eq!(r, m::last_if(&[true], |v: &bool| *v), 0);

  eq!(r, m::first_if(&[false], |v: &bool| *v), 1);
  eq!(r, m::last_if(&[false], |v: &bool| *v), -1);

r
}

// source/blender/blenlib/tests/BLI_binary_search_test.cc:33
pub fn binary_search__Multiple() -> Report {
let mut r = Report::default();

  eq!(r, m::first_if(&[true, true, true, true, true, true], |v: &bool| *v), 0);
  eq!(r, m::first_if(&[false, true, true, true, true, true], |v: &bool| *v), 1);
  eq!(r, m::first_if(&[false, false, true, true, true, true], |v: &bool| *v), 2);
  eq!(r, m::first_if(&[false, false, false, true, true, true], |v: &bool| *v), 3);
  eq!(r, m::first_if(&[false, false, false, false, true, true], |v: &bool| *v), 4);
  eq!(r, m::first_if(&[false, false, false, false, false, true], |v: &bool| *v), 5);
  eq!(r, m::first_if(&[false, false, false, false, false, false], |v: &bool| *v), 6);

  eq!(r, m::last_if(&[false, false, false, false, false, false], |v: &bool| *v), -1);
  eq!(r, m::last_if(&[true, false, false, false, false, false], |v: &bool| *v), 0);
  eq!(r, m::last_if(&[true, true, false, false, false, false], |v: &bool| *v), 1);
  eq!(r, m::last_if(&[true, true, true, false, false, false], |v: &bool| *v), 2);
  eq!(r, m::last_if(&[true, true, true, true, false, false], |v: &bool| *v), 3);
  eq!(r, m::last_if(&[true, true, true, true, true, false], |v: &bool| *v), 4);
  eq!(r, m::last_if(&[true, true, true, true, true, true], |v: &bool| *v), 5);

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:14
pub fn bounds__Empty() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::new(m::VecN([(1.0_f32) as f32;2]), m::VecN([(-1.0_f32) as f32;2]));
  let mut bounds3 = m::Bounds::new(m::VecN([(-1.0_f32) as f32;2]), m::VecN([(1.0_f32) as f32;2]));
  yes!(r, bounds1.is_empty());
  yes!(r, bounds2.is_empty());
  no!(r, bounds3.is_empty());

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:24
pub fn bounds__EmptyInt() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(0);
  let mut bounds2 = m::Bounds::new(1, -1);
  let mut bounds3 = m::Bounds::new(-1, 1);
  yes!(r, bounds1.is_empty());
  yes!(r, bounds2.is_empty());
  no!(r, bounds3.is_empty());

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:34
pub fn bounds__Center() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::point(m::VecN([(-1.0_f32) as f32;2]));
  let mut bounds3 = m::Bounds::new(m::VecN([(-1.0_f32) as f32;2]), m::VecN([(1.0_f32) as f32;2]));
  let mut bounds4 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  eq!(r, bounds1.center(), m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds2.center(), m::VecN([(-1.0_f32) as f32;2]));
  eq!(r, bounds3.center(), m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds4.center(), m::VecN([(-0.5_f32) as f32, (-0.5_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:46
pub fn bounds__Size() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::point(m::VecN([(-1.0_f32) as f32;2]));
  let mut bounds3 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  eq!(r, bounds1.size(), m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds2.size(), m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds3.size(), m::VecN([(5.0_f32) as f32, (9.0_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:56
pub fn bounds__Translate() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  bounds1.translate(m::VecN([(-1.0_f32) as f32;2]));
  bounds2.translate(m::VecN([(2.0_f32) as f32;2]));
  eq!(r, bounds1.min, m::VecN([(-1.0_f32) as f32;2]));
  eq!(r, bounds1.max, m::VecN([(-1.0_f32) as f32;2]));
  eq!(r, bounds2.min, m::VecN([(-1.0_f32) as f32, (-3.0_f32) as f32]));
  eq!(r, bounds2.max, m::VecN([(4.0_f32) as f32, (6.0_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:68
pub fn bounds__ScaleFromCenter() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  bounds1.scale_from_center(m::VecN([(2.0_f32) as f32;2]));
  let bound2_size = bounds2.size();
  bounds2.scale_from_center(m::VecN([(2.0_f32) as f32, (1.0_f32) as f32]));
  eq!(r, bounds1.min, m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds1.max, m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds2.min, m::VecN([(-5.5_f32) as f32, (-5.0_f32) as f32]));
  eq!(r, bounds2.max, m::VecN([(4.5_f32) as f32, (4.0_f32) as f32]));
  eq!(r, bounds2.size(), bound2_size * m::VecN([(2.0_f32) as f32, (1.0_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:82
pub fn bounds__Resize() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  bounds1.resize(m::VecN([(1.0_f32) as f32;2]));
  bounds2.resize(m::VecN([(7.0_f32) as f32, (10.0_f32) as f32]));
  eq!(r, bounds1.center(), m::VecN([(0.0_f32) as f32;2]));
  eq!(r, bounds1.size(), m::VecN([(1.0_f32) as f32;2]));
  eq!(r, bounds2.size(), m::VecN([(7.0_f32) as f32, (10.0_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:93
pub fn bounds__Recenter() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  bounds1.recenter(m::VecN([(-1.0_f32) as f32;2]));
  bounds2.recenter(m::VecN([(2.0_f32) as f32, (3.0_f32) as f32]));
  eq!(r, bounds1.center(), m::VecN([(-1.0_f32) as f32;2]));
  eq!(r, bounds2.center(), m::VecN([(2.0_f32) as f32, (3.0_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:103
pub fn bounds__Pad() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::point(m::VecN([(0.0_f32) as f32;2]));
  let mut bounds2 = m::Bounds::new(m::VecN([(-1.0_f32) as f32;2]), m::VecN([(1.0_f32) as f32;2]));
  let mut bounds3 = m::Bounds::new(m::VecN([(-3.0_f32) as f32, (-5.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (4.0_f32) as f32]));
  bounds1.pad(m::VecN([(1.0_f32) as f32;2]));
  bounds2.pad(1.0_f32);
  bounds3.pad(m::VecN([(1.0_f32) as f32, (2.0_f32) as f32]));
  eq!(r, bounds1.min, m::VecN([(-1.0_f32) as f32;2]));
  eq!(r, bounds1.max, m::VecN([(1.0_f32) as f32;2]));
  eq!(r, bounds2.min, m::VecN([(-2.0_f32) as f32;2]));
  eq!(r, bounds2.max, m::VecN([(2.0_f32) as f32;2]));
  eq!(r, bounds3.min, m::VecN([(-4.0_f32) as f32, (-7.0_f32) as f32]));
  eq!(r, bounds3.max, m::VecN([(3.0_f32) as f32, (6.0_f32) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:119
pub fn bounds__MinMaxEmpty() -> Report {
let mut r = Report::default();

  let empty_span: [m::VecN<f32,2>;0] = [];
  yes!(r, empty_span.is_empty());
  let result = m::min_max(&empty_span);
  eq!(r, result, None);

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:127
pub fn bounds__MinMax() -> Report {
let mut r = Report::default();

  let data = vec![m::VecN([(0) as f32, (1) as f32]), m::VecN([(3) as f32, (-1) as f32]), m::VecN([(0) as f32, (-2) as f32]), m::VecN([(-1) as f32, (1) as f32])];
  let result = m::min_max(&data);
  eq!(r, result.unwrap().min, m::VecN([(-1) as f32, (-2) as f32]));
  eq!(r, result.unwrap().max, m::VecN([(3) as f32, (1) as f32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:135
pub fn bounds__MinMaxFloat() -> Report {
let mut r = Report::default();

  let data = vec![1.0_f32, 3.0_f32, 0.0_f32, -1.0_f32];
  let result = m::min_max(&data);
  eq!(r, result.unwrap().min, -1.0_f32);
  eq!(r, result.unwrap().max, 3.0_f32);

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:143
pub fn bounds__MinGreaterThanZero() -> Report {
let mut r = Report::default();

  let data = vec![1.5_f32, 3.0_f32, 1.1_f32, 100.0_f32];
  let result = m::min_max(&data);
  gt!(r, result.unwrap().min, 1.0_f32);

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:150
pub fn bounds__MinMaxRadii() -> Report {
let mut r = Report::default();

  let data = vec![m::VecN([(0) as i32, (1) as i32]), m::VecN([(3) as i32, (-1) as i32]), m::VecN([(0) as i32, (-2) as i32]), m::VecN([(-1) as i32, (1) as i32])];
  let radii = vec![5, 1, 1, 4];
  let result = m::min_max_with_radii(&data, &radii);
  eq!(r, result.unwrap().min, m::VecN([(-5) as i32, (-4) as i32]));
  eq!(r, result.unwrap().max, m::VecN([(5) as i32, (6) as i32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:159
pub fn bounds__Large() -> Report {
let mut r = Report::default();

  let mut data = vec![m::VecN([0_i32;2]);10000];
  for i in 0..data.len() {
    data[i] = m::VecN([(i) as i32, (i) as i32]);
  }

  let result = m::min_max(&data);
  eq!(r, result.unwrap().min, m::VecN([(0) as i32, (0) as i32]));
  eq!(r, result.unwrap().max, m::VecN([(9999) as i32, (9999) as i32]));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:171
pub fn bounds__Contains() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::new(m::VecN([(-3) as i32, (-5) as i32]), m::VecN([(2) as i32, (4) as i32]));
  let data1 = vec![m::VecN([(0) as i32, (1) as i32]), m::VecN([(3) as i32, (-1) as i32]), m::VecN([(-3) as i32, (-2) as i32]), m::VecN([(-1) as i32, (1) as i32])];
  let expected1 = vec![true, false, true, true];

  for i in 0..data1.len() {
    eq!(r, bounds1.contains(data1[i]), expected1[i]);
  }

  let mut bounds2 = m::Bounds::new(m::VecN([(-2.0_f32) as f32, (-1.0_f32) as f32]), m::VecN([(4.0_f32) as f32, (5.0_f32) as f32]));
  let data2 = vec![
      m::VecN([(-2.0_f32) as f32, (-2.0_f32) as f32]), m::VecN([(-3.0_f32) as f32, (-1.0_f32) as f32]), m::VecN([(4.0_f32) as f32, (6.0_f32) as f32]), m::VecN([(5.0_f32) as f32, (5.0_f32) as f32])];
  let expected2 = vec![false, false, false, false];
  for i in 0..data2.len() {
    eq!(r, bounds2.contains(data2[i]), expected2[i]);
  }

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:190
pub fn bounds__IntersectSegment1D() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::new(-1, 6);
  yes!(r, bounds1.intersects_segment(8, 2));
  no!(r, bounds1.intersects_segment(-2, -3));
  yes!(r, bounds1.intersects_segment(8, 6));
  no!(r, bounds1.intersects_segment(8, 8));
  yes!(r, bounds1.intersects_segment(0, 0));

  let mut bounds2 = m::Bounds::new(-1.0_f32, 6.0_f32);
  yes!(r, bounds2.intersects_segment(8.0_f32, 2.0_f32));
  no!(r, bounds2.intersects_segment(-2.0_f32, -3.0_f32));
  yes!(r, bounds2.intersects_segment(8.0_f32, 6.0_f32));
  no!(r, bounds2.intersects_segment(8.0_f32, 8.0_f32));
  yes!(r, bounds2.intersects_segment(0.0_f32, 0.0_f32));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:207
pub fn bounds__IntersectSegment2D() -> Report {
let mut r = Report::default();

  let mut bounds1 = m::Bounds::new(m::VecN([(-2) as i32, (-1) as i32]), m::VecN([(4) as i32, (5) as i32]));
  yes!(r, bounds1.intersects_segment(m::VecN([(1) as i32, (2) as i32]), m::VecN([(5) as i32, (3) as i32])));
  no!(r, bounds1.intersects_segment(m::VecN([(-4) as i32, (7) as i32]), m::VecN([(5) as i32, (6) as i32])));
  yes!(r, bounds1.intersects_segment(m::VecN([(-2) as i32, (2) as i32]), m::VecN([(-4) as i32, (2) as i32])));
  no!(r, bounds1.intersects_segment(m::VecN([(5) as i32, (5) as i32]), m::VecN([(5) as i32, (5) as i32])));
  yes!(r, bounds1.intersects_segment(m::VecN([(1) as i32, (1) as i32]), m::VecN([(1) as i32, (1) as i32])));
  no!(r, bounds1.intersects_segment(m::VecN([(0) as i32, (-3) as i32]), m::VecN([(-4) as i32, (0) as i32])));
  yes!(r, bounds1.intersects_segment(m::VecN([(1) as i32, (-2) as i32]), m::VecN([(-3) as i32, (1) as i32])));

  let mut bounds2 = m::Bounds::new(m::VecN([(-2.0_f32) as f32, (-1.0_f32) as f32]), m::VecN([(4.0_f32) as f32, (5.0_f32) as f32]));
  yes!(r, bounds2.intersects_segment(m::VecN([(1.0_f32) as f32, (2.0_f32) as f32]), m::VecN([(5.0_f32) as f32, (3.0_f32) as f32])));
  no!(r, bounds2.intersects_segment(m::VecN([(-4.0_f32) as f32, (7.0_f32) as f32]), m::VecN([(5.0_f32) as f32, (6.0_f32) as f32])));
  yes!(r, bounds2.intersects_segment(m::VecN([(-2.0_f32) as f32, (2.0_f32) as f32]), m::VecN([(-4.0_f32) as f32, (2.0_f32) as f32])));
  no!(r, bounds2.intersects_segment(m::VecN([(5.0_f32) as f32, (5.0_f32) as f32]), m::VecN([(5.0_f32) as f32, (5.0_f32) as f32])));
  yes!(r, bounds2.intersects_segment(m::VecN([(1.0_f32) as f32, (1.0_f32) as f32]), m::VecN([(1.0_f32) as f32, (1.0_f32) as f32])));
  no!(r, bounds2.intersects_segment(m::VecN([(0.0_f32) as f32, (-3.0_f32) as f32]), m::VecN([(-4.0_f32) as f32, (0.0_f32) as f32])));
  yes!(r, bounds2.intersects_segment(m::VecN([(1.0_f32) as f32, (-2.0_f32) as f32]), m::VecN([(-3.0_f32) as f32, (1.0_f32) as f32])));

r
}

// source/blender/blenlib/tests/BLI_bounds_test.cc:228
pub fn bounds__IntersectSegment3D() -> Report {
let mut r = Report::default();

  let mut float_bounds = m::Bounds::new(m::VecN([(-2.0_f32) as f32, (-2.0_f32) as f32, (-2.0_f32) as f32]), m::VecN([(2.0_f32) as f32, (2.0_f32) as f32, (2.0_f32) as f32]));
  let mut int_bounds = m::Bounds::new(m::VecN([(-2) as i32, (-2) as i32, (-2) as i32]), m::VecN([(2) as i32, (2) as i32, (2) as i32]));
  
  yes!(r, 
      float_bounds.intersects_segment(m::VecN([(-1.0_f32) as f32, (-1.0_f32) as f32, (-1.0_f32) as f32]), m::VecN([(1.0_f32) as f32, (1.0_f32) as f32, (1.0_f32) as f32])));
  yes!(r, int_bounds.intersects_segment(m::VecN([(-1) as i32, (-1) as i32, (-1) as i32]), m::VecN([(1) as i32, (1) as i32, (1) as i32])));

  
  no!(r, float_bounds.intersects_segment(m::VecN([(-10.0_f32) as f32, (-10.0_f32) as f32, (-10.0_f32) as f32]),
                                               m::VecN([(-10.0_f32) as f32, (-10.0_f32) as f32, (10.0_f32) as f32])));
  no!(r, int_bounds.intersects_segment(m::VecN([(-10) as i32, (-10) as i32, (-10) as i32]), m::VecN([(-10) as i32, (-10) as i32, (-10) as i32])));

  
  yes!(r, 
      float_bounds.intersects_segment(m::VecN([(-4.0_f32) as f32, (-4.0_f32) as f32, (-4.0_f32) as f32]), m::VecN([(4.0_f32) as f32, (4.0_f32) as f32, (4.0_f32) as f32])));
  yes!(r, int_bounds.intersects_segment(m::VecN([(-4) as i32, (-4) as i32, (-4) as i32]), m::VecN([(4) as i32, (4) as i32, (4) as i32])));

  
  yes!(r, float_bounds.intersects_segment(m::VecN([(0.0_f32) as f32, (0.0_f32) as f32, (0.0_f32) as f32]), m::VecN([(4.0_f32) as f32, (4.0_f32) as f32, (4.0_f32) as f32])));
  yes!(r, int_bounds.intersects_segment(m::VecN([(0) as i32, (0) as i32, (0) as i32]), m::VecN([(4) as i32, (4) as i32, (4) as i32])));

  
  yes!(r, 
      float_bounds.intersects_segment(m::VecN([(-4.0_f32) as f32, (-4.0_f32) as f32, (-4.0_f32) as f32]), m::VecN([(0.0_f32) as f32, (0.0_f32) as f32, (0.0_f32) as f32])));
  yes!(r, int_bounds.intersects_segment(m::VecN([(-4) as i32, (-4) as i32, (-4) as i32]), m::VecN([(0) as i32, (0) as i32, (0) as i32])));

  
  yes!(r, 
      float_bounds.intersects_segment(m::VecN([(0.0_f32) as f32, (2.0_f32) as f32, (-4.0_f32) as f32]), m::VecN([(0.0_f32) as f32, (2.0_f32) as f32, (4.0_f32) as f32])));
  yes!(r, int_bounds.intersects_segment(m::VecN([(0) as i32, (2) as i32, (-4) as i32]), m::VecN([(0) as i32, (2) as i32, (4) as i32])));

  
  yes!(r, float_bounds.intersects_segment(m::VecN([(0.0_f32) as f32, (0.0_f32) as f32, (0.0_f32) as f32]), m::VecN([(0.0_f32) as f32, (0.0_f32) as f32, (0.0_f32) as f32])));
  yes!(r, int_bounds.intersects_segment(m::VecN([(0) as i32, (0) as i32, (0) as i32]), m::VecN([(0) as i32, (0) as i32, (0) as i32])));

  
  no!(r, 
      float_bounds.intersects_segment(m::VecN([(4.0_f32) as f32, (4.0_f32) as f32, (4.0_f32) as f32]), m::VecN([(4.0_f32) as f32, (4.0_f32) as f32, (4.0_f32) as f32])));
  no!(r, int_bounds.intersects_segment(m::VecN([(4) as i32, (4) as i32, (4) as i32]), m::VecN([(4) as i32, (4) as i32, (4) as i32])));

r
}

pub const CASES: &[(&str,fn()->Report,u32)] = &[
("index_range.DefaultConstructor",index_range__DefaultConstructor,2),
("index_range.FromBeginSize",index_range__FromBeginSize,6),
("index_range.FromBeginEnd",index_range__FromBeginEnd,6),
("index_range.FromBeginEndInclusive",index_range__FromBeginEndInclusive,5),
("index_range.FromEndSize",index_range__FromEndSize,3),
("index_range.FromSingle",index_range__FromSingle,4),
("index_range.SingleElementRange",index_range__SingleElementRange,4),
("index_range.MultipleElementRange",index_range__MultipleElementRange,6),
("index_range.SubscriptOperator",index_range__SubscriptOperator,3),
("index_range.Before",index_range__Before,4),
("index_range.After",index_range__After,5),
("index_range.Contains",index_range__Contains,5),
("index_range.First",index_range__First,1),
("index_range.Last",index_range__Last,1),
("index_range.OneAfterEnd",index_range__OneAfterEnd,1),
("index_range.OneBeforeStart",index_range__OneBeforeStart,1),
("index_range.Start",index_range__Start,1),
("index_range.Slice",index_range__Slice,3),
("index_range.Intersect",index_range__Intersect,6),
("index_range.SliceRange",index_range__SliceRange,3),
("index_range.DropBack",index_range__DropBack,3),
("index_range.DropBackAll",index_range__DropBackAll,1),
("index_range.DropFront",index_range__DropFront,4),
("index_range.DropFrontLargeN",index_range__DropFrontLargeN,1),
("index_range.DropFrontAll",index_range__DropFrontAll,1),
("index_range.TakeFront",index_range__TakeFront,3),
("index_range.TakeFrontLargeN",index_range__TakeFrontLargeN,1),
("index_range.TakeBack",index_range__TakeBack,3),
("index_range.TakeBackLargeN",index_range__TakeBackLargeN,2),
("index_range.constexpr_",index_range__constexpr_,1),
("index_range.GenericAlgorithms",index_range__GenericAlgorithms,3),
("index_range.SplitByAlignment",index_range__SplitByAlignment,30),
("binary_search.Empty",binary_search__Empty,2),
("binary_search.One",binary_search__One,4),
("binary_search.Multiple",binary_search__Multiple,14),
("bounds.Empty",bounds__Empty,3),
("bounds.EmptyInt",bounds__EmptyInt,3),
("bounds.Center",bounds__Center,4),
("bounds.Size",bounds__Size,3),
("bounds.Translate",bounds__Translate,4),
("bounds.ScaleFromCenter",bounds__ScaleFromCenter,5),
("bounds.Resize",bounds__Resize,3),
("bounds.Recenter",bounds__Recenter,2),
("bounds.Pad",bounds__Pad,6),
("bounds.MinMaxEmpty",bounds__MinMaxEmpty,2),
("bounds.MinMax",bounds__MinMax,2),
("bounds.MinMaxFloat",bounds__MinMaxFloat,2),
("bounds.MinGreaterThanZero",bounds__MinGreaterThanZero,1),
("bounds.MinMaxRadii",bounds__MinMaxRadii,2),
("bounds.Large",bounds__Large,2),
("bounds.Contains",bounds__Contains,8),
("bounds.IntersectSegment1D",bounds__IntersectSegment1D,10),
("bounds.IntersectSegment2D",bounds__IntersectSegment2D,14),
("bounds.IntersectSegment3D",bounds__IntersectSegment3D,16),
];
