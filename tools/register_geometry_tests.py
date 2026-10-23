#!/usr/bin/env python3
"""One-time registration of reviewed geometric-maths translations, not a test pass."""
from pathlib import Path
import hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'tools/port_geometry_math_tests.py';s=p.read_text()
 for old,new in [
  ('SOURCE_LEGACY_SHA','9d03dac9a1a797eade844f588276c114b3dc79241a52830bfbc7323fdc8dc07d'),
  ('SOURCE_MODERN_SHA','6450b2a9c1ac4f54bc1f73f1c9478f77c6b88388438b2e8b384342711ed0f6a4'),
  ("macro+'!(r, '","macro+'!(report, '"),
  ("'fatal_yes!(r, '","'fatal_yes!(report, '"),
  ('let mut r=Report::default();','let mut report=Report::default();'),
  ('{translated}\\nr\\n}}','{translated}\\nreport\\n}}')]:
  if s.count(old)!=1:raise ValueError('Unexpected registration input: '+old)
  s=s.replace(old,new)
 p.write_text(s)
 subprocess.run([sys.executable,str(p)],check=True,cwd=ROOT)
 expected={
 'crates/blended-core/src/geometry_math_cases.rs':'2333ef82a58d7efd859a9499f4d5be113ea48c1e0e9fe436799a0acbbad96afd',
 'crates/blended-core/tests/upstream_geometry_math.rs':'39da2d7a11320e8f25dee572822810aedbab99bd19bcfb9927891fe14d4def86',
 'compatibility/geometry-math-ports.json':'efa128614bf7d63883a9985aa77018fbaa22fd001854952f78ea87a1d7b1e45f'}
 for path,want in expected.items():
  actual=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
  if actual!=want:raise ValueError(f'Prepared test content changed: {path} {actual}')
 print('Thirty reviewed cases registered; implementation and fidelity execution are not yet verified.')
if __name__=='__main__':main()
