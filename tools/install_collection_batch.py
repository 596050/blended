"""One-shot, fail-closed integration of the reviewed collection-port batch.
The bootstrap job removes this installer after committing its output.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE={
 'tools/port_workbench.py':'868662216426a9ba2ba70b19b714662bacf6d110a166c358f1c697f09ec513e8',
 'tools/test_port_audit.py':'9130600f1c602d995906344646e7eab49fab22779f37ed6d1107e9208d65a6c9',
 'tools/assertion_fidelity.py':'8199aa1ac83087e1c46284cfdc1ca729eed9f2d820dca55f30da82462567b58d',
 'tools/fidelity/trace.hh':'7baf6fd7cd7785f7f57e8e7ddf10d7b875d8ef1185aa4948d939065b4bef0b79',
 'tools/fidelity/trace.rs':'1adae8481349cdcb222114dbedf096cede13b0f013f1fe1217a6ffa539a17ca5',
 'tests/test_port_workbench.py':'3d37fccd8cef00b68cdff555f1edd4af474aa50710969382f876f3dee23d4115',
}
def replace(text,old,new,count=1):
    if text.count(old)!=count:raise ValueError('Unexpected migration context: '+old[:120])
    return text.replace(old,new)
def install(root=ROOT,workflows=True):
    for name,sha in BASE.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:raise ValueError('Migration base changed: '+name)
    manifest=json.loads((root/'compatibility/collection-ports.json').read_text())
    target='crates/blended-core/src/collection_cases.rs'
    digest=hashlib.sha256((root/target).read_bytes()).hexdigest()
    if digest!='8c0523d5297b0f8b2114e3c5ff0b77e738a7a9944dfc08c591a3d5db5b6dd572':raise ValueError('Unreviewed generated assertion code')
    if len(manifest['cases'])!=32 or sum(c['expected_runtime_assertions'] for c in manifest['cases'])!=521:raise ValueError('Wrong new case universe')
    contract_path=root/'compatibility/assertion-contracts.lock.json';contracts=json.loads(contract_path.read_text())
    for path in dict.fromkeys(c['path'] for c in manifest['cases']):
        selected=[c for c in manifest['cases'] if c['path']==path]
        if any(c['source_path']==path for c in contracts['contracts']):raise ValueError('Already registered')
        contracts['contracts'].append({'source_path':path,'source_sha256':selected[0]['source_sha256'],'target_path':target,'target_sha256':digest,'case_ids':[c['id'] for c in selected],'assertion_sites':sum(c['assertion_count'] for c in selected),'runtime_assertions':sum(c['expected_runtime_assertions'] for c in selected),'adapter_review':'Original loops, comparison kinds and values retained. Shared Cell bit references, independent clones, empty moved-from state, checked word-address identity, fixed builder capacity and borrowed slices are explicit API adapters.'})
    static_target='crates/blended-core/src/compile_time_cases.rs'
    static_sha=hashlib.sha256((root/static_target).read_bytes()).hexdigest()
    if static_sha!='5d67387a38444edb1e1fadce6f48abd84899c5c9eecfab07138920844471193e':raise ValueError('Unreviewed compile-time port')
    static={'id':'static_assert@219','path':'source/blender/blenlib/tests/BLI_math_vector_test.cc','line':219,'kind':'static_assert','source_sha256':'b52b9c6cb1d46b9f6c35cd6dbcdeccba9641c4649cf3fbe4f6bbd62c6107da51','assertion_count':1,'rust_function':'VECTOR_SIGNED_ZERO_HASH','port_status':'translated','execution':'not_run','execution_mode':'native and wasm compiler const evaluation; not a runtime case'}
    (root/'compatibility/compile-time-ports.json').write_text(json.dumps({'upstream_commit':manifest['upstream_commit'],'cases':[static],'complete_blender_test_port':False},indent=2)+'\n')
    contracts['contracts'].append({'source_path':static['path'],'source_sha256':static['source_sha256'],'target_path':static_target,'target_sha256':static_sha,'case_ids':[static['id']],'assertion_sites':1,'runtime_assertions':0,'adapter_review':'Original signed-zero vector hash comparison evaluated as a Rust constant in native and wasm builds; independent negative compiler test rejects raw signed-zero hashing.'})
    contract_path.write_text(json.dumps(contracts,indent=2)+'\n')
    p=root/'crates/blended-core/src/lib.rs';s=p.read_text()
    if 'pub mod hashing;' in s:raise ValueError('Already installed')
    p.write_text(s+'\npub mod hashing;\npub mod compile_time_cases;\n')
    p=root/'tools/test_port_audit.py';s=p.read_text();s=replace(s,"('structure-ports.json','crates/blended-core/src/structure_cases.rs','upstream_structures'),","('structure-ports.json','crates/blended-core/src/structure_cases.rs','upstream_structures'),\n        ('collection-ports.json','crates/blended-core/src/collection_cases.rs','upstream_collections'),\n        ('compile-time-ports.json','crates/blended-core/src/compile_time_cases.rs','compile_time_cases'),")
    p.write_text(s)
    p=root/'tools/port_workbench.py';s=p.read_text()
    s=replace(s,"const groups=['legacy','additional','structures'];","const groups=['legacy','additional','structures','collections'];")
    s=replace(s,'structure_assertions:0,cases:[]','structure_assertions:0,collection_assertions:0,cases:[]')
    s=replace(s,'w.blended_structures_assertion_count]};','w.blended_structures_assertion_count],collections:[w.blended_collections_case_count,w.blended_collections_run_case,w.blended_collections_assertion_count]};')
    s=replace(s,"if(c.group==='structures')result.structure_assertions+=assertions;","if(c.group==='structures')result.structure_assertions+=assertions;\n   if(c.group==='collections')result.collection_assertions+=assertions;")
    s=replace(s,"('structure-ports.json','structures')]:","('structure-ports.json','structures'),('collection-ports.json','collections')]:")
    s=replace(s,"('structures','structure_assertions')]:","('structures','structure_assertions'),('collections','collection_assertions')]:")
    s=replace(s,"'structures':structures['cases'],'complete_test_port'","'structures':structures['cases'],'collections':json.loads((ROOT/'compatibility/collection-ports.json').read_text())['cases'],'complete_test_port'")
    p.write_text(s)
    p=root/'tests/test_port_workbench.py';s=p.read_text().replace("'structure_assertions':8,","'structure_assertions':8,'collection_assertions':0,")
    s=replace(s,'self.assertEqual(len(cases),99)','self.assertEqual(len(cases),131)');p.write_text(s)
    p=root/'tools/assertion_fidelity.py';s=p.read_text()
    s=replace(s,'data=contracts(root);records=[]','data=contracts(root);records=[];seen=set()')
    s=replace(s,"    for c in data['contracts']:\n        p=upstream/c['source_path'];before=p.read_text()","    for c in data['contracts']:\n        if c['source_path'] in seen:continue\n        seen.add(c['source_path'])\n        p=upstream/c['source_path'];before=p.read_text()")
    s=replace(s,"['additional_cases.rs','structure_cases.rs']:","['additional_cases.rs','structure_cases.rs','collection_cases.rs']:")
    s=replace(s,"    if value.startswith('i:'):return Fraction(int(value[2:]))","    if value.startswith('p64:'):return ('word_pointer',int(value[4:]))\n    if value.startswith('i:'):return Fraction(int(value[2:]))")
    p.write_text(s)
    p=root/'tools/fidelity/trace.hh';s=p.read_text();s=replace(s,'#include <cstdlib>','#include "BLI_bit_ref.hh"\n#include "BLI_span.hh"\n#include <cstdint>\n#include <cstdlib>')
    additions=r'''// Address values are compared as word offsets within this pointer-only test.
inline void pointer_value(std::ostream &out,const uint64_t *v) {
 static const ::testing::TestInfo *last=nullptr;static std::uintptr_t base=0;
 const auto *test=::testing::UnitTest::GetInstance()->current_test_info();
 const auto address=reinterpret_cast<std::uintptr_t>(v);
 if(last!=test){last=test;base=address;}
 const auto difference=static_cast<int64_t>(address)-static_cast<int64_t>(base);
 if(difference%int64_t(sizeof(uint64_t)))std::abort();
 out<<"\"p64:"<<difference/int64_t(sizeof(uint64_t))<<"\"";
}
template<> struct Encoder<uint64_t*> {static void write(std::ostream &out,uint64_t *v){pointer_value(out,v);}};
template<> struct Encoder<const uint64_t*> {static void write(std::ostream &out,const uint64_t *v){pointer_value(out,v);}};
template<> struct Encoder<blender::bits::BitRef> {
 static void write(std::ostream &out,const blender::bits::BitRef &v){value(out,bool(v));}
};
template<class T> struct Encoder<blender::Span<T>> {
 static void write(std::ostream &out,const blender::Span<T> &v){out<<'[';for(int64_t i=0;i<v.size();++i){if(i)out<<',';value(out,v[i]);}out<<']';}
};
'''
    s=replace(s,'inline std::ofstream &stream() {',additions+'inline std::ofstream &stream() {');p.write_text(s)
    p=root/'tools/fidelity/trace.rs';s=p.read_text()
    additions=r'''thread_local! {static POINTER_ORIGIN:RefCell<Option<usize>>=const{RefCell::new(None)};}
impl Value for *const core::cell::Cell<u64> {
 fn encode(&self)->String {POINTER_ORIGIN.with(|origin|{
  let address=*self as usize;let mut origin=origin.borrow_mut();let base=*origin.get_or_insert(address);
  let delta=address as i128-base as i128;let size=core::mem::size_of::<core::cell::Cell<u64>>() as i128;
  assert_eq!(delta%size,0);format!("\"p64:{}\"",delta/size)
 })}
}
impl<T:Value> Value for &[T] {fn encode(&self)->String{format!("[{}]",self.iter().map(Value::encode).collect::<Vec<_>>().join(","))}}
'''
    s=replace(s,'pub fn record(kind:&str',additions+'pub fn record(kind:&str')
    s=replace(s,'fn start(id:&str){TAPE.with(|t|t.borrow_mut().0=id.into());}','fn start(id:&str){TAPE.with(|t|t.borrow_mut().0=id.into());POINTER_ORIGIN.with(|p|*p.borrow_mut()=None);}')
    s=replace(s,' TAPE.with(|t|t.borrow().1.clone())',' for (id,run,count) in crate::collection_cases::CASES{start(id);let r=run();assert!(r.passed(),"Collection port failed");assert_eq!(r.assertions,*count);}\n TAPE.with(|t|t.borrow().1.clone())')
    p.write_text(s)
    if workflows:
        p=root/'.github/workflows/test-port-conformance.yml';s=p.read_text()
        s=replace(s,'quality/assertion-fidelity, main]','quality/assertion-fidelity, compat/collections-fidelity, main]')
        s=replace(s,"'tools/port_structure_tests.py',","'tools/port_structure_tests.py', 'tools/port_collection_tests.py', 'tools/verify_static_port.py', 'tests/test_collection_port.py',")
        s=replace(s,'          python3 tools/port_structure_tests.py\n','          python3 tools/port_structure_tests.py\n          python3 tools/port_collection_tests.py\n',2)
        s=replace(s,'compatibility/structure-ports.json tests/upstream','compatibility/structure-ports.json crates/blended-core/src/collection_cases.rs crates/blended-core/tests/upstream_collections.rs compatibility/collection-ports.json tests/upstream')
        s=replace(s,"          assert len(ports)==len(expected)==99 and all(p['semantics_reviewed'] for p in ports), 'Reviewed assertion contract changed; do not publish'\n          assert {p['id'] for p in ports}=={p['id'] for p in expected}, 'Audit and executable registries diverged'","          runtime_ports=[p for p in ports if p.get('kind')!='static_assert']\n          static_ports=[p for p in ports if p.get('kind')=='static_assert']\n          assert len(runtime_ports)==len(expected)==131 and len(static_ports)==1 and all(p['semantics_reviewed'] for p in ports), 'Reviewed contract changed'\n          assert {p['id'] for p in runtime_ports}=={p['id'] for p in expected}, 'Runtime registry mismatch'")
        s=replace(s,'          python3 -m unittest discover -s tests -v','          python3 -m unittest discover -s tests -v\n          python3 tools/verify_static_port.py --output evidence/static-port.json')
        s=replace(s,'            compatibility/structure-ports.json\n','            compatibility/structure-ports.json\n            compatibility/collection-ports.json\n            compatibility/compile-time-ports.json\n            crates/blended-core/src/collection_cases.rs\n            crates/blended-core/tests/upstream_collections.rs\n')
        s=replace(s,'Publish 99-case Blender conformance subset','Publish 131-case Blender conformance subset')
        p.write_text(s)
if __name__=='__main__':install()
