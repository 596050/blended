#!/usr/bin/env python3
"""Reproduce exact pinned zero-width intervals, not a host Unicode database."""
from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parents[1]
BLOB='1d337ec47f24e04f427937deeedcd773cc3ea474'
def generate(root=ROOT):
 source=root/'.upstream/blender/extern/wcwidth/wcwidth.c';raw=source.read_bytes()
 actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if actual!=BLOB:raise ValueError('Pinned wcwidth source changed')
 text=raw.decode();match=re.search(r'static const struct interval combining\[\] = \{(.*?)\n  \};',text,re.S)
 if match is None:raise ValueError('Missing original combining interval table')
 pairs=re.findall(r'\{\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\}',match[1])
 if not pairs or re.sub(r'\{\s*0x[0-9A-Fa-f]+\s*,\s*0x[0-9A-Fa-f]+\s*\}|[\s,]','',match[1]):raise ValueError('Unexpected table syntax')
 previous=-1
 for a,b in pairs:
  first,last=int(a,16),int(b,16)
  if not previous<first<=last:raise ValueError('Nonmonotonic combining ranges')
  previous=last
 header='// Generated from pinned Blender extern/wcwidth/wcwidth.c, git blob '+BLOB+'.\n// Markus Kuhn -- 2007-05-26; table updated by Blender contributors.\n// Permission to use, copy, modify, and distribute this software\n// for any purpose and without fee is hereby granted. The author\n// disclaims all warranties with regard to this software.\n// Full original notice: LICENSES/wcwidth-original-notice.txt.\n'
 content=header+'const COMBINING:&[(u32,u32)]=&[\n'+''.join(f'({a},{b}),\n' for a,b in pairs)+'];\n'
 (root/'crates/blended-core/src/utf8_combining.rs').write_text(content)
 licence=root/'LICENSES/wcwidth-original-notice.txt';licence.parent.mkdir(exist_ok=True)
 licence.write_text(text[:text.index('*/')+2]+'\n')
 return len(pairs)
if __name__=='__main__':print('Pinned combining intervals:',generate())
