#!/usr/bin/env python3
"""Build and exercise the actual conformance module, without asserting whole-suite parity."""
import argparse
from datetime import datetime,timezone
import hashlib,json,re,shutil,subprocess,sys,tarfile
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
HTML='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blended | Test-port evidence</title><style>body{font:16px/1.55 system-ui;max-width:1100px;margin:48px auto;padding:0 24px;background:#101722;color:#edf2f8}h1{font-size:36px}a{color:#8ed8ff}button{padding:12px 24px;font:inherit;cursor:pointer}table{width:100%;border-collapse:collapse;margin-top:24px}td,th{text-align:left;padding:8px;border-bottom:1px solid #3b4654}.notice{padding:20px;background:#3b2d16;border-left:4px solid #e5ae46}.pass{color:#88e8ad}.fail{color:#ff9f9f}code{overflow-wrap:anywhere}</style><h1>Blended test-port workbench</h1><p class="notice"><strong>The complete Blender test port is unfinished.</strong> This page executes a verified subset. Passing these cases does not establish application or rendering parity.</p><p id="provenance"></p><p><a href="source.tar.gz">Corresponding source</a> · <a href="manifest.json">Case manifest</a> · <a href="audit.json">Full source-candidate audit</a></p><button id="run">Run all ported Blender cases</button><p id="status" role="status">Loading the manifest…</p><table><thead><tr><th>Upstream test</th><th>Assertions</th><th>Result</th></tr></thead><tbody id="cases"></tbody></table><script type="module" src="run.mjs"></script></html>'''
JS='''const manifest=await (await fetch('./manifest.json')).json();
const tbody=document.querySelector('#cases');
document.querySelector('#provenance').textContent=`Source ${manifest.source_commit}; Blender reference ${manifest.reference_commit}.`;
const all=[...manifest.legacy.map((c,i)=>({...c,index:i,group:'legacy'})),...manifest.additional.map((c,i)=>({...c,index:i,group:'additional'}))];
for(const c of all){const tr=document.createElement('tr');for(const text of [c.id,c.assertion_count??'Original case','Not run']){const td=document.createElement('td');td.textContent=text;tr.append(td);}tbody.append(tr);}
document.querySelector('#status').textContent=`${all.length} translated cases ready. Full-suite completeness remains unverified.`;
document.querySelector('#run').addEventListener('click',async()=>{
 const result={source_commit:manifest.source_commit,reference_commit:manifest.reference_commit,status:'failed',complete_test_port:false,passed:0,additional_assertions:0,cases:[],errors:[]};
 const button=document.querySelector('#run');button.disabled=true;
 try{
  const response=await fetch('./blended_core.wasm');if(!response.ok)throw Error('WASM fetch failed');
  const {instance}=await WebAssembly.instantiate(await response.arrayBuffer(),{});const w=instance.exports;
  if(w.blended_case_count()!==manifest.legacy.length||w.blended_additional_case_count()!==manifest.additional.length)throw Error('Registry/manifest count mismatch');
  for(const [i,c] of all.entries()){
   let code,assertions=null;if(c.group==='legacy'){code=w.blended_run_case(c.index);}else{code=w.blended_additional_run_case(c.index);assertions=w.blended_additional_assertion_count(c.index);result.additional_assertions+=assertions;}
   const passed=code===1&&(c.group==='legacy'||assertions===c.assertion_count);result.cases.push({id:c.id,passed,code,assertions});if(passed)result.passed++;
   const td=tbody.children[i].lastElementChild;td.textContent=passed?'Passed':'Failed';td.className=passed?'pass':'fail';
  }
  result.invalid_index_rejected=w.blended_run_case(0xffffffff)===-1&&w.blended_additional_run_case(0xffffffff)===-1;
  if(result.passed===all.length&&result.invalid_index_rejected)result.status='passed';
 }catch(e){result.errors.push(String(e));}
 document.querySelector('#status').textContent=`${result.passed}/${all.length} passed. Full Blender test-port completeness: not established.`;
 window.__portResults=result;button.disabled=false;
});'''
def build(commit):
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Full source commit required')
    subprocess.run([sys.executable,str(ROOT/'tools/prepare_site.py')],check=True,cwd=ROOT)
    out=ROOT/'build/conformance';out.mkdir(parents=True,exist_ok=True)
    wasm=ROOT/'target/wasm32-unknown-unknown/release/blended_core.wasm'
    shutil.copyfile(wasm,out/'blended_core.wasm')
    legacy=json.loads((ROOT/'compatibility/ports.json').read_text())
    added=json.loads((ROOT/'compatibility/additional-ports.json').read_text())
    manifest={'schema':1,'source_commit':commit,'reference_commit':added['upstream_commit'],'legacy':legacy['cases'],'additional':added['cases'],'complete_test_port':False,'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest()}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'index.html').write_text(HTML);(out/'run.mjs').write_text(JS)
    subprocess.run([sys.executable,str(ROOT/'tools/inventory.py'),'--root',str(ROOT/'.upstream/blender'),'--name','blender','--commit',added['upstream_commit'],'--output',str(ROOT/'build/blender-inventory.json')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tools/test_port_audit.py'),'--inventory',str(ROOT/'build/blender-inventory.json'),'--output',str(out/'audit.json')],check=True)
    # Include the precise sources used for the binary, including generated cases.
    with tarfile.open(out/'source.tar.gz','w:gz') as tar:
        for name in ('crates','tools','tests','compatibility','docs','Cargo.toml','Cargo.lock','rust-toolchain.toml','NOTICE.md','upstream.lock.json'):
            p=ROOT/name
            if p.exists():tar.add(p,arcname='blended/'+name,filter=lambda i:None if '__pycache__' in i.name or i.issym() else i)
        for p in (ROOT/'.upstream/blender').glob('COPYING*'):
            if p.is_file():tar.add(p,arcname='upstream-licenses/'+p.name)
    print('Built conformance site',out)
def test(url,commit,output):
    from playwright.sync_api import sync_playwright
    output.parent.mkdir(parents=True,exist_ok=True)
    report={'url':url,'expected_source_commit':commit,'started_utc':datetime.now(timezone.utc).isoformat(),'status':'failed','errors':[],'complete_test_port':False}
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        context=b.new_context(viewport={'width':1200,'height':1000})
        if urlparse(url).hostname=='rawcdn.githack.com':
            context.add_cookies([{'name':'__Http-phish','value':'1','domain':'rawcdn.githack.com','path':'/','secure':True,'httpOnly':True,'sameSite':'Lax'}])
        page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
        try:
            response=page.goto(url,wait_until='networkidle',timeout=90000)
            assert response and response.status==200,'HTTP failure'
            page.wait_for_selector('#cases tr',timeout=30000)
            assert page.locator('#cases tr').count()==45,'Incomplete or unexpected test registry'
            page.locator('#run').click();page.wait_for_function('window.__portResults !== undefined',timeout=60000)
            data=page.evaluate('window.__portResults');report['wasm']=data
            assert data['source_commit']==commit,'Wrong deployed source revision'
            assert data['status']=='passed' and data['passed']==45,'WASM assertion failure'
            assert data['additional_assertions']==225,'Missing assertion execution'
            assert data['invalid_index_rejected'],'Invalid case silently passed'
            assert data['complete_test_port'] is False,'False completion claim'
            assert not report['errors'],'Uncaught browser errors'
            report['browser_version']=b.version;report['status']='passed'
        except Exception as e:report['failure']=str(e)
        finally:
            try:page.screenshot(path=str(output.with_suffix('.png')),full_page=True)
            except Exception:pass
            b.close()
    report['finished_utc']=datetime.now(timezone.utc).isoformat();output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if report['status']=='passed' else 1
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['build','test']);parser.add_argument('--commit',required=True);parser.add_argument('--url');parser.add_argument('--output',type=Path,default=Path('evidence/browser.json'));args=parser.parse_args()
    if args.command=='build':build(args.commit)
    else:
        if not args.url:parser.error('--url required for test')
        sys.exit(test(args.url,args.commit,args.output))
