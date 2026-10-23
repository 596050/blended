from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[1]
def change(path,f):
 p=r/path;p.write_text(f(p.read_text()))
assert len(json.loads((r/'compatibility/assertion-contracts.lock.json').read_text())['contracts'])==17
p=r/'tools/port_matrix_type_tests.py';s=p.read_text()
assert s.count('let c_mat_view=m::View::<f32,4,4,4,4>')==1
p.write_text(s.replace('let c_mat_view=m::View::<f32,4,4,4,4>','let c_mat_view=m::ReadView::<f32,4,4,4,4>'))
import port_matrix_type_tests
port_matrix_type_tests.generate(root=r)
assert hashlib.sha256((r/'crates/blended-core/src/matrix_type_cases.rs').read_bytes()).hexdigest()=='3ae78026afdc5ba7cfd5cbb646cb5a504e5b7c0874f9391b39269177e8b15176'
change('tools/inventory.py',lambda s:s.replace('static_assert|BLI_STATIC_ASSERT)', 'static_assert|BLI_STATIC_ASSERT(?:_ALIGN)?)'))
change('tools/test_port_audit.py',lambda s:s.replace("('numerics-text-ports.json'","('matrix-type-ports.json','crates/blended-core/src/matrix_type_cases.rs','upstream_matrix_types'),\n        ('numerics-text-ports.json'")
 .replace("target_path=root/target\n            contract=next", "case_target=case.get('target_path',target)\n            case_module=case.get('target_module',module)\n            target_path=root/case_target\n            contract=next")
 .replace("c['source_path']==case['path'] and c['source_sha256']", "c['source_path']==case['path'] and c['target_path']==case_target and c['source_sha256']")
 .replace("'target_test':module+'::'+case['rust_function']", "'target_test':case_module+'::'+case['rust_function']"))
change('tools/port_workbench.py',lambda s:s.replace("'numerics_text'", "'numerics_text','matrix_types'",1)
 .replace('numerics_text_assertions:0','numerics_text_assertions:0,matrix_type_assertions:0')
 .replace('w.blended_numerics_text_assertion_count]','w.blended_numerics_text_assertion_count],matrix_types:[w.blended_matrix_types_case_count,w.blended_matrix_types_run_case,w.blended_matrix_types_assertion_count]')
 .replace("if(c.group==='numerics_text')result.numerics_text_assertions+=assertions;","if(c.group==='numerics_text')result.numerics_text_assertions+=assertions;\n   if(c.group==='matrix_types')result.matrix_type_assertions+=assertions;")
 .replace("('numerics-text-ports.json','numerics_text')","('numerics-text-ports.json','numerics_text'),('matrix-type-ports.json','matrix_types')")
 .replace("('numerics_text','numerics_text_assertions')","('numerics_text','numerics_text_assertions'),('matrix_types','matrix_type_assertions')")
 .replace("'complete_test_port':False,'wasm_sha256'","'matrix_types':json.loads((ROOT/'compatibility/matrix-type-ports.json').read_text())['cases'],'complete_test_port':False,'wasm_sha256'"))
change('crates/blended-core/src/lib.rs',lambda s:s+'''
pub mod matrix_types;
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_case_count()->u32 {matrix_type_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_run_case(index:u32)->i32 {
 matrix_type_cases::CASES.get(index as usize).map(|(_,run,count)|{let r=run();i32::from(r.passed()&&r.assertions==*count)}).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_assertion_count(index:u32)->u32 {
 matrix_type_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}
''')
m=json.loads((r/'compatibility/matrix-type-ports.json').read_text())
p=r/'compatibility/assertion-contracts.lock.json';d=json.loads(p.read_text())
source='source/blender/blenlib/tests/BLI_math_matrix_types_test.cc'
d['contracts'].append({'source_path':source,'source_sha256':m['source_files']['BLI_math_matrix_types_test.cc'],'target_path':'crates/blended-core/src/matrix_type_cases.rs','target_sha256':hashlib.sha256((r/'crates/blended-core/src/matrix_type_cases.rs').read_bytes()).hexdigest(),'case_ids':[c['id'] for c in m['cases']],'review':'All 21 runtime cases, original expected operands and matrix macro scalar checks preserved. Shared Cell storage retains mutable view aliasing and copy-on-conversion. Original non-running comments are not tests; no SIMD or ABI equivalence asserted.'})
static_path=r/'compatibility/compile-time-ports.json';static=json.loads(static_path.read_text())
assert len(static['cases'])==1
for c in static['cases']:c['runtime_assertions']=0
for file,line,fn,condition,target_text,mut_before,mut_after,error in [
 ('BLI_string_ref_test.cc',106,'string_ref_null__Constexpr',"sref[2] == 'r'", "const _:()=assert!(SREF.byte(2)==b'r');",'b"World\\0",5','b"Woxld\\0",5',"assertion failed: SREF.byte(2) == b'r'"),
 ('BLI_string_ref_test.cc',107,'string_ref_null__Constexpr','sref.size() == 5','const _:()=assert!(SREF.size()==5);','b"World\\0",5','b"Worl\\0",4','assertion failed: SREF.size() == 5'),
 ('BLI_string_ref_test.cc',594,'string_ref__Constexpr',"sref[2] == 'r'", "const _:()=assert!(SREF.byte(2)==b'r');",'b"World",5','b"Woxld",5',"assertion failed: SREF.byte(2) == b'r'"),
 ('BLI_string_ref_test.cc',595,'string_ref__Constexpr','sref.size() == 5','const _:()=assert!(SREF.size()==5);','b"World",5','b"Worl",4','assertion failed: SREF.size() == 5'),
 ('BLI_index_range_test.cc',310,'index_range__constexpr_','range.size() == 1','const _: () = assert!(RANGE.size() == 1);','m::IndexRange::new(1,1)','m::IndexRange::new(1,2)','assertion failed: RANGE.size() == 1')]:
 path='source/blender/blenlib/tests/'+file;source_bytes=(r/'tests/upstream/blender'/file).read_bytes()
 assert condition in source_bytes.decode().splitlines()[line-1],(file,line)
 module='structure_cases' if file=='BLI_index_range_test.cc' else 'numerics_text_cases'
 target='crates/blended-core/src/'+module+'.rs'
 case={'id':f'static_assert@{line}','path':path,'line':line,'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'rust_function':fn,'kind':'static_assert','assertion_count':1,'runtime_assertions':0,'target_path':target,'target_module':module,'embedded':True,'source_condition':condition,'target_assertion':target_text,'negative_fixture_before':mut_before,'negative_fixture_after':mut_after,'negative_error':error,'status':'ported_unexecuted'}
 static['cases'].append(case)
 c=next(c for c in d['contracts'] if c['source_path']==path and c['target_path']==target)
 c['case_ids'].append(case['id'])
static['notes']='One standalone hash invariant and five embedded constant-evaluation assertions. Positive and deliberately invalid fixture builds verified separately on native and wasm32; no runtime count inflation. Other compile-time assertions remain unported.'
static_path.write_text(json.dumps(static,indent=2)+'\n')
p.write_text(json.dumps(d,indent=2)+'\n')
for name in ['tests/test_collection_port.py','tests/test_numerics_text_port.py']:
 change(name,lambda s:s.replace("['contracts']),17","['contracts']),18").replace('len(c),224','len(c),245').replace('len(cases),224','len(cases),245').replace('in c),1499','in c),1788').replace('in cases),1499','in cases),1788').replace("'collection-ports.json','numerics-text-ports.json'","'collection-ports.json','numerics-text-ports.json','matrix-type-ports.json'"))
change('tests/test_port_workbench.py',lambda s:s.replace("'numerics_text_assertions':0","'numerics_text_assertions':0,'matrix_type_assertions':0").replace('len(cases),224','len(cases),245'))
change('tools/assertion_fidelity.py',lambda s:s.replace("'numerics_text_cases.rs']","'numerics_text_cases.rs','matrix_type_cases.rs']").replace("if name=='numerics_text_cases.rs':","if name in ('numerics_text_cases.rs','matrix_type_cases.rs'):"))
change('tools/fidelity/trace.rs',lambda s:s.replace('pub fn record(','''impl<T:Value,const C:usize,const R:usize>Value for crate::matrix_types::M<T,C,R>{fn encode(&self)->String{self.0.encode()}}
pub fn record(''').replace(' TAPE.with(|t|t.borrow().1.clone())',''' for (id,run,count) in crate::matrix_type_cases::CASES{start(id);let r=run();assert!(r.passed(),"Matrix port failed");assert_eq!(r.assertions,*count);}
 TAPE.with(|t|t.borrow().1.clone())'''))
change('tools/fidelity/trace.hh',lambda s:s.replace('#include "BLI_math_vector_types.hh"','#include "BLI_math_vector_types.hh"\n#include "BLI_math_matrix_types.hh"').replace('template<class T> struct Encoder<blender::Bounds<T>>', '''template<class T,int C,int R,int A>struct Encoder<blender::MatBase<T,C,R,A>>{
 static void write(std::ostream &out,const blender::MatBase<T,C,R,A> &v){out<<'[';for(int c=0;c<C;c++){if(c)out<<',';value(out,v[c]);}out<<']';}
};
template<class T> struct Encoder<blender::Bounds<T>>'''))
