"""Explicit compile-time manifests, distinct from the executable runtime cases."""
from pathlib import Path
import json
STATIC_MANIFESTS=('compile-time-ports.json','span-static-ports.json')
def load_static_cases(root:Path):
    reference=json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']
    cases=[];seen=set()
    for name in STATIC_MANIFESTS:
        data=json.loads((root/'compatibility'/name).read_text())
        if data.get('upstream_commit')!=reference or not data.get('cases'):
            raise ValueError('Missing or stale required static manifest: '+name)
        for case in data['cases']:
            key=(case['path'],case['id'],case['line'])
            if key in seen or case.get('kind')!='static_assert' or case.get('runtime_assertions')!=0:
                raise ValueError('Invalid or duplicate compile-time mapping: '+str(key))
            seen.add(key);cases.append(case)
    return cases
