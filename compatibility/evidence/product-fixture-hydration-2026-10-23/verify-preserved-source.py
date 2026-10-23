"""Confirm fixture hydration left every other original archive file unchanged."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tarfile

directory = Path(__file__).resolve().parent
inventory_path = directory / 'inventory.json'
inventory = json.loads(inventory_path.read_text())
source_root = Path(inventory['source_root'])
archive_path = Path(inventory['source_archive']['path'])
output = directory / 'preserved-source.json'
if output.exists():
    raise RuntimeError('immutable source preservation receipt already exists')


def identity(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': digest}


def check(condition):
    if not condition:
        raise ValueError('source preservation check failed')


check(identity(archive_path) == {key: inventory['source_archive'][key] for key in ('bytes', 'sha256')})
fixtures = {row['path'] for row in inventory['entries']}
prefix = 'blender-' + inventory['source_commit'] + '/'
failures, count, total_bytes, symlinks = [], 0, 0, 0
manifest_digest = hashlib.sha256()
started = datetime.now(timezone.utc).isoformat()
with tarfile.open(archive_path, 'r:gz') as archive:
    for member in archive:
        if not member.name.startswith(prefix) or member.isdir():
            continue
        relative = member.name[len(prefix):]
        if relative in fixtures:
            continue
        parts = PurePosixPath(relative)
        check(relative == parts.as_posix() and not parts.is_absolute() and '..' not in parts.parts)
        path = source_root / relative
        try:
            check(not any(parent.is_symlink() for parent in path.parents))
            if member.issym():
                check(path.is_symlink() and os.readlink(path) == member.linkname)
                symlinks += 1
                observed = {'path': relative, 'symlink_target': member.linkname}
            else:
                check(member.isfile() and path.is_file() and not path.is_symlink())
                with archive.extractfile(member) as stream:
                    expected = {'bytes': member.size, 'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()}
                check(identity(path) == expected)
                count += 1
                total_bytes += member.size
                observed = {'path': relative, **expected}
            manifest_digest.update(json.dumps(observed, sort_keys=True, separators=(',', ':')).encode() + b'\n')
        except (ValueError, OSError) as error:
            failures.append({'path': relative, 'error_type': type(error).__name__})
record = {
    'schema': 1,
    'source_commit': inventory['source_commit'],
    'started_utc': started,
    'finished_utc': datetime.now(timezone.utc).isoformat(),
    'source_archive': inventory['source_archive'],
    'fixture_inventory': {'path': 'inventory.json', **identity(inventory_path)},
    'verifier': {'path': Path(__file__).name, **identity(Path(__file__))},
    'scope': 'Every original non-directory archive entry outside the exact candidate fixture inventory.',
    'verified_regular_files': count,
    'verified_regular_bytes': total_bytes,
    'verified_symlinks': symlinks,
    'verified_manifest_sha256': manifest_digest.hexdigest(),
    'manifest_encoding': 'Archive order; each verified row encoded as sorted compact JSON plus LF.',
    'failures': failures,
    'status': 'unchanged' if not failures else 'requires_review',
    'tests_executed': 0,
    'test_passes': 0,
}
with output.open('x') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps(record, indent=2))
raise SystemExit(0 if not failures else 1)
