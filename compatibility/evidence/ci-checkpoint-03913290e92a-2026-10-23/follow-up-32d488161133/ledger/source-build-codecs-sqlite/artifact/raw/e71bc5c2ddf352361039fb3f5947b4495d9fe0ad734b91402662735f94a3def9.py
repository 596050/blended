#!/usr/bin/env python3
"""Build attributed Solarxy with telemetry disabled; test the real browser separately."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
def run(args,cwd=ROOT):
    print('+',' '.join(map(str,args)),flush=True)
    subprocess.run(args,cwd=cwd,check=True)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',default='./');p.add_argument('--commit',required=True)
    args=p.parse_args()
    if args.base!='./' and (not args.base.startswith('/') or not args.base.endswith('/') or '..' in args.base):p.error('Invalid base URL path')
    solar=ROOT/'.upstream/solarxy';web=solar/'web'
    lock=json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=solar,text=True).strip()
    if actual!=lock['solarxy']['commit']:raise RuntimeError('Solarxy source mismatch')
    changes=[]
    # Do not send this independent deployment's crash reports to the upstream
    # author's GlitchTip project. This modified source is included in the archive.
    (web/'.env.production').write_text('# Blended: external telemetry disabled.\nVITE_GLITCHTIP_DSN=\n')
    changes.append('web/.env.production')
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
    run(['npm','ci'],web);run(['npm','test'],web);run(['npm','run','build','--','--base',args.base],web)
    for asset in (web/'dist').rglob('*.js'):
        if 'app.glitchtip.com/25796' in asset.read_text():raise RuntimeError('Unexpected upstream telemetry DSN in browser bundle')
    destination=ROOT/'site/studio';shutil.copytree(web/'dist',destination)
    source_stage=ROOT/'build/solarxy-source';source_stage.mkdir(parents=True,exist_ok=False)
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=solar).decode().split('\0')
    for path in filter(None,tracked):
        src=solar/path
        if src.is_file() and not src.is_symlink():
            dest=source_stage/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    (source_stage/'BLENDED-PATCHES.json').write_text(json.dumps({'base':args.base,'changed_files':changes,'external_telemetry':False},indent=2))
    (ROOT/'site/source').mkdir(exist_ok=True)
    shutil.make_archive(str(ROOT/'site/source/solarxy-modified-source'),'gztar',root_dir=source_stage)
    shutil.copy2(solar/'LICENSE',destination/'LICENSE.txt');shutil.copy2(solar/'LICENSE',ROOT/'site/LICENSE.txt')
    shutil.copy2(solar/'THIRD-PARTY-NOTICES.md',destination/'THIRD-PARTY-NOTICES.md')
    blended_stage=ROOT/'build/blended-source';blended_stage.mkdir(parents=True,exist_ok=False)
    archive=ROOT/'build/blended-source.tar';run(['git','archive','--format=tar','--output',str(archive),'HEAD'])
    with tarfile.open(archive) as t:t.extractall(blended_stage,filter='data')
    shutil.copy2(solar/'LICENSE',blended_stage/'LICENSE')
    licences=blended_stage/'LICENSES';licences.mkdir(exist_ok=True)
    with urllib.request.urlopen('https://www.apache.org/licenses/LICENSE-2.0.txt',timeout=30) as r:apache=r.read()
    if b'Apache License' not in apache or b'Version 2.0' not in apache:raise RuntimeError('Unexpected Apache licence payload')
    (licences/'Apache-2.0.txt').write_bytes(apache)
    shutil.make_archive(str(ROOT/'site/source/blended-source'),'gztar',root_dir=blended_stage)
    (ROOT/'site/.nojekyll').touch();wasm=ROOT/'site/compat/blended_core.wasm'
    if not wasm.is_file():raise RuntimeError('Missing Blended compatibility WASM')
    manifest={'schema':1,'status':'built_not_deployment_verified','studio_built':True,'source_commit':args.commit,'built_utc':datetime.now(timezone.utc).isoformat(),'deployed_test_status':'see_ci','upstreams':lock,'wasm_sha256':hashlib.sha256(wasm.read_bytes()).hexdigest(),'blender_feature_parity':False,'external_telemetry':False}
    (ROOT/'site/build.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
