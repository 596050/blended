#!/usr/bin/env python3
"""Preserve original Blender tests and fail closed on incomplete browser ports.

Source declarations are candidates, never a complete runtime denominator.
A complete test port is distinct from passing tests and from feature parity.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
from urllib.parse import urlparse

SHA256 = re.compile(r'^[0-9a-f]{64}$')
SHA1 = re.compile(r'^[0-9a-f]{40}$')
LFS_HEADER = b'version https://git-lfs.github.com/spec/v1'
SOURCE_SUFFIXES = {'.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.py', '.glsl', '.osl'}


def lfs_pointer(raw: bytes) -> dict[str, Any] | None:
    if not raw.startswith(LFS_HEADER):
        return None
    if len(raw) > 4096:
        raise ValueError('Oversized LFS pointer')
    text = raw.decode('ascii')
    oid = re.search(r'^oid sha256:([0-9a-f]{64})$', text, re.M)
    size = re.search(r'^size (\d+)$', text, re.M)
    if not oid or not size:
        raise ValueError('Malformed LFS pointer')
    return {'oid': oid[1], 'size': int(size[1])}


def verify_fixture(raw: bytes, expected: dict[str, Any]) -> str:
    if lfs_pointer(raw) is not None:
        return 'lfs_pointer'
    if len(raw) != expected['size']:
        return 'size_mismatch'
    return 'verified' if hashlib.sha256(raw).hexdigest() == expected['oid'] else 'hash_mismatch'


def parse_gtest_list(text: str) -> list[dict[str, Any]]:
    suite = None
    cases, seen = [], set()
    for line in text.splitlines():
        clean = line.split('#', 1)[0].rstrip()
        if not clean:
            continue
        if not clean[0].isspace() and clean.endswith('.'):
            suite = clean[:-1]
        elif suite and clean[0].isspace():
            test = clean.strip()
            if not re.fullmatch(r'[\w/.-]+', test):
                raise ValueError('Unrecognised GoogleTest listing: ' + line)
            identity = suite + '.' + test
            if identity in seen:
                raise ValueError('Duplicate GoogleTest case: ' + identity)
            seen.add(identity)
            disabled = any(part.startswith('DISABLED_') for part in re.split(r'[/.]', identity))
            cases.append({'id': identity, 'disabled': disabled})
    if not cases:
        raise ValueError('Empty GoogleTest registry is not complete')
    return cases


def parse_ctest_json(raw: dict[str, Any]) -> list[dict[str, Any]]:
    cases, seen = [], set()
    for test in raw.get('tests', []):
        name = test['name']
        if not name or name in seen:
            raise ValueError('Empty or duplicate CTest identity: ' + name)
        seen.add(name)
        properties = test.get('properties', [])
        disabled = any(p.get('name') == 'DISABLED' and str(p.get('value')).lower() in {'true', 'on', '1'} for p in properties)
        cases.append({'id': name, 'command': test.get('command', []), 'properties': properties,
                      'backtrace': test.get('backtrace'), 'disabled': disabled})
    if not cases:
        raise ValueError('Empty CTest registry is not complete')
    return cases


def assess(contract: dict, registries: list, ports: list, results: list,
           *, expected_application_commit: str, expected_url: str) -> dict:
    """Evaluate evidence. Missing/disabled/blocked cases never count as executed.

    This validates evidence structure and joins. CI must separately verify the
    referenced logs, build configuration, source hashes and adapter review.
    A hash string alone is not a signature or an independent execution proof.
    """
    blockers: list[dict[str, str]] = []
    def block(code, identity, detail=''):
        blockers.append({'code': code, 'id': str(identity), 'detail': str(detail)})
    pin = contract.get('upstream_commit', '')
    if not SHA1.fullmatch(pin): block('invalid_upstream_pin', pin)
    if not SHA1.fullmatch(expected_application_commit): block('invalid_application_pin', expected_application_commit)
    url = urlparse(expected_url)
    if url.scheme != 'https' or not url.hostname or url.hostname in {'localhost', '127.0.0.1', '::1'}:
        block('public_deployment_required', expected_url)
    for error in contract.get('source_audit_errors', []): block('source_audit', error)
    for f in contract.get('fixtures', []):
        if f.get('status') != 'verified': block('fixture_unavailable', f['path'], f.get('status'))
    for dep in contract.get('external_dependencies', []):
        if dep.get('status') != 'verified': block('dependency_unavailable', dep.get('name', dep.get('path')), dep.get('status'))
    required_profiles = contract.get('required_profiles', [])
    if not required_profiles or len(set(required_profiles)) != len(required_profiles): block('invalid_profiles', '')
    by_profile = {}
    for registry in registries:
        profile = registry['profile']
        if profile in by_profile: block('duplicate_registry', profile)
        if profile not in required_profiles: block('unknown_registry', profile)
        by_profile[profile] = registry
    runtime = {}
    for profile in required_profiles:
        registry = by_profile.get(profile)
        if registry is None:
            block('missing_runtime_registry', profile); continue
        if registry.get('upstream_commit') != pin: block('registry_pin_mismatch', profile)
        if registry.get('complete') is not True: block('runtime_enumeration_incomplete', profile)
        if not SHA256.fullmatch(registry.get('build_config_sha256', '')): block('missing_build_configuration', profile)
        if not registry.get('cases'): block('empty_runtime_registry', profile)
        for case in registry.get('cases', []):
            key = (profile, case['id'])
            if key in runtime: block('duplicate_runtime_case', key)
            runtime[key] = case
            if case.get('disabled'): block('disabled_upstream_case', key)
            if not case.get('source_paths'): block('missing_runtime_source_mapping', key)
    obligations = {x['path']: x for x in contract.get('source_obligations', [])}
    if not obligations: block('empty_source_obligations', '')
    if len(obligations) != len(contract.get('source_obligations', [])): block('duplicate_source_obligation', '')
    source_ports = {}
    mapped_cases = set()
    valid_source_ports = set()
    for port in ports:
        path = port['source_path']
        if path in source_ports: block('duplicate_source_port', path)
        source_ports[path] = port
        expected = obligations.get(path)
        if expected is None:
            block('unknown_source_port', path); continue
        valid = True
        compile_only = expected.get('kind') == 'compile_time'
        checks = [
            (port.get('source_sha256') == expected['sha256'], 'source_hash_mismatch'),
            (port.get('assertions') in {'upstream_verbatim', 'reviewed_translation'}, 'unverified_assertions'),
            (port.get('review') == 'reviewed', 'missing_assertion_review'),
            (bool(port.get('adapter')) and bool(SHA256.fullmatch(port.get('adapter_sha256', ''))), 'missing_browser_adapter'),
            (compile_only or bool(port.get('cases')), 'empty_source_case_mapping')]
        if compile_only:
            receipts = port.get('compilation', {})
            for realm in ('native', 'browser'):
                receipt = receipts.get(realm, {})
                checks.append((receipt.get('status') == 'passed' and receipt.get('upstream_commit') == pin
                               and bool(SHA256.fullmatch(receipt.get('log_sha256', '')))
                               and (realm != 'browser' or receipt.get('application_commit') == expected_application_commit),
                               'missing_compile_time_evidence_' + realm))
        for passed, code in checks:
            if not passed: block(code, path); valid = False
        for ref in port.get('cases', []):
            key = (ref['profile'], ref['id'])
            if key not in runtime: block('unknown_port_case', key); valid = False
            elif path not in runtime[key].get('source_paths', []): block('runtime_source_mismatch', key); valid = False
            mapped_cases.add(key)
        if valid: valid_source_ports.add(path)
    for path in obligations.keys() - source_ports.keys(): block('source_not_ported', path)
    for key, case in runtime.items():
        if key not in mapped_cases: block('runtime_case_not_ported', key)
        for path in case.get('source_paths', []):
            if path not in valid_source_ports: block('runtime_source_not_verified', key, path)
    observed = {}
    statuses = Counter()
    for result in results:
        key = (result.get('profile'), result.get('id'))
        realm = result.get('realm')
        rk = (*key, realm)
        if rk in observed: block('duplicate_execution_result', rk)
        observed[rk] = result
        statuses[f'{realm}:{result.get("status")}'] += 1
        if key not in runtime: block('unregistered_execution_result', rk)
        if realm not in {'native', 'browser'}: block('unknown_execution_realm', rk)
    passed = Counter()
    for key in runtime:
        for realm in ('native', 'browser'):
            rk = (*key, realm)
            result = observed.get(rk)
            if result is None: block('missing_execution', rk); continue
            checks = [
                (result.get('upstream_commit') == pin, 'execution_pin_mismatch'),
                (result.get('executed') is True, 'not_executed'),
                (result.get('status') in {'passed', 'failed'}, 'unexecuted_or_skipped_status'),
                (result.get('status') != 'failed' or result.get('failure_kind') == 'assertion', 'crash_is_not_assertion_execution'),
                (result.get('skipped') == 0, 'nested_skipped_cases'),
                (bool(SHA256.fullmatch(result.get('log_sha256', ''))), 'missing_execution_log')]
            if realm == 'browser':
                checks += [(result.get('application_commit') == expected_application_commit, 'deployed_commit_mismatch'),
                           (result.get('url') == expected_url, 'deployed_url_mismatch')]
            for ok, code in checks:
                if not ok: block(code, rk)
            if all(x[0] for x in checks) and result['status'] == 'passed': passed[realm] += 1
    complete = not blockers
    return {'schema': 1, 'upstream_commit': pin, 'expected_application_commit': expected_application_commit,
            'url': expected_url, 'test_port_complete': complete,
            'conformance_passed': complete and passed['native'] == len(runtime) and passed['browser'] == len(runtime),
            'feature_parity_proven': False, 'source_obligations': len(obligations),
            'verified_source_ports': len(valid_source_ports), 'registered_runtime_cases': len(runtime),
            'native_passed': passed['native'], 'browser_passed': passed['browser'],
            'observed_statuses': dict(statuses), 'blocker_counts': dict(Counter(b['code'] for b in blockers)),
            'blockers': sorted(blockers, key=lambda b: (b['code'], b['id']))}


def git_entries(root: Path, tracked: Path | None = None):
    data = tracked.read_bytes() if tracked else subprocess.check_output(['git', '-C', str(root), 'ls-files', '--stage', '-z'])
    seen = set()
    for entry in data.split(b'\0'):
        if not entry: continue
        header, name = entry.split(b'\t', 1)
        mode, oid, stage = header.decode().split()
        path = os.fsdecode(name)
        pp = PurePosixPath(path)
        if pp.is_absolute() or '..' in pp.parts or path in seen or stage != '0':
            raise ValueError('Invalid/duplicate/conflicted tracked path: ' + path)
        seen.add(path)
        yield path, mode, oid


def build_catalogue(root: Path, pin: str, policy: dict, output: Path, tracked: Path | None = None) -> dict:
    """Hash every tracked file, import originals, retain every LFS dependency.

    Source heuristics only locate additional candidates outside test directories.
    All tracked files remain indexed and the whole checkout is pinned separately.
    """
    try:
        from tools.inventory import scan_cpp, scan_python, CPP_SUFFIXES
    except ModuleNotFoundError:
        from inventory import scan_cpp, scan_python, CPP_SUFFIXES
    output.mkdir(parents=True, exist_ok=True)
    original = output / 'original'; original.mkdir(exist_ok=True)
    if tracked is None:
        actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != pin: raise ValueError('Pinned source commit mismatch')
    records, candidates, compile_assertions, fixtures, obligations, errors, deps = [], [], [], [], [], [], []
    diagnostics = []
    for path, mode, oid in git_entries(root, tracked):
        file = root / path
        if mode == '160000':
            deps.append({'path': path, 'name': path, 'commit': oid, 'status': 'not_materialised'})
            records.append({'path': path, 'git_oid': oid, 'mode': mode, 'kind': 'gitlink'}); continue
        try:
            raw = os.readlink(file).encode() if mode == '120000' else file.read_bytes()
            pointer = lfs_pointer(raw)
            actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if actual != oid: raise ValueError('Tracked blob hash mismatch (materialise assets in a separate cache)')
            digest = hashlib.sha256(raw).hexdigest()
            record = {'path': path, 'git_oid': oid, 'mode': mode, 'sha256': digest, 'bytes': len(raw)}
            parts = PurePosixPath(path).parts
            suffix = file.suffix.lower()
            in_tests = any(p in {'tests', 'test', 'testing', 'testdata', 'test_data'} for p in parts)
            test_name = bool(re.search(r'(^test_|_tests?\.|^tests?\.)', file.name))
            registration = file.name == 'CMakeLists.txt' or suffix == '.cmake'
            found = []
            if suffix in CPP_SUFFIXES or suffix == '.py':
                try:
                    text = raw.decode('utf-8')
                except UnicodeError:
                    text = raw.decode('latin-1')
                    diagnostics.append({'path': path, 'diagnostic': 'Non-UTF8 source; ASCII declaration scan with Latin-1 byte mapping'})
                try:
                    found = scan_python(text, path) if suffix == '.py' else scan_cpp(text, path)
                except SyntaxError as exc:
                    diagnostics.append({'path': path, 'diagnostic': str(exc)})
                for c in found:
                    c.update(upstream_commit=pin, source_sha256=digest, port_status='not_ported', execution='not_run')
                    c['id'] = f'{path}:{c["identity"]}:{c["line"]}'
                    (compile_assertions if c['kind'] == 'static_assert' else candidates).append(c)
            selected = in_tests or test_name or bool(found) or registration or path in {'COPYING', '.gitmodules', '.gitattributes'}
            record.update(in_test_tree=in_tests, registration=registration, included_in_corpus=selected)
            if pointer:
                # All formats, not just .blend: images, video, audio, fonts, caches, imports.
                fixtures.append(dict(path=path, status='lfs_pointer', in_test_tree=in_tests, **pointer))
            is_test_source = (in_tests or test_name or bool(found)) and suffix in SOURCE_SUFFIXES
            if is_test_source and mode != '120000':
                kind = 'compile_time' if found and all(c['kind'] == 'static_assert' for c in found) and not (in_tests or test_name) else 'source'
                obligations.append({'path': path, 'sha256': digest, 'kind': kind,
                                    'candidate_declarations': len(found), 'port_status': 'not_ported'})
            if selected:
                dst = original / path; dst.parent.mkdir(parents=True, exist_ok=True)
                # Symlinks are archived as inert target text; metadata retains the original mode.
                dst.write_bytes(raw)
            records.append(record)
        except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
            errors.append({'path': path, 'error': str(exc)})
    # Blender's external benchmark repository is not fixed by the main source pin.
    if policy.get('require_external_benchmarks', True):
        deps.append({'name': 'blender-benchmarks', 'repository': 'https://projects.blender.org/blender/blender-benchmarks.git', 'status': 'unpinned'})
    contract = {'schema': 1, 'upstream_commit': pin, 'required_profiles': policy['required_profiles'],
                'source_obligations': obligations, 'fixtures': fixtures,
                'source_audit_errors': errors, 'external_dependencies': deps,
                'runtime_enumeration_complete': False, 'discovery_diagnostics': diagnostics,
                'note': 'A complete tracked-file audit is not complete runtime discovery or a browser test port.'}
    outputs = {'contract.json': contract, 'tracked-files.json': records, 'source-candidates.json': candidates,
               'compile-time-assertions.json': compile_assertions, 'registries.json': [], 'ports.json': [], 'results.json': []}
    summary = {'schema': 1, 'upstream_commit': pin, 'tracked_entries': len(records),
               'original_corpus_files': sum(r.get('included_in_corpus', False) for r in records),
               'source_obligations': len(obligations), 'runtime_source_candidates': len(candidates),
               'compile_time_assertions': len(compile_assertions), 'lfs_pointer_paths': len(fixtures),
               'unique_lfs_objects': len({f['oid'] for f in fixtures}),
               'unique_lfs_bytes': sum({f['oid']: f['size'] for f in fixtures}.values()),
               'test_tree_lfs_paths': sum(f['in_test_tree'] for f in fixtures),
               'audit_errors': len(errors), 'discovery_diagnostics': len(diagnostics), 'runtime_enumeration_complete': False,
               'test_port_complete': False, 'feature_parity_proven': False,
               'candidate_kinds': dict(Counter(c['kind'] for c in candidates))}
    outputs['summary.json'] = summary
    for name, obj in outputs.items(): (output / name).write_text(json.dumps(obj, indent=2) + '\n')
    (output / 'README.md').write_text('# Original Blender test corpus\n\nPinned upstream: `' + pin + '`.\n\n'
        'The original/ tree contains unchanged test sources, support files, build registrations and fixture pointers. '
        'All tracked files are indexed and hash-verified; complete source dependencies are pinned in vendor/blender. '
        'LFS pointers are NOT fixture payloads. Source candidate counts are NOT runtime test counts. '
        'A complete browser test port has NOT been achieved. See full-port-report.json for explicit blockers.\n')
    return summary


def audit_fixture_cache(directory: Path, cache: Path) -> dict:
    """Validate every content-addressed payload without mutating the source tree."""
    contract_path = directory / 'contract.json'
    contract = json.loads(contract_path.read_text())
    checked = {}
    for entry in contract['fixtures']:
        oid = entry['oid']
        if oid not in checked:
            payload = cache / oid[:2] / oid[2:4] / oid
            status = 'missing'
            if payload.is_file():
                if payload.stat().st_size != entry['size']:
                    status = 'size_mismatch'
                else:
                    with payload.open('rb') as stream:
                        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                    status = 'verified' if digest == oid else 'hash_mismatch'
            checked[oid] = status
        entry['status'] = checked[oid]
    contract_path.write_text(json.dumps(contract, indent=2) + '\n')
    report = {'schema': 1, 'upstream_commit': contract['upstream_commit'],
              'unique_objects': len(checked), 'statuses': dict(Counter(checked.values())),
              'complete': bool(checked) and all(s == 'verified' for s in checked.values())}
    (directory / 'fixture-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('catalogue'); c.add_argument('--root', type=Path, required=True)
    c.add_argument('--pin', required=True); c.add_argument('--policy', type=Path, required=True)
    c.add_argument('--output', type=Path, required=True); c.add_argument('--tracked', type=Path)
    g = sub.add_parser('gate'); g.add_argument('--directory', type=Path, required=True)
    g.add_argument('--application-commit', required=True); g.add_argument('--url', required=True)
    e = sub.add_parser('enumerate-ctest'); e.add_argument('--build', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    f = sub.add_parser('fixtures'); f.add_argument('--directory', type=Path, required=True)
    f.add_argument('--cache', type=Path, required=True)
    a = p.parse_args()
    if a.cmd == 'fixtures':
        report = audit_fixture_cache(a.directory, a.cache); print(json.dumps(report, indent=2))
        return 0 if report['complete'] else 1
    if a.cmd == 'catalogue':
        summary = build_catalogue(a.root, a.pin, json.loads(a.policy.read_text()), a.output, a.tracked)
        print(json.dumps(summary, indent=2)); return 1 if summary['audit_errors'] else 0
    if a.cmd == 'enumerate-ctest':
        proc = subprocess.run(['ctest', '--test-dir', str(a.build), '--show-only=json-v1'], check=True, capture_output=True, text=True)
        raw = json.loads(proc.stdout); cases = parse_ctest_json(raw)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps({'raw': raw, 'cases': cases, 'complete': False,
            'note': 'CTest registration only. Expand batched GoogleTest/Python/fixture/UI cases and record build options before declaring complete.'}, indent=2)+'\n')
        return 0
    load = lambda name: json.loads((a.directory / name).read_text())
    report = assess(load('contract.json'), load('registries.json'), load('ports.json'), load('results.json'),
                    expected_application_commit=a.application_commit, expected_url=a.url)
    (a.directory / 'full-port-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'blockers'}, indent=2))
    return 0 if report['test_port_complete'] else 1


if __name__ == '__main__': raise SystemExit(main())
