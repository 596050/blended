#!/usr/bin/env python3
"""Compare the actual checkpoint CI artifacts with their frozen references."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

root=Path(__file__).resolve().parent
repo=root.parents[2]
checkpoint='03913290e92a98cd9c45fdecf679072587c4dbe7'
base='9e75e19fbddf80ab68e60c4a7edefd8cd6e3c20c'
tree='a3fbe996e97c8e872ca4d94a1c0f7283e9cb86ad'


def ident(p):
 data=p.read_bytes();return {'path':str(p.relative_to(repo)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def canonical(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def exact_checkpoint_file(path):
 current=repo/path
 data=subprocess.check_output(['git','show',checkpoint+':'+path],cwd=repo)
 assert current.read_bytes()==data,path
 return current


def read(p):return json.loads(p.read_bytes())


assert subprocess.check_output(['git','rev-parse',checkpoint+'^{tree}'],cwd=repo,text=True).strip()==tree
assert subprocess.check_output(['git','show','-s','--format=%P',checkpoint],cwd=repo,text=True).strip()==base
jobs=read(root/'api/ledger-jobs-completed.json')['jobs']
by_id={job['id']:job for job in jobs}
comparisons=[]
for profile,reference,job_id,expected in [
 ('base','unittest-parity-ledger-5.2-2026-10-23',120603512685,(512,597)),
 ('essentials','unittest-parity-ledger-essentials-5.2-2026-10-23',120603512541,(516,601)),
]:
 actual_path=root/'ledger'/profile/'artifact/report.json'
 frozen_path=exact_checkpoint_file('compatibility/evidence/'+reference+'/report.json')
 actual,frozen=read(actual_path),read(frozen_path)
 differing=sorted(key for key in set(actual)|set(frozen) if actual.get(key)!=frozen.get(key))
 assert differing==['contract_sha256','inventory_sha256'],(profile,differing)
 assert actual['pairs']==frozen['pairs'] and actual['registrations']==frozen['registrations']
 assert len(actual['pairs'])==829 and len(actual['registrations'])==132
 assert (actual['successful_execution_pair_count'],actual['outcome_agreement_count'])==expected
 assert actual['gate']=='blocked' and not actual['all_upstream_test_parity'] and not actual['full_feature_parity']
 strict_path=root/'ledger'/profile/'artifact/strict-gate.json';strict=read(strict_path)
 shared=set(actual)&set(strict)
 assert all(actual[key]==strict[key] for key in shared)
 normalizer_only=sorted(set(actual)-set(strict))
 assert normalizer_only==['missing_browser_subtest_count','observation_count_limit','observation_totals','unexpected_browser_subtest_count']
 assert not set(strict)-set(actual)
 steps={step['name']:step for step in by_id[job_id]['steps']}
 assert steps['Reconcile immutable original attempts and explicit resource retries']['conclusion']=='success'
 assert steps['Enforce the strict declared-scope gate']['conclusion']=='failure'
 log=root/'logs'/('ledger-'+profile+'-'+str(job_id)+'.log')
 assert 'Process completed with exit code 1.' in log.read_text()
 comparisons.append({'profile':profile,'job_id':job_id,'job_conclusion':by_id[job_id]['conclusion'],
                     'normalizer_exit_code':0,'normalizer_exit_basis':'Single final command completed successfully in the workflow step.',
                     'strict_gate_exit_code':1,'strict_gate_exit_basis':'Explicit completed-job log.',
                     'actual_report':ident(actual_path),'frozen_report':ident(frozen_path),'strict_report':ident(strict_path),
                     'all_case_pairs_equal':True,'pair_count':len(actual['pairs']),'pairs_canonical_sha256':canonical(actual['pairs']),
                     'all_registrations_equal':True,'registration_count':len(actual['registrations']),
                     'registrations_canonical_sha256':canonical(actual['registrations']),
                     'only_differing_top_level_fields':differing,
                     'difference_scope':'Normalizer provenance changes the contract and inventory identities; every case pair, registration and other field is identical.',
                     'strict_shared_fields_equal':True,'normalizer_only_fields':normalizer_only,
                     'successful_execution_pairs':expected[0],'outcome_agreements':expected[1],
                     'gate':'blocked','new_blender_test_credit':0})

source_artifact=root/'ledger/source-build-codecs-sqlite/artifact'
source_files=[p for p in source_artifact.rglob('*') if p.is_file()]
assert len(source_files)==1
path_map=exact_checkpoint_file('compatibility/evidence/source-rebuild-unittest-39986612484/path-map.json')
assert source_files[0].read_bytes()==path_map.read_bytes()
source_log=root/'logs/ledger-source-build-120603512234.log'
source_text=source_log.read_text()
assert 'exact evidence map cannot shadow a current repository path' in source_text
assert 'Process completed with exit code 2.' in source_text
source_steps={x['name']:x for x in by_id[120603512234]['steps']}
assert source_steps['Reconcile immutable original attempts and explicit resource retries']['conclusion']=='failure'
assert source_steps['Enforce the strict declared-scope gate']['conclusion']=='skipped'
frozen_source=exact_checkpoint_file('compatibility/evidence/unittest-parity-ledger-source-build-39986612484/report.json')
source_ref=read(frozen_source)
assert source_ref['successful_execution_pair_count']==528 and source_ref['outcome_agreement_count']==536
source_comparison={'profile':'source-build-codecs-sqlite','job_id':120603512234,'job_conclusion':'failure',
                   'normalizer_exit_code':2,'strict_gate_exit_code':None,'strict_gate_step':'skipped',
                   'error':'exact evidence map cannot shadow a current repository path',
                   'artifact_file_count':1,'only_artifact_file':ident(source_files[0]),'path_map_exactly_matches_frozen':True,
                   'ci_report_present':False,'ci_case_pair_comparison_possible':False,
                   'frozen_reference':ident(frozen_source),'frozen_successful_execution_pairs':528,'frozen_outcome_agreements':536,
                   'frozen_reference_scope':'Prior original observations only; absent CI output is not filled from this reference.',
                   'source_derived_cause':'The current GitHub checkout root /home/runner/work/blended/blended contains the original absolute map paths. The unchanged guard rejects these as potential current-repository path shadowing.',
                   'new_blender_test_credit':0}

local_path=exact_checkpoint_file('compatibility/evidence/infrastructure-tests-dpx-recovery-2026-10-23/execution.json')
local=read(local_path)
assert local['unittest_summary']=={'tests':383,'seconds':155.557,'result':'OK'} and local['returncode']==0
infra_log=root/'logs/infrastructure-120603512741.log';infra_text=infra_log.read_text()
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s',infra_text)
assert match and int(match[1])==383 and float(match[2])==162.436
assert re.search(r'^\S+ OK\s*$',infra_text,re.M)
assert 'python3 -m unittest discover -s tests -q' in infra_text
assert by_id[120603512741]['conclusion']=='success'
infrastructure={'job_id':120603512741,'job_conclusion':'success','log':ident(infra_log),
                'command':['python3','-m','unittest','discover','-s','tests','-q'],
                'observed_tests':383,'observed_seconds':162.436,'observed_summary':'OK',
                'exit_code':0,'exit_basis':'The single-command infrastructure step completed successfully.',
                'local_reference':ident(local_path),'same_test_count_and_success_as_local':True,
                'local_reference_seconds':155.557,'blender_test_credit':0}

attempts=[]
for number in [1,2]:
 artifact=root/'publication'/f'attempt-{number:02d}'/'artifact'
 receipt_path=artifact/'receipt.json';receipt=read(receipt_path)
 assert receipt['expected']['target_commit']==checkpoint and receipt['expected']['target_tree']==tree and receipt['expected']['base_commit']==base
 assert receipt['expected']['target_branch']=='checkpoint/verified-03913290e92a'
 assert receipt['entry_point_sha256']==hashlib.sha256((root/'publication/inputs/import_checkpoint.py').read_bytes()).hexdigest()
 assert receipt['manifest_sha256']==hashlib.sha256((root/'publication/inputs/manifest.json').read_bytes()).hexdigest()
 assert not receipt['all_upstream_test_parity'] and not receipt['full_feature_parity'] and receipt['blender_tests_executed']==0
 commands={command['name']:command for command in receipt['commands']}
 if number==1:
  assert receipt['status']=='failed' and not receipt['published']
  assert receipt['remote_before']==receipt['remote_after']==base
  assert commands['push']['returncode']==1 and commands['lfs-push']['returncode']==0
  assert all(row['returncode']==0 for name,row in commands.items() if name!='push')
  push_text=(artifact/'commands/17-push.stdout.log').read_text()
  assert 'without `workflows` permission' in push_text
  scope='All verification and LFS upload commands passed. GitHub refused the branch push for missing workflows permission. The remote branch remained at the base commit.'
 else:
  assert receipt['status']=='published' and receipt['published'] and receipt['publication_outcome']=='verified'
  assert receipt['remote_before']==receipt['remote_after']==checkpoint
  assert all(row['returncode']==0 for row in commands.values())
  assert 'push' not in commands and 'lfs-push' not in commands and receipt['lfs_upload_outcome']=='not_attempted'
  scope='Verified the exact existing target after authorized connected-account publication. No branch push or LFS upload was attempted in this rerun.'
 attempts.append({'attempt':number,'receipt':ident(receipt_path),'status':receipt['status'],
                  'remote_before':receipt['remote_before'],'remote_after':receipt['remote_after'],
                  'command_count':len(commands),'command_exit_codes':{name:row['returncode'] for name,row in commands.items()},
                  'scope':scope,'blender_tests_executed':0})
publication_observation=read(root/'publication/inputs/publication-observation.json')
assert publication_observation['target_commit']==checkpoint and publication_observation['target_tree']==tree
assert publication_observation['sole_parent']==base and publication_observation['published']
assert publication_observation['refs']['refs/heads/parity/upstream-browser-ports']==checkpoint
assert publication_observation['refs']['refs/heads/checkpoint/verified-03913290e92a']==checkpoint
summary={'schema':1,'kind':'completed-checkpoint-ci-and-publication-observation','analysis_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'checkpoint':{'commit':checkpoint,'tree':tree,'sole_parent':base},
         'ledger_run_id':40008805411,'ledger_run_conclusion':'failure',
         'ledger_profile_comparisons':comparisons,'source_profile_replay_failure':source_comparison,
         'infrastructure':infrastructure,'publication_run_id':40008313085,'publication_attempts':attempts,
         'connected_account_publication_observation':ident(root/'publication/inputs/publication-observation.json'),
         'scope':'Publication verification and infrastructure/evidence replay only. Full source-build monitoring belongs to a separate capture.',
         'new_blender_test_credit':0,'all_upstream_test_parity':False,'full_feature_parity':False}
output=root/'analysis.json';assert not output.exists();output.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({'analysis':ident(output),'base_pairs':512,'essentials_pairs':516,'source_ci_report_present':False,
                  'infrastructure_tests':383,'infrastructure_result':'OK','publication_attempt2':'verified-existing-target'},indent=2))
