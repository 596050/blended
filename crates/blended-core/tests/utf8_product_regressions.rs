// SPDX-License-Identifier: GPL-3.0-or-later
// Additional product/safety tests, not translated upstream Blender cases.
use blended_core::utf8_compat as u;
#[test]
fn legacy_decoder_and_validator_are_distinct_operations(){
    let bytes=[0xc0,0x80];let mut offset=0;
    assert_eq!(u::decode_step_safe(&bytes,2,&mut offset),0);assert_eq!(offset,2);
    assert_eq!(u::invalid_byte(&bytes,2),0);
    let bytes=[0xfc,0x84,0x80,0x80,0x80,0x80];offset=0;
    assert_eq!(u::invalid_byte(&bytes,6),-1);
    assert_eq!(u::decode_step_safe(&bytes,6,&mut offset),0x04000000);assert_eq!(offset,6);
}
#[test]
fn truncated_decoder_advances_one_unsigned_byte(){
    let bytes=[0xe2,0x82];let mut offset=0;
    assert_eq!(u::decode_step_safe(&bytes,2,&mut offset),0xe2);assert_eq!(offset,1);
    assert_eq!(u::decode_step_safe(&bytes,2,&mut offset),0x82);assert_eq!(offset,2);
}
#[test]
fn copying_partial_codepoint_keeps_unused_sentinels(){
    let mut dst=[0xee;4];assert_eq!(u::copy_into(&mut dst,b"\xc3\xa9\0",2),0);
    assert_eq!(dst,[0,0xee,0xee,0xee]);
}
#[test]
fn small_random_byte_blocks_do_not_advance_the_pinned_state(){
    let mut rng=u::LegacyByteRng::new(1);let mut a=[0;6];let mut b=[0;6];rng.fill(&mut a);rng.fill(&mut b);assert_eq!(a,b);
    let mut c=[0;7];rng.fill(&mut c);assert_eq!(&c[..6],&a);rng.fill(&mut b);assert_ne!(a,b);
}
#[test]
fn cursor_groups_combining_bytes_without_splitting_them(){
    let text=b"A\xcc\x80B\0";let mut pos=0;
    assert!(u::cursor_next8(text,4,&mut pos));assert_eq!(pos,3);
    assert!(u::cursor_next8(text,4,&mut pos));assert_eq!(pos,4);
    assert!(u::cursor_prev8(text,4,&mut pos));assert_eq!(pos,3);
    assert!(u::cursor_prev8(text,4,&mut pos));assert_eq!(pos,0);
}
#[test]
fn malformed_prefix_has_an_explicit_safe_boundary_policy(){
    // Safety adapter policy, not claimed equivalence to an out-of-buffer native pointer.
    let text=[0x80,0x80,0];let mut pos=2;
    assert!(u::cursor_prev8(&text,2,&mut pos));assert_eq!(pos,0);
}
