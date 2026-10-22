// SPDX-FileCopyrightText: 2021-2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Rust adaptations of blenlib at 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Safe slice boundaries are additional preconditions, not full parity claims.
pub fn ulp_diff_ff(a:f32,b:f32)->u32 {
    let aa=a.to_bits()&0x7fff_ffff;let bb=b.to_bits()&0x7fff_ffff;
    if aa>0x7f80_0000 || bb>0x7f80_0000 {return u32::MAX;}
    if (a.to_bits()^b.to_bits())&0x8000_0000==0 {aa.abs_diff(bb)} else {aa+bb}
}
pub fn compare_ff_relative(a:f32,b:f32,max_diff:f32,max_ulps:i32)->bool {
    debug_assert!((0..(1<<22)).contains(&max_ulps));
    (a-b).abs()<=max_diff || ulp_diff_ff(a,b)<=max_ulps as u32
}
pub fn log2_floor_u(x:u32)->u32 {if x<=1 {0} else {31-x.leading_zeros()}}
pub fn log2_ceil_u(x:u32)->u32 {if x<=1 {0} else {32-(x-1).leading_zeros()}}
pub fn ceil_power_of_10(x:f32)->f32 {if x==0.0 {0.0} else {1.0/10.0_f32.powf((1.0/x).log10().floor())}}
pub fn floor_power_of_10(x:f32)->f32 {if x==0.0 {0.0} else {1.0/10.0_f32.powf((1.0/x).log10().ceil())}}
pub fn min_f32(a:f32,b:f32)->f32 {if b<a {b} else {a}}
pub fn clamp_i32(x:i32,lo:i32,hi:i32)->i32 {x.max(lo).min(hi)}
pub fn step(edge:f32,value:f32)->f32 {if value<edge {0.0} else {1.0}}
pub fn midpoint(a:f32,b:f32)->f32 {(a+b)*0.5}
pub fn interpolate_i32(a:i32,b:i32,t:f32)->i32 {(a as f32*(1.0-t)+b as f32*t).round() as i32}
pub fn floored_fmod(a:f32,b:f32)->f32 {a-b*(a/b).floor()}
pub fn mod_periodic_f32(a:f32,b:f32)->f32 {debug_assert!(b!=0.0);floored_fmod(a,b)}
pub fn mod_periodic_i32(a:i32,b:i32)->i32 {assert!(b>0);a.rem_euclid(b)}
pub fn mod_periodic_i64(a:i64,b:i64)->i64 {assert!(b>0);a.rem_euclid(b)}
pub fn safe_powf(a:f32,b:f32)->f32 {if a<0.0 && b!=b.trunc() {0.0} else {a.powf(b)}}
pub fn safe_modf(a:f32,b:f32)->f32 {if b==0.0 {0.0} else {a%b}}
pub fn safe_logf(a:f32,b:f32)->f32 {
    if a<=0.0 || b<=0.0 {return 0.0;}
    let den=b.ln();if den==0.0 {0.0} else {a.ln()/den}
}
pub fn bitscan_reverse_clear_uint(a:&mut u32)->u32 {
    assert!(*a!=0,"bitscan requires a nonzero input");
    let index=a.leading_zeros();*a &= !(0x80000000u32 >> index);index
}
pub fn count_bits_i(x:i32)->u32 {(x as u32).count_ones()}
pub fn count_bits_uint64(x:u64)->u32 {x.count_ones()}
pub fn tridiagonal_solve(a:&[f32],b:&[f32],c:&[f32],d:&[f32],out:&mut[f32],n:usize)->bool {
    if n==0 || [a.len(),b.len(),c.len(),d.len(),out.len()].into_iter().any(|s|s<n) {return false;}
    let mut cp=vec![0.0f64;n];let mut dp=vec![0.0f64;n];
    cp[0]=c[0] as f64/b[0] as f64;dp[0]=d[0] as f64/b[0] as f64;
    for i in 1..n {
        let den=b[i] as f64-a[i] as f64*cp[i-1];
        cp[i]=c[i] as f64/den;dp[i]=(d[i] as f64-a[i] as f64*dp[i-1])/den;
    }
    let mut previous=dp[n-1];out[n-1]=previous as f32;
    for i in (0..n-1).rev() {previous=dp[i]-cp[i]*previous;out[i]=previous as f32;}
    previous.is_finite()
}
pub fn tridiagonal_solve_cyclic(a:&[f32],b:&[f32],c:&[f32],d:&[f32],out:&mut[f32],n:usize)->bool {
    if n==0 || [a.len(),b.len(),c.len(),d.len(),out.len()].into_iter().any(|s|s<n) {return false;}
    if n==1 {out[0]=d[0]/(a[0]+b[0]+c[0]);return out[0].is_finite();}
    if n==2 {return tridiagonal_solve(&[0.0,a[1]+c[1]],b,&[a[0]+c[0],0.0],d,out,n);}
    let (a0,cn)=(a[0],c[n-1]);
    if a0==0.0 && cn==0.0 {return tridiagonal_solve(a,b,c,d,out,n);}
    let mut diagonal=b[..n].to_vec();diagonal[0]-=a0;diagonal[n-1]-=cn;
    let mut rhs=vec![0.0;n];rhs[0]=a0;rhs[n-1]=cn;
    let mut tmp=vec![0.0;n];
    if !tridiagonal_solve(a,&diagonal,c,&rhs,&mut tmp,n) || !tridiagonal_solve(a,&diagonal,c,d,out,n) {return false;}
    let coeff=(out[0]+out[n-1])/(1.0+tmp[0]+tmp[n-1]);
    for i in 0..n {out[i]-=coeff*tmp[i];}true
}
/// Mirrors optional output pointers with a mask. Omitted fields are NaN.
pub fn seconds_decompose(mut seconds:f64,fields:[bool;5])->[f64;5] {
    assert!(fields.iter().any(|&x|x));let mut out=[f64::NAN;5];
    for i in 0..4 {
        if fields[i] {let unit=[86400.0,3600.0,60.0,1.0][i];let value=seconds/unit;out[i]=value.trunc();seconds=value.fract()*unit;}
    }
    if fields[4] {out[4]=seconds/0.001;}
    else if fields[3] {out[3]+=seconds;}
    else if fields[2] {out[2]+=seconds/60.0;}
    else if fields[1] {out[1]+=seconds/3600.0;}
    else if fields[0] {out[0]=seconds/86400.0;}
    out
}
