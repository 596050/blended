// SPDX-FileCopyrightText: 2024 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Rust adaptation of pinned BLI_math_interp.hh and intern/math_interp.cc.
// CPU sampling is independent of the viewport; no renderer parity is implied.
#![allow(clippy::too_many_arguments)]
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub enum InterpWrapMode { Extend, Repeat, Border }
#[derive(Clone,Copy)]
enum CubicFilter { BSpline, Mitchell }
fn validate<T>(buffer:&[T],w:usize,h:usize,c:usize) {
    assert!(w>0 && h>0 && (1..=4).contains(&c));
    let n=w.checked_mul(h).and_then(|n|n.checked_mul(c)).expect("Image shape overflow");
    assert!(buffer.len()>=n,"Image buffer is shorter than its declared shape");
}
pub fn wrap_coord(u:f32,size:usize,mode:InterpWrapMode)->Option<usize> {
    assert!(size>0 && size<=u32::MAX as usize);
    if u>=0.0 {
        if u<(size as f32) {return Some(u as usize);}
        return match mode {
            InterpWrapMode::Extend=>Some(size-1),
            InterpWrapMode::Border=>None,
            InterpWrapMode::Repeat=>Some((u as u32) as usize%size),
        };
    }
    match mode {
        InterpWrapMode::Extend=>Some(0),
        InterpWrapMode::Border=>None,
        InterpWrapMode::Repeat=>{let x=(-u.floor()) as u32 as usize%size;Some(if x==0 {0}else{size-x})}
    }
}
fn nearest<T:Copy+Default>(buffer:&[T],w:usize,h:usize,u:f32,v:f32)->[T;4] {
    validate(buffer,w,h,4);
    // The pinned nearest-border implementation converts to int (truncates).
    if !u.is_finite() || !v.is_finite(){return [T::default();4];}
    let x=u as i64;let y=v as i64;
    if x<0 || y<0 || x>=w as i64 || y>=h as i64 {return [T::default();4];}
    core::array::from_fn(|c|buffer[(y as usize*w+x as usize)*4+c])
}
pub fn interpolate_nearest_border_byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{nearest(b,w,h,u,v)}
pub fn interpolate_nearest_border_fl(b:&[f32],w:usize,h:usize,u:f32,v:f32)->[f32;4]{nearest(b,w,h,u,v)}
trait Texel:Copy {fn to_float(self)->f32;}
impl Texel for f32 {fn to_float(self)->f32{self}}
impl Texel for u8 {fn to_float(self)->f32{self as f32}}
fn pixel<T:Texel>(b:&[T],w:usize,c:usize,x:Option<usize>,y:Option<usize>,channel:usize)->f32 {
    match (x,y){(Some(x),Some(y))=>b[(y*w+x)*c+channel].to_float(),_=>0.0}
}
fn bilinear<T:Texel>(b:&[T],w:usize,h:usize,c:usize,u:f32,v:f32,xmode:InterpWrapMode,ymode:InterpWrapMode,grouped:bool)->[f32;4] {
    validate(b,w,h,c);
    let x1=wrap_coord(u,w,xmode);let x2=wrap_coord(u+1.0,w,xmode);
    let y1=wrap_coord(v,h,ymode);let y2=wrap_coord(v+1.0,h,ymode);
    let a=u-u.floor();let y=v-v.floor();
    let ab=a*y;let mab=(1.0-a)*y;let amb=a*(1.0-y);let mamb=(1.0-a)*(1.0-y);
    let mut out=[0.0;4];
    for channel in 0..c {
        let p1=mamb*pixel(b,w,c,x1,y1,channel);
        let p2=mab*pixel(b,w,c,x1,y2,channel);
        let p3=amb*pixel(b,w,c,x2,y1,channel);
        let p4=ab*pixel(b,w,c,x2,y2,channel);
        // Preserve the pinned four-lane SSE accumulation order, without FMA.
        out[channel]=if grouped{(p1+p3)+(p2+p4)}else{((p1+p3)+p2)+p4};
    }
    out
}
fn byte4(v:[f32;4])->[u8;4]{v.map(|x|(x+0.5) as u8)}
pub fn interpolate_bilinear_wrapmode_fl(b:&[f32],out:&mut[f32],w:usize,h:usize,c:usize,u:f32,v:f32,x:InterpWrapMode,y:InterpWrapMode){
    assert!(out.len()>=c);out[..c].copy_from_slice(&bilinear(b,w,h,c,u,v,x,y,c==4)[..c]);
}
macro_rules! bilinear_fl {
 ($name:ident,$mode:ident)=>{pub fn $name(b:&[f32],w:usize,h:usize,u:f32,v:f32)->[f32;4]{bilinear(b,w,h,4,u,v,InterpWrapMode::$mode,InterpWrapMode::$mode,true)}};
}
bilinear_fl!(interpolate_bilinear_fl,Extend);
bilinear_fl!(interpolate_bilinear_border_fl,Border);
bilinear_fl!(interpolate_bilinear_wrap_fl,Repeat);
pub fn interpolate_bilinear_byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{byte4(bilinear(b,w,h,4,u,v,InterpWrapMode::Extend,InterpWrapMode::Extend,true))}
pub fn interpolate_bilinear_border_byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{byte4(bilinear(b,w,h,4,u,v,InterpWrapMode::Border,InterpWrapMode::Border,true))}
pub fn interpolate_bilinear_wrap_byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{byte4(bilinear(b,w,h,4,u,v,InterpWrapMode::Repeat,InterpWrapMode::Repeat,false))}
fn coefficients(f:f32,filter:CubicFilter)->[f32;4] {
    let f2=f*f;let f3=f2*f;
    match filter {
        CubicFilter::BSpline=>{
            let w3=f3*(1.0/6.0);
            let w0=-w3+f2*0.5-f*0.5+1.0/6.0;
            let w1=f3*0.5-f2*1.0+2.0/3.0;
            let w2=1.0-w0-w1-w3;
            [w0,w1,w2,w3]
        },
        CubicFilter::Mitchell=>[
            -7.0/18.0*f3+5.0/6.0*f2-0.5*f+1.0/18.0,
            7.0/6.0*f3-2.0*f2+8.0/9.0,
            -7.0/6.0*f3+3.0/2.0*f2+0.5*f+1.0/18.0,
            7.0/18.0*f3-1.0/3.0*f2,
        ],
    }
}
fn cubic<T:Texel>(b:&[T],w:usize,h:usize,c:usize,u:f32,v:f32,xmode:InterpWrapMode,ymode:InterpWrapMode,filter:CubicFilter)->[f32;4] {
    validate(b,w,h,c);
    let wx=coefficients(u-u.floor(),filter);let wy=coefficients(v-v.floor(),filter);
    let mut out=[0.0;4];
    for n in 0..4 {
        let y=wrap_coord(v-1.0+n as f32,h,ymode);
        if y.is_none(){continue;}
        for m in 0..4 {
            let x=wrap_coord(u-1.0+m as f32,w,xmode);
            if x.is_none(){continue;}
            let weight=wx[m]*wy[n];
            for channel in 0..c{out[channel]+=pixel(b,w,c,x,y,channel)*weight;}
        }
    }
    if matches!(filter,CubicFilter::Mitchell){for channel in 0..c{out[channel]=out[channel].max(0.0);}}
    out
}
macro_rules! cubic_functions {
 ($byte:ident,$float:ident,$filter:ident)=>{
 pub fn $byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{byte4(cubic(b,w,h,4,u,v,InterpWrapMode::Extend,InterpWrapMode::Extend,CubicFilter::$filter))}
 pub fn $float(b:&[f32],w:usize,h:usize,u:f32,v:f32)->[f32;4]{cubic(b,w,h,4,u,v,InterpWrapMode::Extend,InterpWrapMode::Extend,CubicFilter::$filter)}
 };
}
cubic_functions!(interpolate_cubic_bspline_byte,interpolate_cubic_bspline_fl,BSpline);
cubic_functions!(interpolate_cubic_mitchell_byte,interpolate_cubic_mitchell_fl,Mitchell);
pub fn interpolate_cubic_bspline_wrapmode_fl(b:&[f32],out:&mut[f32],w:usize,h:usize,c:usize,u:f32,v:f32,x:InterpWrapMode,y:InterpWrapMode){
    assert!(out.len()>=c);out[..c].copy_from_slice(&cubic(b,w,h,c,u,v,x,y,CubicFilter::BSpline)[..c]);
}
