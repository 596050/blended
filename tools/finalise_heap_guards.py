#!/usr/bin/env python3
"""One-time, source-hash-guarded updates to subset accounting tests only.

No original Blender assertion, numerical tolerance or reviewed target hash is
changed. The independent locked registry must already contain all 367 cases.
"""
import hashlib
from pathlib import Path
from port_workbench import expected_cases
ROOT=Path(__file__).resolve().parents[1]
ORIGINALS={
 'test_collection_port.py':'f255b3b27c5f85624d84afcb00727b59944bbfc0082cf9948694a6b5ceb25b54',
 'test_extended_port.py':'6176429474f19c58a7fa1944f402daed241f21245de67556d0b23866ce2e898a',
 'test_numeric_types.py':'3dbb550cdba95d285202bbbe694f96e143dcb4c9c3f7fa6f72ddbced2608a1f7',
 'test_geometry_math_port.py':'5a0f23329a1cfa734d115408450c1e7e77b2820c4a1ae73a93531efbc7121f2b',
 'test_port_workbench.py':'df47d78b0e13f211ac98b24d83b9f9ea8210f926241b4f5cdb16bd25fcb4d97a',
 'test_sampling_integration.py':'a15e1921d0467e1c4ffe2c7f7eed8fb53a5e1c1c797c6f5795a069583557f741',
 'test_sampling_port.py':'0c342844c9cf1dee2f11154c22e89f7473e77c937121d39b17a31d0f8ac197bc',
}
def main():
 cases,_=expected_cases()
 assert len(cases)==367 and len({c['id'] for c in cases})==367
 assert sum(c['expected_runtime_assertions'] for c in cases)==33104
 changes=[]
 for name,digest in ORIGINALS.items():
  path=ROOT/'tests'/name;raw=path.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Accounting test baseline changed: '+name)
  before=raw.decode();after=before.replace(',338)',',367)').replace(',16804)',',33104)').replace("['contracts']),25)","['contracts']),28)")
  if name=='test_port_workbench.py':after=after.replace("'curve_assertions':0,","'curve_assertions':0,'heap_assertions':0,")
  if before==after:raise ValueError('Expected explicit accounting update missing: '+name)
  changes.append((path,after))
 for path,after in changes:path.write_text(after)
if __name__=='__main__':main()
