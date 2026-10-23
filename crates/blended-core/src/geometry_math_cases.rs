// SPDX-FileCopyrightText: 2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from unmodified, hash-locked original test bodies.
#![allow(non_snake_case,unused_mut,unused_parens,unused_assignments)]
use crate::geometry_math::*;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! numeq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a as f64)==($b as f64),stringify!($a == $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check((($a as f64)-($b as f64)).abs()<=($e as f64),stringify!($a ~= $b within $e),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! fatal_yes {($r:expr,$a:expr)=>{{let p=$a;$r.check(p,stringify!($a),line!());if !p{return $r;}}};}

// source/blender/blenlib/tests/BLI_math_geom_test.cc:12
pub fn math_geom__DistToLine2DSimple()->Report{let mut report=Report::default();
let mut p = [(5.0_f32) as f32, (1.0_f32) as f32];
let mut a = [(0.0_f32) as f32, (0.0_f32) as f32];
let mut b = [(2.0_f32) as f32, (0.0_f32) as f32];
let mut distance:f32 = dist_to_line_v2(p, a, b);
  near!(report, 1.0_f32, distance, 1e-6);

report
}

// source/blender/blenlib/tests/BLI_math_geom_test.cc:19
pub fn math_geom__DistToLineSegment2DSimple()->Report{let mut report=Report::default();
let mut p = [(3.0_f32) as f32, (1.0_f32) as f32];
let mut a = [(0.0_f32) as f32, (0.0_f32) as f32];
let mut b = [(2.0_f32) as f32, (0.0_f32) as f32];
let mut distance:f32 = dist_to_line_segment_v2(p, a, b);
  near!(report, sqrtf(2.0_f32), distance, 1e-6);

report
}

// source/blender/blenlib/tests/BLI_math_geom_test.cc:26
pub fn math_geom__IsectPointTri2D()->Report{let mut report=Report::default();
let mut tri_cw = [[(-2) as f32, (1) as f32], [(4) as f32, (4) as f32], [(2) as f32, (-3) as f32]];
let mut tri_ccw = [[(-2) as f32, (1) as f32], [(2) as f32, (-3) as f32], [(4) as f32, (4) as f32]];
let mut inside1 = [(0) as f32, (0) as f32];
let mut inside2 = [(2) as f32, (2) as f32];
let mut inside3 = [(2) as f32, (-1) as f32];
let mut inside4 = [(-1) as f32, (1) as f32];
  numeq!(report, -1, isect_point_tri_v2(inside1, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(inside1, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, -1, isect_point_tri_v2(inside2, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(inside2, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, -1, isect_point_tri_v2(inside3, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(inside3, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, -1, isect_point_tri_v2(inside4, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(inside4, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
let mut outside1 = [(2) as f32, (4) as f32];
let mut outside2 = [(-1) as f32, (-1) as f32];
let mut outside3 = [(0) as f32, (3) as f32];
let mut outside4 = [(-4) as f32, (0) as f32];
  numeq!(report, 0, isect_point_tri_v2(outside1, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside1, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside2, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside2, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside3, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside3, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside4, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 0, isect_point_tri_v2(outside4, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
let mut edge1 = [(0) as f32, (2) as f32];
let mut edge2 = [(1) as f32, (-2) as f32];
  numeq!(report, -1, isect_point_tri_v2(edge1, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(edge1, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, -1, isect_point_tri_v2(edge2, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(edge2, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
let mut corner1 = [(4) as f32, (4) as f32];
let mut corner2 = [(2) as f32, (-3) as f32];
  numeq!(report, -1, isect_point_tri_v2(corner1, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(corner1, tri_ccw[0], tri_ccw[1], tri_ccw[2]));
  numeq!(report, -1, isect_point_tri_v2(corner2, tri_cw[0], tri_cw[1], tri_cw[2]));
  numeq!(report, 1, isect_point_tri_v2(corner2, tri_ccw[0], tri_ccw[1], tri_ccw[2]));

report
}

// source/blender/blenlib/tests/BLI_math_geom_test.cc:72
pub fn math_geom__IsectPointQuad2D()->Report{let mut report=Report::default();
let mut quad_cw = [[(-2) as f32, (1) as f32], [(4) as f32, (4) as f32], [(5) as f32, (1) as f32], [(2) as f32, (-3) as f32]];
let mut quad_ccw = [[(-2) as f32, (1) as f32], [(2) as f32, (-3) as f32], [(5) as f32, (1) as f32], [(4) as f32, (4) as f32]];
let mut inside1 = [(0) as f32, (0) as f32];
let mut inside2 = [(2) as f32, (2) as f32];
let mut inside3 = [(3) as f32, (-1) as f32];
let mut inside4 = [(-1) as f32, (1) as f32];
  numeq!(report, -1, isect_point_quad_v2(inside1, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(inside1, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, -1, isect_point_quad_v2(inside2, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(inside2, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, -1, isect_point_quad_v2(inside3, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(inside3, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, -1, isect_point_quad_v2(inside4, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(inside4, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
let mut outside1 = [(2) as f32, (4) as f32];
let mut outside2 = [(-1) as f32, (-1) as f32];
let mut outside3 = [(0) as f32, (3) as f32];
let mut outside4 = [(-4) as f32, (0) as f32];
  numeq!(report, 0, isect_point_quad_v2(outside1, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside1, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside2, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside2, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside3, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside3, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside4, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 0, isect_point_quad_v2(outside4, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
let mut edge1 = [(0) as f32, (2) as f32];
let mut edge2 = [(1) as f32, (-2) as f32];
  numeq!(report, -1, isect_point_quad_v2(edge1, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(edge1, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, -1, isect_point_quad_v2(edge2, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(edge2, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
let mut corner1 = [(4) as f32, (4) as f32];
let mut corner2 = [(2) as f32, (-3) as f32];
  numeq!(report, -1, isect_point_quad_v2(corner1, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(corner1, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));
  numeq!(report, -1, isect_point_quad_v2(corner2, quad_cw[0], quad_cw[1], quad_cw[2], quad_cw[3]));
  numeq!(report, 1, isect_point_quad_v2(corner2, quad_ccw[0], quad_ccw[1], quad_ccw[2], quad_ccw[3]));

report
}

// source/blender/blenlib/tests/BLI_math_geom_test.cc:118
pub fn math_geom__CrossPoly()->Report{let mut report=Report::default();
let mut tri_cw_2d = [[(-1) as f32, (0) as f32], [(0) as f32, (1) as f32], [(1) as f32, (0) as f32]];
let mut tri_cw_3d = [[(-1) as f32, (0) as f32, 0.0_f32], [(0) as f32, (1) as f32, 0.0_f32], [(1) as f32, (0) as f32, 0.0_f32]];
let mut tri_ccw_2d = [[(1) as f32, (0) as f32], [(0) as f32, (1) as f32], [(-1) as f32, (0) as f32]];
let mut tri_ccw_3d = [[(1) as f32, (0) as f32, 0.0_f32], [(0) as f32, (1) as f32, 0.0_f32], [(-1) as f32, (0) as f32, 0.0_f32]];

  let cross_tri_v3_as_vec3 = |poly:[[f32;3];3]| -> [f32;3] {
let mut n = [0.0_f32;3];
cross_tri_v3(&mut n, poly[0], poly[1], poly[2]);
    return [(n[0]) as f32, (n[1]) as f32, (n[2]) as f32];
  };

  let cross_poly_v3_as_vec3 = |poly:[[f32;3];3]| -> [f32;3] {
let mut n = [0.0_f32;3];
cross_poly_v3(&mut n, &poly, 3);
    return [(n[0]) as f32, (n[1]) as f32, (n[2]) as f32];
  };

                  
  numeq!(report, cross_tri_v3_as_vec3(tri_cw_3d)[2], -2);
  numeq!(report, cross_tri_v2(tri_cw_2d[0], tri_cw_2d[1], tri_cw_2d[2]), -2);

  numeq!(report, cross_poly_v3_as_vec3(tri_cw_3d)[2], -2);
  numeq!(report, cross_poly_v2(&tri_cw_2d, 3), -2);

                          
  numeq!(report, cross_tri_v3_as_vec3(tri_ccw_3d)[2], 2);
  numeq!(report, cross_tri_v2(tri_ccw_2d[0], tri_ccw_2d[1], tri_ccw_2d[2]), 2);

  numeq!(report, cross_poly_v3_as_vec3(tri_ccw_3d)[2], 2);
  numeq!(report, cross_poly_v2(&tri_ccw_2d, 3), 2);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:26
pub fn math_geom_hh__NormalQuad()->Report{let mut report=Report::default();
let mut v1 = [(0) as f32, (0) as f32, (0) as f32];
let mut v2 = [(1) as f32, (0) as f32, (0) as f32];
let mut v3 = [(1) as f32, (1) as f32, (0) as f32];
let mut v4 = [(0) as f32, (1) as f32, (0) as f32];
let mut c_n = [0.0_f32;3];
normal_quad_v3(&mut c_n, v1, v2, v3, v4);
let mut n = normal_quad(v1, v2, v3, v4);
  near!(report, c_n[0], n[0], 1e-6_f32);
  near!(report, c_n[1], n[1], 1e-6_f32);
  near!(report, c_n[2], n[2], 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:39
pub fn math_geom_hh__AreaTri()->Report{let mut report=Report::default();
let mut v1 = [(0) as f32, (0) as f32, (0) as f32];
let mut v2 = [(1) as f32, (0) as f32, (0) as f32];
let mut v3 = [(0) as f32, (1) as f32, (0) as f32];
  near!(report, 0.5_f32, area_tri(v1, v2, v3), 1e-6_f32);

                               
  near!(report, area_tri_v3(v1, v2, v3), area_tri(v1, v2, v3), 1e-6_f32);
let mut degen = [(1) as f32, (2) as f32, (3) as f32];
  near!(report, 0.0_f32, area_tri(degen, degen, degen), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:53
pub fn math_geom_hh__CotangentTriWeight()->Report{let mut report=Report::default();
let mut sq3:f32 = sqrtf(3.0_f32);
let mut v1 = [(0) as f32, (0) as f32, (0) as f32];
let mut v2 = [(1) as f32, (0) as f32, (0) as f32];
let mut v3 = [(0.5_f32) as f32, (sq3 * 0.5_f32) as f32, (0) as f32];
  near!(report, cotangent_tri_weight_v3(v1, v2, v3), cotangent_tri_weight(v1, v2, v3), 1e-5_f32);
let mut degen = [(1) as f32, (0) as f32, (0) as f32];
  near!(report, 0.0_f32, cotangent_tri_weight(degen, degen, degen), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:72
pub fn math_geom_hh__PlaneFromPointNormal()->Report{let mut report=Report::default();
let mut co = [(1) as f32, (2) as f32, (3) as f32];
let mut no = [(0) as f32, (0) as f32, (1) as f32];
let mut c_plane = [0.0_f32;4];
plane_from_point_normal_v3(&mut c_plane, co, no);
let mut plane = plane_from_point_normal(co, no);
  near!(report, c_plane[0], plane[0], 1e-6_f32);
  near!(report, c_plane[1], plane[1], 1e-6_f32);
  near!(report, c_plane[2], plane[2], 1e-6_f32);
  near!(report, c_plane[3], plane[3], 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:86
pub fn math_geom_hh__PlanePointSide()->Report{let mut report=Report::default();
let mut plane = [(0) as f32, (0) as f32, (1) as f32, (0) as f32];
  near!(report, 1.0_f32, plane_point_side(plane, [(0) as f32, (0) as f32, (1) as f32]), 1e-6_f32);
  near!(report, -1.0_f32, plane_point_side(plane, [(0) as f32, (0) as f32, (-1) as f32]), 1e-6_f32);
  near!(report, 0.0_f32, plane_point_side(plane, [(5) as f32, (7) as f32, (0) as f32]), 1e-6_f32);
let mut pt = [(1) as f32, (2) as f32, (3) as f32];
let mut c_plane = [(plane[0]) as f32, (plane[1]) as f32, (plane[2]) as f32, (plane[3]) as f32];
  near!(report, plane_point_side_v3(c_plane, pt), plane_point_side(plane, pt), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:106
pub fn math_geom_hh__DistSquaredToLineSegment2D()->Report{let mut report=Report::default();
let mut p = [(3) as f32, (1) as f32];
let mut l1 = [(0) as f32, (0) as f32];
let mut l2 = [(2) as f32, (0) as f32];
  near!(report, dist_squared_to_line_segment_v2(p, l1, l2), dist_squared_to_line_segment(p, l1, l2), 1e-6_f32);
let mut p2 = [(1) as f32, (2) as f32];
let mut l3 = [(0) as f32, (0) as f32];
let mut l4 = [(2) as f32, (0) as f32];
  near!(report, dist_squared_to_line_segment_v2(p2, l3, l4), dist_squared_to_line_segment(p2, l3, l4), 1e-6_f32);
let mut p3 = [(1) as f32, (1) as f32];
let mut degen = [(0) as f32, (0) as f32];
  near!(report, 2.0_f32, dist_squared_to_line_segment(p3, degen, degen), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:125
pub fn math_geom_hh__DistSquaredToLineSegment3D()->Report{let mut report=Report::default();
let mut p = [(0) as f32, (1) as f32, (0) as f32];
let mut l1 = [(0) as f32, (0) as f32, (0) as f32];
let mut l2 = [(1) as f32, (0) as f32, (0) as f32];
  near!(report, dist_squared_to_line_segment_v3(p, l1, l2), dist_squared_to_line_segment(p, l1, l2), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:133
pub fn math_geom_hh__ClosestToLineSegment3D()->Report{let mut report=Report::default();
let mut p = [(0.5_f32) as f32, (1.0_f32) as f32, (0.0_f32) as f32];
let mut l1 = [(0) as f32, (0) as f32, (0) as f32];
let mut l2 = [(1) as f32, (0) as f32, (0) as f32];
let mut c_r = [0.0_f32;3];
closest_to_line_segment_v3(&mut c_r, p, l1, l2);
let mut r = closest_to_line_segment(p, l1, l2);
  near!(report, c_r[0], r[0], 1e-6_f32);
  near!(report, c_r[1], r[1], 1e-6_f32);
  near!(report, c_r[2], r[2], 1e-6_f32);
let mut degen = [(1) as f32, (1) as f32, (1) as f32];
let mut r_degen = closest_to_line_segment(p, degen, degen);
  near!(report, degen[0], r_degen[0], 1e-6_f32);
  near!(report, degen[1], r_degen[1], 1e-6_f32);
  near!(report, degen[2], r_degen[2], 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:153
pub fn math_geom_hh__ClosestToPlaneNormalized()->Report{let mut report=Report::default();
let mut plane = [(0) as f32, (0) as f32, (1) as f32, (-1) as f32];
let mut pt = [(3) as f32, (4) as f32, (5) as f32];
let mut c_r = [0.0_f32;3];
closest_to_plane_normalized_v3(&mut c_r, plane, pt);
let mut r = closest_to_plane_normalized(plane, pt);
  near!(report, c_r[0], r[0], 1e-6_f32);
  near!(report, c_r[1], r[1], 1e-6_f32);
  near!(report, c_r[2], r[2], 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:168
pub fn math_geom_hh__ClosestToPlane()->Report{let mut report=Report::default();
let mut plane = [(0) as f32, (0) as f32, (2) as f32, (-2) as f32];
let mut pt = [(3) as f32, (4) as f32, (5) as f32];
let mut c_r = [0.0_f32;3];
closest_to_plane_v3(&mut c_r, plane, pt);
let mut r = closest_to_plane(plane, pt);
  near!(report, c_r[0], r[0], 1e-6_f32);
  near!(report, c_r[1], r[1], 1e-6_f32);
  near!(report, c_r[2], r[2], 1e-6_f32);
                                      
  near!(report, 1.0_f32, r[2], 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:185
pub fn math_geom_hh__DistSquaredToPlane()->Report{let mut report=Report::default();
let mut unit_plane = [(0) as f32, (0) as f32, (1) as f32, (0) as f32];
let mut pt = [(0) as f32, (0) as f32, (2) as f32];
  near!(report, dist_squared_to_plane_v3(pt, unit_plane), dist_squared_to_plane(pt, unit_plane), 1e-6_f32);
  near!(report, 4.0_f32, dist_squared_to_plane(pt, unit_plane), 1e-6_f32);
let mut scaled_plane = [(0) as f32, (0) as f32, (2) as f32, (0) as f32];
  near!(report, dist_squared_to_plane_v3(pt, scaled_plane), dist_squared_to_plane(pt, scaled_plane), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:208
pub fn math_geom_hh__LinePointFactor3D()->Report{let mut report=Report::default();
let mut p = [(0.5_f32) as f32, (1.0_f32) as f32, (0.0_f32) as f32];
let mut l1 = [(0) as f32, (0) as f32, (0) as f32];
let mut l2 = [(1) as f32, (0) as f32, (0) as f32];
  near!(report, line_point_factor_v3(p, l1, l2), line_point_factor(p, l1, l2), 1e-6_f32);

                              
  near!(report, 0.0_f32, line_point_factor(p, l1, l1), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:217
pub fn math_geom_hh__LinePointFactor2D()->Report{let mut report=Report::default();
let mut p = [(0.5_f32) as f32, (1.0_f32) as f32];
let mut l1 = [(0) as f32, (0) as f32];
let mut l2 = [(1) as f32, (0) as f32];
  near!(report, line_point_factor_v2(p, l1, l2), line_point_factor(p, l1, l2), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:229
pub fn math_geom_hh__AxisDominantToM3()->Report{let mut report=Report::default();
let mut normal = normalize([(0) as f32, (0) as f32, (1) as f32]);
let mut c_mat = [[0.0_f32;3];3];
axis_dominant_v3_to_m3(&mut c_mat, normal);
let mut mat = axis_dominant_to_m3(normal);
  for col in 0..3 {
    for row in 0..3 {
      near!(report, c_mat[col][row], mat[col][row], 1e-6_f32);
    }
  }

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:249
pub fn math_geom_hh__IsectLineLine3D()->Report{let mut report=Report::default();
let mut v1 = [(-1) as f32, (0) as f32, (0) as f32];
let mut v2 = [(1) as f32, (0) as f32, (0) as f32];
let mut v3 = [(0) as f32, (-1) as f32, (0) as f32];
let mut v4 = [(0) as f32, (1) as f32, (0) as f32];
let mut r_i1 = [0.0_f32;3];
let mut r_i2 = [0.0_f32;3];
let mut count:i32 = isect_line_line(v1, v2, v3, v4, &mut r_i1, &mut r_i2);
  numeq!(report, 1, count);
  near!(report, 0.0_f32, r_i1[0], 1e-5_f32);
  near!(report, 0.0_f32, r_i1[1], 1e-5_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:260
pub fn math_geom_hh__IsectLinePlane()->Report{let mut report=Report::default();
let mut l1 = [(0) as f32, (0) as f32, (0) as f32];
let mut l2 = [(0) as f32, (0) as f32, (2) as f32];
let mut plane_co = [(0) as f32, (0) as f32, (1) as f32];
let mut plane_no = [(0) as f32, (0) as f32, (1) as f32];
let mut hit = isect_line_plane(l1, l2, plane_co, plane_no);
  fatal_yes!(report, hit.is_some());
  near!(report, 0.0_f32, hit.as_ref().unwrap()[0], 1e-6_f32);
  near!(report, 0.0_f32, hit.as_ref().unwrap()[1], 1e-6_f32);
  near!(report, 1.0_f32, hit.as_ref().unwrap()[2], 1e-6_f32);
let mut l3 = [(0) as f32, (0) as f32, (0) as f32];
let mut l4 = [(1) as f32, (0) as f32, (0) as f32];
  no!(report, isect_line_plane(l3, l4, plane_co, plane_no).is_some());

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:276
pub fn math_geom_hh__IsectPointTri2D()->Report{let mut report=Report::default();
let mut v1 = [(-1) as f32, (0) as f32];
let mut v2 = [(1) as f32, (0) as f32];
let mut v3 = [(0) as f32, (2) as f32];

                            
  numeq!(report, 1, isect_point_tri([(0) as f32, (0.5_f32) as f32], v1, v2, v3));
                
  numeq!(report, 0, isect_point_tri([(0) as f32, (3) as f32], v1, v2, v3));
                   
  numeq!(report, -1, isect_point_tri([(0) as f32, (0.5_f32) as f32], v3, v2, v1));

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:288
pub fn math_geom_hh__IsectPointQuad2D()->Report{let mut report=Report::default();
let mut v1 = [(0) as f32, (0) as f32];
let mut v2 = [(2) as f32, (0) as f32];
let mut v3 = [(2) as f32, (2) as f32];
let mut v4 = [(0) as f32, (2) as f32];

                        
  numeq!(report, 1, isect_point_quad([(1) as f32, (1) as f32], v1, v2, v3, v4));
                
  numeq!(report, 0, isect_point_quad([(3) as f32, (1) as f32], v1, v2, v3, v4));
                   
  numeq!(report, -1, isect_point_quad([(1) as f32, (1) as f32], v4, v3, v2, v1));
let mut p_inside = [(1) as f32, (1) as f32];
  numeq!(report, isect_point_quad_v2(p_inside, v1, v2, v3, v4), isect_point_quad([(1) as f32, (1) as f32], v1, v2, v3, v4));

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:305
pub fn math_geom_hh__IsectPointPoly()->Report{let mut report=Report::default();

                                                                            
  let verts:Vec<[f32;2]> = [[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]].to_vec();
  yes!(report, isect_point_poly([(0.5_f32) as f32, (0.5_f32) as f32], &verts));
  no!(report, isect_point_poly([(2.0_f32) as f32, (0.5_f32) as f32], &verts));
let mut pt_in = [(0.5_f32) as f32, (0.5_f32) as f32];
  eq!(report, isect_point_poly_v2(
                pt_in, &verts, verts.len()), isect_point_poly(pt_in, &verts));

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:325
pub fn math_geom_hh__BarycentricWeights()->Report{let mut report=Report::default();
let mut v1 = [(0) as f32, (0) as f32];
let mut v2 = [(1) as f32, (0) as f32];
let mut v3 = [(0) as f32, (1) as f32];
let mut centroid = [(1.0_f32 / 3.0_f32) as f32, (1.0_f32 / 3.0_f32) as f32];
let mut c_w = [0.0_f32;3];
barycentric_weights_v2(v1, v2, v3, centroid, &mut c_w);
let mut w = barycentric_weights(v1, v2, v3, centroid);
  near!(report, c_w[0], w[0], 1e-6_f32);
  near!(report, c_w[1], w[1], 1e-6_f32);
  near!(report, c_w[2], w[2], 1e-6_f32);
  near!(report, 1.0_f32 / 3.0_f32, w[0], 1e-5_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:348
pub fn math_geom_hh__PolyToTriCount()->Report{let mut report=Report::default();

                                                    
  numeq!(report, 2, poly_to_tri_count(1, 4));
                                                         
  numeq!(report, 2, poly_to_tri_count(2, 6));
                                           
  numeq!(report, poly_to_tri_count(5, 20), legacy_poly_to_tri_count(5, 20));

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:358
pub fn math_geom_hh__AreaPoly()->Report{let mut report=Report::default();

                              
  let verts:Vec<[f32;2]> = [[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]].to_vec();
  near!(report, 1.0_f32, area_poly(&verts), 1e-6_f32);

                               
  near!(report, area_poly_v2(&verts, verts.len()), area_poly(&verts), 1e-6_f32);

                                                 
  let tri:Vec<[f32;2]> = [[(0) as f32, (0) as f32], [(2) as f32, (0) as f32], [(1) as f32, (1) as f32]].to_vec();
  near!(report, 1.0_f32, area_poly(&tri), 1e-6_f32);

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:374
pub fn math_geom_hh__InterpWeightsPoly()->Report{let mut report=Report::default();

                                                                   
  let verts:Vec<[f32;2]> = [[(0) as f32, (0) as f32], [(1) as f32, (0) as f32], [(1) as f32, (1) as f32], [(0) as f32, (1) as f32]].to_vec();
let mut w = [0.0_f32;4];
interp_weights_poly(&mut w, &verts, [(0.5_f32) as f32, (0.5_f32) as f32]);
  for i in 0..4 {
    near!(report, 0.25_f32, w[i], 1e-5_f32);
  }
let mut c_w = [0.0_f32;4];
interp_weights_poly_v2(&mut c_w, &verts, verts.len(), [(0.5_f32) as f32, (0.5_f32) as f32]);
  for i in 0..4 {
    near!(report, c_w[i], w[i], 1e-6_f32);
  }

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:399
pub fn math_geom_hh__InterpBilinearQuad()->Report{let mut report=Report::default();
let mut v0 = [(0) as f32, (0) as f32, (0) as f32];
let mut v1 = [(1) as f32, (0) as f32, (0) as f32];
let mut v2 = [(1) as f32, (1) as f32, (0) as f32];
let mut v3 = [(0) as f32, (1) as f32, (0) as f32];
let mut center = interp_bilinear_quad(v0, v1, v2, v3, 0.5_f32, 0.5_f32);
  near!(report, 0.5_f32, center[0], 1e-6_f32);
  near!(report, 0.5_f32, center[1], 1e-6_f32);
  near!(report, 0.0_f32, center[2], 1e-6_f32);
let mut quad = [[(v0[0]) as f32, (v0[1]) as f32, (v0[2]) as f32], [(v1[0]) as f32, (v1[1]) as f32, (v1[2]) as f32], [(v2[0]) as f32, (v2[1]) as f32, (v2[2]) as f32], [(v3[0]) as f32, (v3[1]) as f32, (v3[2]) as f32]];
let mut c_res = [0.0_f32;3];
interp_bilinear_quad_v3(quad, 0.25_f32, 0.75_f32, &mut c_res);
let mut res = interp_bilinear_quad(v0, v1, v2, v3, 0.25_f32, 0.75_f32);
  near!(report, c_res[0], res[0], 1e-6_f32);
  near!(report, c_res[1], res[1], 1e-6_f32);
  near!(report, c_res[2], res[2], 1e-6_f32);

                
  eq!(report, v0, interp_bilinear_quad(v0, v1, v2, v3, 0.0_f32, 0.0_f32));
  eq!(report, v1, interp_bilinear_quad(v0, v1, v2, v3, 1.0_f32, 0.0_f32));
  eq!(report, v2, interp_bilinear_quad(v0, v1, v2, v3, 1.0_f32, 1.0_f32));
  eq!(report, v3, interp_bilinear_quad(v0, v1, v2, v3, 0.0_f32, 1.0_f32));

report
}

// source/blender/blenlib/tests/BLI_math_geom_hh_test.cc:437
pub fn math_geom_hh__MapToSphere()->Report{let mut report=Report::default();
let mut up = [(0) as f32, (0) as f32, (1) as f32];
let mut c_u:f32 = 0.0_f32;
let mut c_v:f32 = 0.0_f32;
map_to_sphere_out(&mut c_u, &mut c_v, up[0], up[1], up[2]);
let mut uv = map_to_sphere(up);
  near!(report, c_u, uv[0], 1e-6_f32);
  near!(report, c_v, uv[1], 1e-6_f32);

report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("math_geom.DistToLine2DSimple",math_geom__DistToLine2DSimple,1),
("math_geom.DistToLineSegment2DSimple",math_geom__DistToLineSegment2DSimple,1),
("math_geom.IsectPointTri2D",math_geom__IsectPointTri2D,24),
("math_geom.IsectPointQuad2D",math_geom__IsectPointQuad2D,24),
("math_geom.CrossPoly",math_geom__CrossPoly,8),
("math_geom_hh.NormalQuad",math_geom_hh__NormalQuad,3),
("math_geom_hh.AreaTri",math_geom_hh__AreaTri,3),
("math_geom_hh.CotangentTriWeight",math_geom_hh__CotangentTriWeight,2),
("math_geom_hh.PlaneFromPointNormal",math_geom_hh__PlaneFromPointNormal,4),
("math_geom_hh.PlanePointSide",math_geom_hh__PlanePointSide,4),
("math_geom_hh.DistSquaredToLineSegment2D",math_geom_hh__DistSquaredToLineSegment2D,3),
("math_geom_hh.DistSquaredToLineSegment3D",math_geom_hh__DistSquaredToLineSegment3D,1),
("math_geom_hh.ClosestToLineSegment3D",math_geom_hh__ClosestToLineSegment3D,6),
("math_geom_hh.ClosestToPlaneNormalized",math_geom_hh__ClosestToPlaneNormalized,3),
("math_geom_hh.ClosestToPlane",math_geom_hh__ClosestToPlane,4),
("math_geom_hh.DistSquaredToPlane",math_geom_hh__DistSquaredToPlane,3),
("math_geom_hh.LinePointFactor3D",math_geom_hh__LinePointFactor3D,2),
("math_geom_hh.LinePointFactor2D",math_geom_hh__LinePointFactor2D,1),
("math_geom_hh.AxisDominantToM3",math_geom_hh__AxisDominantToM3,9),
("math_geom_hh.IsectLineLine3D",math_geom_hh__IsectLineLine3D,3),
("math_geom_hh.IsectLinePlane",math_geom_hh__IsectLinePlane,5),
("math_geom_hh.IsectPointTri2D",math_geom_hh__IsectPointTri2D,3),
("math_geom_hh.IsectPointQuad2D",math_geom_hh__IsectPointQuad2D,4),
("math_geom_hh.IsectPointPoly",math_geom_hh__IsectPointPoly,3),
("math_geom_hh.BarycentricWeights",math_geom_hh__BarycentricWeights,4),
("math_geom_hh.PolyToTriCount",math_geom_hh__PolyToTriCount,3),
("math_geom_hh.AreaPoly",math_geom_hh__AreaPoly,3),
("math_geom_hh.InterpWeightsPoly",math_geom_hh__InterpWeightsPoly,8),
("math_geom_hh.InterpBilinearQuad",math_geom_hh__InterpBilinearQuad,10),
("math_geom_hh.MapToSphere",math_geom_hh__MapToSphere,2),
];
