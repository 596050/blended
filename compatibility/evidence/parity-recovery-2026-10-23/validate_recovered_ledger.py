#!/usr/bin/env python3
"""Re-evaluate retained ledger bytes without executing Blender."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

root=Path('/tmp/blended-parity-recovery')
out=root/'recovery-validation'
out.mkdir(exist_ok=True)
rows=[]
for profile in ('base','essentials','source-build-codecs-sqlite'):
    source=root/'retained-replay-profiles'/profile
    destination=out/profile
    destination.mkdir(exist_ok=True)
    command=[sys.executable,str(source/'normalizer/test_parity_ledger.py'),
             '--contract',str(source/'contract.json'),
             '--inventory',str(source/'inventory.json'),
             '--executions',str(source/'executions.json'),
             '--evidence-root',str(source),
             '--output',str(destination/'strict-gate.json')]
    started=dt.datetime.now(dt.timezone.utc).isoformat()
    start=time.monotonic()
    result=subprocess.run(command,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=False)
    (destination/'stdout.log').write_bytes(result.stdout)
    (destination/'stderr.log').write_bytes(result.stderr)
    data=(destination/'strict-gate.json').read_bytes()
    previous=(source/'strict-gate.json').read_bytes()
    obj=json.loads(data)
    normalizer=json.loads((source/'report.json').read_bytes())
    shared=sorted(set(normalizer)&set(obj))
    row={'profile':profile,'command':command,'cwd':str(out),
         'started_utc':started,'duration_seconds':time.monotonic()-start,'returncode':result.returncode,
         'output_bytes':len(data),'output_sha256':hashlib.sha256(data).hexdigest(),
         'byte_identical_to_retained_strict_report':data==previous,
         'normalizer_only_fields':sorted(set(normalizer)-set(obj)),
         'strict_only_fields':sorted(set(obj)-set(normalizer)),
         'shared_fields_equal':all(normalizer[k]==obj[k] for k in shared),
         'strict_successful_pairs':obj['successful_execution_pair_count'],
         'outcome_agreements':obj['outcome_agreement_count'],'gate':obj['gate'],
         'scope':'Post-recovery ledger verification only; no Blender test execution.'}
    assert row['returncode']==1 and row['gate']=='blocked',row
    assert row['byte_identical_to_retained_strict_report'] and row['shared_fields_equal'],row
    rows.append(row)
(root/'recovery-validation.json').write_text(json.dumps({'schema':1,'kind':'post-recovery-ledger-verification','results':rows},indent=2,sort_keys=True)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k not in ('command','cwd')} for row in rows],indent=2))
