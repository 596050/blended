// SPDX-FileCopyrightText: 2023-2025 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Safe Rust adapters for the operations exercised by BLI_array_utils_test.cc.
// Pinned source: 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Sequential execution preserves tested results, not native parallel scheduling.
use crate::data_structures::IndexRange;
use std::collections::HashMap;

pub fn reverse_prefix<T>(data: &mut [T], len: usize) {
    assert!(len <= data.len(), "Reverse prefix outside storage");
    data[..len].reverse();
}
pub fn find_index<T: PartialEq>(data: &[T], len: usize, value: &T) -> i64 {
    assert!(len <= data.len(), "Search prefix outside storage");
    data[..len].iter().position(|v| v == value).map_or(-1, |i| i as i64)
}
pub fn rfind_index<T: PartialEq>(data: &[T], len: usize, value: &T) -> i64 {
    assert!(len <= data.len(), "Search prefix outside storage");
    data[..len].iter().rposition(|v| v == value).map_or(-1, |i| i as i64)
}
pub fn binary_and(dst: &mut [i32], a: &[i32], b: &[i32], n: usize) {
    assert!(n <= dst.len() && n <= a.len() && n <= b.len());
    for i in 0..n { dst[i] = a[i] & b[i]; }
}
pub fn binary_or(dst: &mut [i32], a: &[i32], b: &[i32], n: usize) {
    assert!(n <= dst.len() && n <= a.len() && n <= b.len());
    for i in 0..n { dst[i] = a[i] | b[i]; }
}
/// In-place adjacent deduplication; storage past the returned prefix is retained.
pub fn deduplicate_ordered<T: Eq + Copy>(data: &mut [T], n: usize) -> usize {
    assert!(n <= data.len());
    if n == 0 { return 0; }
    let mut used = 1;
    for i in 1..n {
        if data[i] != data[used - 1] { data[used] = data[i]; used += 1; }
    }
    used
}
pub fn find_all_ranges<T: PartialEq>(data: &[T], value: T) -> Vec<IndexRange> {
    let mut ranges = Vec::new();
    let mut i = 0;
    while i < data.len() {
        if data[i] != value { i += 1; continue; }
        let start = i;
        while i < data.len() && data[i] == value { i += 1; }
        ranges.push(IndexRange::new(start as i64, (i - start) as i64));
    }
    ranges
}
/// The test's borrowed-span and genuinely function-backed VArray shapes.
pub enum VirtualInts<'a> {
    Span(&'a [i32]),
    Function { len: usize, get: Box<dyn Fn(usize) -> i32 + 'a> },
}
impl<'a> VirtualInts<'a> {
    pub fn from_slice(data: &'a [i32]) -> Self { Self::Span(data) }
    pub fn from_fn(len: usize, get: impl Fn(usize) -> i32 + 'a) -> Self { Self::Function { len, get: Box::new(get) } }
    pub fn len(&self) -> usize { match self { Self::Span(v) => v.len(), Self::Function { len, .. } => *len } }
    pub fn is_empty(&self) -> bool { self.len() == 0 }
    pub fn at(&self, i: usize) -> i32 {
        assert!(i < self.len());
        match self { Self::Span(v) => v[i], Self::Function { get, .. } => get(i) }
    }
}
/// First maximum for the tested sequential span/function forms. This is not an
/// implementation of every VArray representation or native reduction schedule.
pub fn max_element_index(values: &VirtualInts<'_>) -> Option<usize> {
    if values.is_empty() { return None; }
    let mut best = 0;
    let mut maximum = values.at(0);
    for i in 1..values.len() {
        let value = values.at(i);
        if maximum < value { best = i; maximum = value; }
    }
    Some(best)
}
/// Map selected IDs to dense group numbers in first-selected-occurrence order.
/// Mask entries have IndexMask's ascending, unique, in-bounds preconditions.
/// Dense IDs use the original lookup-table strategy; sparse IDs use a hash map.
pub fn group_ids_to_indices(ids: &[i32], mask: &[usize], output: &mut [i32], mut first: Option<&mut Vec<i32>>) -> usize {
    assert_eq!(mask.len(), output.len(), "Output must match selected index count");
    assert!(mask.iter().all(|&i| i < ids.len() && i <= i32::MAX as usize));
    assert!(mask.windows(2).all(|w| w[0] < w[1]), "Mask must be strictly ascending");
    if mask.is_empty() { return 0; }
    let min = mask.iter().map(|&i| ids[i] as i64).min().unwrap();
    let max = mask.iter().map(|&i| ids[i] as i64).max().unwrap();
    let extent = (max - min + 1) as u64;
    if extent < (mask.len() as u64).saturating_mul(4) {
        let mut first_element = vec![usize::MAX; extent as usize];
        for &i in mask { let slot = (ids[i] as i64 - min) as usize; first_element[slot] = first_element[slot].min(i); }
        let mut first_indices = Vec::new();
        for &i in mask { if first_element[(ids[i] as i64 - min) as usize] == i { first_indices.push(i as i32); } }
        for (group, &index) in first_indices.iter().enumerate() { first_element[(ids[index as usize] as i64 - min) as usize] = group; }
        for (pos, &i) in mask.iter().enumerate() { output[pos] = first_element[(ids[i] as i64 - min) as usize] as i32; }
        let count = first_indices.len();
        if let Some(first) = first { *first = first_indices; }
        count
    } else {
        let mut groups = HashMap::<i32, i32>::new();
        for (pos, &i) in mask.iter().enumerate() {
            let next = groups.len() as i32;
            let group = *groups.entry(ids[i]).or_insert(next);
            if let Some(ref mut first) = first { if group as usize == first.len() { first.push(i as i32); } }
            output[pos] = group;
        }
        groups.len()
    }
}
