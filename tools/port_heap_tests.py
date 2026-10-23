#!/usr/bin/env python3
"""Source-locked ports of the complete pinned heap and in-place queue test files.

Not a general C++ translator. Unknown source revisions or unhandled syntax fail.
Integer pointer payloads are represented as i32 tokens; the real pointer-identity
cases use actual pointers. Original RNG seeds, algorithms and loop bounds remain.
"""
from pathlib import Path
import hashlib,json,re
from port_collection_tests import extract,split_args,rewrite_calls
from port_numeric_type_tests import comments
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
FILES={
 'BLI_heap_test.cc':'3e555368400a5d1e1d061a88213e602a0140a72094344bb05f0527b89c6dee47',
 'BLI_heap_simple_test.cc':'283d525ab32473e7fa147d6a3cc292ce392cb23d701f84beb16fce42c8dea21b',
 'BLI_inplace_priority_queue_test.cc':'98dd7e546e3c90ea7d06de4fdc20330af925c1651832e9150c5333e6a069b7d4',
}
COUNTS={
 'Empty':2,'One':5,'Range':1025,'RangeReverse':1025,'RangeRemove':513,
 'Duplicates':1025,'Rand1':2,'Rand2':3,'Rand100':101,'ReInsertSimple':1025,
 'ReInsertRandom1':4,'ReInsertRandom2':6,'ReInsertRandom100':202,
 'ReInsertRandom1024':2050,'ReInsertRandom2048':4098,
 'SimpleEmpty':2,'SimpleOne':5,'SimpleRange':1025,'SimpleRangeReverse':1025,
 'SimpleDuplicates':1025,'SimpleRand1':2,'SimpleRand2':3,'SimpleRand100':101,
 'BuildSmall':7,'DecreasePriority':3,'IncreasePriority':3,'PopAll':1000,
 'ManyPriorityChanges':1000,'IndicesAccess':13,
}
HEAD='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked translations. See compatibility/heap-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::priority_heaps::{MinHeap,SimpleMinHeap,NodeId,InplacePriorityQueue,BlenderRng,array_randomize};
use core::cell::Cell;
const SIZE:i32=1024;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! le {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)<=($b),stringify!($a <= $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
// range_fl preserves the reverse write order of the original helper. The safe
// slice replaces a pointer that was decremented past the beginning after its last use.
fn range_fl(values:&mut [f32],size:i32){let mut i=size;while i>0{i-=1;values[i as usize]=i as f32;}}
'''

def original_helper(text,name):
 m=re.search(r'static void '+re.escape(name)+r'\([^)]*\)\s*\{',text)
 if not m:raise ValueError('Missing original helper '+name)
 start=m.end();end=start;depth=1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[start:end-1],text.count('\n',0,m.start())+1

def translate(body,queue=False,helper=False):
 s=comments(body)
 s=re.sub(r'\bin\b','input',s)
 s=s.replace('const char *input = "test";','let input = b"test\\0".as_ptr();')
 for typ in ('HeapSimple','Heap'):
  rust='SimpleMinHeap' if typ=='HeapSimple' else 'MinHeap'
  payload='*const u8' if 'let input = b"test' in s else 'i32'
  s=re.sub(r'\b'+typ+r' \*heap;', '',s)
  function='BLI_heapsimple_new' if typ=='HeapSimple' else 'BLI_heap_new'
  s=re.sub(r'(?:'+typ+r' \*)?heap = '+function+r'\(\);',f'let mut heap={rust}::<{payload}>::new();',s)
 s=s.replace('HeapNode *node_top = BLI_heap_top(heap);','let node_top=heap.top();')
 s=re.sub(r'HeapNode \*\*nodes = MEM_new_array_uninitialized<HeapNode \*>\(size_t\(items_total\), __func__\);','let mut nodes=vec![NodeId::INVALID;items_total as usize];',s)
 s=re.sub(r'float \*values = MEM_new_array_uninitialized<float>\(size_t\(items_total\), __func__\);','let mut values=vec![0.0_f32;items_total as usize];',s)
 s=s.replace('nodes[i] = nullptr','nodes[i] = NodeId::INVALID')
 s=s.replace('const_cast<char *>(input)','input')
 s=rewrite_calls(s,'POINTER_FROM_INT(',lambda a:'('+a+') as i32')
 s=rewrite_calls(s,'POINTER_AS_INT(',lambda a:a)
 s=rewrite_calls(s,'float(',lambda a:'('+a+') as f32')
 s=rewrite_calls(s,'int(',lambda a:'('+a+') as i32')
 s=re.sub(r'(\d+\.\d+)f\b',r'\1_f32',s)
 s=s.replace('nullptr','0_i32')
 methods={'is_empty':'is_empty','len':'len','pop_min':'pop_min','insert':'insert','remove':'remove','node_value_update':'update','is_valid':'is_valid','top':'top','top_value':'top_value'}
 for prefix in ('BLI_heapsimple_','BLI_heap_'):
  for name,method in methods.items():
   def call(a,method=method):
    args=split_args(a)
    if args[0]!='heap':raise ValueError('Unexpected heap receiver')
    return 'heap.'+method+'('+', '.join(args[1:])+')'
   s=rewrite_calls(s,prefix+name+'(',call)
  s=rewrite_calls(s,prefix+'free(',lambda a:'drop(heap)' if split_args(a)==['heap','0_i32'] else (_ for _ in ()).throw(ValueError('Unexpected payload destructor')))
 s=rewrite_calls(s,'BLI_heap_node_value(',lambda a:'heap.node_value('+a+')')
 s=rewrite_calls(s,'BLI_array_randomize(',lambda a:'array_randomize(&mut '+split_args(a)[0]+'[..('+split_args(a)[2]+') as usize], ('+split_args(a)[3]+') as u32)')
 s=rewrite_calls(s,'MEM_delete(',lambda a:'drop('+a+')')
 s=s.replace('range_fl(values,','range_fl(&mut values,')
 for name in ('random_heap_helper','random_heapsimple_helper','random_heap_reinsert_helper'):
  s=rewrite_calls(s,name+'(',lambda a,name=name:name+'(&mut report, '+a+')')
 if queue:
  s=s.replace('RandomNumberGenerator rng;', 'let mut rng=BlenderRng::new(0);')
  s=s.replace('Vector<int> values;', 'let mut values:Vec<Cell<i32>>=Vec::new();')
  s=re.sub(r'Array<int> values = \{([^}]+)\};',r'let values:Vec<Cell<i32>>=vec![\1].into_iter().map(Cell::new).collect();',s)
  s=re.sub(r'InplacePriorityQueue<int> priority_queue(?:\(values\)|\{values\});','let mut priority_queue=InplacePriorityQueue::new(&values);',s)
  s=rewrite_calls(s,'values.append(',lambda a:'values.push(Cell::new('+a+'))')
  s=re.sub(r'values\[(\d+|index)\] = ([^;]+);',r'values[(\1) as usize].set(\2);',s)
  s=s.replace('values[priority_queue.inactive_indices()[0]]','values[priority_queue.inactive_indices()[0]].get()').replace('values[priority_queue.inactive_indices()[1]]','values[priority_queue.inactive_indices()[1]].get()')
  for method in ('priority_increased','priority_decreased','priority_changed'):
   s=rewrite_calls(s,'priority_queue.'+method+'(',lambda a,method=method:'priority_queue.'+method+'(('+a+') as usize)')
  s=s.replace('.size()','.len()')
 else:
  s=re.sub(r'\b(nodes|values)\[([^\]]+)\]',lambda m:m[1]+'[('+m[2]+') as usize]' if not m[2].startswith('..') else m[0],s)
 s=re.sub(r'for \(int (\w+) = 0; \1 < (\w+); \1\+\+\)',r'for \1 in 0..\2',s)
 s=re.sub(r'for \(int (\w+) = ([01]); \1 < items_total; \1 \+= 2\)',r'for \1 in (\2..items_total).step_by(2)',s)
 s=s.replace('for (int out_test = items_total - 1; out_test >= 0; out_test--)','for out_test in (0..items_total).rev()')
 s=s.replace('while (!priority_queue.is_empty())','while !priority_queue.is_empty()')
 s=re.sub(r'\b(?:const )?int (\w+) = ([^;]+);',r'let mut \1:i32=\2;',s)
 s=re.sub(r'\bfloat (\w+) = ([^;]+);',r'let mut \1:f32=\2;',s)
 for cpp,macro in [('EQ','eq'),('LE','le'),('TRUE','yes'),('FALSE','no')]:
  s=rewrite_calls(s,'EXPECT_'+cpp+'(',lambda a,macro=macro:macro+'!(report, '+a+')')
 if re.search(r'\bEXPECT_|\bBLI_|\bMEM_|\b(?:float|Heap|HeapNode|HeapSimple|int)\b|for \(int|nullptr|const_cast|Vector<|Array<',s):raise ValueError('Untranslated syntax: '+s)
 return s

def generate(root=ROOT):
 if json.loads((root/'upstream.lock.json').read_text())['upstreams']['blender']['commit']!=PIN:raise ValueError('Wrong reference')
 output=HEAD;native='// SPDX-License-Identifier: Apache-2.0\n';cases=[];helpers=[]
 for filename,digest in FILES.items():
  path='source/blender/blenlib/tests/'+filename;raw=(root/'.upstream/blender'/path).read_bytes();text=raw.decode()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Source changed: '+path)
  queue='priority_queue' in filename
  names=[] if queue else (['random_heapsimple_helper'] if 'simple' in filename else ['random_heap_helper','random_heap_reinsert_helper'])
  for name in names:
   body,line=original_helper(text,name);translation=translate(body)
   output+=f'\n// Original helper: {path}:{line}\nfn {name}(report:&mut Report,items_total:i32,random_seed:i32){{\n{translation}\n}}\n'
   helpers.append(dict(name=name,path=path,line=line,assertion_sites=len(re.findall(r'\bEXPECT_\w+\(',body))))
  for identity,body,line in extract(text):
   code=translate(body,queue=queue);sites=len(re.findall(r'\bEXPECT_\w+\(',body));fn=identity.replace('.','__');count=COUNTS[identity.split('.')[1]]
   if sites!=len(re.findall(r'\b(?:eq|le|yes|no)!\(',code)):raise ValueError('Lost assertion site '+identity)
   output+=f'\n// {path}:{line}\npub fn {fn}()->Report{{let mut report=Report::default();\n{code}\nreport\n}}\n'
   native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}(){{let r=blended_core::heap_cases::{fn}();assert!(r.passed(),"{{:?}}",r.failures);assert_eq!(r.assertions,{count});}}\n'
   cases.append(dict(id=identity,path=path,line=line,source_sha256=digest,rust_function=fn,assertion_count=sites,expected_runtime_assertions=count,index=len(cases),status='ported_unexecuted'))
  (root/'tests/upstream/blender'/filename).write_bytes(raw)
 output+='\npub const CASES:&[(&str,fn()->Report,u32)]=&[\n'+''.join(f'("{c["id"]}",{c["rust_function"]},{c["expected_runtime_assertions"]}),\n' for c in cases)+'];\n'
 if len(cases)!=29 or {c['id'].split('.')[1] for c in cases}!=set(COUNTS):raise ValueError('Case universe changed')
 (root/'crates/blended-core/src/heap_cases.rs').write_text(output)
 (root/'crates/blended-core/tests/upstream_heaps.rs').write_text(native)
 (root/'compatibility/heap-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit=PIN,source_files=FILES,cases=cases,helpers=helpers,complete_blender_test_port=False,notes='Complete three test files. Same seeds, shuffled lengths and loop counts. Shared Cell<i32> storage preserves external priority mutation before notification. Pointer payload One cases use actual addresses; integer pointer tokens remain i32. Stable node handles replace allocation addresses not inspected by these tests. The pinned in-place queue last-two-items behaviour is intentionally retained and documented, not silently corrected.'),indent=2)+'\n')
 return cases
if __name__=='__main__':
 cases=generate();print(json.dumps(dict(cases=len(cases),runtime_assertions=sum(c['expected_runtime_assertions'] for c in cases))))
