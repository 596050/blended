#!/usr/bin/env python3
"""Fail-closed accounting. A source scanner and a green subset cannot prove completeness."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('ctest','gtest','python','render','ui','compile_time')
def key(c):return f"{c['path']}::{c.get('identity',c.get('id'))}::{c.get('line',1)}"
def evaluate(inventory,ports,runtime=None,execution=None):
    runtime=runtime or {};execution=execution or {};blockers=[]
    cases=inventory.get('cases',[]);keys={key(c) for c in cases}
    source_hashes={f['path']:f['sha256'] for f in inventory.get('files',[])}
    mapped={};seen=set()
    if not cases:blockers.append('empty_source_universe')
    if len(keys)!=len(cases):blockers.append('ambiguous_source_identities')
    for p in ports:
        k=key(p)
        if k in seen:blockers.append('duplicate_port:'+k);continue
        seen.add(k)
        if k not in keys:blockers.append('unknown_port:'+k);continue
        if p.get('source_sha256')!=source_hashes.get(p['path']):blockers.append('source_hash_mismatch:'+k);continue
        if not p.get('semantics_reviewed') or not p.get('target_test') or not re.fullmatch('[0-9a-f]{64}',p.get('target_sha256','')):
            blockers.append('port_not_reviewed:'+k);continue
        if not isinstance(p.get('assertion_count'),int) or p['assertion_count']<0:
            blockers.append('missing_assertion_contract:'+k);continue
        mapped[k]=p
    missing=keys-set(mapped)
    if missing:blockers.append('unported_source_cases')
    if inventory.get('unreadable_files'):blockers.append('unreadable_source_files')
    if runtime.get('commit')!=inventory.get('commit'):blockers.append('runtime_reference_missing_or_stale')
    if runtime.get('complete') is not True or runtime.get('unresolved'):blockers.append('runtime_enumeration_incomplete')
    for name in FAMILIES:
        f=runtime.get('families',{}).get(name,{})
        if f.get('complete') is not True or not re.fullmatch('[0-9a-f]{64}',f.get('raw_evidence_sha256','')):blockers.append('unreconciled_runtime_family:'+name)
    runtime_keys=runtime.get('case_keys',[])
    if not runtime_keys:blockers.append('empty_runtime_universe')
    if len(set(runtime_keys))!=len(runtime_keys):blockers.append('duplicate_runtime_case')
    runtime_missing=set(runtime_keys)-set(mapped)
    if runtime_missing:blockers.append('unported_runtime_cases')
    fixtures=inventory.get('fixtures',[])
    unavailable=[f for f in fixtures if f.get('status')!='verified']
    if inventory.get('fixture_completeness')!='verified' or unavailable:blockers.append('fixture_completeness_not_verified')
    ledger=[dict(c,port_status='mapped_reviewed' if key(c) in mapped else 'not_ported',target_test=mapped.get(key(c),{}).get('target_test')) for c in cases]
    executed=execution.get('case_results',{}) if execution.get('source_commit')==inventory.get('commit') else {}
    conformance=not blockers and bool(mapped) and all(all(executed.get(k,{}).get(t)=='passed' for t in ('native','wasm','deployed')) for k in mapped)
    return dict(schema=2,reference_commit=inventory.get('commit'),complete_test_port=not blockers,test_conformance_complete=conformance,feature_parity=False,
                source_candidates=len(cases),mapped_source_candidates=len(mapped),unported_source_candidates=len(missing),
                unported_runtime_cases=len(runtime_missing),unavailable_fixture_count=len(unavailable),
                declaration_kinds=dict(Counter(c['kind'] for c in cases)),blockers=sorted(set(blockers)),cases=ledger,
                note='Counts are source candidates, including conditional and third-party declarations, NOT a full runtime denominator. Mapping and execution are separate. Assertion equivalence requires review; hashes detect subsequent drift. Test conformance does not establish whole-application feature parity.')

def load_ports(inventory):
    hashes={f['path']:f['sha256'] for f in inventory['files']};ports=[]
    for manifest,target_path,module in (
        ('additional-ports.json','crates/blended-core/src/additional_cases.rs','upstream_additional'),
        ('structure-ports.json','crates/blended-core/src/structure_cases.rs','upstream_structures'),
        ('numerics-text-ports.json','crates/blended-core/src/numerics_text_cases.rs','upstream_numerics_text'),
        ('collection-ports.json','crates/blended-core/src/collection_cases.rs','upstream_collections'),
        ('compile-time-ports.json','crates/blended-core/src/compile_time_cases.rs','compile_time_cases'),
    ):
        generated=ROOT/'compatibility'/manifest
        if not generated.exists():continue
        data=json.loads(generated.read_text())
        if data['upstream_commit']!=inventory['commit']:raise ValueError('Port reference commit mismatch')
        target_hash=hashlib.sha256((ROOT/target_path).read_bytes()).hexdigest()
        for p in data['cases']:
            ports.append(dict(p,semantics_reviewed=False,target_test=module+'::'+p['rust_function'],target_path=target_path,target_sha256=target_hash))
    original=ROOT/'crates/blended-core/src/compat_cases.rs'
    ids=set(re.findall(r'\("(math_vector\.[^"]+)"',original.read_text()))
    path='source/blender/blenlib/tests/BLI_math_vector_test.cc'
    source=ROOT/'.upstream/blender'/path;text=source.read_text() if source.exists() else ''
    for c in inventory['cases']:
        if c['path']==path and c['identity'] in ids:
            start=text.find('TEST(math_vector, '+c['identity'].split('.',1)[1]+')');end=text.find('\nTEST(',start+1)
            body=text[start:end if end>=0 else len(text)]
            ports.append(dict(path=path,id=c['identity'],line=c['line'],source_sha256=hashes[path],assertion_count=len(re.findall(r'\bEXPECT_[A-Z_]+\(',body)),semantics_reviewed=False,target_path='crates/blended-core/src/compat_cases.rs',target_test='upstream_math_vector::'+c['identity'].split('.',1)[1],target_sha256=hashlib.sha256(original.read_bytes()).hexdigest()))
    contract_file=ROOT/'compatibility/assertion-contracts.lock.json'
    contract=json.loads(contract_file.read_text()) if contract_file.exists() else {}
    for p in ports:
        p['semantics_reviewed']=contract.get('reference_commit')==inventory['commit'] and any(
            c.get('source_path')==p['path'] and c.get('source_sha256')==p['source_sha256']
            and c.get('target_path')==p['target_path'] and c.get('target_sha256')==p['target_sha256'] and p['id'] in c.get('case_ids',[])
            for c in contract.get('contracts',[]))
    return ports

def fixture_metadata(root):
    result=[]
    if not root.is_dir():return result
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.is_symlink():continue
        with p.open('rb') as f:head=f.read(256)
        if head.startswith(b'version https://git-lfs.github.com/spec/'):
            text=head.decode('ascii');oid=re.search(r'oid sha256:([0-9a-f]{64})',text);size=re.search(r'\nsize (\d+)',text)
            result.append({'path':p.relative_to(root).as_posix(),'status':'lfs_pointer','oid':oid[1] if oid else None,'expected_bytes':int(size[1]) if size else None})
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime',type=Path);parser.add_argument('--execution',type=Path);parser.add_argument('--require-complete',action='store_true')
    args=parser.parse_args();inv=json.loads(args.inventory.read_text())
    runtime=json.loads(args.runtime.read_text()) if args.runtime else {};execution=json.loads(args.execution.read_text()) if args.execution else {}
    for f in runtime.get('families',{}).values():
        raw=ROOT/f.get('raw_evidence_path','MISSING')
        if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest()!=f.get('raw_evidence_sha256'):f['complete']=False
    result=evaluate(inv,load_ports(inv),runtime,execution)
    assets=fixture_metadata(ROOT/'.upstream/blender/tests/files');result['test_asset_lfs_pointers']=assets
    result['test_asset_missing_bytes']=sum(a.get('expected_bytes') or 0 for a in assets)
    result['execution_scope']='This audit does not execute the candidate tests. Pointer status describes this checkout, not the separate fixture-download verification run.'
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','test_asset_lfs_pointers')},indent=2))
    return 1 if args.require_complete and not result['complete_test_port'] else 0
if __name__=='__main__':sys.exit(main())
