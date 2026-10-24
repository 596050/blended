#!/usr/bin/env python3
"""Unchanged original tests must detect four broken string implementations.

Supplemental controls, not extra upstream cases. Compiler errors, panics and
browser traps are probe failures, not assertion-failure detection.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ('append_noop','string_ops.rs','body','pub fn ncat(', '', 'string.StrCat','BLI_string.bounded_strcpy'),
 ('search_wrong_address','string_ops.rs','replace','if matched{return text.as_ptr().wrapping_add(i);}','if matched{return text.as_ptr();}','string.StringStrncasestr','string.StringNLen'),
 ('transposition_disabled','string_search.rs','replace','if i>0&&j>0&&a[i]==b[j-1]&&a[i-1]==b[j]','if false && i>0&&j>0&&a[i]==b[j-1]&&a[i-1]==b[j]','string_search.damerau_levenshtein_distance','string_search.extract_normalized_words'),
 ('uniqueness_disabled','string_ops.rs','body','pub fn unique_name<F:', 'name.to_vec()', 'BLI_string_utils.BLI_uniquename_cb','BLI_string_utils.BLI_string_replace'),
)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mutate(source,kind,old,new):
 if source.count(old)!=1:raise ValueError('Mutation target changed: '+old)
 if kind=='replace':return source.replace(old,new)
 start=source.index('{',source.index(old))+1;end=start;depth=1
 while depth:
  if end>=len(source):raise ValueError('Unbalanced mutation function')
  if source[end]=='{':depth+=1
  elif source[end]=='}':depth-=1
  end+=1
 return source[:start]+new+source[end-1:]
def command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Unexpected command failure: '+str(args))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 cases=json.loads((ROOT/'compatibility/string-ops-ports.json').read_text())['cases'];by_id={c['id']:(i,c) for i,c in enumerate(cases)}
 tests=ROOT/'crates/blended-core/src/string_ops_cases.rs'
 report={'status':'failed','scope':'negative implementation controls, not new upstream cases','complete_blender_test_port':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'unchanged_test_sha256':digest(tests),'checks':[]}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);report['browser_version']=browser.version
   for name,filename,kind,old,new,target_id,control_id in MUTATIONS:
    index,target=by_id[target_id];control_index,control=by_id[control_id]
    n=target['expected_runtime_assertions'];cn=control['expected_runtime_assertions']
    with tempfile.TemporaryDirectory(prefix='blended-string-mutation-') as d:
     root=Path(d)
     for part in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
      p=ROOT/part
      if p.is_dir():shutil.copytree(p,root/part)
      else:shutil.copyfile(p,root/part)
     examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);example=examples/'string_ops_sensitivity.rs'
     example.write_text(f'fn main(){{let r=blended_core::string_ops_cases::{target["rust_function"]}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{n});println!("ORIGINAL_POSITIVE_CASE_EXECUTED");}}\n')
     result=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','string_ops_sensitivity'],root,output.parent/(name+'.positive.log'))
     if 'ORIGINAL_POSITIVE_CASE_EXECUTED' not in result:raise ValueError('Positive marker missing')
     path=root/'crates/blended-core/src'/filename;original=digest(path);path.write_text(mutate(path.read_text(),kind,old,new))
     if digest(root/'crates/blended-core/src/string_ops_cases.rs')!=digest(tests):raise ValueError('Test source changed')
     example.write_text(f'fn main(){{let c=blended_core::string_ops_cases::{control["rust_function"]}();assert!(c.passed(),"{{:?}}",c.failures);assert_eq!(c.assertions,{cn});let r=blended_core::string_ops_cases::{target["rust_function"]}();assert!(!r.passed());assert_eq!(r.assertions,{n});assert!(!r.failures.is_empty());println!("UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC");}}\n')
     result=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','string_ops_sensitivity'],root,output.parent/(name+'.negative.log'))
     if 'UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC' not in result:raise ValueError('Negative marker missing')
     command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.parent/(name+'.wasm-build.log'))
     wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();page=browser.new_page()
     actual=page.evaluate('''async({data,index,control})=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;return{count:w.blended_string_ops_case_count(),target:w.blended_string_ops_run_case(index),target_assertions:w.blended_string_ops_assertion_count(index),control:w.blended_string_ops_run_case(control),control_assertions:w.blended_string_ops_assertion_count(control),invalid:w.blended_string_ops_run_case(0xffffffff)};}''',{'data':base64.b64encode(wasm).decode(),'index':index,'control':control_index});page.close()
     expected={'count':len(cases),'target':0,'target_assertions':n,'control':1,'control_assertions':cn,'invalid':-1}
     if actual!=expected:raise ValueError('Unexpected browser result: '+str(actual))
     report['checks'].append({'mutation':name,'case':target_id,'control':control_id,'status':'passed','native_assertion_failure_observed':True,'browser':actual,'original_implementation_sha256':original,'mutated_implementation_sha256':digest(path),'wasm_sha256':hashlib.sha256(wasm).hexdigest()})
   browser.close()
  report['status']='passed'
 except Exception as e:
  report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
