// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Pinned BLI_disjoint_set.hh: union by rank and two-pass path compression.
#[derive(Debug, Clone)]
pub struct DisjointSet { parents: Vec<usize>, ranks: Vec<usize> }
impl DisjointSet {
    pub fn new(size: usize) -> Self { Self { parents: (0..size).collect(), ranks: vec![0; size] } }
    pub fn len(&self) -> usize { self.parents.len() }
    pub fn is_empty(&self) -> bool { self.parents.is_empty() }
    pub fn find_root_readonly(&self, index: usize) -> usize {
        assert!(index < self.len()); let mut root = index;
        while self.parents[root] != root { root = self.parents[root]; }
        root
    }
    pub fn find_root(&mut self, index: usize) -> usize {
        let root = self.find_root_readonly(index); let mut current = index;
        while self.parents[current] != root { let parent = self.parents[current]; self.parents[current] = root; current = parent; }
        root
    }
    pub fn join(&mut self, x: usize, y: usize) -> usize {
        let mut left = self.find_root(x); let mut right = self.find_root(y);
        if left == right { return left; }
        if self.ranks[left] < self.ranks[right] { core::mem::swap(&mut left, &mut right); }
        self.parents[right] = left;
        if self.ranks[left] == self.ranks[right] { self.ranks[left] += 1; }
        left
    }
    pub fn in_same_set(&mut self, x: usize, y: usize) -> bool { self.find_root(x) == self.find_root(y) }
}
