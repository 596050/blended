#!/usr/bin/env python3
"""Unchanged original UTF8 tests must detect broken implementations.

Supplemental controls, not extra Blender cases. Compiler errors, panics and
browser traps fail the probe rather than counting as detected assertions.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
from verify_string_ops_sensitivity import mutate
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ('substitution_disabled','pub fn invalid_substitute(', '0', 'string.Utf8InvalidBytesSubstitute','string.Utf8InvalidBytesStrip'),
 ('copy_disabled','pub fn copy_into(', 'dst[0]=0;0', 'string.StrCopyUTF8_TruncateEncodingMulti','string.StringNLenUTF8'),
 ('combining_marks_ignored','pub fn zero_width(', 'false', 'string.StrCursorStepNextUtf8AllCombining','string.StrCursorStepNextUtf8Simple'),
)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args,cwd,log):
    p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError('Unexpected command failure: '+str(args))
    return p.stdout

def run(output):
    from playwright.sync_api import sync_playwright
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    cases=json.loads((ROOT/'compatibility/utf8-ports.json').read_text())['cases'];by_id={c['id']:(i,c) for i,c in enumerate(cases)}
    tests=ROOT/'crates/blended-core/src/utf8_cases.rs'
    report={'status':'failed','scope':'negative implementation controls, not additional upstream cases','complete_blender_test_port':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'unchanged_test_sha256':digest(tests),'checks':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);report['browser_version']=browser.version
            for name,signature,replacement,target_id,control_id in MUTATIONS:
                index,target=by_id[target_id];ci,control=by_id[control_id];n=target['expected_runtime_assertions'];cn=control['expected_runtime_assertions']
                with tempfile.TemporaryDirectory(prefix='blended-utf8-mutation-') as d:
                    root=Path(d)
                    for part in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
                        p=ROOT/part
                        if p.is_dir():shutil.copytree(p,root/part)
                        else:shutil.copyfile(p,root/part)
                    examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);example=examples/'utf8_sensitivity.rs'
                    example.write_text(f'fn main(){{let r=blended_core::utf8_cases::{target["rust_function"]}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{n});println!("ORIGINAL_POSITIVE_CASE_EXECUTED");}}\n')
                    result=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','utf8_sensitivity'],root,output.parent/(name+'.positive.log'))
                    if 'ORIGINAL_POSITIVE_CASE_EXECUTED' not in result:raise ValueError('Missing positive execution')
                    path=root/'crates/blended-core/src/utf8_compat.rs';original=digest(path);path.write_text(mutate(path.read_text(),'body',signature,replacement))
                    if digest(root/'crates/blended-core/src/utf8_cases.rs')!=digest(tests):raise ValueError('Test source changed')
                    example.write_text(f'fn main(){{let c=blended_core::utf8_cases::{control["rust_function"]}();assert!(c.passed(),"{{:?}}",c.failures);assert_eq!(c.assertions,{cn});let r=blended_core::utf8_cases::{target["rust_function"]}();assert!(!r.passed());assert_eq!(r.assertions,{n});assert!(!r.failures.is_empty());println!("UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC");}}\n')
                    result=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','utf8_sensitivity'],root,output.parent/(name+'.negative.log'))
                    if 'UNCHANGED_ASSERTIONS_DETECT_MUTANT_WITHOUT_PANIC' not in result:raise ValueError('Missing negative execution')
                    command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.parent/(name+'.wasm-build.log'))
                    wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes();page=browser.new_page()
                    actual=page.evaluate('''async({data,index,control})=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;return{count:w.blended_utf8_case_count(),target:w.blended_utf8_run_case(index),target_assertions:w.blended_utf8_assertion_count(index),control:w.blended_utf8_run_case(control),control_assertions:w.blended_utf8_assertion_count(control),invalid:w.blended_utf8_run_case(0xffffffff)};}''',{'data':base64.b64encode(wasm).decode(),'index':index,'control':ci});page.close()
                    expected={'count':len(cases),'target':0,'target_assertions':n,'control':1,'control_assertions':cn,'invalid':-1}
                    if actual!=expected:raise ValueError('Unexpected browser mutation results: '+str(actual))
                    report['checks'].append({'mutation':name,'case':target_id,'control':control_id,'status':'passed','native_assertion_failure_observed':True,'browser':actual,'original_implementation_sha256':original,'mutated_implementation_sha256':digest(path),'wasm_sha256':hashlib.sha256(wasm).hexdigest()})
            browser.close()
        report['status']='passed'
    except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
