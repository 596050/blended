// Diagnostic driver only; production implementation and tests unchanged.
fn read(data:&[u8],p:&mut usize)->u32{let value=u32::from_le_bytes(data[*p..*p+4].try_into().unwrap());*p+=4;value}
fn write(out:&mut Vec<u8>,v:u32){out.extend_from_slice(&v.to_le_bytes());}
pub fn generate()->Vec<u8>{let data=include_bytes!("polyfill_probe.inputs.bin");let mut p=0;let total=read(data,&mut p);let mut out=Vec::new();
for k in 0..total{let n=read(data,&mut p) as usize;let base:Vec<[u32;2]>=(0..n).map(|_|[read(data,&mut p),read(data,&mut p)]).collect();
 for rev in 0..2_u32{for cycle in 0..n{for fx in 0..2_u32{for fy in 0..2_u32{
  for v in [k,rev,cycle as u32,fx,fy,n as u32]{write(&mut out,v);}
  let points:Vec<[f32;2]>=(0..n).map(|i|{let mut j=(i+cycle)%n;if rev!=0{j=n-1-j;}let a=base[j][0]^(fx<<31);let b=base[j][1]^(fy<<31);write(&mut out,a);write(&mut out,b);[f32::from_bits(a),f32::from_bits(b)]}).collect();
  let mut tris=crate::polyfill::triangulate(&points);for tri in &tris{for &v in tri{write(&mut out,v);}}
  crate::polyfill::beautify(&points,&mut tris);for tri in &tris{for &v in tri{write(&mut out,v);}}
 }}}}
}assert_eq!(p,data.len());out}
use std::cell::RefCell;thread_local!{static OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn polygon_probe_run()->usize{let v=generate();let n=v.len();OUT.with(|o|*o.borrow_mut()=v);n}
#[unsafe(no_mangle)]pub extern "C" fn polygon_probe_ptr()->*const u8{OUT.with(|o|o.borrow().as_ptr())}
