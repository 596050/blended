#!/usr/bin/env python3
"""Capture the completed runs and both publication attempts from GitHub's public API."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

root=Path(__file__).resolve().parent
base='https://api.github.com/repos/596050/blended/actions/runs/'
queries={
 'publication-attempt-01-jobs':base+'40008313085/attempts/1/jobs?per_page=100',
 'publication-attempt-02-jobs':base+'40008313085/attempts/2/jobs?per_page=100',
 'publication-run-completed':base+'40008313085',
 'ledger-run-completed':base+'40008805411',
}
rows=[]
for name,url in queries.items():
 p=root/'api'/(name+'.json');assert not p.exists(),p
 started=dt.datetime.now(dt.timezone.utc).isoformat()
 req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'blended-ci-evidence-capture'})
 with urllib.request.urlopen(req,timeout=60) as response:
  data=response.read();status=response.status
 obj=json.loads(data)
 p.write_bytes(data)
 row={'url':url,'path':str(p.relative_to(root)),'observed_utc':started,'http_status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 rows.append(row)
 print(json.dumps({'name':name,'http_status':status,'status':obj.get('status'),'conclusion':obj.get('conclusion'),'run_attempt':obj.get('run_attempt'),'jobs':[{'id':j['id'],'name':j['name'],'conclusion':j['conclusion']} for j in obj.get('jobs',[])]}),flush=True)
(root/'api-capture.json').write_text(json.dumps({'schema':1,'kind':'github-public-api-observations','observations':rows},indent=2,sort_keys=True)+'\n')
