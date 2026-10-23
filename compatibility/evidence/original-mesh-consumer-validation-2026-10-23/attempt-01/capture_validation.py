#!/usr/bin/env python3
"""Capture infrastructure-only mesh normalization verification, once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE_PATHS = [
    'tools/reconcile_original_mesh.py', 'tools/test_parity_ledger.py',
    'tools/reconcile_unittest_matrix.py', 'tools/unittest_cohort.py',
    'tools/upstream_invocations.py', 'tools/upstream_invocations_5_2.json',
    'tools/upstream_resources.py', 'tools/probe_blender_fixtures.py',
    'tools/browser_package_overlay.py', 'tests/test_reconcile_original_mesh.py',
    'compatibility/package-overlays/essentials-brushes-5.2.json',
    'compatibility/mesh-driver-profiles/bmesh-bevel-5.2.json',
    'compatibility/mesh-driver-profiles/operators-5.2.json',
]


def utc():
    return datetime.now(timezone.utc).isoformat()


def identity(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def captured_command(name, command):
    before, began = utc(), time.monotonic()
    with (HERE / (name + '.stdout.log')).open('xb') as stdout, (HERE / (name + '.stderr.log')).open('xb') as stderr:
        process = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
    return {'command': command, 'cwd': str(ROOT), 'started_utc': before, 'finished_utc': utc(),
            'elapsed_seconds': time.monotonic() - began, 'actual_process_returncode': process.returncode,
            'stdout': identity(HERE / (name + '.stdout.log')), 'stderr': identity(HERE / (name + '.stderr.log'))}


def main():
    if (HERE / 'execution.json').exists():
        raise FileExistsError('this validation attempt already exists')
    before = [identity(ROOT / path) for path in SOURCE_PATHS]
    for path, pin in zip(SOURCE_PATHS, before):
        destination = HERE / 'sources' / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write((ROOT / path).read_bytes())
        assert identity(destination)['sha256'] == pin['sha256']
    receipt = {
        'schema': 1, 'kind': 'original-mesh-consumer-infrastructure-validation',
        'started_utc': utc(), 'capture_source': identity(__file__), 'python': identity(Path(sys.executable).resolve()),
        'python_version': sys.version, 'inputs_before': before, 'commands': [],
        'original_blender_executions': 0, 'additional_original_test_pass_credit': 0,
        'extends_829_unittest_scope': False, 'all_upstream_test_parity': False, 'full_feature_parity': False,
    }
    tests = captured_command('unittest', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                                         '-p', 'test_reconcile_original_mesh.py', '-v'])
    receipt['commands'].append(tests)
    text = Path(tests['stderr']['path']).read_text()
    result = re.search(r'Ran (\d+) tests in ([0-9.]+)s\n\nOK\n\Z', text)
    receipt['focused_tests'] = {'actual_exit_code': tests['actual_process_returncode'],
                                 'count': int(result[1]) if result else None,
                                 'unittest_seconds': float(result[2]) if result else None,
                                 'all_passed': tests['actual_process_returncode'] == 0 and result is not None}
    expected = {'bmesh-bevel-5.2': (0, 88, 88, 88, 88), 'operators-5.2': (1, 105, 0, 0, 103)}
    receipt['profiles'] = []
    retained = {}
    for name, (exit_code, count, successes, agreements, raw_matches) in expected.items():
        output = HERE / name
        command = captured_command(name, [sys.executable, 'tools/reconcile_original_mesh.py', '--profile',
                                          'compatibility/mesh-driver-profiles/' + name + '.json', '--output', str(output)])
        receipt['commands'].append(command)
        report = json.loads((output / 'report.json').read_bytes())
        observed = (command['actual_process_returncode'], report['paired_obligation_count'],
                    report['successful_execution_pair_count'], report['outcome_agreement_count'],
                    report['raw_terminal_outcome_agreement_count'])
        assert observed == (exit_code, count, successes, agreements, raw_matches), (name, observed)
        assert report['all_upstream_test_parity'] is False and report['full_feature_parity'] is False
        ledger = captured_command(name + '-strict-ledger', [sys.executable, 'tools/test_parity_ledger.py',
                                    '--contract', str(output / 'contract.json'), '--inventory', str(output / 'inventory.json'),
                                    '--executions', str(output / 'executions.json'), '--evidence-root', str(output),
                                    '--output', str(HERE / (name + '-strict-ledger.json'))])
        receipt['commands'].append(ledger)
        assert ledger['actual_process_returncode'] == exit_code
        independently_consumed = json.loads((HERE / (name + '-strict-ledger.json')).read_bytes())
        assert independently_consumed['pairs'] == report['pairs']
        assert independently_consumed['registrations'] == report['registrations']
        conversion = json.loads((output / 'conversion.json').read_bytes())
        for pin in conversion['inputs']:
            retained[pin['path']] = pin['raw_evidence']
        receipt['profiles'].append({
            'selector': name, 'normalizer_exit': command['actual_process_returncode'],
            'strict_ledger_exit': ledger['actual_process_returncode'], 'gate': report['gate'],
            'paired_obligations': count, 'successful_execution_pairs': successes,
            'qualified_outcome_agreements': agreements, 'raw_terminal_outcome_matches': raw_matches,
            'report': identity(output / 'report.json'), 'conversion': identity(output / 'conversion.json'),
        })
    for path, pin in retained.items():
        actual = identity(ROOT / path)
        assert actual['bytes'] == pin['bytes'] and actual['sha256'] == pin['sha256'], path
    receipt['retained_inputs_verified_after_consumption'] = [
        {'path': path, 'bytes': pin['bytes'], 'sha256': pin['sha256']} for path, pin in sorted(retained.items())]
    receipt['inputs_after'] = [identity(ROOT / path) for path in SOURCE_PATHS]
    receipt['all_source_inputs_unchanged'] = receipt['inputs_before'] == receipt['inputs_after']
    assert receipt['all_source_inputs_unchanged'] and receipt['focused_tests']['all_passed']
    receipt['finished_utc'] = utc()
    write(HERE / 'execution.json', receipt)
    files = []
    for path in sorted(HERE.rglob('*')):
        if path.is_file():
            assert not path.is_symlink()
            pin = identity(path)
            pin['path'] = path.relative_to(HERE).as_posix()
            files.append(pin)
    write(HERE / 'file-inventory.json', {'schema': 1, 'kind': 'mesh-validation-file-inventory', 'files': files,
                                         'file_count': len(files), 'bytes': sum(row['bytes'] for row in files)})
    print(json.dumps({'receipt': identity(HERE / 'execution.json'), 'tests': receipt['focused_tests'],
                       'profiles': receipt['profiles'], 'source_inputs_unchanged': receipt['all_source_inputs_unchanged'],
                       'retained_files_reverified': len(retained), 'inventory': identity(HERE / 'file-inventory.json')}, indent=2))


if __name__ == '__main__':
    main()
