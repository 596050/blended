#!/usr/bin/env python3
"""Compare streaming/finalisation/reset behaviour with the unedited pinned C++.

Supplemental differential corpus, not new Blender tests. Exact same serialized
bytes and chunk plans are supplied to both implementations. The original hash
is endian-sensitive; native x86_64 and wasm32 here are little-endian targets.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES={'BLI_hash_mm2a.hh':'8c522a6ea1710d42780081a9485cafe916761d2494739d2eca39dfd19ad57bbf','intern/hash_mm2a.cc':'9f167fa2f586bd070c6ea04c11b8ebf258f841013c85ab7feaf9a1b4a062f331'}
SEEDS=(0,1,0xffffffff,0x12345678)
def corpus():
 records=[];lines=[]
 for seed in SEEDS:
  for length in range(65):
   raw=bytes(((i*73+length*19)^(i>>2))&255 for i in range(length))
   plans={(length,),(),(0,length,0)} if length==0 else {(length,),(0,length,0)}
   plans.update((i,length-i) for i in range(length+1))
   for width in (1,2,3,4,5,7,16):
    full,tail=divmod(length,width);plans.add((width,)*full+((tail,) if tail else ()))
   for plan in sorted(plans):
    if sum(plan)!=length:raise ValueError('Incorrect fixture plan')
    record={'seed':seed,'bytes_hex':raw.hex(),'chunks':list(plan)};records.append(record)
    lines.append(str(seed)+' '+(raw.hex() or '-')+' '+str(len(plan))+' '+ ' '.join(map(str,plan)))
 return '\n'.join(lines)+'\n',records
CPP=r'''// SPDX-License-Identifier: GPL-2.0-or-later
// Driver only. The complete original hash_mm2a.cc is compiled unedited.
#include "BLI_hash_mm2a.hh"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
int main(int argc,char**argv){
 if(argc!=2)return 2;std::ifstream file(argv[1]);if(!file)return 3;
 std::string line;std::cout<<'[';bool first=true;
 while(std::getline(file,line)){
  std::istringstream in(line);uint32_t seed;std::string hex;size_t chunks;
  if(!(in>>seed>>hex>>chunks))throw std::runtime_error("Malformed input");
  std::vector<unsigned char> bytes;
  if(hex!="-")for(size_t i=0;i<hex.size();i+=2)bytes.push_back(std::stoul(hex.substr(i,2),nullptr,16));
  // Non-null backing storage for empty adds; its contents are never read then.
  const size_t size=bytes.size();bytes.push_back(0);
  blender::BLI_HashMurmur2A h;blender::BLI_hash_mm2a_init(&h,seed);size_t offset=0;
  for(size_t i=0;i<chunks;++i){size_t count;if(!(in>>count)||count>size-offset)throw std::runtime_error("Invalid chunk");blender::BLI_hash_mm2a_add(&h,bytes.data()+offset,count);offset+=count;}
  if(offset!=size)throw std::runtime_error("Missing bytes");
  const uint32_t a=blender::BLI_hash_mm2a_end(&h),b=blender::BLI_hash_mm2a_end(&h);
  blender::BLI_hash_mm2a_init(&h,seed);blender::BLI_hash_mm2a_add(&h,bytes.data(),size);
  const uint32_t c=blender::BLI_hash_mm2a_end(&h);
  if(!first)std::cout<<',';first=false;std::cout<<'['<<a<<','<<b<<','<<c<<']';
 }
 std::cout<<"]\n";
}
'''
RUST=r'''// SPDX-License-Identifier: GPL-3.0-or-later
use crate::hash_mm2a::Murmur2A;
use std::cell::RefCell;
pub fn generate()->String{
 let mut output=String::from("[");
 for (ordinal,line) in include_str!("hash_streaming_inputs.txt").lines().enumerate(){
  let mut parts=line.split_whitespace();
  let seed:u32=parts.next().unwrap().parse().unwrap();let hex=parts.next().unwrap();let count:usize=parts.next().unwrap().parse().unwrap();
  let bytes:Vec<u8>=if hex=="-"{Vec::new()}else{(0..hex.len()).step_by(2).map(|i|u8::from_str_radix(&hex[i..i+2],16).unwrap()).collect()};
  let mut h=Murmur2A::new(seed);let mut offset=0;
  for _ in 0..count{let n:usize=parts.next().unwrap().parse().unwrap();h.add(&bytes[offset..offset+n]);offset+=n;}
  assert_eq!(offset,bytes.len());assert!(parts.next().is_none());
  let a=h.end();let b=h.end();h.reset(seed);h.add(&bytes);let c=h.end();
  if ordinal>0{output.push(',');}output.push_str(&format!("[{a},{b},{c}]"));
 }
 output.push(']');output
}
thread_local!{static OUTPUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn data_hash_probe_run()->usize{let s=generate();let n=s.len();OUTPUT.with(|o|*o.borrow_mut()=s.into_bytes());n}
#[unsafe(no_mangle)]pub extern "C" fn data_hash_probe_ptr()->*const u8{OUTPUT.with(|o|o.borrow().as_ptr())}
'''
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run_command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Reference/probe execution failed: '+str(args))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 base=ROOT/'.upstream/blender/source/blender/blenlib';text,records=corpus()
 report={'status':'failed','complete_blender_test_port':False,'scope':'supplemental differential hash corpus, not extra upstream cases','reference_commit':json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']['blender']['commit'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_hashes':SOURCES,'corpus_sha256':hashlib.sha256(text.encode()).hexdigest(),'configurations':len(records),'hash_results_per_configuration':3,'hash_result_count':len(records)*3,'seed_count':len(SEEDS),'lengths':'0 through 64 bytes inclusive','original_endianness_sensitive':True}
 try:
  for name,digest in SOURCES.items():
   if sha(base/name)!=digest:raise ValueError('Unreviewed original hash source '+name)
  output.with_suffix('.inputs.txt').write_text(text)
  output.with_suffix('.inputs.json').write_text(json.dumps(records,indent=2)+'\n')
  output.with_suffix('.driver.cc').write_text(CPP)
  with tempfile.TemporaryDirectory(prefix='blended-hash-differential-') as directory:
   root=Path(directory);(root/'driver.cc').write_text(CPP);(root/'inputs.txt').write_text(text)
   run_command(['g++','-std=c++20','-O2','-fno-strict-aliasing','-I'+str(base),str(root/'driver.cc'),str(base/'intern/hash_mm2a.cc'),'-o',str(root/'reference')],root,output.with_suffix('.reference-build.log'))
   reference=json.loads(run_command([str(root/'reference'),str(root/'inputs.txt')],root,output.with_suffix('.reference.json')))
   if len(reference)!=len(records):raise ValueError('Original reference omitted inputs')
   report['reference_binary_sha256']=sha(root/'reference')
   for name in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
    src=ROOT/name
    if src.is_dir():shutil.copytree(src,root/name)
    else:shutil.copyfile(src,root/name)
   src=root/'crates/blended-core/src';(src/'hash_streaming_probe.rs').write_text(RUST);(src/'hash_streaming_inputs.txt').write_text(text)
   with (src/'lib.rs').open('a') as f:f.write('\npub mod hash_streaming_probe;\n')
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);(examples/'hash_streaming_probe.rs').write_text('fn main(){println!("{}",blended_core::hash_streaming_probe::generate());}\n')
   raw=run_command(['cargo','run','--locked','--quiet','-p','blended-core','--example','hash_streaming_probe'],root,output.with_suffix('.native.log'));native=json.loads(raw);output.with_suffix('.native.json').write_text(raw)
   if native!=reference:raise ValueError('Native streaming, repeated-finaliser or reset results differ')
   run_command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
   wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes()
   with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page()
    raw=page.evaluate('''async data=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;const n=w.data_hash_probe_run(),ptr=w.data_hash_probe_ptr();return new TextDecoder().decode(new Uint8Array(w.memory.buffer,ptr,n));}''',base64.b64encode(wasm).decode())
    report['browser_version']=browser.version;browser.close()
   output.with_suffix('.browser.json').write_text(raw)
   if json.loads(raw)!=reference:raise ValueError('Browser streaming, repeated-finaliser or reset results differ')
   report.update(status='passed',native='exact_match',browser='exact_match',wasm_sha256=hashlib.sha256(wasm).hexdigest(),mode='diagnostic local original C++/Rust/WASM; production public verification separate')
 except Exception as e:
  report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
