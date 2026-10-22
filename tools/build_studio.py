#!/usr/bin/env python3
"""Build Solarxy from pinned source as an attributed foundation, not Blender parity."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
def run(args,cwd=ROOT):
    print('+',' '.join(map(str,args)),flush=True)
    subprocess.run(args,cwd=cwd,check=True)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',default='/blended/studio/')
    p.add_argument('--commit',required=True)
    args=p.parse_args()
    if not args.base.startswith('/') or not args.base.endswith('/') or '..' in args.base:p.error('Invalid base URL path')
    solar=ROOT/'.upstream/solarxy';web=solar/'web'
    lock=json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=solar,text=True).strip()
    if actual!=lock['solarxy']['commit']:raise RuntimeError('Solarxy source mismatch')
    changes=[]
    routes={'/app':'app.html','/player':'player.html','/roadmap':'roadmap.html','/references':'references.html','/player.html':'player.html','/app.html':'app.html'}
    for file in sorted(web.rglob('*')):
        if not file.is_file() or file.suffix not in {'.html','.tsx','.ts'}:continue
        if any(x in file.parts for x in ('node_modules','dist')):continue
        old=file.read_text();new=old
        for src,target in routes.items():
            for q in ('"',"'"):new=new.replace(q+src+q,q+args.base+target+q)
        if new!=old:file.write_text(new);changes.append(file.relative_to(solar).as_posix())
    run(['cargo','test','--locked','-p','solarxy-core','-p','solarxy-kernel','-p','solarxy-graph','--lib'],solar)
    run(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','solarxy-web'],solar)
    run(['wasm-bindgen','--target','web','--out-dir','web/src/wasm/pkg','target/wasm32-unknown-unknown/release/solarxy_web.wasm'],solar)
    run(['npm','ci'],web)
    run(['npm','test'],web)
    run(['npm','run','build','--','--base',args.base],web)
    destination=ROOT/'site/studio'
    shutil.copytree(web/'dist',destination)
    source_stage=ROOT/'build/solarxy-source';source_stage.mkdir(parents=True,exist_ok=False)
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=solar).decode().split('\0')
    for path in filter(None,tracked):
        src=solar/path
        if src.is_file() and not src.is_symlink():
            dest=source_stage/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    (source_stage/'BLENDED-PATCHES.json').write_text(json.dumps({'base':args.base,'changed_files':changes},indent=2))
    (ROOT/'site/source').mkdir(exist_ok=True)
    shutil.make_archive(str(ROOT/'site/source/solarxy-modified-source'),'gztar',root_dir=source_stage)
    shutil.copy2(solar/'LICENSE',destination/'LICENSE.txt')
    shutil.copy2(solar/'LICENSE',ROOT/'site/LICENSE.txt')
    shutil.copy2(solar/'THIRD-PARTY-NOTICES.md',destination/'THIRD-PARTY-NOTICES.md')
    (ROOT/'site/.nojekyll').touch()
    wasm=ROOT/'site/compat/blended_core.wasm'
    if not wasm.is_file():raise RuntimeError('Missing Blended compatibility WASM')
    manifest={'schema':1,'status':'built_not_deployment_verified','studio_built':True,'source_commit':args.commit,'built_utc':datetime.now(timezone.utc).isoformat(),'deployed_test_status':'not_run','upstreams':lock,'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'blender_feature_parity':False}
    (ROOT/'site/build.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
