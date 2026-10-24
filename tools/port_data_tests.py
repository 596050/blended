#!/usr/bin/env python3
"""Reviewed ports of four complete pinned test files, not a general transpiler.

Array helper bodies are explicit language adapters. CSV assertion operands are
translated from original tokens. All original sources are hash locked; no target
expectations are obtained from the replacement implementation.
"""
from pathlib import Path
import hashlib,json,re
from port_string_ref_tests import extract,split_args,rewrite_calls,strip_comments,code_mask
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={
 'BLI_array_utils_test.cc':'06858c8551a0c0647efcc796fc156b3c9138782d093327b629e2437add49278a',
 'BLI_csv_parse_test.cc':'802ef8d0c4cbdb32529940f8ce5f3a1fd1b409ac013620dc55384db1ba5c1120',
 'BLI_hash_mm2a_test.cc':'2e357f9c998653c6de90eb51799bedd5f3de2d4c3247aeb53524b2f09acd08f4',
 'BLI_disjoint_set_test.cc':'09aec67cc7ba73aa5536beb0556c8a43a75047c3b059a50bc7c342b8eabafeba',
}
HEAD=r'''// SPDX-FileCopyrightText: 2023-2025 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Complete source-locked translations; see compatibility/data-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::array_ops as a;
use crate::csv_fields as csv;
use crate::hash_mm2a::Murmur2A;
use crate::disjoint_set::DisjointSet;
use crate::data_structures::IndexRange;
use std::collections::BTreeMap;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{pub fn check(&mut self,p:bool,e:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {e}"));}}pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check($a==$b,stringify!($a == $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(c_string($a)==c_string($b),stringify!($a C-string-equals $b),line!());}};}
fn c_string(s:&[u8])->&[u8]{&s[..s.iter().position(|&b|b==0).unwrap_or(s.len())]}
// EXPECT_EQ_ARRAY expands to exactly N element assertions, with no extra length assertion.
macro_rules! array_eq {($r:expr,$a:expr,$b:expr,$n:expr)=>{{let expected=&$a;let actual=&$b;for i in 0..$n{eq!($r,expected[i],actual[i]);}}};}
fn dedup_test(r:&mut Report,data:&mut [i32],expected:&[i32]){
 let original_len=data.len();let new_len=a::deduplicate_ordered(data,original_len);
 eq!(r,new_len,expected.len());array_eq!(r,data,expected,new_len);
 let test_len=a::deduplicate_ordered(data,new_len);
 eq!(r,test_len,expected.len());array_eq!(r,data,expected,new_len);
}
fn ranges_test(r:&mut Report,data:&[bool],expected:&[IndexRange]){
 let ranges=a::find_all_ranges(data,true);
 eq!(r,ranges.len(),expected.len());array_eq!(r,expected,ranges,expected.len());
}
fn max_test(r:&mut Report,values:a::VirtualInts<'_>,expected:Option<usize>){
 let result=a::max_element_index(&values);
 yes!(r,result.is_some()==expected.is_some());
 if let (Some(result),Some(expected))=(result,expected){eq!(r,result,expected);}
}
fn groups_test(r:&mut Report,ids:&[i32],mask:&[usize]){
 // Independent insertion-ordered VectorSet adapter: BTreeMap only finds the
 // stored insertion index; its sorted traversal is never used for expectations.
 let mut expected_ids=BTreeMap::new();let mut first=Vec::<i32>::new();let mut groups=Vec::<i32>::new();
 for &i in mask{
  if !expected_ids.contains_key(&ids[i]){let index=expected_ids.len() as i32;expected_ids.insert(ids[i],index);first.push(i as i32);}
  groups.push(expected_ids[&ids[i]]);
 }
 let mut group_indices=vec![0_i32;mask.len()];let mut first_indices=Vec::new();
 let count=a::group_ids_to_indices(ids,mask,&mut group_indices,Some(&mut first_indices));
 eq!(r,count,expected_ids.len());eq!(r,first_indices,first);
 let mut only=vec![0_i32;mask.len()];
 eq!(r,a::group_ids_to_indices(ids,mask,&mut only,None),count);
 eq!(r,only,groups);eq!(r,group_indices,groups);
}
#[derive(Default)]struct StrParseResult{success:bool,column_names:Vec<String>,records:Vec<Vec<String>>}
fn strings(fields:&[&[u8]])->Vec<String>{fields.iter().map(|f|String::from_utf8(f.to_vec()).expect("Original fixture is UTF-8")).collect()}
fn record_fields(s:&str)->Option<Vec<String>>{csv::parse_record_fields(s.as_bytes(),0,&csv::Options::default()).map(|(_,f)|strings(&f))}
fn csv_fields(s:&str,options:&csv::Options)->StrParseResult{
 let mut result=StrParseResult::default();
 let chunks=csv::parse_csv_in_chunks(s.as_bytes(),options,|header|{result.column_names=strings(header);},|records|{records.iter().map(|r|strings(r)).collect::<Vec<_>>()});
 if let Some(chunks)=chunks{result.success=true;for chunk in chunks{result.records.extend(chunk);}}
 result
}
'''
ARRAY={
'ReverseStringEmpty':('let mut data=*b"\\0";a::reverse_prefix(&mut data,0);streq!(r,b"",&data);',1),
'ReverseStringSingle':('let mut data=*b"0\\0";a::reverse_prefix(&mut data,1);streq!(r,b"0",&data);',1),
'ReverseString4':('let mut data=*b"0123\\0";a::reverse_prefix(&mut data,4);streq!(r,b"3210",&data);',1),
'ReverseInt4':('let expected=[3_i32,2,1,0];let mut data=[0_i32,1,2,3];a::reverse_prefix(&mut data,4);array_eq!(r,expected,data,4);',4),
'FindIndexStringEmpty':('let data=*b"\\0";let find=b\'0\';eq!(r,a::find_index(&data,0,&find),-1);eq!(r,a::rfind_index(&data,0,&find),-1);',2),
'FindIndexStringSingle':('let data=*b"0\\0";let find=b\'0\';eq!(r,a::find_index(&data,1,&find),0);eq!(r,a::rfind_index(&data,1,&find),0);',2),
'FindIndexStringSingleMissing':('let data=*b"1\\0";let find=b\'0\';eq!(r,a::find_index(&data,1,&find),-1);eq!(r,a::rfind_index(&data,1,&find),-1);',2),
'FindIndexString4':('let data=*b"0123\\0";let find=b\'3\';eq!(r,a::find_index(&data,4,&find),3);eq!(r,a::rfind_index(&data,4,&find),3);',2),
'FindIndexInt4':('let data=[0_i32,1,2,3];let find=3;eq!(r,a::find_index(&data,4,&find),3);eq!(r,a::rfind_index(&data,4,&find),3);',2),
'FindIndexInt4_DupeEnd':('let data=[0_i32,1,2,0];let find=0;eq!(r,a::find_index(&data,4,&find),0);eq!(r,a::rfind_index(&data,4,&find),3);',2),
'FindIndexInt4_DupeMid':('let data=[1_i32,0,0,3];let find=0;eq!(r,a::find_index(&data,4,&find),1);eq!(r,a::rfind_index(&data,4,&find),2);',2),
'FindIndexPointer':(r'''let mut data=[core::ptr::null::<u8>();4];let mut size=0_usize;
let a=b"a\0".as_ptr();let b=b"b\0".as_ptr();let c=b"c\0".as_ptr();let d=b"d\0".as_ptr();
macro_rules! both{($v:expr,$i:expr)=>{{data[size]=$v;size+=1;eq!(r,a::find_index(&data,size,&$v),$i);eq!(r,a::rfind_index(&data,size,&$v),$i);}};}
macro_rules! backward{($v:expr,$i:expr)=>{{data[size]=$v;size+=1;eq!(r,a::rfind_index(&data,size,&$v),$i);}};}
macro_rules! forward{($v:expr,$i:expr)=>{{data[size]=$v;size+=1;eq!(r,a::find_index(&data,size,&$v),$i);}};}
both!(a,0);both!(b,1);both!(c,2);both!(d,3);
size-=1;backward!(a,3);size-=1;forward!(a,0);size-=1;size-=1;backward!(b,2);backward!(a,3);''',12),
'BinaryAndInt4Zero':('let expected=[0,0,0,0];let left=[0,1,0,1];let right=[1,0,1,0];let mut out=[0_i32;4];a::binary_and(&mut out,&left,&right,4);array_eq!(r,expected,out,4);',4),
'BinaryAndInt4Mix':('let expected=[1,0,1,0];let left=[1,1,1,1];let right=[1,0,1,0];let mut out=[0_i32;4];a::binary_and(&mut out,&left,&right,4);array_eq!(r,expected,out,4);',4),
'BinaryOrInt4Alternate':('let left=[0,1,0,1];let right=[1,0,1,0];let expected=[1,1,1,1];let mut out=[0_i32;4];a::binary_or(&mut out,&left,&right,4);array_eq!(r,out,expected,4);',4),
'BinaryOrInt4Mix':('let left=[1,1,0,0];let right=[0,0,1,0];let expected=[1,1,1,0];let mut out=[0_i32;4];a::binary_or(&mut out,&left,&right,4);array_eq!(r,out,expected,4);',4),
'DeduplicateOrdered1':('let mut data=[0];let expected=[0];dedup_test(&mut r,&mut data,&expected);',4),
'DeduplicateOrdered2':('let mut data=[1,2];let expected=[1,2];dedup_test(&mut r,&mut data,&expected);',6),
'DeduplicateOrdered2Same':('let mut data=[1,1];let expected=[1];dedup_test(&mut r,&mut data,&expected);',4),
'DeduplicateOrdered3Same':('let mut data=[1,1,1];let expected=[1];dedup_test(&mut r,&mut data,&expected);',4),
'DeduplicateOrdered3':('let mut data=[3,3,2,2,1,1];let expected=[3,2,1];dedup_test(&mut r,&mut data,&expected);',8),
'FindAllRanges1':('let data=[false];let ranges=a::find_all_ranges(&data,true);eq!(r,ranges.len(),0);',1),
'FindAllRanges2':('let data=[true,true,true];let expected=[IndexRange::new(0,3)];ranges_test(&mut r,&data,&expected);',2),
'FindAllRanges3':('let data=[true,false];let expected=[IndexRange::new(0,1)];ranges_test(&mut r,&data,&expected);',2),
'FindAllRanges4':('let data=[false,true];let expected=[IndexRange::new(1,1)];ranges_test(&mut r,&data,&expected);',2),
'FindAllRanges5':('let data=[true,false,false,true,true,false,true];let expected=[IndexRange::new(0,1),IndexRange::new(3,2),IndexRange::new(6,1)];ranges_test(&mut r,&data,&expected);',4),
'FindMaxElement1':('max_test(&mut r,a::VirtualInts::from_slice(&[]),None);',1),
'FindMaxElement2':('let data=[1];max_test(&mut r,a::VirtualInts::from_slice(&data),Some(0));',2),
'FindMaxElement3':('let data=[1,2,2,1];max_test(&mut r,a::VirtualInts::from_slice(&data),Some(1));',2),
'FindMaxElement4':('max_test(&mut r,a::VirtualInts::from_fn(10,|x|{let x=x as i32;-x*x+9*x}),Some(4));',2),
'GroupIdsToIndicesEmpty':('groups_test(&mut r,&[],&[]);',5),
'GroupIdsToIndicesDense':('let ids=[5,3,5,-2,3,3,0,-2];groups_test(&mut r,&ids,&(0..ids.len()).collect::<Vec<_>>());',5),
'GroupIdsToIndicesSparse':('let ids=[1000000,3,1000000,-2000000,3,7];groups_test(&mut r,&ids,&(0..ids.len()).collect::<Vec<_>>());',5),
'GroupIdsToIndicesMask':('let ids=[4,1,4,2,1,2,4,3];let mask=[1_usize,2,5,6,7];groups_test(&mut r,&ids,&mask);',5),
'GroupIdsToIndicesLarge':('let mut dense_ids=vec![0_i32;100000];let mut sparse_ids=vec![0_i32;100000];for i in 0..dense_ids.len(){let x=i as i32;dense_ids[i]=(x*7919)%20011;sparse_ids[i]=((x*7919)%1009)*1000003;}let mask=(0..dense_ids.len()).filter(|i|i%3!=0).collect::<Vec<_>>();let full=(0..dense_ids.len()).collect::<Vec<_>>();groups_test(&mut r,&dense_ids,&full);groups_test(&mut r,&dense_ids,&mask);groups_test(&mut r,&sparse_ids,&full);groups_test(&mut r,&sparse_ids,&mask);',20),
}

def csv_expression(expr):
 s=expr.strip()
 if s=='std::nullopt':return 'None'
 if s.startswith('StrVec'):
  inner=s[len('StrVec'):].strip()
  if inner=='()':return 'Some(Vec::<String>::new())'
  if inner.startswith('('):inner=inner[1:-1]
  if not(inner.startswith('{') and inner.endswith('}')):raise ValueError('Unreviewed vector expression '+s)
  values=split_args(inner[1:-1]);return 'Some(vec!['+', '.join(v+'.to_owned()' for v in values)+'])'
 if s.startswith('"'):return s+'.to_owned()'
 def simple(args):
  fields=split_args(args);assert len(fields) in (2,3)
  delimiter='b'+fields[2] if len(fields)==3 else "b','"
  return 'Some(csv::find_end_of_simple_field('+fields[0]+'.as_bytes(), '+fields[1]+', '+delimiter+'))'
 s=rewrite_calls(s,'find_end_of_simple_field(',simple)
 s=rewrite_calls(s,'find_end_of_quoted_field(',lambda args:'csv::find_end_of_quoted_field('+split_args(args)[0]+'.as_bytes(), '+split_args(args)[1]+', b\'"\', &[b\'"\',b\'\\\\\'])')
 s=rewrite_calls(s,'parse_record_fields(',lambda args:'record_fields('+args+')')
 s=rewrite_calls(s,'unescape_field(',lambda args:'String::from_utf8(csv::unescape_field('+split_args(args)[0]+'.as_bytes(), &options).into_owned()).expect("Original fixture is UTF-8")')
 s=s.replace('.size()','.len()')
 return s

def translate_csv(body):
 s=strip_comments(body).replace('using StrVec = Vector<std::string>;','').replace('LinearAllocator<> allocator;','// Owned/Cow byte results replace test-only arena storage.')
 s=s.replace('CsvParseOptions options;','let mut options=csv::Options::default();')
 s=re.sub(r'StrParseResult result = parse_csv_fields\(', 'let result=csv_fields(',s)
 s=s.replace(', options);',', &options);')
 def comparison(args):
  fields=split_args(args);assert len(fields)==2
  left,right=fields;lhs=csv_expression(left);rhs=csv_expression(right)
  if left.startswith(('find_end_of_simple_field(','find_end_of_quoted_field(')) and right!='std::nullopt':rhs='Some('+right+')'
  return 'eq!(r, '+lhs+', '+rhs+')'
 s=rewrite_calls(s,'EXPECT_EQ(',comparison)
 for name,mac in [('TRUE','yes'),('FALSE','no')]:s=rewrite_calls(s,'EXPECT_'+name+'(',lambda args,mac=mac:mac+'!(r, '+csv_expression(args)+')')
 if re.search(r'\bEXPECT_|std::|\bStrVec|\bCsvParseOptions|\ballocator\b',code_mask(s)):raise ValueError('Untranslated CSV syntax '+s)
 return s

def translate_hash(body):
 s=strip_comments(body)
 s=s.replace('BLI_HashMurmur2A mm2;','let mut mm2=Murmur2A::default();').replace('uint32_t hash;','let hash:u32;')
 s=re.sub(r'const char \*(\w+) = ("(?:\\.|[^"\\])*");',r'let \1=\2.as_bytes();',s)
 s=s.replace('const int ints[4] = {1, 2, 3, 4};','let ints:[i32;4]=[1,2,3,4];')
 s=rewrite_calls(s,'BLI_hash_mm2a_init(',lambda a:'mm2.reset('+split_args(a)[1]+')')
 def add(args):
  a=split_args(args);assert a[0]=='&mm2'
  m=re.fullmatch(r'reinterpret_cast<const uchar \*>\((\w+)\)',a[1]);assert m
  name=m[1]
  if name=='ints':return 'mm2.add(&ints.iter().flat_map(|v|v.to_ne_bytes()).collect::<Vec<_>>())'
  if a[2]!='strlen('+name+')':raise ValueError('Changed byte count')
  return 'mm2.add('+name+')'
 s=rewrite_calls(s,'BLI_hash_mm2a_add(',add)
 s=rewrite_calls(s,'BLI_hash_mm2a_add_int(',lambda a:'mm2.add_int('+split_args(a)[1]+')')
 s=s.replace('BLI_hash_mm2a_end(&mm2)','mm2.end()')
 s=rewrite_calls(s,'EXPECT_EQ(',lambda a:'eq!(r, '+a+')')
 if re.search(r'BLI_|EXPECT_|reinterpret|strlen|sizeof',s):raise ValueError('Untranslated hash syntax')
 return s

def translate_disjoint(body):
 s=strip_comments(body).replace('DisjointSet disjoint_set(6);','let mut disjoint_set=DisjointSet::new(6);')
 for name,mac in [('EQ','eq'),('TRUE','yes'),('FALSE','no')]:s=rewrite_calls(s,'EXPECT_'+name+'(',lambda args,mac=mac:mac+'!(r, '+args+')')
 return s

def generate(root=ROOT):
 pin=json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit'];assert pin==PIN
 output=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[]
 for filename,digest in FILES.items():
  path='source/blender/blenlib/tests/'+filename;raw=(root/'.upstream/blender'/path).read_bytes();text=raw.decode()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Unreviewed source '+path)
  for identity,body,line in extract(text):
   if identity.startswith('array_utils.'):
    translated,count=ARRAY[identity.split('.')[1]]
   else:
    translated=(translate_csv if identity.startswith('csv_parse.') else translate_hash if identity.startswith('hash_mm2a.') else translate_disjoint)(body)
    count=len(re.findall(r'\bEXPECT_(?:EQ|TRUE|FALSE)\(',code_mask(body)))
    if len(re.findall(r'\b(?:eq|yes|no)!\(',code_mask(translated)))!=count:raise ValueError('Dropped assertion '+identity)
   fn=identity.replace('.','__');output+=f'\n// Original {path}:{line}\npub fn {fn}()->Report{{let mut r=Report::default();\n{translated}\nr\n}}\n'
   native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::data_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
   cases.append(dict(id=identity,path=path,line=line,source_sha256=digest,body_sha256=hashlib.sha256(body.encode()).hexdigest(),rust_function=fn,assertion_count=len(re.findall(r'\bEXPECT_\w+\(',code_mask(body))),expected_runtime_assertions=count,status='ported_unexecuted'))
  (root/'tests/upstream/blender'/filename).write_bytes(raw)
 if len(cases)!=49:raise ValueError('Case universe changed')
 output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 (root/'crates/blended-core/src/data_cases.rs').write_text(output)
 (root/'crates/blended-core/tests/upstream_data.rs').write_text(native)
 (root/'compatibility/data-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files=FILES,cases=cases,complete_blender_test_port=False,adapters=['Original helper and macro assertion expansions retained; no artificial per-element checks for Span operator==.','Independent insertion-ordered expected VectorSet uses BTreeMap lookup plus recorded insertion indices, not the implementation under test.','Original 100000-entry dense and sparse datasets and exact masks retained.','Source-locked CSV assertions preserve escaped bytes and default options; byte-oriented borrowed fields use Vec storage, test-only strings remain UTF-8.','CSV chunk boundaries and malformed-chunk retry are implemented, but parsing is sequential; parallel scheduling parity not claimed.','Murmur2A retains native-endian word loads, little-shift tail processing and mutable end() state; verified native/WASM are little endian.']),indent=2)+'\n')
 print(json.dumps(dict(cases=len(cases),assertions=sum(c['expected_runtime_assertions'] for c in cases))))
 return cases
if __name__=='__main__':generate()
