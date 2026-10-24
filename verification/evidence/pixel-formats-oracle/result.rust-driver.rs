// Diagnostic wrapper only; production implementation and original tests unchanged.
use crate::pixel_formats as m;
fn emit(out:&mut Vec<u8>,v:u32){out.extend_from_slice(&v.to_le_bytes());}
fn read32(data:&[u8],pos:&mut usize)->usize{let v=u32::from_le_bytes(data[*pos..*pos+4].try_into().unwrap());*pos+=4;v as usize}
fn read_vec(data:&[u8],pos:&mut usize)->Vec<f32>{let n=read32(data,pos);(0..n).map(|_|f32::from_bits(read32(data,pos) as u32)).collect()}
fn norm<const N:usize>(out:&mut Vec<u8>,input:&[f32],widths:[u8;N],signed:bool,raw_count:u32){
 for k in 0..input.len(){let f=core::array::from_fn(|j|input[(k+j*17)%input.len()]);let p=m::Normalized::from_float(f,widths,signed);for v in p.integers(){emit(out,v as u32);}for v in p.to_float(){emit(out,v.to_bits());}emit(out,p.packed_bits() as u32);emit(out,(p.packed_bits()>>32) as u32);}
 for raw in 0..raw_count{let mut bits=0_u64;let mut shift=0;for j in 0..N{let width=widths[j];let v=(raw+j as u32*53)&((1_u32<<width)-1);bits|=u64::from(v)<<shift;shift+=width;}let p=m::Normalized::from_bits(bits,widths,signed);for v in p.integers(){emit(out,v as u32);}for v in p.to_float(){emit(out,v.to_bits());}}
}
pub fn generate()->Vec<u8>{
 let data=include_bytes!("pixel_oracle.inputs.bin");let mut pos=0;let floats=read_vec(data,&mut pos);let normalised=read_vec(data,&mut pos);assert_eq!(pos,data.len());let mut out=Vec::new();
 let halves:Vec<u16>=(0..65536_u32).map(|v|v as u16).collect();for &h in &halves{emit(&mut out,m::half_to_float(h).to_bits());}
 let mut decoded=vec![0.0_f32;65536];m::half_to_float_array(&halves,&mut decoded,65536);for &v in &decoded{emit(&mut out,v.to_bits());}
 let before=m::ScopedFlushToZero::control_word();
 {let _guard=m::ScopedFlushToZero::new();if let Some(mode)=m::ScopedFlushToZero::control_word(){assert_eq!(mode&0x8040,0x8040);}m::half_to_float_array(&halves,&mut decoded,65536);for &v in &decoded{emit(&mut out,v.to_bits());}}
 assert_eq!(before,m::ScopedFlushToZero::control_word());
 for &v in &floats{emit(&mut out,u32::from(m::float_to_half(v)));emit(&mut out,u32::from(m::float_to_half_make_finite(v)));}
 let mut output=vec![0_u16;floats.len()];let n=output.len();m::float_to_half_array(&floats,&mut output,n);for &v in &output{emit(&mut out,u32::from(v));}
 m::float_to_half_make_finite_array(&floats,&mut output,n);for &v in &output{emit(&mut out,u32::from(v));}
m::float_to_half_clamp_array(&floats,&mut output,n,-10.0_f32,1000.0_f32);for &v in &output{emit(&mut out,u32::from(v));}
m::float_to_half_clamp_array(&floats,&mut output,n,1.0_f32,2.0_f32);for &v in &output{emit(&mut out,u32::from(v));}
m::float_to_half_clamp_array(&floats,&mut output,n,-2.0_f32,-1.0_f32);for &v in &output{emit(&mut out,u32::from(v));}
let tail_bits=[0x7f800001_u32,0xffc12345_u32,0x0_u32,0x80000000_u32,0x33800000_u32,0xb3800000_u32,0x387fc000_u32,0x38800000_u32,0x477fe000_u32,0xc77fe000_u32,0x7f800000_u32,0xff800000_u32,0x3f801000_u32,0x3f803000_u32,0x3f800000_u32,0xbf800000_u32,0x800000_u32,0x1_u32,0x7fffffff_u32];
let tail_half=[0x7c01_u16,0xfe23_u16,0x0_u16,0x8000_u16,0x1_u16,0x8001_u16,0x3ff_u16,0x400_u16,0x7bff_u16,0xfbff_u16,0x7c00_u16,0xfc00_u16,0x3c01_u16,0x3c02_u16,0x3c00_u16,0xbc00_u16,0x2_u16,0x3_u16,0x7fff_u16];

 for rotation in 0..4{let src:[f32;20]=core::array::from_fn(|i|f32::from_bits(tail_bits[(i+rotation)%19]));let hsrc:[u16;20]=core::array::from_fn(|i|tail_half[(i+rotation)%19]);
 for n in 0..18{let mut f=[f32::from_bits(0x41234567);20];m::half_to_float_array(&hsrc,&mut f,n);for v in f{emit(&mut out,v.to_bits());}
 let mut h=[0xa55a_u16;20];m::float_to_half_array(&src,&mut h,n);for v in h{emit(&mut out,u32::from(v));}
 h.fill(0xa55a);m::float_to_half_make_finite_array(&src,&mut h,n);for v in h{emit(&mut out,u32::from(v));}
h.fill(0xa55a);m::float_to_half_clamp_array(&src,&mut h,n,-10.0_f32,1000.0_f32);for v in h{emit(&mut out,u32::from(v));}
h.fill(0xa55a);m::float_to_half_clamp_array(&src,&mut h,n,1.0_f32,2.0_f32);for v in h{emit(&mut out,u32::from(v));}
h.fill(0xa55a);m::float_to_half_clamp_array(&src,&mut h,n,-2.0_f32,-1.0_f32);for v in h{emit(&mut out,u32::from(v));}
}}
norm(&mut out,&normalised,[8, 8, 8, 8],true,256);
norm(&mut out,&normalised,[8, 8, 8, 8],false,256);
norm(&mut out,&normalised,[16, 16],true,65536);
norm(&mut out,&normalised,[16, 16],false,65536);
norm(&mut out,&normalised,[16, 16, 16, 16],true,0);
norm(&mut out,&normalised,[16, 16, 16, 16],false,0);
norm(&mut out,&normalised,[10, 10, 10, 2],true,1024);
norm(&mut out,&normalised,[10, 10, 10, 2],false,1024);
out}
use std::cell::RefCell;thread_local!{static OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn pixel_oracle_run()->usize{let v=generate();let n=v.len();OUT.with(|o|*o.borrow_mut()=v);n}
#[unsafe(no_mangle)]pub extern "C" fn pixel_oracle_ptr()->*const u8{OUT.with(|o|o.borrow().as_ptr())}
