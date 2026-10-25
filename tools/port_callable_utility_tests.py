#!/usr/bin/env python3
"""Validate and reproduce the complete pinned callable/iterator/session test batch.

This is a finite source-locked adapter, not a general C++ translator. Unknown
source revisions, identities, assertion counts or translated case registries
fail. The reviewed Rust test bodies are not auto-rewritten here.
"""
from pathlib import Path
import hashlib,json,re,shutil
from port_collection_tests import extract
ROOT=Path(__file__).resolve().parents[1]
PIN="94363991e7dcf39e2d70614aa002ab6f67764a5d"
FILES={
 "BLI_function_ref_test.cc":("source/blender/blenlib/tests/BLI_function_ref_test.cc","1e71ba20e88a316d3b5a9328000d9c3059e3c3ff4411515d5581b2b6841eda1e"),
 "BLI_random_access_iterator_mixin_test.cc":("source/blender/blenlib/tests/BLI_random_access_iterator_mixin_test.cc","c3100113d8b5a14f3f90127b75b2a17b71679b8dabe34ec40e4ad58f89d40034"),
 "BLI_session_uid_test.cc":("source/blender/blenlib/tests/BLI_session_uid_test.cc","5a4634b1119f9176e7459715498befb068456f5135e3d4c848660c0672356fa8"),
}
CASES=[
("function_ref.StatelessLambda",16,"52485d9a26d2e1bd29763a6992e5902ad60d853f9ae25e6fd0154eb1082486f1",1),
("function_ref.StatefullLambda",22,"db0af3c34a15f9ee0d2fe52793e576480eadf9230456e931d6bd5ba3bce294e3",1),
("function_ref.StandaloneFunction",35,"163ed904a503c7ead9f42d09758dc1a4b42bab44c8603601ad512e3a2b98bf26",1),
("function_ref.ConstantFunction",41,"0a2907d58feb86ea2fd8811f1775bd95e82139d725122ae91164751d6d6ea4f0",1),
("function_ref.MutableStatefullLambda",48,"0b258f5f8a0a2a445a067a45be6df1441c75cd9fc44e659380efbfebb272cc5a",3),
("function_ref.Null",58,"a829196ea2322fc10d402c05f9f72177fe02d06513aee3916066a87b1935b280",3),
("function_ref.CopyDoesNotReferenceFunctionRef",71,"968190cc7cfa4d335d09dabaa3b01a428fe794cd533b20d9641e5227177700da",1),
("function_ref.CopyDoesNotReferenceFunctionRef2",81,"b4be617c9c6f44277920dab15500bc824ef1766909a1961d95a7f82de8fe04bb",1),
("function_ref.ReferenceAnotherFunctionRef",92,"89f2eda9ec9392588d976449b6b2de392504877d664bc46cc99fe43926cf1747",2),
("function_ref.InitializeWithNull",104,"62bb4d7ad71123ddfe3988d32a0bdf4346c456e60fc49d3715e9c88efb9742c0",1),
("function_ref.OverloadSelection",120,"af2c88112185bd082e20284de67ea23ad7603ad62b33375a2cb0077f4e8f47a6",2),
("function_ref.FalsyStdFunction",129,"ba790e7c2c378d958357cdf8ea3cfba077a591e80075f3a54f0b2f76f3bf2cfb",4),
("function_ref.FalsyFunctionPointer",144,"ffcafa7dbed810e1750d464fb34d99ace599e1b7d850ec4c085c55aeb844788a",2),
("random_access_iterator_mixin.DoublingIterator",33,"90ea62eb04c7383906e73804b8116b5ce4e57310f923d89d298de20e66223752",5),
("SessionUID.GenerateBasic",11,"45d79cb4dc900ac7db37a5d4d4ef9329d042dc726d84c1aec9d208c2d5b37370",2),
]
def source_for(identity):
 if identity.startswith("function_ref."):return FILES["BLI_function_ref_test.cc"]
 if identity.startswith("random_access_iterator_mixin."):return FILES["BLI_random_access_iterator_mixin_test.cc"]
 return FILES["BLI_session_uid_test.cc"]
def generate(root=ROOT):
 lock=json.loads((root/"upstream.lock.json").read_text())
 if lock["upstreams"]["blender"]["commit"]!=PIN:raise ValueError("Wrong pinned Blender commit")
 observed={}
 for name,(path,digest) in FILES.items():
  source=root/".upstream/blender"/path;raw=source.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("Pinned source changed: "+path)
  shutil.copyfile(source,root/"tests/upstream/blender"/name)
  for identity,body,line in extract(raw.decode()):
   observed[identity]=(line,hashlib.sha256(body.encode()).hexdigest(),len(re.findall(r"\bEXPECT_[A-Z_]+\s*\(",body)))
 expected={identity:(line,body_hash,count) for identity,line,body_hash,count in CASES}
 if observed!=expected:
  missing=set(expected)-set(observed);extra=set(observed)-set(expected)
  raise ValueError(f"Original callable utility case universe changed; missing={missing}, extra={extra}, differences={[(k,observed.get(k),expected.get(k)) for k in expected if observed.get(k)!=expected.get(k)]}")
 target=(root/"crates/blended-core/src/callable_utility_cases.rs").read_text()
 registered=re.findall(r'\("([^"]+)",\s*([A-Za-z0-9_]+),\s*(\d+)\)',target)
 if [(identity,identity.replace(".","__"),str(count)) for identity,_,_,count in CASES]!=registered:
  raise ValueError("Translated executable registry differs from reviewed source universe")
 cases=[]
 for index,(identity,line,body_hash,count) in enumerate(CASES):
  path,digest=source_for(identity)
  cases.append(dict(id=identity,path=path,line=line,kind="TEST",source_sha256=digest,source_body_sha256=body_hash,
                    rust_function=identity.replace(".","__"),assertion_count=count,expected_runtime_assertions=count,index=index,status="ported_unexecuted"))
 manifest=dict(schema=1,upstream_commit=PIN,source_files={name:dict(path=path,sha256=digest) for name,(path,digest) in FILES.items()},
               cases=cases,complete_blender_test_port=False,
               notes="Three complete enabled runtime source files. FunctionRef is non-owning and copied by underlying callable identity. The Rust typed-dispatch adaptation preserves the two overload results but does not claim C++ overload-resolution language equivalence. SessionUID preserves non-zero session uniqueness. Iterator coverage is the exact doubling-iterator behavior exercised upstream.")
 (root/"compatibility/callable-utility-ports.json").write_text(json.dumps(manifest,indent=2)+"\n")
 native="// SPDX-License-Identifier: Apache-2.0\nuse blended_core::callable_utility_cases as c;\nmacro_rules! check {($name:ident,$func:ident,$count:expr)=>{#[test]fn $name(){let r=c::$func();assert!(r.passed(),\"{:?}\",r.failures);assert_eq!(r.assertions,$count);}}}\n"
 for identity,_,_,count in CASES:
  fn=identity.replace(".","__");test=fn.replace("__","_")
  native+=f"check!({test},{fn},{count});\n"
 (root/"crates/blended-core/tests/upstream_callable_utils.rs").write_text(native)
 return cases
if __name__=="__main__":
 cases=generate();print(json.dumps(dict(cases=len(cases),assertion_events=sum(c["expected_runtime_assertions"] for c in cases))))
