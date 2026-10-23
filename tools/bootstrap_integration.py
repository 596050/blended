#!/usr/bin/env python3
"""One-time integration of two pinned, previously verified source branches.

Every input and output is hash checked before any file is written. This script
never updates review hashes from newly generated expectations or claims a test pass.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
REFS=('7e6411a031203a4976517575b23ca8e889e9a408','cf2cb3fa4f8814151d7f4ab7efdfb70d2931f920')
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    for ref in REFS:
        subprocess.run(['git','fetch','--no-tags','--depth=1','origin',ref],cwd=ROOT,check=True)
    pending={}
    for part in range(1,5):
        for item in json.loads((ROOT/f'integration/part{part}.json').read_text())['files']:
            path=Path(item['path'])
            if path.is_absolute() or '..' in path.parts or path.parts[0] not in ('NOTICE.md','crates','tools','tests','compatibility'):
                raise ValueError('Unexpected integration path: '+str(path))
            if str(path) in pending:raise ValueError('Duplicate path')
            if 'content' in item:output=item['content'].encode()
            else:
                if item['ref'] not in REFS:raise ValueError('Unexpected source revision')
                original=subprocess.check_output(['git','show',item['ref']+':'+item['source_path']],cwd=ROOT)
                if sha(original)!=item['source_sha256']:raise ValueError('Source hash mismatch: '+str(path))
                lines=original.decode().splitlines(True)
                previous=len(lines)+1
                for start,end,replacement in reversed(item['edits']):
                    if not 0<=start<=end<previous:raise ValueError('Overlapping/out-of-range edit')
                    previous=start
                    lines[start:end]=[replacement]
                output=''.join(lines).encode()
            if sha(output)!=item['target_sha256']:raise ValueError('Prepared output hash mismatch: '+str(path)+' actual '+sha(output))
            pending[str(path)]=output
    for path,output in pending.items():
        destination=ROOT/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(output)
    subprocess.run([sys.executable,'tools/fetch_upstreams.py','blender'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'tools/port_numeric_type_tests.py'],cwd=ROOT,check=True)
    expected={
      'compatibility/numeric-type-ports.json':'e888813e4c795011e710b4e9357e3d432beffa76ebce7afbefaf5019878e8b9f',
      'crates/blended-core/src/numeric_type_cases.rs':'97de960ad0409593d061dfd01cb30337c84acbdaea2901f34c06a1b1335b1732',
      'crates/blended-core/tests/upstream_numeric_types.rs':'59538fe2c5bc1d9d7a9331c8d8e4752a853f9af91565be67d5cf43fd706c09ed'}
    for path,digest in expected.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Generated output differs from the prepared candidate: '+path)
    print(json.dumps({'source_files_validated':len(pending),'generated_files_validated':len(expected),'complete_blender_test_port':False}))
if __name__=='__main__':main()
