#!/usr/bin/env python3
"""One-time reviewed registration. Never silently reapprove changed targets in CI."""
from pathlib import Path
import hashlib,json
from port_string_ops_tests import generate,FILES
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Changed registration baseline: '+path)
 p.write_text(s.replace(old,new))
def install():
 cases=generate()
 p=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod string_ops_cases;' in p.read_text():raise ValueError('Already registered; do not refresh hashes')
 with p.open('a') as f:f.write('''
pub mod string_ops;
pub mod string_search;
pub mod string_ops_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_string_ops_case_count()->u32{string_ops_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_string_ops_run_case(index:u32)->i32{string_ops_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_string_ops_assertion_count(index:u32)->u32{string_ops_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('string_ops','string-ops-ports.json','string_ops_cases','upstream_string_ops','port_string_ops_tests.py','string_ops_assertions',('blended_string_ops_case_count','blended_string_ops_run_case','blended_string_ops_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/assertion_fidelity.py',"'heap_cases.rs','data_cases.rs']:","'heap_cases.rs','data_cases.rs','string_ops_cases.rs']:")
 replace('tools/assertion_fidelity.py',"('string_ref_cases.rs','bit_span_cases.rs','data_cases.rs'):","('string_ref_cases.rs','bit_span_cases.rs','data_cases.rs','string_ops_cases.rs'):")
 replace('tools/assertion_fidelity.py','        changes={', '''        changes={
          'macro_rules! peq ': 'macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::pointer_pair($a,$b),stringify!($a pointer-equals $b),line!());}};}',
          'macro_rules! lt ': 'macro_rules! lt {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::lt($a,$b),stringify!($a < $b),line!());}};}',
'''.rstrip())
 replace('tools/assertion_fidelity.py',"'EQ':2,'GT':2,", "'EQ':2,'GT':2,'LT':2,")
 replace('tools/assertion_fidelity.py',"    if value.startswith('p8:'):","    if value in ('palias:null','palias:a','palias:b'):return ('pointer_alias',value[7:])\n    if value.startswith('p8:'):")
 replace('tools/fidelity/trace.rs','pub fn gt<T:', '''pub fn pointer_pair(a:*const u8,b:*const u8)->bool {
 let origin=if a.is_null(){b}else{a};
 let encode=|p:*const u8|format!("\\\"palias:{}\\\"",if p.is_null(){"null"}else if p==origin{"a"}else{"b"});
 let passed=a==b;record("EQ",passed,&[encode(a),encode(b)]);passed
}
pub fn lt<T:PartialOrd+Value>(a:T,b:T)->bool{let p=a<b;record("LT",p,&[a.encode(),b.encode()]);p}
pub fn gt<T:''')
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|t.borrow().1.clone())',' for (id,run,n) in crate::string_ops_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|t.borrow().1.clone())')
 replace('tools/fidelity/trace.hh','namespace blended_fidelity {','namespace blender {struct WordInfo;}\nnamespace blended_fidelity {')
 replace('tools/fidelity/trace.hh','template<class T,int N> struct Encoder<blender::VecBase<T,N>>', '''// Defined by the original test after the overlay include. Dependent member
// access is instantiated only once that original type is complete.
template<> struct Encoder<blender::WordInfo> {
 template<class T> static void write(std::ostream &out,const T&v){out<<'[';value(out,v.start);out<<',';value(out,v.end);out<<']';}
};
struct PointerAlias {const void *value;const void *origin;};
template<> struct Encoder<PointerAlias> {static void write(std::ostream&out,PointerAlias v){out<<"\\\"palias:"<<(v.value==nullptr?"null":v.value==v.origin?"a":"b")<<"\\\"";}};
template<class T,int N> struct Encoder<blender::VecBase<T,N>>''')
 old='template<class A,class B> void eq(const A &a,const B &b) {record("EQ",bool(::testing::internal::EqHelper::Compare("a","b",a,b)),nullptr,nullptr,a,b);EXPECT_EQ(a,b);}'
 new='''template<class A,class B> void eq(const A &a,const B &b) {
 const bool passed=bool(::testing::internal::EqHelper::Compare("a","b",a,b));
 if constexpr(std::is_pointer_v<A> && std::is_pointer_v<B>){
  // Different input literals in the string fixture have unrelated allocation
  // layouts across C++ and Rust. Preserve real equality/nullness with pair-local
  // alias labels; do not apply this normalization to older pointer-offset tests.
  if(std::strcmp(::testing::UnitTest::GetInstance()->current_test_info()->test_suite_name(),"string")==0){
   const void *aa=static_cast<const void*>(a),*bb=static_cast<const void*>(b),*origin=aa?aa:bb;
   record("EQ",passed,nullptr,nullptr,PointerAlias{aa,origin},PointerAlias{bb,origin});
  }else record("EQ",passed,nullptr,nullptr,a,b);
 }else record("EQ",passed,nullptr,nullptr,a,b);
 EXPECT_EQ(a,b);
}'''
 replace('tools/fidelity/trace.hh',old,new)
 replace('tools/fidelity/trace.hh','template<class A,class B> void gt(','''template<class A,class B> void lt(const A &a,const B &b){record("LT",a<b,nullptr,nullptr,a,b);EXPECT_LT(a,b);}
template<class T> void vector_eq(const std::vector<T>&expected,const std::vector<T>&actual){
 record("EQ",expected.size()==actual.size(),nullptr,nullptr,expected.size(),actual.size());
 if(expected.size()==actual.size())for(size_t i=0;i<expected.size();++i)record("EQ",bool(::testing::internal::EqHelper::Compare("expected","actual",expected[i],actual[i])),nullptr,nullptr,expected[i],actual[i]);
 ::EXPECT_EQ_VECTOR(expected,actual);
}
template<class A,class B> void gt(''')
 with (ROOT/'tools/fidelity/trace.hh').open('a') as f:f.write('\n#undef EXPECT_LT\n#define EXPECT_LT(a,b) ::blended_fidelity::lt((a),(b))\n#define EXPECT_EQ_VECTOR ::blended_fidelity::vector_eq\n')
 p=ROOT/'compatibility/assertion-contracts.lock.json';data=json.loads(p.read_text());target='crates/blended-core/src/string_ops_cases.rs'
 for filename,digest in FILES.items():
  path='source/blender/blenlib/tests/'+filename
  data['contracts'].append(dict(source_path=path,source_sha256=digest,target_path=target,target_sha256=hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),case_ids=[c['id'] for c in cases if c['path']==path]))
 p.write_text(json.dumps(data,indent=2)+'\n')
 from port_workbench import expected_cases
 current,_=expected_cases();assert len(current)==464 and sum(c['expected_runtime_assertions'] for c in current)==34214
 for name in ('test_collection_port.py','test_data_port.py','test_extended_port.py','test_geometry_math_port.py','test_heap_port.py','test_numeric_types.py','test_port_workbench.py','test_sampling_integration.py','test_sampling_port.py'):
  p=ROOT/'tests'/name;before=p.read_text();after=before.replace(',416)',',464)').replace(',33368)',',34214)').replace("['contracts']),32)","['contracts']),35)")
  if name=='test_port_workbench.py':after=after.replace("'data_assertions':0,","'data_assertions':0,'string_ops_assertions':0,")
  if before==after:raise ValueError('Subset accounting baseline changed: '+name)
  p.write_text(after)
if __name__=='__main__':install()
