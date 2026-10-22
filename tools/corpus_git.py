#!/usr/bin/env python3
"""Stage an audited corpus as raw Git blobs, ignoring all content filters.

Use only with a dedicated publication repository. Replaces that index, not
working files or refs. Original LFS pointers are preserved as source bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess


def stage_raw_corpus(source: Path, repository: Path) -> dict:
    source, repository = source.resolve(), repository.resolve()
    if not (repository / '.git').is_dir():
        raise ValueError('A dedicated, initialised publication repository is required')
    files = []
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source).as_posix()
        if path.is_symlink() or '.git' in PurePosixPath(relative).parts:
            raise ValueError('Unsafe corpus entry: ' + relative)
        if path.is_file():
            files.append((relative, path))
    original = {}
    records = json.loads((source / 'tracked-files.json').read_text())
    for item in records:
        if not item.get('included_in_corpus'):
            continue
        relative = 'original/' + item['path']
        pp = PurePosixPath(item['path'])
        if pp.is_absolute() or '..' in pp.parts or relative in original:
            raise ValueError('Unsafe or duplicate original path: ' + relative)
        path = source / relative
        if path.is_symlink():
            raise ValueError('Original symlinks must be inert target text: ' + relative)
        data = path.read_bytes()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if hashlib.sha256(data).hexdigest() != item['sha256'] or oid != item['git_oid']:
            raise ValueError('Upstream original content mismatch: ' + relative)
        original[relative] = item
    git = ['git', '-C', str(repository)]
    entries = bytearray()
    # --no-filters prevents nested upstream .gitattributes from rewriting
    # reference bytes through newline normalisation, LFS or other filters.
    for relative, path in files:
        data = path.read_bytes()
        oid = subprocess.check_output(git + ['hash-object', '-w', '--no-filters', '--stdin'], input=data).strip()
        expected = original.get(relative)
        if expected and oid.decode() != expected['git_oid']:
            raise ValueError('Git did not preserve raw original: ' + relative)
        mode = b'100755' if expected and expected.get('mode') == '100755' else b'100644'
        entries.extend(mode + b' ' + oid + b'\t' + os.fsencode(relative) + b'\0')
    subprocess.run(git + ['read-tree', '--empty'], check=True)
    subprocess.run(git + ['update-index', '-z', '--index-info'], input=entries, check=True)
    staged = {}
    for entry in subprocess.check_output(git + ['ls-files', '--stage', '-z']).split(b'\0'):
        if entry:
            header, path = entry.split(b'\t', 1)
            staged[os.fsdecode(path)] = header.split()[1].decode()
    for path, item in original.items():
        if staged.get(path) != item['git_oid']:
            raise ValueError('Staged upstream blob mismatch: ' + path)
    return {'files_staged': len(staged), 'original_blobs_verified': len(original),
            'normalisation_applied': False, 'fixture_payloads_mirrored': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--repository', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(stage_raw_corpus(a.source, a.repository), indent=2))
