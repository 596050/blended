#!/usr/bin/env python3
"""Source-locked ports of four complete BLI collection test files, not a general translator.

Expected assertions come from upstream, not from the implementation. Pointer identity,
shared bit references, copy/move state and original loop bounds are preserved.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={
 'BLI_bit_ref_test.cc':'1d101274b2f6c0e52cbeaf892103d36b4af695bbbeecd11f43178ea7df572b40',
 'BLI_bit_vector_test.cc':'21297ed08bd7a266030f15d416dc483fe43fca1901fa99e4a3ccba02ccbe744c',
 'BLI_index_ranges_builder_test.cc':'9b24613cc64a90a6ae177173fdd3f63fa35c185ac7e8a83f63d1eb0d90cdd7cc',
 'BLI_unique_sorted_indices_test.cc':'9230df5cc6251e46aeacc59e95489591b908a190f7647076fde2d2eed8b4341f',
}
LOOP_COUNTS={'bit_vector.SizeConstructor':131,'bit_vector.SizeFillConstructor':128,'bit_vector.Iterator':100}
HEAD='''// SPDX-FileCopyrightText: 2023-2024 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from four complete, hash-locked Blender test files.
// See compatibility/collection-ports.json for API adaptations and provenance.
#![allow(non_snake_case, unused_mut, unused_parens)]
use crate::collections as m;
use core::cell::Cell;
#[derive(Debug,Default)]
pub struct Report { pub assertions: u32, pub failures: Vec<String> }
impl Report {
    fn check(&mut self, condition:bool, expression:&str, line:u32) {
        self.assertions+=1;
        if !condition {self.failures.push(format!("line {line}: {expression}"));}
    }
    pub fn passed(&self)->bool {self.assertions>0 && self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
'''
def extract(text):
    for match in re.finditer(r'\bTEST\((\w+),\s*(\w+)\)\s*\{',text):
        start=match.end();i=start;depth=1
        while depth:
            if text[i]=='{':depth+=1
            elif text[i]=='}':depth-=1
            i+=1
        yield match[1]+'.'+match[2],text[start:i-1],text.count('\n',0,match.start())+1

def split_args(text):
    depth=0;start=0;out=[]
    for i,ch in enumerate(text):
        if ch in '([{':depth+=1
        elif ch in ')]}':depth-=1
        elif ch==',' and not depth:out.append(text[start:i].strip());start=i+1
    return out+[text[start:].strip()]

def rewrite_calls(text,token,fn):
    pos=0
    while (start:=text.find(token,pos))>=0:
        i=start+len(token);depth=1
        while depth:
            if text[i]=='(':depth+=1
            elif text[i]==')':depth-=1
            i+=1
        value=fn(text[start+len(token):i-1]);text=text[:start]+value+text[i:];pos=start+len(value)
    return text

def expression(s,filename):
    s=s.strip().replace("'",'').replace('uint64_t(-1)','u64::MAX').replace('~','!')
    if filename=='BLI_bit_ref_test.cc':
        if s=='data':return 'data.get()'
        s=re.sub(r'\b(mask_first_n_bits|mask_last_n_bits|mask_single_bit|mask_range_bits)\(',r'm::\1(',s)
        s=s.replace('int_containing_bit(data_const,','m::word_ptr(&array,').replace('int_containing_bit(data,','m::word_ptr(&array,')
        s=re.sub(r'\b(data(?:_const)?) \+ (\d+)',r'\1.wrapping_add(\2)',s)
        if s in ('read_ref','ref'):s='read_ref.test()'
        s=s.replace('MutableBitRef(', 'm::MutableBitRef::new(').replace('BitRef(', 'm::BitRef::new(')
        if re.match(r'm::(?:Mutable)?BitRef::new\(',s) and not s.endswith('.test()'):s+='.test()'
    if filename=='BLI_bit_vector_test.cc':
        s=re.sub(r'\b(vec2?)\[([^\]]+)\]',r'\1.get(\2)',s)
        s=re.sub(r'ELEM\((\w+),\s*(.*?)\)',lambda m:'matches!('+m[1]+', '+m[2].replace(',',' |')+')',s)
        if s=='bit':s='bit.test()'
    if filename=='BLI_index_ranges_builder_test.cc':s=re.sub(r'builder\[(\d+)\]',r'builder.get(\1)',s)
    if filename=='BLI_unique_sorted_indices_test.cc':
        s=re.sub(r'std::get<IndexRange>\(parts\[(\d+)\]\)',r'parts[\1].as_range()',s)
        s=re.sub(r'std::get<Span<int>>\(parts\[(\d+)\]\)',r'parts[\1].as_slice()',s)
        s=re.sub(r'Span<int>\(\{([^}]+)\}\)',r'&[\1][..]',s)
        s=re.sub(r'\b(find_size_of_next_range|non_empty_is_range|non_empty_as_range|find_size_until_next_range|find_content_range)<int>',r'm::\1',s)
        s=re.sub(r'\{([^{}]+)\}',r'&[\1]',s)
        s=s.replace('data.index_range()','m::IndexRange::from_size(data.len() as i64)').replace('parts.size()','(parts.len() as i64)')
        s=s.replace('(data,','(&data,')
    s=s.replace('IndexRange::','m::IndexRange::').replace('m::m::','m::')
    s=rewrite_calls(s,'IndexRange(',lambda a: 'm::IndexRange::empty()' if not a.strip() else 'm::IndexRange::'+('new' if len(split_args(a))==2 else 'from_size')+'('+a+')')
    return s

def translate(body,filename):
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
    for name,macro in [('EQ','eq'),('TRUE','yes'),('FALSE','no')]:
        code=rewrite_calls(code,'EXPECT_'+name+'(',lambda s,macro=macro:macro+'!(r, '+', '.join(expression(x,filename) for x in split_args(s))+')')
    if filename=='BLI_bit_ref_test.cc':
        code=re.sub(r'uint64_t data = ([^;]+);',lambda m:'let data = Cell::new('+('u64::MAX' if m[1]=='-1' else '('+m[1]+') as u64')+');',code)
        code=code.replace('std::array<uint64_t, 5> array;', 'let array: [Cell<u64>;5] = core::array::from_fn(|_|Cell::new(0));')
        code=code.replace('uint64_t *data = array.data();','let data = array.as_ptr();').replace('const uint64_t *data_const = data;','let data_const = data;')
        if 'array.as_ptr()' in code:code=code.replace('data.get()','data')
        code=code.replace('MutableBitRef mutable_ref(&data, 3);','let mutable_ref = m::MutableBitRef::new(&data, 3);').replace('BitRef ref = mutable_ref;','let read_ref = mutable_ref.as_read();')
        code=code.replace('MutableBitRef(&data,','m::MutableBitRef::new(&data,').replace('m::m::','m::').replace('.set();','.set(true);')
    elif filename=='BLI_bit_vector_test.cc':
        code=re.sub(r'BitVector(?:<>)? (vec2?)\(\{([^}]+)\}\);',r'let mut \1 = m::BitVector::from_values(&[\2]);',code)
        code=re.sub(r'BitVector(?:<>)? (vec2?)\((\d+)(?:, (true|false))?\);',lambda m:f'let mut {m[1]} = m::BitVector::with_fill({m[2]}, {m[3] or "false"});',code)
        code=code.replace('BitVector vec;','let mut vec = m::BitVector::default();').replace('BitVector<> vec;','let mut vec = m::BitVector::default();')
        code=code.replace('BitVector<> vec2 = vec;', 'let mut vec2 = vec.clone();').replace('BitVector<> vec2 = std::move(vec);','let mut vec2 = core::mem::take(&mut vec);')
        code=re.sub(r'\b(vec2?)\[(\d+)\]\.set\(\);',r'\1.bit_mut(\2).set(true);',code)
        code=code.replace('for (BitRef bit : const_cast<const BitVector<> &>(vec))','for bit in vec.iter()').replace('for (BitRef bit : vec)','for bit in vec.iter()').replace('for (MutableBitRef bit : vec)','for bit in vec.iter_mut()')
        code=re.sub(r'for \(const int64_t (\w+) : IndexRange\((\d+)\)\)',r'for \1 in 0_i64..\2',code)
        code=code.replace('int64_t index = 0;','let mut index: i64 = 0;').replace('index++;','index+=1;')
        code=re.sub(r'ELEM\((\w+),\s*(.*?)\)',lambda m:'matches!('+m[1]+', '+m[2].replace(',',' |')+')',code)
    elif filename=='BLI_index_ranges_builder_test.cc':
        code=re.sub(r'IndexRangesBuilderBuffer<int, (\d+)> builder_buffer;\s*IndexRangesBuilder<int> builder\{builder_buffer\};',r'let mut builder = m::IndexRangesBuilder::<\1>::new();',code)
    else:
        code=re.sub(r'(?:Array|Vector)<int> data = \{([^}]+)\};',r'let data: Vec<i32> = vec![\1];',code)
        code=code.replace('Vector<std::variant<IndexRange, Span<int>>> parts;','let mut parts = Vec::new();')
        code=re.sub(r'const int64_t parts_num = split_to_ranges_and_spans<int>\(data, (\d+), parts\);',r'let parts_num = m::split_to_ranges_and_spans(&data, \1, &mut parts);',code)
    if re.search(r'\bEXPECT_|\bstd::|\bint64_t\b|\buint64_t\b|\bBitVector\s*<|\bconst_cast\b',code):raise ValueError('Untranslated C++ in '+filename+'\n'+code)
    return code

def generate(root=ROOT,upstream=None):
    upstream=upstream or root/'.upstream/blender'
    if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Pinned commit changed')
    output=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
    for name,sha in FILES.items():
        path='source/blender/blenlib/tests/'+name;raw=(upstream/path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Unreviewed source change: '+name)
        for identity,body,line in extract(raw.decode()):
            fn=identity.replace('.','__');code=translate(body,name)
            sites=len(re.findall(r'\bEXPECT_(?:EQ|TRUE|FALSE)\s*\(',body))
            if sites!=len(re.findall(r'\b(?:eq|yes|no)!',code)):raise ValueError('Assertion count changed: '+identity)
            runtime=LOOP_COUNTS.get(identity,sites)
            output+=f'\n// {path}:{line}\npub fn {fn}()->Report {{\nlet mut r=Report::default();\n{code}\nr\n}}\n'
            native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::collection_cases::{fn}();assert_eq!(r.assertions,{runtime});assert!(r.passed(),"{{r:?}}");}}\n'
            cases.append({'id':identity,'path':path,'line':line,'source_sha256':sha,'body_sha256':hashlib.sha256(body.encode()).hexdigest(),'rust_function':fn,'assertion_count':sites,'expected_runtime_assertions':runtime,'port_status':'translated','execution':'not_run'})
        dest=root/'tests/upstream/blender'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    (root/'crates/blended-core/src/collection_cases.rs').write_text(output)
    (root/'crates/blended-core/tests/upstream_collections.rs').write_text(native)
    manifest={'schema':1,'upstream_commit':PIN,'complete_blender_test_port':False,'cases':cases,'adapters':[
      'Bit references use shared Cell<u64> words; converted read references retain live aliasing, not a copied boolean.',
      'Pointer tests preserve word-address identity with checked slice addressing, including both upstream pointer-qualification contexts.',
      'Copy and move cases preserve independent copies and the observable empty moved-from state; no claim of matching inline-allocation strategy.',
      'IndexRangesBuilder retains fixed capacity and merges adjacent ascending ranges.',
      'C++ Span values map to borrowed Rust slices; IndexRange equality and all assertion/loop sequences retain the upstream contract.',
      'Uninitialised source words in the pointer-only test are initialised in safe Rust; the test does not read their contents.'
    ]}
    (root/'compatibility/collection-ports.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'assertion_sites':sum(c['assertion_count'] for c in cases),'runtime_assertions':sum(c['expected_runtime_assertions'] for c in cases)}))
if __name__=='__main__':generate()
