#!/usr/bin/env python3
"""One-time registration; reviewed target hash is fixed, never auto-approved in CI."""
from pathlib import Path
import hashlib,json
from port_span_tests import generate,PATH,PIN
ROOT=Path(__file__).resolve().parents[1]
REVIEWED_TARGET_SHA='2ca5f78a2ea21751394c6f41f7a227acb202158fd5ed2a712f3d38e6510b968c'
def replace(path,old,new):
    p=ROOT/path;text=p.read_text()
    if text.count(old)!=1:raise ValueError('Registration baseline changed: '+path)
    p.write_text(text.replace(old,new))
def main():
    lib=ROOT/'crates/blended-core/src/lib.rs'
    if 'pub mod span_cases;' in lib.read_text():raise ValueError('Already registered; do not refresh reviewed hashes')
    cases,statics=generate()
    target='crates/blended-core/src/span_cases.rs'
    if hashlib.sha256((ROOT/target).read_bytes()).hexdigest()!=REVIEWED_TARGET_SHA:raise ValueError('Reviewed span translation changed')
    shard=dict(schema=1,reference_commit=PIN,contracts=[dict(source_path=PATH,source_sha256=cases[0]['source_sha256'],target_path=target,target_sha256=REVIEWED_TARGET_SHA,case_ids=[c['id'] for c in cases]+[c['id'] for c in statics])])
    (ROOT/'compatibility/span-assertion-contract.lock.json').write_text(json.dumps(shard,indent=2)+'\n')
    with lib.open('a') as f:f.write('''
pub mod spans;
pub mod span_cases;
#[unsafe(no_mangle)]pub extern "C" fn blended_spans_case_count()->u32{span_cases::CASES.len() as u32}
#[unsafe(no_mangle)]pub extern "C" fn blended_spans_run_case(index:u32)->i32{span_cases::CASES.get(index as usize).map(|(_,run,n)|{let r=run();i32::from(r.passed()&&r.assertions==*n)}).unwrap_or(-1)}
#[unsafe(no_mangle)]pub extern "C" fn blended_spans_assertion_count(index:u32)->u32{span_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)}
''')
    replace('tools/port_registry.py','\n)\nTOTAL_KEYS=',"\n    Group('spans','span-ports.json','span_cases','upstream_spans','port_span_tests.py','span_assertions',('blended_spans_case_count','blended_spans_run_case','blended_spans_assertion_count')),\n)\nTOTAL_KEYS=")
    replace('tools/contract_registry.py','EXTENSIONS=("compatibility/polyfill-assertion-contract.lock.json",)','EXTENSIONS=("compatibility/polyfill-assertion-contract.lock.json","compatibility/span-assertion-contract.lock.json")')
    replace('tools/test_port_audit.py','from port_registry import GROUPS','from port_registry import GROUPS\nfrom static_port_registry import STATIC_MANIFESTS')
    replace('tools/test_port_audit.py',"('compile-time-ports.json','crates/blended-core/src/compile_time_cases.rs','compile_time_cases')", "*((name,'crates/blended-core/src/compile_time_cases.rs','compile_time_cases') for name in STATIC_MANIFESTS)")
    replace('tools/assertion_fidelity.py',"recording_header='polyfill.hh' if Path(c['source_path']).name=='BLI_polyfill_2d_test.cc' else 'trace.hh'", "recording_header={'BLI_polyfill_2d_test.cc':'polyfill.hh','BLI_span_test.cc':'span.hh'}.get(Path(c['source_path']).name,'trace.hh')")
    replace('tools/assertion_fidelity.py',"'pixel_format_cases.rs','polyfill_cases.rs']:","'pixel_format_cases.rs','polyfill_cases.rs','span_cases.rs']:")
    replace('tools/assertion_fidelity.py','        # Preserve the original scalar EQ expected-value cast.', '''        if name=='span_cases.rs':
            changes['macro_rules! peq ']='macro_rules! peq {($r:expr,$a:expr,$b:expr)=>{{$r.check(crate::fidelity_trace::pointer_pair(($a) as *const u8,($b) as *const u8),stringify!($a pointer-equals $b),line!());}};}'
        # Preserve the original scalar EQ expected-value cast.''')
    replace('tools/fidelity/trace.rs',' TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))',' for (id,run,n) in crate::span_cases::CASES{start(id);let r=run();end(r.passed()&&r.assertions==*n);}\n TAPE.with(|t|core::mem::take(&mut t.borrow_mut().1))')
    # Tighten safe casts: pointer provenance must not be reinterpreted as numeric
    # memory through a safe API. Original tests need only numeric/numeric and
    # pointer/pointer casts; no assertion or expectation changes here.
    replace('crates/blended-core/src/spans.rs', '''    pub trait Bits: Copy {}
    macro_rules! primitive {($($t:ty),*)=>{$(impl Bits for $t {})*};}
    primitive!(i8,u8,i16,u16,i32,u32,i64,u64,isize,usize,f32,f64);
    impl<T> Bits for *const T {}
    impl<T> Bits for *mut T {}''', '''    pub trait Scalar: Copy {}
    pub trait CastTo<U: Copy>: Copy {}
    macro_rules! primitive {($($t:ty),*)=>{$(impl Scalar for $t {})*};}
    primitive!(i8,u8,i16,u16,i32,u32,i64,u64,isize,usize,f32,f64);
    impl<T:Scalar,U:Scalar> CastTo<U> for T {}
    impl<T,U> CastTo<*const U> for *const T {}
    impl<T,U> CastTo<*mut U> for *mut T {}
    impl<T,U> CastTo<*const U> for *mut T {}
    impl<T,U> CastTo<*mut U> for *const T {}''')
    replace('crates/blended-core/src/spans.rs',"impl<'a, T: sealed::Bits> Span<'a, T> {\n    pub fn cast<U: sealed::Bits>(self) -> Span<'a, U> {", "impl<'a, T: Copy> Span<'a, T> {\n    pub fn cast<U: Copy>(self) -> Span<'a, U> where T: sealed::CastTo<U> {")
    from port_workbench import expected_cases
    from static_port_registry import load_static_cases
    current,_=expected_cases()
    assert len(current)==581 and sum(c['expected_runtime_assertions'] for c in current)==3196371
    assert len(load_static_cases(ROOT))==19
    # These are only infrastructure-universe guards. Original expected values,
    # tolerances, case bodies and historical lock files are not rewritten.
    changed=[]
    for path in sorted((ROOT/'tests').glob('test_*.py')):
        before=path.read_text();after=before.replace(',541)',',581)').replace(',3196218)',',3196371)').replace("['contracts']),39)","['contracts']),40)")
        if path.name=='test_port_workbench.py':after=after.replace("'polyfill_assertions':0,","'polyfill_assertions':0,'span_assertions':0,")
        if after!=before:path.write_text(after);changed.append(path.name)
    print(json.dumps(dict(registered_runtime=len(cases),registered_static=len(statics),runtime_assertions=153,total_runtime=len(current),updated_infrastructure_guards=changed)))
if __name__=='__main__':main()
