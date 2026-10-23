#!/usr/bin/env python3
"""Restore exact recovered bytes into the published checkpoint."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

root=Path('/workspace/scratch/d63596d831b2/blended')
source=Path('/tmp/blended-parity-recovery/repo-fragments')
base='9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c'
actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert actual==base,actual
rows=subprocess.check_output(['git','ls-tree','-rz',base],cwd=root).split(b'\0')
tracked={}
for row in rows:
 if row:
  info,path=row.split(b'\t',1)
  mode,kind,digest=info.decode().split()
  tracked[path.decode()]={'mode':mode,'kind':kind,'git_sha1':digest}

def blob_sha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()

planned=[]
for p in sorted(source.rglob('*')):
 if not p.is_file():continue
 assert not p.is_symlink(),p
 rel=p.relative_to(source).as_posix();dest=root/rel;data=p.read_bytes()
 entry=tracked.get(rel)
 if entry:
  assert entry['kind']=='blob' and entry['mode'] in ('100644','100755'),entry
  if rel!='tools/reconcile_unittest_matrix.py':
   assert blob_sha(data)==entry['git_sha1'],rel
 if dest.exists():
  assert dest.is_file() and not dest.is_symlink(),dest
  old=dest.read_bytes()
  if old==data:
   action='verified-existing-published-bytes'
  else:
   assert rel=='tools/reconcile_unittest_matrix.py',rel
   assert entry is not None and blob_sha(old)==entry['git_sha1'],rel
   assert sha(data)=='6675c3f1604ef92f3aa139e0d0cc9a91f0a59487b46e0cb5f9685676cd5caa5c'
   action='restore-exact-newer-normalizer'
 else:
  assert entry is None,rel
  action='restore-new-evidence'
 planned.append((p,dest,rel,data,action,entry))
result={'schema':1,'kind':'exact-retained-byte-restoration','base_commit':base,
        'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'records':[]}
for p,dest,rel,data,action,entry in planned:
 if action!='verified-existing-published-bytes':
  dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_bytes(data)
 assert dest.read_bytes()==data,rel
 result['records'].append({'path':rel,'source':str(p),'action':action,'bytes':len(data),'sha256':sha(data),'published_entry':entry})
result['completed_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
from collections import Counter
result['action_counts']=dict(Counter(r['action'] for r in result['records']))
out=Path('/tmp/blended-parity-recovery/restoration.json')
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'actions':result['action_counts'],'receipt_bytes':out.stat().st_size,'receipt_sha256':sha(out.read_bytes())},indent=2))
