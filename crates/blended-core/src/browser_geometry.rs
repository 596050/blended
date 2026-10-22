// SPDX-License-Identifier: GPL-3.0-or-later
//! New modeller contracts, not claimed to be ported Blender tests.
#[derive(Debug,Clone)]
pub struct Mesh { pub positions: Vec<f32>, pub indices: Vec<u32> }
pub fn box_mesh(_width:f32,_height:f32,_depth:f32)->Option<Mesh> { todo!("TDD red: implement box geometry") }
pub fn plane_mesh(_width:f32,_depth:f32)->Option<Mesh> { todo!("TDD red: implement plane geometry") }
