#!/usr/bin/env python3
"""Observe a fresh normalizer and strict-ledger run after exact byte recovery."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root=Path('/workspace/scratch/d63596d831b2/blended')
work=Path('/tmp/blended-parity-recovery')
out=work/'fresh-source-normalization'
assert not out.exists(),out
logs=work/'fresh-source-normalization-capture'
logs.mkdir(exist_ok=False)
relative=['tools/reconcile_unittest_matrix.py','tools/test_parity_ledger.py','tools/unittest_cohort.py',
          'tools/upstream_resources.py','tools/probe_blender_fixtures.py','tools/upstream_invocations.py',
          'tools/upstream_invocations_5_2.json','tools/browser_package_overlay.py',
          'compatibility/package-overlays/essentials-brushes-5.2.json']

def ident(p):
    data=p.read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def snapshot():return {p:ident(root/p) for p in relative}

def execute(label,command,expected):
    started=dt.datetime.now(dt.timezone.utc).isoformat();start=time.monotonic()
    result=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=False)
    (logs/(label+'.stdout.log')).write_bytes(result.stdout)
    (logs/(label+'.stderr.log')).write_bytes(result.stderr)
    row={'command':command,'cwd':str(root),'started_utc':started,
         'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'duration_seconds':time.monotonic()-start,'returncode':result.returncode,
         'expected_returncode':expected,'stdout':ident(logs/(label+'.stdout.log')),
         'stderr':ident(logs/(label+'.stderr.log'))}
    if result.returncode!=expected:
        (logs/(label+'-failure.json')).write_text(json.dumps(row,indent=2)+'\n')
        raise RuntimeError(row)
    return row

before=snapshot()
normalizer_command=[sys.executable,'tools/reconcile_unittest_matrix.py','--repo-root','.',
    '--source-plan','compatibility/evidence/unittest-native-5.2-2026-10-23/discovery-inventory.json',
    '--native-retry-plan','compatibility/evidence/unittest-native-resources-5.2-2026-10-23/resource-retry-inventory.json',
    '--browser-matrix','compatibility/evidence/source-rebuild-unittest-39986612484/main/matrix.json',
    '--browser-matrix','compatibility/evidence/source-rebuild-unittest-39986612484/resources/matrix.json',
    '--native-context','compatibility/evidence/runtime-context-2026-10-23/native-context.json',
    '--browser-context','compatibility/evidence/runtime-context-source-build-39986612484/browser-context.json',
    '--path-map','compatibility/evidence/source-rebuild-unittest-39986612484/path-map.json',
    '--output',str(out),'--report-only']
normalizer=execute('normalizer',normalizer_command,0)
strict_command=[sys.executable,'tools/test_parity_ledger.py','--contract',str(out/'contract.json'),
    '--inventory',str(out/'inventory.json'),'--executions',str(out/'executions.json'),
    '--evidence-root',str(out),'--output',str(logs/'strict-gate.json')]
strict=execute('strict-gate',strict_command,1)
after=snapshot()
assert before==after
frozen=root/'compatibility/evidence/unittest-parity-ledger-source-build-39986612484'
files={p.relative_to(out).as_posix():p for p in out.rglob('*') if p.is_file()}
frozenfiles={p.relative_to(frozen).as_posix():p for p in frozen.rglob('*') if p.is_file()}
assert len(files)==858 and set(files)==set(frozenfiles),(len(files),len(frozenfiles))
comparisons=[{'path':rel,**ident(p),'byte_equal':p.read_bytes()==frozenfiles[rel].read_bytes()} for rel,p in sorted(files.items())]
assert all(v['byte_equal'] for v in comparisons)
report=json.loads((out/'report.json').read_bytes())
strictreport=json.loads((logs/'strict-gate.json').read_bytes())
shared=set(report)&set(strictreport)
assert all(report[k]==strictreport[k] for k in shared)
assert report['successful_execution_pair_count']==528 and report['outcome_agreement_count']==536
assert report['gate']=='blocked' and not report['all_upstream_test_parity'] and not report['full_feature_parity']
receipt={'schema':1,'kind':'post-recovery-normalizer-and-ledger-execution',
         'scope':'New execution of the infrastructure normalizer over exact recovered original observations. No new Blender execution.',
         'normalizer':normalizer,'strict_gate':strict,'implementation_before':before,'implementation_after':after,
         'implementation_unchanged':True,'normalizer_output_file_count':len(files),
         'normalizer_output_files_identical_to_retained_profile':True,'file_comparisons':comparisons,
         'normalizer_report':ident(out/'report.json'),'strict_report':ident(logs/'strict-gate.json'),
         'normalizer_only_fields':sorted(set(report)-set(strictreport)),
         'strict_only_fields':sorted(set(strictreport)-set(report)),
         'all_shared_report_fields_equal':True,
         'strict_successful_pairs':528,'outcome_agreements':536,
         'missing_browser_outcomes':report['observation_totals']['browser']['missing_outcomes'],
         'missing_browser_subtests':report['missing_browser_subtest_count'],
         'all_upstream_test_parity':False,'full_feature_parity':False,
         'python':{'executable':sys.executable,'version':sys.version,'binary':ident(Path(sys.executable).resolve())},
         'blender_test_update_key_present': 'BLENDER_TEST_UPDATE' in os.environ}
receipt_path=work/'fresh-source-normalization-execution.json'
receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('file_comparisons','implementation_before','implementation_after','normalizer','strict_gate')},indent=2))
print(json.dumps({'receipt':str(receipt_path),**ident(receipt_path)}))
