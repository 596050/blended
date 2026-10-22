#!/usr/bin/env python3
"""Build the bounded Three.js + Rust modeller, not a full Blender clone."""
import argparse,json,shutil,subprocess,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(args,cwd=ROOT):subprocess.run(args,cwd=cwd,check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args()
 actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if actual!=a.commit:raise RuntimeError('Source commit mismatch')
 run(['cargo','test','--locked','--workspace','--all-targets'])
 run(['node','--test','modeller/model.test.mjs'])
 run(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'])
 run(['python3','tools/prepare_site.py'])
 out=ROOT/'build/modeller';out.parent.mkdir(exist_ok=True)
 shutil.copytree(ROOT/'modeller',out)
 (out/'compat').mkdir();shutil.copy2(ROOT/'target/wasm32-unknown-unknown/release/blended_core.wasm',out/'compat/blended_core.wasm');shutil.copy2(ROOT/'site/compat/ports.json',out/'compat/ports.json')
 deps=ROOT/'build/three';deps.mkdir()
 packed=json.loads(subprocess.check_output(['npm','pack','three@0.180.0','--ignore-scripts','--json'],cwd=deps,text=True))[0]
 archive=deps/packed['filename']
 with tarfile.open(archive) as t:t.extractall(deps,filter='data')
 package=deps/'package';info=json.loads((package/'package.json').read_text())
 if info['name']!='three' or info['version']!='0.180.0':raise RuntimeError('Dependency pin mismatch')
 vendor=out/'vendor';vendor.mkdir();shutil.copytree(package/'build',vendor/'build');shutil.copytree(package/'examples/jsm',vendor/'examples/jsm');shutil.copy2(package/'LICENSE',vendor/'LICENSE')
 (out/'source').mkdir();shutil.copy2(archive,out/'source'/archive.name)
 source=ROOT/'build/modeller-source';source.mkdir()
 temporary=ROOT/'build/modeller-source.tar';run(['git','archive','--format=tar','--output',str(temporary),'HEAD'])
 with tarfile.open(temporary) as t:t.extractall(source,filter='data')
 licences={
 'LICENSE.txt':'https://raw.githubusercontent.com/marko-koljancic/solarxy/9aa3b49191f0904478fd3a19dc7a4c1fbbfb6e36/LICENSE',
 'APACHE-2.0.txt':'https://www.apache.org/licenses/LICENSE-2.0.txt'}
 for name,url in licences.items():
  with urllib.request.urlopen(url,timeout=30) as r:data=r.read()
  if b'License' not in data and b'LICENSE' not in data:raise RuntimeError('Unexpected licence response')
  (out/name).write_bytes(data);(source/name).write_bytes(data)
 shutil.make_archive(str(out/'source/blended-source'),'gztar',root_dir=source)
 (out/'build.json').write_text(json.dumps({'source_commit':a.commit,'stage':'limited-modeller-alpha','blender_parity':False,'render_backend':'Three.js 0.180.0 WebGL 2','geometry_backend':'Rust WASM box/plane, Three.js sphere and OBJ/STL parsing','upstream_ports':{'blender':17,'cycles_native_only':3},'acceptance_status':'see matching CI run','three_package_integrity':packed.get('integrity'),'limits':['No mesh edit or sculpt mode','No animation/rigging/simulation','No native .blend import','No Cycles parity','OBJ export does not include materials','20 MB import limit; bounded snapshot history']},indent=2)+'\n')
 (out/'.nojekyll').touch()
if __name__=='__main__':main()
