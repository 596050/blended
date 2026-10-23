#!/usr/bin/env python3
"""Conservative source-test discovery, NOT runtime enumeration or parity proof."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
STATUSES=('passed','failed','blocked','unsupported','not_run')
CPP_SUFFIXES={'.c','.cc','.cpp','.cxx','.h','.hh','.hpp'}
EXCLUDED={'.git','node_modules','target','dist','__pycache__','.venv'}
def summary(cases):
    counts=Counter(c['execution'] for c in cases)
    invalid=set(counts)-set(STATUSES)
    if invalid:raise ValueError(f'Unknown execution status: {sorted(invalid)}')
    return {s:counts[s] for s in STATUSES}
def _mask(text):
    pattern=r'R"([^ ()\\\t\r\n]{0,16})\([\s\S]*?\)\1"|//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern,lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),text)
def _case(path,line,identity,kind,expanded=False):
    return dict(path=path,line=line,identity=identity,kind=kind,requires_runtime_expansion=expanded,execution='not_run',port_status='not_ported')
def scan_cpp(text,path):
    clean=_mask(text);results=[]
    pattern=r'\b(TEST|TEST_F|TEST_P|TYPED_TEST|TYPED_TEST_P)\s*\(\s*([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*\)'
    for m in re.finditer(pattern,clean):
        results.append(_case(path,clean.count('\n',0,m.start())+1,f'{m[2]}.{m[3]}',m[1],m[1] in {'TEST_P','TYPED_TEST','TYPED_TEST_P'} or m[2].isupper()))
    for m in re.finditer(r'\bstatic_assert\s*\(',clean):
        line=clean.count('\n',0,m.start())+1
        results.append(_case(path,line,f'static_assert@{line}','static_assert'))
    return sorted(results,key=lambda c:c['line'])
def scan_python(text,path):
    tree=ast.parse(text,filename=path);found=[]
    def walk(node,scope):
        for child in ast.iter_child_nodes(node):
            if isinstance(child,ast.ClassDef):walk(child,scope+[child.name])
            elif isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                if child.name.startswith('test_'):found.append(_case(path,child.lineno,'.'.join(scope+[child.name]),'python_test',bool(child.decorator_list)))
            else:walk(child,scope)
    walk(tree,[]);return found

def scan_rust(text,path):
    # Do not treat Rust lifetimes ('a) as multi-line character literals.
    pattern=r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\\n])\''
    clean=re.sub(pattern,lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),text)
    tests=r'#\s*\[\s*(?:test|wasm_bindgen_test)\s*\](?:\s*#\[[^\]]*\])*\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)'
    return [_case(path,clean.count('\n',0,m.start())+1,m[1],'rust_test') for m in re.finditer(tests,clean)]
def _fixture_root_records(root, fixture_roots):
    records=[]
    for value in sorted(set(fixture_roots)):
        if not isinstance(value,str) or not value or '\\' in value:
            raise ValueError('Fixture roots must be canonical relative POSIX paths')
        rel=PurePosixPath(value)
        if rel.is_absolute() or '..' in rel.parts or value!=rel.as_posix():
            raise ValueError(f'Fixture root escapes or is not canonical: {value}')
        path=root.joinpath(*rel.parts)
        linked=any(root.joinpath(*rel.parts[:i]).is_symlink() for i in range(1,len(rel.parts)+1))
        status='symlink_unverified' if linked else 'missing' if not path.exists() else 'present' if path.is_dir() else 'not_directory'
        records.append(dict(path=value,status=status,files_discovered=0))
    return records

def _fixture_file(file, path, declared):
    record=dict(path=path,declared_roots=declared,discovery_basis='declared_fixture_root' if declared else 'blend_extension')
    if file.is_symlink():
        return dict(record,status='symlink_unverified')
    with file.open('rb') as stream:
        prefix=stream.read(160);stream.seek(0)
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    pointer=prefix.startswith(b'version https://git-lfs.github.com/spec/')
    record.update(size=file.stat().st_size,sha256=digest,hash_scope='file_bytes',status='lfs_pointer' if pointer else 'present_unvalidated')
    if pointer:
        oid=re.search(rb'(?m)^oid sha256:([0-9a-f]{64})$',prefix)
        size=re.search(rb'(?m)^size ([0-9]+)$',prefix)
        record.update(lfs_oid_sha256=oid[1].decode() if oid else None,lfs_declared_size=int(size[1]) if size else None,lfs_pointer_valid=bool(oid and size))
    return record

def inventory(root:Path,name:str,commit:str,*,fixture_roots=()):
    if not root.is_dir():raise ValueError(f'Missing source checkout: {root}')
    cases,files,fixtures,errors=[],[],[],[]
    root_records=_fixture_root_records(root,fixture_roots)
    for file in sorted(root.rglob('*')):
        rel=file.relative_to(root)
        if any(p in EXCLUDED for p in rel.parts):continue
        path=rel.as_posix();suffix=file.suffix.lower()
        declared=[r['path'] for r in root_records if r['path']=='.' or path==r['path'] or path.startswith(r['path']+'/')]
        fixture=suffix=='.blend' or bool(declared)
        if fixture and (file.is_file() or file.is_symlink()):
            try:fixtures.append(_fixture_file(file,path,declared))
            except OSError as exc:
                fixtures.append(dict(path=path,declared_roots=declared,status='unreadable',error=str(exc)))
                errors.append(dict(path=path,phase='fixture_presence',error=str(exc)))
        if file.is_symlink() or not file.is_file():continue
        if suffix not in CPP_SUFFIXES|{'.py','.rs'}:continue
        file_record=dict(path=path,discovered=0,discovery_status='unresolved')
        files.append(file_record)
        try:
            raw=file.read_bytes();file_record['sha256']=hashlib.sha256(raw).hexdigest();text=raw.decode('utf-8')
            scanner=scan_cpp if suffix in CPP_SUFFIXES else scan_python if suffix=='.py' else scan_rust
            discovered=scanner(text,path)
            file_record.update(discovered=len(discovered),discovery_status='scanned_heuristically')
            for case in discovered:case.update(upstream=name,upstream_commit=commit,id=f'{name}:{commit}:{path}:{case["identity"]}:{case["line"]}')
            cases.extend(discovered)
        except (UnicodeError,SyntaxError,OSError) as exc:
            file_record['discovery_error']=str(exc)
            errors.append(dict(path=path,phase='source_discovery',error=str(exc)))
    for record in root_records:
        record['files_discovered']=sum(record['path'] in f.get('declared_roots',[]) for f in fixtures)
    return dict(schema=1,upstream=name,commit=commit,discovery='heuristic_source_scan',runtime_enumeration_complete=False,fixture_completeness='unknown',fixture_roots=root_records,fixtures_available=any(f['status']=='present_unvalidated' for f in fixtures),fixtures_available_means='At least one regular fixture file has bytes; validity and dependency closure are unverified.',files=files,cases=cases,fixtures=fixtures,unreadable_files=errors,counts=summary(cases),limitations=['Does not expand C/C++ macros or conditional build configuration.','Does not enumerate parameter values, generated tests or factories.','Does not discover every UI, render-driver, JS/TS, CMake or external test.','Rust raw strings and nested comments need more complete lexical handling.','Fixture presence covers declared roots and .blend files, not runtime dependency closure.','LFS pointer hashes describe pointer text; the LFS oid separately identifies the absent payload.','Does not execute tests or validate fixture coverage.','A complete denominator requires upstream runtime discovery.'])
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixture-root',action='append',default=[],help='Relative directory whose files are fixture candidates; repeat as needed')
    a=p.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',a.commit):p.error('Full pinned commit required')
    result=inventory(a.root,a.name,a.commit,fixture_roots=a.fixture_root);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('upstream','commit','counts','runtime_enumeration_complete')}))
if __name__=='__main__':main()
