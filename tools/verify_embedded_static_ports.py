#!/usr/bin/env python3
"""Compile original embedded constant assertions on native and WASM targets.

The positive build uses unmodified reviewed sources. Each negative shadow changes
only one case's input constant, leaving its assertion and all expected values
unchanged. It must fail at that exact assertion, not due to a missing compiler.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def scoped_mutation(text:str,case:dict)->str:
    marker='pub fn '+case['rust_function']+'('
    if text.count(marker)!=1:raise ValueError('Missing or duplicate enclosing function')
    start=text.index(marker);end=text.find('\npub fn ',start+len(marker));end=len(text) if end<0 else end
    body=text[start:end]
    if body.count(case['target_assertion'])!=1:raise ValueError('Missing or duplicate constant assertion')
    before=case['negative_fixture_before'];after=case['negative_fixture_after']
    if body.count(before)!=1 or before==after:raise ValueError('Wrong mutation preimage')
    return text[:start]+body.replace(before,after,1)+text[end:]

def verify(output:Path)->dict:
    from assertion_fidelity import contracts
    from inventory import scan_cpp
    reviewed=contracts(ROOT)
    manifest=json.loads((ROOT/'compatibility/compile-time-ports.json').read_text())
    cases=[c for c in manifest['cases'] if c.get('embedded')]
    if len(cases)!=5:raise ValueError('Unexpected embedded assertion universe')
    for c in cases:
        path=ROOT/c['target_path'];src=(ROOT/'tests/upstream/blender'/Path(c['path']).name).read_text()
        if c['source_condition'] not in src.splitlines()[c['line']-1]:raise ValueError('Wrong source condition')
        if c['id'] not in {x['identity'] for x in scan_cpp(src,c['path'])}:raise ValueError('Source identity missing')
        if not any(x['source_path']==c['path'] and x['target_path']==c['target_path'] and c['id'] in x['case_ids'] for x in reviewed['contracts']):raise ValueError('Missing reviewed constant mapping')
        scoped_mutation(path.read_text(),c)
    output.parent.mkdir(parents=True,exist_ok=True)
    report={'reference_commit':manifest['upstream_commit'],'project_commit':os.environ.get('GITHUB_SHA'),'scope':'five embedded constant assertions; not runtime tests','complete_blender_test_port':False,'status':'failed','positive_builds':[],'negative_checks':[]}
    def compile_at(cwd:Path,target:str,logname:str):
        cmd=['cargo','check','--locked','-p','blended-core','--lib']
        if target!='native':cmd+=['--target',target]
        env={**os.environ,'CARGO_TERM_COLOR':'never','CARGO_TARGET_DIR':str(cwd/'_target')}
        run=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        log=output.parent/logname;log.write_text(run.stdout)
        return run,{'target':target,'returncode':run.returncode,'log':logname,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
    with tempfile.TemporaryDirectory(prefix='blended-embedded-static-') as temp:
        root=Path(temp)
        for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
            p=ROOT/name
            if p.is_dir():shutil.copytree(p,root/name)
            else:shutil.copyfile(p,root/name)
        for target in ['native','wasm32-unknown-unknown']:
            run,row=compile_at(root,target,f'embedded-{target}-positive.log');row['passed']=run.returncode==0;report['positive_builds'].append(row)
            if run.returncode:raise RuntimeError('Positive build failed: '+target)
        for i,c in enumerate(cases):
            p=root/c['target_path'];before=p.read_text();p.write_text(scoped_mutation(before,c))
            try:
                for target in ['native','wasm32-unknown-unknown']:
                    run,row=compile_at(root,target,f'embedded-{i}-{target}-negative.log')
                    row.update({'source_path':c['path'],'source_assertion':c['id'],'enclosing_function':c['rust_function'],'target_path':c['target_path'],'passed':run.returncode!=0 and 'E0080' in run.stdout and c['negative_error'] in run.stdout})
                    report['negative_checks'].append(row)
                    if not row['passed']:raise RuntimeError('Did not reject the exact false constant: '+c['id'])
            finally:p.write_text(before)
    report['status']='passed';output.write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(verify(args.output),indent=2))
