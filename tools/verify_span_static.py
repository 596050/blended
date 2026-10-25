#!/usr/bin/env python3
"""Execute original compile-time span contracts, not runtime substitutes.

Positive builds compile the unmodified reviewed translation. Every negative
shadow alters only the input/operation of one existing predicate; expected
assertion values and the predicate mechanism stay unchanged. An unrelated
compiler error is not accepted as successful detection.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=(
 ('const _:()=assert!(SPAN.at(2)==1);','const _:()=assert!(SPAN.at(1)==1);','E0080'),
 ('const _:()=assert!(SPAN.len()==3);','const _:()=assert!(SPAN.take_front(2).len()==3);','E0080'),
 ('const _:()=assert!(SPAN.slice(1,2).len()==2);','const _:()=assert!(SPAN.slice(1,1).len()==2);','E0080'),
 ('const _:()=assert!(!SPAN.has_duplicates_linear());','const _:()=assert!(!Span::from_slice(&[3,3,1]).has_duplicates_linear());','E0080'),
 ('const IC:bool=SPAN.first_index(1)==2;','const IC:bool=SPAN.first_index(3)==2;','E0080'),
 ('const _:fn()=require_into::<Src0,Dst0>;','const _:fn()=require_into::<Dst0,Src0>;','E0277'),
 ('const _:fn()=require_into::<Src1,Dst1>;','const _:fn()=require_into::<Dst1,Src1>;','E0277'),
 ('const _:fn()=require_into::<Src2,Dst2>;','const _:fn()=require_into::<Dst2,Src2>;','E0277'),
 ('const _:fn()=require_into::<Src3,Dst3>;','const _:fn()=require_into::<Dst3,Src3>;','E0277'),
 ('const _:fn()=require_into::<Src4,Dst4>;','const _:fn()=require_into::<Dst4,Src4>;','E0277'),
 ('not_into!(Src5,Dst5);','not_into!(Dst5,Src5);','E0283'),
 ('not_into!(Src6,Dst6);','not_into!(Dst6,Src6);','E0283'),
 ('not_into!(Src7,Dst7);','not_into!(Src3,Dst3);','E0283'),
)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def diagnostics(text):
    rows=[]
    for line in text.splitlines():
        try:row=json.loads(line)
        except json.JSONDecodeError:continue
        if row.get('reason')=='compiler-message' and row.get('message',{}).get('level')=='error':rows.append(row['message'])
    return rows

def run(output):
    from assertion_fidelity import contracts
    from static_port_registry import load_static_cases
    from inventory import scan_cpp
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    reviewed=contracts(ROOT);data=json.loads((ROOT/'compatibility/span-static-ports.json').read_text());cases=data['cases']
    original=ROOT/'crates/blended-core/src/span_cases.rs';before=original.read_text()
    if len(cases)!=13 or [c['condition_index'] for c in cases]!=list(range(13)):raise ValueError('Original predicate universe changed')
    if len(load_static_cases(ROOT))!=19:raise ValueError('Missing historical or new compile-time mappings')
    cpp=(ROOT/'tests/upstream/blender/BLI_span_test.cc').read_text()
    source_keys={(c['identity'],c['line']) for c in scan_cpp(cpp,cases[0]['path']) if c['kind']=='static_assert'}
    if source_keys!={(c['id'],c['line']) for c in cases}:raise ValueError('Source compile-time predicates differ')
    for case,(old,new,code) in zip(cases,MUTATIONS):
        if before.count(old)!=1 or old==new:raise ValueError('Ambiguous mutation target '+case['id'])
        if not any(c['source_path']==case['path'] and c['target_path']==case['target_path'] and case['id'] in c['case_ids'] for c in reviewed['contracts']):raise ValueError('Predicate not reviewed')
        if cpp.splitlines()[case['line']-1].strip()!=case['source_condition']:raise ValueError('Original condition changed')
    report={'status':'failed','complete_blender_test_port':False,'scope':'13 original compile-time predicates, not 13 runtime tests','reference_commit':data['upstream_commit'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'target_sha256':sha(original),'rustc':subprocess.check_output(['rustc','--version','--verbose'],text=True),'positive_builds':[],'negative_checks':[]}
    def check(root,target,name):
        args=['cargo','check','--locked','-p','blended-core','--lib','--message-format=json']
        if target!='native':args+=['--target',target]
        env={**os.environ,'CARGO_TERM_COLOR':'never','CARGO_TARGET_DIR':str(root/'_target')}
        process=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True,timeout=180)
        log=output.parent/(name+'.log');log.write_text(process.stdout+process.stderr)
        return process,dict(target=target,returncode=process.returncode,log=log.name,log_sha256=sha(log)),diagnostics(process.stdout)
    try:
        with tempfile.TemporaryDirectory(prefix='blended-span-static-') as d:
            root=Path(d)
            for name in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
                source=ROOT/name
                if source.is_dir():shutil.copytree(source,root/name)
                else:shutil.copyfile(source,root/name)
            for target in ('native','wasm32-unknown-unknown'):
                process,row,errors=check(root,target,target+'-positive');row['passed']=process.returncode==0 and not errors;report['positive_builds'].append(row)
                if not row['passed']:raise RuntimeError('Unmodified static predicates failed: '+target)
            path=root/'crates/blended-core/src/span_cases.rs'
            for case,(old,new,expected_code) in zip(cases,MUTATIONS):
                changed=before.replace(old,new);path.write_text(changed)
                try:
                    for target in ('native','wasm32-unknown-unknown'):
                        process,row,errors=check(root,target,f'{case["condition_index"]}-{target}-negative')
                        # Rust points into the original predicate or its local macro.
                        # Reject every other diagnostic code, missing-module errors,
                        # toolchain failures and failures in unrelated source files.
                        codes=[e.get('code',{}).get('code') for e in errors]
                        source_matches=all(any(s.get('file_name','').endswith('span_cases.rs') for s in e.get('spans',[])) for e in errors)
                        passed=process.returncode!=0 and bool(errors) and set(codes)=={expected_code} and source_matches
                        row.update(source_assertion=case['id'],source_line=case['line'],category=case['category'],expected_error_code=expected_code,observed_error_codes=codes,mutation_before=old,mutation_after=new,mutated_sha256=sha(path),passed=passed)
                        report['negative_checks'].append(row)
                        if not passed:raise RuntimeError('Wrong failure for original predicate '+case['id']+' on '+target)
                finally:path.write_text(before)
            if sha(path)!=sha(original):raise ValueError('Original source not restored')
        report.update(status='passed',original_predicates=13,native_predicates=13,wasm_predicates=13,negative_compilations=26,mutations_change_inputs_not_expected_values=True)
    except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
