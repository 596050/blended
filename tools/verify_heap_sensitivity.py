#!/usr/bin/env python3
"""Require unchanged original tests to detect two broken implementations.

Supplemental negative probes, not additional upstream test cases. Every mutation
gets its own clean shadow. Compilation errors, traps and exceptions do not
satisfy the expected assertion failures.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ('remove_noop','pub fn remove(&mut self,id:NodeId)', 'heap.RangeRemove',513,'heap.One',5),
 ('priority_increase_noop','pub fn priority_increased(&mut self,index:usize)', 'inplace_priority_queue.IncreasePriority',3,'inplace_priority_queue.BuildSmall',7),
)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def remove_body(source,signature):
 if source.count(signature)!=1:raise ValueError('Mutation target changed: '+signature)
 start=source.index('{',source.index(signature))+1;i=start;depth=1
 while depth:
  if i>=len(source):raise ValueError('Unbalanced mutation target')
  if source[i]=='{':depth+=1
  elif source[i]=='}':depth-=1
  i+=1
 return source[:start]+' /* intentionally broken diagnostic implementation */ '+source[i-1:]
def command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180)
 log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Unexpected command failure, not valid mutation detection: '+str(args))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 contracts=json.loads((ROOT/'compatibility/heap-ports.json').read_text())['cases']
 by_id={c['id']:(i,c) for i,c in enumerate(contracts)}
 source=ROOT/'crates/blended-core/src/priority_heaps.rs'
 test_file=ROOT/'crates/blended-core/src/heap_cases.rs'
 evidence={'status':'failed','complete_blender_test_port':False,'scope':'negative implementation controls, not new upstream cases','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'original_implementation_sha256':digest(source),'unchanged_original_test_port_sha256':digest(test_file),'checks':[]}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);evidence['browser_version']=browser.version
   for name,signature,identity,count,control,control_count in MUTATIONS:
    index,c=by_id[identity];control_index,cc=by_id[control]
    if c['expected_runtime_assertions']!=count or cc['expected_runtime_assertions']!=control_count:raise ValueError('Original assertion contract changed')
    with tempfile.TemporaryDirectory(prefix='blended-heap-mutation-') as d:
     root=Path(d)
     for part in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
      p=ROOT/part
      if p.is_dir():shutil.copytree(p,root/part)
      else:shutil.copyfile(p,root/part)
     examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
     example=examples/'heap_sensitivity.rs'
     target_fn=c['rust_function'];control_fn=cc['rust_function']
     example.write_text(f'fn main(){{let r=blended_core::heap_cases::{target_fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});println!("POSITIVE_ORIGINAL_CASE_EXECUTED");}}\n')
     text=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','heap_sensitivity'],root,output.parent/(name+'.positive.log'))
     if 'POSITIVE_ORIGINAL_CASE_EXECUTED' not in text:raise ValueError('Positive case did not execute')
     changed=root/'crates/blended-core/src/priority_heaps.rs';changed.write_text(remove_body(changed.read_text(),signature))
     if digest(root/'crates/blended-core/src/heap_cases.rs')!=digest(test_file):raise ValueError('A test changed during mutation')
     example.write_text(f'fn main(){{let c=blended_core::heap_cases::{control_fn}();assert!(c.passed());assert_eq!(c.assertions,{control_count});let r=blended_core::heap_cases::{target_fn}();assert!(!r.passed());assert_eq!(r.assertions,{count});assert!(!r.failures.is_empty());println!("NEGATIVE_ASSERTIONS_OBSERVED_WITHOUT_PANIC");}}\n')
     text=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','heap_sensitivity'],root,output.parent/(name+'.negative.log'))
     if 'NEGATIVE_ASSERTIONS_OBSERVED_WITHOUT_PANIC' not in text:raise ValueError('Negative assertion report missing')
     command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.parent/(name+'.wasm-build.log'))
     wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();page=browser.new_page()
     result=page.evaluate('''async({data,index,control})=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;return{count:w.blended_heaps_case_count(),target:w.blended_heaps_run_case(index),target_assertions:w.blended_heaps_assertion_count(index),control:w.blended_heaps_run_case(control),control_assertions:w.blended_heaps_assertion_count(control),invalid:w.blended_heaps_run_case(0xffffffff)};}''',{'data':base64.b64encode(wasm).decode(),'index':index,'control':control_index});page.close()
     expected={'count':len(contracts),'target':0,'target_assertions':count,'control':1,'control_assertions':control_count,'invalid':-1}
     if result!=expected:raise ValueError('Unexpected browser mutation result: '+str(result))
     evidence['checks'].append({'mutation':name,'case':identity,'control':control,'status':'passed','native_assertion_failure_observed':True,'browser':result,'mutation_sha256':digest(changed),'wasm_sha256':hashlib.sha256(wasm).hexdigest()})
   browser.close()
  evidence['status']='passed'
 except Exception as e:
  evidence['failure']=str(e);output.write_text(json.dumps(evidence,indent=2)+'\n');raise
 output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
