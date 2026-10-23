#!/usr/bin/env python3
"""Reviewed complete-file ports for bit spans, bit groups and C bitmaps.

Includes the original iteration bounds and the assertion-free empty-span smoke
case. Helpers expand exactly to the assertions executed by Blender's testing.h.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from port_string_ref_tests import strip_comments,split_args,rewrite_calls,extract
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={'BLI_bit_span_test.cc': '8dcf6c71063a45f72623b2d33dcaddaad7c4c06d447b93bfc15754a96a8fff82', 'BLI_bit_group_vector_test.cc': '246c01c57c51251ff2fe657fd6a1c85138baa00ddb492b7fc223293046e39763', 'BLI_bitmap_test.cc': '49c1ee49fb00de67637066d232214ddab45375ebda6141ccb4811ca26aaa296d'}
COUNTS={
 'bit_span.DefaultConstructor':4,'bit_span.Iteration':108,'bit_span.MutableIteration':2,
 'bit_span.SubscriptOperator':14,'bit_span.RangeConstructor':5,'bit_span.Set':4,
 'bit_span.SetEmpty':0,'bit_span.SetSliced':1280,'bit_span.IsBounded':19,
 'bit_span.CopyFrom':100,'bit_span.InPlaceOr':6400,'bit_span.InPlaceAnd':6400,
 'bit_span.ForEach1':1,'bit_span.ForEach1Cancel':4,'bit_span.FindFirst1Index':7,
 'bit_span.FindFirst0Index':5,'bit_span.or_bools_into_bits':10,
 'bit_span.to_index_ranges_small':3,'bit_span.to_index_ranges_all_ones':2,
 'bit_group_vector.DefaultConstruct':1,'bit_group_vector.Construct':3,
 'bit_group_vector.CopyConstruct':62,'bit_group_vector.foreachAnd':12,
 'bitmap.empty_is_all_unset':10,'bitmap.find_first_unset_empty':1,
 'bitmap.find_first_unset_full':1,'bitmap.find_first_unset_middle':2,
}
HEAD='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from three complete hash-locked Blender bit test files.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::bit_spans as m;
use core::cell::Cell;
#[derive(Debug,Default)]
pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
    fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
    // SetEmpty has no EXPECT statements upstream. Completion is verified by
    // explicit start/end events, native test discovery and a negative mutation.
    pub fn passed(&self)->bool{self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let(a,b)=(&$a,&$b);$r.check(a==b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! seq_eq {($r:expr,$a:expr,$b:expr)=>{{let(a,b)=($a,$b);eq!($r,a.len() as i64,b.len() as i64);if a.len()==b.len(){for i in 0..a.len(){eq!($r,a[i],b[i]);}}}};}
'''
POISON='''
    // Preserve placement construction over deliberately poisoned storage. Do not
    // inspect the invalid representation until write() has fully constructed it.
    {
        let mut storage=core::mem::MaybeUninit::<m::BitSpan<'static>>::uninit();
        unsafe{core::ptr::write_bytes(storage.as_mut_ptr().cast::<u8>(),0xff,core::mem::size_of::<m::BitSpan<'static>>());}
        let span=storage.write(m::BitSpan::empty());
        yes!(r,span.is_empty());eq!(r,span.size(),0);
    }
    {
        let mut storage=core::mem::MaybeUninit::<m::MutableBitSpan<'static>>::uninit();
        unsafe{core::ptr::write_bytes(storage.as_mut_ptr().cast::<u8>(),0xff,core::mem::size_of::<m::MutableBitSpan<'static>>());}
        let span=storage.write(m::MutableBitSpan::empty());
        yes!(r,span.is_empty());eq!(r,span.size(),0);
    }
'''

def transform(identity,body):
    if identity=='bit_span.DefaultConstructor':return POISON
    code=strip_comments(body)
    code=re.sub(r"(?<=[0-9a-fA-F])'(?=[0-9a-fA-F])",'',code)
    code=code.replace('uint64_t(-1)','u64::MAX').replace('~uint64_t(0)','u64::MAX').replace('uint64_t(0)','0_u64')
    code=code.replace('BitsPerInt','64_i64').replace('0xFBu','0xFB_u64')
    scalar=set(re.findall(r'uint64_t (data\d*)\s*=',code))
    arrays=set(re.findall(r'(?:std::array<uint64_t,\s*\d+>\s+|uint64_t\s+)(\w+)\s*(?:\[|;|\{)',code))
    for name in sorted(scalar,key=len,reverse=True):
        code=re.sub(r'\buint64_t '+name+r' = ([^;]+);',lambda m:f'let {name} = Cell::new(({m[1]}) as u64);',code)
    code=re.sub(r'std::array<uint64_t, (\d+)> (\w+)(?:\{\})?;',lambda m:f'let {m[2]}: [Cell<u64>;{m[1]}] = core::array::from_fn(|_|Cell::new(0));',code)
    code=re.sub(r'uint64_t (\w+)\[(\d+)\] = \{([^}]+)\};',lambda m:f'let {m[1]}: [Cell<u64>;{m[2]}] = [{m[3]}].map(Cell::new);',code)
    code=re.sub(r'memset\((\w+)\.data\(\), 0, sizeof\(\1\)\);',r'for word in &\1 {word.set(0);}',code)
    code=re.sub(r'(\w+)\.fill\(-1\);',r'for word in &\1 {word.set(u64::MAX);}',code)
    code=code.replace('uint64_t i = 0;','let mut i: u64 = 0;').replace('for (uint64_t &value : src_data)','for value in &src_data').replace('value = i;','value.set(i);')
    # Local dynamic arrays retain ordered values. BitVector is the production packed-bit adapter.
    code=re.sub(r'(?:const )?Vector<int> (\w+)\s*(?:=\s*)?\{([^}]+)\};',r'let \1: Vec<i32> = vec![\2];',code)
    code=re.sub(r'Vector<int> (\w+);',r'let mut \1: Vec<i32> = Vec::new();',code)
    code=re.sub(r'Vector<bool> (\w+)\((\d+), (true|false)\);',r'let mut \1: Vec<bool> = vec![\3;\2];',code)
    code=code.replace('BitVector<> bits(bools.size());','let mut bits = m::BitVector::with_fill(bools.len() as i64, false);')
    code=re.sub(r'BitVector<> (\w+)\((\d+)(?:, (true|false))?\);',lambda m:f'let mut {m[1]} = m::BitVector::with_fill({m[2]}, {m[3] or "false"});',code)
    code=re.sub(r'BitVector<> (\w+)\{Span<bool>\{([^}]+)\}\};',r'let mut \1 = m::BitVector::from_values(&[\2]);',code)
    code=re.sub(r'BitGroupVector<> (\w+);',r'let \1 = m::BitGroupVector::default();',code)
    code=re.sub(r'BitGroupVector<> (\w+)\((\d+), (\d+)\);',r'let \1 = m::BitGroupVector::new(\2,\3);',code)
    code=code.replace('BitGroupVector<> copy(groups);','let copy = groups.clone();')
    code=re.sub(r'IndexRangesBuilderBuffer<int, (\d+)> builder_buffer;\s*IndexRangesBuilder<int> builder\(builder_buffer\);',r'let mut builder = m::IndexRangesBuilder::<\1>::new();',code)
    code=re.sub(r'BLI_BITMAP_DECLARE\((\w+), (\d+)\);',r'let mut \1 = m::Bitmap::new(\2);',code)
    code=re.sub(r'BLI_bitmap_flip_all\((\w+), (\d+)\)',r'\1.flip_all(\2)',code)
    code=re.sub(r'BLI_bitmap_find_first_unset\((\w+), (\d+)\)',r'\1.find_first_unset(\2)',code)
    code=re.sub(r'BLI_BITMAP_TEST_BOOL\((\w+), (\w+)\)',r'\1.get(\2)',code)
    code=re.sub(r'BLI_BITMAP_DISABLE\((\w+), (\d+)\)',r'\1.set(\2,false)',code)
    code=re.sub(r'BLI_BITMAP_ENABLE\((\w+), (\d+)\)',r'\1.set(\2,true)',code)
    # Convert range literals before bit-span constructor adaptation.
    code=rewrite_calls(code,'IndexRange(',lambda a:'m::IndexRange::'+('new' if len(split_args(a))==2 else 'from_size')+'('+a+')')
    code=code.replace('IndexRange::from_', 'm::IndexRange::from_').replace('m::m::','m::')
    code=re.sub(r'\.slice\(\{([^}]+)\}\)',r'.slice(m::IndexRange::new(\1))',code)
    # Declarations and calls share the same checked borrowed constructor adapter.
    code=re.sub(r'(?:const )?(MutableBitSpan|BitSpan) (\w+)[({]',lambda m:'DECL_'+m[1]+'_'+m[2]+'(',code)
    code=re.sub(r'(DECL_[^;]+)\};',r'\1);',code)
    def ctor(kind,a):
        args=split_args(a)
        if args==['']:return f'm::{kind}::empty()'
        if len(args)==1:return f'm::{kind}::from_vector(&{args[0]})'
        data,rng=args
        if data.startswith('&') and data[1:] in scalar:words='core::slice::from_ref('+data+')'
        elif data.endswith('.data()'):words='&'+data[:-7]
        else:words='&'+data
        rng=re.sub(r'(\w+)\.size\(\)',r'(\1.len() as i64)',rng) if '.data()' in data else rng
        if not rng.startswith('m::IndexRange::'):rng='m::IndexRange::from_size('+rng+')'
        return f'm::{kind}::new({words}, {rng})'
    while (mat:=re.search(r'DECL_(MutableBitSpan|BitSpan)_(\w+)\(',code)):
        kind,name=mat.groups();code=rewrite_calls(code,mat[0],lambda a,kind=kind,name=name:f'let mut {name} = '+ctor(kind,a))
    for kind in ['MutableBitSpan','BitSpan']:
        code=rewrite_calls(code,kind+'(',lambda a,kind=kind:ctor(kind,a))
    code=code.replace('BitSpan span = mutable_span;','let span = mutable_span.as_read();')
    code=re.sub(r'(MutableBoundedBitSpan|BoundedBitSpan) (\w+) = (\w+)\[([^\]]+)\];',lambda m:f'let {m[2]} = {m[3]}.group({m[4]})'+('.as_read()' if m[1]=='BoundedBitSpan' else '')+';',code)
    code=re.sub(r'\bgroups\[(\d+)\]',r'groups.group(\1)',code)
    # Indexing preserves shared references, not Boolean snapshots.
    span_names=set(re.findall(r'let (?:mut )?(\w+) = m::(?:Mutable)?BitSpan::',code))|{'span','mutable_span','copy_span','src','dst','span_1','span_2'}
    for name in sorted(span_names,key=len,reverse=True):
        code=re.sub(r'\b'+name+r'\[([^\]]+)\]',name+r'.bit(\1)',code)
    code=re.sub(r'(groups\.group\(\d+\))\[([^\]]+)\]',r'\1.bit(\2)',code)
    for name in ['vec_a','vec_b','vec','bits','mask']:
        code=re.sub(r'\b'+name+r'\[([^\]]+)\]',name+r'.bit_mut(\1)',code)
    code=code.replace('.set();','.set(true);').replace('.set_all();','.set_all(true);')
    code=re.sub(r'\bbuilder\[(\d+)\]',r'builder.get(\1)',code)
    # Numeric source counters and loops keep the original bounds.
    code=re.sub(r'for \(int i = 0; i < (\d+); \+\+i\)',r'for i in 0..\1',code)
    code=re.sub(r'\bint (index|i) = ([^;]+);',r'let mut \1: i32 = \2;',code)
    code=code.replace('index++;','index+=1;').replace('i++;','i+=1;')
    code=re.sub(r'for \(int i = 0; i < (\d+); \+\+i\)',r'for i in 0..\1',code)
    code=re.sub(r'for \((?:\[\[maybe_unused\]\] )?const (?:int64_t|int) (\w+) : ([^)]+\([^)]*\))\)',r'for \1 in \2',code)
    code=re.sub(r'for \(const int (\w+) : \{([^}]+)\}\)',r'for \1 in [\2]',code)
    code=code.replace('for (const BitRef bit : span)','for bit in span.iter()').replace('for (MutableBitRef bit : span)','for bit in span.iter()')
    code=re.sub(r'for (\w+) in (\w+)\.index_range\(\)',r'for \1 in 0..\2.size()',code)
    code=re.sub(r'for (\w+) in m::IndexRange::from_size\((\d+)\)',r'for \1 in 0_i64..\2',code)
    for name in scalar:code=code.replace('iter_1_indices('+name+')','m::iter_1_indices('+name+'.get())')
    code=code.replace('.append(','.push(')
    code=code.replace('ELEM(index, 2, 3)','matches!(index,2|3)')
    # Callback return semantics, including cancellation after visiting the current bit.
    code=re.sub(r'foreach_1_index\((.*?),\s*\[&\]\(const int i\) \{(.*?)\}\);',lambda m:'m::foreach_1_index(&('+m[1]+'), |i| {'+m[2].replace('return ','').replace(';\n    ',';\n    ')+(' true ' if 'return' not in m[2] else '')+'});',code,flags=re.S)
    code=re.sub(r'(\bi < (?:5|15)|\bfalse|\btrue);\s*\}\);',r'\1 });',code)
    def expr_adapter(a):
        parts=split_args(a)
        if len(parts)!=3 or re.sub(r'\s+', '',parts[0])!='[](constBitInta,constBitIntb){returna^b;}':raise ValueError('Unreviewed bit expression callback')
        return 'm::find_first_1_index_expr(&'+parts[1]+', &'+parts[2]+', |a,b| a ^ b)'
    code=rewrite_calls(code,'find_first_1_index_expr(',expr_adapter)
    for fn in ['find_first_1_index','find_first_0_index','is_bounded_span']:
        code=rewrite_calls(code,fn+'(',lambda a,fn=fn:'m::'+fn+'(&('+a+'))')
    code=rewrite_calls(code,'bits::or_bools_into_bits(',lambda a:'m::or_bools_into_bits(&'+split_args(a)[0]+', &('+split_args(a)[1]+'))')
    code=rewrite_calls(code,'bits_to_index_ranges(',lambda a:'m::bits_to_index_ranges(&('+split_args(a)[0]+'), &mut '+split_args(a)[1]+')')
    code=code.replace('groups.foreach_and(mask)','groups.foreach_and(&mask)').replace('.as_span()', '.as_slice()')
    code=code.replace('span_1 |= span_2;', 'span_1.or_assign(span_2);').replace('span_1 &= span_2;', 'span_1.and_assign(span_2);')
    code=re.sub(r'Span\(\{([^}]+)\}\)',r'&[\1][..]',code)
    code=code.replace('std::nullopt','None')
    code=rewrite_calls(code,'EXPECT_EQ_SPAN(',lambda a:'seq_eq!(r,'+a+')')
    # Assertions preserve source operands; bit-reference conversions are explicit.
    def operand(a):
        a=a.strip()
        if a in scalar:return a+'.get()'
        if a=='data' and 'SubscriptOperator' in identity:return 'data.as_ptr()'
        if re.fullmatch(r'data\[\d+\]',a):return a+'.get()'
        if re.search(r'\.bit(?:_mut)?\([^()]*\)$',a):return a+'.test()'
        return a
    for name,macro in [('EQ','eq'),('TRUE','yes'),('FALSE','no')]:
        def assertion(a,name=name,macro=macro):
            args=[operand(x) for x in split_args(a)]
            if name=='EQ' and args[0].startswith('m::find_first_') and args[1]!='None':args[1]='Some('+args[1]+')'
            return macro+'!(r, '+', '.join(args)+')'
        code=rewrite_calls(code,'EXPECT_'+name+'(',assertion)
    code=code.replace('bools.size()','(bools.len() as i64)').replace('src_data.size()','(src_data.len() as i64)').replace('data.size()','(data.len() as i64)').replace('data_1.size()','(data_1.len() as i64)').replace('data_2.size()','(data_2.len() as i64)')
    if re.search(r'\bEXPECT_|\bstd::|\buint64_t\b|\bint64_t\b|\bBitSpan\s+|\bBitVector\s*<|\bVector<|\bBLI_BITMAP',code):raise ValueError('Unsupported C++ in '+identity+'\n'+code)
    return code

def generate(root=ROOT,upstream=None):
    upstream=upstream or root/'.upstream/blender';out=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
    if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong source pin')
    for name,sha in FILES.items():
        path='source/blender/blenlib/tests/'+name;raw=(upstream/path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Unreviewed upstream source change: '+name)
        for identity,body,line in extract(raw.decode()):
            code=transform(identity,body);fn=identity.replace('.','__');count=COUNTS[identity]
            sites=len(re.findall(r'\bEXPECT_(?:EQ_SPAN|EQ|TRUE|FALSE)\s*\(',body))
            if sites!=len(re.findall(r'\b(?:eq|yes|no|seq_eq)!',code)):raise ValueError('Assertion sites changed in '+identity)
            out+=f'\n// {path}:{line}\npub fn {fn}()->Report {{\nlet mut r=Report::default();\n{code}\nr\n}}\n'
            native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::bit_span_cases::{fn}();assert_eq!(r.assertions,{count});assert!(r.passed(),"{{r:?}}");}}\n'
            cases.append(dict(id=identity,path=path,line=line,source_sha256=sha,body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=sites,expected_runtime_assertions=count,assertion_free_smoke=count==0,port_status='translated',execution='not_run'))
        (root/'tests/upstream/blender'/name).write_bytes(raw)
    if set(COUNTS)!={c['id'] for c in cases}:raise ValueError('Source case universe changed')
    out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    (root/'crates/blended-core/src/bit_span_cases.rs').write_text(out);(root/'crates/blended-core/tests/upstream_bit_spans.rs').write_text(native)
    (root/'compatibility/bit-span-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,complete_blender_test_port=False,cases=cases,adapters=['Shared Cell<u64> backing preserves live read/mutable aliases; slices use original bit offsets.','Placement default construction retains the deliberately poisoned storage setup using MaybeUninit.','Original 640 and 6400 iteration bounds, callback cancellation and assertion helper expansion are preserved.','Uninitialised C++ backing words are safely initialised before otherwise identical writes; no asserted result depends on the old indeterminate bits.','The zero-assertion SetEmpty smoke case is separately tracked and must complete, not disappear from execution.']),indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases),sites=sum(c['assertion_count'] for c in cases),runtime=sum(c['expected_runtime_assertions'] for c in cases))))
if __name__=='__main__':generate()
