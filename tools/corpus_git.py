#!/usr/bin/env python3
"""Preserve exact original sources, without creating a paid LFS mirror.

Every original is retained in original-blender-tests.tar.gz. Non-pointer
original files are also browsable individually. All bytes are hash-verified.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile


def stage_raw_corpus(source: Path, repository: Path) -> dict:
    source, repository = source.resolve(), repository.resolve()
    if not (repository / '.git').is_dir():
        raise ValueError('A dedicated, initialised publication repository is required')
    files = []
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source).as_posix()
        if path.is_symlink() or '.git' in PurePosixPath(relative).parts:
            raise ValueError('Unsafe corpus entry: ' + relative)
        if path.is_file(): files.append((relative, path))
    original = {}
    for item in json.loads((source / 'tracked-files.json').read_text()):
        if not item.get('included_in_corpus'): continue
        relative = 'original/' + item['path']
        pp = PurePosixPath(item['path'])
        if pp.is_absolute() or '..' in pp.parts or relative in original:
            raise ValueError('Unsafe or duplicate original path: ' + relative)
        path = source / relative
        if path.is_symlink(): raise ValueError('Original symlink must be inert target text: ' + relative)
        data = path.read_bytes()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if hashlib.sha256(data).hexdigest() != item['sha256'] or oid != item['git_oid']:
            raise ValueError('Upstream original content mismatch: ' + relative)
        original[relative] = item
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode='w') as archive:
        for relative, item in sorted(original.items()):
            data = (source / relative).read_bytes()
            info = tarfile.TarInfo(relative); info.size = len(data)
            info.mode = 0o755 if item.get('mode') == '100755' else 0o644
            archive.addfile(info, io.BytesIO(data))
    packed = gzip.compress(archive_buffer.getvalue(), mtime=0)
    archive_path = source / 'original-blender-tests.tar.gz'
    archive_path.write_bytes(packed)
    files = [(name, path) for name, path in files if name != archive_path.name]
    files.append((archive_path.name, archive_path))
    pointer_paths = {relative for relative in original if (source / relative).read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1')}
    # GitHub rejects standalone pointers without its own corresponding LFS
    # objects. Archive exact pointers instead of buying/mirroring that storage.
    files = [(relative, path) for relative, path in files if relative not in pointer_paths]
    with tarfile.open(fileobj=io.BytesIO(packed), mode='r:gz') as archive:
        for relative, item in original.items():
            data = archive.extractfile(relative).read()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Archived source mismatch: ' + relative)
    layout = {'schema': 1, 'canonical_original_archive': archive_path.name,
              'canonical_archive_sha256': hashlib.sha256(packed).hexdigest(),
              'original_files_verified': len(original), 'archived_lfs_pointer_paths': len(pointer_paths),
              'individually_browsable_originals': len(original) - len(pointer_paths),
              'fixture_payloads_mirrored': False,
              'note': 'Extract the canonical archive to restore the entire original/ tree. Raw LFS pointers are stored inside the archive, not as GitHub LFS references. Fixture payloads are downloaded from pinned public Blender LFS by the test workflow.'}
    layout_path = source / 'CORPUS-LAYOUT.json'; layout_path.write_text(json.dumps(layout, indent=2)+'\n')
    files = [(n,p) for n,p in files if n != layout_path.name] + [(layout_path.name, layout_path)]
    git = ['git', '-C', str(repository)]
    entries = bytearray()
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
            header, path = entry.split(b'\t', 1); staged[os.fsdecode(path)] = header.split()[1].decode()
    for path, item in original.items():
        if path not in pointer_paths and staged.get(path) != item['git_oid']:
            raise ValueError('Staged upstream blob mismatch: ' + path)
    return dict(layout, files_staged=len(staged), original_blobs_verified=len(original), normalisation_applied=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--repository', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(stage_raw_corpus(a.source, a.repository), indent=2))
