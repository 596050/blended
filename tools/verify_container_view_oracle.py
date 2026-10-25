#!/usr/bin/env python3
"""Supplemental exact observations. Unordered key traversal is canonicalised;
within-key insertion order, real backing storage and pointer offsets are not.
The original clear_and_shrink declaration fails to instantiate, so this corpus
uses supported clear() on both targets and does not certify the former operation.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
LIMIT={'operation':'MultiValueMap<int,int>::clear_and_shrink()', 'original_instantiation':'fails: underlying Map has no clear_and_shrink member', 'equivalence_certified':False, 'corpus_clear_points':'supported clear() on both targets', 'failure_record':'evidence/container-oracle-reference-limit.json'}
RUST=r'''
use crate::container_views::{MultiValueMap,OwnedKey,GMutableSpan};use core::cell::Cell;
fn emit(out:&mut Vec<u8>,v:i64){out.extend_from_slice(&(v as u32).to_le_bytes());}
fn bucket(out:&mut Vec<u8>,v:&[i32]){emit(out,v.len() as i64);for &x in v{emit(out,x as i64);}}
fn snapshot(out:&mut Vec<u8>,m:&MultiValueMap<i32,i32>){emit(out,m.len() as i64);emit(out,i64::from(m.is_empty()));let mut keys:Vec<i32>=m.keys().copied().collect();keys.sort();emit(out,keys.len() as i64);for key in keys{emit(out,key as i64);bucket(out,m.lookup(&key));}
let mut values:Vec<Vec<i32>>=m.values().map(|v|v.to_vec()).collect();values.sort();emit(out,values.len() as i64);for v in values{bucket(out,&v);}
let mut items:Vec<(i32,Vec<i32>)>=m.items().map(|(&k,v)|(k,v.to_vec())).collect();items.sort();emit(out,items.len() as i64);for (key,v) in items{emit(out,key as i64);bucket(out,&v);}}
pub fn generate()->Vec<u8>{let mut out=Vec::new();emit(&mut out,0x43564f31);emit(&mut out,16);emit(&mut out,64);
for seed in 0..16{let mut map=MultiValueMap::<i32,i32>::new();for step in 0..64{let key=(step*7+seed*3)%11-5;let v=(step*13+seed*17)%53-26;
match step%8{0=>map.add(key,v),1=>map.add_multiple(key,&[v,v+1,v]),2=>map.add_multiple(key,&[]),3=>{map.add_non_duplicates(key,v);map.add_non_duplicates(key,v);},4=>{for(i,x)in map.lookup_mut(&key).iter_mut().enumerate(){*x+=i as i32+1;}},5=>{for(&k,values)in map.items_mut(){for x in values{*x+=k;}}},6=>bucket(&mut out,map.lookup(&999)),7=>{let copy=map.clone();map.add(key,v);snapshot(&mut out,&copy);if step==31||step==63{map.clear();}},_=>unreachable!()};snapshot(&mut out,&map);}}
for n in 0..=64{let values:[Cell<i32>;64]=core::array::from_fn(|i|Cell::new(i as i32*13-n as i32));let m=GMutableSpan::from_cells(&values[..n]);let s=m.as_readonly();emit(&mut out,s.len() as i64);emit(&mut out,(s.len()*s.descriptor().size()) as i64);emit(&mut out,i64::from(s.is_empty()));emit(&mut out,i64::from(s.typed::<i32>().is_ok()));
for i in 0..n{emit(&mut out,(s.pointer_at(i) as usize-values.as_ptr() as usize) as i64);emit(&mut out,s.typed::<i32>().unwrap().get(i) as i64);if i%2==1{unsafe{let p=m.pointer_at(i).cast::<i32>();p.write(p.read()+7);}}else{let v=m.typed::<i32>().unwrap();v.set(i,v.get(i)+7);}emit(&mut out,values[i].get() as i64);emit(&mut out,s.typed::<i32>().unwrap().get(i) as i64);}
for i in 0..n{values[i].set(-values[i].get());emit(&mut out,s.typed::<i32>().unwrap().get(i) as i64);}}
let bits=[0_u32,0x80000000,0x3f800000,0xbf800000,0x7f800000,0xff800000,0x7f812345,0x7fc12345];
for n in 0..=16{let values:[Cell<f32>;16]=core::array::from_fn(|i|Cell::new(f32::from_bits(bits[i%8])));let m=GMutableSpan::from_cells(&values[..n]);let s=m.as_readonly();emit(&mut out,s.len() as i64);emit(&mut out,(s.len()*s.descriptor().size()) as i64);emit(&mut out,i64::from(s.typed::<f32>().is_ok()));for i in 0..n{emit(&mut out,s.typed::<f32>().unwrap().get(i).to_bits() as i64);m.typed::<f32>().unwrap().set(i,f32::from_bits(bits[(i+3)%8]));emit(&mut out,values[i].get().to_bits() as i64);emit(&mut out,s.typed::<f32>().unwrap().get(i).to_bits() as i64);}}
let mut owned=MultiValueMap::<OwnedKey<i32>,Box<i32>>::new();owned.add(OwnedKey::new(4),Box::new(6));owned.add(OwnedKey::new(4),Box::new(7));emit(&mut out,owned.len() as i64);let mut observed=Vec::new();for(key,v)in owned.items(){emit(&mut out,*key.value().unwrap() as i64);emit(&mut out,owned.lookup(key).len() as i64);for x in v{observed.push(**x);}}observed.sort();for v in observed{emit(&mut out,v as i64);}owned.add(OwnedKey::null(),Box::new(3));owned.add(OwnedKey::null(),Box::new(4));emit(&mut out,owned.len() as i64);let null_values=owned.lookup(&OwnedKey::null());emit(&mut out,null_values.len() as i64);for v in null_values{emit(&mut out,**v as i64);}out}
use std::cell::RefCell;thread_local!{static OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn container_oracle_run()->usize{let data=generate();let n=data.len();OUT.with(|o|*o.borrow_mut()=data);n}
#[unsafe(no_mangle)]pub extern "C" fn container_oracle_ptr()->*const u8{OUT.with(|o|o.borrow().as_ptr())}
'''
def expected_words():
 out=[0x43564f31,16,64]
 def bucket(values):out.append(len(values));out.extend(values)
 def snapshot(m):
  out.extend((len(m),int(not m),len(m)))
  for key,values in sorted(m.items()):out.append(key);bucket(values)
  out.append(len(m))
  for values in sorted(m.values()):bucket(values)
  out.append(len(m))
  for key,values in sorted(m.items()):out.append(key);bucket(values)
 for seed in range(16):
  m={}
  for step in range(64):
   key=(step*7+seed*3)%11-5;v=(step*13+seed*17)%53-26;op=step%8
   if op==0:m.setdefault(key,[]).append(v)
   elif op==1:m.setdefault(key,[]).extend((v,v+1,v))
   elif op==2:m.setdefault(key,[])
   elif op==3:
    values=m.setdefault(key,[])
    if v not in values:values.append(v)
   elif op==4:
    if key in m:m[key]=[x+i+1 for i,x in enumerate(m[key])]
   elif op==5:m={k:[x+k for x in values] for k,values in m.items()}
   elif op==6:bucket([])
   else:
    copy={k:values[:] for k,values in m.items()};m.setdefault(key,[]).append(v);snapshot(copy)
    if step in (31,63):m.clear()
   snapshot(m)
 for n in range(65):
  out.extend((n,n*4,int(n==0),1));values=[i*13-n for i in range(n)]
  for i in range(n):out.extend((i*4,values[i],values[i]+7,values[i]+7));values[i]+=7
  out.extend(-v for v in values)
 bits=(0,0x80000000,0x3f800000,0xbf800000,0x7f800000,0xff800000,0x7f812345,0x7fc12345)
 for n in range(17):
  out.extend((n,n*4,1))
  for i in range(n):out.extend((bits[i%8],bits[(i+3)%8],bits[(i+3)%8]))
 out.extend((2,4,1,4,1,6,7,3,2,3,4))
 return [v&0xffffffff for v in out]
def check(path):
 data=path.read_bytes();expected=b''.join(struct.pack('<I',v) for v in expected_words())
 if data!=expected:
  first=next((i for i,(a,b) in enumerate(zip(data,expected)) if a!=b),min(len(data),len(expected)))
  raise ValueError(f'Observation mismatch/truncation at byte {first}, expected {len(expected)} bytes, got {len(data)}')
 return len(expected)//4

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args,cwd,log,stdout=None):
 if stdout:
  with stdout.open('wb') as stream:p=subprocess.run(args,cwd=cwd,stdout=stream,stderr=subprocess.PIPE,timeout=180)
  log.write_bytes(p.stderr)
 else:p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);log.write_bytes(p.stdout)
 if p.returncode:raise RuntimeError('Probe failed, not an equivalence result: '+str(args))
def build(directory):
 from playwright.sync_api import sync_playwright
 directory=directory.resolve();directory.mkdir(parents=True,exist_ok=True)
 report={'status':'failed','complete_blender_test_port':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scope':'supplemental map/view observations, not extra upstream cases','original_cpp_comparison':'pending separate comparison','original_api_limit':LIMIT}
 try:
  with tempfile.TemporaryDirectory(prefix='blended-container-oracle-') as d:
   root=Path(d)
   for name in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
    p=ROOT/name
    if p.is_dir():shutil.copytree(p,root/name)
    else:shutil.copyfile(p,root/name)
   (root/'crates/blended-core/src/container_oracle.rs').write_text(RUST);(directory/'probe.rs').write_text(RUST)
   with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod container_oracle;\n')
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);(examples/'container_oracle.rs').write_text('use std::io::Write;fn main(){std::io::stdout().write_all(&blended_core::container_oracle::generate()).unwrap();}\n')
   native=directory/'container-native.bin';browser_file=directory/'container-browser.bin'
   command(['cargo','run','--locked','--release','--quiet','-p','blended-core','--example','container_oracle'],root,directory/'native.log',stdout=native)
   count=check(native)
   command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,directory/'wasm-build.log')
   wasm=root/'target/wasm32-unknown-unknown/release/blended_core.wasm'
   with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    encoded=page.evaluate('''async data=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports,n=w.container_oracle_run(),ptr=w.container_oracle_ptr(),v=new Uint8Array(w.memory.buffer,ptr,n);let s='';for(let i=0;i<v.length;i+=8192)s+=String.fromCharCode(...v.subarray(i,i+8192));return btoa(s);}''',base64.b64encode(wasm.read_bytes()).decode())
    browser_file.write_bytes(base64.b64decode(encoded,validate=True));check(browser_file);report.update(browser_version=browser.version,browser_errors=errors);browser.close()
    if errors:raise ValueError('Browser errors')
   report.update(status='passed',native_vs_independent_model='exact_match',browser_vs_independent_model='exact_match',output_words=count,output_bytes=count*4,native_sha256=sha(native),browser_sha256=sha(browser_file),wasm_sha256=sha(wasm),map_operation_sequences=16,map_operations_per_sequence=64,integer_view_lengths=list(range(65)),float_view_lengths=list(range(17)),unordered_key_iteration_normalised=True,within_key_value_order_preserved=True)
 except Exception as e:report['failure']=str(e);(directory/'container-rust-status.json').write_text(json.dumps(report,indent=2)+'\n');raise
 (directory/'container-rust-status.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
def compare(reference,directory,output):
 report={'status':'failed','complete_blender_test_port':False,'scope':'supplemental original-header values, aliases and within-allocation pointer offsets; not extra upstream cases','original_api_limit':LIMIT}
 try:
  metadata=json.loads((directory/'container-rust-status.json').read_text())
  if metadata['status']!='passed' or metadata.get('original_api_limit')!=LIMIT:raise ValueError('Replacement probe incomplete or wrong scope')
  count=check(reference)
  for name in ('container-native.bin','container-browser.bin'):
   check(directory/name)
   if reference.read_bytes()!=(directory/name).read_bytes():raise ValueError('Original/replacement byte mismatch')
  report.update(status='passed',source_commit=metadata['source_commit'],reference_commit='94363991e7dcf39e2d70614aa002ab6f67764a5d',original_cpp_vs_native='exact_match',original_cpp_vs_chromium='exact_match',all_three_vs_independent_model='exact_match',output_words=count,output_bytes=count*4,output_sha256=sha(reference),map_operations=1024,integer_view_lengths=[0,64],float_view_lengths=[0,16],native_map_iteration_order_certified=False,memory_safety_or_abi_proved=False)
 except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','compare']);p.add_argument('--output',required=True,type=Path);p.add_argument('--reference',type=Path);p.add_argument('--root',type=Path);a=p.parse_args()
 if a.command=='build':build(a.output)
 else:compare(a.reference,a.root,a.output)
