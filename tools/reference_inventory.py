#!/usr/bin/env python3
"""Reconcile actual native GoogleTest discovery with a scoped Rust test port.
A module-level list is not Blender's complete runtime universe.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

def parse_gtest_listing(text:str)->dict:
    cases=[];disabled=[];suite=None;registrations=[];counts=Counter()
    for line in text.splitlines():
        line=line.split('#',1)[0].rstrip()
        if not line:continue
        if not line.startswith(' ') and line.endswith('.'):
            suite=line[:-1]
            if not re.fullmatch(r'[\w/]+',suite):raise ValueError('Unexpected test-suite name: '+suite)
        elif line.startswith('  '):
            name=line.strip()
            if suite is None or not re.fullmatch(r'[\w/]+',name):raise ValueError('Malformed test listing')
            identity=suite+'.'+name
            cases.append(identity);counts[identity]+=1
            registrations.append({'id':identity,'occurrence':counts[identity]})
            if any(p.startswith('DISABLED_') for p in (suite+'/'+name).split('/')):disabled.append(identity)
        elif cases or suite:raise ValueError('Unexpected text inside test listing: '+line)
        elif not (line.startswith('Running main()') or line.startswith('Note:')):raise ValueError('Unrecognised listing preamble: '+line)
    if not cases:raise ValueError('Empty runtime test universe')
    return {'case_ids':cases,'disabled':disabled,'registrations':registrations,'ambiguous_identities':{k:v for k,v in counts.items() if v>1}}

def parse_results(text:str)->dict[str,str]:
    root=ET.fromstring(text);result={}
    for c in root.iter('testcase'):
        identity=c.get('classname','')+'.'+c.get('name','')
        if identity.startswith('.') or identity.endswith('.') or identity in result:raise ValueError('Invalid or duplicate XML identity')
        if c.find('failure') is not None or c.find('error') is not None:state='failed'
        elif c.find('skipped') is not None or c.get('result')=='skipped':state='skipped'
        elif c.get('status')=='run' and c.get('result')=='completed':state='passed'
        else:state='not_run'
        result[identity]=state
    if not result or len(result)!=int(root.get('tests','-1')):raise ValueError('XML result count differs from executed case records')
    return result

def reconcile(discovered:list[str],mapped:list[str],results:dict[str,str],prefixes:list[str])->dict:
    if not discovered or not mapped or len(set(mapped))!=len(mapped):raise ValueError('Invalid runtime/mapped case universe')
    selected={c for c in discovered if any(c.startswith(p) for p in prefixes)}
    ambiguous={k:v for k,v in Counter(discovered).items() if v>1}
    selected_ambiguities={k:v for k,v in ambiguous.items() if k in selected}
    missing=selected-set(mapped);unknown=set(mapped)-selected
    unexpected=set(results)-selected;unexecuted=selected-set(results)
    return {
        'discovered_module_registrations':len(discovered),'distinct_module_labels':len(set(discovered)),
        'ambiguous_module_identities':ambiguous,'ambiguous_selected_identities':selected_ambiguities,
        'module_identity_reconciliation_complete':not ambiguous,'selected_case_count':len(selected),
        'mapped_selected_cases':len(selected & set(mapped)),
        'selected_families_complete':not missing and not unknown and not selected_ambiguities and bool(selected),
        'selected_reference_tests_passed':bool(selected) and not selected_ambiguities and not unexpected and not unexecuted and all(results[c]=='passed' for c in selected),
        'unmapped_selected_cases':sorted(missing),'mapped_not_discovered':sorted(unknown),
        'unexpected_execution_cases':sorted(unexpected),'unexecuted_selected_cases':sorted(unexecuted),
        'selected_cases':[{'id':c,'reference_execution':results.get(c,'not_run'),'rust_port_mapped':c in mapped} for c in sorted(selected)],
        'complete_blender_runtime_enumeration':False,'full_blender_test_port':False,
        'scope':'One configured BLI executable; selected range, binary-search and bounds families. Other modules, configurations, Python, rendering and UI are not covered.'}

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def build_report(evidence:Path,manifest:Path,root:Path)->dict:
    data=json.loads(manifest.read_text());commit=(evidence/'blender-commit.txt').read_text().strip()
    if data['upstream_commit']!=commit:raise ValueError('Reference commit mismatch')
    for case in data['cases']:
        snapshot=root/'tests/upstream/blender'/Path(case['path']).name
        if sha(snapshot)!=case['source_sha256']:raise ValueError('Port source snapshot differs from pinned manifest')
    discovery=parse_gtest_listing((evidence/'gtest-list.txt').read_text())
    results=parse_results((evidence/'reference-results.xml').read_text())
    report=reconcile(discovery['case_ids'],[c['id'] for c in data['cases']],results,['index_range.','binary_search.','bounds.'])
    ctest=json.loads((evidence/'ctest.json').read_text())
    report.update(reference_commit=commit,library_commit=(evidence/'libraries-commit.txt').read_text().strip(),compiler=(evidence/'compiler.txt').read_text().strip(),disabled_module_cases=discovery['disabled'],ctest_registrations=len(ctest.get('tests',[])),ctest_registration_is_not_full_execution=True,raw_evidence_sha256={p.name:sha(p) for p in sorted(evidence.iterdir()) if p.is_file() and p.name!='runtime-reconciliation.json'},discovered_case_ids=discovery['case_ids'],runtime_registrations=discovery['registrations'])
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=Path('compatibility/structure-ports.json'))
    args=parser.parse_args();report=build_report(args.evidence,args.manifest,Path(__file__).resolve().parents[1])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('discovered_case_ids','selected_cases','runtime_registrations')},indent=2))
    raise SystemExit(0 if report['selected_families_complete'] and report['selected_reference_tests_passed'] else 1)
