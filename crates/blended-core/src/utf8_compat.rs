// SPDX-FileCopyrightText: 1999 Tom Tromey
// SPDX-FileCopyrightText: 2000 Red Hat, Inc. All rights reserved.
// SPDX-FileCopyrightText: 2011-2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Adapted from pinned string_utf8.cc, string_cursor_utf8.cc and rand.cc.
// Reference 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Compatibility, not strict modern Unicode validation: legacy 5/6-byte sequences
// and the original selective invalid-code checks are intentionally retained.
// Safe slices replace native pointers without reading beyond the supplied input.
include!("utf8_combining.rs");

pub fn size_or_error(first: u8) -> i32 {
    match first {
        0..=127 => 1,
        192..=223 => 2,
        224..=239 => 3,
        240..=247 => 4,
        248..=251 => 5,
        252..=253 => 6,
        _ => -1,
    }
}
fn skip(first: u8) -> usize { size_or_error(first).max(1) as usize }

/// The pinned validator reports the start of the first erroneous byte sequence.
/// NUL is invalid inside the explicitly supplied length, not an early stop.
pub fn invalid_byte(bytes: &[u8], len: usize) -> isize {
    assert!(len <= bytes.len());
    let mut i = 0;
    while i < len {
        let c = bytes[i];
        if c == 0 || c >= 254 { return i as isize; }
        if c < 128 { i += 1; continue; }
        if c & 0xc0 != 0xc0 { return i as isize; }
        let n = skip(c);
        if i + n > len || bytes[i + 1] & 0xc0 != 0x80 { return i as isize; }
        let second = bytes[i + 1];
        let bad = match n {
            2 => c & 0x3e == 0,
            3 => {
                let pair = (second, bytes[i + 2]);
                (c == 0xe0 && second & 0x20 == 0)
                    || (c == 0xed && matches!(pair, (0xa0,0x80)|(0xad,0xbf)|(0xae,0x80)|(0xaf,0xbf)|(0xb0,0x80)|(0xbe,0x80)|(0xbf,0xbf)))
                    || (c == 0xef && matches!(pair, (0xbf,0xbe)|(0xbf,0xbf)))
            }
            4 => c == 0xf0 && second & 0x30 == 0,
            5 => c == 0xf8 && second & 0x38 == 0,
            6 => c == 0xfc && second & 0x3c == 0,
            _ => unreachable!(),
        };
        if bad || bytes[i+2..i+n].iter().any(|b| b & 0xc0 != 0x80) { return i as isize; }
        i += n;
    }
    -1
}

pub fn invalid_strip(bytes: &mut [u8], len: usize) -> i32 {
    assert!(len < bytes.len() && bytes[len] == 0);
    let mut remaining = len;
    let mut offset = 0;
    let mut errors = 0;
    loop {
        let bad = invalid_byte(&bytes[offset..], remaining);
        if bad < 0 { break; }
        offset += bad as usize;
        remaining -= bad as usize + 1;
        errors += 1;
        if remaining == 0 { bytes[offset] = 0; break; }
        bytes.copy_within(offset+1..offset+remaining+2, offset);
    }
    errors
}

pub fn invalid_substitute(bytes: &mut [u8], len: usize, substitute: u8) -> i32 {
    assert!(len < bytes.len() && bytes[len] == 0 && substitute != 0);
    let mut offset = 0;
    let mut errors = 0;
    loop {
        let bad = invalid_byte(&bytes[offset..], len - offset);
        if bad < 0 { break; }
        offset += bad as usize;
        bytes[offset] = substitute;
        offset += 1;
        errors += 1;
    }
    errors
}

/// Returns the original decoded value and consumed length; malformed input
/// consumes one unsigned byte. Legacy overlong/5/6-byte decoding is deliberate.
pub fn decode_step_safe(bytes: &[u8], len: usize, offset: &mut usize) -> u32 {
    assert!(len <= bytes.len() && *offset < len);
    let start = *offset;
    let first = bytes[start];
    let n = size_or_error(first);
    if n > 0 && start + n as usize <= len {
        let n = n as usize;
        let mask = [0_u8,0x7f,0x1f,0x0f,0x07,0x03,0x01][n];
        let mut value = u32::from(first & mask);
        let mut valid = true;
        for &b in &bytes[start+1..start+n] {
            if b & 0xc0 != 0x80 { valid = false; break; }
            value = (value << 6) | u32::from(b & 0x3f);
        }
        if valid { *offset += n; return value; }
    }
    *offset += 1;
    u32::from(first)
}

pub fn count_bytes(bytes: &[u8], limit: usize) -> (usize, usize) {
    assert!(limit <= bytes.len());
    let mut offset = 0;
    let mut count = 0;
    while offset < bytes.len() && bytes[offset] != 0 {
        let mut step = skip(bytes[offset]);
        if offset + step > limit { break; }
        for j in 1..step { if bytes[offset+j] == 0 { step = j; break; } }
        offset += step;
        count += 1;
    }
    (count, offset)
}

/// Capacity includes the final NUL. Continuation-byte validity is not checked
/// by the original copying function. An embedded NUL still ends a partial run.
pub fn copy_into(dst: &mut [u8], src: &[u8], capacity: usize) -> usize {
    assert!(capacity > 0 && capacity <= dst.len());
    let mut position = 0;
    let mut remaining = capacity - 1;
    while position < src.len() {
        let n = skip(src[position]);
        if n > remaining { break; }
        remaining -= n;
        for _ in 0..n {
            let b = *src.get(position).expect("Source must contain its promised bytes or NUL");
            dst[position] = b;
            if b == 0 { return position; }
            position += 1;
        }
    }
    dst[position] = 0;
    position
}

/// The exact single-%s formatting form exercised by these tests. This adapter
/// is intentionally not represented as a complete C varargs formatter.
pub fn printf_s(dst: &mut [u8], src: &[u8], capacity: usize, actual_length: bool) -> usize {
    assert!(capacity > 0 && capacity <= dst.len());
    let required = src.iter().position(|&v| v == 0).unwrap_or(src.len());
    let copied = required.min(capacity - 1);
    dst[..copied].copy_from_slice(&src[..copied]);
    dst[copied] = 0;
    if required < capacity { return required; }
    let trimmed = count_bytes(&dst[..capacity], capacity - 1).1;
    dst[trimmed] = 0;
    if actual_length { trimmed } else { required }
}

pub fn offset_from_index(bytes: &[u8], len: usize, target: usize) -> usize {
    let mut offset = 0;
    for _ in 0..target {
        if offset >= len { break; }
        decode_step_safe(bytes, len, &mut offset);
    }
    offset
}

/// Whether pinned wcwidth is zero, which is the only width predicate used by
/// these cursor operations. Generated intervals are the exact pinned table.
pub fn zero_width(code: u32) -> bool {
    if code >= 0xf0000 || (0xe000..0xf8ff).contains(&code) || (0x1f300..0x1fbff).contains(&code) { return false; }
    if code == 0 { return true; }
    if code < 32 || (0x7f..0xa0).contains(&code) { return false; }
    let index = COMBINING.partition_point(|&(_,last)| last < code);
    index < COMBINING.len() && COMBINING[index].0 <= code
}
fn zero_width_at(bytes: &[u8], offset: usize) -> bool {
    let first = bytes[offset];
    let n = size_or_error(first);
    if n < 0 || offset + n as usize > bytes.len() { return false; }
    let n = n as usize;
    if bytes[offset+1..offset+n].iter().any(|b| b & 0xc0 != 0x80) { return false; }
    let mut pos = offset;
    zero_width(decode_step_safe(bytes, bytes.len(), &mut pos))
}

pub fn cursor_next8(bytes: &[u8], len: usize, pos: &mut i32) -> bool {
    assert!(*pos >= 0 && len < bytes.len());
    if *pos as usize >= len { return false; }
    let mut next = *pos as usize;
    loop {
        if next < len+1 && bytes[next] != 0 {
            next += 1;
            while next < len+1 && bytes[next] & 0xc0 == 0x80 { next += 1; }
        }
        if next >= len+1 || bytes[next] == 0 || !zero_width_at(bytes,next) { break; }
    }
    *pos = next.min(len) as i32;
    true
}
pub fn cursor_prev8(bytes: &[u8], len: usize, pos: &mut i32) -> bool {
    assert!(*pos >= 0 && len < bytes.len());
    if *pos == 0 || *pos as usize > len { return false; }
    let mut prev = *pos as usize;
    loop {
        prev -= 1;
        while prev > 0 && bytes[prev] & 0xc0 == 0x80 { prev -= 1; }
        // Safe boundary policy for all-continuation prefixes: stop at zero.
        // The original tests never require a pointer preceding the buffer.
        if prev == 0 || !zero_width_at(bytes,prev) { break; }
    }
    *pos = prev as i32;
    true
}
pub fn cursor_next32(text: &[u32], len: usize, pos: &mut i32) -> bool {
    assert!(*pos >= 0 && len <= text.len());
    if *pos as usize >= len { return false; }
    loop {
        *pos += 1;
        if *pos as usize >= len || text[*pos as usize] == 0 || !zero_width(text[*pos as usize]) { break; }
    }
    true
}
pub fn cursor_prev32(text: &[u32], len: usize, pos: &mut i32) -> bool {
    assert!(*pos >= 0 && len <= text.len());
    if *pos == 0 { return false; }
    assert!(*pos as usize <= text.len());
    loop {
        *pos -= 1;
        if *pos == 0 || !zero_width(text[*pos as usize]) { break; }
    }
    true
}

/// Exact pinned byte fixture generator. This differs from get_int32: a partial
/// six-byte batch does not advance state. Native x86_64 and wasm32 are verified
/// little-endian targets; to_ne_bytes preserves the original endian dependence.
pub struct LegacyByteRng { state: u64 }
impl LegacyByteRng {
    pub fn new(seed: u32) -> Self { Self { state: ((seed as u64) << 16) | 0x330e } }
    fn step(&mut self) { self.state = self.state.wrapping_mul(0x5deece66d).wrapping_add(0xb) & 0xffffffffffff; }
    pub fn fill(&mut self, output: &mut [u8]) {
        let n = output.len();
        let full = if n > 6 { n - n % 6 } else { 0 };
        let mut i = 0;
        while i < full { output[i..i+6].copy_from_slice(&self.state.to_ne_bytes()[..6]); i += 6; self.step(); }
        if i < n { output[i..].copy_from_slice(&self.state.to_ne_bytes()[..n-i]); }
    }
}
