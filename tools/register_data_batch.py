#!/usr/bin/env python3
"""One-time reviewed registration, not a CI target-hash auto-approval."""
from pathlib import Path
import hashlib,json
from port_data_tests import generate,FILES
ROOT=Path(__file__).resolve().parents[1]
def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Baseline changed; review '+path)
 p.write_text(s.replace(old,new))
def install():
 cases=generate()
 p=ROOT/'crates/blended-core/src/lib.rs'
 if 'pub mod data_cases;' in p.read_text():raise ValueError('Already registered; never silently refresh reviewed hashes')
 with p.open('a') as f:f.write('''
pub mod array_ops;
pub mod csv_fields;
pub mod hash_mm2a;
pub mod disjoint_set;
pub mod data_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_data_case_count()->u32{data_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_data_run_case(index:u32)->i32{data_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_data_assertion_count(index:u32)->u32{data_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
 replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('data','data-ports.json','data_cases','upstream_data','port_data_tests.py','data_assertions',('blended_data_case_count','blended_data_run_case','blended_data_assertion_count')),\n)\nTOTAL_KEYS=")
 replace('tools/assertion_fidelity.py',"'heap_cases.rs']:","'heap_cases.rs','data_cases.rs']:")
 replace('tools/assertion_fidelity.py',"('string_ref_cases.rs','bit_span_cases.rs'):","('string_ref_cases.rs','bit_span_cases.rs','data_cases.rs'):")
 replace('tools/assertion_fidelity.py','        changes={', '''        changes={
          'macro_rules! streq ': 'macro_rules! streq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::str_eq(c_string($a),c_string($b)),stringify!($a C-string-equals $b),line!());}};}',
'''.rstrip())
 replace('tools/assertion_fidelity.py',"'EQ':2,'GT':2,", "'EQ':2,'GT':2,'STREQ':2,")
 replace('tools/fidelity/trace.rs','pub fn eq_refs<','impl Value for String {fn encode(&self)->String{bytes_value(self.as_bytes())}}\nimpl<T:Value> Value for Vec<T> {fn encode(&self)->String{self.as_slice().encode()}}\npub fn str_eq(a:&[u8],b:&[u8])->bool{let p=a==b;record("STREQ",p,&[bytes_value(a),bytes_value(b)]);p}\npub fn eq_refs<')
 replace('tools/fidelity/trace.rs',' TAPE.with(|t|t.borrow().1.clone())',' for (id,run,n) in crate::data_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|t.borrow().1.clone())')
 replace('tools/fidelity/trace.hh','// String-value assertions', '''template<class T,int64_t N,class A> struct Encoder<blender::Vector<T,N,A>> {
 static void write(std::ostream &out,const blender::Vector<T,N,A>&v){out<<'[';for(int64_t i=0;i<v.size();++i){if(i)out<<',';value(out,v[i]);}out<<']';}
};
// String-value assertions''')
 replace('tools/fidelity/trace.hh','template<class A,class B> void eq(', '''template<class T> void array_eq(const T*expected,const T*actual,size_t n){
 for(size_t i=0;i<n;++i)record("EQ",bool(::testing::internal::EqHelper::Compare("expected","actual",expected[i],actual[i])),nullptr,nullptr,expected[i],actual[i]);
 ::EXPECT_EQ_ARRAY(expected,actual,n);
}
inline void str_eq(const char*a,const char*b){
 const bool passed=bool(::testing::internal::CmpHelperSTREQ("a","b",a,b));
 record("STREQ",passed,nullptr,nullptr,a?std::optional<std::string>(a):std::nullopt,b?std::optional<std::string>(b):std::nullopt);
 EXPECT_STREQ(a,b);
}
template<class A,class B> void eq(''')
 with (ROOT/'tools/fidelity/trace.hh').open('a') as f:f.write('\n#define EXPECT_EQ_ARRAY ::blended_fidelity::array_eq\n#undef EXPECT_STREQ\n#define EXPECT_STREQ(a,b) ::blended_fidelity::str_eq((a),(b))\n')
 p=ROOT/'compatibility/assertion-contracts.lock.json';data=json.loads(p.read_text());target='crates/blended-core/src/data_cases.rs'
 for name,digest in FILES.items():
  path='source/blender/blenlib/tests/'+name
  data['contracts'].append(dict(source_path=path,source_sha256=digest,target_path=target,target_sha256=hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),case_ids=[c['id'] for c in cases if c['path']==path]))
 p.write_text(json.dumps(data,indent=2)+'\n')
 from port_workbench import expected_cases
 current,_=expected_cases();assert len(current)==416 and sum(c['expected_runtime_assertions'] for c in current)==33368
 # These are infrastructure subset-total guards only, not translated expectations.
 for name in ('test_collection_port.py','test_extended_port.py','test_numeric_types.py','test_geometry_math_port.py','test_port_workbench.py','test_sampling_integration.py','test_sampling_port.py','test_heap_port.py'):
  p=ROOT/'tests'/name;s=p.read_text();updated=s.replace(',367)',',416)').replace(',33104)',',33368)').replace("['contracts']),28)","['contracts']),32)")
  if name=='test_port_workbench.py':updated=updated.replace("'heap_assertions':0,","'heap_assertions':0,'data_assertions':0,")
  if s==updated:raise ValueError('Expected subset guard missing: '+name)
  p.write_text(updated)
if __name__=='__main__':install()
