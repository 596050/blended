// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Complete runtime assertion bodies from BLI_math_vector_test.cc at
// 94363991e7dcf39e2d70614aa002ab6f67764a5d, with explicit Rust array adapters.
// The separate signed-zero hash static_assert is still NOT ported.
use crate::math::*;
#[derive(Debug,Default)]
pub struct Report { pub assertions:u32, pub failures:Vec<String> }
impl Report {
    fn check(&mut self,ok:bool,label:&str) {self.assertions+=1;if !ok {self.failures.push(label.into());}}
    pub fn passed(&self)->bool {self.assertions>0&&self.failures.is_empty()}
}
fn float_eq(a:f32,b:f32)->bool {
    if a.is_nan()||b.is_nan() {return false;}
    fn ordered(x:f32)->u32 {let b=x.to_bits();if b&0x80000000!=0 {(!b).wrapping_add(1)}else{b|0x80000000}}
    ordered(a).abs_diff(ordered(b))<=4
}
fn floats<const N:usize>(r:&mut Report,a:[f32;N],b:[f32;N]) {
    for i in 0..N {r.check(float_eq(a[i],b[i]),"EXPECT_FLOAT_EQ component");}
}
fn near(r:&mut Report,a:[f32;3],b:[f32;3]) {
    for i in 0..3 {r.check((f64::from(a[i])-f64::from(b[i])).abs()<=f64::from(1e-6_f32),"EXPECT_NEAR component");}
}
fn clamp_vec_with_floats()->Report {
    let mut r=Report::default();
    let mut a=[-1.0,-1.0];clamp_f32(&mut a,0.0,1.0);floats(&mut r,[0.0,0.0],a);
    let mut b=[0.5,0.5];clamp_f32(&mut b,0.0,1.0);floats(&mut r,[0.5,0.5],b);
    let mut c=[2.0,2.0];clamp_f32(&mut c,0.0,1.0);floats(&mut r,[1.0,1.0],c);r
}
fn test_invert_v3_safe()->Report {
    let mut r=Report::default();
    floats(&mut r,[0.0,0.5,0.33333333333_f32],safe_rcp3([0.0,2.0,3.0]));
    floats(&mut r,rcp3([1.0,2.0,3.0]),safe_rcp3([1.0,2.0,3.0]));r
}
fn clamp()->Report {
    let mut r=Report::default();let a=clamp_i32([0,100,-100],[5,40,-95],[7,45,5]);
    r.check(a[0]==5,"result.x == 5");r.check(a[1]==45,"result.y == 45");r.check(a[2]==-95,"result.z == -95");
    let b=clamp_i32([0,100,-100],[-50;3],[50;3]);
    r.check(b[0]==0,"result_2.x == 0");r.check(b[1]==50,"result_2.y == 50");r.check(b[2]==-50,"result_2.z == -50");r
}
fn min_list()->Report {
    let mut r=Report::default();let inf=f32::INFINITY;
    r.check(min3(&[[1.0,2.0,3.0]])==Some([1.0,2.0,3.0]),"single vector min");
    r.check(min3(&[[1.0,2.0,3.0],[0.0,5.0,2.0]])==Some([0.0,2.0,2.0]),"two vector min");
    r.check(min3(&[[1.0,2.0,3.0],[0.0,5.0,2.0],[2.0,4.0,1.5]])==Some([0.0,2.0,1.5]),"three vector min");
    r.check(min3(&[[inf,2.0,3.0],[0.0,-inf,inf],[2.0,4.0,-inf]])==Some([0.0,-inf,-inf]),"infinite vector min");
    let value=min3(&[[f32::NAN,2.0,3.0],[0.0,f32::NAN,2.0],[2.0,4.0,f32::NAN]]).expect("nonempty input");
    r.check(value[0].is_nan(),"isnan(result.x)");r.check(value[1]==2.0,"result.y == 2.0");r.check(value[2]==2.0,"result.z == 2.0");r
}
fn max_list()->Report {
    let mut r=Report::default();let inf=f32::INFINITY;
    r.check(max3(&[[1.0,2.0,3.0]])==Some([1.0,2.0,3.0]),"single vector max");
    r.check(max3(&[[1.0,2.0,3.0],[0.0,5.0,2.0]])==Some([1.0,5.0,3.0]),"two vector max");
    r.check(max3(&[[1.0,2.0,3.0],[0.0,5.0,2.0],[2.0,4.0,1.5]])==Some([2.0,5.0,3.0]),"three vector max");
    r.check(max3(&[[inf,2.0,3.0],[0.0,-inf,inf],[2.0,4.0,-inf]])==Some([inf,4.0,inf]),"infinite vector max");
    let value=max3(&[[f32::NAN,2.0,3.0],[0.0,f32::NAN,2.0],[2.0,4.0,f32::NAN]]).expect("nonempty input");
    r.check(value[0].is_nan(),"isnan(result.x)");r.check(value[1]==4.0,"result.y == 4.0");r.check(value[2]==3.0,"result.z == 3.0");r
}
fn interpolate_int()->Report {
    let mut r=Report::default();let a=lerp_i32([0,-100,50],[0,100,100],0.75);
    r.check(a[0]==0,"result.x == 0");r.check(a[1]==50,"result.y == 50");r.check(a[2]==87,"result.z == 87");r
}
fn interpolate_float()->Report {
    let mut r=Report::default();floats(&mut r,lerp_f32([40.0,-100.0,50.0],[20.0,100.0,100.0],0.5),[30.0,0.0,75.0]);r
}
fn ceil_to_multiple()->Report {
    let mut r=Report::default();let a=ceil_multiple3([21,16,0],[8,16,15]).expect("positive divisor");
    // Upstream uses EXPECT_FLOAT_EQ even though the result is an integer vector.
    floats(&mut r,a.map(|v|v as f32),[24.0,16.0,0.0]);r
}
fn divide_ceil()->Report {
    let mut r=Report::default();let a=divide_ceil3([21,16,0],[8,16,15]).expect("positive divisor");
    floats(&mut r,a.map(|v|v as f32),[3.0,1.0,0.0]);r
}
fn sign()->Report {let mut r=Report::default();floats(&mut r,sign3([-21,16,0]).map(|v|v as f32),[-1.0,1.0,0.0]);r}
fn sqrt()->Report {let mut r=Report::default();near(&mut r,sqrt3([1.0,4.0,9.0]),[1.0,2.0,3.0]);r}
fn safe_sqrt()->Report {let mut r=Report::default();near(&mut r,safe_sqrt3([1.0,-4.0,9.0]),[1.0,0.0,3.0]);r}
fn rcp()->Report {let mut r=Report::default();near(&mut r,rcp3([1.0,2.0,4.0]),[1.0,0.5,0.25]);r}
fn safe_rcp()->Report {let mut r=Report::default();near(&mut r,safe_rcp3([1.0,0.0,4.0]),[1.0,0.0,0.25]);r}
fn exp()->Report {let mut r=Report::default();near(&mut r,exp3([1.0,2.0,3.0]),[2.718281828459045_f32,7.38905609893065_f32,20.085536923187668_f32]);r}
fn log()->Report {let mut r=Report::default();near(&mut r,log3([1.0,2.0,3.0]),[0.0,0.69314718056_f32,1.09861228867_f32]);r}
fn square()->Report {let mut r=Report::default();near(&mut r,square3([1.0,2.0,3.0]),[1.0,4.0,9.0]);r}
pub const ASSERTION_COUNTS:[u32;17]=[6,6,6,7,7,3,3,3,3,3,3,3,3,3,3,3,3];
pub const REPORTS:[fn()->Report;17]=[clamp_vec_with_floats,test_invert_v3_safe,clamp,min_list,max_list,interpolate_int,interpolate_float,ceil_to_multiple,divide_ceil,sign,sqrt,safe_sqrt,rcp,safe_rcp,exp,log,square];
type Case=(&'static str,fn()->bool);
pub const CASES:[Case;17]=[
("math_vector.ClampVecWithFloats",||clamp_vec_with_floats().passed()),
("math_vector.test_invert_v3_safe",||test_invert_v3_safe().passed()),
("math_vector.Clamp",||clamp().passed()),
("math_vector.MinList",||min_list().passed()),
("math_vector.MaxList",||max_list().passed()),
("math_vector.InterpolateInt",||interpolate_int().passed()),
("math_vector.InterpolateFloat",||interpolate_float().passed()),
("math_vector.CeilToMultiple",||ceil_to_multiple().passed()),
("math_vector.DivideCeil",||divide_ceil().passed()),
("math_vector.Sign",||sign().passed()),
("math_vector.sqrt",||sqrt().passed()),
("math_vector.safe_sqrt",||safe_sqrt().passed()),
("math_vector.rcp",||rcp().passed()),
("math_vector.safe_rcp",||safe_rcp().passed()),
("math_vector.exp",||exp().passed()),
("math_vector.log",||log().passed()),
("math_vector.square",||square().passed()),
];
