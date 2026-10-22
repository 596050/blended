// SPDX-License-Identifier: GPL-3.0-or-later
//! Initial Cycles integer maths compatibility slice. Not a rendering engine.
//! The three upstream tests specify small-value behaviour. Overflow handling
//! below is explicit and is not claimed compatible with undefined C++ domains.
/// Strictly greater power of two, unlike u32::next_power_of_two.
/// Returns zero when a greater power cannot be represented in 32 bits.
pub fn next_power_of_two(value: u32) -> u32 {
    if value == 0 { 1 } else { 1_u32.checked_shl(32-value.leading_zeros()).unwrap_or(0) }
}
/// Strictly smaller power of two, except 0 -> 0 and 1 -> 1.
pub fn prev_power_of_two(value: u32) -> u32 {
    if value <= 1 { value } else { 1_u32 << (31-(value-1).leading_zeros()) }
}
pub fn reverse_integer_bits(value: u32) -> u32 { value.reverse_bits() }
