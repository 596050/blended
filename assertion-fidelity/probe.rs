
// Appended only in a diagnostic shadow. Original test/helper bodies unchanged.
pub fn mask_diagnostic_tape()->Vec<u8>{
 fn emit(out:&mut Vec<u8>,v:u64){out.extend_from_slice(&v.to_le_bytes());}
 let mut out=b"MASKORC2".to_vec();emit(&mut out,50);let mut rng=BlenderRng::new(0);
 for _ in 0..50{
  let size=(rng.get_int32()%200000+1) as usize;emit(&mut out,size as u64);
  for _ in 0..3{let values=random_bools(&mut rng,size);out.extend(values.into_iter().map(u8::from));}
 }
 emit(&mut out,3*2*64*64);
 for origin in [0_i64,16380,(1_i64<<31)-128]{for stride in [1_i64,17]{
  for abits in 0..64{for bbits in 0..64{
   let cbits=((abits*17)^(bbits*31))&63;
   for value in [origin,stride,abits as i64,bbits as i64,cbits as i64]{emit(&mut out,value as u64);}
   let build=|bits:i32|IndexMask::from_indices((0..6).filter(|i|bits&(1<<i)!=0).map(|i|origin+i*stride));
   let a=build(abits);let b=build(bbits);let c=build(cbits);let universe=build(63);let builder=ExprBuilder::new();
   let mut write_mask=|mask:IndexMask|{
    let mut bits=0_u64;for i in 0..6{if mask.contains(origin+i*stride){bits|=1_u64<<i;}}
    emit(&mut out,mask.len() as u64);emit(&mut out,bits);
    for index in mask.iter(){emit(&mut out,index as u64);}
   };
   write_mask(builder.merge([(&a).into(),(&b).into(),(&c).into()]).evaluate());
   write_mask(builder.intersect([(&a).into(),(&b).into()]).evaluate());
   write_mask(builder.subtract((&a).into(),[(&b).into(),(&c).into()]).evaluate());
   write_mask(a.complement(&universe));write_mask(a.complement(&b));
   write_mask(builder.subtract(builder.merge([(&a).into(),(&b).into()]),[builder.intersect([(&b).into(),(&c).into()])]).evaluate());
  }}
 }}
 out
}
use std::cell::RefCell;
thread_local!{static MASK_ORACLE_OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_oracle_run()->usize{let bytes=mask_diagnostic_tape();let n=bytes.len();MASK_ORACLE_OUT.with(|out|*out.borrow_mut()=bytes);n}
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_oracle_ptr()->*const u8{MASK_ORACLE_OUT.with(|out|out.borrow().as_ptr())}
