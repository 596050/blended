#!/usr/bin/env python3
"""Build and exercise the actual conformance module, without asserting whole-suite parity."""
import argparse
from datetime import datetime,timezone
import hashlib,json,re,shutil,subprocess,sys,tarfile
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
from port_registry import GROUPS,TOTAL_KEYS,ABI,verify_runtime_contract_bijection
HTML='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blended | Test-port evidence</title><style>body{font:16px/1.55 system-ui;max-width:1100px;margin:48px auto;padding:0 24px;background:#101722;color:#edf2f8}h1{font-size:36px}a{color:#8ed8ff}button{padding:12px 24px;font:inherit;cursor:pointer}table{width:100%;border-collapse:collapse;margin-top:24px}td,th{text-align:left;padding:8px;border-bottom:1px solid #3b4654}.notice{padding:20px;background:#3b2d16;border-left:4px solid #e5ae46}.pass{color:#88e8ad}.fail{color:#ff9f9f}code{overflow-wrap:anywhere}</style><h1>Blended test-port workbench</h1><p class="notice"><strong>The complete Blender test port is unfinished.</strong> This page executes a verified subset. Passing these cases does not establish application or rendering parity.</p><p id="provenance"></p><p><a href="source.tar.gz">Corresponding source</a> · <a href="manifest.json">Case manifest</a> · <a href="audit.json">Full source-candidate audit</a></p><button id="run">Run all ported Blender cases</button><p id="status" role="status">Loading the manifest…</p><table><thead><tr><th>Upstream test</th><th>Assertions</th><th>Result</th></tr></thead><tbody id="cases"></tbody></table><script type="module" src="run.mjs"></script></html>'''
JS='''const response=await fetch('./manifest.json');
if(!response.ok)throw Error('Manifest fetch failed');
const manifest=await response.json();
const tbody=document.querySelector('#cases');
document.querySelector('#provenance').textContent=`Source ${manifest.source_commit}; Blender reference ${manifest.reference_commit}.`;
const groups=manifest.groups;
if(!Array.isArray(groups)||new Set(groups).size!==groups.length)throw Error('Malformed group registry');
const all=groups.flatMap(group=>manifest[group].map((c,index)=>({...c,index,group})));
if(new Set(all.map(c=>c.id)).size!==all.length)throw Error('Duplicate case identity');
for(const c of all){const tr=document.createElement('tr');for(const text of [c.id,c.expected_runtime_assertions??c.assertion_count??'Original case','Not run']){const td=document.createElement('td');td.textContent=text;tr.append(td);}tbody.append(tr);}
document.querySelector('#status').textContent=`${all.length} translated cases ready. Full-suite completeness remains unverified.`;
document.querySelector('#run').addEventListener('click',async()=>{
 const result={source_commit:manifest.source_commit,reference_commit:manifest.reference_commit,status:'failed',complete_test_port:false,passed:0,vector_assertions:0,additional_assertions:0,structure_assertions:0,collection_assertions:0,cases:[],errors:[]};
 for(const key of Object.values(manifest.total_keys))result[key]=0;
 const button=document.querySelector('#run');button.disabled=true;
 try{
  const response=await fetch('./blended_core.wasm');if(!response.ok)throw Error('WASM fetch failed');
  const bytes=await response.arrayBuffer();
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==manifest.wasm_sha256)throw Error('WASM hash/manifest mismatch');
  result.wasm_sha256=digest;
  const {instance}=await WebAssembly.instantiate(bytes,{});const w=instance.exports;
  const registries=Object.fromEntries(groups.map(g=>[g,manifest.abi[g].map(name=>{if(typeof w[name]!=='function')throw Error('Missing ABI '+name);return w[name];})]));
  for(const group of groups){if(registries[group][0]()!==manifest[group].length)throw Error(`Registry/manifest count mismatch: ${group}`);}
  for(const [i,c] of all.entries()){
   const [,run,count]=registries[c.group];const code=run(c.index);const assertions=count?count(c.index):null;
   result[manifest.total_keys[c.group]]+=assertions;
   const expected=c.expected_runtime_assertions??c.assertion_count;
   const passed=code===1&&assertions===expected;
   result.cases.push({id:c.id,group:c.group,passed,code,assertions});if(passed)result.passed++;
   const td=tbody.children[i].lastElementChild;td.textContent=passed?'Passed':'Failed';td.className=passed?'pass':'fail';
  }
  result.invalid_index_rejected=groups.every(g=>registries[g][1](0xffffffff)===-1);
  if(result.passed===all.length&&result.invalid_index_rejected)result.status='passed';
 }catch(e){result.errors.push(String(e));}
 document.querySelector('#status').textContent=`${result.passed}/${all.length} passed. Full Blender test-port completeness: not established.`;
 window.__portResults=result;button.disabled=false;
});'''

def expected_cases(root=ROOT):
    """Trusted universe from checked-out test sources, not served-page totals."""
    lock=json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']
    ids=re.findall(r'\("(math_vector\.[^"]+)"',(root/'crates/blended-core/src/compat_cases.rs').read_text())
    vector=json.loads((root/'compatibility/vector-assertions.json').read_text())
    if vector['reference_commit']!=lock or vector['target_sha256']!=hashlib.sha256((root/'crates/blended-core/src/compat_cases.rs').read_bytes()).hexdigest():raise ValueError('Vector assertion contract changed')
    if [c['id'] for c in vector['cases']]!=ids:raise ValueError('Vector registry mismatch')
    result=[{'id':c['id'],'group':'legacy','expected_runtime_assertions':c['assertion_count']} for c in vector['cases']]
    for registry in GROUPS:
        filename,group=registry.manifest,registry.name
        data=json.loads((root/'compatibility'/filename).read_text())
        if data['upstream_commit']!=lock:raise ValueError('Reference revision mismatch: '+filename)
        for case in data['cases']:
            count=case.get('expected_runtime_assertions',case['assertion_count'])
            if type(count) is not int or count<0:raise ValueError('Invalid assertion execution count')
            if count==0 and (case.get('assertion_free_smoke') is not True or case['assertion_count']!=0):raise ValueError('Unreviewed zero-assertion case')
            result.append({'id':case['id'],'group':group,'expected_runtime_assertions':count})
    if not ids or len({c['id'] for c in result})!=len(result):raise ValueError('Empty or duplicate trusted case universe')
    verify_runtime_contract_bijection(root,result)
    return result,lock

def validate_result(data,expected,commit,reference):
    if data.get('source_commit')!=commit or data.get('reference_commit')!=reference:raise ValueError('Wrong source/reference revision')
    if data.get('complete_test_port') is not False:raise ValueError('False completion claim')
    cases=data.get('cases',[])
    if [(c.get('id'),c.get('group')) for c in cases]!=[(c['id'],c['group']) for c in expected]:raise ValueError('Missing, reordered, duplicate or substituted test identity')
    for actual,contract in zip(cases,expected):
        if actual.get('passed') is not True or actual.get('code')!=1:raise ValueError('WASM assertion failure: '+contract['id'])
        if actual.get('assertions')!=contract['expected_runtime_assertions']:raise ValueError('Assertion execution changed: '+contract['id'])
    for group,key in TOTAL_KEYS.items():
        total=sum(c['expected_runtime_assertions'] or 0 for c in expected if c['group']==group)
        if data.get(key)!=total:raise ValueError('Missing assertion execution: '+group)
    if not re.fullmatch('[0-9a-f]{64}',data.get('wasm_sha256','')):raise ValueError('Missing verified WASM hash')
    if data.get('status')!='passed' or data.get('passed')!=len(expected) or data.get('invalid_index_rejected') is not True or data.get('errors'):raise ValueError('Incomplete or failed execution')

def build(commit):
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Full source commit required')
    subprocess.run([sys.executable,str(ROOT/'tools/prepare_site.py')],check=True,cwd=ROOT)
    # Additional build acceptance, not a rewrite of upstream tests: cover the
    # genuine rotations/reversals accidentally absent from the original helper.
    # Diagnostic Rust/WASM builds use isolated temporary directories and cannot
    # replace the production module or silently alter reviewed test expectations.
    subprocess.run([sys.executable,str(ROOT/'tools/verify_polyfill_oracle.py'),'--output',str(ROOT/'evidence/polyfill-oracle/result.json')],check=True,cwd=ROOT)
    out=ROOT/'build/conformance';out.mkdir(parents=True,exist_ok=True)
    wasm=ROOT/'target/wasm32-unknown-unknown/release/blended_core.wasm'
    shutil.copyfile(wasm,out/'blended_core.wasm')
    legacy=json.loads((ROOT/'compatibility/ports.json').read_text())
    added=json.loads((ROOT/'compatibility/additional-ports.json').read_text())
    structures=json.loads((ROOT/'compatibility/structure-ports.json').read_text())
    expected,reference=expected_cases()
    if reference!=added['upstream_commit']:raise ValueError('Reference mismatch')
    manifest={'schema':3,'source_commit':commit,'reference_commit':reference,'groups':list(ABI),'abi':ABI,'total_keys':TOTAL_KEYS,'legacy':legacy['cases'],'complete_test_port':False,'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest()}
    for registry in GROUPS:manifest[registry.name]=json.loads((ROOT/'compatibility'/registry.manifest).read_text())['cases']
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'index.html').write_text(HTML);(out/'run.mjs').write_text(JS)
    subprocess.run([sys.executable,str(ROOT/'tools/inventory.py'),'--root',str(ROOT/'.upstream/blender'),'--name','blender','--commit',added['upstream_commit'],'--output',str(ROOT/'build/blender-inventory.json')],check=True)
    subprocess.run([sys.executable,str(ROOT/'tools/test_port_audit.py'),'--inventory',str(ROOT/'build/blender-inventory.json'),'--output',str(out/'audit.json')],check=True)
    with tarfile.open(out/'source.tar.gz','w:gz') as tar:
        for name in ('crates','tools','tests','compatibility','docs','LICENSES','Cargo.toml','Cargo.lock','rust-toolchain.toml','NOTICE.md','upstream.lock.json'):
            p=ROOT/name
            if p.exists():tar.add(p,arcname='blended/'+name,filter=lambda i:None if '__pycache__' in i.name or i.issym() else i)
        for p in (ROOT/'.upstream/blender').glob('COPYING*'):
            if p.is_file():tar.add(p,arcname='upstream-licenses/'+p.name)
    print('Built conformance site',out)
def test(url,commit,output):
    from playwright.sync_api import sync_playwright
    output.parent.mkdir(parents=True,exist_ok=True)
    expected,reference=expected_cases()
    report={'url':url,'expected_case_count':len(expected),'expected_source_commit':commit,'started_utc':datetime.now(timezone.utc).isoformat(),'status':'failed','errors':[],'complete_test_port':False}
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
            assert page.locator('#cases tr').count()==len(expected),'Incomplete or unexpected test registry'
            page.locator('#run').click();page.wait_for_function('window.__portResults !== undefined',timeout=60000)
            data=page.evaluate('window.__portResults');report['wasm']=data
            validate_result(data,expected,commit,reference)
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
