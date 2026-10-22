#!/usr/bin/env python3
"""Fetch pinned checkouts. Reference inventories retain LFS pointers explicitly."""
import argparse
import json
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
def run(*args, cwd=None, env=None):
    result=subprocess.run(args,cwd=cwd,env=env,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(f'Command {args!r} failed ({result.returncode})\n{result.stdout}\n{result.stderr}')
    return result.stdout.strip()
def fetch(name,entry):
    dst=ROOT/'.upstream'/name
    dst.parent.mkdir(exist_ok=True)
    if dst.exists():
        if not (dst/'.git').exists():raise RuntimeError(f'Not a git checkout: {dst}')
        if run('git','status','--porcelain',cwd=dst):raise RuntimeError(f'Dirty checkout: {dst}')
        if run('git','rev-parse','HEAD',cwd=dst)!=entry['commit']:raise RuntimeError('Commit mismatch')
        return dst
    dst.mkdir()
    env=os.environ.copy()
    if name in {'blender','cycles'}:
        # Source discovery is not a fixture-enabled reference run. GitHub's
        # Blender mirror does not supply every LFS object. Preserve pointers
        # as unavailable fixtures rather than downloading or faking payloads.
        env['GIT_LFS_SKIP_SMUDGE']='1'
        print(f'{name}: metadata checkout; LFS pointers retained, fixtures NOT validated',flush=True)
    run('git','init',str(dst),env=env)
    run('git','remote','add','origin',f'https://github.com/{entry["repository"]}.git',cwd=dst,env=env)
    run('git','fetch','--depth=1','origin',entry['commit'],cwd=dst,env=env)
    run('git','checkout','--detach','FETCH_HEAD',cwd=dst,env=env)
    if run('git','rev-parse','HEAD',cwd=dst)!=entry['commit']:raise RuntimeError('Commit mismatch')
    return dst
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('names',nargs='+',choices=['blender','cycles','solarxy'])
    args=p.parse_args()
    lock=json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']
    for name in args.names:print(fetch(name,lock[name]),flush=True)
