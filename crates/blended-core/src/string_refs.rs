// SPDX-License-Identifier: GPL-3.0-or-later
//! Borrowed byte-string references matching the exercised Blender StringRef contracts.
//!
//! Indices and lengths count bytes, not Unicode characters. No UTF-8 validity is
//! required except when requesting UTF-8-safe truncation. References never allocate
//! or replace their backing storage; explicit owned conversions copy the bytes.
use std::io::{self, Write};
use core::ops::Index;

#[derive(Clone, Copy, Debug)]
pub struct StringRef<'a> { bytes: &'a [u8], start: usize, len: usize }
impl<'a> StringRef<'a> {
    pub const fn empty() -> Self { Self { bytes: &[], start: 0, len: 0 } }
    pub const fn from_bytes(bytes: &'a [u8]) -> Self { Self { bytes, start: 0, len: bytes.len() } }
    pub const fn from_cstr(bytes: &'a [u8]) -> Self {
        let mut len=0; while len<bytes.len() && bytes[len]!=0 {len+=1;}
        Self{bytes,start:0,len}
    }
    pub const fn from_cstr_len(bytes:&'a [u8],len:usize)->Self {
        assert!(len<=bytes.len(),"StringRef length exceeds backing storage");
        Self{bytes,start:0,len}
    }
    pub const fn from_bounds(bytes:&'a [u8],start:usize,end:usize)->Self {
        assert!(start<=end && end<=bytes.len(),"Invalid string pointer range");
        Self{bytes,start,len:end-start}
    }
    pub const fn size(self)->i64 { self.len as i64 }
    pub const fn is_empty(self)->bool {self.len==0}
    pub fn data(self)->*const u8 {self.bytes.as_ptr().wrapping_add(self.start)}
    pub const fn at(self,index:usize)->u8 {assert!(index<self.len);self.bytes[self.start+index]}
    pub fn as_bytes(self)->&'a [u8] {&self.bytes[self.start..self.start+self.len]}
    pub fn iter(self)->impl Iterator<Item=u8>+'a {self.as_bytes().iter().copied()}
    pub fn to_owned_bytes(self)->Bytes {Bytes::from_slice(self.as_bytes())}
    pub fn write_to(self,out:&mut impl Write)->io::Result<()> {out.write_all(self.as_bytes())}
    pub const fn find_first_of(self,byte:u8)->i64 {
        let mut i=0;while i<self.len {if self.bytes[self.start+i]==byte{return i as i64;}i+=1;}-1
    }
    pub fn startswith(self,prefix:&[u8])->bool {self.as_bytes().starts_with(prefix)}
    pub fn endswith(self,suffix:&[u8])->bool {self.as_bytes().ends_with(suffix)}
    pub const fn drop_prefix(self,n:usize)->Self {
        let count=if n>self.len{self.len}else{n};Self{start:self.start+count,len:self.len-count,..self}
    }
    pub fn drop_known_prefix(self,prefix:&[u8])->Self {assert!(self.startswith(prefix));self.drop_prefix(prefix.len())}
    pub const fn drop_suffix(self,n:usize)->Self {Self{len:if n>self.len{0}else{self.len-n},..self}}
    pub const fn substr(self,start:usize,len:usize)->Self {
        assert!(start<=self.len,"Substring starts outside view");
        Self{start:self.start+start,len:if len>self.len-start{self.len-start}else{len},..self}
    }
    pub const fn substr_to_end(self,start:usize)->Self {self.substr(start,self.len)}
    pub fn trim_left_bytes(self,bytes:&[u8])->Self {
        let n=self.as_bytes().iter().take_while(|b|bytes.contains(b)).count();self.drop_prefix(n)
    }
    pub fn trim_right_bytes(self,bytes:&[u8])->Self {
        let n=self.as_bytes().iter().rev().take_while(|b|bytes.contains(b)).count();self.drop_suffix(n)
    }
    pub fn trim_bytes(self,bytes:&[u8])->Self {self.trim_left_bytes(bytes).trim_right_bytes(bytes)}
    pub fn trim_whitespace(self)->Self {self.trim_bytes(b" \t\n\r\x0b\x0c")}
    pub fn trim_left_whitespace(self)->Self {self.trim_left_bytes(b" \t\n\r\x0b\x0c")}
    pub fn trim_right_whitespace(self)->Self {self.trim_right_bytes(b" \t\n\r\x0b\x0c")}
    pub fn copy_bytes_truncated(self,dst:&mut [u8]) {
        assert!(!dst.is_empty(),"Destination needs space for a NUL byte");
        let n=self.len.min(dst.len()-1);dst[..n].copy_from_slice(&self.as_bytes()[..n]);dst[n]=0;
    }
    pub fn copy_utf8_truncated(self,dst:&mut [u8]) {
        assert!(!dst.is_empty(),"Destination needs space for a NUL byte");
        let bytes=self.as_bytes();let mut n=self.len.min(dst.len()-1);
        // Only back up when truncating through a UTF-8 continuation sequence. A
        // complete sequence at the end remains intact. Invalid bytes are not decoded.
        if n<bytes.len(){while n>0 && bytes[n]&0xc0==0x80{n-=1;}}
        dst[..n].copy_from_slice(&bytes[..n]);dst[n]=0;
    }
}
impl Index<usize> for StringRef<'_>{type Output=u8;fn index(&self,i:usize)->&u8{assert!(i<self.len);&self.bytes[self.start+i]}}
impl AsRef<[u8]> for StringRef<'_>{fn as_ref(&self)->&[u8]{self.as_bytes()}}
impl<T:AsRef<[u8]>+?Sized> PartialEq<T> for StringRef<'_>{fn eq(&self,other:&T)->bool{self.as_bytes()==other.as_ref()}}
impl Eq for StringRef<'_>{}

#[derive(Clone, Copy, Debug)]
pub struct StringRefNull<'a>(StringRef<'a>);
impl<'a> StringRefNull<'a>{
    pub const fn empty()->Self{Self(StringRef::from_cstr(b"\0"))}
    pub const fn from_cstr(bytes:&'a [u8])->Self{
        let view=StringRef::from_cstr(bytes);assert!(view.len<bytes.len(),"Missing NUL terminator");Self(view)
    }
    pub const fn from_cstr_len(bytes:&'a [u8],len:usize)->Self{
        assert!(len<bytes.len() && bytes[len]==0,"Expected NUL at the stated end");Self(StringRef::from_cstr_len(bytes,len))
    }
    pub const fn size(self)->i64{self.0.size()}
    pub const fn at(self,i:usize)->u8{assert!(i<=self.0.len);self.0.bytes[self.0.start+i]}
    pub fn data(self)->*const u8{self.0.data()}
    pub const fn find_first_of(self,byte:u8)->i64{self.0.find_first_of(byte)}
    pub fn as_bytes(self)->&'a[u8]{self.0.as_bytes()}
}
impl Index<usize> for StringRefNull<'_>{type Output=u8;fn index(&self,i:usize)->&u8{assert!(i<=self.0.len);&self.0.bytes[self.0.start+i]}}
impl AsRef<[u8]> for StringRefNull<'_>{fn as_ref(&self)->&[u8]{self.as_bytes()}}
impl<T:AsRef<[u8]>+?Sized> PartialEq<T> for StringRefNull<'_>{fn eq(&self,other:&T)->bool{self.as_bytes()==other.as_ref()}}
impl Eq for StringRefNull<'_>{}

#[derive(Clone,Debug,Default)]
pub struct Bytes(Vec<u8>);
impl Bytes{
    pub fn from_slice(bytes:&[u8])->Self{Self(bytes.to_vec())}
    pub fn data(&self)->*const u8{self.0.as_ptr()}
    pub fn size(&self)->i64{self.0.len() as i64}
}
impl AsRef<[u8]> for Bytes{fn as_ref(&self)->&[u8]{&self.0}}
impl<T:AsRef<[u8]>+?Sized> PartialEq<T> for Bytes{fn eq(&self,other:&T)->bool{self.0.as_slice()==other.as_ref()}}
impl Eq for Bytes{}
pub fn concat(a:&impl AsRef<[u8]>,b:&impl AsRef<[u8]>)->Bytes{
    let mut out=Vec::with_capacity(a.as_ref().len().checked_add(b.as_ref().len()).expect("String length overflow"));
    out.extend_from_slice(a.as_ref());out.extend_from_slice(b.as_ref());Bytes(out)
}
pub const fn array_with_first<const N:usize>(first:i32)->[i32;N]{assert!(N>0);let mut a=[0;N];a[0]=first;a}
