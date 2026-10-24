#!/usr/bin/env python3
"""Exact original-C++ polygon sequences for genuinely transformed inputs.

Supplemental differential checks, not extra upstream cases. The pinned original
TEST helper accidentally reuses the untransformed polygon; this corpus does not.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,struct,subprocess,tempfile
from port_polyfill_tests import ROOT,PIN,SOURCE,SHA,parse,extract
SOURCES=('intern/polyfill_2d.cc','intern/polyfill_2d_beautify.cc','intern/BLI_heap.cc','intern/BLI_memarena.cc','intern/math_geom.cc','BLI_math_geom_c.hh','intern/math_geom_inline.cc','BLI_math_vector_c.hh','intern/math_vector_inline.cc')
EXPECTED_HASHES={'intern/polyfill_2d.cc':'54627f28ba1dc29378f5c3fd0bdaddc0ee008eeccc50f5373c288d9f5c265d66','intern/polyfill_2d_beautify.cc':'ea328c820451911b312b13df02536ae240af5430b1db808a879c2196cfe9edd9','intern/BLI_heap.cc':'91bf514c89ccfe833346ddd7a4e1df72814bd38f9ecafc716f42c4edc2a0f7df','intern/BLI_memarena.cc':'b52c803d7b5e32a66a611621563812c68c4f10da8d2cf123c688fb50e92a51ce','intern/math_geom.cc':'68114c7b9742363686ab606c54791b2d745df3cb8c339aaac057397fd3c0c419','BLI_math_geom_c.hh':'ffca54ed739d6b5cdd5e687bbcde02201a0cdbbcc13fdc5f75e183b5b16fa0cf','intern/math_geom_inline.cc':'14fd1a90f4a4c5bc041b6343bb73c7cb57b1f41e1d4c44c987414da4a71452b3','BLI_math_vector_c.hh':'258fd71cd66927886b91ec313377e64f0963f2550788b112c8ec5683a04582f3','intern/math_vector_inline.cc':'15c60e8a6119fac59928921d0f7e3dc2a6b3489ccec5b54342c238ff749f9104'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args,root,log,stdout=None):
 if stdout:
  with stdout.open('wb') as stream:result=subprocess.run(args,cwd=root,stdout=stream,stderr=subprocess.PIPE,timeout=240)
  log.write_bytes(result.stderr)
 else:
  result=subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240);log.write_bytes(result.stdout)
 if result.returncode:raise RuntimeError('Oracle command failed, not passing comparison: '+str(args))

def original_inputs():
 raw=(ROOT/'.upstream/blender'/SOURCE).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Original fixture source changed')
 polygons=[];meta=[]
 for identity,body,line in extract(raw.decode()):
  coords,bits,flag,count=parse(body);polygons.append(bits);meta.append({'id':identity,'vertices':len(bits),'flag':flag,'source_line':line})
 data=struct.pack('<I',len(polygons))+b''.join(struct.pack('<I',len(p))+b''.join(struct.pack('<II',*v) for v in p) for p in polygons)
 return data,meta

def original_cross(root):
 text=(root/'intern/math_geom.cc').read_text();start=text.index('float cross_poly_v2(');end=text.index('\n}',start)+2
 return '#include "BLI_math_geom_c.hh"\nnamespace blender {\n'+text[start:end]+'\n}\n'

ALLOCATOR=r'''// Supplemental host-allocation bridge, not Blender guarded-allocation parity.
// Original ear clipping, beauty, heap and arena sources remain unedited.
#include "MEM_guardedalloc.h"
#include <cstdlib>
#include <cstring>
#include <limits>
#include <cstddef>
void *MEM_new_uninitialized(size_t n,const char*){void*p=std::malloc(n?n:1);if(!p)std::abort();return p;}
void *MEM_new_zeroed(size_t n,const char*){void*p=std::calloc(1,n?n:1);if(!p)std::abort();return p;}
static void *zero_aligned(size_t n,size_t s,size_t a,const char*){if(s&&n>std::numeric_limits<size_t>::max()/s)std::abort();if(a>alignof(std::max_align_t))std::abort();void*p=std::calloc(n?n:1,s?s:1);if(!p)std::abort();return p;}
static void *reallocate(void*p,size_t n,const char*){void*q=std::realloc(p,n?n:1);if(!q)std::abort();return q;}
static void release(void*p,mem_guarded::internal::DestructorType){std::free(p);}
void *(*MEM_new_array_zeroed_aligned)(size_t,size_t,size_t,const char*)=zero_aligned;
void *(*MEM_realloc_uninitialized_id)(void*,size_t,const char*)=reallocate;
void (*mem_guarded::internal::mem_freeN_ex)(void*,mem_guarded::internal::DestructorType)=release;
'''
CPP=r'''// GPL-3.0-or-later supplemental driver; original implementations linked unchanged.
#include "BLI_polyfill_2d.hh"
#include "BLI_polyfill_2d_beautify.hh"
#include "BLI_heap.hh"
#include "BLI_memarena.hh"
#include <array>
#include <vector>
#include <fstream>
#include <bit>
#include <cstdlib>
uint32_t read(std::istream&s){unsigned char b[4];s.read((char*)b,4);if(!s)std::abort();return uint32_t(b[0])|uint32_t(b[1])<<8|uint32_t(b[2])<<16|uint32_t(b[3])<<24;}
void write(std::ostream&s,uint32_t v){char b[4]={char(v),char(v>>8),char(v>>16),char(v>>24)};s.write(b,4);}
int main(int argc,char**argv){if(argc!=3)return 2;std::ifstream input(argv[1],std::ios::binary);std::ofstream out(argv[2],std::ios::binary);uint32_t total=read(input);
for(uint32_t k=0;k<total;++k){uint32_t n=read(input);std::vector<std::array<uint32_t,2>> base(n);for(auto&v:base){v[0]=read(input);v[1]=read(input);}
 for(uint32_t rev=0;rev<2;++rev)for(uint32_t cycle=0;cycle<n;++cycle)for(uint32_t fx=0;fx<2;++fx)for(uint32_t fy=0;fy<2;++fy){
  for(uint32_t v:{k,rev,cycle,fx,fy,n})write(out,v);
  std::vector<std::array<float,2>> points(n);for(uint32_t i=0;i<n;++i){uint32_t j=(i+cycle)%n;if(rev)j=n-1-j;auto a=base[j][0]^(fx<<31),b=base[j][1]^(fy<<31);points[i]={std::bit_cast<float>(a),std::bit_cast<float>(b)};write(out,a);write(out,b);}
  std::vector<std::array<uint32_t,3>> triangles(n-2);auto*p=reinterpret_cast<const float(*)[2]>(points.data());auto*t=reinterpret_cast<unsigned(*)[3]>(triangles.data());
  blender::BLI_polyfill_calc(p,n,0,t);for(auto&tri:triangles)for(auto v:tri)write(out,v);
  auto*a=blender::BLI_memarena_new(16384,"polygon oracle");auto*h=blender::BLI_heap_new();blender::BLI_polyfill_beautify(p,n,t,a,h);for(auto&tri:triangles)for(auto v:tri)write(out,v);blender::BLI_heap_free(h,nullptr);blender::BLI_memarena_free(a);
 }
}if(input.peek()!=EOF||!out)return 3;}
'''
RUST=r'''// Diagnostic driver only; production implementation and tests unchanged.
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
'''
NODE="""import fs from 'node:fs';const bytes=fs.readFileSync(process.argv[2]);const{instance}=await WebAssembly.instantiate(bytes,{});const w=instance.exports,n=w.polygon_probe_run(),ptr=w.polygon_probe_ptr();fs.writeFileSync(process.argv[3],Buffer.from(w.memory.buffer,ptr,n));console.log(JSON.stringify({runtime:process.version,bytes:n}));"""

def compare(reference,port,meta):
 a=reference.read_bytes();b=port.read_bytes()
 if len(a)!=len(b):raise ValueError('Different or truncated differential result length')
 offset=0;configurations=0;triangles=0;changed=0
 for case in meta:
  n=case['vertices'];words=8*n-6
  for rev in range(2):
   for cycle in range(n):
    for fx in range(2):
     for fy in range(2):
      end=offset+4*words
      if a[offset:end]!=b[offset:end]:
       mismatch=next(i for i in range(0,end-offset,4) if a[offset+i:offset+i+4]!=b[offset+i:offset+i+4])//4
       raise ValueError(f"Exact polygon output differs: {case['id']} reverse={rev}, cycle={cycle}, flip={fx},{fy}, word={mismatch}")
      start=offset+4*(6+2*n);middle=start+12*(n-2)
      if a[start:middle]!=a[middle:end]:changed+=1
      offset=end;configurations+=1;triangles+=2*(n-2)
 if offset!=len(a):raise ValueError('Unexpected trailing output words')
 return dict(configurations=configurations,triangulation_results=2*configurations,triangle_triplets=triangles,beautification_changed_outputs=changed,output_words=len(a)//4,output_sha256=hashlib.sha256(a).hexdigest())

def run(output,reference_only=False):
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 status={'status':'failed','complete_blender_test_port':False,'scope':'supplemental genuine polygon permutations, not extra upstream test cases','reference_commit':PIN,'source_hashes':EXPECTED_HASHES,'allocation_scope':'Unedited original algorithm, heap and arena; explicit host malloc/calloc bridge replaces guarded allocator, not allocator-parity evidence'}
 try:
  base=ROOT/'.upstream/blender/source/blender/blenlib'
  for name,digest in EXPECTED_HASHES.items():
   if sha(base/name)!=digest:raise ValueError('Original source mismatch '+name)
  data,meta=original_inputs();inputs=output.with_suffix('.inputs.bin');inputs.write_bytes(data);output.with_suffix('.cases.json').write_text(json.dumps(meta,indent=2)+'\n')
  with tempfile.TemporaryDirectory(prefix='blended-polygon-oracle-') as d:
   root=Path(d)
   for name,text in [('original.cc',CPP),('allocator.cc',ALLOCATOR),('cross.cc',original_cross(base))]:(root/name).write_text(text);output.with_suffix('.'+name).write_text(text)
   flags=['-std=c++20','-O2','-DNDEBUG','-ffunction-sections','-fdata-sections','-ffp-contract=off','-fno-fast-math']
   command(['g++',*flags,'-I'+str(base),'-I'+str(ROOT/'.upstream/blender/intern/guardedalloc'),str(root/'original.cc'),str(root/'allocator.cc'),str(root/'cross.cc'),*[str(base/name) for name in SOURCES[:4]],'-Wl,--gc-sections','-o',str(root/'original')],root,output.with_suffix('.cpp-build.log'))
   reference=output.with_suffix('.reference.bin');command([str(root/'original'),str(inputs),str(reference)],root,output.with_suffix('.reference.log'))
   status.update(compare(reference,reference,meta),corpus_sha256=sha(inputs),original_binary_sha256=sha(root/'original'),compiler_flags=flags)
   if reference_only:status.update(status='reference_generated',native='not_run',wasm='not_run')
   else:
    status['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    status['rust_implementation_sha256']=sha(ROOT/'crates/blended-core/src/polyfill.rs')
    for name in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
     p=ROOT/name
     if p.is_dir():shutil.copytree(p,root/name)
     else:shutil.copyfile(p,root/name)
    (root/'crates/blended-core/src/polyfill_probe.rs').write_text(RUST);(root/'crates/blended-core/src/polyfill_probe.inputs.bin').write_bytes(data)
    output.with_suffix('.rust-driver.rs').write_text(RUST);output.with_suffix('.node-driver.mjs').write_text(NODE)
    with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod polyfill_probe;\n')
    examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);(examples/'polyfill_probe.rs').write_text('use std::io::Write;fn main(){std::io::stdout().write_all(&blended_core::polyfill_probe::generate()).unwrap();}\n')
    native=output.with_suffix('.native.bin');command(['cargo','run','--locked','--release','--quiet','-p','blended-core','--example','polyfill_probe'],root,output.with_suffix('.native.log'),stdout=native);compare(reference,native,meta)
    command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
    wasm=root/'target/wasm32-unknown-unknown/release/blended_core.wasm';node=root/'run.mjs';node.write_text(NODE);wasm_result=output.with_suffix('.wasm.bin')
    command(['node',str(node),str(wasm),str(wasm_result)],root,output.with_suffix('.wasm.log'));compare(reference,wasm_result,meta)
    status.update(status='passed',native='exact_match',wasm='exact_match',wasm_runtime='Node.js, diagnostic module; production Chromium URL checks are separate',wasm_sha256=sha(wasm),native_output_sha256=sha(native),wasm_output_sha256=sha(wasm_result))
 except Exception as e:status['failure']=str(e);output.write_text(json.dumps(status,indent=2)+'\n');raise
 output.write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status,indent=2));return status
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference-only',action='store_true');a=p.parse_args();run(a.output,a.reference_only)
