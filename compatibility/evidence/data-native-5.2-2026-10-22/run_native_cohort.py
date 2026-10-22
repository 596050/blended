#!/usr/bin/env python3
"""Local discovery receipt for unchanged upstream candidate suites; no browser claim."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent
SOURCE_REPO = Path('/workspace/scratch/d63596d831b2/research_ports/native-gessa')
COMMIT = 'fbe6228777e7d9afefcd61a413844e790ae75db7'
BINARY = Path('/workspace/scratch/d63596d831b2/research_tests/native_ref/blender-5.2.0-linux-x64/blender')
ARCHIVE = BINARY.parent.parent / 'blender-5.2.0-linux-x64.tar.xz'
ARCHIVE_SHA256 = '96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48'
BINARY_SHA256 = '83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27'
MODULES = ('bl_id_management.py', 'bl_rna_accessors.py', 'bl_pyapi_idprop.py', 'bl_blendfile_io.py')
DEPENDENCIES = {
    'bl_id_management.py': ['bpy', 'unittest', 'random', 'factory startup datablocks'],
    'bl_rna_accessors.py': ['bpy', 'unittest', 'factory startup datablocks'],
    'bl_pyapi_idprop.py': ['bpy', 'rna_prop_ui', 'idprop', 'unittest', 'array', 'numpy for five conditional tests'],
    'bl_blendfile_io.py': ['bpy', 'bl_blendfile_utils.py', 'writable output directory', 'factory startup datablocks'],
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def parse_unittest_outcomes(name, lines):
    """Retain native warnings between a verbose case header and its outcome."""
    outcomes, pending = [], None
    statuses = re.compile(r'ok|FAIL|ERROR|skipped .+|expected failure|unexpected success')
    for line in lines:
        found = re.fullmatch(r'(test_\S+) \(([^)]+)\) \.\.\. (.*)', line)
        if found:
            if pending is not None:
                raise RuntimeError('case outcome missing before the next test header')
            pending = {'id': name + '::' + found[2], 'interleaved_output': []}
            if statuses.fullmatch(found[3]):
                pending['outcome'] = found[3]
                outcomes.append(pending)
                pending = None
            elif found[3]:
                pending['interleaved_output'].append(found[3])
        elif pending is not None:
            if statuses.fullmatch(line):
                pending['outcome'] = line
                outcomes.append(pending)
                pending = None
            else:
                pending['interleaved_output'].append(line)
    if pending is not None:
        raise RuntimeError('final case outcome missing')
    return outcomes


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    sources = ROOT / 'sources'
    sources.mkdir(exist_ok=True)
    assert ARCHIVE.stat().st_size == 384441228
    assert sha256(ARCHIVE) == ARCHIVE_SHA256
    assert sha256(BINARY) == BINARY_SHA256
    manifest = {'schema': 1, 'scope': 'candidate Blender 5.2.0 next-suite discovery',
                'upstream_commit': COMMIT, 'browser_executed': False, 'product_target_parity': False,
                'source_files': []}
    for name in (*MODULES, 'bl_blendfile_utils.py', 'CMakeLists.txt'):
        path = 'tests/python/' + name
        data = subprocess.check_output(['git', 'show', COMMIT + ':' + path], cwd=SOURCE_REPO)
        destination = sources / name
        destination.write_bytes(data)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        manifest['source_files'].append({'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                         'git_blob_sha1': blob, 'upstream_url': 'https://github.com/blender/blender/blob/' + COMMIT + '/' + path})
    (ROOT / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    identity_code = (
        "import bpy,json; print('BLENDED_COHORT_IDENTITY:'+json.dumps({"
        "'version':list(bpy.app.version),'build_hash':bpy.app.build_hash.decode(),"
        "'version_string':bpy.app.version_string,'binary_path':bpy.app.binary_path}),flush=True)"
    )
    receipt = {'schema': 1, 'scope': 'unchanged upstream native suite discovery only',
               'upstream_commit': COMMIT, 'browser_executed': False, 'full_feature_parity': False,
               'artifact': {'archive_sha256': ARCHIVE_SHA256, 'archive_bytes': ARCHIVE.stat().st_size,
                            'executable_sha256': BINARY_SHA256}, 'modules': []}
    for name in MODULES:
        command = [str(BINARY), '--background', '--factory-startup', '--threads', '1',
                   '--python-exit-code', '1', '--python-expr', identity_code, '--python', str(sources / name)]
        if name == 'bl_blendfile_io.py':
            command += ['--', '--output-dir', str(ROOT / 'generated-blendfiles')]
        else:
            command += ['--', '--verbose']
        started = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120, check=False)
        elapsed = time.monotonic() - started
        log_path = ROOT / (name.removesuffix('.py') + '.log')
        log_path.write_bytes(result.stdout)
        lines = result.stdout.decode('utf-8', 'replace').splitlines()
        identities = [json.loads(line.split(':', 1)[1]) for line in lines if line.startswith('BLENDED_COHORT_IDENTITY:')]
        identity_ok = len(identities) == 1 and identities[0]['version'] == [5, 2, 0] and identities[0]['build_hash'] == COMMIT[:12]
        row = {'source': next(item for item in manifest['source_files'] if item['path'].endswith('/' + name)),
               'dependencies': DEPENDENCIES[name], 'external_fixtures': [], 'command': command,
               'returncode': result.returncode, 'elapsed_seconds': elapsed,
               'identity': identities[0] if len(identities) == 1 else identities, 'identity_verified': identity_ok,
               'log': {'path': log_path.name, 'bytes': log_path.stat().st_size, 'sha256': sha256(log_path)}}
        if name == 'bl_blendfile_io.py':
            tree = ast.parse((sources / name).read_bytes())
            row['declared_case_ids'] = [node.name + '.' + child.name for node in tree.body if isinstance(node, ast.ClassDef)
                                        for child in node.body if isinstance(child, ast.FunctionDef) and child.name.startswith('test_')]
            row['reporting_scope'] = 'unchanged custom upstream main completed; no per-case outcome instrumentation'
            row['case_results'] = None
            row['status'] = 'module_completed' if result.returncode == 0 and identity_ok else 'failed'
        else:
            outcomes = parse_unittest_outcomes(name, lines)
            counts = [int(found[1]) for line in lines if (found := re.fullmatch(r'Ran (\d+) tests? in .+s', line))]
            row['case_results'] = outcomes
            row['tests_run'] = counts[0] if len(counts) == 1 else None
            row['all_reported_cases_passed'] = bool(outcomes) and all(item['outcome'] == 'ok' for item in outcomes)
            row['status'] = ('passed' if result.returncode == 0 and identity_ok and row['all_reported_cases_passed'] and
                             row['tests_run'] == len(outcomes) else 'failed')
            if name == 'bl_pyapi_idprop.py':
                row['conditional_numpy_case_ids'] = [item['id'] for item in outcomes if 'TestBufferProtocol_Numpy.' in item['id']]
                assert len(row['conditional_numpy_case_ids']) == 5
        receipt['modules'].append(row)
        (ROOT / 'native-cohort-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'module': name, 'status': row['status'], 'tests_run': row.get('tests_run'),
                          'declared_custom_cases': len(row.get('declared_case_ids', [])), 'elapsed_seconds': elapsed}), flush=True)
    receipt['generated_files'] = [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': sha256(path)}
                                  for path in sorted((ROOT / 'generated-blendfiles').glob('*')) if path.is_file()]
    receipt['status'] = 'completed' if all(row['status'] in ('passed', 'module_completed') for row in receipt['modules']) else 'failed'
    (ROOT / 'native-cohort-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if receipt['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
