#!/usr/bin/env python3
"""Download and preserve exact reported CI artifacts, with bounded member checks."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import urllib.request
import zipfile


def identity(p):
 data=p.read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def preserve(spec,archive,out):
 assert identity(archive)=={k:spec[k] for k in ('bytes','sha256')},spec['id']
 members=[];seen=set()
 with zipfile.ZipFile(archive) as z:
  assert len(z.infolist()) < 5000
  assert sum(x.file_size for x in z.infolist()) < 200_000_000
  for entry in z.infolist():
   rel=PurePosixPath(entry.filename)
   assert str(rel)==entry.filename and not rel.is_absolute() and '..' not in rel.parts and '\\' not in entry.filename
   assert not any(ord(c)<32 for c in entry.filename)
   assert entry.filename not in seen;seen.add(entry.filename)
   assert not entry.is_dir() and stat.S_IFMT(entry.external_attr>>16) in (0,stat.S_IFREG)
   data=z.read(entry)
   assert len(data)==entry.file_size
   target=out/spec['profile']/'artifact'/entry.filename
   target.parent.mkdir(parents=True,exist_ok=True)
   assert not target.exists(),target
   target.write_bytes(data)
   ident={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
   assert identity(target)==ident
   members.append({'name':entry.filename,**ident,'zip_crc32':f'{entry.CRC:08x}',
                   'retained_path':str(target.relative_to(out))})
 return {'artifact_id':spec['id'],'artifact_name':spec['name'],'expected_zip':{k:spec[k] for k in ('bytes','sha256')},
         'downloaded_zip':identity(archive),'temporary_archive':str(archive),'member_count':len(members),'members':members}


def main():
 p=argparse.ArgumentParser();p.add_argument('--specs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--download-dir',type=Path,required=True)
 a=p.parse_args();specs=json.loads(a.specs.read_text());a.download_dir.mkdir(exist_ok=True)
 receipts=[]
 for spec in specs:
  started=dt.datetime.now(dt.timezone.utc).isoformat()
  archive=a.download_dir/(str(spec['id'])+'.zip')
  assert not archive.exists()
  with urllib.request.urlopen(spec['url'],timeout=60) as response,archive.open('xb') as f:
   status=response.status;ctype=response.headers.get('Content-Type')
   while chunk:=response.read(1024*1024):f.write(chunk)
  row=preserve(spec,archive,a.output)
  row.update({'download_started_utc':started,'download_finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'http_status':status,'content_type':ctype})
  receipts.append(row)
  print(json.dumps({k:v for k,v in row.items() if k not in ('members','temporary_archive')},sort_keys=True),flush=True)
 result={'schema':1,'kind':'ci-artifact-download-and-preservation','artifacts':receipts,'all_upstream_test_parity':False,'full_feature_parity':False}
 target=a.output/'download-receipts.json';assert not target.exists();target.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
