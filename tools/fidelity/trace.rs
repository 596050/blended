// SPDX-License-Identifier: Apache-2.0
// Build-only instrumentation; this is not a replacement for the production tests.
use std::cell::RefCell;
use crate::data_structures::{Bounds,VecN,IndexRange};
thread_local! {static TAPE:RefCell<(String,String)>=const{RefCell::new((String::new(),String::new()))};}
pub trait Value {fn encode(&self)->String;}
macro_rules! ints {($($t:ty),*)=>{$(impl Value for $t {fn encode(&self)->String {format!("\"i:{}\"",self)}})*};}
ints!(i8,i16,i32,i64,isize,u8,u16,u32,u64,usize);
impl Value for bool {fn encode(&self)->String{format!("\"b:{}\"",if *self {1}else{0})}}
impl Value for f64 {fn encode(&self)->String{format!("\"f:{:016x}\"",self.to_bits())}}
impl Value for f32 {fn encode(&self)->String{(*self as f64).encode()}}
impl<T:Value,const N:usize> Value for [T;N] {fn encode(&self)->String{format!("[{}]",self.iter().map(Value::encode).collect::<Vec<_>>().join(","))}}
impl<T:Value,const N:usize> Value for VecN<T,N> {fn encode(&self)->String{self.0.encode()}}
impl<T:Value> Value for Bounds<T> {fn encode(&self)->String{format!("{{\"min\":{},\"max\":{}}}",self.min.encode(),self.max.encode())}}
impl<T:Value> Value for Option<T> {fn encode(&self)->String {self.as_ref().map(Value::encode).unwrap_or_else(||"\"none\"".into())}}
impl Value for IndexRange {fn encode(&self)->String{format!("{{\"start\":{},\"size\":{}}}",if self.is_empty(){0_i64.encode()}else{self.start().encode()},self.size().encode())}}
thread_local! {static POINTER_ORIGIN:RefCell<Option<usize>>=const{RefCell::new(None)};}
impl Value for *const core::cell::Cell<u64> {
 fn encode(&self)->String {POINTER_ORIGIN.with(|origin|{
  let address=*self as usize;let mut origin=origin.borrow_mut();let base=*origin.get_or_insert(address);
  let delta=address as i128-base as i128;let size=core::mem::size_of::<core::cell::Cell<u64>>() as i128;
  assert_eq!(delta%size,0);format!("\"p64:{}\"",delta/size)
 })}
}
impl<T:Value> Value for &[T] {fn encode(&self)->String{format!("[{}]",self.iter().map(Value::encode).collect::<Vec<_>>().join(","))}}
thread_local! {static BYTE_POINTER_ORIGIN:RefCell<Option<usize>>=const{RefCell::new(None)};}
impl Value for *const u8 {
 fn encode(&self)->String {BYTE_POINTER_ORIGIN.with(|origin|{let address=*self as usize;let mut origin=origin.borrow_mut();let base=*origin.get_or_insert(address);format!("\"p8:{}\"",address as i128-base as i128)})}
}
fn bytes_value(bytes:&[u8])->String{format!("\"s:{}\"",bytes.iter().map(|b|format!("{b:02x}")).collect::<String>())}
impl Value for crate::string_refs::StringRef<'_>{fn encode(&self)->String{bytes_value(self.as_bytes())}}
impl Value for crate::string_refs::StringRefNull<'_>{fn encode(&self)->String{bytes_value(self.as_bytes())}}
impl Value for crate::string_refs::Bytes{fn encode(&self)->String{bytes_value(self.as_ref())}}
impl Value for String {fn encode(&self)->String{bytes_value(self.as_bytes())}}
impl<T:Value> Value for Vec<T> {fn encode(&self)->String{self.as_slice().encode()}}
pub fn str_eq(a:&[u8],b:&[u8])->bool{let p=a==b;record("STREQ",p,&[bytes_value(a),bytes_value(b)]);p}
pub fn eq_refs<A:PartialEq<B>+Value+?Sized,B:Value+?Sized>(a:&A,b:&B)->bool{let p=a==b;record("EQ",p,&[a.encode(),b.encode()]);p}
impl<T:Value,const N:usize> Value for crate::numeric_vectors::V<T,N>{fn encode(&self)->String{self.0.encode()}}
impl<T:Value,const C:usize,const R:usize> Value for crate::matrix_types::M<T,C,R>{fn encode(&self)->String{self.0.encode()}}
pub fn record(kind:&str,passed:bool,values:&[String]) {
 TAPE.with(|t|{let mut t=t.borrow_mut();let line=format!("{{\"case\":\"{}\",\"kind\":\"{}\",\"passed\":{},\"values\":[{}]}}\n",t.0,kind,passed,values.join(","));t.1.push_str(&line);});
}
pub fn eq<T:PartialEq+Value>(a:T,b:T)->bool {let p=a==b;record("EQ",p,&[a.encode(),b.encode()]);p}
pub fn le<T:PartialOrd+Value>(a:T,b:T)->bool{let p=a<=b;record("LE",p,&[a.encode(),b.encode()]);p}
pub fn pointer_pair(a:*const u8,b:*const u8)->bool {
 let origin=if a.is_null(){b}else{a};
 let encode=|p:*const u8|format!("\"palias:{}\"",if p.is_null(){"null"}else if p==origin{"a"}else{"b"});
 let passed=a==b;record("EQ",passed,&[encode(a),encode(b)]);passed
}
pub fn lt<T:PartialOrd+Value>(a:T,b:T)->bool{let p=a<b;record("LT",p,&[a.encode(),b.encode()]);p}
pub fn gt<T:PartialOrd+Value>(a:T,b:T)->bool {let p=a>b;record("GT",p,&[a.encode(),b.encode()]);p}
pub fn boolean(kind:&str,v:bool)->bool {let p=if kind=="FALSE"{!v}else{v};record(kind,p,&[v.encode()]);p}
// These predicates reproduce the helpers in the pinned tests, including the older
// pinned GoogleTest's infinity behaviour, not the latest upstream documentation.
pub fn float_eq(a:f32,b:f32)->bool {
 fn ordered(v:f32)->u32{let n=v.to_bits();if n&0x80000000!=0{(!n).wrapping_add(1)}else{n|0x80000000}}
 let p=!a.is_nan()&&!b.is_nan()&&ordered(a).abs_diff(ordered(b))<=4;
 record("FLOAT_EQ",p,&[a.encode(),b.encode()]);p
}
pub fn near(a:f64,b:f64,e:f64)->bool {let p=(a-b).abs()<=e;record("NEAR",p,&[a.encode(),b.encode(),e.encode()]);p}
fn start(id:&str){TAPE.with(|t|t.borrow_mut().0=id.into());POINTER_ORIGIN.with(|p|*p.borrow_mut()=None);BYTE_POINTER_ORIGIN.with(|p|*p.borrow_mut()=None);record("CASE_BEGIN",true,&[]);}
fn end(passed:bool){record("CASE_END",passed,&[]);assert!(passed,"Port case failed");}
pub fn run_all()->String {
 TAPE.with(|t|*t.borrow_mut()=(String::new(),String::new()));
 for ((id,_),run) in crate::compat_cases::CASES.iter().zip(crate::compat_cases::REPORTS){start(id);end(run().passed());}
 for (id,run) in crate::additional_cases::CASES{start(id);end(run().passed());}
 for (id,run,count) in crate::structure_cases::CASES{start(id);let r=run();end(r.passed() && r.assertions==*count);}
 for (id,run,count) in crate::collection_cases::CASES{start(id);let r=run();end(r.passed() && r.assertions==*count);}
 for (id,run,count) in crate::string_ref_cases::CASES{start(id);let r=run();end(r.passed() && r.assertions==*count);}
 for (id,run,count) in crate::bit_span_cases::CASES{start(id);let r=run();end(r.passed() && r.assertions==*count);}
 for (id,run,count) in crate::numeric_type_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}
 for (id,run,count) in crate::matrix_type_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}
 for (id,run,count) in crate::geometry_math_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}
 for (id,run,count) in crate::sampling_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}
 for (id,run,count) in crate::curve_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}
 for (id,run,count) in crate::heap_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}
 for (id,run,n) in crate::data_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}
 for (id,run,n) in crate::string_ops_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}
 for (id,run,n) in crate::utf8_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}
 for (id,run,n) in crate::pixel_format_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}
 TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))
}
thread_local!{static OUTPUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn blended_fidelity_run()->usize{let s=run_all();let n=s.len();OUTPUT.with(|o|*o.borrow_mut()=s.into_bytes());n}
#[unsafe(no_mangle)]pub extern "C" fn blended_fidelity_ptr()->*const u8{OUTPUT.with(|o|o.borrow().as_ptr())}
