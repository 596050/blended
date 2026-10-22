// SPDX-License-Identifier: GPL-3.0-or-later
// New browser-product tests. These are NOT counted as upstream Blender ports.
use blended_core::browser_geometry::*;
#[test] fn box_has_independent_face_vertices_and_twelve_triangles(){let m=box_mesh(2.,4.,6.).unwrap();assert_eq!(m.positions.len(),72);assert_eq!(m.indices.len(),36);}
#[test] fn box_has_exact_dimensions(){let m=box_mesh(2.,4.,6.).unwrap();for a in 0..3 {let v:Vec<f32>=m.positions.chunks(3).map(|p|p[a]).collect();assert_eq!(v.iter().copied().fold(f32::INFINITY,f32::min),-([1.,2.,3.][a]));assert_eq!(v.iter().copied().fold(f32::NEG_INFINITY,f32::max),[1.,2.,3.][a]);}}
#[test] fn box_faces_point_outwards(){let m=box_mesh(2.,2.,2.).unwrap();for tri in m.indices.chunks(3){let p=|i:u32|[m.positions[i as usize*3],m.positions[i as usize*3+1],m.positions[i as usize*3+2]];let a=p(tri[0]);let b=p(tri[1]);let c=p(tri[2]);let u=[b[0]-a[0],b[1]-a[1],b[2]-a[2]];let v=[c[0]-a[0],c[1]-a[1],c[2]-a[2]];let n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];assert!(n[0]*a[0]+n[1]*a[1]+n[2]*a[2]>0.);}}
#[test] fn invalid_box_dimensions_rejected(){for x in [0.,-1.,f32::NAN,f32::INFINITY]{assert!(box_mesh(x,1.,1.).is_none());assert!(box_mesh(1.,x,1.).is_none());assert!(box_mesh(1.,1.,x).is_none());}}
#[test] fn plane_is_xz_with_two_triangles(){let m=plane_mesh(4.,6.).unwrap();assert_eq!(m.positions.len(),12);assert_eq!(m.indices.len(),6);assert!(m.positions.chunks(3).all(|p|p[1]==0.));assert!(m.indices.iter().all(|i|*i<4));}
#[test] fn invalid_plane_dimensions_rejected(){assert!(plane_mesh(0.,1.).is_none());assert!(plane_mesh(1.,f32::NAN).is_none());}
