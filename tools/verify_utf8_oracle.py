#!/usr/bin/env python3
"""Original C++ decoder/validator and byte-RNG oracle. Supplemental, not test ports."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from verify_heap_inputs import definition
ROOT=Path(__file__).resolve().parents[1]
PIN='94363991e7dcf39e2d70614aa002ab6f67764a5d'
HASHES={'intern/string_utf8.cc':'882da073f7421c63dd5c81a09aed66ae6eb21bcdf3f9c1e098465b846c4ec0f3','intern/rand.cc':'aac6c52e01cf6271419bdbfd47a6ad140912432fd598d8330df82b9a039373f5','BLI_rand.hh':'4226aa1b035ae085f87a3ac1c2467b7f2fc0235c354a5f2553e2cdd5cea82c82'}
SIZES=tuple(range(1,13))+(16,31,32,33)
def corpus():
    result=[b'']+[bytes([a]) for a in range(256)]+[bytes([a,b]) for a in range(256) for b in range(256)]
    for first in range(0xc0,0xfe):
        for second in (0,0x7f,0x80,0x9f,0xa0,0xbf,0xc0,0xff):
            for length in range(3,8):result.append(bytes([first,second]+[0x80]*(length-2)))
    return result

def cpp_source():
    base=ROOT/'.upstream/blender/source/blender/blenlib'
    for name,digest in HASHES.items():
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=digest:raise ValueError('Original source mismatch: '+name)
    text=(base/'intern/string_utf8.cc').read_text();rng=(base/'intern/rand.cc').read_text()
    functions=[definition(text,s) for s in ('BLI_INLINE int utf8_char_compute_skip(', 'BLI_INLINE int utf8_char_compute_skip_or_error_with_mask(', 'BLI_INLINE uint utf8_char_decode(', 'ptrdiff_t BLI_str_utf8_invalid_byte(', 'uint BLI_str_utf8_as_unicode_step_or_error(', 'uint BLI_str_utf8_as_unicode_step_safe(')]
    functions.append(definition(rng,'void RandomNumberGenerator::get_bytes('))
    code='#include "BLI_rand.hh"\n#include "BLI_string_utf8.hh"\n#include "BLI_utildefines.hh"\n#include <fstream>\n#include <iostream>\n#include <vector>\nnamespace blender {\n'+'\n'.join(functions)+'\n}\n'
    code+=r'''
uint32_t read32(std::istream &s){unsigned char b[4];s.read(reinterpret_cast<char*>(b),4);if(!s)std::abort();return uint32_t(b[0])|(uint32_t(b[1])<<8)|(uint32_t(b[2])<<16)|(uint32_t(b[3])<<24);}
int main(int argc,char **argv){if(argc!=2)return 2;std::ifstream input(argv[1],std::ios::binary);const auto count=read32(input);std::cout<<"[\n";
for(uint32_t n=0;n<count;++n){auto len=read32(input);std::vector<char> data(len+1,0);input.read(data.data(),len);if(!input) return 3;if(n)std::cout<<",\n";std::cout<<"["<<blender::BLI_str_utf8_invalid_byte(data.data(),len);size_t index=0;while(index<len&&data[index]!=0){auto value=blender::BLI_str_utf8_as_unicode_step_safe(data.data(),len,&index);std::cout<<","<<value<<","<<index;}std::cout<<"]";}
std::cout<<",[";bool first=true;
'''
    for size in SIZES:code+=f'{{blender::RandomNumberGenerator rng(1);std::vector<char> data({size});for(int i=0;i<256;++i){{rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){{if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}}}}\n'
    code+='std::cout<<"]]\\n";}\n'
    return code,[hashlib.sha256(f.encode()).hexdigest() for f in functions]

def rust_source():
    code='''use crate::utf8_compat as u;
fn read32(data:&[u8],offset:&mut usize)->usize{let n=u32::from_le_bytes(data[*offset..*offset+4].try_into().unwrap()) as usize;*offset+=4;n}
pub fn generate()->String{let data=include_bytes!("utf8_oracle.bin");let mut offset=0;let count=read32(data,&mut offset);let mut rows:Vec<Vec<i64>>=Vec::new();for _ in 0..count{let len=read32(data,&mut offset);let bytes=&data[offset..offset+len];offset+=len;let mut row=vec![u::invalid_byte(bytes,len) as i64];let mut index=0;while index<len&&bytes[index]!=0{let value=u::decode_step_safe(bytes,len,&mut index);row.push(value as i64);row.push(index as i64);}rows.push(row);}assert_eq!(offset,data.len());let mut bytes_out=Vec::new();
'''
    for size in SIZES:code+=f'{{let mut rng=u::LegacyByteRng::new(1);let mut bytes=[0_u8;{size}];for _ in 0..256{{rng.fill(&mut bytes);bytes_out.extend(bytes.iter().map(|&b|b as i64));}}}}\n'
    code+='rows.push(bytes_out);format!("{:?}",rows)}\n'
    code+='use std::cell::RefCell;thread_local!{static OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}\n#[unsafe(no_mangle)]pub extern "C" fn utf8_oracle_run()->usize{let s=generate();let n=s.len();OUT.with(|o|*o.borrow_mut()=s.into_bytes());n}\n#[unsafe(no_mangle)]pub extern "C" fn utf8_oracle_ptr()->*const u8{OUT.with(|o|o.borrow().as_ptr())}\n'
    return code

def command(args,root,log):
    p=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=180);log.write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError('Oracle command failed: '+str(args))
    return p.stdout

def run(output):
    from playwright.sync_api import sync_playwright
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    evidence={'status':'failed','complete_blender_test_port':False,'scope':'supplemental full single/two-byte and bounded legacy decoder corpus, not extra upstream cases','reference_commit':PIN,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_hashes':HASHES}
    try:
        cases=corpus();data=struct.pack('<I',len(cases))+b''.join(struct.pack('<I',len(s))+s for s in cases)
        output.with_suffix('.inputs.bin').write_bytes(data)
        with tempfile.TemporaryDirectory(prefix='blended-utf8-oracle-') as d:
            root=Path(d);src=root/'original.cc';code,function_hashes=cpp_source();src.write_text(code);output.with_suffix('.original.cc').write_text(code)
            base=ROOT/'.upstream/blender'
            command(['g++','-std=c++20','-O2','-DNDEBUG','-funsigned-char','-I'+str(base/'source/blender/blenlib'),'-I'+str(base/'intern/guardedalloc'),str(src),'-o',str(root/'original')],root,output.with_suffix('.cpp-build.log'))
            reference=json.loads(command([str(root/'original'),str(output.with_suffix('.inputs.bin'))],root,output.with_suffix('.reference.json')))
            for name in ('crates','Cargo.toml','Cargo.lock','rust-toolchain.toml'):
                p=ROOT/name
                if p.is_dir():shutil.copytree(p,root/name)
                else:shutil.copyfile(p,root/name)
            (root/'crates/blended-core/src/utf8_oracle.rs').write_text(rust_source());(root/'crates/blended-core/src/utf8_oracle.bin').write_bytes(data)
            with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod utf8_oracle;\n')
            examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);(examples/'utf8_oracle.rs').write_text('fn main(){println!("{}",blended_core::utf8_oracle::generate());}\n')
            native=json.loads(command(['cargo','run','--locked','--quiet','-p','blended-core','--example','utf8_oracle'],root,output.with_suffix('.native.log')))
            if native!=reference:raise ValueError('Native decoder/validator/RNG results differ from original C++')
            command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
            wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes()
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page()
                raw=page.evaluate('''async data=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports,n=w.utf8_oracle_run(),ptr=w.utf8_oracle_ptr();return new TextDecoder().decode(new Uint8Array(w.memory.buffer,ptr,n));}''',base64.b64encode(wasm).decode())
                evidence['browser_version']=browser.version;browser.close()
            output.with_suffix('.browser.json').write_text(raw)
            if json.loads(raw)!=reference:raise ValueError('Browser decoder/validator/RNG results differ from original C++')
            evidence.update(status='passed',native='exact_match',browser='exact_match',byte_sequences=len(cases),all_single_bytes=256,all_two_byte_sequences=65536,legacy_sequences=len(cases)-65793,decoder_codepoint_offset_pairs=sum((len(r)-1)//2 for r in reference[:-1]),validator_results=len(cases),random_byte_blocks=len(SIZES)*256,random_bytes=len(reference[-1]),byte_rng_lengths=list(SIZES),byte_rng_seed=1,corpus_sha256=hashlib.sha256(data).hexdigest(),original_function_hashes=function_hashes,reference_binary_sha256=hashlib.sha256((root/'original').read_bytes()).hexdigest(),wasm_sha256=hashlib.sha256(wasm).hexdigest(),endianness='x86_64/wasm32 little endian; random byte generator remains endian-sensitive',mode='diagnostic local original C++ versus native Rust/Chromium; production public URL tested separately')
    except Exception as e:evidence['failure']=str(e);output.write_text(json.dumps(evidence,indent=2)+'\n');raise
    output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
