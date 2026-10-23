#!/usr/bin/env python3
"""Execution sensitivity checks, not additional Blender tests or revised expectations.

Original generated tests remain byte-identical. Two implementation mutations must
be caught without changing assertion counts. An instrumented original infinity
smoke call must execute once. Compiler errors and browser traps fail this probe.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180)
 log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Command failure is not mutation detection: '+str(args))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output.parent.mkdir(parents=True,exist_ok=True)
 report={'status':'failed','complete_blender_test_port':False,'scope':'diagnostic implementation mutations and smoke-call observation, not upstream case counts','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
 try:
  files=['crates/blended-core/src/sampling_cases.rs','crates/blended-core/src/curve_cases.rs']
  original={f:digest(ROOT/f) for f in files}
  with tempfile.TemporaryDirectory(prefix='blended-sampling-probe-') as directory:
   root=Path(directory)
   for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
    src=ROOT/name
    if src.is_dir():shutil.copytree(src,root/name)
    else:shutil.copyfile(src,root/name)
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
   example=examples/'sampling_sensitivity.rs'
   example.write_text('''fn main(){
for (_,run,count) in blended_core::sampling_cases::CASES {let r=run();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,*count);}
for (_,run,count) in blended_core::curve_cases::CASES {let r=run();assert!(r.passed(),"{:?}",r.failures);assert_eq!(r.assertions,*count);}
println!("ALL_36_UNMODIFIED_SAMPLING_CASES_EXECUTED");
}''')
   stdout=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','sampling_sensitivity'],root,output.with_suffix('.positive.log'))
   if 'ALL_36_UNMODIFIED_SAMPLING_CASES_EXECUTED' not in stdout:raise ValueError('Missing positive execution marker')
   p=root/'crates/blended-core/src/image_sampling.rs';before=p.read_text()
   signature='pub fn interpolate_bilinear_border_byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{byte4(bilinear(b,w,h,4,u,v,InterpWrapMode::Border,InterpWrapMode::Border,true))}'
   if before.count(signature)!=1:raise ValueError('Border implementation changed; review mutation')
   after=before.replace(signature,signature.replace('InterpWrapMode::Border','InterpWrapMode::Extend'))
   prefix='pub fn interpolate_bilinear_wrap_byte(b:&[u8],w:usize,h:usize,u:f32,v:f32)->[u8;4]{'
   if after.count(prefix)!=1:raise ValueError('Repeat implementation changed; review observation')
   after=after.replace(prefix,prefix+'if !u.is_finite()||!v.is_finite(){INFINITY_VISITS.fetch_add(1,core::sync::atomic::Ordering::SeqCst);}')
   after+='\nstatic INFINITY_VISITS:core::sync::atomic::AtomicU32=core::sync::atomic::AtomicU32::new(0);\n#[unsafe(no_mangle)]pub extern "C" fn blended_infinity_visits()->u32{INFINITY_VISITS.load(core::sync::atomic::Ordering::SeqCst)}\n'
   p.write_text(after)
   report['image_mutation']={'original_sha256':hashlib.sha256(before.encode()).hexdigest(),'diagnostic_sha256':digest(p),'change':'border byte sampler uses Extend instead of Border; wrap sampler increments a diagnostic counter for the preserved nonfinite call'}
   p=root/'crates/blended-core/src/curve_sampling.rs';before=p.read_text();needle='indices.len()-usize::from(include_last)'
   if before.count(needle)!=1:raise ValueError('Uniform sampler changed; review mutation')
   p.write_text(before.replace(needle,'indices.len()-0'))
   report['curve_mutation']={'original_sha256':hashlib.sha256(before.encode()).hexdigest(),'diagnostic_sha256':digest(p),'change':'include_last no longer changes the uniform denominator'}
   if {f:digest(root/f) for f in files}!=original:raise ValueError('Original test assertions changed')
   report['unchanged_test_sha256']=original
   example.write_text('''fn main(){
let control=blended_core::sampling_cases::math_interp__NearestCharExactSamples();assert!(control.passed());
let border=blended_core::sampling_cases::math_interp__BilinearCharPartiallyOutsideImageBorder();assert!(!border.passed());assert_eq!(border.assertions,3);assert!(!border.failures.is_empty());
let curve=blended_core::curve_cases::length_parameterize__FloatSimple();assert!(!curve.passed());assert_eq!(curve.assertions,7);assert!(!curve.failures.is_empty());
let n=blended_core::image_sampling::blended_infinity_visits();let smoke=blended_core::sampling_cases::math_interp__BilinearCharPartiallyOutsideImageWrap();assert!(smoke.passed());assert_eq!(smoke.assertions,3);assert_eq!(blended_core::image_sampling::blended_infinity_visits()-n,1);
println!("BORDER_AND_CURVE_MUTATIONS_DETECTED_INFINITY_CALL_OBSERVED");
}''')
   stdout=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','sampling_sensitivity'],root,output.with_suffix('.negative.log'))
   if 'BORDER_AND_CURVE_MUTATIONS_DETECTED_INFINITY_CALL_OBSERVED' not in stdout:raise ValueError('Missing sensitivity marker')
   command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
   wasm=root/'target/wasm32-unknown-unknown/release/blended_core.wasm'
   with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    actual=page.evaluate('''async base64=>{const {instance}=await WebAssembly.instantiate(Uint8Array.from(atob(base64),c=>c.charCodeAt(0)),{});const w=instance.exports;const initial=w.blended_infinity_visits();const smoke=w.blended_sampling_run_case(11);const visits=w.blended_infinity_visits()-initial;return {control:w.blended_sampling_run_case(0),border:w.blended_sampling_run_case(9),border_assertions:w.blended_sampling_assertion_count(9),curve:w.blended_curves_run_case(0),curve_assertions:w.blended_curves_assertion_count(0),smoke,visits};}''',base64.b64encode(wasm.read_bytes()).decode())
    report['browser']={'version':browser.version,'result':actual,'errors':errors,'wasm_sha256':digest(wasm),'mode':'local diagnostic module; not deployed production build'};browser.close()
   if errors or actual!={'control':1,'border':0,'border_assertions':3,'curve':0,'curve_assertions':7,'smoke':1,'visits':1}:raise ValueError('Incorrect browser sensitivity result: '+str(actual))
   report['status']='passed'
 except Exception as exc:
  report['error']=str(exc);raise
 finally:output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
