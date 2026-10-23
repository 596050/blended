#!/usr/bin/env python3
"""Compare exact randomized inputs with pinned original C++ and real Rust/WASM.

Supplemental fixture verification, not additional upstream test cases. The C++
oracle uses original BLI_rand.hh and four unedited rand.cc functions. Only the
RNG wrapper's unused allocator hooks are omitted in the stack adapter.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
SEEDS=(0,1234,4321,9876,5321)
SHUFFLES=((1,1234),(2,1234),(100,4321),(1024,9876),(2048,5321))
SOURCE_HASHES={'BLI_rand.hh':'4226aa1b035ae085f87a3ac1c2467b7f2fc0235c354a5f2553e2cdd5cea82c82','intern/rand.cc':'aac6c52e01cf6271419bdbfd47a6ad140912432fd598d8330df82b9a039373f5'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def definition(text,signature):
 if text.count(signature)!=1:raise ValueError('Ambiguous original function '+signature)
 start=text.index(signature);begin=text.index('{',start);i=begin+1;depth=1
 while depth:
  if text[i]=='{':depth+=1
  elif text[i]=='}':depth-=1
  i+=1
 return text[start:i]
def cpp_source(root=ROOT):
 base=root/'.upstream/blender/source/blender/blenlib'
 for name,digest in SOURCE_HASHES.items():
  if sha(base/name)!=digest:raise ValueError('Original input generator changed '+name)
 text=(base/'intern/rand.cc').read_text()
 functions=[definition(text,s) for s in ('void BLI_rng_seed(', 'uint BLI_rng_get_uint(', 'void BLI_rng_shuffle_array(', 'void BLI_array_randomize(')]
 code='#include "BLI_rand.hh"\n#include <cstdlib>\n#include <cstring>\n#include <iostream>\n#include <vector>\nnamespace blender { struct RNG { RandomNumberGenerator rng; };\n'+'\n'.join(functions)+'\n}\n'
 code+='void print(const std::vector<int>&v){std::cout<<"[";for(size_t i=0;i<v.size();++i){if(i)std::cout<<",";std::cout<<v[i];}std::cout<<"]";}\nint main(){std::cout<<"[";std::cout<<"[";bool first=true;\n'
 for seed in SEEDS:code+=f'{{if(!first)std::cout<<",";first=false;blender::RandomNumberGenerator rng({seed}u);std::vector<int> v;for(int i=0;i<3000;++i)v.push_back(rng.get_int32());print(v);}}\n'
 code+='std::cout<<"],[";first=true;\n'
 for n,seed in SHUFFLES:code+=f'{{if(!first)std::cout<<",";first=false;std::vector<int> v({n});for(int i=0;i<{n};++i)v[i]=i;blender::BLI_array_randomize(v.data(),sizeof(int),{n},{seed}u);print(v);}}\n'
 code+='std::cout<<"]]\\n";}\n'
 return code

def rust_source():
 s='use crate::priority_heaps::{BlenderRng,array_randomize};\npub fn generate()->String {let mut sequences=Vec::new();\n'
 for seed in SEEDS:s+=f'{{let mut rng=BlenderRng::new({seed});sequences.push((0..3000).map(|_|rng.get_int32()).collect::<Vec<i32>>());}}\n'
 s+='let mut shuffles=Vec::new();\n'
 for n,seed in SHUFFLES:s+=f'{{let mut v:Vec<i32>=(0..{n}).collect();array_randomize(&mut v,{seed});shuffles.push(v);}}\n'
 s+='format!("[{:?},{:?}]",sequences,shuffles)}\n'
 s+='use std::cell::RefCell;thread_local!{static OUTPUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}\n#[unsafe(no_mangle)]pub extern "C" fn heap_inputs_run()->usize{let s=generate();let n=s.len();OUTPUT.with(|o|*o.borrow_mut()=s.into_bytes());n}\n#[unsafe(no_mangle)]pub extern "C" fn heap_inputs_ptr()->*const u8{OUTPUT.with(|o|o.borrow().as_ptr())}\n'
 return s

def command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Command failed; not a verified input match: '+str(args))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 evidence={'status':'failed','scope':'supplemental deterministic fixture verification, not upstream case count','complete_blender_test_port':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'original_source_hashes':SOURCE_HASHES,'rust_implementation_sha256':sha(ROOT/'crates/blended-core/src/priority_heaps.rs')}
 try:
  with tempfile.TemporaryDirectory(prefix='blended-heap-inputs-') as d:
   root=Path(d);src=root/'original.cc';src.write_text(cpp_source());shutil.copyfile(src,output.with_suffix('.original.cc'))
   base=ROOT/'.upstream/blender'
   command(['g++','-std=c++20','-O2','-DNDEBUG','-I'+str(base/'source/blender/blenlib'),'-I'+str(base/'intern/guardedalloc'),str(src),'-o',str(root/'original')],root,output.with_suffix('.cpp-build.log'))
   reference=json.loads(command([str(root/'original')],root,output.with_suffix('.reference.json')))
   for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
    p=ROOT/name
    if p.is_dir():shutil.copytree(p,root/name)
    else:shutil.copyfile(p,root/name)
   (root/'crates/blended-core/src/heap_input_probe.rs').write_text(rust_source())
   with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod heap_input_probe;\n')
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
   (examples/'heap_inputs.rs').write_text('fn main(){println!("{}",blended_core::heap_input_probe::generate());}\n')
   raw=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','heap_inputs'],root,output.with_suffix('.native.log'))
   native=json.loads(raw);output.with_suffix('.native.json').write_text(raw)
   if native!=reference:raise ValueError('Native randomized inputs differ from original C++')
   command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
   wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes()
   with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page()
    raw=page.evaluate('''async data=>{const {instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),x=>x.charCodeAt(0)),{});const w=instance.exports;const n=w.heap_inputs_run(),ptr=w.heap_inputs_ptr();return new TextDecoder().decode(new Uint8Array(w.memory.buffer,ptr,n));}''',base64.b64encode(wasm).decode())
    evidence['browser_version']=browser.version;browser.close()
   output.with_suffix('.browser.json').write_text(raw)
   if json.loads(raw)!=reference:raise ValueError('Browser randomized inputs differ from original C++')
   evidence.update(status='passed',native='exact_match',browser='exact_match',rng_values=15000,shuffled_items=sum(n for n,_ in SHUFFLES),seeds=list(SEEDS),shuffle_fixtures=[list(p) for p in SHUFFLES],wasm_sha256=hashlib.sha256(wasm).hexdigest(),mode='local compiled original C++ versus diagnostic native/WASM; production public tests are separate')
 except Exception as e:
  evidence['failure']=str(e);output.write_text(json.dumps(evidence,indent=2)+'\n');raise
 output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
