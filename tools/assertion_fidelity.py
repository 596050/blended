#!/usr/bin/env python3
"""Independent assertion transcripts for the mapped subset. Never a full-parity certificate.

The C++ overlay records original values and still invokes pinned GoogleTest.
The Rust shadow records the corresponding values without modifying checked-in tests.
Exact comparisons stay exact; floating outputs use the original assertion rule.
Every diagnostic transformation is saved for inspection.
"""
from __future__ import annotations
import argparse, difflib, hashlib, json, math, re, shutil, struct, sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def contracts(root:Path):
    data=json.loads((root/'compatibility/assertion-contracts.lock.json').read_text())
    pin=json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']
    if data['reference_commit']!=pin:raise ValueError('Contract/reference mismatch')
    for c in data['contracts']:
        snapshot=root/'tests/upstream/blender'/Path(c['source_path']).name
        if digest(snapshot)!=c['source_sha256']:raise ValueError('Source snapshot changed: '+str(snapshot))
        if digest(root/c['target_path'])!=c['target_sha256']:raise ValueError('Reviewed Rust assertions changed: '+c['target_path'])
    return data

def cpp(root:Path,upstream:Path):
    data=contracts(root);records=[]
    for c in data['contracts']:
        p=upstream/c['source_path'];before=p.read_text()
        if digest(p)!=c['source_sha256']:raise ValueError('Actual upstream source differs from reviewed snapshot')
        header=(root/'tools/fidelity/trace.hh').resolve().as_posix()
        # Include after original includes but before namespaces. Test bodies stay byte-for-byte intact.
        at=before.index('namespace ')
        after=before[:at]+f'#include "{header}"\n'+before[at:]
        p.write_text(after)
        records.append({'source':c['source_path'],'original_sha256':c['source_sha256'],'overlay_sha256':digest(p)})
    out=root/'evidence/fidelity';out.mkdir(parents=True,exist_ok=True)
    (out/'cpp-overlay.json').write_text(json.dumps({'reference':data['reference_commit'],'changes':records,'scope':'include-only diagnostic overlays; no original test-body edits'},indent=2)+'\n')

def calls(text:str,token:str):
    """Locate balanced calls, preserving parentheses inside string literals."""
    pos=0
    while (start:=text.find(token,pos))>=0:
        i=start+len(token);depth=1;quote=None;escape=False
        while i<len(text) and depth:
            c=text[i]
            if quote:
                if escape:escape=False
                elif c=='\\':escape=True
                elif c==quote:quote=None
            elif c=='"':quote=c
            elif c=='(':depth+=1
            elif c==')':depth-=1
            i+=1
        if depth:raise ValueError('Unbalanced diagnostic call')
        yield start,i,text[start+len(token):i-1]
        pos=i

def shadow(root:Path,out:Path):
    contracts(root)
    if out.exists():raise ValueError('Refusing to overwrite shadow checkout')
    out.mkdir(parents=True)
    for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
        src=root/name;dst=out/name
        if src.is_dir():shutil.copytree(src,dst)
        else:shutil.copyfile(src,dst)
    src=out/'crates/blended-core/src'
    shutil.copyfile(root/'tools/fidelity/trace.rs',src/'fidelity_trace.rs')
    with (src/'lib.rs').open('a') as f:f.write('\npub mod fidelity_trace;\n')
    modifications=[]
    for name in ['additional_cases.rs','structure_cases.rs']:
        p=src/name;before=p.read_text();after=before
        changes={
          'macro_rules! eq ': 'macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::eq($a,$b),stringify!($a == $b),line!());}};} ',
          'macro_rules! gt ': 'macro_rules! gt {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::gt($a,$b),stringify!($a > $b),line!());}};} ',
          'macro_rules! feq ': 'macro_rules! feq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::float_eq($a as f32,$b as f32),stringify!($a ~= $b),line!());}};} ',
          'macro_rules! near ': 'macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{$r.check(crate::fidelity_trace::near($a as f64,$b as f64,$e as f64),stringify!($a ~= $b within $e),line!());}};} ',
          'macro_rules! yes ': 'macro_rules! yes {($r:expr,$a:expr)=>{{$r.check(crate::fidelity_trace::boolean("TRUE",$a),stringify!($a),line!());}};} ',
          'macro_rules! no ': 'macro_rules! no {($r:expr,$a:expr)=>{{$r.check(crate::fidelity_trace::boolean("FALSE",$a),stringify!(!$a),line!());}};} ',
        }
        # Preserve the original scalar EQ expected-value cast. Structure EQ is same-type.
        if name=='additional_cases.rs':changes['macro_rules! eq ']='macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let a=$a;$r.check(crate::fidelity_trace::eq(a,$b as _),stringify!($a == $b),line!());}};} '
        for prefix,replacement in changes.items():
            lines=after.splitlines();matches=[i for i,s in enumerate(lines) if s.startswith(prefix)]
            if matches:
                if len(matches)!=1:raise ValueError('Ambiguous macro overlay')
                lines[matches[0]]=replacement.rstrip();after='\n'.join(lines)+'\n'
        p.write_text(after);modifications.append((name,before,after))
    p=src/'compat_cases.rs';before=p.read_text();after=before
    for start,end,body in reversed(list(calls(before,'r.check('))):
        # The last argument is a diagnostic string; nested commas belong to the expression.
        match=re.fullmatch(r'(.*),\s*("(?:[^"\\]|\\.)*")',body,re.S)
        if not match:raise ValueError('Unrecognised vector assertion')
        expr,label=match.groups()
        if expr.startswith('float_eq('):expr='crate::fidelity_trace::'+expr
        elif 'f64::from(a[i])' in expr:expr='crate::fidelity_trace::near(f64::from(a[i]),f64::from(b[i]),f64::from(1e-6_f32))'
        elif expr.endswith('.is_nan()'):expr='crate::fidelity_trace::boolean("TRUE",'+expr+')'
        elif expr.count('==')==1:
            a,b=expr.split('==');expr=f'crate::fidelity_trace::eq({a},{b})'
        else:raise ValueError('Unreviewed vector overlay: '+expr)
        after=after[:start]+f'r.check({expr},{label})'+after[end:]
    p.write_text(after);modifications.append(('compat_cases.rs',before,after))
    examples=out/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
    (examples/'assertion_trace.rs').write_text('fn main(){print!("{}",blended_core::fidelity_trace::run_all());}\n')
    evidence=root/'evidence/fidelity';evidence.mkdir(parents=True,exist_ok=True)
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=n,tofile='shadow/'+n)) for n,a,b in modifications)
    (evidence/'rust-overlay.patch').write_text(patch)
    (evidence/'rust-overlay.json').write_text(json.dumps({'scope':'build-only recording helpers; checked-in production test bodies unchanged','input_hashes':{n:hashlib.sha256(a.encode()).hexdigest() for n,a,_ in modifications},'patch_sha256':hashlib.sha256(patch.encode()).hexdigest()},indent=2)+'\n')

def normal(value):
    if isinstance(value,list):return tuple(normal(v) for v in value)
    if isinstance(value,dict):return tuple((k,normal(v)) for k,v in sorted(value.items()))
    if not isinstance(value,str):raise ValueError('Malformed tagged trace value')
    if value.startswith('i:'):return Fraction(int(value[2:]))
    if value.startswith('f:'):
        n=struct.unpack('>d',bytes.fromhex(value[2:]))[0]
        if math.isnan(n):return 'nan'
        if math.isinf(n):return 'positive_infinity' if n>0 else 'negative_infinity'
        return Fraction(n)
    if value in ['none','b:0','b:1']:return value
    raise ValueError('Unknown trace value: '+value)

def f32_order(value):
    if not isinstance(value,Fraction):return None
    bits=struct.unpack('>I',struct.pack('>f',float(value)))[0]
    return ((~bits+1)&0xffffffff) if bits&0x80000000 else bits|0x80000000

def equivalent(kind,a,b,fixed=()):
    if fixed and any(is_fixed and x!=y for is_fixed,x,y in zip(fixed,a,b)):return False
    if a==b:return True
    if kind=='FLOAT_EQ':
        return all(x==y or (isinstance(x,Fraction) and isinstance(y,Fraction) and abs(f32_order(x)-f32_order(y))<=4) for x,y in zip(a,b))
    if kind=='NEAR':
        return a[2]==b[2] and isinstance(a[2],Fraction) and all(x==y or (isinstance(x,Fraction) and isinstance(y,Fraction) and abs(x-y)<=a[2]) for x,y in zip(a[:2],b[:2]))
    return False

def compare(reference:list,port:list,expected:list):
    ref=defaultdict(list);got=defaultdict(list)
    for row in reference:ref[row['case']].append(row)
    for row in port:got[row['case']].append(row)
    ids=[c['id'] for c in expected]
    if len(set(ids))!=len(ids) or not ids:raise ValueError('Invalid expected case universe')
    if set(ref)!=set(ids) or set(got)!=set(ids):raise ValueError('Missing or unexpected case identity')
    checked=0;approx=[]
    for contract in expected:
        key=contract['id'];a,b=ref[key],got[key];n=contract['expected_runtime_assertions']
        if len(a)!=n or len(b)!=n:raise ValueError('Missing, duplicate or extra assertion: '+key)
        for i,(r,p) in enumerate(zip(a,b)):
            if r.get('kind')!=p.get('kind'):raise ValueError(f'Assertion kind differs: {key}:{i}')
            kind=r['kind'];arity={'EQ':2,'GT':2,'FLOAT_EQ':2,'NEAR':3,'TRUE':1,'FALSE':1}.get(kind)
            if not arity or len(r['values'])!=arity or len(p['values'])!=arity:raise ValueError('Malformed assertion arity')
            if r.get('passed') is not True or p.get('passed') is not True:raise ValueError('Failed assertion: '+key)
            rv,pv=normal(r['values']),normal(p['values'])
            options=[pv]
            if kind in ['EQ','FLOAT_EQ']:options.append(tuple(reversed(pv)))
            if kind=='NEAR':options.append((pv[1],pv[0],pv[2]))
            if not any(equivalent(kind,rv,v,r.get('fixed',())) for v in options):raise ValueError(f'Assertion values/tolerance differ: {key}:{i}: {r["values"]} != {p["values"]}')
            if rv not in options:approx.append({'case':key,'ordinal':i,'kind':kind,'reference':r['values'],'port':p['values']})
            checked+=1
    return {'status':'passed','case_count':len(ids),'assertions_compared':checked,'floating_differences_within_original_rule':approx,'complete_blender_test_port':False,'scope':'mapped runtime subset; equality operand order may differ; empty-range start normalised by upstream equality; not a proof of all behaviour'}

def load_tape(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]

def browser(wasm:Path,output:Path):
    from playwright.sync_api import sync_playwright
    import base64
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        tape=page.evaluate('''async data=>{const bytes=Uint8Array.from(atob(data),c=>c.charCodeAt(0));const {instance}=await WebAssembly.instantiate(bytes,{});const w=instance.exports;const n=w.blended_fidelity_run();const ptr=w.blended_fidelity_ptr();return new TextDecoder().decode(new Uint8Array(w.memory.buffer,ptr,n));}''',base64.b64encode(wasm.read_bytes()).decode())
        output.write_text(tape)
        output.with_suffix('.environment.json').write_text(json.dumps({'browser':b.version,'wasm_sha256':digest(wasm),'errors':errors,'mode':'local diagnostic overlay, not public deployment'},indent=2)+'\n')
        b.close()
        if errors:raise ValueError('Browser errors')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['cpp','shadow','compare','browser']);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--upstream',type=Path);p.add_argument('--output',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--port',type=Path);p.add_argument('--wasm',type=Path);a=p.parse_args()
    if a.command=='cpp':cpp(a.root,a.upstream)
    elif a.command=='shadow':shadow(a.root,a.output)
    elif a.command=='browser':browser(a.wasm,a.output)
    else:
        sys.path.insert(0,str(a.root/'tools'));from port_workbench import expected_cases
        expected,pin=expected_cases(a.root)
        report={'status':'failed','complete_blender_test_port':False,'reference_commit':pin,'reference_trace_sha256':digest(a.reference),'port_trace_sha256':digest(a.port)}
        try:report.update(compare(load_tape(a.reference),load_tape(a.port),expected))
        except Exception as e:report['failure']=str(e)
        a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
        return 0 if report['status']=='passed' else 1
    return 0
if __name__=='__main__':sys.exit(main())
