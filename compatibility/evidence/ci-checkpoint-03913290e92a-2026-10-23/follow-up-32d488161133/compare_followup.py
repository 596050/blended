#!/usr/bin/env python3
"""Verify actual relocated-checkout CI outputs without adding Blender test credit."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parent
repo=root.parents[3]
initial=root.parent
jobs=json.loads((root/'api/jobs-completed.json').read_text())['jobs']
job_by_id={j['id']:j for j in jobs}

def identity(p):
 data=p.read_bytes();return {'path':str(p.relative_to(repo)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def load(p):return json.loads(p.read_bytes())

def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def files(p):return {q.relative_to(p).as_posix():q for q in p.rglob('*') if q.is_file()}

rows=[]
for profile,job_id,expected,reference in [
 ('base',120606900247,(512,597),'unittest-parity-ledger-5.2-2026-10-23'),
 ('essentials',120606900127,(516,601),'unittest-parity-ledger-essentials-5.2-2026-10-23'),
 ('source-build-codecs-sqlite',120606900207,(528,536),'unittest-parity-ledger-source-build-39986612484'),
]:
 artifact=root/'ledger'/profile/'artifact';actual=load(artifact/'report.json');strict=load(artifact/'strict-gate.json')
 frozen=repo/'compatibility/evidence'/reference;frozen_report=load(frozen/'report.json')
 assert actual['pairs']==frozen_report['pairs'] and actual['registrations']==frozen_report['registrations']
 assert len(actual['pairs'])==829 and len(actual['registrations'])==132
 differences=sorted(k for k in set(actual)|set(frozen_report) if actual.get(k)!=frozen_report.get(k))
 assert differences==([] if profile=='source-build-codecs-sqlite' else ['contract_sha256','inventory_sha256'])
 assert (actual['successful_execution_pair_count'],actual['outcome_agreement_count'])==expected
 assert actual['gate']=='blocked' and not actual['all_upstream_test_parity'] and not actual['full_feature_parity']
 assert all(actual[k]==strict[k] for k in set(actual)&set(strict))
 assert sorted(set(actual)-set(strict))==['missing_browser_subtest_count','observation_count_limit','observation_totals','unexpected_browser_subtest_count']
 assert not set(strict)-set(actual)
 steps={s['name']:s for s in job_by_id[job_id]['steps']}
 assert steps['Reconcile immutable original attempts and explicit resource retries']['conclusion']=='success'
 assert steps['Enforce the strict declared-scope gate']['conclusion']=='failure'
 log=root/'logs'/(profile+'.log');text=log.read_text()
 assert 'Process completed with exit code 1.' in text
 assert 'exact evidence map cannot shadow a current repository path' not in text
 if profile=='source-build-codecs-sqlite':
  a=files(artifact);b=files(frozen)
  assert len(b)==858 and set(a)-set(b)=={'strict-gate.json'} and not set(b)-set(a)
  comparison_basis='All 858 frozen source-profile files, plus a separate new CI strict-gate report.'
  compared_count=858
 else:
  a=files(artifact);b=files(initial/'ledger'/profile/'artifact')
  assert set(a)==set(b)
  comparison_basis='Every artifact member from the initial checkpoint CI profile, including strict-gate.json.'
  compared_count=len(b)
 for name in b:assert a[name].read_bytes()==b[name].read_bytes(),(profile,name)
 rows.append({'profile':profile,'job_id':job_id,'normalizer_exit_code':0,
              'normalizer_exit_basis':'The step containing the final normalizer command completed successfully.',
              'strict_gate_exit_code':1,'strict_gate_exit_basis':'Explicit completed-job log.',
              'successful_execution_pairs':expected[0],'outcome_agreements':expected[1],'gate':'blocked',
              'report':identity(artifact/'report.json'),'strict_report':identity(artifact/'strict-gate.json'),
              'frozen_report':identity(frozen/'report.json'),'frozen_report_differing_fields':differences,
              'all_case_pairs_equal':True,'case_pair_count':829,'pairs_canonical_sha256':canonical(actual['pairs']),
              'all_registrations_equal':True,'registration_count':132,
              'whole_file_comparison_basis':comparison_basis,'compared_file_count':compared_count,'all_compared_files_byte_identical':True,
              'source_profile_missing_outcomes':actual['observation_totals']['browser']['missing_outcomes'],
              'missing_browser_subtests':actual['missing_browser_subtest_count'],'new_blender_test_credit':0})

source=next(x for x in rows if x['profile']=='source-build-codecs-sqlite')
assert source['report']['sha256']=='913a5f430f2ea9df35ec2878240a3c3b3b6783062c733a2e9a6f58d3b6c21b0b'
assert source['source_profile_missing_outcomes']==80 and source['missing_browser_subtests']==57
infra=root/'logs/infrastructure.log';text=infra.read_text()
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s',text)
assert match and int(match[1])==383 and float(match[2])==93.848
assert re.search(r'^\S+ OK\s*$',text,re.M)
assert job_by_id[120606899733]['conclusion']=='success'
workflow=root/'inputs/.github/workflows/test-parity-ledger.yml'
assert hashlib.sha256(workflow.read_bytes()).hexdigest()=='d36eaac18eddce8746572ad03d74b1c2ffb6c443c0291eee49fd5dbc37891ea1'
path_map=root/'inputs/compatibility/evidence/source-rebuild-unittest-39986612484/path-map.json'
entries=load(path_map)['entries'];assert len(entries)==730
new_checkout=Path('/home/runner/work/blended/blended/parity-evidence-checkout')
assert all(not Path(x['original_path']).is_relative_to(new_checkout) for x in entries)
source_inputs=load(root/'input-capture.json')
assert source_inputs['changed_paths']==['.github/workflows/test-parity-ledger.yml']
assert all(x.get('unchanged_from_parent') is True for x in source_inputs['inputs'] if x.get('git_path') not in (None,'.github/workflows/test-parity-ledger.yml'))
summary={'schema':1,'kind':'completed-workflow-relocation-ci-comparison','analyzed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'commit':'32d488161133c5721e8379531b18af65a86e6624','sole_parent':'03913290e92a98cd9c45fdecf679072587c4dbe7',
         'tree':'45c4e8b119149315215a48b7d39fdcd99e48ff34','run_id':40009788126,'run_conclusion':'failure',
         'workflow_only_change':True,'normalizer_and_historical_map_unchanged':True,
         'historical_map_entries':730,'historical_entries_inside_new_checkout':0,
         'profile_comparisons':rows,
         'infrastructure':{'job_id':120606899733,'job_conclusion':'success','log':identity(infra),
                           'observed_tests':383,'observed_seconds':93.848,'observed_result':'OK',
                           'exit_code':0,'exit_basis':'Single-command infrastructure step completed successfully.',
                           'same_test_count_and_success_as_initial_ci_and_local_capture':True},
         'claim_limit':'All normalizers now complete. All strict parity gates remain blocked. These jobs replay prior evidence and add no new Blender test observations.',
         'new_blender_test_credit':0,'all_upstream_test_parity':False,'full_feature_parity':False}
p=root/'analysis.json';assert not p.exists();p.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({'analysis':identity(p),'profiles':[{'profile':x['profile'],'normalizer_exit':0,'strict_exit':1,'successful_pairs':x['successful_execution_pairs'],'agreements':x['outcome_agreements'],'identical_files':x['compared_file_count']} for x in rows],'infrastructure_tests':383,'infrastructure_seconds':93.848},indent=2))
