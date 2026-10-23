#!/usr/bin/env python3
"""Negative execution probe, not an additional upstream test.

Mutate only the line/plane implementation to return None. The original ported
ASSERT_TRUE must record a single failed assertion and return normally, before
any unwrap. A compiler error, panic or browser trap is a failed probe.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def run_command(command,root,log):
 p=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=180)
 log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Probe command failed, not a passing negative assertion: '+str(command))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output.parent.mkdir(parents=True,exist_ok=True)
 evidence={'status':'failed','scope':'negative execution probe for the existing math_geom_hh.IsectLinePlane case, not another upstream case','complete_blender_test_port':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
 manifest=json.loads((ROOT/'compatibility/geometry-math-ports.json').read_text())['cases']
 index=next(i for i,c in enumerate(manifest) if c['id']=='math_geom_hh.IsectLinePlane')
 control=next(i for i,c in enumerate(manifest) if c['id']=='math_geom_hh.AreaTri')
 assert manifest[index]['expected_runtime_assertions']==4
 with tempfile.TemporaryDirectory(prefix='blended-fatal-probe-') as directory:
  root=Path(directory)
  for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
   src=ROOT/name
   if src.is_dir():shutil.copytree(src,root/name)
   else:shutil.copyfile(src,root/name)
  examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
  probe=examples/'fatal_assertion_probe.rs'
  probe.write_text('fn main(){let r=blended_core::geometry_math_cases::math_geom_hh__IsectLinePlane();assert!(r.passed());assert_eq!(r.assertions,4);println!("POSITIVE_ORIGINAL_CASE_EXECUTED");}\n')
  positive=run_command(['cargo','run','--locked','--quiet','-p','blended-core','--example','fatal_assertion_probe'],root,output.with_suffix('.positive.log'))
  assert 'POSITIVE_ORIGINAL_CASE_EXECUTED' in positive
  source=root/'crates/blended-core/src/geometry_math.rs';before=source.read_text()
  signature='pub fn isect_line_plane(a:V3,b:V3,p:V3,n:V3)->Option<V3>{'
  if before.count(signature)!=1:raise ValueError('Implementation changed; review this mutation')
  start=before.index(signature)+len(signature);end=start;depth=1
  while depth:
   if end>=len(before):raise ValueError('Unbalanced function')
   if before[end]=='{':depth+=1
   elif before[end]=='}':depth-=1
   end+=1
  after=before[:start]+'None'+before[end-1:];source.write_text(after)
  evidence.update(original_implementation_sha256=hashlib.sha256(before.encode()).hexdigest(),mutated_implementation_sha256=hashlib.sha256(after.encode()).hexdigest(),original_positive_case_executed=True)
  probe.write_text('fn main(){let control=blended_core::geometry_math_cases::math_geom_hh__AreaTri();assert!(control.passed());let r=blended_core::geometry_math_cases::math_geom_hh__IsectLinePlane();assert!(!r.passed());assert_eq!(r.assertions,1);assert_eq!(r.failures.len(),1);assert!(r.failures[0].contains("hit.is_some()"));println!("NEGATIVE_FATAL_STOP_OBSERVED_WITHOUT_PANIC");}\n')
  result=run_command(['cargo','run','--locked','--quiet','-p','blended-core','--example','fatal_assertion_probe'],root,output.with_suffix('.negative.log'))
  assert 'NEGATIVE_FATAL_STOP_OBSERVED_WITHOUT_PANIC' in result
  evidence['native_fatal_stop']='passed'
  run_command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.build.log'))
  wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes()
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
   page=browser.new_page()
   actual=page.evaluate('''async ({base64,index,control})=>{
    const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
    const {instance}=await WebAssembly.instantiate(bytes,{});const w=instance.exports;
    return {case_count:w.blended_geometry_math_case_count(),control:w.blended_geometry_math_run_case(control),target:w.blended_geometry_math_run_case(index),assertions:w.blended_geometry_math_assertion_count(index),invalid:w.blended_geometry_math_run_case(0xffffffff)};
   }''',{'base64':base64.b64encode(wasm).decode(),'index':index,'control':control})
   evidence['browser']={**actual,'version':browser.version,'wasm_sha256':hashlib.sha256(wasm).hexdigest(),'mode':'local diagnostic mutation, not production deployment'}
   browser.close()
  if actual!={'case_count':30,'control':1,'target':0,'assertions':1,'invalid':-1}:raise ValueError('Fatal stop was not preserved: '+str(actual))
  evidence['status']='passed'
 output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.output)
