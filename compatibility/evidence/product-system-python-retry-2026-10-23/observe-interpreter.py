"""Observe the same system interpreter with the declared private package path."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import setuptools
import pkg_resources


def identity(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


print(json.dumps({'executable': identity(sys.executable), 'version': sys.version, 'sys_path': sys.path,
                  'setuptools_version': setuptools.__version__,
                  'metadata_setuptools_version': importlib.metadata.version('setuptools'),
                  'setuptools_module': identity(setuptools.__file__),
                  'pkg_resources_module': identity(pkg_resources.__file__)}))
