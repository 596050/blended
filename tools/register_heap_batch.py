#!/usr/bin/env python3
"""One-time registration of the reviewed heap translation, never a CI hash auto-approval."""
from pathlib import Path
import hashlib,json
from port_heap_tests import generate,FILES
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Baseline changed; review '+path)
 p.write_text(s.replace(old,new))
def install():
 cases=generate()
 p=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod heap_cases;' in p.read_text():raise ValueError('Batch already registered; do not refresh reviewed hashes')
 with p.open('a') as f:f.write('''
pub mod priority_heaps;
pub mod heap_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_heaps_case_count()->u32{heap_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_heaps_run_case(index:u32)->i32{heap_cases::CASES.get(index as usize).map(|(_,run,count)|{let r=run();i32::from(r.passed()&&r.assertions==*count)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_heaps_assertion_count(index:u32)->u32{heap_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('heaps','heap-ports.json','heap_cases','upstream_heaps','port_heap_tests.py','heap_assertions',('blended_heaps_case_count','blended_heaps_run_case','blended_heaps_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/assertion_fidelity.py',"'curve_cases.rs','geometry_math_cases.rs']:","'curve_cases.rs','geometry_math_cases.rs','heap_cases.rs']:")
 replace('tools/assertion_fidelity.py',"        changes={", "        changes={\n          'macro_rules! le ': 'macro_rules! le {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::le($a,$b),stringify!($a <= $b),line!());}};}',")
 replace('tools/assertion_fidelity.py',"'EQ':2,'GT':2,", "'EQ':2,'GT':2,'LE':2,")
 replace('tools/fidelity/trace.rs','pub fn gt<T:', 'pub fn le<T:PartialOrd+Value>(a:T,b:T)->bool{let p=a<=b;record("LE",p,&[a.encode(),b.encode()]);p}\npub fn gt<T:')
 replace('tools/fidelity/trace.rs', ' TAPE.with(|t|t.borrow().1.clone())', ' for (id,run,count) in crate::heap_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*count);}\n TAPE.with(|t|t.borrow().1.clone())')
 replace('tools/fidelity/trace.hh','template<> struct Encoder<char*>', 'template<> struct Encoder<void*> {static void write(std::ostream &out,void *v){byte_pointer_value(out,static_cast<const char*>(v));}};\ntemplate<> struct Encoder<char*>')
 replace('tools/fidelity/trace.hh','template<class A,class B> void gt(', 'template<class A,class B> void le(const A &a,const B &b){record("LE",a<=b,nullptr,nullptr,a,b);EXPECT_LE(a,b);}\ntemplate<class A,class B> void gt(')
 with (ROOT/'tools/fidelity/trace.hh').open('a') as f:f.write('\n#undef EXPECT_LE\n#define EXPECT_LE(a,b) ::blended_fidelity::le((a),(b))\n')
 p=ROOT/'compatibility/assertion-contracts.lock.json';data=json.loads(p.read_text())
 target='crates/blended-core/src/heap_cases.rs';digest=hashlib.sha256((ROOT/target).read_bytes()).hexdigest()
 for filename,source_digest in FILES.items():
  path='source/blender/blenlib/tests/'+filename
  data['contracts'].append(dict(source_path=path,source_sha256=source_digest,target_path=target,target_sha256=digest,case_ids=[c['id'] for c in cases if c['path']==path]))
 p.write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':install()
