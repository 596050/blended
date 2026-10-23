// SPDX-License-Identifier: GPL-3.0-or-later
//! Borrowed byte-string views. UTF-8 truncation and byte truncation are distinct.
//! Trimming follows Blender's byte-set semantics, not Unicode whitespace rules.
use core::{fmt,ops::{Add,Deref,Index}};
#[derive(Debug,Clone,Copy)]
pub struct CString<'a>(&'a [u8]);
impl<'a>CString<'a>{
 pub const fn new(bytes:&'a [u8])->Self{assert!(!bytes.is_empty()&&bytes[bytes.len()-1]==0);Self(bytes)}
 pub const fn as_bytes(&self)->&'a[u8]{self.0}
 pub const fn as_ptr(&self)->*const u8{self.0.as_ptr()}
}
impl AsRef<[u8]> for CString<'_>{fn as_ref(&self)->&[u8]{self.0}}
#[derive(Debug,Clone,Copy,Default)]
pub struct StringRef<'a>{backing:&'a[u8],start:usize,length:usize}
impl<'a>StringRef<'a>{
 pub fn new<T:AsRef<[u8]>+?Sized>(input:&'a T)->Self{let bytes=input.as_ref();Self::with_length(bytes,bytes.iter().position(|b|*b==0).unwrap_or(bytes.len()))}
 pub const fn const_new(bytes:&'a[u8],length:usize)->Self{assert!(length<=bytes.len());Self{backing:bytes,start:0,length}}
 pub const fn with_length(bytes:&'a[u8],length:usize)->Self{Self::const_new(bytes,length)}
 pub const fn size(&self)->usize{self.length}
 pub const fn byte(&self,index:usize)->u8{assert!(index<self.length);self.backing[self.start+index]}
 pub const fn find_first_of(&self,byte:u8)->i64{let mut i=0;while i<self.length{if self.backing[self.start+i]==byte{return i as i64;}i+=1;} -1}
 pub fn data(&self)->*const u8{self.backing.as_ptr().wrapping_add(self.start)}
 pub fn as_bytes(&self)->&'a[u8]{&self.backing[self.start..self.start+self.length]}
 pub fn startswith<T:AsRef<[u8]>>(&self,other:T)->bool{self.as_bytes().starts_with(other.as_ref())}
 pub fn endswith<T:AsRef<[u8]>>(&self,other:T)->bool{self.as_bytes().ends_with(other.as_ref())}
 pub const fn substr(&self,start:usize,length:usize)->Self{assert!(start<=self.length);let remaining=self.length-start;Self{backing:self.backing,start:self.start+start,length:if length<remaining{length}else{remaining}}}
 pub const fn drop_prefix(&self,n:usize)->Self{let n=if n<self.length{n}else{self.length};self.substr(n,self.length-n)}
 pub const fn drop_suffix(&self,n:usize)->Self{let n=if n<self.length{n}else{self.length};self.substr(0,self.length-n)}
 pub fn drop_known_prefix<T:AsRef<[u8]>>(&self,prefix:T)->Self{let bytes=prefix.as_ref();assert!(self.as_bytes().starts_with(bytes));self.drop_prefix(bytes.len())}
 pub fn trim_left<T:AsRef<[u8]>>(&self,characters:T)->Self{let remove=characters.as_ref();let n=self.as_bytes().iter().take_while(|b|remove.contains(b)).count();self.drop_prefix(n)}
 pub fn trim_right<T:AsRef<[u8]>>(&self,characters:T)->Self{let remove=characters.as_ref();let n=self.as_bytes().iter().rev().take_while(|b|remove.contains(b)).count();self.drop_suffix(n)}
 pub fn trim<T:AsRef<[u8]>>(&self,characters:T)->Self{self.trim_left(characters.as_ref()).trim_right(characters.as_ref())}
 pub fn copy_bytes_truncated(&self,dst:&mut[u8]){assert!(!dst.is_empty());let n=self.length.min(dst.len()-1);dst[..n].copy_from_slice(&self.as_bytes()[..n]);dst[n]=0;}
 pub fn copy_utf8_truncated(&self,dst:&mut[u8]){
  assert!(!dst.is_empty());let data=self.as_bytes();let mut n=self.length.min(dst.len()-1);
  if n<self.length{while n>0&&(data[n]&0xc0)==0x80{n-=1;}}
  dst[..n].copy_from_slice(&data[..n]);dst[n]=0;
 }
}
impl AsRef<[u8]> for StringRef<'_>{fn as_ref(&self)->&[u8]{self.as_bytes()}}
impl Index<usize> for StringRef<'_>{type Output=u8;fn index(&self,i:usize)->&u8{assert!(i<self.length);&self.backing[self.start+i]}}
impl<T:AsRef<[u8]>+?Sized> PartialEq<T> for StringRef<'_>{fn eq(&self,other:&T)->bool{self.as_bytes()==other.as_ref()}}
impl Eq for StringRef<'_>{}
impl fmt::Display for StringRef<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{let text=core::str::from_utf8(self.as_bytes()).map_err(|_|fmt::Error)?;f.write_str(text)}}
#[derive(Debug,Clone,Copy)]
pub struct StringRefNull<'a>(StringRef<'a>);
impl<'a>StringRefNull<'a>{
 pub fn new(bytes:&'a[u8])->Self{let n=bytes.iter().position(|b|*b==0).expect("NUL terminator required");Self::const_new(bytes,n)}
 pub const fn with_length(bytes:&'a[u8],length:usize)->Self{Self::const_new(bytes,length)}
 pub const fn const_new(bytes:&'a[u8],length:usize)->Self{assert!(length<bytes.len()&&bytes[length]==0);Self(StringRef::const_new(bytes,length))}
 pub const fn size(&self)->usize{self.0.size()}
 pub const fn byte(&self,index:usize)->u8{assert!(index<=self.0.length);self.0.backing[self.0.start+index]}
 pub const fn find_first_of(&self,byte:u8)->i64{self.0.find_first_of(byte)}
}
impl Default for StringRefNull<'_>{fn default()->Self{Self::const_new(b"\0",0)}}
impl<'a>Deref for StringRefNull<'a>{type Target=StringRef<'a>;fn deref(&self)->&Self::Target{&self.0}}
impl AsRef<[u8]> for StringRefNull<'_>{fn as_ref(&self)->&[u8]{self.0.as_bytes()}}
impl Index<usize> for StringRefNull<'_>{type Output=u8;fn index(&self,i:usize)->&u8{assert!(i<=self.0.length);&self.0.backing[self.0.start+i]}}
impl<T:AsRef<[u8]>+?Sized> PartialEq<T> for StringRefNull<'_>{fn eq(&self,other:&T)->bool{self.0.as_bytes()==other.as_ref()}}
impl Eq for StringRefNull<'_>{}
macro_rules! reverse_eq{($t:ty)=>{
 impl PartialEq<StringRef<'_>> for $t{fn eq(&self,rhs:&StringRef<'_>)->bool{self.as_bytes()==rhs.as_bytes()}}
 impl PartialEq<StringRefNull<'_>> for $t{fn eq(&self,rhs:&StringRefNull<'_>)->bool{self.as_bytes()==rhs.as_bytes()}}
};}
reverse_eq!(&str);reverse_eq!(String);
impl<T:AsRef<[u8]>> Add<T> for StringRef<'_>{type Output=String;fn add(self,rhs:T)->String{let mut bytes=self.as_bytes().to_vec();bytes.extend_from_slice(rhs.as_ref());String::from_utf8(bytes).expect("UTF-8 string addition")}}
impl Add<StringRef<'_>> for &str{type Output=String;fn add(self,rhs:StringRef<'_>)->String{let mut s=self.to_owned();s.push_str(&rhs.to_string());s}}
impl Add<StringRef<'_>> for String{type Output=String;fn add(mut self,rhs:StringRef<'_>)->String{self.push_str(&rhs.to_string());self}}
