from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1]
def mod(path,f):
 p=r/path;t=p.read_text();p.write_text(f(t))
assert len(json.loads((r/'compatibility/assertion-contracts.lock.json').read_text())['contracts'])==14
p=r/'tools/port_numerics_text_tests.py';s=p.read_text()
s=s.replace("if len(args)==1:return 's::StringRef::new(&('+string_expr(args[0])+'))'", "if len(args)==1:\n            if args[0].startswith('s::StringRef::with_length('):\n                return args[0]\n            if args[0].startswith('Span<char>'):\n                return string_expr(args[0])\n            return 's::StringRef::new(&('+string_expr(args[0])+'))'")
s=s.replace("elif rest.startswith('='):","elif identity.endswith('.StdStringConstructor') and expr=='str':out='s::StringRef::with_length(str.as_bytes(),str.len())'\n        elif rest.startswith('='):")
s=s.replace('Constexpr string assertions are embedded and vector compile-time contracts are tracked separately.','Four constexpr string assertions are retained in the generated cases. Nine standalone C++ vector type/layout assertions remain unported and are not hidden from the source ledger.')
p.write_text(s)
import port_numerics_text_tests
port_numerics_text_tests.generate(root=r)
assert hashlib.sha256((r/'crates/blended-core/src/numerics_text_cases.rs').read_bytes()).hexdigest()=='2527ffb7be007ed05defdf8a92c77386584ce376bb15831f57135fc3143dba21'
mod('crates/blended-core/src/lib.rs',lambda s:s+'\npub mod numeric_vectors;\npub mod string_views;\npub mod color_types;\n'+'''
#[unsafe(no_mangle)]
pub extern "C" fn blended_numerics_text_case_count()->u32 {numerics_text_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_numerics_text_run_case(index:u32)->i32 {
    numerics_text_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_numerics_text_assertion_count(index:u32)->u32 {
    numerics_text_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}
''')
mod('tools/port_workbench.py',lambda s:s.replace("'structures','collections'","'structures','collections','numerics_text'")
 .replace('collection_assertions:0','collection_assertions:0,numerics_text_assertions:0')
 .replace('w.blended_collections_assertion_count]','w.blended_collections_assertion_count],numerics_text:[w.blended_numerics_text_case_count,w.blended_numerics_text_run_case,w.blended_numerics_text_assertion_count]')
 .replace("if(c.group==='collections')result.collection_assertions+=assertions;","if(c.group==='collections')result.collection_assertions+=assertions;\n   if(c.group==='numerics_text')result.numerics_text_assertions+=assertions;")
 .replace("('collection-ports.json','collections')","('collection-ports.json','collections'),('numerics-text-ports.json','numerics_text')")
 .replace("('collections','collection_assertions')","('collections','collection_assertions'),('numerics_text','numerics_text_assertions')")
 .replace("'complete_test_port':False,'wasm_sha256'","'numerics_text':json.loads((ROOT/'compatibility/numerics-text-ports.json').read_text())['cases'],'complete_test_port':False,'wasm_sha256'"))
mod('tools/test_port_audit.py',lambda s:s.replace("('collection-ports.json'","('numerics-text-ports.json','crates/blended-core/src/numerics_text_cases.rs','upstream_numerics_text'),\n        ('collection-ports.json'"))
m=json.loads((r/'compatibility/numerics-text-ports.json').read_text())
p=r/'compatibility/assertion-contracts.lock.json';d=json.loads(p.read_text())
for name,sha in m['source_files'].items():
 path='source/blender/blenlib/tests/'+name
 d['contracts'].append({'source_path':path,'source_sha256':sha,'target_path':'crates/blended-core/src/numerics_text_cases.rs','target_sha256':hashlib.sha256((r/'crates/blended-core/src/numerics_text_cases.rs').read_bytes()).hexdigest(),'case_ids':[c['id'] for c in m['cases'] if c['path']==path],'review':'Runtime assertions, literal inputs, typed constructors and explicit swizzle writeback reviewed. Standalone vector type traits/layout assertions remain unported; string constexpr assertions are retained in the executable cases.'})
p.write_text(json.dumps(d,indent=2)+'\n')
mod('tests/test_port_workbench.py',lambda s:s.replace("'collection_assertions':0","'collection_assertions':0,'numerics_text_assertions':0").replace('len(cases),131','len(cases),224'))
mod('tests/test_collection_port.py',lambda s:s.replace("['contracts']),14","['contracts']),17").replace('len(c),131','len(c),224').replace('in c),1049','in c),1499').replace("'collection-ports.json','compile-time-ports.json'","'collection-ports.json','numerics-text-ports.json','compile-time-ports.json'"))
mod('tools/assertion_fidelity.py',lambda s:s.replace("['additional_cases.rs','structure_cases.rs','collection_cases.rs']","['additional_cases.rs','structure_cases.rs','collection_cases.rs','numerics_text_cases.rs']")
 .replace("# Preserve the original scalar EQ expected-value cast.","""if name=='numerics_text_cases.rs':
            changes['macro_rules! eq ']='macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::eq_ref(&($a),&($b)),stringify!($a == $b),line!());}};} '
            changes['macro_rules! numeq ']='macro_rules! numeq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::eq($a as f64,$b as f64),stringify!($a == $b),line!());}};} '
        # Preserve the original scalar EQ expected-value cast.""")
 .replace("if value.startswith('p64:'):","if value.startswith('p8:'):return ('byte_pointer',int(value[3:]))\n    if value.startswith('s:'):return ('bytes',bytes.fromhex(value[2:]))\n    if value.startswith('p64'):".replace("startswith('p64')","startswith('p64:')")))
mod('tools/fidelity/trace.rs',lambda s:s.replace('pub fn record(','''impl<T:Value,const N:usize> Value for crate::numeric_vectors::V<T,N>{fn encode(&self)->String{self.0.encode()}}
fn text_value(bytes:&[u8])->String{format!("\\\"s:{}\\\"",bytes.iter().map(|b|format!("{b:02x}")).collect::<String>())}
impl Value for str{fn encode(&self)->String{text_value(self.as_bytes())}}
impl Value for &str{fn encode(&self)->String{text_value(self.as_bytes())}}
impl Value for String{fn encode(&self)->String{text_value(self.as_bytes())}}
impl Value for crate::string_views::StringRef<'_>{fn encode(&self)->String{text_value(self.as_bytes())}}
impl Value for crate::string_views::StringRefNull<'_>{fn encode(&self)->String{text_value(self.as_bytes())}}
impl Value for *const u8{fn encode(&self)->String{POINTER_ORIGIN.with(|origin|{
 let address=*self as usize;let mut origin=origin.borrow_mut();let base=*origin.get_or_insert(address);
 format!("\\\"p8:{}\\\"",address as i128-base as i128)
})}}
pub fn eq_ref<A:PartialEq<B>+Value+?Sized,B:Value+?Sized>(a:&A,b:&B)->bool{
 let p=a==b;record("EQ",p,&[a.encode(),b.encode()]);p
}
pub fn record(''').replace(' TAPE.with(|t|t.borrow().1.clone())', ''' for (id,run,count) in crate::numerics_text_cases::CASES{start(id);let r=run();assert!(r.passed(),"Numeric/text port failed");assert_eq!(r.assertions,*count);}
 TAPE.with(|t|t.borrow().1.clone())'''))
mod('tools/fidelity/trace.hh',lambda s:s.replace('#include "BLI_span.hh"','#include "BLI_span.hh"\n#include "BLI_string_ref.hh"\n#include <string_view>')
 .replace('inline std::ofstream &stream()', '''inline void text_value(std::ostream &out,const char *p,size_t n){
 out<<"\\\"s:";static constexpr char hex[]="0123456789abcdef";
 for(size_t i=0;i<n;++i){auto v=static_cast<unsigned char>(p[i]);out<<hex[v>>4]<<hex[v&15];}out<<'"';
}
template<> struct Encoder<std::string>{static void write(std::ostream &out,const std::string &v){text_value(out,v.data(),v.size());}};
template<> struct Encoder<std::string_view>{static void write(std::ostream &out,const std::string_view &v){text_value(out,v.data(),v.size());}};
template<> struct Encoder<blender::StringRef>{static void write(std::ostream &out,const blender::StringRef &v){text_value(out,v.data(),v.size());}};
template<> struct Encoder<blender::StringRefNull>{static void write(std::ostream &out,const blender::StringRefNull &v){text_value(out,v.data(),v.size());}};
template<> struct Encoder<const char*>{static void write(std::ostream &out,const char *v){text_value(out,v,std::strlen(v));}};
template<> struct Encoder<char*>{static void write(std::ostream &out,const char *v){text_value(out,v,std::strlen(v));}};
template<size_t N>struct Encoder<char[N]>{static void write(std::ostream &out,const char (&v)[N]){text_value(out,v,std::strlen(v));}};
struct ByteAddress{const char *ptr;};
template<>struct Encoder<ByteAddress>{static void write(std::ostream &out,ByteAddress v){
 static const ::testing::TestInfo *last=nullptr;static std::uintptr_t base=0;
 auto *test=::testing::UnitTest::GetInstance()->current_test_info();auto address=reinterpret_cast<std::uintptr_t>(v.ptr);
 if(last!=test){last=test;base=address;}
 out<<"\\\"p8:"<<static_cast<int64_t>(address)-static_cast<int64_t>(base)<<"\\\"";
}};
inline std::ofstream &stream()''')
 .replace('template<class A,class B> void eq(const A &a,const B &b) {record("EQ",bool(::testing::internal::EqHelper::Compare("a","b",a,b)),nullptr,nullptr,a,b);EXPECT_EQ(a,b);}', '''template<class A,class B> void eq(const A &a,const B &b) {
 const bool p=bool(::testing::internal::EqHelper::Compare("a","b",a,b));
 if constexpr(std::is_pointer_v<A>&&std::is_pointer_v<B>&&std::is_same_v<std::remove_cv_t<std::remove_pointer_t<A>>,char>&&std::is_same_v<std::remove_cv_t<std::remove_pointer_t<B>>,char>){record("EQ",p,nullptr,nullptr,ByteAddress{a},ByteAddress{b});}
 else{record("EQ",p,nullptr,nullptr,a,b);}
 EXPECT_EQ(a,b);
}'''))
mod('tools/inventory.py',lambda s:s.replace("r'\\bstatic_assert\\s*\\('","r'\\b(?:static_assert|BLI_STATIC_ASSERT)\\s*\\('"))
