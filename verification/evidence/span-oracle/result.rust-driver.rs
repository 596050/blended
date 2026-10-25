
use crate::spans::{Span,MutableSpan};
use core::cell::Cell;
fn emit(out:&mut Vec<u8>,v:i64){out.extend_from_slice(&(v as u32).to_le_bytes());}
fn view(out:&mut Vec<u8>,s:Span<'_,i32>){emit(out,s.len() as i64);for v in s.iter(){emit(out,v as i64);}}
fn mutable_view(out:&mut Vec<u8>,s:MutableSpan<'_,i32>){view(out,s.as_span());}
pub fn generate()->Vec<u8>{let mut out=Vec::new();
 for n in 0..=32{
  let storage:[Cell<i32>;96]=core::array::from_fn(|i|Cell::new(((i*17+n*3)%101) as i32-50));
  let s=Span::from_cells(&storage[..n]);let m=MutableSpan::from_cells(&storage[..n]);
  emit(&mut out,s.size_in_bytes() as i64);emit(&mut out,i64::from(s.is_empty()));view(&mut out,s);
  for k in 0..=n+6{view(&mut out,s.drop_front(k));view(&mut out,s.drop_back(k));view(&mut out,s.take_front(k));view(&mut out,s.take_back(k));mutable_view(&mut out,m.drop_front(k));mutable_view(&mut out,m.drop_back(k));mutable_view(&mut out,m.take_front(k));mutable_view(&mut out,m.take_back(k));}
  for start in 0..=n{
   for len in 0..=n-start{let a=s.slice(start,len);let b=m.slice(start,len);view(&mut out,a);mutable_view(&mut out,b);emit(&mut out,((a.data() as usize-s.data() as usize)/core::mem::size_of::<i32>()) as i64);emit(&mut out,((b.as_span().data() as usize-s.data() as usize)/core::mem::size_of::<i32>()) as i64);}
   for len in 0..=n+3{view(&mut out,s.slice_safe(start,len));mutable_view(&mut out,m.slice_safe(start,len));}
  }
  for value in -55..=55{emit(&mut out,i64::from(s.contains(value)));emit(&mut out,s.count(value) as i64);}
  emit(&mut out,i64::from(s.has_duplicates_linear()));
  for i in 0..n{emit(&mut out,s.first_index(s.at(i)) as i64);emit(&mut out,s.last(i) as i64);emit(&mut out,i64::from(s.contains_ptr(s.data().wrapping_add(i))));}
  emit(&mut out,i64::from(s.contains_ptr(s.data().wrapping_add(n))));
  for v in s.iter().rev(){emit(&mut out,v as i64);}
  m.fill(7);view(&mut out,s);m.reverse();view(&mut out,s);
  for i in 0..n{storage[i].set(i as i32*5-17);}
  view(&mut out,s);m.reverse();view(&mut out,s);
  let selected:Vec<usize>=(0..n).step_by(3).collect();m.fill_indices(&selected,-11);view(&mut out,s);
  for cell in m.iter().rev(){cell.set(cell.get()+13);}
  view(&mut out,s);let copy:[i32;96]=core::array::from_fn(|i|90-i as i32);
  m.copy_from(Span::from_slice(&copy[..n]));view(&mut out,s);
 }
 for length in 0..=8{
  let raw=[0x01234567_u32,0x89abcdef,0x00000000,0xffffffff,0x80000000,0x7fc12345,0x3f800000,0xdeadbeef];
  let words=Span::from_slice(&raw[..length]);let bytes=words.cast::<u8>();let shorts=words.cast::<u16>();
  emit(&mut out,bytes.len() as i64);for v in bytes.iter(){emit(&mut out,v as i64);}
  emit(&mut out,shorts.len() as i64);for v in shorts.iter(){emit(&mut out,v as i64);}
  let roundtrip=shorts.cast::<u32>();emit(&mut out,roundtrip.len() as i64);for v in roundtrip.iter(){emit(&mut out,v as i64);}
 }
 let mut a=2_i32;let mut b=5_i32;let mut c=8_i32;let ap=&mut a as *mut i32;let bp=&mut b as *mut i32;let cp=&mut c as *mut i32;
 let pointers=[ap,bp,core::ptr::null_mut()].map(Cell::new);let mutable=MutableSpan::from_cells(&pointers);
 let read:Span<'_,*const i32>=mutable.into();
 emit(&mut out,i64::from(read.at(0)==ap));pointers[0].set(cp);emit(&mut out,i64::from(read.at(0)==cp));mutable.set(1,ap);emit(&mut out,i64::from(pointers[1].get()==ap));
 let original:Span<'_,*mut i32>=mutable.into();let floats=original.cast::<*mut f32>();emit(&mut out,i64::from(floats.at(0)==cp.cast()));emit(&mut out,i64::from(floats.at(1)==ap.cast()));emit(&mut out,i64::from(floats.at(2).is_null()));
 out}
use std::cell::RefCell;thread_local!{static OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn span_oracle_run()->usize{let v=generate();let n=v.len();OUT.with(|o|*o.borrow_mut()=v);n}
#[unsafe(no_mangle)]pub extern "C" fn span_oracle_ptr()->*const u8{OUT.with(|o|o.borrow().as_ptr())}
