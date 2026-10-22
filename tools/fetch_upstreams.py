#!/usr/bin/env python3
"""Fetch pinned reference checkouts without overwriting dirty source."""
import argparse
import json
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()
def fetch(name, entry):
    dst = ROOT / '.upstream' / name
    dst.parent.mkdir(exist_ok=True)
    if dst.exists():
        if not (dst / '.git').exists(): raise RuntimeError(f'Not a git checkout: {dst}')
        if run('git','status','--porcelain',cwd=dst): raise RuntimeError(f'Dirty checkout: {dst}')
        if run('git','rev-parse','HEAD',cwd=dst) != entry['commit']: raise RuntimeError('Commit mismatch')
        return dst
    dst.mkdir()
    run('git','init',str(dst))
    run('git','remote','add','origin',f'https://github.com/{entry["repository"]}.git',cwd=dst)
    run('git','fetch','--depth=1','origin',entry['commit'],cwd=dst)
    run('git','checkout','--detach','FETCH_HEAD',cwd=dst)
    if run('git','rev-parse','HEAD',cwd=dst) != entry['commit']: raise RuntimeError('Commit mismatch')
    return dst
if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('names',nargs='+',choices=['blender','cycles','solarxy'])
    args=p.parse_args()
    lock=json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']
    for name in args.names: print(fetch(name,lock[name]),flush=True)
