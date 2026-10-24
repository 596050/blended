#!/usr/bin/env python3
"""Full-event, bounded-memory reconciliation. No sampling or hash-only substitute."""
from __future__ import annotations
import argparse,base64,gzip,hashlib,json,shutil
from pathlib import Path
CHUNK_EVENTS=256

def file_sha(path:Path)->str:
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def index_trace(path:Path,expected:list[dict])->dict:
    counts={c['id']:c['expected_runtime_assertions'] for c in expected}
    if not counts or len(counts)!=len(expected):raise ValueError('Invalid expected case universe')
    if any(type(n) is not int or n<0 for n in counts.values()):raise ValueError('Invalid assertion count')
    result,active,count,start={},None,0,0
    with path.open('rb') as stream:
        while True:
            offset=stream.tell();raw=stream.readline()
            if not raw:break
            if not raw.strip():continue
            row=json.loads(raw);key,kind=row.get('case'),row.get('kind')
            if key not in counts:raise ValueError('Unexpected case identity')
            if kind=='CASE_BEGIN':
                if active is not None or key in result or row.get('passed') is not True or row.get('values')!=[]:raise ValueError('Invalid/duplicate case begin')
                active,count,start=key,0,stream.tell()
            elif kind=='CASE_END':
                if active!=key or row.get('passed') is not True or row.get('values')!=[]:raise ValueError('Invalid/failed case end')
                if count!=counts[key]:raise ValueError('Missing, duplicate or extra assertion: '+key)
                result[key]=(start,offset,count);active=None
            else:
                if active!=key:raise ValueError('Assertion outside an executed case')
                count+=1
                if count>counts[key]:raise ValueError('Excess assertion events: '+key)
        if active is not None or set(result)!=set(counts):raise ValueError('Unexecuted or unfinished case')
    return result

def case_events(stream,bounds):
    start,end,count=bounds;stream.seek(start);seen=0
    while stream.tell()<end:
        raw=stream.readline()
        if not raw:raise ValueError('Truncated trace after indexing')
        if raw.strip():seen+=1;yield json.loads(raw)
    if stream.tell()!=end or seen!=count:raise ValueError('Trace changed after indexing')

def compare_files(reference:Path,port:Path,expected:list[dict])->dict:
    from assertion_fidelity import compare
    before=(file_sha(reference),file_sha(port))
    ri,pi=index_trace(reference,expected),index_trace(port,expected)
    checked,differences=0,[]
    with reference.open('rb') as rf,port.open('rb') as pf:
        for contract in expected:
            key=contract['id'];rr=iter(case_events(rf,ri[key]));pr=iter(case_events(pf,pi[key]));base=0;total=contract['expected_runtime_assertions']
            while base<total:
                size=min(CHUNK_EVENTS,total-base)
                r=[next(rr) for _ in range(size)];p=[next(pr) for _ in range(size)]
                # The existing reviewed comparator checks every event, unchanged.
                batch=compare(r,p,[{'id':key,'expected_runtime_assertions':size}])
                for item in batch['floating_differences_within_original_rule']:
                    item['ordinal']+=base;differences.append(item)
                checked+=batch['assertions_compared'];base+=size
            sentinel=object()
            if next(rr,sentinel) is not sentinel or next(pr,sentinel) is not sentinel:raise ValueError('Additional events after expected case end')
    if before!=(file_sha(reference),file_sha(port)):raise ValueError('Trace changed during reconciliation')
    return {'status':'passed','case_count':len(expected),'case_boundaries_verified':True,
            'assertion_free_cases':[c['id'] for c in expected if c['expected_runtime_assertions']==0],
            'assertions_compared':checked,'floating_differences_within_original_rule':differences,
            'complete_blender_test_port':False,
            'comparison_mode':'all events, bounded batches using original reviewed comparator; no sampling',
            'scope':'mapped runtime subset; original comparison normalisations retained; not proof of all behaviour'}

def browser_tape(wasm:Path,output:Path):
    """Transfer the complete tape without a giant DevTools response."""
    from playwright.sync_api import sync_playwright
    output.parent.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        length=page.evaluate('''async data=>{const {instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports,n=w.blended_fidelity_run(),ptr=w.blended_fidelity_ptr();window.__fidelityTape={w,n,ptr};return n;}''',base64.b64encode(wasm.read_bytes()).decode())
        if type(length) is not int or length<=0:raise ValueError('Missing executed browser trace')
        with output.open('wb') as stream:
            for offset in range(0,length,262144):
                count=min(262144,length-offset)
                # Encodings are ASCII. Chunks can split JSON lines without loss.
                chunk=page.evaluate('''({offset,count})=>{const{w,n,ptr}=window.__fidelityTape;if(offset+count>n)throw Error('Trace bounds');return new TextDecoder('ascii',{fatal:true}).decode(new Uint8Array(w.memory.buffer,ptr+offset,count));}''',{'offset':offset,'count':count})
                raw=chunk.encode('ascii')
                if len(raw)!=count:raise ValueError('Truncated browser trace chunk')
                stream.write(raw)
        output.with_suffix('.environment.json').write_text(json.dumps({'browser':browser.version,'wasm_sha256':file_sha(wasm),'trace_bytes':length,'trace_sha256':file_sha(output),'errors':errors,'transfer':'complete ASCII tape in bounded chunks; no sampled events','mode':'local diagnostic overlay, not public deployment'},indent=2)+'\n')
        browser.close()
        if errors:raise ValueError('Browser errors')

def pack(directory:Path):
    """Keep every event; verify decompressed SHA/size before removing raw copies."""
    records=[]
    for path in sorted(directory.glob('*.jsonl')):
        source_hash,size=file_sha(path),path.stat().st_size;target=path.with_suffix('.jsonl.gz')
        if target.exists():raise ValueError('Refusing to overwrite compressed evidence')
        with path.open('rb') as source,target.open('wb') as sink:
            with gzip.GzipFile(filename='',fileobj=sink,mode='wb',mtime=0) as packed:shutil.copyfileobj(source,packed,length=1024*1024)
        digest,restored=hashlib.sha256(),0
        with gzip.open(target,'rb') as stream:
            while block:=stream.read(1024*1024):restored+=len(block);digest.update(block)
        if digest.hexdigest()!=source_hash or restored!=size:raise ValueError('Lossless evidence verification failed')
        records.append({'raw_name':path.name,'raw_bytes':size,'raw_sha256':source_hash,'compressed_name':target.name,'compressed_bytes':target.stat().st_size,'compressed_sha256':file_sha(target)})
    if not records:raise ValueError('No raw transcripts available to preserve')
    (directory/'TRACE-STORAGE.json').write_text(json.dumps({'schema':1,'all_events_preserved':True,'compression':'gzip, lossless','verification':'full decompressed SHA-256 and byte count checked before raw removal','records':records},indent=2)+'\n')
    for record in records:(directory/record['raw_name']).unlink()
    return records

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);a=parser.parse_args();print(json.dumps(pack(a.directory),indent=2))
