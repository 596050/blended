#!/usr/bin/env python3
"""All cases of the pinned UTF-8 test file. Finite reviewed adapter, not a transpiler.

Preserves legacy five/six-byte behaviour, original stress corpus, 256 byte values,
12 buffer sizes, random-byte draws, padded comparisons and every cursor input.
The original corpus carries Markus Kuhn's CC BY 4.0 attribution; retain snapshot.
"""
from pathlib import Path
import hashlib,json,re
from port_string_ops_tests import c_bytes,lit,extract_cases,calls,split_args,strip_comments
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
PATH='source/blender/blenlib/tests/BLI_string_utf8_test.cc'
HASH='0821a446fa0de157022ec8d27ffbd5b50ae50d6f9889bb67a9cf7ac0d269b572'
HEAD=r'''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Stress fixture derived by upstream from Markus Kuhn, 2015-08-28, CC BY 4.0.
// See tests/upstream/blender/BLI_string_utf8_test.cc for full source/attribution.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::utf8_compat as u;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,l:u32){self.assertions+=1;if !p{self.failures.push(format!("line {l}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(c_string($a)==c_string($b),stringify!($a C-string-equals $b),line!());}};}
fn c_string(a:&[u8])->&[u8]{&a[..a.iter().position(|&v|v==0).unwrap_or(a.len())]}
fn copy_call(dst:&mut[u8],src:&[u8],cap:usize,formatting:bool)->usize{
 if formatting{u::printf_s(dst,src,cap,true)}else{u::copy_into(dst,src,cap)}
}
// Each helper preserves the original macro's statement/loop/assertion order.
fn basic_copy(r:&mut Report,src:&[u8],formatting:bool){
 let mut dst=vec![255_u8;src.len()];copy_call(&mut dst,src,src.len(),formatting);
 eq!(r,c_string(&dst).len(),dst.len()-1);streq!(r,&dst,src);
}
fn truncate_encoding(r:&mut Report,size:i32,src:&[u8]){
 eq!(r,u::size_or_error(src[0]),size);
 let mut dst=vec![255_u8;src.len()];u::copy_into(&mut dst,src,src.len());
 eq!(r,c_string(&dst).len(),dst.len()-1);streq!(r,&dst,src);
 let cap=dst.len()-1;u::copy_into(&mut dst,src,cap);streq!(r,&dst,b"");
}
fn terminate_early(r:&mut Report,size:i32,src:&[u8],formatting:bool){
 let mut src=src.to_vec();eq!(r,u::size_or_error(src[0]),size);
 let mut dst=vec![255_u8;src.len()];copy_call(&mut dst,&src,src.len(),formatting);
 eq!(r,c_string(&dst).len(),dst.len()-1);streq!(r,&dst,&src);
 for i in (2..dst.len()).rev(){src[i]=0;dst.fill(255);let cap=dst.len();
  let n=copy_call(&mut dst,&src,cap,formatting);
  streq!(r,&dst,&src);eq!(r,c_string(&dst).len(),i);eq!(r,n,i);
 }
}
fn trunc_expect(r:&mut Report,src:&[u8],expected:&[u8],cap:usize,formatting:bool){
 let mut dst=vec![0_u8;cap+1];dst[cap]=255;
 let n=copy_call(&mut dst,src,cap,formatting);
 eq!(r,n,c_string(&dst).len());streq!(r,&dst,expected);eq!(r,dst[cap],255_u8);
}
// Do not append a NUL to unpadded input: boundary handling is what is tested.
fn as_char32(src:&[u8],limit:usize,dst:&mut[u32])->usize{
 let mut i=0;let mut n=0;
 while i<limit&&src[i]!=0{dst[n]=u::decode_step_safe(src,limit,&mut i);n+=1;}i
}
fn compare_pad(r:&mut Report,src:&[u8],padded_size:usize){
 let size=src.len();let mut padded=vec![0_u8;padded_size];padded[..size].copy_from_slice(src);
 let mut a=vec![u32::MAX;size];let mut b=vec![u32::MAX;size];let ia=as_char32(src,size,&mut a);
 for pass in 0..2{b.fill(u32::MAX);let ib=as_char32(&padded,if pass==1{size}else{padded_size},&mut b);
  for i in 0..size{eq!(r,a[i],b[i]);}eq!(r,ia,ib);
 }
}
fn compare_padding(r:&mut Report,src:&[u8]){compare_pad(r,src,src.len()+1);compare_pad(r,src,src.len()+7);}
fn at_buffer_size(r:&mut Report,size:usize){
 let mut src=vec![0_u8;size];
 for i in 0..=255_i32{src.fill(i as u8);compare_padding(r,&src);
  if size>1{let mut mul=1_i32;while mul<256{
   for ofs in 1..size{src[ofs]=(i+(ofs as i32*mul)) as u8;}compare_padding(r,&src);
   for ofs in 1..size{src[ofs]=(i-(ofs as i32*mul)) as u8;}compare_padding(r,&src);mul*=2;
  }}
 }
 let mut rng=u::LegacyByteRng::new(1);
 for _ in 0..256{rng.fill(&mut src);compare_padding(r,&src);}
}
'''

def no_directives(s):
    # C preprocessor continuation lines are one directive, not invocations.
    return re.sub(r'^\s*#(?:[^\n\\]|\\[^\n]|\\\n)*[^\n]*\n?', '',s,flags=re.M)

def definitions(text):
    return {m[1]:m[2] for m in re.finditer(r'^#define (STR_MB_ALPHA_\d) ("[^\n]+")$',text,re.M)}

def expand_literals(expr,defs):
    for key,value in defs.items():expr=expr.replace(key,value)
    return expr

def array_bytes(args,nul=False):
    values=[]
    for a in args:
        if a.startswith("'") and a.endswith("'"):
            data=c_bytes('"'+a[1:-1].replace('"','\\"')+'"');assert len(data)==1;values.append(data[0])
        else:values.append(int(a,0))
    if nul:values.append(0)
    if any(not 0<=v<=255 for v in values):raise ValueError('Invalid byte fixture')
    return '&['+','.join(str(v)+'_u8' for v in values)+']',len(values)

def fixture(text):
    clean=strip_comments(text)
    start=clean.index('utf8_invalid_tests[][3] = {')+len('utf8_invalid_tests[][3] = {')
    end=clean.index('\n};',start);entries=[]
    for entry in split_args(clean[start:end]):
        if not entry.strip():continue
        if not(entry.startswith('{') and entry.endswith('}')):raise ValueError('Invalid fixture row')
        parts=split_args(entry[1:-1])
        if parts==['nullptr']*3:continue
        if len(parts)!=3:raise ValueError('Wrong fixture arity')
        raw=[c_bytes(v)+b'\0' for v in parts]
        if len(raw[0])!=80:raise ValueError('Lost original fixed buffer length')
        entries.append((parts,raw))
    return entries

def cursor(body):
    s=body
    def declare(m):
        typ,name,expr=m.groups()
        if typ=='char32_t':
            # Only the original U string's ASCII and explicit four-hex \u escapes.
            raw=expr[2:-1];vals=[];i=0
            while i<len(raw):
                if raw[i]=='\\':
                    if raw[i:i+2]!='\\u':raise ValueError('Unexpected UTF32 literal')
                    vals.append(int(raw[i+2:i+6],16));i+=6
                else:vals.append(ord(raw[i]));i+=1
            vals.append(0);out='&['+','.join(str(v)+'_u32' for v in vals)+']'
        else:out=lit(expr,True)
        return f'let {name}={out};'
    s=re.sub(r'const (char32_t|char) (\w+)\[\] = (U?"(?:\\.|[^"\\])*");',declare,s)
    s=re.sub(r'const size_t (\w+) = (\d+);',r'let \1:usize=\2;',s)
    s=re.sub(r'\bint pos = (\d+);',r'let mut pos:i32=\1;',s)
    s=s.replace('&pos','&mut pos')
    for mode in ('next','prev'):
        for enc in ('8','32'):s=s.replace('BLI_str_cursor_step_'+mode+'_utf'+enc,'u::cursor_'+mode+enc)
    s=re.sub(r'(u::cursor_\w+\([^;]+?\)) \? pos : -1',r'if \1{pos}else{-1}',s)
    for old,new in [('EXPECT_EQ','eq'),('EXPECT_TRUE','yes'),('EXPECT_FALSE','no')]:s=s.replace(old+'(',new+'!(r,')
    count=len(re.findall(r'\b(?:eq|yes|no)!\(',s))
    if re.search(r'BLI_|\bconst |char32_t|EXPECT_',s):raise ValueError('Untranslated cursor body')
    return s,count

def translate(identity,body,defs,rows):
    name=identity.split('.')[1];plain=no_directives(body);out='';count=0
    if name.startswith('StrCursor'):return cursor(plain)
    if name=='Utf8InvalidBytesStrip':return '''for &(src,expected,errors) in INVALID_FIXTURES{
 let mut buff=[0_u8;80];buff.copy_from_slice(src);let found=u::invalid_strip(&mut buff,79);
 eq!(r,found,errors);streq!(r,&buff,expected);
}''',2*len(rows)
    if name=='Utf8InvalidBytesSubstitute':return '''for &(src,_,errors) in INVALID_FIXTURES{
 let mut buff=[0_u8;80];buff.copy_from_slice(src);let found=u::invalid_substitute(&mut buff,79,b'?');
 eq!(r,found,errors);eq!(r,u::invalid_byte(&buff,79),-1);eq!(r,c_string(&buff).len(),79_usize);
}''',3*len(rows)
    if name=='Utf8InvalidBytesSubstitutePatterns':
        for args in calls(plain,'TEST_SIMPLE('):
            assert len(args)==3 and args[0].startswith('ARRAY_ARG({') and args[0].endswith('})')
            src,_=array_bytes(split_args(args[0][11:-2]))
            out+='{let mut buff='+src[1:]+';let n=c_string(&buff).len();eq!(r,u::invalid_substitute(&mut buff,n,b\'?\'),'+args[1]+');streq!(r,&buff,'+lit(args[2])+');}\n';count+=2
        return out,count
    if name=='StringNLenUTF8':
        for args in calls(plain,'EXPECT_EQ('):
            a=calls(args[0],'BLI_strnlen_utf8(')[0]
            out+=f'eq!(r,u::count_bytes({lit(expand_literals(a[0],defs),True)},{a[1]}).0,{args[1]}_usize);\n';count+=1
        return out,count
    if name=='StringNLenUTF8_Incomplete':
        expr=re.search(r'const char \*ref_str =\s*(.*?);',body,re.S)[1]
        out+='let source='+lit(expand_literals(expr,defs),True)+';let mut buf=[0_u8;22];\n'
        for offset,n in calls(plain,'EXPECT_BYTE_OFFSET('):
            out+='{buf.copy_from_slice(source);buf['+offset+']=0;let (n,ofs)=u::count_bytes(&buf,21);eq!(r,n,'+n+'_usize);eq!(r,ofs,'+offset+'_usize);}\n';count+=2
        return out,count
    formatting=name.startswith('StrPrintf')
    if name in ('StrCopyUTF8_ASCII','StrPrintfUTF8_ASCII'):
        token='SNPRINTF_UTF8_ASCII(' if formatting else 'STRNCPY_UTF8_ASCII('
        for args in calls(plain,token):
            src,_=array_bytes(args,True);out+=f'basic_copy(&mut r,{src},{str(formatting).lower()});\n';count+=2
        return out,count
    if name=='StrCopyUTF8_ASCII_Truncate':
        for args in calls(plain,'STRNCPY_UTF8_ASCII_TRUNCATE('):
            cap=args[0];src,size=array_bytes(args[1:])
            out+='{let mut src='+src[1:]+f';let mut dst=[255_u8;{size}];u::copy_into(&mut dst,&src,{cap});let expected=core::cmp::min(src.len(),{cap})-1;src[expected]=0;eq!(r,c_string(&dst).len(),expected);streq!(r,&dst,&src);}}\n';count+=2
        return out,count
    if name=='StrCopyUTF8_TruncateEncoding':
        for args in calls(plain,'STRNCPY_UTF8_TRUNCATE('):
            src,_=array_bytes(args[1:],True);out+=f'truncate_encoding(&mut r,{args[0]},{src});\n';count+=4
        return out,count
    if name in ('StrCopyUTF8_TerminateEncodingEarly','StrPrintfUTF8_TerminateEncodingEarly'):
        token='SNPRINTF_UTF8_TERMINATE_EARLY(' if formatting else 'STRNCPY_UTF8_TERMINATE_EARLY('
        for args in calls(plain,token):
            src,size=array_bytes(args[1:],True);out+=f'terminate_early(&mut r,{args[0]},{src},{str(formatting).lower()});\n';count+=3+3*max(size-2,0)
        return out,count
    if name in ('StrCopyUTF8_TruncateEncodingMulti','StrPrintfUTF8_TruncateEncodingMulti'):
        token='SNPRINTF_UTF8_TRUNC_EXPECT(' if formatting else 'STRNCPY_UTF8_TRUNC_EXPECT('
        for a,b,n in calls(plain,token):
            out+=f'trunc_expect(&mut r,{lit(expand_literals(a,defs),True)},{lit(expand_literals(b,defs))},{n},{str(formatting).lower()});\n';count+=3
        return out,count
    if name=='Utf8OffsetFromIndex_ClampedIndex':
        expr=re.search(r'test_strings\[\] = \{(.*?)\};',body,re.S)[1]
        vals=[v for v in split_args(expr) if v]
        out+='for text in ['+','.join(lit(expand_literals(v,defs),True)+'.as_slice()' for v in vals)+']{\nlet len=c_string(text).len();let n=u::count_bytes(text,len).0;let ofs=u::offset_from_index(text,len,n);\neq!(r,u::offset_from_index(text,len,n+1),ofs);eq!(r,u::offset_from_index(text,len,n+10),ofs);}\n'
        return out,2*len(vals)
    if name=='Utf8AsUnicodeStep':
        sizes=[int(x) for x in re.findall(r'utf8_as_char32_test_at_buffer_size<(\d+)>\(\);',plain)]
        if sizes!=list(range(1,13)):raise ValueError('Original size universe changed')
        for n in sizes:out+=f'at_buffer_size(&mut r,{n});\n';count+=(512 if n==1 else 4608)*4*(n+1)
        return out,count
    raise ValueError('Unknown original test '+identity)

def generate(root=ROOT):
    if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong pin')
    raw=(root/'.upstream/blender'/PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=HASH:raise ValueError('Original changed')
    text=raw.decode();defs=definitions(text);rows=fixture(text);out=HEAD
    out+='\nconst INVALID_FIXTURES:&[(&[u8],&[u8],i32)]=&[\n'+''.join('('+lit(a[0],True)+','+lit(a[1],True)+','+str(b[2][0])+'),\n' for a,b in rows)+'];\n'
    cases=[];native='// SPDX-License-Identifier: Apache-2.0\n'
    for identity,body,line,kind in extract_cases(text):
        code,count=translate(identity,body,defs,rows)
        if count==0:raise ValueError('No assertions in '+identity)
        fn=identity.replace('.','__')
        out+=f'\n// {PATH}:{line}\npub fn {fn}()->Report{{let mut r=Report::default();\n{code}\nr\n}}\n'
        native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::utf8_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
        cases.append(dict(id=identity,path=PATH,line=line,test_kind=kind,source_sha256=HASH,source_body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=len(re.findall(r"\bEXPECT_\w+\(",body)),expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
    if len(cases)!=39:raise ValueError('Original universe changed')
    out+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    (root/'crates/blended-core/src/utf8_cases.rs').write_text(out)
    (root/'crates/blended-core/tests/upstream_utf8.rs').write_text(native)
    (root/'tests/upstream/blender/BLI_string_utf8_test.cc').write_bytes(raw)
    (root/'compatibility/utf8-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files={'BLI_string_utf8_test.cc':HASH},cases=cases,invalid_fixture_count=len(rows),stress_buffer_sizes=list(range(1,13)),stress_assertions=1626112,complete_blender_test_port=False,notes='Every original case and macro/helper loop retained. Legacy validation is not modern Unicode scalar validation. printf adapter covers the original %s call form, not a general varargs formatter. Random-byte getter retains original platform endianness; source reference is little endian.'),indent=2)+'\n')
    return cases
if __name__=='__main__':
    c=generate();print(len(c),sum(x['expected_runtime_assertions'] for x in c))
