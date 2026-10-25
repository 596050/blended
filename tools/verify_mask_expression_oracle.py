#!/usr/bin/env python3
"""Supplemental exact-mask and random-input comparison, not upstream case counts.
The reference tape is produced by original C++ in mask_expression.hh. Rust calls
its actual translated helper. Full bytes, absolute indices and input offsets are
compared, within the original constructor's static 2^31 range domain.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
REVIEWED_CASES='84f8039f2797880492b283ab58f9f455cd30ef9b7e97d18b0275813d8a596a23'
ORIGINS=(0,16380,(1<<31)-128)
STRIDES=(1,17)
PROBE=r'''
// Appended only in a diagnostic shadow. Original test/helper bodies unchanged.
pub fn mask_diagnostic_tape()->Vec<u8>{
 fn emit(out:&mut Vec<u8>,v:u64){out.extend_from_slice(&v.to_le_bytes());}
 let mut out=b"MASKORC2".to_vec();emit(&mut out,50);let mut rng=BlenderRng::new(0);
 for _ in 0..50{
  let size=(rng.get_int32()%200000+1) as usize;emit(&mut out,size as u64);
  for _ in 0..3{let values=random_bools(&mut rng,size);out.extend(values.into_iter().map(u8::from));}
 }
 emit(&mut out,3*2*64*64);
 for origin in [0_i64,16380,(1_i64<<31)-128]{for stride in [1_i64,17]{
  for abits in 0..64{for bbits in 0..64{
   let cbits=((abits*17)^(bbits*31))&63;
   for value in [origin,stride,abits as i64,bbits as i64,cbits as i64]{emit(&mut out,value as u64);}
   let build=|bits:i32|IndexMask::from_indices((0..6).filter(|i|bits&(1<<i)!=0).map(|i|origin+i*stride));
   let a=build(abits);let b=build(bbits);let c=build(cbits);let universe=build(63);let builder=ExprBuilder::new();
   let mut write_mask=|mask:IndexMask|{
    let mut bits=0_u64;for i in 0..6{if mask.contains(origin+i*stride){bits|=1_u64<<i;}}
    emit(&mut out,mask.len() as u64);emit(&mut out,bits);
    for index in mask.iter(){emit(&mut out,index as u64);}
   };
   write_mask(builder.merge([(&a).into(),(&b).into(),(&c).into()]).evaluate());
   write_mask(builder.intersect([(&a).into(),(&b).into()]).evaluate());
   write_mask(builder.subtract((&a).into(),[(&b).into(),(&c).into()]).evaluate());
   write_mask(a.complement(&universe));write_mask(a.complement(&b));
   write_mask(builder.subtract(builder.merge([(&a).into(),(&b).into()]),[builder.intersect([(&b).into(),(&c).into()])]).evaluate());
  }}
 }}
 out
}
use std::cell::RefCell;
thread_local!{static MASK_ORACLE_OUT:RefCell<Vec<u8>>=const{RefCell::new(Vec::new())};}
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_oracle_run()->usize{let bytes=mask_diagnostic_tape();let n=bytes.len();MASK_ORACLE_OUT.with(|out|*out.borrow_mut()=bytes);n}
#[unsafe(no_mangle)]pub extern "C" fn blended_mask_oracle_ptr()->*const u8{MASK_ORACLE_OUT.with(|out|out.borrow().as_ptr())}
'''
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def command(args,cwd,log,stdout=None):
 if stdout:
  with stdout.open('wb') as out:p=subprocess.run(args,cwd=cwd,stdout=out,stderr=subprocess.PIPE,timeout=240)
  log.write_bytes(p.stderr)
 else:
  p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240);log.write_bytes(p.stdout)
 if p.returncode:raise RuntimeError('Diagnostic command failed, not equivalence: '+str(args))
def read_mask_observation(number,origin,stride,expected_bits):
 size,bits=number(),number()
 if bits!=expected_bits or size!=expected_bits.bit_count():raise ValueError('Observed set differs from independent truth-table result')
 values=[number() for _ in range(size)]
 expected=[origin+i*stride for i in range(6) if expected_bits&(1<<i)]
 if values!=expected:raise ValueError('Absolute selected indices differ from the independent input positions')
 return size

def inspect_tape(path):
 with Path(path).open('rb') as f:
  if f.read(8)!=b'MASKORC2':raise ValueError('Wrong tape identity')
  def number():
   raw=f.read(8)
   if len(raw)!=8:raise ValueError('Truncated tape')
   return struct.unpack('<Q',raw)[0]
  if number()!=50:raise ValueError('Original randomized loop changed')
  sizes=[]
  for _ in range(50):
   size=number()
   if not 1<=size<=200000:raise ValueError('Invalid original random length')
   values=f.read(3*size)
   if len(values)!=3*size or any(v>1 for v in values):raise ValueError('Invalid or omitted fixture bytes')
   sizes.append(size)
  count=number()
  if count!=24576:raise ValueError('Supplemental configuration count changed')
  observations=selected_values=0
  # Validate independently of the expression implementation and trace codec.
  for origin in ORIGINS:
   for stride in STRIDES:
    for a in range(64):
     for b in range(64):
      c=((a*17)^(b*31))&63
      if [number() for _ in range(5)]!=[origin,stride,a,b,c]:raise ValueError('Supplemental absolute input configuration changed')
      expected=(a|b|c,a&b,a&~b&~c,63&~a,b&~a,(a|b)&~(b&c))
      for result in expected:
       selected_values+=read_mask_observation(number,origin,stride,result);observations+=1
  if f.read(1):raise ValueError('Unaccounted output bytes')
 return dict(mask_origins=list(ORIGINS),mask_strides=list(STRIDES),original_static_range_limit=1<<31,rust_above_reference_limit_certified=False,random_iterations=50,random_lengths=sizes,random_boolean_values=sum(sizes)*3,mask_configurations=count,mask_results=observations,configuration_words=count*5,mask_count_and_membership_words=observations*2,absolute_selected_index_values=selected_values)
def equal_bytes(a,b):
 if a.stat().st_size!=b.stat().st_size:raise ValueError('Truncated/extra diagnostic output')
 with a.open('rb') as x,b.open('rb') as y:
  offset=0
  while chunk:=x.read(1024*1024):
   other=y.read(len(chunk))
   if chunk!=other:
    at=next(i for i,(p,q) in enumerate(zip(chunk,other)) if p!=q)
    raise ValueError('Original/replacement data mismatch at byte '+str(offset+at))
   offset+=len(chunk)
 return offset

def build(output):
 from playwright.sync_api import sync_playwright
 output=output.resolve();output.mkdir(parents=True,exist_ok=True)
 target=ROOT/'crates/blended-core/src/mask_expression_cases.rs'
 if sha(target)!=REVIEWED_CASES:raise ValueError('Original translated cases changed before diagnostic execution')
 report={'status':'failed','complete_blender_test_port':False,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'unchanged_test_sha256':sha(target),'mode':'local diagnostic Rust/Chromium; original C++ and public URL verification are separate'}
 try:
  with tempfile.TemporaryDirectory(prefix='blended-mask-oracle-') as name:
   root=Path(name)
   for part in ['crates','Cargo.toml','Cargo.lock','rust-toolchain.toml']:
    p=ROOT/part
    if p.is_dir():shutil.copytree(p,root/part)
    else:shutil.copyfile(p,root/part)
   with (root/'crates/blended-core/src/mask_expression_cases.rs').open('a') as f:f.write(PROBE)
   (output/'probe.rs').write_text(PROBE)
   examples=root/'crates/blended-core/examples';examples.mkdir(exist_ok=True)
   (examples/'mask_oracle.rs').write_text('use std::io::Write;fn main(){std::io::stdout().write_all(&blended_core::mask_expression_cases::mask_diagnostic_tape()).unwrap();}\n')
   native=output/'mask-native.bin';browser_path=output/'mask-browser.bin'
   command(['cargo','run','--locked','--release','--quiet','-p','blended-core','--example','mask_oracle'],root,output/'native-build.log',stdout=native)
   expected=inspect_tape(native)
   command(['cargo','build','--locked','--release','--target','wasm32-unknown-unknown','-p','blended-core'],root,output/'wasm-build.log')
   wasm=root/'target/wasm32-unknown-unknown/release/blended_core.wasm'
   with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    length=page.evaluate('''async data=>{const{instance}=await WebAssembly.instantiate(Uint8Array.from(atob(data),c=>c.charCodeAt(0)),{});const w=instance.exports,n=w.blended_mask_oracle_run(),ptr=w.blended_mask_oracle_ptr();window.__maskOracle={w,n,ptr};return n;}''',base64.b64encode(wasm.read_bytes()).decode())
    if length!=native.stat().st_size:raise ValueError('Unexpected browser tape length')
    with browser_path.open('wb') as sink:
     for offset in range(0,length,262144):
      count=min(262144,length-offset)
      encoded=page.evaluate('''({offset,count})=>{const{w,n,ptr}=window.__maskOracle;if(offset+count>n)throw Error('bounds');const v=new Uint8Array(w.memory.buffer,ptr+offset,count);let s='';for(let i=0;i<v.length;i+=8192)s+=String.fromCharCode(...v.subarray(i,i+8192));return btoa(s);}''',dict(offset=offset,count=count))
      raw=base64.b64decode(encoded,validate=True)
      if len(raw)!=count:raise ValueError('Truncated browser transfer')
      sink.write(raw)
    report.update(browser_version=browser.version,browser_errors=errors);browser.close()
    if errors:raise ValueError('Browser errors')
   size=equal_bytes(native,browser_path)
   report.update(status='passed',native_vs_browser='exact_match',original_cpp_comparison='pending separate comparison job',output_bytes=size,native_sha256=sha(native),browser_sha256=sha(browser_path),wasm_sha256=sha(wasm),**expected)
 except Exception as e:
  report['failure']=str(e);(output/'mask-rust-status.json').write_text(json.dumps(report,indent=2)+'\n');raise
 (output/'mask-rust-status.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
def compare(reference,root,output):
 report={'status':'failed','complete_blender_test_port':False,'scope':'supplemental exact original-C++ inputs and absolute selected-index results, not extra Blender cases'}
 try:
  metadata=json.loads((root/'mask-rust-status.json').read_text())
  if metadata['status']!='passed':raise ValueError('Rust/browser probe did not pass')
  expected=inspect_tape(reference)
  for name in ['mask-native.bin','mask-browser.bin']:equal_bytes(reference,root/name)
  report.update(status='passed',source_commit=metadata['source_commit'],reference_commit='94363991e7dcf39e2d70614aa002ab6f67764a5d',original_cpp_vs_native='exact_match',original_cpp_vs_chromium='exact_match',output_sha256=sha(reference),output_bytes=reference.stat().st_size,**expected)
 except Exception as e:report['failure']=str(e);output.write_text(json.dumps(report,indent=2)+'\n');raise
 output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['build','compare']);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--reference',type=Path);parser.add_argument('--root',type=Path);args=parser.parse_args()
 if args.command=='build':build(args.output)
 else:compare(args.reference,args.root,args.output)
