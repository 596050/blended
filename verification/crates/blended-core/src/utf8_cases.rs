// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Stress fixture derived by upstream from Markus Kuhn, 2015-08-28, CC BY 4.0.
// See tests/upstream/blender/BLI_string_utf8_test.cc for full source/attribution.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::utf8_compat as u;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,l:u32){self.assertions+=1;if !p{self.failures.push(format!("line {l}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(c_string($a)==c_string($b),stringify!($a C-string-equals $b),line!());}};}
fn c_string(a:&[u8])->&[u8]{&a[..a.iter().position(|&v|v==0).unwrap_or(a.len())]}
fn copy_call(dst:&mut[u8],src:&[u8],cap:usize,formatting:bool)->usize{
 if formatting{u::printf_s(dst,src,cap,true)}else{u::copy_into(dst,src,cap)}
}
// Each helper preserves the original macro's statement/loop/assertion order.
fn basic_copy(r:&mut Report,src:&[u8],formatting:bool){
 let mut dst=vec![255_u8;src.len()];copy_call(&mut dst,src,src.len(),formatting);
 eq!(r,c_string(&dst).len(),dst.len()-1);streq!(r,&dst,src);
}
fn truncate_encoding(r:&mut Report,size:i32,src:&[u8]){
 eq!(r,u::size_or_error(src[0]),size);
 let mut dst=vec![255_u8;src.len()];u::copy_into(&mut dst,src,src.len());
 eq!(r,c_string(&dst).len(),dst.len()-1);streq!(r,&dst,src);
 let cap=dst.len()-1;u::copy_into(&mut dst,src,cap);streq!(r,&dst,b"");
}
fn terminate_early(r:&mut Report,size:i32,src:&[u8],formatting:bool){
 let mut src=src.to_vec();eq!(r,u::size_or_error(src[0]),size);
 let mut dst=vec![255_u8;src.len()];copy_call(&mut dst,&src,src.len(),formatting);
 eq!(r,c_string(&dst).len(),dst.len()-1);streq!(r,&dst,&src);
 for i in (2..dst.len()).rev(){src[i]=0;dst.fill(255);let cap=dst.len();
  let n=copy_call(&mut dst,&src,cap,formatting);
  streq!(r,&dst,&src);eq!(r,c_string(&dst).len(),i);eq!(r,n,i);
 }
}
fn trunc_expect(r:&mut Report,src:&[u8],expected:&[u8],cap:usize,formatting:bool){
 let mut dst=vec![0_u8;cap+1];dst[cap]=255;
 let n=copy_call(&mut dst,src,cap,formatting);
 eq!(r,n,c_string(&dst).len());streq!(r,&dst,expected);eq!(r,dst[cap],255_u8);
}
// Do not append a NUL to unpadded input: boundary handling is what is tested.
fn as_char32(src:&[u8],limit:usize,dst:&mut[u32])->usize{
 let mut i=0;let mut n=0;
 while i<limit&&src[i]!=0{dst[n]=u::decode_step_safe(src,limit,&mut i);n+=1;}i
}
fn compare_pad(r:&mut Report,src:&[u8],padded_size:usize){
 let size=src.len();let mut padded=vec![0_u8;padded_size];padded[..size].copy_from_slice(src);
 let mut a=vec![u32::MAX;size];let mut b=vec![u32::MAX;size];let ia=as_char32(src,size,&mut a);
 for pass in 0..2{b.fill(u32::MAX);let ib=as_char32(&padded,if pass==1{size}else{padded_size},&mut b);
  for i in 0..size{eq!(r,a[i],b[i]);}eq!(r,ia,ib);
 }
}
fn compare_padding(r:&mut Report,src:&[u8]){compare_pad(r,src,src.len()+1);compare_pad(r,src,src.len()+7);}
fn at_buffer_size(r:&mut Report,size:usize){
 let mut src=vec![0_u8;size];
 for i in 0..=255_i32{src.fill(i as u8);compare_padding(r,&src);
  if size>1{let mut mul=1_i32;while mul<256{
   for ofs in 1..size{src[ofs]=(i+(ofs as i32*mul)) as u8;}compare_padding(r,&src);
   for ofs in 1..size{src[ofs]=(i-(ofs as i32*mul)) as u8;}compare_padding(r,&src);mul*=2;
  }}
 }
 let mut rng=u::LegacyByteRng::new(1);
 for _ in 0..256{rng.fill(&mut src);compare_padding(r,&src);}
}

const INVALID_FIXTURES:&[(&[u8],&[u8],i32)]=&[
(b"You should see the Greek word 'kosme':       \x22\xce\xba\xe1\xbd\xb9\xcf\x83\xce\xbc\xce\xb5\x22                    |\x00",b"You should see the Greek word 'kosme':       \x22\xce\xba\xe1\xbd\xb9\xcf\x83\xce\xbc\xce\xb5\x22                    |\x00",0),
(b"2.1.1  1 byte  (U-00000000):        \x22\x00\x22                                       |\x00",b"2.1.1  1 byte  (U-00000000):        \x22\x22                                       |\x00",1),
(b"2.1.2  2 bytes (U-00000080):        \x22\xc2\x80\x22                                      |\x00",b"2.1.2  2 bytes (U-00000080):        \x22\xc2\x80\x22                                      |\x00",0),
(b"2.1.3  3 bytes (U-00000800):        \x22\xe0\xa0\x80\x22                                     |\x00",b"2.1.3  3 bytes (U-00000800):        \x22\xe0\xa0\x80\x22                                     |\x00",0),
(b"2.1.4  4 bytes (U-00010000):        \x22\xf0\x90\x80\x80\x22                                    |\x00",b"2.1.4  4 bytes (U-00010000):        \x22\xf0\x90\x80\x80\x22                                    |\x00",0),
(b"2.1.5  5 bytes (U-00200000):        \x22\xf8\x88\x80\x80\x80\x22                                   |\x00",b"2.1.5  5 bytes (U-00200000):        \x22\xf8\x88\x80\x80\x80\x22                                   |\x00",0),
(b"2.1.6  6 bytes (U-04000000):        \x22\xfc\x84\x80\x80\x80\x80\x22                                  |\x00",b"2.1.6  6 bytes (U-04000000):        \x22\xfc\x84\x80\x80\x80\x80\x22                                  |\x00",0),
(b"2.2.1  1 byte  (U-0000007F):        \x22\x7f\x22                                       |\x00",b"2.2.1  1 byte  (U-0000007F):        \x22\x7f\x22                                       |\x00",0),
(b"2.2.2  2 bytes (U-000007FF):        \x22\xdf\xbf\x22                                      |\x00",b"2.2.2  2 bytes (U-000007FF):        \x22\xdf\xbf\x22                                      |\x00",0),
(b"2.2.3  3 bytes (U-0000FFFF):        \x22\xef\xbf\xbf\x22                                     |\x00",b"2.2.3  3 bytes (U-0000FFFF):        \x22\x22                                     |\x00",3),
(b"2.2.4  4 bytes (U-001FFFFF):        \x22\xf7\xbf\xbf\xbf\x22                                    |\x00",b"2.2.4  4 bytes (U-001FFFFF):        \x22\xf7\xbf\xbf\xbf\x22                                    |\x00",0),
(b"2.2.5  5 bytes (U-03FFFFFF):        \x22\xfb\xbf\xbf\xbf\xbf\x22                                   |\x00",b"2.2.5  5 bytes (U-03FFFFFF):        \x22\xfb\xbf\xbf\xbf\xbf\x22                                   |\x00",0),
(b"2.2.6  6 bytes (U-7FFFFFFF):        \x22\xfd\xbf\xbf\xbf\xbf\xbf\x22                                  |\x00",b"2.2.6  6 bytes (U-7FFFFFFF):        \x22\xfd\xbf\xbf\xbf\xbf\xbf\x22                                  |\x00",0),
(b"2.3.1  U-0000D7FF = ed 9f bf = \x22\xed\x9f\xbf\x22                                          |\x00",b"2.3.1  U-0000D7FF = ed 9f bf = \x22\xed\x9f\xbf\x22                                          |\x00",0),
(b"2.3.2  U-0000E000 = ee 80 80 = \x22\xee\x80\x80\x22                                          |\x00",b"2.3.2  U-0000E000 = ee 80 80 = \x22\xee\x80\x80\x22                                          |\x00",0),
(b"2.3.3  U-0000FFFD = ef bf bd = \x22\xef\xbf\xbd\x22                                          |\x00",b"2.3.3  U-0000FFFD = ef bf bd = \x22\xef\xbf\xbd\x22                                          |\x00",0),
(b"2.3.4  U-0010FFFF = f4 8f bf bf = \x22\xf4\x8f\xbf\xbf\x22                                      |\x00",b"2.3.4  U-0010FFFF = f4 8f bf bf = \x22\xf4\x8f\xbf\xbf\x22                                      |\x00",0),
(b"2.3.5  U-00110000 = f4 90 80 80 = \x22\xf4\x90\x80\x80\x22                                      |\x00",b"2.3.5  U-00110000 = f4 90 80 80 = \x22\xf4\x90\x80\x80\x22                                      |\x00",0),
(b"3.1.1  First continuation byte 0x80: \x22\x80\x22                                      |\x00",b"3.1.1  First continuation byte 0x80: \x22\x22                                      |\x00",1),
(b"3.1.2  Last  continuation byte 0xbf: \x22\xbf\x22                                      |\x00",b"3.1.2  Last  continuation byte 0xbf: \x22\x22                                      |\x00",1),
(b"3.1.3  2 continuation bytes: \x22\x80\xbf\x22                                             |\x00",b"3.1.3  2 continuation bytes: \x22\x22                                             |\x00",2),
(b"3.1.4  3 continuation bytes: \x22\x80\xbf\x80\x22                                            |\x00",b"3.1.4  3 continuation bytes: \x22\x22                                            |\x00",3),
(b"3.1.5  4 continuation bytes: \x22\x80\xbf\x80\xbf\x22                                           |\x00",b"3.1.5  4 continuation bytes: \x22\x22                                           |\x00",4),
(b"3.1.6  5 continuation bytes: \x22\x80\xbf\x80\xbf\x80\x22                                          |\x00",b"3.1.6  5 continuation bytes: \x22\x22                                          |\x00",5),
(b"3.1.7  6 continuation bytes: \x22\x80\xbf\x80\xbf\x80\xbf\x22                                         |\x00",b"3.1.7  6 continuation bytes: \x22\x22                                         |\x00",6),
(b"3.1.8  7 continuation bytes: \x22\x80\xbf\x80\xbf\x80\xbf\x80\x22                                        |\x00",b"3.1.8  7 continuation bytes: \x22\x22                                        |\x00",7),
(b"3.1.9      \x22\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\x22 |\x00",b"3.1.9      \x22\x22 |\x00",64),
(b"3.2.1      \x22\xc0 \xc1 \xc2 \xc3 \xc4 \xc5 \xc6 \xc7 \xc8 \xc9 \xca \xcb \xcc \xcd \xce \xcf \xd0 \xd1 \xd2 \xd3 \xd4 \xd5 \xd6 \xd7 \xd8 \xd9 \xda \xdb \xdc \xdd \xde \xdf \x22 |\x00",b"3.2.1      \x22                                \x22 |\x00",32),
(b"3.2.2      \x22\xe0 \xe1 \xe2 \xe3 \xe4 \xe5 \xe6 \xe7 \xe8 \xe9 \xea \xeb \xec \xed \xee \xef \x22                                 |\x00",b"3.2.2      \x22                \x22                                 |\x00",16),
(b"3.2.3      \x22\xf0 \xf1 \xf2 \xf3 \xf4 \xf5 \xf6 \xf7 \x22                                                 |\x00",b"3.2.3      \x22        \x22                                                 |\x00",8),
(b"3.2.4      \x22\xf8 \xf9 \xfa \xfb \x22                                                         |\x00",b"3.2.4      \x22    \x22                                                         |\x00",4),
(b"3.2.4      \x22\xfc \xfd \x22                                                             |\x00",b"3.2.4      \x22  \x22                                                             |\x00",2),
(b"3.3.1  2-byte sequence with last byte missing (U+0000):     \x22\xc0\x22               |\x00",b"3.3.1  2-byte sequence with last byte missing (U+0000):     \x22\x22               |\x00",1),
(b"3.3.2  3-byte sequence with last byte missing (U+0000):     \x22\xe0\x80\x22              |\x00",b"3.3.2  3-byte sequence with last byte missing (U+0000):     \x22\x22              |\x00",2),
(b"3.3.3  4-byte sequence with last byte missing (U+0000):     \x22\xf0\x80\x80\x22             |\x00",b"3.3.3  4-byte sequence with last byte missing (U+0000):     \x22\x22             |\x00",3),
(b"3.3.4  5-byte sequence with last byte missing (U+0000):     \x22\xf8\x80\x80\x80\x22            |\x00",b"3.3.4  5-byte sequence with last byte missing (U+0000):     \x22\x22            |\x00",4),
(b"3.3.5  6-byte sequence with last byte missing (U+0000):     \x22\xfc\x80\x80\x80\x80\x22           |\x00",b"3.3.5  6-byte sequence with last byte missing (U+0000):     \x22\x22           |\x00",5),
(b"3.3.6  2-byte sequence with last byte missing (U-000007FF): \x22\xdf\x22               |\x00",b"3.3.6  2-byte sequence with last byte missing (U-000007FF): \x22\x22               |\x00",1),
(b"3.3.7  3-byte sequence with last byte missing (U-0000FFFF): \x22\xef\xbf\x22              |\x00",b"3.3.7  3-byte sequence with last byte missing (U-0000FFFF): \x22\x22              |\x00",2),
(b"3.3.8  4-byte sequence with last byte missing (U-001FFFFF): \x22\xf7\xbf\xbf\x22             |\x00",b"3.3.8  4-byte sequence with last byte missing (U-001FFFFF): \x22\x22             |\x00",3),
(b"3.3.9  5-byte sequence with last byte missing (U-03FFFFFF): \x22\xfb\xbf\xbf\xbf\x22            |\x00",b"3.3.9  5-byte sequence with last byte missing (U-03FFFFFF): \x22\x22            |\x00",4),
(b"3.3.10 6-byte sequence with last byte missing (U-7FFFFFFF): \x22\xfd\xbf\xbf\xbf\xbf\x22           |\x00",b"3.3.10 6-byte sequence with last byte missing (U-7FFFFFFF): \x22\x22           |\x00",5),
(b"3.4      \x22\xc0\xe0\x80\xf0\x80\x80\xf8\x80\x80\x80\xfc\x80\x80\x80\x80\xdf\xef\xbf\xf7\xbf\xbf\xfb\xbf\xbf\xbf\xfd\xbf\xbf\xbf\xbf\x22                                     |\x00",b"3.4      \x22\x22                                     |\x00",30),
(b"3.5.1  fe = \x22\xfe\x22                                                               |\x00",b"3.5.1  fe = \x22\x22                                                               |\x00",1),
(b"3.5.2  ff = \x22\xff\x22                                                               |\x00",b"3.5.2  ff = \x22\x22                                                               |\x00",1),
(b"3.5.3  fe fe ff ff = \x22\xfe\xfe\xff\xff\x22                                                   |\x00",b"3.5.3  fe fe ff ff = \x22\x22                                                   |\x00",4),
(b"4.1.1  U+002F     = c0 af             = \x22\xc0\xaf\x22                                  |\x00",b"4.1.1  U+002F     = c0 af             = \x22\x22                                  |\x00",2),
(b"4.1.2  U+002F     = e0 80 af          = \x22\xe0\x80\xaf\x22                                 |\x00",b"4.1.2  U+002F     = e0 80 af          = \x22\x22                                 |\x00",3),
(b"4.1.3  U+002F     = f0 80 80 af       = \x22\xf0\x80\x80\xaf\x22                                |\x00",b"4.1.3  U+002F     = f0 80 80 af       = \x22\x22                                |\x00",4),
(b"4.1.4  U+002F     = f8 80 80 80 af    = \x22\xf8\x80\x80\x80\xaf\x22                               |\x00",b"4.1.4  U+002F     = f8 80 80 80 af    = \x22\x22                               |\x00",5),
(b"4.1.5  U+002F     = fc 80 80 80 80 af = \x22\xfc\x80\x80\x80\x80\xaf\x22                              |\x00",b"4.1.5  U+002F     = fc 80 80 80 80 af = \x22\x22                              |\x00",6),
(b"4.2.1  U-0000007F = c1 bf             = \x22\xc1\xbf\x22                                  |\x00",b"4.2.1  U-0000007F = c1 bf             = \x22\x22                                  |\x00",2),
(b"4.2.2  U-000007FF = e0 9f bf          = \x22\xe0\x9f\xbf\x22                                 |\x00",b"4.2.2  U-000007FF = e0 9f bf          = \x22\x22                                 |\x00",3),
(b"4.2.3  U-0000FFFF = f0 8f bf bf       = \x22\xf0\x8f\xbf\xbf\x22                                |\x00",b"4.2.3  U-0000FFFF = f0 8f bf bf       = \x22\x22                                |\x00",4),
(b"4.2.4  U-001FFFFF = f8 87 bf bf bf    = \x22\xf8\x87\xbf\xbf\xbf\x22                               |\x00",b"4.2.4  U-001FFFFF = f8 87 bf bf bf    = \x22\x22                               |\x00",5),
(b"4.2.5  U+0000     = fc 83 bf bf bf bf = \x22\xfc\x83\xbf\xbf\xbf\xbf\x22                              |\x00",b"4.2.5  U+0000     = fc 83 bf bf bf bf = \x22\x22                              |\x00",6),
(b"4.3.1  U+0000     = c0 80             = \x22\xc0\x80\x22                                  |\x00",b"4.3.1  U+0000     = c0 80             = \x22\x22                                  |\x00",2),
(b"4.3.2  U+0000     = e0 80 80          = \x22\xe0\x80\x80\x22                                 |\x00",b"4.3.2  U+0000     = e0 80 80          = \x22\x22                                 |\x00",3),
(b"4.3.3  U+0000     = f0 80 80 80       = \x22\xf0\x80\x80\x80\x22                                |\x00",b"4.3.3  U+0000     = f0 80 80 80       = \x22\x22                                |\x00",4),
(b"4.3.4  U+0000     = f8 80 80 80 80    = \x22\xf8\x80\x80\x80\x80\x22                               |\x00",b"4.3.4  U+0000     = f8 80 80 80 80    = \x22\x22                               |\x00",5),
(b"4.3.5  U+0000     = fc 80 80 80 80 80 = \x22\xfc\x80\x80\x80\x80\x80\x22                              |\x00",b"4.3.5  U+0000     = fc 80 80 80 80 80 = \x22\x22                              |\x00",6),
(b"5.1.1  U+D800 = ed a0 80 = \x22\xed\xa0\x80\x22                                              |\x00",b"5.1.1  U+D800 = ed a0 80 = \x22\x22                                              |\x00",3),
(b"5.1.2  U+DB7F = ed ad bf = \x22\xed\xad\xbf\x22                                              |\x00",b"5.1.2  U+DB7F = ed ad bf = \x22\x22                                              |\x00",3),
(b"5.1.3  U+DB80 = ed ae 80 = \x22\xed\xae\x80\x22                                              |\x00",b"5.1.3  U+DB80 = ed ae 80 = \x22\x22                                              |\x00",3),
(b"5.1.4  U+DBFF = ed af bf = \x22\xed\xaf\xbf\x22                                              |\x00",b"5.1.4  U+DBFF = ed af bf = \x22\x22                                              |\x00",3),
(b"5.1.5  U+DC00 = ed b0 80 = \x22\xed\xb0\x80\x22                                              |\x00",b"5.1.5  U+DC00 = ed b0 80 = \x22\x22                                              |\x00",3),
(b"5.1.6  U+DF80 = ed be 80 = \x22\xed\xbe\x80\x22                                              |\x00",b"5.1.6  U+DF80 = ed be 80 = \x22\x22                                              |\x00",3),
(b"5.1.7  U+DFFF = ed bf bf = \x22\xed\xbf\xbf\x22                                              |\x00",b"5.1.7  U+DFFF = ed bf bf = \x22\x22                                              |\x00",3),
(b"5.2.1  U+D800 U+DC00 = ed a0 80 ed b0 80 = \x22\xed\xa0\x80\xed\xb0\x80\x22                           |\x00",b"5.2.1  U+D800 U+DC00 = ed a0 80 ed b0 80 = \x22\x22                           |\x00",6),
(b"5.2.2  U+D800 U+DFFF = ed a0 80 ed bf bf = \x22\xed\xa0\x80\xed\xbf\xbf\x22                           |\x00",b"5.2.2  U+D800 U+DFFF = ed a0 80 ed bf bf = \x22\x22                           |\x00",6),
(b"5.2.3  U+DB7F U+DC00 = ed ad bf ed b0 80 = \x22\xed\xad\xbf\xed\xb0\x80\x22                           |\x00",b"5.2.3  U+DB7F U+DC00 = ed ad bf ed b0 80 = \x22\x22                           |\x00",6),
(b"5.2.4  U+DB7F U+DFFF = ed ad bf ed bf bf = \x22\xed\xad\xbf\xed\xbf\xbf\x22                           |\x00",b"5.2.4  U+DB7F U+DFFF = ed ad bf ed bf bf = \x22\x22                           |\x00",6),
(b"5.2.5  U+DB80 U+DC00 = ed ae 80 ed b0 80 = \x22\xed\xae\x80\xed\xb0\x80\x22                           |\x00",b"5.2.5  U+DB80 U+DC00 = ed ae 80 ed b0 80 = \x22\x22                           |\x00",6),
(b"5.2.6  U+DB80 U+DFFF = ed ae 80 ed bf bf = \x22\xed\xae\x80\xed\xbf\xbf\x22                           |\x00",b"5.2.6  U+DB80 U+DFFF = ed ae 80 ed bf bf = \x22\x22                           |\x00",6),
(b"5.2.7  U+DBFF U+DC00 = ed af bf ed b0 80 = \x22\xed\xaf\xbf\xed\xb0\x80\x22                           |\x00",b"5.2.7  U+DBFF U+DC00 = ed af bf ed b0 80 = \x22\x22                           |\x00",6),
(b"5.2.8  U+DBFF U+DFFF = ed af bf ed bf bf = \x22\xed\xaf\xbf\xed\xbf\xbf\x22                           |\x00",b"5.2.8  U+DBFF U+DFFF = ed af bf ed bf bf = \x22\x22                           |\x00",6),
(b"5.3.1  U+FFFE = ef bf be = \x22\xef\xbf\xbe\x22                                              |\x00",b"5.3.1  U+FFFE = ef bf be = \x22\x22                                              |\x00",3),
(b"5.3.2  U+FFFF = ef bf bf = \x22\xef\xbf\xbf\x22                                              |\x00",b"5.3.2  U+FFFF = ef bf bf = \x22\x22                                              |\x00",3),
];

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:324
pub fn string__Utf8InvalidBytesStrip()->Report{let mut r=Report::default();
for &(src,expected,errors) in INVALID_FIXTURES{
 let mut buff=[0_u8;80];buff.copy_from_slice(src);let found=u::invalid_strip(&mut buff,79);
 eq!(r,found,errors);streq!(r,&buff,expected);
}
r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:343
pub fn string__Utf8InvalidBytesSubstitute()->Report{let mut r=Report::default();
for &(src,_,errors) in INVALID_FIXTURES{
 let mut buff=[0_u8;80];buff.copy_from_slice(src);let found=u::invalid_substitute(&mut buff,79,b'?');
 eq!(r,found,errors);eq!(r,u::invalid_byte(&buff,79),-1);eq!(r,c_string(&buff).len(),79_usize);
}
r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:360
pub fn string__Utf8InvalidBytesSubstitutePatterns()->Report{let mut r=Report::default();
{let mut buff=[0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),0);streq!(r,&buff,b"");}
{let mut buff=[65_u8,0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),0);streq!(r,&buff,b"A");}
{let mut buff=[255_u8,0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),1);streq!(r,&buff,b"?");}
{let mut buff=[224_u8,239_u8,0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),2);streq!(r,&buff,b"??");}
{let mut buff=[224_u8,65_u8,0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),1);streq!(r,&buff,b"?A");}
{let mut buff=[65_u8,239_u8,0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),1);streq!(r,&buff,b"A?");}
{let mut buff=[224_u8,65_u8,237_u8,0_u8];let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b'?'),2);streq!(r,&buff,b"?A?");}

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:395
pub fn string__StringNLenUTF8()->Report{let mut r=Report::default();
eq!(r,u::count_bytes(b"\x00",0).0,0_usize);
eq!(r,u::count_bytes(b"\x00",1).0,0_usize);
eq!(r,u::count_bytes(b"\xfc\x80\x80\x80\x80\x80\x00",6).0,1_usize);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:402
pub fn string__StringNLenUTF8_Incomplete()->Report{let mut r=Report::default();
let source=b"A\xc2\xaa\xe0\xa0\x80\xf0\x90\x80\x80\xf8\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00";let mut buf=[0_u8;22];
{buf.copy_from_slice(source);buf[0]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,0_usize);eq!(r,ofs,0_usize);}
{buf.copy_from_slice(source);buf[1]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,1_usize);eq!(r,ofs,1_usize);}
{buf.copy_from_slice(source);buf[2]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,2_usize);eq!(r,ofs,2_usize);}
{buf.copy_from_slice(source);buf[3]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,2_usize);eq!(r,ofs,3_usize);}
{buf.copy_from_slice(source);buf[4]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,3_usize);eq!(r,ofs,4_usize);}
{buf.copy_from_slice(source);buf[5]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,3_usize);eq!(r,ofs,5_usize);}
{buf.copy_from_slice(source);buf[6]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,3_usize);eq!(r,ofs,6_usize);}
{buf.copy_from_slice(source);buf[7]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,4_usize);eq!(r,ofs,7_usize);}
{buf.copy_from_slice(source);buf[8]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,4_usize);eq!(r,ofs,8_usize);}
{buf.copy_from_slice(source);buf[9]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,4_usize);eq!(r,ofs,9_usize);}
{buf.copy_from_slice(source);buf[10]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,4_usize);eq!(r,ofs,10_usize);}
{buf.copy_from_slice(source);buf[11]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,5_usize);eq!(r,ofs,11_usize);}
{buf.copy_from_slice(source);buf[12]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,5_usize);eq!(r,ofs,12_usize);}
{buf.copy_from_slice(source);buf[13]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,5_usize);eq!(r,ofs,13_usize);}
{buf.copy_from_slice(source);buf[14]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,5_usize);eq!(r,ofs,14_usize);}
{buf.copy_from_slice(source);buf[15]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,5_usize);eq!(r,ofs,15_usize);}
{buf.copy_from_slice(source);buf[16]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,6_usize);eq!(r,ofs,16_usize);}
{buf.copy_from_slice(source);buf[17]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,6_usize);eq!(r,ofs,17_usize);}
{buf.copy_from_slice(source);buf[18]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,6_usize);eq!(r,ofs,18_usize);}
{buf.copy_from_slice(source);buf[19]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,6_usize);eq!(r,ofs,19_usize);}
{buf.copy_from_slice(source);buf[20]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,6_usize);eq!(r,ofs,20_usize);}
{buf.copy_from_slice(source);buf[21]=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,6_usize);eq!(r,ofs,21_usize);}

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:455
pub fn string__StrCopyUTF8_ASCII()->Report{let mut r=Report::default();
basic_copy(&mut r,&[97_u8,0_u8],false);
basic_copy(&mut r,&[97_u8,98_u8,99_u8,0_u8],false);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:473
pub fn string__StrCopyUTF8_ASCII_Truncate()->Report{let mut r=Report::default();
{let mut src=[0_u8];let mut dst=[255_u8;1];u::copy_into(&mut dst,&src,1);let expected=core::cmp::min(src.len(),1)-1;src[expected]=0;eq!(r,c_string(&dst).len(),expected);streq!(r,&dst,&src);}
{let mut src=[65_u8,65_u8,65_u8,65_u8];let mut dst=[255_u8;4];u::copy_into(&mut dst,&src,3);let expected=core::cmp::min(src.len(),3)-1;src[expected]=0;eq!(r,c_string(&dst).len(),expected);streq!(r,&dst,&src);}

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:493
pub fn string__StrCopyUTF8_TruncateEncoding()->Report{let mut r=Report::default();
truncate_encoding(&mut r,6,&[252_u8,1_u8,1_u8,1_u8,1_u8,1_u8,0_u8]);
truncate_encoding(&mut r,5,&[248_u8,1_u8,1_u8,1_u8,1_u8,0_u8]);
truncate_encoding(&mut r,4,&[240_u8,1_u8,1_u8,1_u8,0_u8]);
truncate_encoding(&mut r,3,&[224_u8,1_u8,1_u8,0_u8]);
truncate_encoding(&mut r,2,&[192_u8,1_u8,0_u8]);
truncate_encoding(&mut r,1,&[96_u8,0_u8]);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:519
pub fn string__StrCopyUTF8_TruncateEncodingMulti()->Report{let mut r=Report::default();
trunc_expect(&mut r,b"A\x00",b"A",2,false);
trunc_expect(&mut r,b"A\x00",b"",1,false);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"\xc2\xaa",3,false);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"",2,false);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"",1,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"\xe0\xa0\x80",4,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80",5,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",4,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",6,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",5,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",4,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",7,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",6,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",5,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",4,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xc2\xaa\xc2\xaa\x00",b"\xc2\xaa\xc2\xaa",5,false);
trunc_expect(&mut r,b"\xc2\xaa\xc2\xaa\x00",b"\xc2\xaa",4,false);
trunc_expect(&mut r,b"\xc2\xaa\xc2\xaa\x00",b"\xc2\xaa",3,false);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"",2,false);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"",1,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"\xe0\xa0\x80\xe0\xa0\x80",7,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"\xe0\xa0\x80",6,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"\xe0\xa0\x80",5,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"\xe0\xa0\x80",4,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xe0\xa0\x80\xe0\xa0\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80\xf0\x90\x80\x80",9,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80",8,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80",7,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80",6,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80",5,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"",4,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\xf0\x90\x80\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80",11,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",10,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",9,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",8,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",7,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",6,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"",5,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"",4,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\xf8\x80\x80\x80\x80\x00",b"",1,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80",13,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",12,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",11,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",10,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",9,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",8,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",7,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"",6,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"",5,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"",4,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"",3,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"",2,false);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\xfc\x80\x80\x80\x80\x80\x00",b"",1,false);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:619
pub fn string__StrCopyUTF8_TerminateEncodingEarly()->Report{let mut r=Report::default();
terminate_early(&mut r,6,&[252_u8,1_u8,1_u8,1_u8,1_u8,1_u8,0_u8],false);
terminate_early(&mut r,5,&[248_u8,1_u8,1_u8,1_u8,1_u8,0_u8],false);
terminate_early(&mut r,4,&[240_u8,1_u8,1_u8,1_u8,0_u8],false);
terminate_early(&mut r,3,&[224_u8,1_u8,1_u8,0_u8],false);
terminate_early(&mut r,2,&[192_u8,1_u8,0_u8],false);
terminate_early(&mut r,1,&[96_u8,0_u8],false);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:658
pub fn string__StrPrintfUTF8_ASCII()->Report{let mut r=Report::default();
basic_copy(&mut r,&[97_u8,0_u8],true);
basic_copy(&mut r,&[97_u8,98_u8,99_u8,0_u8],true);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:676
pub fn string__StrPrintfUTF8_TerminateEncodingEarly()->Report{let mut r=Report::default();
terminate_early(&mut r,6,&[252_u8,1_u8,1_u8,1_u8,1_u8,1_u8,0_u8],true);
terminate_early(&mut r,5,&[248_u8,1_u8,1_u8,1_u8,1_u8,0_u8],true);
terminate_early(&mut r,4,&[240_u8,1_u8,1_u8,1_u8,0_u8],true);
terminate_early(&mut r,3,&[224_u8,1_u8,1_u8,0_u8],true);
terminate_early(&mut r,2,&[192_u8,1_u8,0_u8],true);
terminate_early(&mut r,1,&[96_u8,0_u8],true);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:709
pub fn string__StrPrintfUTF8_TruncateEncodingMulti()->Report{let mut r=Report::default();
trunc_expect(&mut r,b"A\x00",b"A",2,true);
trunc_expect(&mut r,b"A\x00",b"",1,true);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"\xc2\xaa",3,true);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"",2,true);
trunc_expect(&mut r,b"\xc2\xaa\x00",b"",1,true);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"\xe0\xa0\x80",4,true);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"",3,true);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"",2,true);
trunc_expect(&mut r,b"\xe0\xa0\x80\x00",b"",1,true);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"\xf0\x90\x80\x80",5,true);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",4,true);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",3,true);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",2,true);
trunc_expect(&mut r,b"\xf0\x90\x80\x80\x00",b"",1,true);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"\xf8\x80\x80\x80\x80",6,true);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",5,true);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",4,true);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",3,true);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",2,true);
trunc_expect(&mut r,b"\xf8\x80\x80\x80\x80\x00",b"",1,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"\xfc\x80\x80\x80\x80\x80",7,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",6,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",5,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",4,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",3,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",2,true);
trunc_expect(&mut r,b"\xfc\x80\x80\x80\x80\x80\x00",b"",1,true);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:764
pub fn string__Utf8OffsetFromIndex_ClampedIndex()->Report{let mut r=Report::default();
for text in [b"\x00".as_slice(),b"TEST\x00".as_slice(),b"A\x00".as_slice(),b"\xc2\xaa\x00".as_slice(),b"\xe0\xa0\x80\x00".as_slice(),b"\xf0\x90\x80\x80\x00".as_slice(),b"A\xc2\xaa\xe0\xa0\x80\xf0\x90\x80\x80\x00".as_slice(),b"\xf0\x90\x80\x80\xe0\xa0\x80\xc2\xaaA\x00".as_slice()]{
let len=c_string(text).len();let n=u::count_bytes(text,len).0;let ofs=u::offset_from_index(text,len,n);
eq!(r,u::offset_from_index(text,len,n+1),ofs);eq!(r,u::offset_from_index(text,len,n+10),ofs);}

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:873
pub fn string__Utf8AsUnicodeStep()->Report{let mut r=Report::default();
at_buffer_size(&mut r,1);
at_buffer_size(&mut r,2);
at_buffer_size(&mut r,3);
at_buffer_size(&mut r,4);
at_buffer_size(&mut r,5);
at_buffer_size(&mut r,6);
at_buffer_size(&mut r,7);
at_buffer_size(&mut r,8);
at_buffer_size(&mut r,9);
at_buffer_size(&mut r,10);
at_buffer_size(&mut r,11);
at_buffer_size(&mut r,12);

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:897
pub fn string__StrCursorStepNextUtf32Empty()->Report{let mut r=Report::default();

  let empty=&[0_u32];
  let len:usize=0;
  let mut pos:i32=0;
  no!(r,u::cursor_next32(empty, len, &mut pos));
  pos = 1;
  no!(r,u::cursor_next32(empty, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:913
pub fn string__StrCursorStepNextUtf32Single()->Report{let mut r=Report::default();

  let single=&[48_u32,0_u32];
  let len:usize=1;
  let mut pos:i32=0;
  yes!(r,u::cursor_next32(single, len, &mut pos) && pos == 1);
  no!(r,u::cursor_next32(single, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:929
pub fn string__StrCursorStepNextUtf32Simple()->Report{let mut r=Report::default();

  let simple=&[48_u32,49_u32,50_u32,0_u32];
  let len:usize=3;
  let mut pos:i32=0;
  yes!(r,u::cursor_next32(simple, len, &mut pos) && pos == 1);
  yes!(r,u::cursor_next32(simple, len, &mut pos) && pos == 2);
  no!(r,u::cursor_next32(simple, len - 1, &mut pos));
  yes!(r,u::cursor_next32(simple, len, &mut pos) && pos == 3);
  no!(r,u::cursor_next32(simple, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:947
pub fn string__StrCursorStepNextUtf32AllCombining()->Report{let mut r=Report::default();

  let allcombining=&[768_u32,768_u32,768_u32,0_u32];
  let len:usize=3;
  let mut pos:i32=0;
  yes!(r,u::cursor_next32(allcombining, len, &mut pos) && pos == 3);
  pos = 1;
  yes!(r,u::cursor_next32(allcombining, len, &mut pos) && pos == 3);
  pos = 2;
  yes!(r,u::cursor_next32(allcombining, len, &mut pos) && pos == 3);
  pos = 3;
  no!(r,u::cursor_next32(allcombining, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:967
pub fn string__StrCursorStepNextUtf32Complex()->Report{let mut r=Report::default();

                                                                
  let complex=&[768_u32,65_u32,768_u32,800_u32,66_u32,0_u32];
  let len:usize=5;
  let mut pos:i32=0;
  yes!(r,u::cursor_next32(complex, len, &mut pos) && pos == 1);
  pos = 1;
  yes!(r,u::cursor_next32(complex, len, &mut pos) && pos == 4);
  pos = 2;
  yes!(r,u::cursor_next32(complex, len, &mut pos) && pos == 4);
  pos = 3;
  yes!(r,u::cursor_next32(complex, len, &mut pos) && pos == 4);
  pos = 4;
  yes!(r,u::cursor_next32(complex, len, &mut pos) && pos == 5);
  pos = 5;
  no!(r,u::cursor_next32(complex, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:992
pub fn string__StrCursorStepNextUtf32Invalid()->Report{let mut r=Report::default();

                                                                                      
  let invalid=&[192_u32,768_u32,9_u32,768_u32,13_u32,768_u32,10_u32,768_u32,0_u32];
  let len:usize=8;
  let mut pos:i32=0;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 2);
  pos = 1;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 2);
  pos = 2;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 4);
  pos = 3;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 4);
  pos = 4;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 6);
  pos = 5;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 6);
  pos = 6;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 8);
  pos = 7;
  yes!(r,u::cursor_next32(invalid, len, &mut pos) && pos == 8);
  pos = 8;
  no!(r,u::cursor_next32(invalid, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1023
pub fn string__StrCursorStepPrevUtf32Empty()->Report{let mut r=Report::default();

  let empty=&[0_u32];
  let len:usize=0;
  let mut pos:i32=0;
  no!(r,u::cursor_prev32(empty, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1037
pub fn string__StrCursorStepPrevUtf32Single()->Report{let mut r=Report::default();

  let single=&[48_u32,0_u32];
  let len:usize=1;
  let mut pos:i32=1;
  yes!(r,u::cursor_prev32(single, len, &mut pos) && pos == 0);
  no!(r,u::cursor_prev32(single, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1052
pub fn string__StrCursorStepPrevUtf32Simple()->Report{let mut r=Report::default();

  let simple=&[48_u32,49_u32,50_u32,0_u32];
  let len:usize=3;
  let mut pos:i32=3;
  yes!(r,u::cursor_prev32(simple, len, &mut pos) && pos == 2);
  yes!(r,u::cursor_prev32(simple, len, &mut pos) && pos == 1);
  yes!(r,u::cursor_prev32(simple, len, &mut pos) && pos == 0);
  no!(r,u::cursor_prev32(simple, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1069
pub fn string__StrCursorStepPrevUtf32AllCombining()->Report{let mut r=Report::default();

  let allcombining=&[768_u32,768_u32,768_u32,0_u32];
  let len:usize=3;
  let mut pos:i32=3;
  yes!(r,u::cursor_prev32(allcombining, len, &mut pos) && pos == 0);
  pos = 2;
  yes!(r,u::cursor_prev32(allcombining, len, &mut pos) && pos == 0);
  pos = 1;
  yes!(r,u::cursor_prev32(allcombining, len, &mut pos) && pos == 0);
  pos = 0;
  no!(r,u::cursor_prev32(allcombining, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1089
pub fn string__StrCursorStepPrevUtf32Complex()->Report{let mut r=Report::default();

                                                                
  let complex=&[768_u32,65_u32,768_u32,800_u32,66_u32,0_u32];
  let len:usize=5;
  let mut pos:i32=5;
  yes!(r,u::cursor_prev32(complex, len, &mut pos) && pos == 4);
  pos = 4;
  yes!(r,u::cursor_prev32(complex, len, &mut pos) && pos == 1);
  pos = 3;
  yes!(r,u::cursor_prev32(complex, len, &mut pos) && pos == 1);
  pos = 2;
  yes!(r,u::cursor_prev32(complex, len, &mut pos) && pos == 1);
  pos = 1;
  yes!(r,u::cursor_prev32(complex, len, &mut pos) && pos == 0);
  pos = 0;
  no!(r,u::cursor_prev32(complex, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1114
pub fn string__StrCursorStepPrevUtf32Invalid()->Report{let mut r=Report::default();

                                                                                      
  let invalid=&[192_u32,768_u32,9_u32,768_u32,13_u32,768_u32,10_u32,768_u32,0_u32];
  let len:usize=8;
  let mut pos:i32=8;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 6);
  pos = 7;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 6);
  pos = 6;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 4);
  pos = 5;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 4);
  pos = 4;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 2);
  pos = 3;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 2);
  pos = 2;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 0);
  pos = 1;
  yes!(r,u::cursor_prev32(invalid, len, &mut pos) && pos == 0);
  pos = 0;
  no!(r,u::cursor_prev32(invalid, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1144
pub fn string__StrCursorStepNextUtf8Empty()->Report{let mut r=Report::default();

  let empty=b"\x00";
  let len:usize=0;
  let mut pos:i32=0;
  no!(r,u::cursor_next8(empty, len, &mut pos));
  pos = 1;
  no!(r,u::cursor_next8(empty, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1159
pub fn string__StrCursorStepNextUtf8Single()->Report{let mut r=Report::default();

  let single=b"0\x00";
  let len:usize=1;
  let mut pos:i32=0;
  yes!(r,u::cursor_next8(single, len, &mut pos) && pos == 1);
  no!(r,u::cursor_next8(single, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1174
pub fn string__StrCursorStepNextUtf8Simple()->Report{let mut r=Report::default();

  let simple=b"012\x00";
  let len:usize=3;
  let mut pos:i32=0;
  yes!(r,u::cursor_next8(simple, len, &mut pos) && pos == 1);
  yes!(r,u::cursor_next8(simple, len, &mut pos) && pos == 2);
  no!(r,u::cursor_next8(simple, len - 1, &mut pos));
  yes!(r,u::cursor_next8(simple, len, &mut pos) && pos == 3);
  no!(r,u::cursor_next8(simple, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1192
pub fn string__StrCursorStepNextUtf8AllCombining()->Report{let mut r=Report::default();

  let allcombining=b"\xcc\x80\xcc\x80\xcc\x80\x00";
  let len:usize=6;
  let mut pos:i32=0;
  yes!(r,u::cursor_next8(allcombining, len, &mut pos) && pos == 6);
  pos = 1;
  yes!(r,u::cursor_next8(allcombining, len, &mut pos) && pos == 6);
  pos = 2;
  yes!(r,u::cursor_next8(allcombining, len, &mut pos) && pos == 6);
  pos = 3;
  yes!(r,u::cursor_next8(allcombining, len, &mut pos) && pos == 6);
  pos = 4;
  yes!(r,u::cursor_next8(allcombining, len, &mut pos) && pos == 6);
  pos = 5;
  yes!(r,u::cursor_next8(allcombining, len, &mut pos) && pos == 6);
  pos = 6;
  no!(r,u::cursor_next8(allcombining, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1218
pub fn string__StrCursorStepNextUtf8AllComplex()->Report{let mut r=Report::default();

                                                                     
  let complex=b"\xcc\x80A\xc2\xa9\xcc\x80\xcc\xa0B\x00";
  let len:usize=10;
  let mut pos:i32=0;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 2);
  pos = 1;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 2);
  pos = 2;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 3);
  pos = 3;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 9);
  pos = 4;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 9);
  pos = 5;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 9);
  pos = 6;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 9);
  pos = 7;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 9);
  pos = 8;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 9);
  pos = 9;
  yes!(r,u::cursor_next8(complex, len, &mut pos) && pos == 10);
  pos = 10;
  no!(r,u::cursor_next8(complex, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1253
pub fn string__StrCursorStepNextUtf8Invalid()->Report{let mut r=Report::default();

                                                                         
  let invalid=b"\xc0\xcc\x80\x09\x0d\x0a\xcc\x80\x00";
  let len:usize=8;
  let mut pos:i32=0;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 3);
  pos = 1;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 3);
  pos = 2;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 3);
  pos = 3;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 4);
  pos = 4;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 5);
  pos = 5;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 8);
  pos = 6;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 8);
  pos = 7;
  eq!(r,if u::cursor_next8(invalid, len, &mut pos){pos}else{-1}, 8);
  pos = 8;
  no!(r,u::cursor_next8(invalid, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1284
pub fn string__StrCursorStepPrevUtf8Empty()->Report{let mut r=Report::default();

  let empty=b"\x00";
  let len:usize=0;
  let mut pos:i32=0;
  no!(r,u::cursor_prev8(empty, len, &mut pos));
  pos = 1;
  no!(r,u::cursor_prev8(empty, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1300
pub fn string__StrCursorStepPrevUtf8Single()->Report{let mut r=Report::default();

  let single=b"0\x00";
  let len:usize=1;
  let mut pos:i32=1;
  yes!(r,u::cursor_prev8(single, len, &mut pos) && pos == 0);
  no!(r,u::cursor_prev8(single, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1315
pub fn string__StrCursorStepPrevUtf8Simple()->Report{let mut r=Report::default();

  let simple=b"012\x00";
  let len:usize=3;
  let mut pos:i32=3;
  yes!(r,u::cursor_prev8(simple, len, &mut pos) && pos == 2);
  yes!(r,u::cursor_prev8(simple, len, &mut pos) && pos == 1);
  yes!(r,u::cursor_prev8(simple, len, &mut pos) && pos == 0);
  no!(r,u::cursor_prev8(simple, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1332
pub fn string__StrCursorStepPrevUtf8AllCombining()->Report{let mut r=Report::default();

  let allcombining=b"\xcc\x80\xcc\x80\xcc\x80\x00";
  let len:usize=6;
  let mut pos:i32=6;
  yes!(r,u::cursor_prev8(allcombining, len, &mut pos) && pos == 0);
  pos = 5;
  yes!(r,u::cursor_prev8(allcombining, len, &mut pos) && pos == 0);
  pos = 4;
  yes!(r,u::cursor_prev8(allcombining, len, &mut pos) && pos == 0);
  pos = 3;
  yes!(r,u::cursor_prev8(allcombining, len, &mut pos) && pos == 0);
  pos = 2;
  yes!(r,u::cursor_prev8(allcombining, len, &mut pos) && pos == 0);
  pos = 1;
  yes!(r,u::cursor_prev8(allcombining, len, &mut pos) && pos == 0);
  pos = 0;
  no!(r,u::cursor_prev8(allcombining, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1358
pub fn string__StrCursorStepPrevUtf8Complex()->Report{let mut r=Report::default();

                                                                     
  let complex=b"\xcc\x80A\xc2\xa9\xcc\x80\xcc\xa0B\x00";
  let len:usize=10;
  let mut pos:i32=10;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 9);
  pos = 9;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 3);
  pos = 8;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 3);
  pos = 7;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 3);
  pos = 6;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 3);
  pos = 5;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 3);
  pos = 4;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 3);
  pos = 3;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 2);
  pos = 2;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 0);
  pos = 1;
  yes!(r,u::cursor_prev8(complex, len, &mut pos) && pos == 0);
  pos = 0;
  no!(r,u::cursor_prev8(complex, len, &mut pos));

r
}

// source/blender/blenlib/tests/BLI_string_utf8_test.cc:1393
pub fn string__StrCursorStepPrevUtf8Invalid()->Report{let mut r=Report::default();

                                                                         
  let invalid=b"\xc0\xcc\x80\x09\x0d\x0a\xcc\x80\x00";
  let len:usize=8;
  let mut pos:i32=8;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 5);
  pos = 7;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 5);
  pos = 6;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 5);
  pos = 5;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 4);
  pos = 4;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 3);
  pos = 3;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 0);
  pos = 2;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 0);
  pos = 1;
  yes!(r,u::cursor_prev8(invalid, len, &mut pos) && pos == 0);
  pos = 0;
  no!(r,u::cursor_prev8(invalid, len, &mut pos));

r
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("string.Utf8InvalidBytesStrip",string__Utf8InvalidBytesStrip,156),
("string.Utf8InvalidBytesSubstitute",string__Utf8InvalidBytesSubstitute,234),
("string.Utf8InvalidBytesSubstitutePatterns",string__Utf8InvalidBytesSubstitutePatterns,14),
("string.StringNLenUTF8",string__StringNLenUTF8,3),
("string.StringNLenUTF8_Incomplete",string__StringNLenUTF8_Incomplete,44),
("string.StrCopyUTF8_ASCII",string__StrCopyUTF8_ASCII,4),
("string.StrCopyUTF8_ASCII_Truncate",string__StrCopyUTF8_ASCII_Truncate,4),
("string.StrCopyUTF8_TruncateEncoding",string__StrCopyUTF8_TruncateEncoding,24),
("string.StrCopyUTF8_TruncateEncodingMulti",string__StrCopyUTF8_TruncateEncodingMulti,216),
("string.StrCopyUTF8_TerminateEncodingEarly",string__StrCopyUTF8_TerminateEncodingEarly,63),
("string.StrPrintfUTF8_ASCII",string__StrPrintfUTF8_ASCII,4),
("string.StrPrintfUTF8_TerminateEncodingEarly",string__StrPrintfUTF8_TerminateEncodingEarly,63),
("string.StrPrintfUTF8_TruncateEncodingMulti",string__StrPrintfUTF8_TruncateEncodingMulti,81),
("string.Utf8OffsetFromIndex_ClampedIndex",string__Utf8OffsetFromIndex_ClampedIndex,16),
("string.Utf8AsUnicodeStep",string__Utf8AsUnicodeStep,1626112),
("string.StrCursorStepNextUtf32Empty",string__StrCursorStepNextUtf32Empty,2),
("string.StrCursorStepNextUtf32Single",string__StrCursorStepNextUtf32Single,2),
("string.StrCursorStepNextUtf32Simple",string__StrCursorStepNextUtf32Simple,5),
("string.StrCursorStepNextUtf32AllCombining",string__StrCursorStepNextUtf32AllCombining,4),
("string.StrCursorStepNextUtf32Complex",string__StrCursorStepNextUtf32Complex,6),
("string.StrCursorStepNextUtf32Invalid",string__StrCursorStepNextUtf32Invalid,9),
("string.StrCursorStepPrevUtf32Empty",string__StrCursorStepPrevUtf32Empty,1),
("string.StrCursorStepPrevUtf32Single",string__StrCursorStepPrevUtf32Single,2),
("string.StrCursorStepPrevUtf32Simple",string__StrCursorStepPrevUtf32Simple,4),
("string.StrCursorStepPrevUtf32AllCombining",string__StrCursorStepPrevUtf32AllCombining,4),
("string.StrCursorStepPrevUtf32Complex",string__StrCursorStepPrevUtf32Complex,6),
("string.StrCursorStepPrevUtf32Invalid",string__StrCursorStepPrevUtf32Invalid,9),
("string.StrCursorStepNextUtf8Empty",string__StrCursorStepNextUtf8Empty,2),
("string.StrCursorStepNextUtf8Single",string__StrCursorStepNextUtf8Single,2),
("string.StrCursorStepNextUtf8Simple",string__StrCursorStepNextUtf8Simple,5),
("string.StrCursorStepNextUtf8AllCombining",string__StrCursorStepNextUtf8AllCombining,7),
("string.StrCursorStepNextUtf8AllComplex",string__StrCursorStepNextUtf8AllComplex,11),
("string.StrCursorStepNextUtf8Invalid",string__StrCursorStepNextUtf8Invalid,9),
("string.StrCursorStepPrevUtf8Empty",string__StrCursorStepPrevUtf8Empty,2),
("string.StrCursorStepPrevUtf8Single",string__StrCursorStepPrevUtf8Single,2),
("string.StrCursorStepPrevUtf8Simple",string__StrCursorStepPrevUtf8Simple,4),
("string.StrCursorStepPrevUtf8AllCombining",string__StrCursorStepPrevUtf8AllCombining,7),
("string.StrCursorStepPrevUtf8Complex",string__StrCursorStepPrevUtf8Complex,11),
("string.StrCursorStepPrevUtf8Invalid",string__StrCursorStepPrevUtf8Invalid,9),
];
