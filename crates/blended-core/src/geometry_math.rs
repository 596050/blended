// SPDX-FileCopyrightText: 2001-2026 Blender Authors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Geometric maths adapted from Blender 94363991e7dcf39e2d70614aa002ab6f67764a5d.
//! Fixed-size vectors retain f32 arithmetic and the original degenerate branches.
//! Legacy output-buffer entry points remain available beside typed return values.
use std::array::from_fn;
pub type V2=[f32;2]; pub type V3=[f32;3]; pub type V4=[f32;4];
fn add<const N:usize>(a:[f32;N],b:[f32;N])->[f32;N]{from_fn(|i|a[i]+b[i])}
fn sub<const N:usize>(a:[f32;N],b:[f32;N])->[f32;N]{from_fn(|i|a[i]-b[i])}
fn mul<const N:usize>(a:[f32;N],s:f32)->[f32;N]{from_fn(|i|a[i]*s)}
fn dot<const N:usize>(a:[f32;N],b:[f32;N])->f32{let mut r=a[0]*b[0];for i in 1..N{r+=a[i]*b[i];}r}
fn cross(a:V3,b:V3)->V3{[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}
fn length<const N:usize>(v:[f32;N])->f32{dot(v,v).sqrt()}
pub fn normalize<const N:usize>(v:[f32;N])->[f32;N]{let sq=dot(v,v);if sq>1.0e-35{mul(v,1.0/sq.sqrt())}else{[0.0;N]}}
pub fn sqrtf(v:f32)->f32{v.sqrt()}
pub fn cross_tri_v2(a:V2,b:V2,c:V2)->f32{(a[0]-b[0])*(b[1]-c[1])+(a[1]-b[1])*(c[0]-b[0])}
pub fn cross_tri_v3(out:&mut V3,a:V3,b:V3,c:V3){*out=cross(sub(a,b),sub(b,c));}
pub fn cross_poly_v2(p:&[V2],n:usize)->f32{assert!(n<=p.len());if n==0{return 0.0;}let mut cross=0.0;let mut prev=p[n-1];for &cur in &p[..n]{cross+=(prev[0]-cur[0])*(cur[1]+prev[1]);prev=cur;}cross}
pub fn cross_poly_v3(out:&mut V3,p:&[V3],n:usize){assert!(n<=p.len());*out=[0.0;3];if n==0{return;}let mut prev=p[n-1];for &cur in &p[..n]{out[0]+=(prev[1]-cur[1])*(prev[2]+cur[2]);out[1]+=(prev[2]-cur[2])*(prev[0]+cur[0]);out[2]+=(prev[0]-cur[0])*(prev[1]+cur[1]);prev=cur;}}
pub fn area_tri_v2(a:V2,b:V2,c:V2)->f32{(0.5*cross_tri_v2(a,b,c)).abs()}
pub fn area_tri_v3(a:V3,b:V3,c:V3)->f32{length(cross(sub(a,b),sub(b,c)))*0.5}
pub fn area_tri<const N:usize>(a:[f32;N],b:[f32;N],c:[f32;N])->f32{assert!(N==2||N==3);if N==2{area_tri_v2([a[0],a[1]],[b[0],b[1]],[c[0],c[1]])}else{area_tri_v3([a[0],a[1],a[2]],[b[0],b[1],b[2]],[c[0],c[1],c[2]])}}
pub fn area_poly_v2(p:&[V2],n:usize)->f32{(0.5*cross_poly_v2(p,n)).abs()}
pub fn area_poly(p:&[V2])->f32{area_poly_v2(p,p.len())}
pub fn normal_tri(a:V3,b:V3,c:V3)->V3{normalize(cross(sub(a,b),sub(b,c)))}
pub fn normal_quad_v3(out:&mut V3,a:V3,b:V3,c:V3,d:V3)->f32{let n=cross(sub(a,c),sub(b,d));let sq=dot(n,n);*out=normalize(n);if sq>1.0e-35{sq.sqrt()}else{0.0}}
pub fn normal_quad(a:V3,b:V3,c:V3,d:V3)->V3{let mut n=[0.0;3];normal_quad_v3(&mut n,a,b,c,d);n}
pub fn plane_from_point_normal_v3(out:&mut V4,p:V3,n:V3){*out=[n[0],n[1],n[2],-dot(n,p)];}
pub fn plane_from_point_normal(p:V3,n:V3)->V4{let mut plane=[0.0;4];plane_from_point_normal_v3(&mut plane,p,n);plane}
pub fn plane_point_side(plane:V4,p:V3)->f32{plane[0]*p[0]+plane[1]*p[1]+plane[2]*p[2]+plane[3]}
pub fn plane_point_side_v3(plane:V4,p:V3)->f32{plane_point_side(plane,p)}
pub fn line_point_factor<const N:usize>(p:[f32;N],a:[f32;N],b:[f32;N])->f32{let d=sub(b,a);let denom=dot(d,d);if denom==0.0{0.0}else{dot(sub(p,a),d)/denom}}
pub fn line_point_factor_v2(p:V2,a:V2,b:V2)->f32{let d=sub(b,a);let sq=dot(d,d);if sq>0.0{dot(d,sub(p,a))/sq}else{0.0}}
pub fn line_point_factor_v3(p:V3,a:V3,b:V3)->f32{let d=sub(b,a);let sq=dot(d,d);if sq>0.0{dot(d,sub(p,a))/sq}else{0.0}}
fn closest_line<const N:usize>(p:[f32;N],a:[f32;N],b:[f32;N])->[f32;N]{add(a,mul(sub(b,a),line_point_factor(p,a,b)))}
pub fn closest_to_line_segment<const N:usize>(p:[f32;N],a:[f32;N],b:[f32;N])->[f32;N]{let d=sub(b,a);let denom=dot(d,d);if denom==0.0{return a;}let t=dot(sub(p,a),d)/denom;if t<=0.0{return a;}if t>=1.0{return b;}add(a,mul(d,t))}
pub fn closest_to_line_segment_v3(out:&mut V3,p:V3,a:V3,b:V3)->f32{let t=line_point_factor(p,a,b);if t<=0.0{*out=a;0.0}else if t>=1.0{*out=b;1.0}else{*out=add(a,mul(sub(b,a),t));t}}
pub fn dist_squared_to_line<const N:usize>(p:[f32;N],a:[f32;N],b:[f32;N])->f32{let d=sub(closest_line(p,a,b),p);dot(d,d)}
pub fn dist_squared_to_line_v2(p:V2,a:V2,b:V2)->f32{dist_squared_to_line(p,a,b)}
pub fn dist_squared_to_line_v3(p:V3,a:V3,b:V3)->f32{dist_squared_to_line(p,a,b)}
pub fn dist_to_line_v2(p:V2,a:V2,b:V2)->f32{dist_squared_to_line_v2(p,a,b).sqrt()}
pub fn dist_squared_to_line_segment<const N:usize>(p:[f32;N],a:[f32;N],b:[f32;N])->f32{let d=sub(p,closest_to_line_segment(p,a,b));dot(d,d)}
pub fn dist_squared_to_line_segment_v2(p:V2,a:V2,b:V2)->f32{dist_squared_to_line_segment(p,a,b)}
pub fn dist_squared_to_line_segment_v3(p:V3,a:V3,b:V3)->f32{dist_squared_to_line_segment(p,a,b)}
pub fn dist_to_line_segment_v2(p:V2,a:V2,b:V2)->f32{dist_squared_to_line_segment_v2(p,a,b).sqrt()}
pub fn closest_to_plane_normalized(plane:V4,p:V3)->V3{sub(p,mul([plane[0],plane[1],plane[2]],plane_point_side(plane,p)))}
pub fn closest_to_plane_normalized_v3(out:&mut V3,plane:V4,p:V3){*out=closest_to_plane_normalized(plane,p);}
pub fn closest_to_plane(plane:V4,p:V3)->V3{let n=[plane[0],plane[1],plane[2]];sub(p,mul(n,plane_point_side(plane,p)/dot(n,n)))}
pub fn closest_to_plane_v3(out:&mut V3,plane:V4,p:V3){*out=closest_to_plane(plane,p);}
pub fn dist_squared_to_plane(p:V3,plane:V4)->f32{let n=[plane[0],plane[1],plane[2]];let len2=dot(n,n);let f=plane_point_side(plane,p)/len2;len2*(f*f)}
pub fn dist_squared_to_plane_v3(p:V3,plane:V4)->f32{dist_squared_to_plane(p,plane)}
pub fn axis_dominant_to_m3(n:V3)->[V3;3]{
 let f=n[0]*n[0]+n[1]*n[1];
 let (x,y)=if f>f32::EPSILON{let d=1.0/f.sqrt();let x=[n[1]*d,-n[0]*d,0.0];let y=[-n[2]*x[1],n[2]*x[0],n[0]*x[1]-n[1]*x[0]];(x,y)}else{([if n[2]<0.0{-1.0}else{1.0},0.0,0.0],[0.0,1.0,0.0])};
 // Blender stores columns and transposes the basis rows.
 [[x[0],y[0],n[0]],[x[1],y[1],n[1]],[x[2],y[2],n[2]]]
}
pub fn axis_dominant_v3_to_m3(out:&mut [V3;3],n:V3){*out=axis_dominant_to_m3(n);}
pub fn isect_line_line(v1:V3,v2:V3,v3:V3,v4:V3,r1:&mut V3,r2:&mut V3)->i32{
 let a=sub(v2,v1);let b=sub(v4,v3);let c=sub(v3,v1);let ab=cross(a,b);let div=dot(ab,ab);
 if div==0.0{return 0;}let d=dot(c,ab);
 if d.abs()<=0.000001{*r1=add(v1,mul(a,dot(cross(c,b),ab)/div));*r2=*r1;return 1;}
 let mut t=sub(v1,v3);t=mul(ab,dot(t,ab)/dot(ab,ab));
 let v3t=add(v3,t);let v4t=add(v4,t);let c=sub(v3t,v1);let a=sub(v2,v1);let b=sub(v4t,v3t);let ab=cross(a,b);
 *r1=add(v1,mul(a,dot(cross(c,b),ab)/dot(ab,ab)));*r2=sub(*r1,t);2
}
pub fn isect_line_plane(a:V3,b:V3,p:V3,n:V3)->Option<V3>{let u=sub(b,a);let h=sub(a,p);let denom=dot(n,u);if denom.abs()>f32::EPSILON{Some(add(a,mul(u,-dot(n,h)/denom)))}else{None}}
fn side(a:V2,b:V2,p:V2)->f32{(a[0]-p[0])*(b[1]-p[1])-(b[0]-p[0])*(a[1]-p[1])}
fn polygon_orientation(p:V2,poly:&[V2])->i32{let mut plus=true;let mut minus=true;for i in 0..poly.len(){let s=side(poly[i],poly[(i+1)%poly.len()],p);plus&=s>=0.0;minus&=s<=0.0;}if plus{1}else if minus{-1}else{0}}
pub fn isect_point_tri_v2(p:V2,a:V2,b:V2,c:V2)->i32{polygon_orientation(p,&[a,b,c])}
pub fn isect_point_tri(p:V2,a:V2,b:V2,c:V2)->i32{isect_point_tri_v2(p,a,b,c)}
pub fn isect_point_quad_v2(p:V2,a:V2,b:V2,c:V2,d:V2)->i32{polygon_orientation(p,&[a,b,c,d])}
pub fn isect_point_quad(p:V2,a:V2,b:V2,c:V2,d:V2)->i32{isect_point_quad_v2(p,a,b,c,d)}
pub fn isect_point_poly_v2(p:V2,verts:&[V2],n:usize)->bool{assert!(n<=verts.len());if n==0{return false;}let mut hit=false;let mut j=n-1;for i in 0..n{if (verts[i][1]>p[1])!=(verts[j][1]>p[1])&&p[0]<(verts[j][0]-verts[i][0])*(p[1]-verts[i][1])/(verts[j][1]-verts[i][1])+verts[i][0]{hit=!hit;}j=i;}hit}
pub fn isect_point_poly(p:V2,verts:&[V2])->bool{isect_point_poly_v2(p,verts,verts.len())}
pub fn barycentric_weights_v2(a:V2,b:V2,c:V2,p:V2,out:&mut V3){*out=[cross_tri_v2(b,c,p),cross_tri_v2(c,a,p),cross_tri_v2(a,b,p)];let total=out[0]+out[1]+out[2];*out=mul(*out,1.0/total);if !out.iter().all(|v|v.is_finite()){*out=[1.0/3.0;3];}}
pub fn barycentric_weights(a:V2,b:V2,c:V2,p:V2)->V3{let mut w=[0.0;3];barycentric_weights_v2(a,b,c,p,&mut w);w}
fn half_tan(a:V2,b:V2,p:V2)->f64{let a=[a[0] as f64-p[0] as f64,a[1] as f64-p[1] as f64];let b=[b[0] as f64-p[0] as f64,b[1] as f64-p[1] as f64];let area=a[0]*b[1]-a[1]*b[0];if area==0.0{return 0.0;}let d=a[0]*b[0]+a[1]*b[1];let l=(a[0]*a[0]+a[1]*a[1]).sqrt()*(b[0]*b[0]+b[1]*b[1]).sqrt();let r=(l-d)/area;if r.is_finite(){r}else{0.0}}
pub fn interp_weights_poly_v2(w:&mut [f32],verts:&[V2],n:usize,p:V2){
 assert!(n>=3&&n<=verts.len()&&w.len()>=n);let mut maximum=0.0_f32;
 for v in &verts[..n]{maximum=maximum.max((v[0]-p[0]).abs());maximum=maximum.max((v[1]-p[1]).abs());}
 let eps=16.0_f32*f32::EPSILON*maximum;
 let eps2=eps*eps;let mut total=0.0_f32;let mut curr=n-1;let mut previous_half=half_tan(verts[n-2],verts[n-1],p);
 for next in 0..n{
  let a=verts[curr];let b=verts[next];let dx=a[0] as f64-p[0] as f64;let dy=a[1] as f64-p[1] as f64;let len=(dx*dx+dy*dy).sqrt();
  if len<(eps as f64){w[..n].fill(0.0);w[curr]=1.0;return;}
  if dist_squared_to_line_segment_v2(p,a,b)<eps2{w[..n].fill(0.0);let t=line_point_factor_v2(p,a,b).clamp(0.0,1.0);w[curr]=1.0-t;w[next]=t;return;}
  let ht=half_tan(a,b,p);w[curr]=if len==0.0{0.0}else{((previous_half+ht)/len) as f32};total+=w[curr];curr=next;previous_half=ht;
 }
 if total!=0.0{for value in &mut w[..n]{*value/=total;}}
}
pub fn interp_weights_poly(w:&mut [f32],verts:&[V2],p:V2){interp_weights_poly_v2(w,verts,verts.len(),p)}
pub fn interp_bilinear_quad(a:V3,b:V3,c:V3,d:V3,u:f32,v:f32)->V3{let mut r=[0.0;3];interp_bilinear_quad_v3([a,b,c,d],u,v,&mut r);r}
pub fn interp_bilinear_quad_v3(data:[V3;4],u:f32,v:f32,r:&mut V3){*r=mul(data[0],(1.0-u)*(1.0-v));*r=add(*r,mul(data[1],u*(1.0-v)));*r=add(*r,mul(data[2],u*v));*r=add(*r,mul(data[3],(1.0-u)*v));}
pub fn cotangent_tri_weight_v3(a:V3,b:V3,c:V3)->f32{let u=sub(b,a);let v=sub(c,a);let clen=length(cross(u,v));if clen>f32::EPSILON{dot(u,v)/clen}else{0.0}}
pub fn cotangent_tri_weight(a:V3,b:V3,c:V3)->f32{cotangent_tri_weight_v3(a,b,c)}
fn snap(mut u:f32)->f32{if u<0.0{u+=1.0;}let eps=0.25/65536.0;if u<eps{0.0}else if 1.0-eps<u{1.0}else{u}}
pub fn map_to_sphere_out(u:&mut f32,v:&mut f32,x:f32,y:f32,z:f32)->bool{let lenxy=(x*x+y*y).sqrt();let regular=lenxy>z.abs()*(0.25/65536.0);*u=if regular{snap(x.atan2(-y)/(2.0*std::f32::consts::PI))}else{0.5};*v=snap(lenxy.atan2(-z)/std::f32::consts::PI);regular}
pub fn map_to_sphere(p:V3)->V2{let(mut u,mut v)=(0.0,0.0);map_to_sphere_out(&mut u,&mut v,p[0],p[1],p[2]);[u,v]}
pub fn legacy_poly_to_tri_count(polys:i32,corners:i32)->i32{corners-2*polys}
pub fn poly_to_tri_count(polys:i32,corners:i32)->i32{legacy_poly_to_tri_count(polys,corners)}
