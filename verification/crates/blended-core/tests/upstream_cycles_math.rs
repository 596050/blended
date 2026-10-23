// SPDX-FileCopyrightText: 2011-2022 Blender Foundation
// SPDX-License-Identifier: Apache-2.0
// Exact input/output cases from cycles/src/test/util_math_test.cpp
// at a456b761034dda42c32eef9f4aae0fa5a5c9f604. No renderer-parity claim.
use blended_core::cycles_math::*;
#[test]
fn next_power_of_two() {
    for (input,expected) in [(0,1),(1,2),(2,4),(3,4),(4,8)] {
        assert_eq!(blended_core::cycles_math::next_power_of_two(input),expected,"input {input}");
    }
}
#[test]
fn prev_power_of_two() {
    for (input,expected) in [(0,0),(1,1),(2,1),(3,2),(4,2),(5,4),(6,4),(7,4),(8,4)] {
        assert_eq!(blended_core::cycles_math::prev_power_of_two(input),expected,"input {input}");
    }
}
#[test]
fn reverse_integer_bits() {
    for (input,expected) in [(0xffffffff,0xffffffff),(0,0),(1,0x80000000),(0x80000000,1),(0xffff0000,0x0000ffff),(0x0000ffff,0xffff0000),(0x00ff0000,0x0000ff00),(0x0000ff00,0x00ff0000),(0xaaaaaaaa,0x55555555)] {
        assert_eq!(blended_core::cycles_math::reverse_integer_bits(input),expected,"input {input:#x}");
    }
}
