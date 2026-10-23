"""Materialise a hash-locked, locally tested patch. Never marks reference fidelity complete."""
import hashlib,json,re,subprocess,sys,zlib
from pathlib import Path,PurePosixPath
ROOT=Path.cwd()
DIGEST='b6d9474db9c4084a6418edec9c6cafa623d0a61ef20ad8a5f97dc29a71060914'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(name):
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] not in {'crates','tools','tests','compatibility','evidence'} or '\\' in name:raise ValueError('Invalid path '+name)
 q=ROOT/name
 if any(x.is_symlink() for x in [q,*q.parents] if x!=ROOT.parent):raise ValueError('Symlink path '+name)
 return q
parts=sorted((ROOT/'.port-transfer').glob('part-*'))
if len(parts)!=16:raise ValueError('Incomplete payload')
blob=b''.join(p.read_bytes() for p in parts)
if hashlib.sha256(blob).hexdigest()!=DIGEST:raise ValueError('Transfer checksum mismatch')
d=zlib.decompressobj();raw=d.decompress(blob,2_000_001)
if len(raw)>2_000_000 or not d.eof or d.unused_data or d.unconsumed_tail:raise ValueError('Invalid bounded payload')
data=json.loads(raw)
if data['schema']!=1:raise ValueError('Unsupported schema')
names={f['path'] for f in data['files']}
if len(names)!=len(data['files']):raise ValueError('Duplicate files')
for f in data['files']:
 p=safe(f['path']);expected=f['base_sha256']
 if expected is None:
  if p.exists():raise ValueError('Refusing to replace new path '+f['path'])
 elif not p.is_file() or sha(p)!=expected:raise ValueError('Base source changed '+f['path'])
headers=re.findall(r'^diff --git a/(\S+) b/(\S+)$',data['patch'],re.M)
if {a for a,b in headers}!=names or any(a!=b for a,b in headers):raise ValueError('Patch paths differ')
for args in [['git','apply','--check','-'],['git','apply','-']]:subprocess.run(args,input=data['patch'],text=True,check=True)
for f in data['files']:
 if sha(safe(f['path']))!=f['target_sha256']:raise ValueError('Changed patch result '+f['path'])
for script in data['generators']:
 safe(script);subprocess.run([sys.executable,script],check=True)
for name,expected in data['generated'].items():
 if sha(safe(name))!=expected:raise ValueError('Generator drift '+name)
out=ROOT/'evidence/extended-tdd/transfer-verification.json'
out.write_text(json.dumps({'payload_sha256':DIGEST,'changed_files':len(names),'generated_files':len(data['generated']),'verified_file_hashes':data['files'],'complete_blender_test_port':False,'original_cpp_fidelity_executed':False},indent=2)+'\n')
print('Verified exact transfer and regeneration; original-reference fidelity remains pending')
