"""Generate a deliberately narrow, source-locked Rust port. Not a general C++ translator."""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[1];UP=ROOT/'.upstream/blender'
FILES=['BLI_math_base_test.cc','BLI_math_base_safe_test.cc','BLI_math_bits_test.cc','BLI_math_solvers_test.cc','BLI_math_time_test.cc']
SOURCE_SHA256={'BLI_math_base_test.cc':'afffefc44fbf4f8591ac97ede6958f0bff157c684116b07e63d66a0981581a8e','BLI_math_base_safe_test.cc':'c31be0d9964e56534459d8007f6a3343c3aef016ea370cfd5ee953401c6d3b78','BLI_math_bits_test.cc':'344cadb1445fd5f4c92dd848c919ee518f0265d1fcef2c4829ee0e213c0f502e','BLI_math_solvers_test.cc':'352bfa9b6384039123f872ab5b7ef6d4908b66b3e8de44f720b6663dc9197c08','BLI_math_time_test.cc':'a313532d82a278d570f44e1fae37895d9e8da4f1767f9d92cdb0f49f81bc3f76'}
HEAD='''// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Literal inputs, expected results and assertion types from five pinned Blender files.
// See compatibility/additional-ports.json. Not whole-application parity.
#![allow(non_snake_case, unused_mut, unused_parens, clippy::excessive_precision)]
use crate::scalar_math as m;
#[derive(Debug, Default)]
pub struct Report { pub assertions: u32, pub failures: Vec<String> }
impl Report {
    fn check(&mut self, ok: bool, expression: &str, line: u32) {
        self.assertions += 1;
        if !ok { self.failures.push(format!("line {line}: {expression}")); }
    }
    pub fn passed(&self) -> bool { self.assertions > 0 && self.failures.is_empty() }
}
fn equal<T: PartialEq>(a: T, b: T) -> bool { a == b }
fn float_equal(a: f32, b: f32) -> bool {
    if a.is_nan() || b.is_nan() { return false; }
    fn ordered(x: f32) -> u32 {
        let bits=x.to_bits();
        if bits & 0x80000000 != 0 { (!bits).wrapping_add(1) } else { bits | 0x80000000 }
    }
    ordered(a).abs_diff(ordered(b)) <= 4
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{let a=$a;$r.check(equal(a,$b as _),stringify!($a == $b),line!());}};}
macro_rules! feq {($r:expr,$a:expr,$b:expr)=>{{$r.check(float_equal($a as f32,$b as f32),stringify!($a ~= $b),line!());}};}
macro_rules! near {($r:expr,$a:expr,$b:expr,$e:expr)=>{{let (a,b,e)=($a as f64,$b as f64,$e as f64);$r.check((a-b).abs()<=e,stringify!($a ~= $b within $e),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
'''
FLOAT_FUNCS={'compare_ff_relative':(0,1,2),'ulp_diff_ff':(0,1),'ceil_power_of_10':(0,), 'floor_power_of_10':(0,), 'min_f32':(0,1),'step':(0,1),'midpoint':(0,1),'interpolate_i32':(2,), 'floored_fmod':(0,1),'mod_periodic_f32':(0,1),'safe_powf':(0,1),'safe_modf':(0,1),'safe_logf':(0,1)}
def split_args(s):
    out=[];start=depth=0
    for i,c in enumerate(s):
        if c in '([{':depth+=1
        elif c in ')]}':depth-=1
        elif c==',' and depth==0:out.append(s[start:i].strip());start=i+1
    out.append(s[start:].strip());return out

def expr(s):
    s=s.strip().replace('std::numeric_limits<int>::max()', 'i32::MAX').replace('std::numeric_limits<int>::min()', 'i32::MIN')
    s=s.replace('sizeof(float)','core::mem::size_of::<f32>()').replace('sizeof(int)','core::mem::size_of::<i32>()')
    s=s.replace('FLT_EPSILON','f32::EPSILON').replace('INFINITY','f32::INFINITY').replace('NAN','f32::NAN')
    s=s.replace('math::mod_periodic<int64_t>', 'mod_periodic_i64')
    s=s.replace('math::mod_periodic', 'mod_periodic_f32' if re.search(r'\d(?:[.e0-9+-]*f)\b',s) else 'mod_periodic_i32')
    for a,b in [('math::min','min_f32'),('math::clamp','clamp_i32'),('math::step','step'),('math::midpoint','midpoint'),('math::interpolate','interpolate_i32')]:s=s.replace(a,b)
    s=re.sub(r'(\d+(?:\.\d*)?(?:e[+-]?\d+)?)[fF]\b',lambda m:(m[1]+'0' if m[1].endswith('.') else m[1])+'_f32',s)
    s=re.sub(r'\b(\d+)\.(?!\d)',r'\1.0',s)
    # Unsuffixed C++ hex literals above INT_MAX select unsigned int.
    # Rust defaults these to i32 before an `as _` cast, so preserve their source type.
    s=re.sub(r'\b0x[0-9a-fA-F]+\b',lambda m:m[0]+'_u32' if 0x7fffffff<int(m[0],16)<=0xffffffff else m[0],s)
    match=re.fullmatch(r'(\w+)\((.*)\)',s,re.S)
    if match:
        name,args=match[1],split_args(match[2])
        if name in FLOAT_FUNCS:args=[f'({v}) as f32' if i in FLOAT_FUNCS[name] else v for i,v in enumerate(args)]
        s='m::'+name+'('+', '.join(args)+')'
    return s

def extract(text):
    for mo in re.finditer(r'\bTEST\((\w+),\s*(\w+)\)\s*\{',text):
        start=mo.end();depth=1;i=start
        while depth:
            if text[i]=='{':depth+=1
            elif text[i]=='}':depth-=1
            i+=1
        yield mo[1]+'.'+mo[2],mo[2],text[start:i-1],text.count('\n',0,mo.start())+1

def main():
    out=HEAD;cases=[];native='// SPDX-License-Identifier: Apache-2.0\n'
    for filename in FILES:
        path='source/blender/blenlib/tests/'+filename;raw=(UP/path).read_bytes();text=raw.decode()
        if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256[filename]:raise ValueError('Pinned source changed: '+filename)
        for identity,name,body,line in extract(text):
            fn=identity.replace('.','__');clean=re.sub(r'/\*.*?\*/|//[^\n]*','',body,flags=re.S)
            assertions=len(re.findall(r'\bEXPECT_[A-Z_]+\s*\(',clean))
            if filename in FILES[:2]:
                lines=[]
                for stmt in clean.split(';'):
                    stmt=stmt.strip()
                    if not stmt:continue
                    mo=re.fullmatch(r'(?:const )?float (\w+)\s*=\s*(.*)',stmt,re.S)
                    if mo:lines.append(f'let {mo[1]}: f32 = {expr(mo[2])};');continue
                    mo=re.fullmatch(r'EXPECT_(TRUE|FALSE|EQ|FLOAT_EQ|NEAR)\((.*)\)',stmt,re.S)
                    if not mo:raise ValueError((filename,stmt))
                    macro={'TRUE':'yes','FALSE':'no','EQ':'eq','FLOAT_EQ':'feq','NEAR':'near'}[mo[1]]
                    lines.append(macro+'!(r, '+', '.join(expr(a) for a in split_args(mo[2]))+');')
                code='\n'.join(lines)
            elif filename==FILES[2] and name=='BitscanReverseClearUint':
                code=clean.replace('uint a =','let mut a: u32 =').replace('bitscan_reverse_clear_uint(&a)','m::bitscan_reverse_clear_uint(&mut a)')
                code=re.sub(r'EXPECT_EQ\((.*?),\s*([^,;]+)\)',r'eq!(r, \1, \2)',code)
            elif filename==FILES[2]:
                code='''{
 eq!(r,m::count_bits_i(0),0); eq!(r,m::count_bits_uint64(0),0);
}
{
 let value:i32=(1<<0)|(1<<5)|(1<<7);
 let count_32=m::count_bits_i(value); let count_64=m::count_bits_uint64(value as u64);
 eq!(r,count_32,3);eq!(r,count_64,3);
}
{
 let value:u64=(1u64<<0)|(1u64<<50);let count=m::count_bits_uint64(value);eq!(r,count,2);
}
{let value:i32=-1;let count=m::count_bits_i(value);eq!(r,count,32);}
{let value:u64=u64::MAX;let count=m::count_bits_uint64(value);eq!(r,count,64);}'''
            elif filename==FILES[3]:
                code=re.sub(r'const float (\w+)\[(\d+)\]\s*=\s*\{([^}]+)\};',lambda m:f'let {m[1]}: [f32; {m[2]}] = ['+', '.join(v.strip()+'.0' for v in m[3].split(','))+'];',clean)
                code=re.sub(r'float (\w+)\[(\d+)\];',r'let mut \1 = [0.0_f32; \2];',code)
                code=code.replace('BLI_tridiagonal_solve_cyclic(a, b, c, d, x,','m::tridiagonal_solve_cyclic(&a, &b, &c, &d, &mut x,').replace('BLI_tridiagonal_solve(a, b, c, d, x,','m::tridiagonal_solve(&a, &b, &c, &d, &mut x,')
                code=code.replace('EXPECT_TRUE(', 'yes!(r, ').replace('EXPECT_FLOAT_EQ(', 'feq!(r, ')
            else:
                code='''let seconds:f64=2.0*86400.0+13.0*3600.0+33.0*60.0+9.0+369.0*0.001;
let epsilon=1e-8_f64;
let t=m::seconds_decompose(seconds,[true,true,true,true,true]);
near!(r,2.0,t[0],epsilon); near!(r,13.0,t[1],epsilon); near!(r,33.0,t[2],epsilon); near!(r,9.0,t[3],epsilon); near!(r,369.0,t[4],epsilon);
let t=m::seconds_decompose(seconds,[false,true,true,true,false]);
near!(r,61.0,t[1],epsilon); near!(r,33.0,t[2],epsilon); near!(r,9.369,t[3],epsilon);
let t=m::seconds_decompose(seconds,[false,false,false,true,false]);
near!(r,seconds,t[3],epsilon);
let t=m::seconds_decompose(seconds,[true,false,true,false,true]);
near!(r,2.0,t[0],epsilon); near!(r,813.0,t[2],epsilon); near!(r,9369.0,t[4],epsilon);'''
            generated=len(re.findall(r'\b(?:eq|feq|near|yes|no)!',code))
            if assertions!=generated:raise ValueError((name,assertions,generated))
            out+=f'\n// {path}:{line}\npub fn {fn}() -> Report {{\nlet mut r=Report::default();\n{code}\nr\n}}\n'
            native+=f'#[test]\n#[allow(non_snake_case)]\nfn {fn}() {{ let r=blended_core::additional_cases::{fn}(); assert!(r.passed(),"{{r:?}}"); }}\n'
            cases.append(dict(id=identity,path=path,line=line,source_sha256=hashlib.sha256(raw).hexdigest(),body_sha256=hashlib.sha256(body.encode()).hexdigest(),assertion_count=assertions,rust_function=fn,assertion_policy='exact EXPECT_EQ, four-ULP EXPECT_FLOAT_EQ, original EXPECT_NEAR; nonfatal assertions collected',port_status='translated',execution='not_run'))
    out+='\npub const CASES: &[(&str,fn()->Report)] = &[\n'+''.join(f'("{c["id"]}",{c["rust_function"]}),\n' for c in cases)+'];\n'
    (ROOT/'crates/blended-core/src/additional_cases.rs').write_text(out)
    (ROOT/'crates/blended-core/tests/upstream_additional.rs').write_text(native)
    (ROOT/'compatibility/additional-ports.json').write_text(json.dumps(dict(schema=1,upstream_commit='94363991e7dcf39e2d70614aa002ab6f67764a5d',cases=cases,selected_source_cases_mapped=True,complete_blender_test_port=False),indent=2)+'\n')
    for f in FILES:
        dest=ROOT/'tests/upstream/blender'/f;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((UP/'source/blender/blenlib/tests'/f).read_bytes())
    print(len(cases),'cases',sum(c['assertion_count'] for c in cases),'assertions')
if __name__=='__main__':main()
