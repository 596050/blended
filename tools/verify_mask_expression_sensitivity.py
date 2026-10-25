#!/usr/bin/env python3
"""Require unchanged original mask tests to detect three wrong set operations.
Supplemental controls, not additional upstream cases. Compiler errors, panics
and browser traps fail the probe rather than counting as assertion detection.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
from verify_span_sensitivity import mutate
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ('union_ignores_other','pub fn union(&self,other:&Self)->Self','self.clone()','index_mask_expression.Union','index_mask_expression.IntersectMulti'),
 ('intersection_is_union','pub fn intersection(&self,other:&Self)->Self','self.union(other)','index_mask_expression.Intersection','index_mask_expression.Difference'),
 ('subtraction_disabled','pub fn difference(&self,other:&Self)->Self','self.clone()','index_mask_expression.Difference','index_mask_expression.Union'),
)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args,cwd,log):
 result=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError('Unexpected command failure, not an assertion result: '+str(args))
 return result.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 cases=json.loads((ROOT/'compatibility/mask-expression-ports.json').read_text())['cases'];by_id={c['id']:(i,c) for i,c in enumerate(cases)}
 tests=ROOT/'crates/blended-core/src/mask_expression_cases.rs'
 report={'status':'failed','complete_blender_test_port':False,'scope':'implementation-only negative controls, not additional upstream cases','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'unchanged_test_sha256':digest(tests),'checks':[]}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);report['browser_version']=browser.version
   for name,signature,replacement,target_id,control_id in MUTATIONS:
    index,target=by_id[target_id];ci,control=by_id[control_id];n=target['expected_runtime_assertions'];cn=control['expected_runtime_assertions']
    with tempfile.TemporaryDirectory(prefix='blended-mask-mutation-') as directory:
     root=Path(directory)
     for part in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
      p=ROOT/part
      if p.is_dir():shutil.copytree(p,root/part)
      else:shutil.copyfile(p,root/part)
     examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);example=examples/'mask_sensitivity.rs'
     example.write_text(f'fn main(){{let r=blended_core::mask_expression_cases::{target["rust_function"]}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{n});println!("ORIGINAL_POSITIVE_CASE_EXECUTED");}}\n')
     result=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','mask_sensitivity'],root,output.parent/(name+'.positive.log'))
     if 'ORIGINAL_POSITIVE_CASE_EXECUTED' not in result:raise ValueError('Positive case did not execute')
     impl=root/'crates/blended-core/src/mask_expressions.rs';original=digest(impl);impl.write_text(mutate(impl.read_text(),'body',signature,replacement))
     if digest(root/'crates/blended-core/src/mask_expression_cases.rs')!=digest(tests):raise ValueError('Original translated tests changed')
     example.write_text(f'fn main(){{let c=blended_core::mask_expression_cases::{control["rust_function"]}();assert!(c.passed(),"{{:?}}",c.failures);assert_eq!(c.assertions,{cn});let r=blended_core::mask_expression_cases::{target["rust_function"]}();assert!(!r.passed());assert_eq!(r.assertions,{n});assert!(!r.failures.is_empty());println!("UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC");}}\n')
     result=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','mask_sensitivity'],root,output.parent/(name+'.negative.log'))
     if 'UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC' not in result:raise ValueError('Negative case did not execute')
     command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.parent/(name+'.wasm-build.log'))
     wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();page=browser.new_page()
     actual=page.evaluate('''async({data,index,control})=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;return{count:w.blended_mask_expressions_case_count(),target:w.blended_mask_expressions_run_case(index),target_assertions:w.blended_mask_expressions_assertion_count(index),control:w.blended_mask_expressions_run_case(control),control_assertions:w.blended_mask_expressions_assertion_count(control),invalid:w.blended_mask_expressions_run_case(0xffffffff)};}''',{'data':base64.b64encode(wasm).decode(),'index':index,'control':ci});page.close()
     expected={'count':len(cases),'target':0,'target_assertions':n,'control':1,'control_assertions':cn,'invalid':-1}
     if actual!=expected:raise ValueError('Unexpected browser mutation result '+str(actual))
     report['checks'].append(dict(mutation=name,case=target_id,control=control_id,status='passed',native_assertion_failure_observed=True,browser=actual,original_implementation_sha256=original,mutated_implementation_sha256=digest(impl),wasm_sha256=hashlib.sha256(wasm).hexdigest()))
   browser.close()
  report['status']='passed'
 except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.output)
