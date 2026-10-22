#!/usr/bin/env python3
"""Source-locked translations of three complete Blender test files, not a general C++ port."""
from pathlib import Path
import hashlib, json, re
from port_scalar_tests import extract, split_args
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={
    'BLI_index_range_test.cc':'df16feb982375c7420535382262caa09ee454c4330bb8c3357b24d712f15c74a',
    'BLI_binary_search_test.cc':'727451f8fcbc5d230558c26f82d6c46b62752688b006ca5e1e54c7d90daa9f5d',
    'BLI_bounds_test.cc':'a0b86885646bd7e606917154df25260e0bdfb8b36d2b24a1e3d6a7f9040fca1c',
}
HEAD='''// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from complete pinned test files. Values and assertion sites are retained.
// Rust slice/vector APIs replace C++ Span/Array/Vector; see structure-ports.json.
#![allow(non_snake_case, unused_mut, unused_parens)]
use crate::data_structures as m;
#[derive(Debug,Default)]
pub struct Report { pub assertions: u32, pub failures: Vec<String> }
impl Report {
    fn check(&mut self, condition: bool, expression: &str, line: u32) {
        self.assertions += 1;
        if !condition { self.failures.push(format!("line {line}: {expression}")); }
    }
    pub fn passed(&self) -> bool { self.assertions > 0 && self.failures.is_empty() }
}
macro_rules! eq { ($r:expr,$a:expr,$b:expr) => {{ $r.check($a == $b,stringify!($a == $b),line!()); }}; }
macro_rules! gt { ($r:expr,$a:expr,$b:expr) => {{ $r.check($a > $b,stringify!($a > $b),line!()); }}; }
macro_rules! yes { ($r:expr,$a:expr) => {{ $r.check($a,stringify!($a),line!()); }}; }
macro_rules! no { ($r:expr,$a:expr) => {{ $r.check(!$a,stringify!(!$a),line!()); }}; }
'''
def replace_calls(code,name,convert):
    pattern=re.compile(r'(?<![\w:])'+re.escape(name)+r'\s*\(')
    while mo:=pattern.search(code):
        i=mo.end();depth=1
        while depth:
            if code[i]=='(':depth+=1
            elif code[i]==')':depth-=1
            i+=1
        args=split_args(code[mo.end():i-1]);args=[] if args==[''] else args
        code=code[:mo.start()]+convert(args)+code[i:]
    return code

def transform(body,identity):
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
    code=re.sub(r'(\d+(?:\.\d*)?(?:e[+-]?\d+)?)[fF]\b',lambda m:(m[1]+'0' if m[1].endswith('.') else m[1])+'_f32',code)
    if identity=='index_range.constexpr_':
        return '''const RANGE: m::IndexRange = m::IndexRange::new(1,1);
let compiles: [i32; RANGE.get(0) as usize] = [1];
const _: () = assert!(RANGE.size() == 1);
eq!(r, compiles[0], 1);'''
    code=re.sub(r'\b(?:const )?Bounds<\w+> (\w+)\(([^;]+)\);',lambda mo:'let mut '+mo[1]+' = m::Bounds::'+('point' if len(split_args(mo[2]))==1 else 'new')+'('+mo[2]+');',code)
    code=re.sub(r'\bArray<\w+> (\w+) = \{([^;]*)\};',r'let \1 = vec![\2];',code)
    for typ,n,scalar in [('float2',2,'f32'),('float3',3,'f32'),('int2',2,'i32'),('int3',3,'i32')]:
        def vec(args,n=n,scalar=scalar):
            if len(args)==1:return f'm::VecN([({args[0]}) as {scalar};{n}])'
            if len(args)!=n:raise ValueError('Unexpected vector arity')
            return 'm::VecN(['+', '.join(f'({a}) as {scalar}' for a in args)+'])'
        code=replace_calls(code,typ,vec)
    code=code.replace('Array<int2> data(10000);','let mut data = vec![m::VecN([0_i32;2]);10000];')
    code=code.replace('Span<float2> empty_span{};','let empty_span: [m::VecN<f32,2>;0] = [];')
    code=code.replace('const float2 bound2_size','let bound2_size')
    code=code.replace('std::nullopt','None')
    code=re.sub(r'(\w+)\.as_span\(\)',r'&\1',code)
    code=code.replace('bounds::min_max','m::min_max').replace('m::min_max(empty_span)','m::min_max(&empty_span)')
    code=code.replace('result->','result.unwrap().')
    code=re.sub(r'for \(const int(?:64_t)? i : (\w+)\.index_range\(\)\)',r'for i in 0..\1.len()',code)
    code=code.replace('Vector<int64_t> vector;', 'let mut vector: Vec<i64> = Vec::new();')
    code=code.replace('vector.append(', 'vector.push(').replace('vector.size()', '(vector.len() as i64)')
    code=code.replace('for (int64_t value : range)', 'for value in range.iter()')
    code=code.replace('for (int i = 0; i < 4; i++)', 'for i in 0..4_usize').replace('vector[i], i + 6','vector[i], (i + 6) as i64')
    code=code.replace('*range.begin()','range.iter().next().unwrap()')
    code=code.replace('std::any_of(range.begin(), range.end(), [](int v) { return v == 6; })','range.iter().any(|v| v == 6)')
    code=code.replace('std::any_of(range.begin(), range.end(), [](int v) { return v == 20; })','range.iter().any(|v| v == 20)')
    code=code.replace('std::count_if(range.begin(), range.end(), [](int v) { return v < 7; })','range.iter().filter(|&v| v < 7).count()')
    code=re.sub(r'\bIndexRange (\w+);',r'let \1 = m::IndexRange::empty();',code)
    code=re.sub(r'\b(?:const )?IndexRange (\w+)[({]([^;]+)[)}];',r'let \1 = IndexRange(\2);',code)
    code=re.sub(r'\b(?:const )?IndexRange (\w+)\s*=',r'let \1 =',code)
    code=re.sub(r'(?<!:)\bIndexRange::','m::IndexRange::',code)
    def ir(args):
        return 'm::IndexRange::'+('new' if len(args)==2 else 'from_size' if len(args)==1 else 'empty')+'('+', '.join(args)+')'
    code=replace_calls(code,'IndexRange',ir)
    code=code.replace('.slice(m::IndexRange::', '.slice_range(m::IndexRange::')
    code=re.sub(r'\b(range|slice|a)\[([^\]]+)\]',r'\1.get(\2)',code)
    code=code.replace('AlignedIndexRanges ranges', 'let ranges').replace('split_index_range_by_alignment(', 'm::split_index_range_by_alignment(')
    code=re.sub(r'\bauto (\w+)\s*=',r'let \1 =',code)
    code=re.sub(r'Span(?:<bool>)?\{([^}]+)\}',r'&[\1]',code).replace('Span<bool>{}','&[]')
    code=code.replace('value_pass','|v: &bool| *v').replace('first_if(', 'm::first_if(').replace('last_if(', 'm::last_if(')
    for before,after in [('EXPECT_EQ','eq'),('EXPECT_GT','gt'),('EXPECT_TRUE','yes'),('EXPECT_FALSE','no')]:
        code=code.replace(before+'(',after+'!(r, ')
    if re.search(r'EXPECT_|\b(?:Array|Span|Bounds|IndexRange|Vector)<|std::|->',code):raise ValueError(('Unhandled construct',identity,code))
    return code

def generate():
    out=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
    for filename,expected in FILES.items():
        path='source/blender/blenlib/tests/'+filename
        raw=(ROOT/'.upstream/blender'/path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Source changed: '+filename)
        dest=ROOT/'tests/upstream/blender'/filename;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        for identity,name,body,line in extract(raw.decode()):
            code=transform(body,identity)
            source_sites=len(re.findall(r'\bEXPECT_\w+\s*\(',body))
            target_sites=len(re.findall(r'\b(?:eq|gt|yes|no)!',code))
            if source_sites!=target_sites:raise ValueError((identity,source_sites,target_sites))
            count=source_sites + (3 if identity=='index_range.MultipleElementRange' else 6 if identity=='bounds.Contains' else 0)
            function=identity.replace('.','__')
            out+=f'\n// {path}:{line}\npub fn {function}() -> Report {{\nlet mut r = Report::default();\n{code}\nr\n}}\n'
            native+=f'#[test]\n#[allow(non_snake_case)]\nfn {function}() {{let r=blended_core::structure_cases::{function}();assert_eq!(r.assertions,{count},"Assertion execution changed");assert!(r.passed(),"{{r:?}}");}}\n'
            cases.append(dict(id=identity,path=path,line=line,source_sha256=expected,body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=function,assertion_count=source_sites,expected_runtime_assertions=count,compile_time_assertions=int(identity=='index_range.constexpr_'),port_status='translated',execution='not_run'))
    out+='\npub const CASES: &[(&str,fn()->Report,u32)] = &[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    (ROOT/'crates/blended-core/src/structure_cases.rs').write_text(out)
    (ROOT/'crates/blended-core/tests/upstream_structures.rs').write_text(native)
    meta=dict(schema=1,upstream_commit=PIN,cases=cases,selected_source_files_complete=True,complete_blender_test_port=False,adapter_policy='C++ Span/Array/Vector storage uses Rust slices/Vec; vector values use fixed-size VecN. IndexRange operator[] uses a checked const get method. EXPECT_EQ/GT/TRUE/FALSE remain nonfatal and exact. Repeated assertions, loop bounds, and the constexpr/static assertion are preserved.')
    (ROOT/'compatibility/structure-ports.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f'{len(cases)} cases; {sum(c["assertion_count"] for c in cases)} assertion sites; {sum(c["expected_runtime_assertions"] for c in cases)} runtime assertions; 1 compile-time assertion')
if __name__=='__main__':generate()
