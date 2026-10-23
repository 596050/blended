#!/usr/bin/env python3
"""Prove the assertion-free upstream SetEmpty case executes its actual operations.

The negative build changes only empty-span set_all into a panic. The original test
must then fail natively and trap in Chromium WASM. A compiler failure is not a
successful mutation detection. No checked-in implementation is modified.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1]
def run(output:Path):
    from playwright.sync_api import sync_playwright
    import base64
    output.parent.mkdir(parents=True,exist_ok=True)
    evidence={'scope':'negative execution probe for bit_span.SetEmpty; not another upstream test','complete_blender_test_port':False,'status':'failed'}
    cases=json.loads((ROOT/'compatibility/bit-span-ports.json').read_text())['cases']
    index=next(i for i,c in enumerate(cases) if c['id']=='bit_span.SetEmpty')
    assert cases[index]['assertion_free_smoke'] and cases[index]['expected_runtime_assertions']==0
    with tempfile.TemporaryDirectory(prefix='blended-zero-smoke-') as d:
        shadow=Path(d)
        for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
            p=ROOT/name
            if p.is_dir():shutil.copytree(p,shadow/name)
            else:shutil.copyfile(p,shadow/name)
        source=shadow/'crates/blended-core/src/bit_spans.rs';before=source.read_text()
        marker='    pub fn set_all(self,value:bool){'
        assert before.count(marker)==1
        broken=before.replace(marker,marker+'\n        if self.is_empty(){panic!("MUTATION_EMPTY_SPAN_EXECUTED");}')
        source.write_text(broken)
        evidence.update(original_sha256=hashlib.sha256(before.encode()).hexdigest(),mutated_sha256=hashlib.sha256(broken.encode()).hexdigest())
        cmd=['cargo','test','--locked','--test','upstream_bit_spans','bit_span__SetEmpty','--','--exact']
        native=subprocess.run(cmd,cwd=shadow,capture_output=True,text=True,timeout=120)
        log=output.with_suffix('.native.log');log.write_text(native.stdout+native.stderr)
        evidence['native_negative']={'exit':native.returncode,'mutation_observed':native.returncode!=0 and 'MUTATION_EMPTY_SPAN_EXECUTED' in native.stdout+native.stderr and '1 failed' in native.stdout,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
        build=subprocess.run(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],cwd=shadow,capture_output=True,text=True,timeout=120)
        output.with_suffix('.build.log').write_text(build.stdout+build.stderr)
        if build.returncode:raise RuntimeError('Mutated WASM did not build; not a passing negative test')
        wasm=(shadow/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
            page=browser.new_page()
            actual=page.evaluate('''async ({base64,index})=>{
                const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
                const {instance}=await WebAssembly.instantiate(bytes,{});
                const w=instance.exports;
                if(w.blended_bit_spans_case_count()!==27)throw Error('Unexpected probe registry');
                const control=w.blended_bit_spans_run_case(0);
                try{return {control,returned:w.blended_bit_spans_run_case(index),trapped:false};}
                catch(e){return {control,trapped:e instanceof WebAssembly.RuntimeError,message:String(e)};}
            }''',{'base64':base64.b64encode(wasm).decode(),'index':index})
            evidence['browser_negative']={**actual,'browser':browser.version,'wasm_sha256':hashlib.sha256(wasm).hexdigest()};browser.close()
        if evidence['native_negative']['mutation_observed'] and actual.get('trapped') is True and actual.get('control')==1:evidence['status']='passed'
    output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
    return 0 if evidence['status']=='passed' else 1
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'evidence/extended-tdd/zero-assertion-negative.json');a=p.parse_args();sys.exit(run(a.output))
