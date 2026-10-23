#!/usr/bin/env python3
"""Generate traceability metadata; never manufacture executed test results."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=(ROOT/'crates/blended-core/src/compat_cases.rs').read_text()
    names=re.findall(r'\("(math_vector\.[^"]+)",',source)
    if len(names)!=17 or len(set(names))!=17: raise RuntimeError('Unexpected compatibility registry')
    lock=json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']
    cases=[{'id':name,'rust_test':'upstream_math_vector::'+name.split('.',1)[1],'wasm_index':i,'port_status':'written','execution':'not_run'} for i,name in enumerate(names)]
    manifest={'schema':1,'upstream_repository':'blender/blender','upstream_commit':lock['blender']['commit'],'source_path':'source/blender/blenlib/tests/BLI_math_vector_test.cc','cases':cases,'full_feature_parity':False,'outstanding':['signed-zero hash static assertion','all remaining Blender subsystems','complete runtime enumeration'],'assertion_policy':'Original exact comparisons, four-ULP EXPECT_FLOAT_EQ and 1e-6 EXPECT_NEAR retained as applicable.'}
    for dest in ['compatibility/ports.json','site/compat/ports.json']:
        path=ROOT/dest; path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'site/build.json').write_text(json.dumps({'schema':1,'studio_built':False,'source_commit':None,'upstreams':lock,'blender_feature_parity':False},indent=2)+'\n')
if __name__=='__main__': main()
