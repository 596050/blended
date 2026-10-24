// SPDX-FileCopyrightText: 2014 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Adapted from pinned blenlib/intern/hash_mm2a.cc. Not cryptographic or portable file hashing.
const M: u32 = 0x5bd1e995;
fn mix(hash: &mut u32, word: &mut u32) {
    *word = word.wrapping_mul(M); *word ^= *word >> 24; *word = word.wrapping_mul(M);
    *hash = hash.wrapping_mul(M) ^ *word;
}
#[derive(Debug, Clone, Default)]
pub struct Murmur2A { hash: u32, tail: u32, count: u32, size: u32 }
impl Murmur2A {
    pub fn new(seed: u32) -> Self { Self { hash: seed, ..Self::default() } }
    pub fn reset(&mut self, seed: u32) { *self = Self::new(seed); }
    fn mix_tail(&mut self, data: &mut &[u8]) {
        while !data.is_empty() && (data.len() < 4 || self.count != 0) {
            self.tail |= u32::from(data[0]) << (self.count * 8);
            self.count += 1; *data = &data[1..];
            if self.count == 4 { mix(&mut self.hash, &mut self.tail); self.tail = 0; self.count = 0; }
        }
    }
    pub fn add(&mut self, mut data: &[u8]) {
        self.size = self.size.wrapping_add(data.len() as u32);
        self.mix_tail(&mut data);
        while data.len() >= 4 {
            // Safe unaligned load with the original native-endian word interpretation.
            let mut word = u32::from_ne_bytes(data[..4].try_into().unwrap());
            mix(&mut self.hash, &mut word); data = &data[4..];
        }
        self.mix_tail(&mut data);
    }
    pub fn add_int(&mut self, value: i32) { self.add(&value.to_ne_bytes()); }
    /// The original finaliser mutates hash, tail AND size. Repeated calls do not
    /// return a cached value, and reset is required to start a new stream.
    pub fn end(&mut self) -> u32 {
        mix(&mut self.hash, &mut self.tail); mix(&mut self.hash, &mut self.size);
        self.hash ^= self.hash >> 13; self.hash = self.hash.wrapping_mul(M); self.hash ^= self.hash >> 15;
        self.hash
    }
}
