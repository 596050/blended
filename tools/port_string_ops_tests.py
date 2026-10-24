#!/usr/bin/env python3
"""Complete source-locked string-operation, fuzzy-search and name-utility ports.

This is a finite reviewed adapter, not a general C++ transpiler. Fixtures and
assertion operands come from the pinned originals, never replacement outputs.
C escapes are decoded to bytes (not Unicode-escaped then UTF-8 encoded).
"""
from pathlib import Path
import hashlib,json,re
from port_string_ref_tests import strip_comments,code_mask,split_args,rewrite_calls
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={'BLI_string_test.cc': 'aa13f49f37424ccf376f1b91434dc7bc2a1dd0867408c29a89b5ebb718bac7d4', 'BLI_string_search_test.cc': 'cb9933e4e03afce0c64003e182ef2940e2ada6865dd990f1124a7aba7007f9d0', 'BLI_string_utils_test.cc': '0cf9854d8ef84186abe772ce890c09e6dbec14855e8029201a4ed23bcf3b52b4'}
STRINGS=re.compile(r'"(?:\\.|[^"\\])*"')

def c_bytes(expression):
    """Decode adjacent ordinary C literals and the one original arrow macro."""
    expression=expression.replace('UI_MENU_ARROW_SEP',r'"\xe2\x96\xb8"')
    tokens=list(STRINGS.finditer(expression))
    if not tokens or STRINGS.sub('',expression).strip():raise ValueError('Unsupported C literal '+expression)
    out=bytearray()
    for token in tokens:
        s=token[0][1:-1];i=0
        while i<len(s):
            ch=s[i];i+=1
            if ch!='\\':out.extend(ch.encode('utf-8'));continue
            ch=s[i];i+=1
            escapes={'a':7,'b':8,'f':12,'n':10,'r':13,'t':9,'v':11,'\\':92,'"':34,"'":39,'?':63}
            if ch in escapes:out.append(escapes[ch])
            elif ch in '01234567':
                start=i-1
                while i<len(s) and i-start<3 and s[i] in '01234567':i+=1
                out.append(int(s[start:i],8))
            elif ch=='x':
                start=i
                while i<len(s) and s[i] in '0123456789abcdefABCDEF':i+=1
                if i==start:raise ValueError('Empty hex escape')
                out.append(int(s[start:i],16))
            else:raise ValueError('Unsupported C escape '+ch)
    return bytes(out)

def lit(expression,nul=False):
    data=c_bytes(expression)+(b'\0' if nul else b'')
    return 'b"'+''.join(chr(b) if 32<=b<127 and b not in (34,92) else '\\x%02x'%b for b in data)+'"'

def extract_cases(text):
    clean=strip_comments(text);mask=code_mask(clean)
    for m in re.finditer(r'\b(TEST(?:_F)?)\(\s*(\w+),\s*(\w+)\)\s*\{',mask):
        i=m.end();start=i;depth=1
        while depth:
            if mask[i]=='{':depth+=1
            elif mask[i]=='}':depth-=1
            i+=1
        yield m[2]+'.'+m[3],clean[start:i-1],text.count('\n',0,m.start())+1,m[1]

def calls(s,token):
    result=[]
    rewrite_calls(s,token,lambda a:result.append(split_args(a)) or 'CAPTURED')
    return result

def pair_lists(body):
    result={}
    for m in re.finditer(r'(?:const )?CompareWordsArray\s+(\w+)\s*\{',body):
        start=m.end();mask=code_mask(body);i=start;depth=1
        while depth:
            if mask[i]=='{':depth+=1
            elif mask[i]=='}':depth-=1
            i+=1
        pairs=[]
        for entry in split_args(body[start:i-1]):
            if not entry:continue
            if not(entry.startswith('{') and entry.endswith('}')):raise ValueError('Expected pair')
            args=split_args(entry[1:-1]);assert len(args)==2
            pairs.append(args)
        result[m[1]]=pairs
    return result

HEAD=r'''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked test adapters; see compatibility/string-ops-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::string_ops as s;
use crate::string_search as search;
use crate::string_refs::Bytes;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{let a:*const u8=$a;let b:*const u8=$b;$r.check(a==b,stringify!($a pointer-equals $b),line!());}};}
macro_rules! le {($r:expr,$a:expr,$b:expr)=>{{$r.check($a<=$b,stringify!($a <= $b),line!());}};}
macro_rules! lt {($r:expr,$a:expr,$b:expr)=>{{$r.check($a<$b,stringify!($a < $b),line!());}};}
macro_rules! gt {($r:expr,$a:expr,$b:expr)=>{{$r.check($a>$b,stringify!($a > $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(c_string($a)==c_string($b),stringify!($a C-string-equals $b),line!());}};}
fn c_string(a:&[u8])->&[u8]{&a[..a.iter().position(|&v|v==0).unwrap_or(a.len())]}
// Preserve EXPECT_EQ_VECTOR's length assertion and conditional element checks.
fn words_test(r:&mut Report,text:&[u8],max_length:usize,expected:&[[i32;2]],max_words:Option<usize>){
 if let Some(n)=max_words{assert!(n<=expected.len()-1,"Original CHECK_LE fixture condition");}
 let effective=max_words.unwrap_or(expected.len());
 let mut actual=vec![[-1_i32,-1_i32];effective+1];
 let n=s::find_split_words(text,max_length,b' ',&mut actual,effective);
 le!(r,n,actual.len()-1);
 actual.resize(n+1,[-1,-1]);
 eq!(r,actual.len(),expected.len());
 if actual.len()==expected.len(){for i in 0..actual.len(){eq!(r,actual[i],expected[i]);}}
}
fn natural_test(r:&mut Report,pairs:&[(&[u8],&[u8])],kind:i32){
 for &(a,b) in pairs{let result=s::casecmp_natural(a,b);match kind{0=>eq!(r,result,0),-1=>lt!(r,result,0),1=>gt!(r,result,0),_=>unreachable!()}}
}
fn escape_test(r:&mut Report,pairs:&[(&[u8],&[u8])]){
 let mut dst=[0_u8;64];
 for &(a,b) in pairs{
  lt!(r,c_string(a).len()*2+1,dst.len());
  let n=s::escape_into(&mut dst,a,64);
  streq!(r,&dst,b);eq!(r,n,c_string(&dst).len());
  let n=s::unescape_into(&mut dst,b,c_string(b).len());
  streq!(r,&dst,a);eq!(r,n,c_string(&dst).len());
 }
}
fn join_test(r:&mut Report,parts:&[&[u8]],n:usize,buffer:&mut[u8;128],sep:Option<u8>){
 let len=s::join_into(buffer,128,&parts[..n],sep);
 let alloc=s::join_owned(&parts[..n],sep);
 streq!(r,&alloc,buffer);
 for size in (1..=len+1).rev(){let mut dst=[0_u8;128];let actual=s::join_into(&mut dst,size,&parts[..n],sep);eq!(r,actual+1,size);eq!(r,s::strncmp(&dst,buffer,actual),0);}
}
'''

def format_case(body):
    m=re.search(r'char (\w+)\[(BLI_STR_FORMAT_\w+)\];',body);assert m
    name,size=m.groups();size={'BLI_STR_FORMAT_INT32_GROUPED_SIZE':15,'BLI_STR_FORMAT_UINT64_GROUPED_SIZE':27,'BLI_STR_FORMAT_INT64_BYTE_UNIT_SIZE':15,'BLI_STR_FORMAT_INT32_DECIMAL_UNIT_SIZE':7,'BLI_STR_FORMAT_INT32_INTEGER_UNIT_SIZE':5}[size]
    out=f'let mut {name}=[0_u8;{size}];\n';count=0
    token=re.compile(r'BLI_str_format_(\w+)\(([^;]+)\);\s*EXPECT_STREQ\(((?:"(?:\\.|[^"\\])*")\s*),\s*'+name+r'\);')
    for m in token.finditer(body):
        fn,args,expected=m.groups();args=split_args(args);assert args[0]==name
        value=re.sub(r'^\w+\s*=\s*','',args[1]).replace('INT32_MAX','i32::MAX').replace('INT32_MIN','i32::MIN')
        value=re.sub(r'(\d+)u\b',r'\1_u64',value)
        fn={'int_grouped':'format_i32','uint64_grouped':'format_u64','byte_unit':'format_bytes','decimal_unit':'format_decimal','integer_unit':'format_integer'}[fn]
        out+=f's::{fn}(&mut {name}, {value}'+(', '+args[2] if len(args)>2 else '')+');\n'
        out+=f'streq!(r,{lit(expected)},&{name});\n';count+=1
    if 'EXPECT_EQ' in body:out+=f'eq!(r,{name}.len(),c_string(&{name}).len()+1);\n';count+=1
    if count!=len(re.findall(r'EXPECT_(?:STREQ|EQ)\(',body)):raise ValueError('Untranslated formatting assertion')
    return out,count

def partition_case(identity,body):
    utf8='Utf8' in identity;right='StrRPartition' in identity or 'Ex' in identity
    delim='[45_u32,46,95,241,9775,0]' if utf8 else '[45_u32,46,95,126,92,0]'
    out='';count=0
    # Each original block has exactly one input, one operation and three checks.
    pattern=re.compile(r'const char \*str = ("(?:\\.|[^"\\])*");(.*?)(?=\n\s*\})',re.S)
    for match in pattern.finditer(body):
        literal,block=match.groups();m=re.search(r'pre_len = BLI_str_\w+\((.*?)\);',block,re.S);assert m
        args=split_args(m[1]);limit='Some('+re.search(r'str \+ (\d+)',args[1])[1]+')' if 'Ex' in identity else 'None'
        out+='\n{let text='+lit(literal,True)+';\nlet part=s::partition(text,'+limit+',&'+delim+','+str(utf8).lower()+','+str(right).lower()+');\n'
        expected_len=calls(block,'EXPECT_EQ(')[0];assert expected_len[0]=='pre_len'
        out+=f'eq!(r,part.prefix_len,{expected_len[1]}_usize);\n'
        if 'EXPECT_STREQ' in block:
            a=calls(block,'EXPECT_EQ(')[1];offset=re.fullmatch(r'&str\[(\d+)\]',a[0]);assert offset and a[1]=='sep'
            out+=f'peq!(r,text.as_ptr().wrapping_add({offset[1]}),part.separator_ptr());\n'
            expected=calls(block,'EXPECT_STREQ(')[0];assert expected[1]=='suf'
            out+=f'streq!(r,{lit(expected[0])},part.suffix_bytes().expect("Original non-null suffix"));\n'
        else:
            out+='peq!(r,part.separator_ptr(),core::ptr::null());\npeq!(r,part.suffix_ptr(),core::ptr::null());\n'
        out+='}\n';count+=3
    if count!=len(re.findall(r'EXPECT_(?:EQ|STREQ)\(',body)):raise ValueError('Partition assertion coverage mismatch')
    return out,count

def word_case(body):
    out='';count=0
    if 'const string words' in body:out+='let words=b"too many chars";let words_len=words.len();\n'
    for args in calls(body,'testStringFindSplitWords('):
        text=lit(args[0]) if args[0].startswith('"') else args[0]
        if len(args)==2:maxlen=f'{text}.len()';pairs=args[1];maxwords='None'
        else:maxlen=args[1];pairs=args[2];maxwords='Some('+args[3]+')' if len(args)==4 else 'None'
        nums=re.findall(r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*\}',pairs)
        if not nums:raise ValueError('Missing sentinel/word pairs')
        expected='&['+','.join('['+a+','+b+']' for a,b in nums)+']'
        out+=f'words_test(&mut r,{text},{maxlen},{expected},{maxwords});\n';count+=2+len(nums)
    return out,count

def natural_or_escape(identity,body):
    groups=pair_lists(body);out='';count=0
    for name,pairs in groups.items():out+='let '+name+':&[(&[u8],&[u8])]=&['+','.join('('+lit(a)+','+lit(b)+')' for a,b in pairs)+'];\n'
    if identity.startswith('StringCasecmpNatural.'):
        assert 'positive = copyWithSwappedWords(negative)' in body
        out+='let positive:Vec<(&[u8],&[u8])>=negative.iter().map(|&(a,b)|(b,a)).collect();\n'
        for name,kind in [('equal',0),('negative',-1),('positive',1)]:
            out+=f'natural_test(&mut r,&{name},{kind});\n';count+=len(groups['negative' if name=='positive' else name])
    else:
        for args in calls(body,'testEscapeWords('):
            assert len(args)==1 and args[0] in groups
            out+=f'escape_test(&mut r,{args[0]});\n';count+=5*len(groups[args[0]])
    return out,count

def scalar_expr(s):
    s=s.strip().replace('UI_MENU_ARROW_SEP',r'"\xe2\x96\xb8"')
    # Literal bytes may be adjacent or contain C-only escapes.
    strings=list(STRINGS.finditer(s))
    for m in reversed(strings):s=s[:m.start()]+lit(m[0])+s[m.end():]
    s=re.sub(r"'([^'\\])'",r"b'\1'",s)
    functions={'BLI_strnlen':'s::nlen','BLI_string_elem_split_by_delim':'s::element_in_delimited','BLI_string_max_possible_word_count':'s::max_possible_words','BLI_string_is_decimal':'s::is_decimal','BLI_str_startswith':'s::starts_with','BLI_str_endswith':'s::ends_with','damerau_levenshtein_distance':'search::damerau_levenshtein_distance','get_fuzzy_match_errors':'search::fuzzy_errors'}
    # C adjacent strings are merged after converting each original input expression.
    for a,b in functions.items():s=s.replace(a+'(',b+'(')
    if re.search(r'b"(?:\\.|[^"\\])*"\s*b"',s):
        # Only the arrow-adjacent input occurs in the source scalar tests.
        s=re.sub(r'(?:b"(?:\\.|[^"\\])*"\s*){2,}',lambda m:'b"'+''.join(STRINGS.findall(m[0])).replace('""','')[1:-1]+'"',s)
    return s

def simple_case(body):
    out='';count=0
    for m in re.finditer(r'EXPECT_(EQ|TRUE|FALSE)\(',code_mask(body)):
        start=m.end();mask=code_mask(body);i=start;depth=1
        while depth:
            if mask[i]=='(':depth+=1
            elif mask[i]==')':depth-=1
            i+=1
        args=split_args(body[start:i-1]);args=[scalar_expr(a) for a in args]
        out+={'EQ':'eq','TRUE':'yes','FALSE':'no'}[m[1]]+'!(r,'+', '.join(args)+');\n';count+=1
    return out,count

def main_case(identity,body):
    name=identity.split('.')[1]
    if name=='StrCat':
        # Ignore the definition, preserving its body in HEAD through explicit expansion.
        body=body[body.index('\n\n'):];out='';count=0
        for a in calls(body,'STR_N_CAT('):
            assert len(a)==4;initial,size,src,expected=a
            out+=f'{{let mut dst=s::buffer({lit(initial)},{size}+1);dst[{size}]=0xff;s::ncat(&mut dst,{lit(src)},{size});streq!(r,&dst,{lit(expected)});eq!(r,dst[{size}],0xff_u8);}}\n';count+=2
        return out,count
    if name=='StrReplaceRange':
        body=body[body.index('\n\n'):];out='';count=0
        for a in calls(body,'STR_REPLACE_RANGE('):
            initial,size,beg,end,repl,expected=a
            out+=f'{{let mut text=s::buffer({lit(initial)},{size});s::replace_range(&mut text,{beg},{end},{lit(repl)});streq!(r,&text,{lit(expected)});}}\n';count+=1
        return out,count
    if 'Partition' in name:return partition_case(identity,body)
    if name.startswith('StrFormat'):return format_case(body)
    if identity.startswith('StringFindSplitWords.'):return word_case(body)
    if identity.startswith(('StringCasecmpNatural.','StringEscape.')):return natural_or_escape(identity,body)
    if name=='StrJoin_Truncate':
        out='let mut buffer=[0_u8;128];\n';count=0
        for m in re.finditer(r'const char \*strings\[\] = \{(.*?)\};(.*?)(?=\n\s*\})',body,re.S):
            parts=split_args(m[1]);out+='{let parts:&[&[u8]]=&['+','.join(lit(x) for x in parts)+'];\n'
            for fn,sep in [('string_join_array_test_truncate','None'),('string_join_array_with_sep_char_test_truncate',"Some(b'|')")]:
                args=calls(m[2],fn+'(')[0];n=len(parts) if args[1]=='ARRAY_SIZE(strings)' else int(args[1]);assert args[0]=='strings' and args[2]=='buffer'
                length=sum(len(c_bytes(x).split(b'\0')[0]) for x in parts[:n])+(max(n-1,0) if sep!='None' else 0)
                out+=f'join_test(&mut r,parts,{n},&mut buffer,{sep});\n';count+=1+2*(length+1)
                occurrence=0 if sep=='None' else 1
                expect=calls(m[2],'EXPECT_STREQ(')[occurrence];assert expect[0]=='buffer'
                out+=f'streq!(r,&buffer,{lit(expect[1])});\n';count+=1
            out+='}\n'
        return out,count
    if name=='StringStrncasestr':
        out='let text=b"search here\\0";\n';count=0
        matches=re.findall(r'res = BLI_strncasestr\((.*?)\);\s*EXPECT_EQ\((.*?)\);',body,re.S)
        for raw,comparison in matches:
            a=split_args(raw);expected=split_args(comparison)[1];assert a[0]=='str_test0'
            pointer='core::ptr::null()' if 'nullptr' in expected else 'text.as_ptr().wrapping_add('+ (expected.split('+')[1].strip() if '+' in expected else '0') +')'
            out+=f'{{let res=s::ncasestr(text,{lit(a[1])},{a[2]});peq!(r,res,{pointer});}}\n';count+=1
        return out,count
    if name=='bounded_strcpy':
        out='';count=0
        pairs=re.findall(r'STRNCPY\(str,\s*("(?:\\.|[^"\\])*")\);\s*EXPECT_STREQ\(str,\s*("(?:\\.|[^"\\])*")\);',body)
        for inp,expected in pairs:out+=f'{{let mut text=[0_u8;8];s::copy_into(&mut text,{lit(inp)},8);streq!(r,&text,{lit(expected)});}}\n';count+=1
        return out,count
    return simple_case(body)

def search_case(identity,body):
    if identity.endswith('extract_normalized_words'):
        a=calls(body,'extract_normalized_words(')[0];out='let (words,ids)=search::normalized_words('+lit(a[0])+');\n';count=0
        for left,right in calls(body,'EXPECT_EQ('):
            if left=='words.size()':out+=f'eq!(r,words.len(),{right}_usize);\n'
            elif left.startswith('word_group_ids'):out+=f'eq!(r,{left.replace("word_group_ids","ids")},{right}_i32);\n'
            else:out+=f'eq!(r,Bytes::from_slice(&{left}),Bytes::from_slice({lit(right)}));\n'
            count+=1
        return out,count
    # Parse complete assertion operands, joining adjacent C string tokens first.
    out='';count=0
    for a,b in calls(body,'EXPECT_EQ('):
        def exp(v):
            for name,target in [('damerau_levenshtein_distance','damerau_levenshtein_distance'),('get_fuzzy_match_errors','fuzzy_errors')]:
                if v.startswith(name+'('):return 'search::'+target+'('+','.join(lit(x) for x in split_args(v[len(name)+1:-1]))+')'
            return v
        out+='eq!(r,'+exp(a)+','+exp(b)+');\n';count+=1
    return out,count

def utils_case(identity,body):
    if identity.endswith('BLI_string_replace'):
        out='';count=0
        for m in re.finditer(r'std::string s = ("(?:\\.|[^"\\])*");\s*BLI_string_replace\((.*?)\);\s*EXPECT_EQ\((.*?)\);',body,re.S):
            initial,op,ex=m.groups();args=split_args(op);expected=split_args(ex);assert args[0]=='s' and expected[0]=='s'
            out+=f'{{let mut text={lit(initial)}.to_vec();s::replace_all(&mut text,{lit(args[1])},{lit(args[2])});eq!(r,Bytes::from_slice(&text),Bytes::from_slice({lit(expected[1])}));}}\n';count+=1
        return out,count
    out='let names:&[&[u8]]=&[b"Foo",b"Bar",b"Bar.003",b"Baz.001",b"Big.999"];\nlet exists=|v:&[u8]|names.contains(&v);\n';count=0
    # Frozen original callback fixture, not a canned result for the function.
    for m in re.finditer(r'char name\[64\] = ("(?:\\.|[^"\\])*");\s*BLI_uniquename_cb\((.*?)\);\s*EXPECT_STREQ\((.*?)\);',body,re.S):
        initial,op,ex=m.groups();args=split_args(op);expected=split_args(ex)
        assert args[0]=='unique_check_func' and args[2]=="'.'" and args[3:] == ['name','sizeof(name)'] and expected[0]=='name'
        out+=f'{{let mut name=s::buffer({lit(initial)},64);s::unique_name_into(&exists,{lit(args[1])},b\'.\',&mut name);streq!(r,&name,{lit(expected[1])});}}\n';count+=1
    for left,right in calls(body,'EXPECT_EQ('):
        assert left.startswith('BLI_uniquename_cb(')
        args=split_args(left[len('BLI_uniquename_cb('):-1]);assert args[0]=='unique_check' and args[1]=="'.'"
        out+='eq!(r,Bytes::from_slice(&s::unique_name(&exists,b\'.\','+lit(args[2])+')),Bytes::from_slice('+lit(right)+'));\n';count+=1
    return out,count

def generate(root=ROOT):
    assert json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']==PIN
    output=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
    for filename,digest in FILES.items():
        path='source/blender/blenlib/tests/'+filename;raw=(root/'.upstream/blender'/path).read_bytes();text=raw.decode()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Unreviewed original source '+path)
        for identity,body,line,kind in extract_cases(text):
            translator=search_case if filename=='BLI_string_search_test.cc' else utils_case if filename=='BLI_string_utils_test.cc' else main_case
            code,count=translator(identity,body)
            if count<=0:raise ValueError('Missing executable assertions '+identity)
            fn=identity.replace('.','__');output+=f'\n// Original {path}:{line} ({kind})\npub fn {fn}()->Report{{let mut r=Report::default();\n{code}\nr\n}}\n'
            native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::string_ops_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
            cases.append(dict(id=identity,path=path,line=line,kind=kind,source_sha256=digest,body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=len(re.findall(r'EXPECT_\w+\(',code_mask(body))),expected_runtime_assertions=count,status='ported_unexecuted'))
        (root/'tests/upstream/blender'/filename).write_bytes(raw)
    if len(cases)!=48 or len({c['id'] for c in cases})!=48:raise ValueError('Case universe changed')
    output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
    (root/'crates/blended-core/src/string_ops_cases.rs').write_text(output)
    (root/'crates/blended-core/tests/upstream_string_ops.rs').write_text(native)
    (root/'compatibility/string-ops-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files=FILES,cases=cases,complete_blender_test_port=False,adapters=['All TEST and TEST_F bodies are mapped; helper assertion expansions and loops retained.','C literals preserve raw UTF-8, hexadecimal, octal, embedded NUL and control bytes.','Pointer assertions compare real returned addresses with original offset expressions. Diagnostic pointer values are normalized per equality pair for these cross-allocation cases; null remains a distinct value.','WordInfo start/end objects use [i32;2] values and preserve EXPECT_EQ_VECTOR length and element checks.','Locale-sensitive original routines are compared in C locale; no general locale compatibility claim.','Rust byte buffers replace C stack/heap storage; original buffer sizes and sentinels retained.']),indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases),assertions=sum(c['expected_runtime_assertions'] for c in cases))))
    return cases
if __name__=='__main__':generate()
