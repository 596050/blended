#!/usr/bin/env python3
"""Complete retained CI closure from re-downloaded, hash-verified artifact members."""
import datetime as dt
import hashlib
import json
from pathlib import Path

root=Path('/workspace/scratch/d63596d831b2/blended')
archive_root=Path('/tmp/blended-ci-artifact-recovery-39986612484')
map_path=root/'compatibility/evidence/source-rebuild-unittest-39986612484/path-map.json'
raw=map_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='49f721772bf1022dea2b74c083e0f2406f4e099220c1b285af929a9ddeff125e'
m=json.loads(raw)
assert len(m['entries'])==730
prefix='compatibility/evidence/source-rebuild-unittest-39986612484/'
receipt={'schema':1,'kind':'exact-ci-artifact-file-recovery','started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'source_run_id':39986612484,'entries':[]}
for item in m['entries']:
    assert item['path'].startswith(prefix)
    suffix=item['path'][len(prefix):]
    assert suffix.split('/')[0] in ('main','resources') and '..' not in Path(suffix).parts
    src=archive_root/suffix
    assert src.is_file() and not src.is_symlink(),src
    data=src.read_bytes()
    assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],src
    dst=root/item['path']
    if dst.exists():
        assert dst.is_file() and not dst.is_symlink() and dst.read_bytes()==data,dst
        action='verified-existing-identical'
    else:
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
        assert dst.read_bytes()==data
        action='restored-from-exact-artifact-member'
    receipt['entries'].append({**item,'source':str(src),'action':action})
from collections import Counter
receipt['action_counts']=dict(Counter(x['action'] for x in receipt['entries']))
assert receipt['action_counts']=={'verified-existing-identical':678,'restored-from-exact-artifact-member':52}
receipt['completed_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
out=Path('/tmp/blended-parity-recovery/ci-artifact-file-recovery.json')
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'actions':receipt['action_counts'],'receipt_bytes':out.stat().st_size,'receipt_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2))
