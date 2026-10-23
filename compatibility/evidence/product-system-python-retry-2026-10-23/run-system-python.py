"""Retry one exact original CTest invocation with authenticated private dependencies."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

out = Path(__file__).resolve().parent
repo = out.parents[2]
workspace = repo.parent
prior = repo / 'compatibility/evidence/product-expanded-config-2026-10-23'
target = 'script_validate_on_system_python'
receipt_path = out / 'system-python-execution.json'
if receipt_path.exists():
    raise RuntimeError('previous execution receipt is immutable')


def identity(path):
    data = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def now():
    return datetime.now(timezone.utc).isoformat()


previous = json.loads((prior / 'system-python-execution.json').read_text())
configuration = json.loads((prior / 'configure.json').read_text())
dependency_receipt = json.loads((out / 'dependency-packages.json').read_text())
require(configuration['configured'] and configuration['returncode'] == 0, 'original configuration did not succeed')
require(dependency_receipt['status'] == 'verified_extracted', 'private dependencies are not verified')
original = previous['original_registration']
require(original['name'] == target and original['command'][0] == '/usr/bin/python3.12', 'original interpreter or driver changed')
script = Path(original['command'][1])
require(identity(script) == previous['original_script'], 'original test script bytes changed')
package_root = Path(dependency_receipt['extraction_root'])
package_path = package_root / 'usr/lib/python3/dist-packages'
environment = dict(os.environ)
overrides = dict(previous['environment_overrides'])
inherited_pythonpath = environment.get('PYTHONPATH')
overrides['PYTHONPATH'] = str(package_path) + (os.pathsep + inherited_pythonpath if inherited_pythonpath else '')
environment.update(overrides)
record = {'schema': 1, 'kind': 'selected-original-ctest-execution', 'source_commit': previous['source_commit'],
          'previous_failed_attempt': identity(prior / 'system-python-execution.json'),
          'previous_failed_log': identity(prior / 'system-python.log'),
          'previous_failed_junit': identity(prior / 'system-python-junit.xml'),
          'configuration': identity(prior / 'configure.json'), 'ctest_listing': identity(prior / 'ctest.json'),
          'dependency_receipt': identity(out / 'dependency-packages.json'),
          'original_registration': original, 'original_script': identity(script),
          'system_interpreter': identity(Path(original['command'][0])), 'tool': identity(Path(__file__)),
          'environment_overrides': overrides, 'inherited_pythonpath': inherited_pythonpath,
          'selected_registration_count': 1, 'runtime_leaf_enumeration_complete': False, 'runtime_leaf_count': None,
          'browser_parity': False, 'full_feature_parity': False,
          'scope': 'One original system-Python CTest driver; no inferred leaf cases or browser passes.',
          'started_utc': now(), 'process_completed': False, 'returncode': None, 'ctest_driver_passed': False}
try:
    observation_command = [original['command'][0], str(out / 'observe-interpreter.py')]
    with (out / 'interpreter.stdout.json').open('xb') as stdout, (out / 'interpreter.stderr.txt').open('xb') as stderr:
        observation = subprocess.run(observation_command, cwd=repo, env=environment, stdout=stdout, stderr=stderr, timeout=30)
    record['interpreter_observation'] = {'command': observation_command, 'returncode': observation.returncode,
                                         'stdout': identity(out / 'interpreter.stdout.json'), 'stderr': identity(out / 'interpreter.stderr.txt'),
                                         'tool': identity(out / 'observe-interpreter.py')}
    require(observation.returncode == 0, 'same-interpreter private-package observation failed')
    observed = json.loads((out / 'interpreter.stdout.json').read_text())
    require(observed['executable'] == record['system_interpreter'], 'runtime interpreter identity changed')
    for key in ('setuptools_module', 'pkg_resources_module'):
        require(Path(observed[key]['path']).is_relative_to(package_path), 'dependency import did not use the declared private package')
    command = list(previous['command'])
    command[command.index('--output-junit') + 1] = str(out / 'system-python-junit.xml')
    record['command'] = command
    record['ctest_tool'] = identity(Path(command[0]))
    record['argv_difference_from_previous'] = 'Only --output-junit changes to a fresh evidence destination.'
    listing_command = [command[0], '--test-dir', command[command.index('--test-dir') + 1], '--build-config', 'Release',
                       '--tests-regex', '^' + target + '$', '--show-only=json-v1']
    with (out / 'selected-ctest.json').open('xb') as stdout, (out / 'selected-ctest.stderr.txt').open('xb') as stderr:
        listing_result = subprocess.run(listing_command, cwd=repo, env=environment, stdout=stdout, stderr=stderr, timeout=60)
    require(listing_result.returncode == 0, 'original registration could not be re-read')
    listing = json.loads((out / 'selected-ctest.json').read_text())
    selected = listing['tests']
    require(len(selected) == 1, 'selected original registration count changed')
    for key in ('name', 'command', 'config', 'properties'):
        require(selected[0].get(key) == original.get(key), 'original CTest registration changed: ' + key)
    record['selected_registration_verification'] = {'command': listing_command, 'returncode': listing_result.returncode,
                                                    'listing': identity(out / 'selected-ctest.json'),
                                                    'stderr': identity(out / 'selected-ctest.stderr.txt')}
    record['execution_started_utc'] = now()
    with (out / 'system-python.log').open('xb') as log:
        result = subprocess.run(command, cwd=repo, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=300)
    record.update(process_completed=True, returncode=result.returncode, log=identity(out / 'system-python.log'))
    junit = out / 'system-python-junit.xml'
    if junit.is_file():
        record['ctest_junit'] = identity(junit)
        tree = ET.parse(junit).getroot()
        cases = list(tree.iter('testcase'))
        record['observed_ctest_cases'] = [{**case.attrib, 'failure': case.find('failure') is not None,
                                           'error': case.find('error') is not None, 'skipped': case.find('skipped') is not None}
                                          for case in cases]
        record['ctest_driver_passed'] = result.returncode == 0 and len(cases) == 1 and cases[0].get('name') == target and all(
            cases[0].find(tag) is None for tag in ('failure', 'error', 'skipped'))
    require(identity(script) == previous['original_script'], 'original script changed during execution')
    require(identity(Path(original['command'][0])) == record['system_interpreter'], 'system interpreter changed during execution')
except Exception as error:
    record.update(error_type=type(error).__name__, error=str(error))
    raise
finally:
    record['finished_utc'] = now()
    with receipt_path.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: record[key] for key in ('process_completed', 'returncode', 'ctest_driver_passed', 'runtime_leaf_count', 'browser_parity')}))
raise SystemExit(0 if record['ctest_driver_passed'] else 1)
