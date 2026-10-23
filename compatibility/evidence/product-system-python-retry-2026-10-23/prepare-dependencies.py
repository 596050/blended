"""Extract exact authenticated Noble Python build dependencies without installing them."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

out = Path(__file__).resolve().parent
repo = out.parents[2]
workspace = repo.parent
apt_root = workspace / 'runtime/product-host-deps/apt'
prefix = workspace / 'runtime/product-system-python-deps/root'
prior = repo / 'compatibility/evidence/product-configure-2026-10-23'
receipt_path = out / 'dependency-packages.json'
if receipt_path.exists() or prefix.exists():
    raise RuntimeError('choose new dependency outputs; previous evidence is immutable')
prefix.mkdir(parents=True)
environment = dict(os.environ)
environment['APT_CONFIG'] = str(apt_root / 'apt.conf')
version = '68.1.2-2ubuntu1.2'
packages = ['python3-setuptools=' + version, 'python3-pkg-resources=' + version]


def identity(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def now():
    return datetime.now(timezone.utc).isoformat()


record = {'schema': 1, 'purpose': 'private dependencies for the unchanged original system-Python CTest driver',
          'started_utc': now(), 'requested_packages': packages, 'stages': [], 'packages': [],
          'environment_overrides': {'APT_CONFIG': str(apt_root / 'apt.conf')},
          'authenticated_index_receipt': identity(prior / 'host-package-index.json'),
          'host_package_status_before': identity(Path('/var/lib/dpkg/status')),
          'extraction_root': str(prefix), 'host_package_installations': 0, 'tests_executed': 0}


def stage(name, command):
    log_path = out / ('dependency-' + name + '.log')
    started = now()
    with log_path.open('xb') as log:
        result = subprocess.run(command, cwd=workspace, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    row = {'name': name, 'command': command, 'started_utc': started, 'finished_utc': now(),
           'returncode': result.returncode, 'log': identity(log_path)}
    record['stages'].append(row)
    with (out / 'dependency-attempts.jsonl').open('a') as stream:
        stream.write(json.dumps(row, sort_keys=True) + '\n')
    require(result.returncode == 0, 'dependency stage failed: ' + name)


try:
    index = json.loads((prior / 'host-package-index.json').read_text())
    require(index['returncode'] == 0, 'previous authenticated index update failed')
    for row in [index['apt_configuration'], index['trusted_keyring'], *index['package_indices']]:
        observed = identity(Path(row['path']))
        require(observed['sha256'] == row['sha256'] and observed['bytes'] == row['bytes'], 'authenticated index input changed')
    options = ['--no-install-recommends', '--no-install-suggests', '--reinstall']
    stage('plan', ['/usr/bin/apt-get', '--simulate', *options, 'install', *packages])
    stage('uris', ['/usr/bin/apt-get', '--print-uris', '--download-only', *options, 'install', *packages])
    stage('download', ['/usr/bin/apt-get', '--yes', '--download-only', *options, 'install', *packages])
    for specification in packages:
        package = specification.split('=')[0]
        metadata = subprocess.check_output(['/usr/bin/apt-cache', 'show', specification], env=environment, text=True)
        metadata_path = out / (package + '.authenticated-metadata.txt')
        with metadata_path.open('x') as stream:
            stream.write(metadata)
        candidates = []
        for paragraph in metadata.split('\n\n'):
            fields = dict(line.split(': ', 1) for line in paragraph.splitlines()
                          if line and not line.startswith(' ') and ': ' in line)
            if fields.get('Package') == package and fields.get('Version') == version and fields.get('SHA256'):
                candidates.append(fields)
        archives = list((apt_root / 'cache/archives').glob(package + '_' + version + '_all.deb'))
        require(len(archives) == 1, 'exact requested package archive missing')
        archive = archives[0]
        actual = identity(archive)
        matching = [fields for fields in candidates if fields['SHA256'] == actual['sha256'] and int(fields['Size']) == actual['bytes']]
        require(bool(matching), 'package bytes differ from authenticated official metadata')
        fields = matching[0]
        control = subprocess.check_output(['dpkg-deb', '--field', str(archive), 'Package', 'Version', 'Architecture'], text=True)
        require('Package: ' + package in control and 'Version: ' + version in control and 'Architecture: all' in control,
                'package control identity changed')
        result = subprocess.run(['dpkg-deb', '--extract', str(archive), str(prefix)], capture_output=True, text=True)
        require(result.returncode == 0, 'private package extraction failed')
        record['packages'].append({**actual, 'package': package, 'version': version, 'architecture': 'all',
                                   'authenticated_sha256': fields['SHA256'], 'official_archive_path': fields['Filename'],
                                   'depends': fields.get('Depends', ''), 'metadata': identity(metadata_path),
                                   'extraction_returncode': result.returncode, 'extraction_stdout': result.stdout,
                                   'extraction_stderr': result.stderr})
    files = []
    for path in sorted(prefix.rglob('*')):
        if path.is_symlink():
            files.append({'relative_path': path.relative_to(prefix).as_posix(), 'symlink_target': os.readlink(path)})
        elif path.is_file():
            files.append({'relative_path': path.relative_to(prefix).as_posix(), **{k: v for k, v in identity(path).items() if k != 'path'}})
    with (out / 'extracted-package-files.json').open('x') as stream:
        json.dump({'files': files}, stream, indent=2)
        stream.write('\n')
    record['extracted_files'] = identity(out / 'extracted-package-files.json')
    record['status'] = 'verified_extracted'
except Exception as error:
    record.update(status='failed', error_type=type(error).__name__, error=str(error))
    raise
finally:
    record.update(finished_utc=now(), host_package_status_after=identity(Path('/var/lib/dpkg/status')),
                  tool=identity(Path(__file__)))
    require(record['host_package_status_before'] == record['host_package_status_after'], 'host package status changed')
    with receipt_path.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': record['status'], 'packages': len(record['packages']), 'host_package_installations': 0}))
