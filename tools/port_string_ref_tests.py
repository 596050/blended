#!/usr/bin/env python3
"""Faithful source-locked translation of the complete BLI string-reference test file.

This is a reviewed syntax adapter, not an arbitrary C++ transpiler. Source changes
fail closed. Borrowed bytes, pointer identity, NUL termination and constexpr checks
are preserved rather than replaced by canned expected values.
"""
from __future__ import annotations
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
NAME='BLI_string_ref_test.cc'
SOURCE_HASH='c5ff75c549388f3e0b58aa29909f97134f3108dcd17b6d12d1f8ecb4980f43c3'

# Numeric separators must be consumed as part of a preprocessing-number token,
# not as the beginning of a character literal. Masking preserves offsets/lines.
_NUMERIC = r"(?<![\w.])(?:[0-9]|\.[0-9])(?:[eEpP][+-]|[\w.]|'(?=\w))*"
_LITERAL = r'R"([^ ()\\\t\r\n]{0,16})\([\s\S]*?\)\1"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
_COMMENTS = r'//[^\n]*|/\*[\s\S]*?\*/'
_TOKENS = re.compile(_NUMERIC + '|' + _LITERAL + '|' + _COMMENTS)

def _spaces(text):
    return ''.join('\n' if c == '\n' else ' ' for c in text)

def code_mask(text):
    return _TOKENS.sub(lambda m: _spaces(m[0]), text)

def strip_comments(text):
    return _TOKENS.sub(lambda m: _spaces(m[0]) if m[0].startswith(('//', '/*')) else m[0], text)

def split_args(text):
    out=[];start=0;depth=0
    for i,c in enumerate(code_mask(text)):
        if c in '([{':depth+=1
        elif c in ')]}':
            depth-=1
            if depth<0:raise ValueError('Unbalanced argument delimiter')
        elif c==',' and depth==0:out.append(text[start:i].strip());start=i+1
    if depth:raise ValueError('Unbalanced argument list')
    return out+[text[start:].strip()]

def rewrite_calls(text,token,fn):
    pos=0
    while True:
        masked=code_mask(text);start=masked.find(token,pos)
        if start<0:return text
        i=start+len(token);depth=1
        while i<len(text) and depth:
            c=masked[i]
            if c=='(':depth+=1
            elif c==')':depth-=1
            i+=1
        if depth:raise ValueError('Unbalanced call: '+token)
        value=fn(text[start+len(token):i-1]);text=text[:start]+value+text[i:];pos=start+len(value)

def extract(text):
    clean=strip_comments(text);masked=code_mask(clean)
    for m in re.finditer(r'\bTEST\(\s*(\w+),\s*(\w+)\)\s*\{',masked):
        start=m.end();i=start;depth=1
        while i<len(clean) and depth:
            c=masked[i]
            if c=='{':depth+=1
            elif c=='}':depth-=1
            i+=1
        if depth:raise ValueError('Unbalanced source case: '+m[1]+'.'+m[2])
        yield m[1]+'.'+m[2],clean[start:i-1],text.count('\n',0,m.start())+1

def byte_literal(lit,nul=False):
    # Python and the reviewed C++ file share the escape forms used here.
    value=ast.literal_eval(lit).encode('utf-8')+(b'\0' if nul else b'')
    return 'b"'+''.join(chr(c) if 32<=c<127 and c not in (34,92) else '\\x%02x'%c for c in value)+'"'

def ctor(kind,args):
    a=split_args(args)
    if a==['']:return f'm::{kind}::empty()'
    if kind=='StringRef' and len(a)==2 and a==['nullptr','nullptr']:return 'm::StringRef::empty()'
    if a[0].startswith('"') and a[0].endswith('"'):
        first=byte_literal(a[0],True)
        return f'm::{kind}::from_cstr({first})' if len(a)==1 else f'm::{kind}::from_cstr_len({first}, {a[1]})'
    if len(a)==2:
        if a[1]==a[0]:return f'm::{kind}::from_bounds({a[0]},0,0)'
        if a[1].startswith(a[0]+' + '):return f'm::{kind}::from_bounds({a[0]},0,{a[1][len(a[0])+3:]})'
        return f'm::{kind}::from_cstr_len({a[0]}, {a[1]})'
    if a[0]=='str':return f'm::{kind}::from_cstr({a[0]}.as_ref())'
    if a[0]=='view':return f'm::{kind}::from_bytes({a[0]}.as_ref())'
    if a[0]=='dst':return f'm::{kind}::from_cstr(&dst)'
    return f'm::{kind}::from_bytes({a[0]})'

def translate(identity,body):
    code=body.replace('BLI_STR_UTF8_SUPERSCRIPT_2 BLI_STR_UTF8_SUPERSCRIPT_2','"²²"').replace('BLI_STR_UTF8_SUPERSCRIPT_2','"²"')
    # Character values are bytes, not Unicode code points; Blender builds with unsigned char.
    code=re.sub(r"'(?:\\.|[^'\\])*'",lambda m:('0_u8' if m[0] in ("'\\0'","'\\000'") else 'b'+m[0]),code)
    code=re.sub(r'\bref\b','sref',code)
    # Keep quoted tokens in a table so transformations cannot edit literal text.
    strings=[]
    def token(m):strings.append(m[0]);return '@L'+str(len(strings)-1)+'@'
    code=re.sub(r'"(?:\\.|[^"\\])*"',token,code)
    def restore(s):
        return re.sub(r'@L(\d+)@',lambda m:strings[int(m[1])],s)
    code=re.sub(r'const char \*(\w+) = (@L\d+@);',lambda m:f'let {m[1]} = {byte_literal(restore(m[2]),True)};',code)
    code=re.sub(r'std::string (\w+) = (@L\d+@);',lambda m:f'let {m[1]} = m::Bytes::from_slice({byte_literal(restore(m[2]))});',code)
    code=re.sub(r'std::string_view (\w+) = (@L\d+@);',lambda m:f'let {m[1]}: &[u8] = {byte_literal(restore(m[2]))};',code)
    code=re.sub(r'(?m)^\s*(StringRefNull|StringRef) (\w+);',lambda m:f'\nlet {m[2]} = m::{m[1]}::empty();',code)
    # Handle declarations with balanced constructor calls; the source shapes are locked.
    code=re.sub(r'(StringRefNull|StringRef) (\w+)\(',lambda m:'DECL_'+m[1]+'_'+m[2]+'(',code)
    while (match:=re.search(r'DECL_(StringRefNull|StringRef)_(\w+)\(',code)):
        kind,name=match.groups();tok=match[0]
        code=rewrite_calls(code,tok,lambda a,kind=kind,name=name:f'let {name} = '+ctor(kind,restore(a)))
    # Above injected literal bytes are preserved; remaining source literal tokens are views.
    code=re.sub(r'StringRef\(Span<char>\((@L\d+@), (\d+)\)\)',lambda m:f'm::StringRef::from_cstr_len({byte_literal(restore(m[1]),True)}, {m[2]})',code)
    code=rewrite_calls(code,'StringRef(',lambda a:ctor('StringRef',restore(a)))
    code=rewrite_calls(code,'StringRefNull(',lambda a:ctor('StringRefNull',restore(a)))
    code=rewrite_calls(code,'std::string(',lambda a:'m::Bytes::from_slice('+byte_literal(restore(a))+')')
    code=re.sub(r'StringRef (\w+) = (@L\d+@);',lambda m:f'let {m[1]} = m::StringRef::from_cstr({byte_literal(restore(m[2]),True)});',code)
    code=code.replace('StringRef sref = view;','let sref = m::StringRef::from_bytes(view);')
    code=code.replace('std::string_view view = sref;','let view = sref.as_bytes();')
    code=re.sub(r'StringRef (\w+) = ([^;]+);',r'let \1 = \2;',code)
    code=re.sub(r'std::string (\w+) = ([^;]+);',lambda m:f'let {m[1]} = '+ ('sref.to_owned_bytes()' if m[2]=='sref' else m[2])+';',code)
    code=code.replace('std::stringstream ss;','let mut ss: Vec<u8> = Vec::new();').replace('ss << sref;','sref.write_to(&mut ss).expect("memory stream write");').replace('ss.str()','m::Bytes::from_slice(&ss)')
    code=code.replace('Vector<char> chars;','let mut chars: Vec<u8> = Vec::new();').replace('for (char c : sref)','for c in sref.iter()').replace('chars.append(c)','chars.push(c)').replace('chars.size()','(chars.len() as i64)')
    code=re.sub(r'char dst\[(\d+)\];',r'let mut dst: [u8;\1] = [0;\1];',code)
    code=re.sub(r'memset\(dst, 0xFF, (\d+)\);',r'dst.fill(0xFF);',code)
    code=code.replace('.copy_utf8_truncated(dst)','.copy_utf8_truncated(&mut dst)').replace('.copy_bytes_truncated(dst)','.copy_bytes_truncated(&mut dst)')
    for name in ['trim','trim_left','trim_right']:
        def trimming(a,name=name):
            if not a:return '.'+name+'_whitespace()'
            if a.startswith('@L'):return '.'+name+'_bytes('+byte_literal(restore(a))+')'
            return '.'+name+'_bytes(&['+a+'])'
        code=rewrite_calls(code,'.'+name+'(',trimming)
    for name in ['startswith','endswith','drop_known_prefix']:
        code=rewrite_calls(code,'.'+name+'(',lambda a,name=name:'.'+name+'('+byte_literal(restore(a))+')')
    code=rewrite_calls(code,'.substr(',lambda a:'.substr_to_end('+a+')' if len(split_args(a))==1 else '.substr('+a+')')
    # Preserve constexpr values and compile-time assertions, including the dependent array bound.
    code=code.replace('constexpr let sref =','const SREF: m::'+('StringRefNull' if identity.startswith('string_ref_null.') else 'StringRef')+"<'static> =")
    if 'const SREF:' in code:
        code=code.replace('sref[2]','SREF.at(2)').replace('sref.size()','SREF.size()').replace("sref.find_first_of(b'o')","SREF.find_first_of(b'o')")
        code=re.sub(r'BLI_STATIC_ASSERT\((.*?), @L\d+@\);',r'const _: () = assert!(\1);',code)
        code=code.replace("std::array<int, std::size_t(SREF.find_first_of(b'o'))> compiles = {1};","const COMP_LEN: usize = SREF.find_first_of(b'o') as usize;\nconst COMPILES: [i32;COMP_LEN] = m::array_with_first(1);\nlet compiles = COMPILES;")
    # Literal strings in comparisons are borrowed byte views, never pointer-comparison substitutes.
    code=re.sub(r'@L(\d+)@',lambda m:'m::StringRef::from_bytes('+byte_literal(strings[int(m[1])])+')',code)
    # Own-string/borrowed-view concatenation is an explicit language adapter.
    code=re.sub(r'let result = ([^;]+) \+ ([^;]+);',r'let result = m::concat(&(\1), &(\2));',code)
    # Raw data assertions compare actual addresses, not string contents.
    code=code.replace('EXPECT_EQ(sref.data(), str)','EXPECT_EQ(sref.data(), str.as_ptr())')
    # Equality between views and C-array destination has C-string semantics.
    code=code.replace('EXPECT_EQ(sref, dst)','EXPECT_EQ(sref, m::StringRef::from_cstr(&dst))')
    for name,macro in [('EQ','eq'),('TRUE','yes'),('FALSE','no')]:
        code=rewrite_calls(code,'EXPECT_'+name+'(',lambda a,macro=macro:macro+'!(r, '+a+')')
    if 'view, m::StringRef' in code:code=code.replace('eq!(r, view, m::StringRef','eq!(r, m::StringRef::from_bytes(view), m::StringRef')
    if re.search(r'\bEXPECT_|\bstd::|\bStringRef\s+|\bStringRefNull\s+|BLI_STATIC_ASSERT|@L',code):raise ValueError('Untranslated C++: '+identity+'\n'+code)
    return code

HEAD='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Generated from the complete pinned BLI_string_ref_test.cc. Do not edit generated tests.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::string_refs as m;
#[derive(Debug,Default)]
pub struct Report { pub assertions:u32, pub failures:Vec<String> }
impl Report {
    fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}
    pub fn passed(&self)->bool{self.assertions>0 && self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let (a,b)=(&$a,&$b);$r.check(a==b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$v:expr)=>{{$r.check($v,stringify!($v),line!());}};}
macro_rules! no {($r:expr,$v:expr)=>{{$r.check(!$v,stringify!(!$v),line!());}};}
'''

def generate(root=ROOT,upstream=None):
    upstream=upstream or root/'.upstream/blender';path='source/blender/blenlib/tests/'+NAME
    assert json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']==PIN
    raw=(upstream/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_HASH:raise ValueError('Unreviewed upstream source change')
    output=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
    for identity,body,line in extract(raw.decode()):
        translated=translate(identity,body);fn=identity.replace('.','__');sites=len(re.findall(r'\bEXPECT_(?:EQ|TRUE|FALSE)\s*\(',body))
        if sites!=len(re.findall(r'\b(?:eq|yes|no)!',translated)):raise ValueError('Assertion sites changed: '+identity)
        output+=f'\n// {path}:{line}\npub fn {fn}()->Report {{\nlet mut r=Report::default();\n{translated}\nr\n}}\n'
        native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::string_ref_cases::{fn}();assert_eq!(r.assertions,{sites});assert!(r.passed(),"{{r:?}}");}}\n'
        cases.append(dict(id=identity,path=path,line=line,source_sha256=SOURCE_HASH,body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=sites,expected_runtime_assertions=sites,embedded_compile_time_assertions=body.count('BLI_STATIC_ASSERT'),port_status='translated',execution='not_run'))
    output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    (root/'crates/blended-core/src/string_ref_cases.rs').write_text(output)
    (root/'crates/blended-core/tests/upstream_string_refs.rs').write_text(native)
    (root/'tests/upstream/blender'/NAME).write_bytes(raw)
    (root/'compatibility/string-ref-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,complete_blender_test_port=False,cases=cases,adapters=['C string literals retain NUL-terminated backing; borrowed views keep the original storage address.','String values and trimming use UTF-8 bytes, not Unicode scalar indices.','Both constexpr cases retain const evaluation and the source assertions.','std::string/ostream/view syntax uses owned byte buffers, memory Write and borrowed byte slices.']),indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases),assertions=sum(c['assertion_count'] for c in cases))))
if __name__=='__main__':generate()
