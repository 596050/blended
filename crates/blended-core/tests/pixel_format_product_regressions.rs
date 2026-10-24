// SPDX-License-Identifier: GPL-3.0-or-later
// Supplemental product tests. Not translated upstream Blender test cases.
use blended_core::pixel_formats as m;
#[test]
fn signed_zeros_and_nan_payloads_are_preserved_as_profiled(){
    assert_eq!(m::half_to_float(0x8000).to_bits(),0x80000000);
    assert_eq!(m::float_to_half(f32::from_bits(0x80000000)),0x8000);
    assert_eq!(m::float_to_half_make_finite(f32::from_bits(0xff800001)),0x8000);
    assert_eq!(m::half_to_float(0x7c01).to_bits(),0x7f802000);
    let input=[f32::from_bits(0x7f812000);5];let mut output=[0;6];
    m::float_to_half_array(&input,&mut output,5);
    assert_eq!(output,[0x7e09,0x7e09,0x7e09,0x7e09,0x7e00,0]);
}
#[test]
fn half_midpoints_round_to_even_including_subnormals(){
    assert_eq!(m::float_to_half(f32::from_bits(0x3f801000)),0x3c00);
    assert_eq!(m::float_to_half(f32::from_bits(0x3f803000)),0x3c02);
    assert_eq!(m::float_to_half(2_f32.powi(-25)),0);
    assert_eq!(m::float_to_half(3.0*2_f32.powi(-25)),2);
    assert_eq!(m::float_to_half(65520.0),0x7c00);
}
#[test]
fn zero_length_conversion_and_tails_keep_sentinels(){
    let mut f=[f32::from_bits(0x41234567);8];let original=f;
    m::half_to_float_array(&[],&mut f,0);assert_eq!(f,original);
    m::half_to_float_array(&[1,2,3],&mut f,3);assert_eq!(&f[3..],&original[3..]);
    let mut h=[0xa55a;8];m::float_to_half_array(&[1.0],&mut h,1);assert_eq!(h[0],0x3c00);assert!(h[1..].iter().all(|&v|v==0xa55a));
}
#[test]
fn clamp_nan_prefix_and_tail_retain_pinned_difference(){
    let input=[f32::from_bits(0x7f800001);5];let mut output=[0;5];
    m::float_to_half_clamp_array(&input,&mut output,5,1.0,2.0);
    assert_eq!(output,[0x3c00,0x3c00,0x3c00,0x3c00,0]);
    m::float_to_half_clamp_array(&input,&mut output,5,-2.0,-1.0);
    assert_eq!(output,[0xbc00,0xbc00,0xbc00,0xbc00,0]);
}
#[test]
fn normalised_values_truncate_and_raw_minimum_is_not_silently_clamped(){
    assert_eq!(m::char4_norm([0.5,-0.5,2.0,-2.0]).integers(),[63,-63,127,-127]);
    assert_eq!(m::uchar4_norm([0.5,-0.5,2.0,-2.0]).integers(),[127,0,255,0]);
    let signed=m::Normalized::<2>::from_bits(0x7fff8000,[16,16],true);
    assert_eq!(signed.integers(),[-32768,32767]);assert_eq!(signed.to_float(),[-32768.0_f32/32767.0_f32,1.0]);
}
#[test]
fn packed_ten_bit_formats_keep_two_bit_alpha_distinct(){
    let x=m::int1010102_norm([0.5,-0.5,1.0,-1.0]);
    assert_eq!(x.integers(),[255,-255,511,-1]);
    assert_eq!((x.packed_bits()>>30)&3,3);
    assert_eq!(m::uint1010102_norm([0.5,0.0,1.0,0.5]).integers(),[511,0,1023,1]);
}
#[test]
fn scoped_fp_mode_is_real_on_native_and_restored_exactly(){
    let before=m::ScopedFlushToZero::control_word();
    assert_eq!(before.is_some(),m::ScopedFlushToZero::hardware_supported());
    {let _guard=m::ScopedFlushToZero::new();
     if let Some(word)=m::ScopedFlushToZero::control_word(){assert_eq!(word&0x8040,0x8040);}
     let during=m::ScopedFlushToZero::control_word();
     {let _nested=m::ScopedFlushToZero::new();}
     assert_eq!(m::ScopedFlushToZero::control_word(),during);
    }
    assert_eq!(m::ScopedFlushToZero::control_word(),before);
}
