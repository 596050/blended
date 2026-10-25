#!/usr/bin/env python3
"""Require unchanged original callable/iterator/session tests to detect broken implementations.

Supplemental negative controls only. Compiler errors, panics and browser traps
are failures of this probe, not accepted evidence that assertions detected the mutation.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ("function_ref_truthiness_broken","function_ref_compat.rs",
  "pub fn is_some(&self)->bool{self.callback.is_some()}\\n pub fn call(&mut self)->R{unsafe{self.callback.expect(\\\"calling empty FunctionRef\\\")(self.data)}}",
  "pub fn is_some(&self)->bool{true}\\n pub fn call(&mut self)->R{unsafe{self.callback.expect(\\\"calling empty FunctionRef\\\")(self.data)}}",
  "function_ref.Null","function_ref.ConstantFunction"),
 ("iterator_not_doubled","random_access_compat.rs",
  "self.slice[self.index as usize]*2",
  "self.slice[self.index as usize]",
  "random_access_iterator_mixin.DoublingIterator","function_ref.StatelessLambda"),
 ("session_uid_reused","session_uid_compat.rs",
  " SessionUID(value)\n}",
  " SessionUID(1)\n}",
  "SessionUID.GenerateBasic","function_ref.StandaloneFunction"),
)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError("Unexpected command failure, not valid assertion detection: "+str(args))
 return p.stdout
def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
 cases=json.loads((ROOT/"compatibility/callable-utility-ports.json").read_text())["cases"]
 by_id={c["id"]:(i,c) for i,c in enumerate(cases)}
 test_source=ROOT/"crates/blended-core/src/callable_utility_cases.rs"
 report=dict(status="failed",scope="implementation-only negative controls, not extra upstream cases",
             complete_blender_test_port=False,source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
             unchanged_test_sha256=digest(test_source),checks=[])
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which("google-chrome") or shutil.which("chromium"),headless=True,args=["--no-sandbox"])
   report["browser_version"]=browser.version
   for name,filename,old,new,target_id,control_id in MUTATIONS:
    index,target=by_id[target_id];control_index,control=by_id[control_id]
    target_count=target["expected_runtime_assertions"];control_count=control["expected_runtime_assertions"]
    with tempfile.TemporaryDirectory(prefix="blended-callable-mutation-") as directory:
     root=Path(directory)
     for part in ["crates","Cargo.toml","Cargo.lock","rust-toolchain.toml"]:
      src=ROOT/part;dst=root/part
      if src.is_dir():shutil.copytree(src,dst)
      else:shutil.copyfile(src,dst)
     examples=root/"crates/blended-core/examples";examples.mkdir(exist_ok=True)
     example=examples/"callable_sensitivity.rs"
     example.write_text(f'fn main(){{let r=blended_core::callable_utility_cases::{target["rust_function"]}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{target_count});println!("ORIGINAL_POSITIVE_CASE_EXECUTED");}}\n')
     text=command(["cargo","run","--locked","--quiet","-p","blended-core","--example","callable_sensitivity"],root,output.parent/(name+".positive.log"))
     if "ORIGINAL_POSITIVE_CASE_EXECUTED" not in text:raise ValueError("Positive case did not execute")
     path=root/"crates/blended-core/src"/filename;source=path.read_text()
     if source.count(old)!=1:raise ValueError("Mutation target changed: "+name)
     original=digest(path);path.write_text(source.replace(old,new))
     if digest(root/"crates/blended-core/src/callable_utility_cases.rs")!=digest(test_source):raise ValueError("Original translated tests changed during mutation")
     example.write_text(f'fn main(){{let c=blended_core::callable_utility_cases::{control["rust_function"]}();assert!(c.passed(),"{{:?}}",c.failures);assert_eq!(c.assertions,{control_count});let r=blended_core::callable_utility_cases::{target["rust_function"]}();assert!(!r.passed(),"mutant unexpectedly passed");assert_eq!(r.assertions,{target_count});assert!(!r.failures.is_empty());println!("UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC");}}\n')
     text=command(["cargo","run","--locked","--quiet","-p","blended-core","--example","callable_sensitivity"],root,output.parent/(name+".negative.log"))
     if "UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC" not in text:raise ValueError("Mutation assertion failure marker missing")
     command(["cargo","build","--locked","--release","--target","wasm32-unknown-unknown","-p","blended-core"],root,output.parent/(name+".wasm-build.log"))
     wasm=(root/"target/wasm32-unknown-unknown/release/blended_core.wasm").read_bytes();page=browser.new_page()
     actual=page.evaluate("""async({data,index,control})=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;return{count:w.blended_callable_utils_case_count(),target:w.blended_callable_utils_run_case(index),target_assertions:w.blended_callable_utils_assertion_count(index),control:w.blended_callable_utils_run_case(control),control_assertions:w.blended_callable_utils_assertion_count(control),invalid:w.blended_callable_utils_run_case(0xffffffff)};}""",
                          {"data":base64.b64encode(wasm).decode(),"index":index,"control":control_index})
     page.close()
     expected={"count":len(cases),"target":0,"target_assertions":target_count,"control":1,"control_assertions":control_count,"invalid":-1}
     if actual!=expected:raise ValueError("Unexpected browser mutation result: "+str(actual))
     report["checks"].append(dict(mutation=name,case=target_id,control=control_id,status="passed",
                                  native_assertion_failure_observed=True,browser=actual,
                                  original_implementation_sha256=original,mutated_implementation_sha256=digest(path),
                                  wasm_sha256=hashlib.sha256(wasm).hexdigest()))
   browser.close()
  report["status"]="passed"
 except Exception as error:
  report["failure"]=str(error);output.write_text(json.dumps(report,indent=2)+"\n");raise
 output.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report,indent=2))
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);args=p.parse_args();run(args.output)
