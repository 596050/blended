// SPDX-License-Identifier: GPL-3.0-or-later
//! Typed colour-space and alpha conversions. These are not a full shading system.
use core::marker::PhantomData;
use std::sync::OnceLock;
#[derive(Debug,Clone,Copy,PartialEq)]pub enum Theme{}
#[derive(Debug,Clone,Copy,PartialEq)]pub enum Linear{}
#[derive(Debug,Clone,Copy,PartialEq)]pub enum ByteEncoded{}
#[derive(Debug,Clone,Copy,PartialEq)]pub enum Straight{}
#[derive(Debug,Clone,Copy,PartialEq)]pub enum Premultiplied{}
#[derive(Debug,Clone,Copy,PartialEq)]
pub struct Color<T,S,A>{pub r:T,pub g:T,pub b:T,pub a:T,space:PhantomData<S>,alpha:PhantomData<A>}
impl<T,S,A>Color<T,S,A>{pub const fn new(r:T,g:T,b:T,a:T)->Self{Self{r,g,b,a,space:PhantomData,alpha:PhantomData}}}
pub type ThemeByte=Color<u8,Theme,Straight>;pub type ThemeFloat=Color<f32,Theme,Straight>;
pub type LinearStraight=Color<f32,Linear,Straight>;pub type LinearPremultiplied=Color<f32,Linear,Premultiplied>;
pub type EncodedPremultiplied=Color<u8,ByteEncoded,Premultiplied>;
static SRGB:OnceLock<[f32;256]>=OnceLock::new();
pub fn srgb_to_linear(v:f32)->f32{if v<0.04045{if v<0.0{0.0}else{v*(1.0/12.92)}}else{((v+0.055)*(1.0/1.055)).powf(2.4)}}
pub fn linear_to_srgb(v:f32)->f32{if v<0.0031308{if v<0.0{0.0}else{v*12.92}}else{1.055*v.powf(1.0/2.4)-0.055}}
pub fn init_srgb_conversion(){SRGB.get_or_init(||core::array::from_fn(|i|srgb_to_linear(i as f32/255.0)));}
fn byte(v:f32)->u8{(v*255.0+0.5).clamp(0.0,255.0) as u8}
pub fn to_float(v:ThemeByte)->ThemeFloat{ThemeFloat::new(v.r as f32/255.0,v.g as f32/255.0,v.b as f32/255.0,v.a as f32/255.0)}
pub fn to_byte(v:ThemeFloat)->ThemeByte{ThemeByte::new(byte(v.r),byte(v.g),byte(v.b),byte(v.a))}
pub fn to_scene_linear(v:ThemeByte)->LinearStraight{init_srgb_conversion();let t=SRGB.get().unwrap();LinearStraight::new(t[v.r as usize],t[v.g as usize],t[v.b as usize],v.a as f32/255.0)}
pub fn premultiply_alpha(v:LinearStraight)->LinearPremultiplied{LinearPremultiplied::new(v.r*v.a,v.g*v.a,v.b*v.a,v.a)}
pub fn unpremultiply_alpha(v:LinearPremultiplied)->LinearStraight{if v.a==0.0||v.a==1.0{LinearStraight::new(v.r,v.g,v.b,v.a)}else{let inv=1.0/v.a;LinearStraight::new(v.r*inv,v.g*inv,v.b*inv,v.a)}}
pub fn to_theme4f(v:LinearStraight)->ThemeFloat{ThemeFloat::new(linear_to_srgb(v.r),linear_to_srgb(v.g),linear_to_srgb(v.b),v.a)}
pub fn to_theme4b(v:LinearStraight)->ThemeByte{to_byte(to_theme4f(v))}
pub fn encode(v:LinearPremultiplied)->EncodedPremultiplied{EncodedPremultiplied::new(byte(linear_to_srgb(v.r)),byte(linear_to_srgb(v.g)),byte(linear_to_srgb(v.b)),byte(v.a))}
pub fn decode(v:EncodedPremultiplied)->LinearPremultiplied{LinearPremultiplied::new(srgb_to_linear(v.r as f32/255.0),srgb_to_linear(v.g as f32/255.0),srgb_to_linear(v.b as f32/255.0),v.a as f32/255.0)}
