// SPDX-FileCopyrightText: 2024-2026 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Rust compatibility implementation of pinned math_half.cc and
// BLI_normalized_int_types.hh, revision 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Integer conversions avoid accidental dependence on subnormal FP intermediates.
// Array NaN payload conventions match the pinned SSE2 four-lane prefix and scalar
// tail; this is a semantic implementation, not a claim of SIMD performance parity.

/// Round an unsigned significand rightward with ties-to-even.
fn round_shift_even(value: u32, shift: u32) -> u32 {
    if shift >= 32 { return 0; }
    if shift == 0 { return value; }
    let base = value >> shift;
    let remainder = value & ((1_u32 << shift) - 1);
    let midpoint = 1_u32 << (shift - 1);
    base + u32::from(remainder > midpoint || (remainder == midpoint && base & 1 != 0))
}

pub fn float_to_half(value: f32) -> u16 {
    let bits = value.to_bits();
    let sign = ((bits >> 16) & 0x8000) as u16;
    let magnitude = bits & 0x7fff_ffff;
    let result = if magnitude >= 0x4780_0000 {
        if magnitude > 0x7f80_0000 { 0x7e00 } else { 0x7c00 }
    } else if magnitude < 0x3880_0000 {
        let exponent = magnitude >> 23;
        if exponent < 102 { 0 }
        else { round_shift_even((magnitude & 0x7f_ffff) | 0x80_0000, 126 - exponent) as u16 }
    } else {
        let odd = (magnitude >> 13) & 1;
        (magnitude.wrapping_add(0xc800_0fff).wrapping_add(odd) >> 13) as u16
    };
    sign | result
}

pub fn float_to_half_make_finite(value: f32) -> u16 {
    let half = float_to_half(value);
    if half & 0x7c00 != 0x7c00 { half }
    else if half & 0x03ff == 0 { half ^ 0x07ff }
    else { half & 0x8000 }
}

pub fn half_to_float(value: u16) -> f32 {
    let sign = (u32::from(value) & 0x8000) << 16;
    let exponent = (u32::from(value) >> 10) & 31;
    let mantissa = u32::from(value) & 0x03ff;
    let bits = match exponent {
        0 if mantissa == 0 => sign,
        0 => {
            let leading = 31 - mantissa.leading_zeros();
            sign | ((103 + leading) << 23) | ((mantissa << (23 - leading)) & 0x7f_ffff)
        }
        31 => sign | 0x7f80_0000 | (mantissa << 13),
        _ => sign | ((exponent + 112) << 23) | (mantissa << 13),
    };
    f32::from_bits(bits)
}

pub fn half_to_float_array(source: &[u16], output: &mut [f32], length: usize) {
    assert!(length <= source.len() && length <= output.len(), "Conversion bounds");
    let bulk_end = length & !3;
    for i in 0..length {
        let mut bits = half_to_float(source[i]).to_bits();
        if i < bulk_end && source[i] & 0x7fff > 0x7c00 { bits |= 0x0040_0000; }
        output[i] = f32::from_bits(bits);
    }
}

pub fn float_to_half_array(source: &[f32], output: &mut [u16], length: usize) {
    assert!(length <= source.len() && length <= output.len(), "Conversion bounds");
    let bulk_end = length & !3;
    for i in 0..length {
        let bits = source[i].to_bits();
        output[i] = if i < bulk_end && bits & 0x7fff_ffff > 0x7f80_0000 {
            ((bits >> 16) & 0x8000) as u16 | 0x7e00 | ((bits >> 13) & 0x01ff) as u16
        } else { float_to_half(source[i]) };
    }
}

pub fn float_to_half_make_finite_array(source: &[f32], output: &mut [u16], length: usize) {
    assert!(length <= source.len() && length <= output.len(), "Conversion bounds");
    for i in 0..length { output[i] = float_to_half_make_finite(source[i]); }
}

pub fn float_to_half_clamp_array(source: &[f32], output: &mut [u16], length: usize, min: f32, max: f32) {
    assert!(length <= source.len() && length <= output.len(), "Conversion bounds");
    assert!(min <= max && min.is_finite() && max.is_finite(), "Finite ordered bounds required");
    let bulk_end = length & !3;
    for i in 0..length {
        // The pinned SSE4.1 prefix converts NaNs to zero BEFORE clamping.
        // The scalar tail clamps first and then converts a remaining NaN to zero.
        let mut value = source[i];
        if i < bulk_end && value.is_nan() { value = 0.0; }
        if value < min { value = min; } else if value > max { value = max; }
        if value.is_nan() { value = 0.0; }
        output[i] = float_to_half(value);
    }
}

/// A packed integer representation with explicit component widths. Little-endian
/// GPU byte order is available via `packed_bits`, but native C++ object layout is
/// not promised. Conversion truncates, rather than rounds, as pinned upstream.
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Normalized<const N: usize> { storage: u64, widths: [u8; N], signed: bool }
impl<const N: usize> Normalized<N> {
    fn validate(widths: &[u8; N], signed: bool) {
        assert!(N > 0 && widths.iter().all(|&b| b >= 1 + u8::from(signed) && b <= 16));
        assert!(widths.iter().map(|&v| u32::from(v)).sum::<u32>() <= 64);
    }
    pub fn from_float(values: [f32; N], widths: [u8; N], signed: bool) -> Self {
        Self::validate(&widths, signed);
        let mut storage = 0_u64;
        let mut shift = 0_u32;
        for i in 0..N {
            assert!(!values[i].is_nan(), "NaN-to-integer conversion is outside the defined upstream contract");
            let maximum = ((1_u32 << (widths[i] - u8::from(signed))) - 1) as f32;
            let minimum = if signed { -maximum } else { 0.0 };
            let scaled = (values[i] * maximum).max(minimum).min(maximum);
            let component = scaled as i64;
            storage |= ((component as u64) & ((1_u64 << widths[i]) - 1)) << shift;
            shift += u32::from(widths[i]);
        }
        Self {storage, widths, signed}
    }
    pub fn from_bits(storage: u64, widths: [u8; N], signed: bool) -> Self {
        Self::validate(&widths, signed);
        let total = widths.iter().map(|&v| u32::from(v)).sum::<u32>();
        assert!(total == 64 || storage >> total == 0, "Non-component bits set");
        Self {storage, widths, signed}
    }
    pub fn integers(&self) -> [i32; N] {
        let mut result = [0; N];
        let mut offset = 0;
        for i in 0..N {
            let width = u32::from(self.widths[i]);
            let field = ((self.storage >> offset) & ((1_u64 << width) - 1)) as i32;
            result[i] = if self.signed { (field << (32 - width)) >> (32 - width) } else { field };
            offset += width;
        }
        result
    }
    pub fn to_float(&self) -> [f32; N] {
        let values = self.integers();
        core::array::from_fn(|i| values[i] as f32 / ((1_u32 << (self.widths[i] - u8::from(self.signed))) - 1) as f32)
    }
    pub fn packed_bits(&self) -> u64 { self.storage }
}
pub fn char4_norm(v:[f32;4])->Normalized<4>{Normalized::from_float(v,[8;4],true)}
pub fn uchar4_norm(v:[f32;4])->Normalized<4>{Normalized::from_float(v,[8;4],false)}
pub fn short2_norm(v:[f32;2])->Normalized<2>{Normalized::from_float(v,[16;2],true)}
pub fn ushort2_norm(v:[f32;2])->Normalized<2>{Normalized::from_float(v,[16;2],false)}
pub fn short4_norm(v:[f32;4])->Normalized<4>{Normalized::from_float(v,[16;4],true)}
pub fn ushort4_norm(v:[f32;4])->Normalized<4>{Normalized::from_float(v,[16;4],false)}
pub fn int1010102_norm(v:[f32;4])->Normalized<4>{Normalized::from_float(v,[10,10,10,2],true)}
pub fn uint1010102_norm(v:[f32;4])->Normalized<4>{Normalized::from_float(v,[10,10,10,2],false)}

/// Thread-local CPU control register guard. Like the pinned C++ implementation,
/// unsupported targets are a no-op, explicitly exposed via `hardware_supported`.
/// WebAssembly checks outputs without claiming to perturb a hardware mode.
pub struct ScopedFlushToZero {
    saved: Option<u32>,
    _not_send: core::marker::PhantomData<std::rc::Rc<()>>,
}
impl ScopedFlushToZero {
    pub const fn hardware_supported() -> bool { cfg!(target_arch="x86_64") }
    pub fn control_word() -> Option<u32> {
        #[cfg(target_arch="x86_64")]
        {
            let mut word = 0_u32;
            // SAFETY: the pointer denotes a live, writable aligned u32; this
            // instruction is available on every x86_64 target.
            unsafe { core::arch::asm!("stmxcsr [{p}]", p=in(reg) &mut word, options(nostack,preserves_flags)); }
            Some(word)
        }
        #[cfg(not(target_arch="x86_64"))]
        { None }
    }
    #[cfg(target_arch="x86_64")]
    fn restore(word: u32) {
        // SAFETY: only an observed MXCSR, with supported FTZ/DAZ bits optionally
        // enabled, reaches this private function. No reserved bits are invented.
        unsafe { core::arch::asm!("ldmxcsr [{p}]", p=in(reg) &word, options(nostack,preserves_flags)); }
    }
    pub fn new() -> Self {
        let saved = Self::control_word();
        #[cfg(target_arch="x86_64")]
        if let Some(word) = saved { Self::restore(word | 0x8040); }
        Self {saved, _not_send: core::marker::PhantomData}
    }
}
impl Default for ScopedFlushToZero {fn default()->Self{Self::new()}}
impl Drop for ScopedFlushToZero {
    fn drop(&mut self) {
        #[cfg(target_arch="x86_64")]
        if let Some(word) = self.saved { Self::restore(word); }
    }
}
