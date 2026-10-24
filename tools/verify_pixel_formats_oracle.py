#!/usr/bin/env python3
"""Bit-exact original-C++ oracle for a named scalar/SSE2 reference profile.

Supplemental evidence, not additional Blender cases. Half decoding is exhaustive;
float/normalised inputs are an explicit finite corpus, not all possible inputs.
"""
from __future__ import annotations
from pathlib import Path
import argparse, base64, hashlib, json, shutil, struct, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
HASHES={
 'intern/math_half.cc':'91a1cfc2f736da48c1ffb21a64901712a8549f1be822c01907cd72c61f4dc55d',
 'BLI_math_half.hh':'91e5404626be809de1b084aaa6dccbc104058b4aaeceb42cddf96b9b80b145aa',
 'BLI_normalized_int_types.hh':'b5f2e03d9b1b7cc00ca869613844017a427e5f91e5e902214a1a3f87a2a8d033',
 'BLI_simd.hh':'84af823ff645fcdc73080f109157b782560dfe24fa2ca9cd2002822901f56230',
}
FORMATS=(('char4_norm',4,8,True,256),('uchar4_norm',4,8,False,256),
 ('short2_norm',2,16,True,65536),('ushort2_norm',2,16,False,65536),
 ('short4_norm',4,16,True,0),('ushort4_norm',4,16,False,0),
 ('int1010102_norm',4,10,True,1024),('uint1010102_norm',4,10,False,1024))
TAIL_BITS=(0x7f800001,0xffc12345,0x00000000,0x80000000,0x33800000,0xb3800000,0x387fc000,
 0x38800000,0x477fe000,0xc77fe000,0x7f800000,0xff800000,0x3f801000,0x3f803000,
 0x3f800000,0xbf800000,0x00800000,0x00000001,0x7fffffff)
TAIL_HALF=(0x7c01,0xfe23,0x0000,0x8000,0x0001,0x8001,0x03ff,0x0400,0x7bff,0xfbff,
 0x7c00,0xfc00,0x3c01,0x3c02,0x3c00,0xbc00,0x0002,0x0003,0x7fff)
BOUNDS=((-10.0,1000.0),(1.0,2.0),(-2.0,-1.0))
def sha(path:Path)->str:
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def fbits(value:float)->int:return struct.unpack('<I',struct.pack('<f',value))[0]
def fvalue(bits:int)->float:return struct.unpack('<f',struct.pack('<I',bits))[0]
def half_value(bits:int)->float:
 # Only finite positive values used to generate input locations, not expectations.
 return struct.unpack('<e',struct.pack('<H',bits))[0]
def corpus():
 values=set()
 # Exact representable finite halves, and both neighbours of every rounding tie.
 for half in range(0x7c00):
  value=half_value(half);values.add(fbits(value));values.add(fbits(-value))
  upper=half_value(half+1) if half<0x7bff else 65536.0
  midpoint=fbits((value+upper)*0.5)
  for b in (midpoint-1,midpoint,midpoint+1):values.update((b,b|0x80000000))
 for exponent in range(256):
  for mantissa in (0,1,0xfff,0x1000,0x1001,0x3fffff,0x7fffff):
   b=(exponent<<23)|mantissa;values.update((b,b|0x80000000))
 # Explicit payload/sign variety, independent of Python NaN canonicalisation.
 values.update(TAIL_BITS)
 for payload in range(1,0x800000,0x4000):values.update((0x7f800000|payload,0xff800000|payload))
 state=0x13579bdf
 for _ in range(32768):
  state=(state*1664525+1013904223)&0xffffffff;values.add(state)
 floats=sorted(values)
 norm={fbits(x) for x in (0.0,-0.0,-2.0,-1.0,-0.9999999,-0.5,0.1,0.5,0.9999999,1.0,2.0,1e30,-1e30)}
 for i in range(-1024,1025):norm.add(fbits(i/512))
 for maximum in (1,3,127,255,511,1023,32767,65535):
  for i in (-maximum,-maximum+1,-2,-1,0,1,2,maximum-1,maximum):
   b=fbits(i/maximum);norm.add(b)
   if b&0x7fffffff:
    norm.update(((b-1)&0xffffffff,(b+1)&0xffffffff))
 normalised=sorted(norm)
 assert all(b&0x7f800000!=0x7f800000 for b in normalised)
 return floats,normalised

def input_bytes(floats,norm):
 return struct.pack('<I',len(floats))+b''.join(struct.pack('<I',v) for v in floats)+struct.pack('<I',len(norm))+b''.join(struct.pack('<I',v) for v in norm)

def sections(nf,nn):
 result=[];offset=0
 def add(name,count):
  nonlocal offset
  result.append({'name':name,'word_offset':offset,'word_count':count});offset+=count
 add('all_half_patterns_scalar_bits',65536)
 add('all_half_patterns_array_bits',65536)
 add('all_half_patterns_array_ftz_daz_bits',65536)
 add('float_scalar_half_and_finite',2*nf)
 add('float_array_half',nf);add('float_array_finite',nf)
 for i in range(3):add('float_array_clamp_'+str(i),nf)
 for rotate in range(4):
  for n in range(18):
   add(f'array_tail_{rotate}_{n}',6*20)
 for name,n,_,_,raw_count in FORMATS:
  add(name+'_float_encoding_and_decoding',nn*(2*n+2))
  if raw_count:add(name+'_all_raw_component_patterns',raw_count*2*n)
 return result

def cpp_driver():
 code=r'''// Supplemental driver. Original math_half.cc and normalised header are unedited.
#include "BLI_math_half.hh"
#include "BLI_normalized_int_types.hh"
#include "BLI_simd.hh"
#include <bit>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <immintrin.h>
using namespace blender;
std::vector<uint32_t> words;
void emit(uint32_t v){words.push_back(v);}
uint32_t read32(std::istream &s){unsigned char b[4];s.read((char*)b,4);if(!s)std::abort();return uint32_t(b[0])|(uint32_t(b[1])<<8)|(uint32_t(b[2])<<16)|(uint32_t(b[3])<<24);}
std::vector<float> read_vector(std::istream &s){auto n=read32(s);std::vector<float> v(n);for(auto &f:v)f=std::bit_cast<float>(read32(s));return v;}
template<class T,int N> void normalised(const std::vector<float>&input,int width,bool is_signed,uint32_t raw_count){
 using V=typename T::VecT;using I=typename T::IntVecT;
 for(size_t k=0;k<input.size();++k){V f;for(int j=0;j<N;++j)f[j]=input[(k+size_t(j)*17)%input.size()];T packed(f);I iv(packed);V decoded(packed);uint64_t storage=0;int shift=0;
 for(int j=0;j<N;++j){int w=(width==10&&j==3)?2:width;storage|=(uint64_t(uint32_t(iv[j]))&((uint64_t(1)<<w)-1))<<shift;shift+=w;emit(uint32_t(iv[j]));}
 for(int j=0;j<N;++j)emit(std::bit_cast<uint32_t>(decoded[j]));emit(uint32_t(storage));emit(uint32_t(storage>>32));}
 for(uint32_t raw=0;raw<raw_count;++raw){I fields;for(int j=0;j<N;++j){int w=(width==10&&j==3)?2:width;uint32_t v=(raw+uint32_t(j)*53)&((1u<<w)-1);int32_t signed_value=(is_signed&&(v&(1u<<(w-1))))?int32_t(v)-int32_t(1u<<w):int32_t(v);fields[j]=signed_value;}T packed(fields);I back(packed);V decoded(packed);for(int j=0;j<N;++j)emit(uint32_t(back[j]));for(int j=0;j<N;++j)emit(std::bit_cast<uint32_t>(decoded[j]));}
}
int main(int argc,char**argv){
 if(argc!=3)return 2;std::ifstream input(argv[1],std::ios::binary);auto floats=read_vector(input);auto norm=read_vector(input);if(input.peek()!=EOF)return 3;
 // Explicit baseline profile: nearest-even, gradual input denormals, exceptions masked.
 uint32_t saved=_mm_getcsr();_mm_setcsr(0x1f80);std::vector<uint16_t> halves(65536);for(uint32_t i=0;i<65536;++i){halves[i]=uint16_t(i);emit(std::bit_cast<uint32_t>(math::half_to_float(uint16_t(i))));}
 std::vector<float> decoded(65536);math::half_to_float_array(halves.data(),decoded.data(),halves.size());for(float v:decoded)emit(std::bit_cast<uint32_t>(v));
 uint32_t before=_mm_getcsr(),during=0,after=0;
 {ScopedFlushToZero guard;during=_mm_getcsr();if((during&0x8040)!=0x8040)return 4;math::half_to_float_array(halves.data(),decoded.data(),halves.size());for(float v:decoded)emit(std::bit_cast<uint32_t>(v));}
 after=_mm_getcsr();if(after!=before)return 5;
 for(float v:floats){emit(math::float_to_half(v));emit(math::float_to_half_make_finite(v));}
 std::vector<uint16_t> output(floats.size());math::float_to_half_array(floats.data(),output.data(),output.size());for(auto v:output)emit(v);
 math::float_to_half_make_finite_array(floats.data(),output.data(),output.size());for(auto v:output)emit(v);
'''
 for lo,hi in BOUNDS:code+=f'math::float_to_half_clamp_array(floats.data(),output.data(),output.size(),{lo}f,{hi}f);for(auto v:output)emit(v);\n'
 code+='const uint32_t tail_bits[]={'+','.join(hex(b)+'u' for b in TAIL_BITS)+'};\n'
 code+='const uint16_t tail_half[]={'+','.join(hex(b) for b in TAIL_HALF)+'};\n'
 code+=r'''
 for(size_t rotation=0;rotation<4;++rotation){float src[20];uint16_t hsrc[20];for(size_t i=0;i<20;++i){src[i]=std::bit_cast<float>(tail_bits[(i+rotation)%19]);hsrc[i]=tail_half[(i+rotation)%19];}
 for(size_t n=0;n<18;++n){std::vector<float> f(20,std::bit_cast<float>(0x41234567u));math::half_to_float_array(hsrc,f.data(),n);for(float v:f)emit(std::bit_cast<uint32_t>(v));
 std::vector<uint16_t> h(20,0xa55a);math::float_to_half_array(src,h.data(),n);for(auto v:h)emit(v);
 std::fill(h.begin(),h.end(),0xa55a);math::float_to_half_make_finite_array(src,h.data(),n);for(auto v:h)emit(v);
'''
 for lo,hi in BOUNDS:code+=f'std::fill(h.begin(),h.end(),0xa55a);math::float_to_half_clamp_array(src,h.data(),n,{lo}f,{hi}f);for(auto v:h)emit(v);\n'
 code+='}}\n'
 for name,n,w,sg,raw in FORMATS:code+=f'normalised<{name},{n}>(norm,{w},{str(sg).lower()},{raw});\n'
 code+=r'''
 _mm_setcsr(saved);std::ofstream result(argv[2],std::ios::binary);for(auto w:words){const char b[4]={char(w),char(w>>8),char(w>>16),char(w>>24)};result.write(b,4);}if(!result)return 6;
 std::cerr<<"{\"hardware_fp_control\":true,\"before\":"<<before<<",\"during\":"<<during<<",\"after\":"<<after<<",\"restored\":true,\"output_words\":"<<words.size()<<"}\n";
}
'''
 return code

def rust_driver():
 code=r'''// Diagnostic wrapper only; production implementation and original tests unchanged.
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
'''
 for lo,hi in BOUNDS:code+=f'm::float_to_half_clamp_array(&floats,&mut output,n,{lo}_f32,{hi}_f32);for &v in &output{{emit(&mut out,u32::from(v));}}\n'
 code+='let tail_bits=['+','.join(hex(b)+'_u32' for b in TAIL_BITS)+'];\n'
 code+='let tail_half=['+','.join(hex(b)+'_u16' for b in TAIL_HALF)+'];\n'
 code+=r'''
 for rotation in 0..4{let src:[f32;20]=core::array::from_fn(|i|f32::from_bits(tail_bits[(i+rotation)%19]));let hsrc:[u16;20]=core::array::from_fn(|i|tail_half[(i+rotation)%19]);
 for n in 0..18{let mut f=[f32::from_bits(0x41234567);20];m::half_to_float_array(&hsrc,&mut f,n);for v in f{emit(&mut out,v.to_bits());}
 let mut h=[0xa55a_u16;20];m::float_to_half_array(&src,&mut h,n);for v in h{emit(&mut out,u32::from(v));}
 h.fill(0xa55a);m::float_to_half_make_finite_array(&src,&mut h,n);for v in h{emit(&mut out,u32::from(v));}
'''
 for lo,hi in BOUNDS:code+=f'h.fill(0xa55a);m::float_to_half_clamp_array(&src,&mut h,n,{lo}_f32,{hi}_f32);for v in h{{emit(&mut out,u32::from(v));}}\n'
 code+='}}\n'
 for name,n,w,sg,raw in FORMATS:
  widths=[w]*(n-1)+[2 if w==10 else w]
  code+=f'norm(&mut out,&normalised,{str(widths)},{str(sg).lower()},{raw});\n'
 code+='out}\nuse std::cell::RefCell;thread_local!{static OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}\n#[unsafe(no_mangle)]pub extern "C" fn pixel_oracle_run()->usize{let v=generate();let n=v.len();OUT.with(|o|*o.borrow_mut()=v);n}\n#[unsafe(no_mangle)]pub extern "C" fn pixel_oracle_ptr()->*const u8{OUT.with(|o|o.borrow().as_ptr())}\n'
 return code

def compare_bytes(reference:Path,port:Path,layout):
 if port.stat().st_size!=reference.stat().st_size:raise ValueError('Truncated or extra oracle output')
 with reference.open('rb') as a,port.open('rb') as b:
  offset=0
  while raw:=a.read(1048576):
   got=b.read(len(raw))
   if raw!=got:
    k=next(i for i in range(0,len(raw),4) if raw[i:i+4]!=got[i:i+4]);index=(offset+k)//4
    section=next(s for s in layout if s['word_offset']<=index<s['word_offset']+s['word_count'])
    raise ValueError(f'Bit mismatch {section["name"]}, word {index-section["word_offset"]}: original={raw[k:k+4].hex()} replacement={got[k:k+4].hex()}')
   offset+=len(raw)
 return offset//4

def command(args,cwd,log,stdout=None):
 if stdout:
  with stdout.open('wb') as out:p=subprocess.run(args,cwd=cwd,stdout=out,stderr=subprocess.PIPE,timeout=240)
  log.write_bytes(p.stderr)
 else:
  p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240);log.write_bytes(p.stdout)
 if p.returncode:raise RuntimeError('Oracle execution failed, not a passing comparison: '+str(args))

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 evidence={'status':'failed','complete_blender_test_port':False,'scope':'supplemental bit-exact conversion corpus; not extra Blender test cases','reference_commit':PIN,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_hashes':HASHES,'reference_profile':'x86_64 scalar/SSE2 four-lane arrays, SSE4.1 clamp; nearest-even; no F16C/AVX or NEON'}
 try:
  source=ROOT/'.upstream/blender/source/blender/blenlib'
  for name,digest in HASHES.items():
   if sha(source/name)!=digest:raise ValueError('Original source changed '+name)
  floats,norm=corpus();data=input_bytes(floats,norm);input_path=output.with_suffix('.inputs.bin');input_path.write_bytes(data);layout=sections(len(floats),len(norm));expected_words=sum(s['word_count'] for s in layout)
  output.with_suffix('.layout.json').write_text(json.dumps(layout,indent=2)+'\n')
  with tempfile.TemporaryDirectory(prefix='blended-pixel-oracle-') as directory:
   root=Path(directory);cpp=root/'original.cc';cpp.write_text(cpp_driver());output.with_suffix('.original.cc').write_text(cpp.read_text())
   flags=['-std=c++20','-O2','-DNDEBUG','-msse4.1','-mno-avx','-mno-f16c','-fno-fast-math','-ffp-contract=off']
   command(['g++',*flags,'-I'+str(source),'-I'+str(ROOT/'.upstream/blender/intern/guardedalloc'),str(cpp),str(source/'intern/math_half.cc'),'-o',str(root/'original')],root,output.with_suffix('.cpp-build.log'))
   reference=output.with_suffix('.reference.bin');command([str(root/'original'),str(input_path),str(reference)],root,output.with_suffix('.reference.log'))
   cpp_environment=json.loads(output.with_suffix('.reference.log').read_text());assert reference.stat().st_size==expected_words*4
   for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
    p=ROOT/name
    if p.is_dir():shutil.copytree(p,root/name)
    else:shutil.copyfile(p,root/name)
   (root/'crates/blended-core/src/pixel_oracle.rs').write_text(rust_driver());(root/'crates/blended-core/src/pixel_oracle.inputs.bin').write_bytes(data)
   output.with_suffix('.rust-driver.rs').write_text(rust_driver())
   with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod pixel_oracle;\n')
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
   (examples/'pixel_oracle.rs').write_text('use std::io::Write;fn main(){assert!(blended_core::pixel_formats::ScopedFlushToZero::hardware_supported());std::io::stdout().write_all(&blended_core::pixel_oracle::generate()).unwrap();}\n')
   native=output.with_suffix('.native.bin');command(['cargo','run','--locked','--quiet','--release','-p','blended-core','--example','pixel_oracle'],root,output.with_suffix('.native.log'),stdout=native)
   compare_bytes(reference,native,layout)
   command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
   wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();browser_output=output.with_suffix('.browser.bin')
   with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    result=page.evaluate('''async data=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports,n=w.pixel_oracle_run(),ptr=w.pixel_oracle_ptr();window.__pixelOracle={w,n,ptr};return{bytes:n,hardware_fp_control:w.blended_pixel_formats_hardware_fp_control()};}''',base64.b64encode(wasm).decode())
    if result!={'bytes':expected_words*4,'hardware_fp_control':0}:raise ValueError('Browser output size/capability mismatch '+str(result))
    with browser_output.open('wb') as sink:
     for offset in range(0,result['bytes'],262144):
      count=min(262144,result['bytes']-offset)
      encoded=page.evaluate('''({offset,count})=>{const{w,n,ptr}=window.__pixelOracle;if(offset+count>n)throw Error('bounds');const v=new Uint8Array(w.memory.buffer,ptr+offset,count);let s='';for(let i=0;i<v.length;i+=8192)s+=String.fromCharCode(...v.subarray(i,i+8192));return btoa(s);}''',{'offset':offset,'count':count})
      raw=base64.b64decode(encoded,validate=True)
      if len(raw)!=count:raise ValueError('Truncated binary browser transfer')
      sink.write(raw)
    evidence.update(browser_version=browser.version,browser_errors=errors,browser_hardware_fp_control=False);browser.close()
    if errors:raise ValueError('Browser errors')
   compare_bytes(reference,browser_output,layout)
   evidence.update(status='passed',native='bit_exact_match',browser='bit_exact_match',all_half_patterns=65536,float_bit_inputs=len(floats),normalised_component_inputs=len(norm),output_u32_words=expected_words,output_bytes=expected_words*4,raw_normalised_component_patterns=sum(f[4] for f in FORMATS),array_lengths=list(range(18)),tail_rotations=4,clamp_bounds=BOUNDS,native_hardware_fp_control=True,reference_fp_control=cpp_environment,browser_fp_scope='Output check only; WebAssembly cannot set MXCSR. Native guard actually toggles/restores FTZ/DAZ.',compiler_flags=flags,corpus_sha256=sha(input_path),original_binary_sha256=sha(root/'original'),reference_output_sha256=sha(reference),native_output_sha256=sha(native),browser_output_sha256=sha(browser_output),wasm_sha256=hashlib.sha256(wasm).hexdigest(),mode='local diagnostic original C++/Rust/Chromium; production public URL verification is separate')
 except Exception as e:evidence['failure']=str(e);output.write_text(json.dumps(evidence,indent=2)+'\n');raise
 output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
