#!/usr/bin/env python3
"""Preserve exact original build artifact bytes and record this new recovery."""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

ZIP_EXPECTED = {'bytes': 222636519, 'sha256': 'c19e2f15d1d5bf07dd5bd80b72a0a7514c71cb4884bc50ca576f4562ba85878f'}
SOURCE_EXPECTED = {'bytes': 172975, 'sha256': '44bdb061bcd22a7a2b7756e93fe406a9eabfd2dd9e9f8fd4b63947ff31e2503f'}
ARCHIVES = {
    'blender-source-development.tar.gz': {
        'bytes': 109564486, 'sha256': '0d51a33313902a0331df02d900fc5776fd0855e8b0f2062b46cf0150d859499a'},
    'essentials/blender-source-development-essentials.tar.gz': {
        'bytes': 112253979, 'sha256': 'c2105e12ae93e1804f82f3f49fdec3e0185ce2dd7fe9f26e97f4d3b44308df3c'},
}
RAW_PREFIX = '/home/runner/work/blended/blended/evidence/browser-source-build/'
REPORT_EXPECTED = {'bytes': 780486, 'sha256': '913a5f430f2ea9df35ec2878240a3c3b3b6783062c733a2e9a6f58d3b6c21b0b'}


def identity(path: Path) -> dict:
    assert path.is_file() and not path.is_symlink(), path
    size = 0
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while block := handle.read(1024 * 1024):
            size += len(block)
            digest.update(block)
    return {'bytes': size, 'sha256': digest.hexdigest()}


def stream_identity(handle) -> dict:
    size = 0
    digest = hashlib.sha256()
    while block := handle.read(1024 * 1024):
        size += len(block)
        digest.update(block)
    return {'bytes': size, 'sha256': digest.hexdigest()}


def canonical_member(name: str) -> str:
    path = PurePosixPath(name)
    assert not path.is_absolute() and str(path) == name and path.parts, name
    assert '..' not in path.parts and '\\' not in name and not any(ord(c) < 32 for c in name), name
    return name


def write_json(path: Path, obj: dict) -> None:
    assert not path.exists(), path
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--extracted', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--parity-report', required=True, type=Path)
    parser.add_argument('--parity-conversion', required=True, type=Path)
    args = parser.parse_args()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    assert identity(args.archive) == ZIP_EXPECTED
    assert identity(args.parity_report) == REPORT_EXPECTED
    assert identity(args.extracted / 'source-build.json') == SOURCE_EXPECTED
    output = args.output.resolve()
    destination = output / 'build'
    assert not destination.exists(), destination
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    with zipfile.ZipFile(args.archive) as archive:
        assert len(archive.infolist()) == 155
        for info in archive.infolist():
            name = canonical_member(info.filename)
            assert name not in seen, name
            seen.add(name)
            mode = info.external_attr >> 16
            assert not info.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG), (name, mode)
            with archive.open(info) as handle:
                member_identity = stream_identity(handle)
            assert member_identity['bytes'] == info.file_size, name
            source = args.extracted / name
            assert identity(source) == member_identity, name
            excluded = name in ARCHIVES
            if excluded:
                assert member_identity == ARCHIVES[name], name
                disposition = 'external-engine-archive'
                reason = 'Large engine payload remains an identified CI artifact; it is excluded from the repository evidence copy.'
                retained_path = None
            else:
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                assert not target.exists(), target
                with source.open('rb') as src, target.open('xb') as dst:
                    while block := src.read(1024 * 1024):
                        dst.write(block)
                assert identity(target) == member_identity, target
                disposition = 'preserved-exact-original-bytes'
                reason = None
                retained_path = 'build/' + name
            rows.append({'member': name, **member_identity, 'zip_crc32': f'{info.CRC:08x}',
                         'zip_compressed_bytes': info.compress_size, 'zip_external_mode': mode,
                         'source_extracted_path': str(source.resolve()), 'retained_path': retained_path,
                         'disposition': disposition, 'reason': reason})
    actual_files = {p.relative_to(args.extracted).as_posix() for p in args.extracted.rglob('*') if p.is_file()}
    assert actual_files == seen
    by_name = {row['member']: row for row in rows}
    assert len(rows) == 155 and sum(row['retained_path'] is not None for row in rows) == 153
    assert {row['member'] for row in rows if row['retained_path'] is None} == set(ARCHIVES)
    build = json.loads((destination / 'source-build.json').read_text())
    overlay = json.loads((destination / 'essentials/package-overlay.json').read_text())
    cache = json.loads((destination / 'dependency-cache-reuse.json').read_text())
    harvest = [json.loads(line) for line in (destination / 'dependency-harvest.jsonl').read_text().splitlines() if line.strip()]
    assert len(harvest) == 4184 and len({x['path'] for x in harvest}) == 4184
    assert build['blended_checkout_commit'] == 'f25e69ed72fed2d31d7d65e657fd6515da4bd792'
    assert build['status'] == 'built' and build['tests_executed'] is False
    assert build['full_feature_parity'] is False
    assert cache['status'] == 'verified' and cache['verified_files'] == 4103 and cache['verified_aliases'] == 3
    assert len(build['stages']) == 132
    verified_stage_logs = []
    for stage in build['stages']:
        assert stage['status'] == 'passed' and stage['exit_code'] == 0, stage['name']
        spec = stage['log_identity']
        assert spec['path'] == stage['log'] and spec['path'].startswith(RAW_PREFIX), spec
        relative = spec['path'][len(RAW_PREFIX):]
        assert relative in by_name
        assert {k: by_name[relative][k] for k in ('bytes', 'sha256')} == {k: spec[k] for k in ('bytes', 'sha256')}
        verified_stage_logs.append({'stage': stage['name'], 'original_log_path': spec['path'],
                                    'retained_path': 'build/' + relative, 'bytes': spec['bytes'], 'sha256': spec['sha256']})
    assert {k: build['artifact'][k] for k in ('bytes', 'sha256')} == ARCHIVES['blender-source-development.tar.gz']
    assert {k: overlay['artifact'][k] for k in ('bytes', 'sha256')} == ARCHIVES['essentials/blender-source-development-essentials.tar.gz']
    assert identity(destination / 'essentials/base-source-build.json') == SOURCE_EXPECTED
    assert {k: overlay['source_build_receipt'][k] for k in ('bytes', 'sha256')} == SOURCE_EXPECTED
    assert overlay['engine_recompiled'] is False and overlay['tests_executed'] == 0
    duration = (dt.datetime.fromisoformat(build['finished_utc']) - dt.datetime.fromisoformat(build['started_utc'])).total_seconds()
    assert duration == 2771.476395
    parity = json.loads(args.parity_report.read_text())
    conversion = json.loads(args.parity_conversion.read_text())
    assert len(conversion['registrations']) == 31
    assert parity['successful_execution_pair_count'] == 528 and parity['outcome_agreement_count'] == 536
    assert parity['gate'] == 'blocked' and not parity['all_upstream_test_parity'] and not parity['full_feature_parity']
    summary = {
        'schema': 1, 'kind': 'post-recovery-original-build-analysis',
        'basis': 'Original source-build receipt, its exact stage logs, cache receipt and harvest manifest. This is not a new build.',
        'source_build_receipt': {'path': 'build/source-build.json', **SOURCE_EXPECTED},
        'original_build': {
            'checkout_commit': build['blended_checkout_commit'], 'port_commit': build['port_commit'],
            'upstream_commit': build['upstream_commit'], 'started_utc': build['started_utc'],
            'finished_utc': build['finished_utc'], 'duration_seconds': duration, 'jobs': build['jobs'],
            'stage_count': 132, 'passed_stage_count': 132, 'nonzero_stage_exit_count': 0,
            'build_mode': build['build_mode'], 'with_buildinfo': build['with_buildinfo'],
            'tests_executed_in_build': build['tests_executed'], 'deployed': build['deployed'],
            'shipping_profile': build['shipping_profile'], 'hardware_verified': build['hardware_verified'],
            'bitwise_reproducibility_verified': build['bitwise_reproducibility_verified'],
            'selected_stages': [{k: stage[k] for k in ('name', 'duration_seconds', 'status', 'exit_code')}
                                for stage in build['stages'] if stage['name'] in ('compile-engine','dependency-openimageio','dependency-sqlite','dependency-python')],
            'codec_patch_manifest_sha256': build['codec_patchset']['manifest_sha256'],
            'contains_new_dpx_signed_size_patch': False,
            'configured_features': {key: build['configured_features'][key] for key in ('WITH_IMAGE_CINEON','WITH_IMAGE_OPENJPEG','WITH_IMAGE_WEBP')},
        },
        'cache_reuse': {
            'basis': 'Original cache-reuse receipt reports these checks during the CI build. Recovery did not revalidate absent dependency payloads.',
            'cache_key': cache['cache_key'], 'verified_files': cache['verified_files'],
            'verified_bytes': cache['verified_bytes'], 'verified_source_derived_aliases': cache['verified_aliases'],
            'harvest_manifest_record_count': len(harvest), 'harvest_manifest_distinct_paths': len({x['path'] for x in harvest}),
            'harvest_scope': 'File identities recorded by the new build; this recovery preserves and checks the manifest bytes, not all cache payloads.',
        },
        'separate_original_test_observations': {
            'basis': 'Recovered original main/resources observations normalized in a separate verified execution; no Blender rerun during recovery.',
            'report': {'path': '../unittest-parity-ledger-source-build-39986612484/report.json', **REPORT_EXPECTED},
            'selected_invocations': len(conversion['registrations']),
            'required_source_registrations': parity['required_registration_count'],
            'unresolved_source_registrations': parity['unresolved_registration_count'],
            'paired_obligations': parity['paired_obligation_count'],
            'distinct_case_ids': parity['known_case_count'],
            'successful_execution_pairs': parity['successful_execution_pair_count'],
            'outcome_agreements': parity['outcome_agreement_count'],
            'observation_totals': parity['observation_totals'],
            'missing_browser_subtests': parity['missing_browser_subtest_count'],
            'unexpected_browser_subtests': parity['unexpected_browser_subtest_count'],
            'gate': parity['gate'],
        },
        'all_upstream_test_parity': False, 'full_feature_parity': False,
    }
    summary_path = output / 'summary.json'
    write_json(summary_path, summary)
    member_path = output / 'artifact-members.json'
    write_json(member_path, {'schema':1, 'kind':'original-ci-artifact-member-inventory',
                            'artifact_id':12518531963, 'run_id':39986612484,
                            'archive':{'path':str(args.archive.resolve()), **ZIP_EXPECTED},
                            'member_count':155, 'preserved_member_count':153, 'external_engine_archive_count':2, 'members':rows})
    recovery = {
        'schema':1, 'kind':'new-recovery-of-original-build-artifact',
        'recovery_started_utc':started, 'recovery_finished_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'source':{'repository':'596050/blended','run_id':39986612484,'artifact_id':12518531963,
                  'artifact_name':'browser-source-development-39986612484',
                  'run_url':'https://github.com/596050/blended/actions/runs/39986612484'},
        'archive':{'path':str(args.archive.resolve()),**ZIP_EXPECTED},
        'verification':{'archive_expected_sha256_matched':True,'archive_expected_bytes_matched':True,
                        'regular_unique_canonical_members':155,'archive_members_crc_verified_on_full_read':155,
                        'extracted_member_identities_matched':155,'preserved_member_identities_matched':153,
                        'excluded_engine_archives_identified_and_verified':2,'source_build_receipt_identity_matched':True,
                        'original_stage_log_identities_matched':132},
        'script':{'path':str(Path(__file__).resolve()),**identity(Path(__file__).resolve())},
        'member_inventory':{'path':'artifact-members.json',**identity(member_path)},
        'summary':{'path':'summary.json',**identity(summary_path)},
        'stage_log_checks':verified_stage_logs,
        'commands':{'scope':'Recovery code only; no original build command was rerun.',
                    'archive':str(args.archive.resolve()),'extracted':str(args.extracted.resolve()),
                    'output':str(output),'parity_report':str(args.parity_report.resolve()),
                    'parity_conversion':str(args.parity_conversion.resolve())},
        'claim_limit':'The build ran earlier in CI. These timestamps belong to evidence recovery. Original build receipt and logs are preserved unchanged.',
        'all_upstream_test_parity':False,'full_feature_parity':False,
    }
    write_json(output / 'recovery.json', recovery)
    print(json.dumps({'preserved_members':153,'external_engine_archives':2,
                      'original_build_duration_seconds':duration,'original_passed_stages':132,
                      'source_build_receipt':SOURCE_EXPECTED,'recovery':identity(output/'recovery.json')},indent=2))


if __name__ == '__main__':
    main()
