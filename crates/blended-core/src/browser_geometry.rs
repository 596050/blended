// SPDX-License-Identifier: GPL-3.0-or-later
//! New modeller contracts. These are not claimed as upstream Blender test ports.
use std::cell::RefCell;
#[derive(Debug,Clone)]
pub struct Mesh { pub positions: Vec<f32>, pub indices: Vec<u32> }
fn valid(x:f32)->bool{x.is_finite()&&x>0.0&&x<=1_000_000.0}
pub fn box_mesh(width:f32,height:f32,depth:f32)->Option<Mesh>{
 if ![width,height,depth].into_iter().all(valid){return None;}
 let (x,y,z)=(width/2.0,height/2.0,depth/2.0);
 let faces=[
  [[x,-y,-z],[x,y,-z],[x,y,z],[x,-y,z]],
  [[-x,-y,z],[-x,y,z],[-x,y,-z],[-x,-y,-z]],
  [[-x,y,-z],[-x,y,z],[x,y,z],[x,y,-z]],
  [[-x,-y,z],[-x,-y,-z],[x,-y,-z],[x,-y,z]],
  [[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]],
  [[x,-y,-z],[-x,-y,-z],[-x,y,-z],[x,y,-z]],
 ];
 let mut positions=Vec::with_capacity(72);let mut indices=Vec::with_capacity(36);
 for (i,face) in faces.iter().enumerate(){for p in face{positions.extend_from_slice(p);}let b=i as u32*4;indices.extend_from_slice(&[b,b+1,b+2,b,b+2,b+3]);}
 Some(Mesh{positions,indices})
}
pub fn plane_mesh(width:f32,depth:f32)->Option<Mesh>{
 if !valid(width)||!valid(depth){return None;}
 let(x,z)=(width/2.0,depth/2.0);
 Some(Mesh{positions:vec![-x,0.,-z,-x,0.,z,x,0.,z,x,0.,-z],indices:vec![0,1,2,0,2,3]})
}
thread_local!{static OUTPUT:RefCell<Option<Mesh>>=const{RefCell::new(None)};}
fn set_output(mesh:Option<Mesh>)->i32{let ok=mesh.is_some();OUTPUT.with(|v|*v.borrow_mut()=mesh);i32::from(ok)}
#[unsafe(no_mangle)]pub extern "C" fn blended_make_box(w:f32,h:f32,d:f32)->i32{set_output(box_mesh(w,h,d))}
#[unsafe(no_mangle)]pub extern "C" fn blended_make_plane(w:f32,d:f32)->i32{set_output(plane_mesh(w,d))}
// The browser copies these views before requesting another mesh. Pointers
// remain valid until the next make call, which replaces this owned buffer.
#[unsafe(no_mangle)]pub extern "C" fn blended_positions_ptr()->usize{OUTPUT.with(|v|v.borrow().as_ref().map_or(0,|m|m.positions.as_ptr() as usize))}
#[unsafe(no_mangle)]pub extern "C" fn blended_positions_len()->usize{OUTPUT.with(|v|v.borrow().as_ref().map_or(0,|m|m.positions.len()))}
#[unsafe(no_mangle)]pub extern "C" fn blended_indices_ptr()->usize{OUTPUT.with(|v|v.borrow().as_ref().map_or(0,|m|m.indices.as_ptr() as usize))}
#[unsafe(no_mangle)]pub extern "C" fn blended_indices_len()->usize{OUTPUT.with(|v|v.borrow().as_ref().map_or(0,|m|m.indices.len()))}
