#!/usr/bin/env python3
"""Implementation-only mutations. Compiler errors, panics and browser traps fail
this probe; only unchanged original assertions failing with controls passing count.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ('multiple_reversed','self.buckets.entry(key).or_default().extend_from_slice(values);','self.buckets.entry(key).or_default().extend(values.iter().rev().cloned());','multi_value_map.AddMultiple','multi_value_map.LookupExistant'),
 ('prepend_instead_of_append','self.buckets.entry(key).or_default().push(value);','self.buckets.entry(key).or_default().insert(0,value);','multi_value_map.LookupExistant','GenericSpanTest.TypeConstructor'),
 ('typed_write_ignored','unsafe{self.view.ptr.cast_mut().add(index).write(value)}','let _=value;','GenericSpanTest.MutableBufferAndSizeConstructor','GenericSpanTest.BufferAndSizeConstructor'),
 ('pointer_stride_zero','self.ptr.add(index*self.descriptor.size)','self.ptr.add(0)','GenericSpanTest.BufferAndSizeConstructor','multi_value_map.Keys'),
)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args,cwd,log):
 r=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError('Unexpected failure, not an assertion result: '+str(args))
 return r.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 cases=json.loads((ROOT/'compatibility/container-view-ports.json').read_text())['cases'];by_id={c['id']:(i,c) for i,c in enumerate(cases)}
 tests=ROOT/'crates/blended-core/src/container_view_cases.rs'
 report={'status':'failed','complete_blender_test_port':False,'scope':'supplemental negative controls, not extra upstream cases','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'unchanged_test_sha256':sha(tests),'checks':[]}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);report['browser_version']=browser.version
   for name,old,new,target_id,control_id in MUTATIONS:
    index,target=by_id[target_id];ci,control=by_id[control_id];n=target['expected_runtime_assertions'];cn=control['expected_runtime_assertions']
    with tempfile.TemporaryDirectory(prefix='blended-container-negative-') as d:
     root=Path(d)
     for part in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
      p=ROOT/part
      if p.is_dir():shutil.copytree(p,root/part)
      else:shutil.copyfile(p,root/part)
     examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);example=examples/'container_sensitivity.rs'
     example.write_text(f'fn main(){{let r=blended_core::container_view_cases::{target["rust_function"]}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{n});println!("POSITIVE_CASE_EXECUTED");}}\n')
     if 'POSITIVE_CASE_EXECUTED' not in command(['cargo','run','--locked','--quiet','-p','blended-core','--example','container_sensitivity'],root,output.parent/(name+'.positive.log')):raise ValueError('Positive case missing')
     implementation=root/'crates/blended-core/src/container_views.rs';before=implementation.read_text();original=sha(implementation)
     if before.count(old)!=1:raise ValueError('Ambiguous mutation target')
     implementation.write_text(before.replace(old,new))
     if sha(root/'crates/blended-core/src/container_view_cases.rs')!=sha(tests):raise ValueError('Original test changed')
     example.write_text(f'fn main(){{let c=blended_core::container_view_cases::{control["rust_function"]}();assert!(c.passed(),"{{:?}}",c.failures);assert_eq!(c.assertions,{cn});let r=blended_core::container_view_cases::{target["rust_function"]}();assert!(!r.passed());assert_eq!(r.assertions,{n});assert!(!r.failures.is_empty());println!("ASSERTION_FAILURE_WITHOUT_PANIC");}}\n')
     if 'ASSERTION_FAILURE_WITHOUT_PANIC' not in command(['cargo','run','--locked','--quiet','-p','blended-core','--example','container_sensitivity'],root,output.parent/(name+'.negative.log')):raise ValueError('Negative report missing')
     command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.parent/(name+'.wasm-build.log'))
     wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();page=browser.new_page()
     actual=page.evaluate('''async({data,index,control})=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;return{count:w.blended_container_views_case_count(),target:w.blended_container_views_run_case(index),target_assertions:w.blended_container_views_assertion_count(index),control:w.blended_container_views_run_case(control),control_assertions:w.blended_container_views_assertion_count(control),invalid:w.blended_container_views_run_case(0xffffffff)};}''',dict(data=base64.b64encode(wasm).decode(),index=index,control=ci));page.close()
     expected=dict(count=len(cases),target=0,target_assertions=n,control=1,control_assertions=cn,invalid=-1)
     if actual!=expected:raise ValueError('Unexpected browser response '+str(actual))
     report['checks'].append(dict(mutation=name,case=target_id,control=control_id,status='passed',native_assertion_failure_observed=True,browser=actual,original_implementation_sha256=original,mutated_implementation_sha256=sha(implementation),wasm_sha256=hashlib.sha256(wasm).hexdigest()))
   browser.close()
  report['status']='passed'
 except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
