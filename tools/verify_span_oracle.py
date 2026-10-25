#!/usr/bin/env python3
"""Differential checks against the pinned unedited C++ span header.

Supplemental corpus, not extra upstream cases or a memory-safety/ABI proof.
Addresses are compared as within-allocation offsets or actual alias relations.
Empty oversized views compare sizes/values, not out-of-view pointer locations.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
HEADER_SHA='10a4bf1b95358a4f8eafb18a728f3d2131f5a0cbf337648f44d010d11fd9ad60'
CPP=r'''
#include "BLI_span.hh"
#include <array>
#include <vector>
#include <iostream>
#include <cstring>
#include <cstdint>
using namespace blender;
std::vector<uint32_t> output;
void emit(int64_t x){output.push_back(uint32_t(x));}
void view(Span<int> s){emit(s.size());for(int x:s)emit(x);}
void mutable_view(MutableSpan<int> s){view(s);}
int main(){
 for(int n=0;n<=32;++n){
  std::array<int,96> storage;for(int i=0;i<96;++i)storage[i]=(i*17+n*3)%101-50;
  Span<int> s(storage.data(),n);MutableSpan<int> m(storage.data(),n);
  emit(s.size_in_bytes());emit(s.is_empty());view(s);
  for(int k=0;k<=n+6;++k){view(s.drop_front(k));view(s.drop_back(k));view(s.take_front(k));view(s.take_back(k));mutable_view(m.drop_front(k));mutable_view(m.drop_back(k));mutable_view(m.take_front(k));mutable_view(m.take_back(k));}
  for(int start=0;start<=n;++start){
   for(int len=0;len<=n-start;++len){auto a=s.slice(start,len);auto b=m.slice(start,len);view(a);mutable_view(b);emit(a.data()-storage.data());emit(b.data()-storage.data());}
   for(int len=0;len<=n+3;++len){view(s.slice_safe(start,len));mutable_view(m.slice_safe(start,len));}
  }
  for(int value=-55;value<=55;++value){emit(s.contains(value));emit(s.count(value));}
  emit(s.has_duplicates__linear_search());
  for(int i=0;i<n;++i){emit(s.first_index(s[i]));emit(s.last(i));emit(s.contains_ptr(storage.data()+i));}
  emit(s.contains_ptr(storage.data()+n));
  for(auto it=s.rbegin();it!=s.rend();++it)emit(*it);
  m.fill(7);view(s);m.reverse();view(s);
  for(int i=0;i<n;++i)storage[i]=i*5-17;
  view(s);m.reverse();view(s);
  std::vector<int> selected;for(int i=0;i<n;i+=3)selected.push_back(i);
  m.fill_indices(Span<int>(selected),-11);view(s);
  for(auto it=m.rbegin();it!=m.rend();++it)*it+=13;
  view(s);std::array<int,96> copy;for(int i=0;i<96;++i)copy[i]=90-i;
  m.copy_from(Span<int>(copy.data(),n));view(s);
 }
 for(int length=0;length<=8;++length){
  alignas(8) std::array<uint32_t,8> raw={0x01234567,0x89abcdef,0x00000000,0xffffffff,0x80000000,0x7fc12345,0x3f800000,0xdeadbeef};
  Span<uint32_t> words(raw.data(),length);auto bytes=words.cast<uint8_t>();auto shorts=words.cast<uint16_t>();
  emit(bytes.size());for(int64_t i=0;i<bytes.size();++i){uint8_t value;std::memcpy(&value,bytes.data()+i,1);emit(value);}
  emit(shorts.size());for(int64_t i=0;i<shorts.size();++i){uint16_t value;std::memcpy(&value,shorts.data()+i,2);emit(value);}
  auto roundtrip=shorts.cast<uint32_t>();emit(roundtrip.size());for(int64_t i=0;i<roundtrip.size();++i){uint32_t value;std::memcpy(&value,roundtrip.data()+i,4);emit(value);}
 }
 int a=2,b=5,c=8;std::array<int*,3> pointers={&a,&b,nullptr};
 MutableSpan<int*> mut(pointers);Span<const int*> read=mut;
 emit(read[0]==&a);pointers[0]=&c;emit(read[0]==&c);mut[1]=&a;emit(pointers[1]==&a);
 Span<int*> original=mut;auto floats=original.cast<float*>();emit(floats[0]==reinterpret_cast<float*>(&c));emit(floats[1]==reinterpret_cast<float*>(&a));emit(floats[2]==nullptr);
 for(uint32_t w:output){char b[4]={char(w),char(w>>8),char(w>>16),char(w>>24)};std::cout.write(b,4);}
 return std::cout?0:2;
}
'''
RUST=r'''
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
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args,root,log,stdout=None):
    if stdout:
        with stdout.open('wb') as stream:p=subprocess.run(args,cwd=root,stdout=stream,stderr=subprocess.PIPE,timeout=180)
        log.write_bytes(p.stderr)
    else:
        p=subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);log.write_bytes(p.stdout)
    if p.returncode:raise RuntimeError('Oracle command failed: '+str(args))
def run(output):
    from playwright.sync_api import sync_playwright
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    header=ROOT/'.upstream/blender/source/blender/blenlib/BLI_span.hh'
    if sha(header)!=HEADER_SHA:raise ValueError('Original span header changed')
    report={'status':'failed','complete_blender_test_port':False,'scope':'explicit supplementary span slicing, mutation, pointer and byte-cast corpus; not extra upstream cases','reference_commit':PIN,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'original_header_sha256':HEADER_SHA,'lengths':list(range(33)),'oversize_empty_pointer_addresses_compared':False,'memory_safety_or_abi_parity_proved':False}
    try:
        with tempfile.TemporaryDirectory(prefix='blended-span-oracle-') as d:
            root=Path(d);cpp=root/'original.cc';cpp.write_text(CPP);output.with_suffix('.original.cc').write_text(CPP);output.with_suffix('.rust-driver.rs').write_text(RUST)
            includes=[str(header.parent),str(ROOT/'.upstream/blender/intern/guardedalloc')]
            command(['g++','-std=c++20','-O2','-DNDEBUG',*['-I'+p for p in includes],str(cpp),'-o',str(root/'original')],root,output.with_suffix('.cpp-build.log'))
            reference=output.with_suffix('.reference.bin');command([str(root/'original')],root,output.with_suffix('.reference.log'),stdout=reference)
            # The declared C++ type trait succeeds, but the constructor body
            # fails when actually instantiated. Record, do not silently fix it.
            gap=root/'original_conversion_gap.cc'
            gap.write_text('#include "BLI_span.hh"\n#include <type_traits>\nusing namespace blender;\nstatic_assert(std::is_convertible_v<MutableSpan<int*>,MutableSpan<const int*>>);\nvoid instantiate(MutableSpan<int*> input){MutableSpan<const int*> output=input;(void)output;}\n')
            output.with_suffix('.conversion-gap.cc').write_text(gap.read_text())
            failed=subprocess.run(['g++','-std=c++20','-O2','-DNDEBUG',*['-I'+p for p in includes],'-c',str(gap),'-o',str(root/'gap.o')],cwd=root,capture_output=True,text=True,timeout=60)
            gaplog=output.with_suffix('.conversion-gap.log');gaplog.write_text(failed.stdout+failed.stderr)
            if failed.returncode==0 or 'BLI_span.hh' not in failed.stderr or 'static_cast' not in failed.stderr or 'int**' not in failed.stderr or 'static assertion failed' in failed.stderr:
                raise ValueError('Unexpected original constructor-gap result; review reference limitation')
            report['original_conversion_limit']={'trait_predicate':'accepted by original compiler','actual_constructor':'fails in unedited pinned header','conversion':'MutableSpan<int*> -> MutableSpan<const int*>','not_compared_as_executable_parity':True,'diagnostic_sha256':sha(gaplog)}
            for name in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
                source=ROOT/name
                if source.is_dir():shutil.copytree(source,root/name)
                else:shutil.copyfile(source,root/name)
            (root/'crates/blended-core/src/span_oracle.rs').write_text(RUST)
            with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod span_oracle;\n')
            examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
            (examples/'span_oracle.rs').write_text('use std::io::Write;fn main(){std::io::stdout().write_all(&blended_core::span_oracle::generate()).unwrap();}\n')
            native=output.with_suffix('.native.bin');command(['cargo','run','--locked','--quiet','-p','blended-core','--example','span_oracle'],root,output.with_suffix('.native.log'),stdout=native)
            if native.read_bytes()!=reference.read_bytes():raise ValueError('Native observations differ from original C++')
            command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
            wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();browser_path=output.with_suffix('.browser.bin')
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                n=page.evaluate('''async data=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports,n=w.span_oracle_run(),ptr=w.span_oracle_ptr();window.__spanOracle={w,n,ptr};return n;}''',base64.b64encode(wasm).decode())
                if n!=reference.stat().st_size:raise ValueError('Browser output size mismatch')
                with browser_path.open('wb') as stream:
                    for offset in range(0,n,262144):
                        count=min(262144,n-offset)
                        raw=page.evaluate('''({offset,count})=>{const{w,n,ptr}=window.__spanOracle;if(offset+count>n)throw Error('bounds');let s='';const b=new Uint8Array(w.memory.buffer,ptr+offset,count);for(let i=0;i<b.length;i+=8192)s+=String.fromCharCode(...b.subarray(i,i+8192));return btoa(s);}''',{'offset':offset,'count':count})
                        block=base64.b64decode(raw,validate=True)
                        if len(block)!=count:raise ValueError('Truncated browser output')
                        stream.write(block)
                report.update(browser_version=browser.version,browser_errors=errors);browser.close()
                if errors:raise ValueError('Browser execution errors')
            if browser_path.read_bytes()!=reference.read_bytes():raise ValueError('Browser observations differ from original C++')
            report.update(status='passed',native='exact_match',browser='exact_match',output_words=reference.stat().st_size//4,output_bytes=reference.stat().st_size,reference_sha256=sha(reference),native_sha256=sha(native),browser_sha256=sha(browser_path),original_binary_sha256=sha(root/'original'),wasm_sha256=hashlib.sha256(wasm).hexdigest(),mode='local diagnostic original C++ versus native Rust/Chromium; production deployed test is separate')
    except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
