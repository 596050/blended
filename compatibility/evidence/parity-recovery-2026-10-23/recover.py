#!/usr/bin/env python3
"""Recover exact retained bytes. This does not rerun Blender or reconstruct results."""
from __future__ import annotations
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath

DEST = Path('/tmp/blended-parity-recovery')
PREFLIGHT = Path('/tmp/blended-source-ledger-preflight-39986612484')
REPLAYS = Path('/tmp/blended-ci-three-profile-replay-39986612484')
SOURCE = REPLAYS / 'source-build-codecs-sqlite'
EXPECTED = {
    'report.json': (780486, '913a5f430f2ea9df35ec2878240a3c3b3b6783062c733a2e9a6f58d3b6c21b0b'),
    'normalizer/reconcile_unittest_matrix.py': (83881, '6675c3f1604ef92f3aa139e0d0cc9a91f0a59487b46e0cb5f9685676cd5caa5c'),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_rel(raw: str) -> str:
    p = PurePosixPath(raw)
    if p.is_absolute() or str(p) != raw or '..' in p.parts or '\\' in raw:
        raise ValueError(f'noncanonical relative path: {raw!r}')
    if not p.parts or any(ord(c) < 32 for c in raw):
        raise ValueError(f'invalid relative path: {raw!r}')
    return raw


def read_regular(p: Path) -> bytes:
    if p.is_symlink() or not p.is_file():
        raise ValueError(f'not a regular file: {p}')
    return p.read_bytes()


def evidence(root: Path, spec: dict) -> bytes:
    data = read_regular(root / clean_rel(spec['path']))
    if len(data) != spec['bytes'] or sha(data) != spec['sha256']:
        raise ValueError(f'evidence identity mismatch: {spec}')
    return data


records = []
written = {}


def retain(src: Path, relative_dest: str, basis: str, expected: dict | None = None) -> None:
    relative_dest = clean_rel(relative_dest)
    data = read_regular(src)
    digest = sha(data)
    if expected and (expected['bytes'] != len(data) or expected['sha256'] != digest):
        raise ValueError(f'recovery expected identity mismatch: {src}')
    out = DEST / relative_dest
    if out.exists() and read_regular(out) != data:
        raise ValueError(f'recovery destination collision: {out}')
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        out.write_bytes(data)
    if read_regular(out) != data:
        raise ValueError(f'copy verification mismatch: {out}')
    if relative_dest in written and written[relative_dest] != digest:
        raise ValueError(f'multiple different recovery bytes: {relative_dest}')
    written[relative_dest] = digest
    records.append({
        'source': str(src), 'destination': relative_dest,
        'bytes': len(data), 'sha256': digest, 'basis': basis,
    })


started = dt.datetime.now(dt.timezone.utc).isoformat()
for name, (size, digest) in EXPECTED.items():
    for directory in (SOURCE, PREFLIGHT):
        data = read_regular(directory / name)
        assert (len(data), sha(data)) == (size, digest), (directory, name)

preflight_files = {p.relative_to(PREFLIGHT).as_posix(): p for p in PREFLIGHT.rglob('*') if p.is_file()}
replay_files = {p.relative_to(SOURCE).as_posix(): p for p in SOURCE.rglob('*') if p.is_file()}
assert len(preflight_files) == 858
assert set(preflight_files) <= set(replay_files)
for name, p in sorted(preflight_files.items()):
    assert read_regular(p) == read_regular(replay_files[name]), name
    retain(p, 'repo-fragments/compatibility/evidence/unittest-parity-ledger-source-build-39986612484/' + name,
           'Retained preflight bytes, independently byte-equal to the CI profile replay copy.')

conversion = json.loads(read_regular(SOURCE / 'conversion.json'))
pathmap_spec = conversion['path_mapping']['map']
pathmap = json.loads(evidence(SOURCE, pathmap_spec))
assert pathmap['schema'] == 1 and pathmap['kind'] == 'exact-evidence-path-map'
assert len(pathmap['entries']) == 730
origins = conversion['raw_origins']
assert len(origins) == 866
by_digest = {}
for name, spec in sorted(origins.items()):
    clean_rel(name)
    data = evidence(SOURCE, spec)
    by_digest.setdefault(spec['sha256'], spec)
    retain(SOURCE / spec['path'], 'repo-fragments/' + name,
           'Original repository path and byte identity retained in conversion.raw_origins.', spec)

missing = []
recoverable = 0
for entry in pathmap['entries']:
    clean_rel(entry['path'])
    spec = by_digest.get(entry['sha256'])
    if spec is None:
        missing.append(entry)
        continue
    assert spec['bytes'] == entry['bytes']
    retain(SOURCE / spec['path'], 'repo-fragments/' + entry['path'],
           'Exact path-map target restored from a retained identical SHA256 and byte-count payload.', entry)
    recoverable += 1

retain(SOURCE / 'normalizer/reconcile_unittest_matrix.py', 'repo-fragments/tools/reconcile_unittest_matrix.py',
       'Pinned exact original normalizer source snapshot; expected SHA256 independently retained in conversation summary.')

for profile in ('base', 'essentials', 'source-build-codecs-sqlite'):
    directory = REPLAYS / profile
    for p in sorted(directory.rglob('*')):
        if p.is_file():
            retain(p, 'retained-replay-profiles/' + profile + '/' + p.relative_to(directory).as_posix(),
                   'Retained replay bytes; copying is not a new test execution.')

report = json.loads(read_regular(SOURCE / 'report.json'))
summary = {
    'schema': 1,
    'kind': 'retained-byte-recovery-observation',
    'recovery_started_utc': started,
    'recovery_completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'scope': 'Existing temporary files only. No Blender execution and no historical receipt synthesis.',
    'expected_historical_anchors': {name: {'bytes': size, 'sha256': digest} for name, (size, digest) in EXPECTED.items()},
    'normalized_source_profile_files': len(preflight_files),
    'normalized_source_profile_cross_copy_byte_mismatches': 0,
    'replay_extra_files': sorted(set(replay_files) - set(preflight_files)),
    'original_path_snapshots_recovered': len(origins),
    'path_map_entries': len(pathmap['entries']),
    'path_map_files_recovered_by_exact_identity': recoverable,
    'path_map_files_missing': len(missing),
    'missing_path_map_entries': missing,
    'new_regression_test_source_found': False,
    'new_regression_test_source_recreated': False,
    'historical_full_infrastructure_execution_receipt_found': False,
    'copied_file_count': len(written),
    'copy_mapping_record_count': len(records),
    'all_upstream_test_parity': False,
    'full_feature_parity': False,
    'records': records,
}
(DEST / 'recovery-manifest.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('records','missing_path_map_entries')}, indent=2))
print('manifest_sha256', sha((DEST / 'recovery-manifest.json').read_bytes()))
