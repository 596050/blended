#!/usr/bin/env python3
"""Compile the actual signed-zero port and prove an incorrect hash is rejected.

A negative test succeeds only for the expected rustc const-evaluation failure,
not for a missing compiler, target, syntax error or arbitrary build failure.
"""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main(output):
    output.parent.mkdir(parents=True,exist_ok=True)
    source=ROOT/'crates/blended-core/src/compile_time_cases.rs'
    result={'reference_commit':json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']['blender']['commit'],'source_assertion':'source/blender/blenlib/tests/BLI_math_vector_test.cc:219','target_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'complete_blender_test_port':False,'checks':[],'status':'failed'}
    with tempfile.TemporaryDirectory(prefix='blended-static-') as td:
        temp=Path(td)
        for name in ['Cargo.toml','Cargo.lock','rust-toolchain.toml','crates']:
            src=ROOT/name;dst=temp/name
            if src.is_dir():shutil.copytree(src,dst)
            else:shutil.copyfile(src,dst)
        def check(target,negative):
            command=['cargo','check','--locked','-p','blended-core']+(['--target',target] if target else [])
            run=subprocess.run(command,cwd=temp,capture_output=True,text=True,timeout=120)
            label=target or 'native';text=run.stdout+run.stderr
            logfile=output.parent/('static-'+label+('-negative' if negative else '-positive')+'.log');logfile.write_text(text)
            expected=run.returncode!=0 and 'E0080' in text and 'Blender vector signed-zero hash invariant' in text and 'compile_time_cases.rs' in text
            passed=expected if negative else run.returncode==0
            result['checks'].append({'target':label,'negative_mutation':negative,'returncode':run.returncode,'passed':passed,'log':logfile.name,'log_sha256':hashlib.sha256(text.encode()).hexdigest()})
            if not passed:raise RuntimeError('Unexpected compiler result: '+label)
        try:
            for t in [None,'wasm32-unknown-unknown']:check(t,False)
            p=temp/'crates/blended-core/src/hashing.rs';s=p.read_text()
            token='if value==0.0 {0} else {value.to_bits() as u64}'
            if s.count(token)!=1:raise ValueError('Hash implementation changed; review mutation')
            p.write_text(s.replace(token,'value.to_bits() as u64'))
            for t in [None,'wasm32-unknown-unknown']:check(t,True)
            result['status']='passed'
        except Exception as e:result['failure']=str(e)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='passed' else 1
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(main(a.output))
