#!/usr/bin/env python3
"""Exact original-C++ comparison of natural ordering and bounded search pointers.

Supplemental corpus, not extra Blender cases. Four unedited source functions are
extracted from the SHA-locked original string.cc. The driver supplies the original
ELEM macro semantics and the C locale, not replacement algorithm expectations.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='cab551c029222178c9e94f997080cadc2f3898aa105ac7e5966c15367e5fbd57'
LIMITS=(0,1,2,3,4,8,32)
def corpus():
 words=[b'',b' ',b'  ',b'.',b'. ',b' .',b'0',b'00',b'000',b'1',b'01',b'001',b'2',b'10',b'A',b'a',b'AA',b'aA',b'ab',b'AB',b'foo.bar',b'foo 1.bar',b'search here',b'EARC',b'earcq',b'\t',b'\n',b'\x7f']
 words.extend(prefix+n for prefix in (b'x',b'X',b'.x',b' x') for n in (b'0',b'1',b'01',b'2',b'10',b'001',b'999'))
 assert len(set(words))==len(words) and all(all(c<128 for c in word) for word in words)
 return '\n'.join(w.hex() or '-' for w in words)+'\n',words

def definition(text,signature):
 if text.count(signature)!=1:raise ValueError('Original function identity changed: '+signature)
 start=text.index(signature);i=text.index('{',start)+1;depth=1
 while depth:
  if i>=len(text):raise ValueError('Unbalanced original function')
  if text[i]=='{':depth+=1
  elif text[i]=='}':depth-=1
  i+=1
 return text[start:i]
CPP=r'''// SPDX-License-Identifier: GPL-2.0-or-later
#include <cctype>
#include <clocale>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <stdexcept>
#define ELEM(a,b,c) (((a)==(b))||((a)==(c)))
namespace blender {
__ORIGINAL_FUNCTIONS__
}
int main(int argc,char**argv){
 if(argc!=2)return 2;std::setlocale(LC_ALL,"C");std::ifstream file(argv[1]);if(!file)return 3;
 std::vector<std::string> words;std::string line;
 while(std::getline(file,line)){std::string word;if(line!="-"){if(line.size()%2)throw std::runtime_error("Bad fixture");for(size_t i=0;i<line.size();i+=2)word.push_back(char(std::stoul(line.substr(i,2),nullptr,16)));}words.push_back(word);}
 bool first=true;std::cout<<'[';
 for(const auto&a:words)for(const auto&b:words){
  if(!first)std::cout<<',';first=false;std::cout<<'['<<blender::BLI_strcasecmp_natural(a.c_str(),b.c_str());
  for(size_t n: {0,1,2,3,4,8,32}){const char*p=blender::BLI_strncasestr(a.c_str(),b.c_str(),n);std::cout<<','<<(p?p-a.c_str():-1);}
  std::cout<<']';
 }
 std::cout<<"]\n";
}
'''
RUST=r'''// SPDX-License-Identifier: GPL-3.0-or-later
use crate::string_ops::{casecmp_natural,ncasestr};
use std::cell::RefCell;
pub fn generate()->String{
 let words:Vec<Vec<u8>>=include_str!("string_oracle_inputs.txt").lines().map(|s|{let mut v=if s=="-"{vec![]}else{(0..s.len()).step_by(2).map(|i|u8::from_str_radix(&s[i..i+2],16).unwrap()).collect::<Vec<_>>()};v.push(0);v}).collect();
 let mut results=Vec::new();
 for a in &words{for b in &words{let mut row=vec![casecmp_natural(a,b) as i64];for n in [0,1,2,3,4,8,32]{let p=ncasestr(a,b,n);let offset=if p.is_null(){-1}else{let base=a.as_ptr() as usize;assert!((p as usize)>=base&&(p as usize)<base+a.len());(p as usize-base) as i64};row.push(offset);}results.push(row);}}
 format!("{:?}",results)
}
thread_local!{static OUTPUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn string_oracle_run()->usize{let s=generate();let n=s.len();OUTPUT.with(|o|*o.borrow_mut()=s.into_bytes());n}
#[unsafe(no_mangle)]pub extern "C" fn string_oracle_ptr()->*const u8{OUTPUT.with(|o|o.borrow().as_ptr())}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args,cwd,log):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,timeout=180);log.write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError('Oracle/probe command failed: '+str(args))
 return p.stdout

def run(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True);text,words=corpus()
 original=ROOT/'.upstream/blender/source/blender/blenlib/intern/string.cc'
 report={'status':'failed','complete_blender_test_port':False,'scope':'supplemental natural-order and bounded-search corpus, not extra upstream tests','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'reference_commit':json.loads((ROOT/'upstream.lock.json').read_text())['upstreams']['blender']['commit'],'original_source_sha256':SOURCE_SHA,'corpus_sha256':hashlib.sha256(text.encode()).hexdigest(),'word_count':len(words),'ordered_pairs':len(words)**2,'natural_comparisons':len(words)**2,'search_offset_comparisons':len(words)**2*len(LIMITS),'search_lengths':list(LIMITS),'locale':'C','corpus_scope':'ASCII including empty, control, case, numeric-prefix and leading-zero inputs'}
 try:
  if sha(original)!=SOURCE_SHA:raise ValueError('Original string source changed')
  raw=original.read_text();functions=[definition(raw,s) for s in ('int BLI_strncasecmp(', 'char *BLI_strncasestr(', 'static int left_number_strcmp(', 'int BLI_strcasecmp_natural(')]
  cpp=CPP.replace('__ORIGINAL_FUNCTIONS__','\n\n'.join(functions));output.with_suffix('.original.cc').write_text(cpp);output.with_suffix('.inputs.txt').write_text(text)
  report['function_sha256']=[hashlib.sha256(f.encode()).hexdigest() for f in functions]
  with tempfile.TemporaryDirectory(prefix='blended-string-oracle-') as d:
   root=Path(d);(root/'original.cc').write_text(cpp);(root/'inputs.txt').write_text(text)
   command(['g++','-std=c++20','-O2',str(root/'original.cc'),'-o',str(root/'original')],root,output.with_suffix('.cpp-build.log'))
   reference=json.loads(command([str(root/'original'),str(root/'inputs.txt')],root,output.with_suffix('.reference.json')))
   if len(reference)!=len(words)**2 or any(len(row)!=1+len(LIMITS) for row in reference):raise ValueError('Incomplete original oracle output')
   report['reference_binary_sha256']=sha(root/'original')
   for name in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
    p=ROOT/name
    if p.is_dir():shutil.copytree(p,root/name)
    else:shutil.copyfile(p,root/name)
   (root/'crates/blended-core/src/string_oracle_inputs.txt').write_text(text);(root/'crates/blended-core/src/string_oracle.rs').write_text(RUST)
   with (root/'crates/blended-core/src/lib.rs').open('a') as f:f.write('\npub mod string_oracle;\n')
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True);(examples/'string_oracle.rs').write_text('fn main(){println!("{}",blended_core::string_oracle::generate());}\n')
   data=command(['cargo','run','--locked','--quiet','-p','blended-core','--example','string_oracle'],root,output.with_suffix('.native.log'));output.with_suffix('.native.json').write_text(data)
   if json.loads(data)!=reference:raise ValueError('Native values or pointer offsets differ from original C++')
   command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output.with_suffix('.wasm-build.log'))
   wasm=(root/'target/wasm32-unknown-unknown/release/blended_core.wasm').read_bytes()
   with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page()
    data=page.evaluate('''async data=>{const {instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports;const n=w.string_oracle_run(),ptr=w.string_oracle_ptr();return new TextDecoder().decode(new Uint8Array(w.memory.buffer,ptr,n));}''',base64.b64encode(wasm).decode());report['browser_version']=browser.version;browser.close()
   output.with_suffix('.browser.json').write_text(data)
   if json.loads(data)!=reference:raise ValueError('Browser values or pointer offsets differ from original C++')
   report.update(status='passed',native='exact_match',browser='exact_match',wasm_sha256=hashlib.sha256(wasm).hexdigest(),mode='diagnostic local C++/Rust/WASM; production public tests are separate')
 except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
