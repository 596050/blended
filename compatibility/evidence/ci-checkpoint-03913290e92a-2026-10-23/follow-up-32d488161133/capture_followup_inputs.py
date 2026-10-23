#!/usr/bin/env python3
"""Capture completed run metadata and exact published workflow-relocation inputs."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

root=Path(__file__).resolve().parent
repo=root.parents[3]
commit='32d488161133c5721e8379531b18af65a86e6624'
parent='03913290e92a98cd9c45fdecf679072587c4dbe7'
assert subprocess.check_output(['git','show','-s','--format=%P',commit],cwd=repo,text=True).strip()==parent
assert subprocess.check_output(['git','rev-parse',commit+'^{tree}'],cwd=repo,text=True).strip()=='45c4e8b119149315215a48b7d39fdcd99e48ff34'
changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],cwd=repo,text=True).splitlines()
assert changed==['.github/workflows/test-parity-ledger.yml']
inputs=[]
for path in ['.github/workflows/test-parity-ledger.yml','tools/reconcile_unittest_matrix.py','tools/test_parity_ledger.py','compatibility/evidence/source-rebuild-unittest-39986612484/path-map.json']:
 data=subprocess.check_output(['git','show',commit+':'+path],cwd=repo)
 old=subprocess.check_output(['git','show',parent+':'+path],cwd=repo)
 if path!='.github/workflows/test-parity-ledger.yml':assert data==old
 target=root/'inputs'/path;target.parent.mkdir(exist_ok=True,parents=True);assert not target.exists();target.write_bytes(data)
 inputs.append({'commit':commit,'git_path':path,'preserved_path':str(target.relative_to(root)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'unchanged_from_parent':data==old})
p=repo.parent/'deliverables/workflow-checkout-relocation-039.json';data=p.read_bytes();target=root/'inputs/workflow-checkout-relocation-039.json';target.write_bytes(data)
inputs.append({'source':str(p),'preserved_path':str(target.relative_to(root)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
url='https://api.github.com/repos/596050/blended/actions/runs/40009788126'
req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'blended-ci-evidence-capture'})
started=dt.datetime.now(dt.timezone.utc).isoformat()
with urllib.request.urlopen(req,timeout=60) as response:data=response.read();status=response.status
obj=json.loads(data);assert obj['head_sha']==commit and obj['status']=='completed' and obj['conclusion']=='failure'
p=root/'api/run-completed.json';assert not p.exists();p.write_bytes(data)
receipt={'schema':1,'kind':'published-workflow-relocation-input-capture','commit':commit,'parent':parent,'changed_paths':changed,'inputs':inputs,
         'api':{'url':url,'observed_utc':started,'http_status':status,'path':str(p.relative_to(root)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}}
(root/'input-capture.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'run_id':obj['id'],'status':obj['status'],'conclusion':obj['conclusion'],'changed_paths':changed,'input_count':len(inputs)}))
