#!/usr/bin/env python3
"""Normalize two retained original Blender mesh captures, separately.

No Blender, browser, captured Python producer, or original test is executed.
The selected successful native invocation supplies the fixed denominator.
Original stdout, source specifications, process receipts and launcher events
are checked independently before the unchanged generic ledger is called.
Retained measurements remain producer evidence, not a fresh runtime measurement.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import timedelta
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any

try:
    from .test_parity_ledger import assess, canonical_sha256, digest, load_json, require
    from .reconcile_unittest_matrix import (
        BROWSER as CONTEXT_BROWSER, NATIVE as CONTEXT_NATIVE, Captured, Evidence,
        encoded, engine_files, identity, read_contexts, sha, timestamp, unique_refs,
    )
    from .unittest_cohort import CMAKE_SOURCES, UPSTREAM_SHA
except ImportError:
    from test_parity_ledger import assess, canonical_sha256, digest, load_json, require
    from reconcile_unittest_matrix import (
        BROWSER as CONTEXT_BROWSER, NATIVE as CONTEXT_NATIVE, Captured, Evidence,
        encoded, engine_files, identity, read_contexts, sha, timestamp, unique_refs,
    )
    from unittest_cohort import CMAKE_SOURCES, UPSTREAM_SHA


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_ROOT = PurePosixPath('/workspace/scratch/d63596d831b2/blended')
HISTORICAL_RUNTIME = HISTORICAL_ROOT.parent / 'runtime'
TARGET = {'repository': 'blender/blender', 'commit': UPSTREAM_SHA}
EV = 'compatibility/evidence/'
CONFIGURATION = 'blender-5.2-source-derived-original-mesh'
NATIVE = 'native-reference'
CATALOG = ('tools/upstream_invocations_5_2.json', 140627,
           'c326f9a99e665b15901dda134afd0c074c5c150441ed2971d977ce134a1fe7f2')
HELPER = ('tests/python/modules/mesh_test.py', 40007,
          'fd764b05f86479f45eb52731eb2009b7321dfa74a258c4886c4c73083bf3ee5e')
PROBE = ('tools/probe_browser_port.py', 75480,
         '2dd05ff937337d861972e224c63639f90c471002eab496a1f2595853303672cd')
SAVED_PROBE = EV + 'source-rebuild-unittest-39986612484/main/harness/tools/probe_browser_port.py'
OVERLAY_TOOL = ('tools/browser_package_overlay.py', 19562,
                'af2c68cb6c60c9908e5ade48d7b811a4efac00221db9fd0e86e53a3defd6bacc')
SOURCE_ARCHIVE = (78785728, 'de0fdadf28015805370d1815facaf9139fbb1e161d8c540d1765484beabb3a99')
CONTEXT_IDENTITIES = {
    'native_archive': (384441228, '96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48'),
    'native_executable': (174666336, '83e8261eace07a5337f71b52d156c1eece1a6ba913403cc6406182ae58bacf27'),
    'native_configuration': (2902, '56567a375fa9f3b505be355e3e9676f67f997a42788fbe15904907722712aaae'),
    'browser_executable': (297680200, 'ed05e73a2cdf875326fcfa438b31c71a6a885a353610731dd52090dfc476f778'),
    'engine_archive': (110053572, '3d813cf86ee16eea1530251942f481fc96ec693a8202d9f39392c82f28266910'),
    'source_build': (165401, '5ed2a839fc340d16de08a096be3db74506a4cffdaaa87f40fbd1553810b53ce3'),
    'cmake_cache': (64011, '026c70cc6d3a121258bbf3986c6fea94d823f8e74fdfb6c58227e8ce3eebb773'),
}
ENGINE_IDENTITIES = {
    'blender_browser.js': ('fc6757edf1624671c766a847ffee391b638b90f35874b1b54fbdd1c8cfe95ffb', 694154),
    'blender_browser.wasm': ('27b25e78567bc6b95b81ef43fbf255c91b3655a9d4b6b9615296621e5d1fcf23', 119225569),
    'blender_browser.data': ('a66c183e1248e08426f28a73c961676b9f8d9bc7df6de4888f74cecc0dcd03a2', 171547054),
}
BACKGROUND_ARGUMENTS = [
    '--background', '--console-crash-handler', '--factory-startup', '--debug-memory',
    '--debug-exit-on-error', '--python-exit-code', '1', '--python-expr',
    "import bpy;bpy.context.preferences.filepaths.file_preview_type='NONE'",
]
THREAD_ENVIRONMENT = {name: '1' for name in
                      ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}
BROWSER_ENVIRONMENT = {
    'BLENDER_SYSTEM_RESOURCES': '/bw', 'BLENDER_SYSTEM_PYTHON': '/bw/python',
    'BLENDER_SYSTEM_SCRIPTS': '/bw/scripts', 'BLENDER_SYSTEM_DATAFILES': '/bw/datafiles',
    'BLENDER_USER_RESOURCES': '/projects', 'TMPDIR': '/projects/.recovery', **THREAD_ENVIRONMENT,
}
PROFILES = {
    'bmesh-bevel-5.2': {
        'registration': 'bmesh_bevel', 'index': 49, 'count': 88, 'marker': 'BEVEL_BROWSER_EVENT ',
        'source_dir': 'bmesh-bevel-source-native-5.2-2026-10-23',
        'native_dir': 'bmesh-bevel-source-native-elevated-5.2-2026-10-23',
        'browser_dir': 'bmesh-bevel-browser-essentials-5.2-2026-10-23',
        'attempt': 'attempt-03-v2-elevated',
        'profile': 'original-bmesh-bevel-essentials-chromium-custom-launcher-v2',
        'browser_kind': 'original-bmesh-bevel-browser-invocation',
        'host_kind': 'browser-bevel-host-process-capture',
        'script': ('tests/python/bevel_operator.py', 20590,
                   'f6643470ca03ebe4b6517f5f2151a6699b66557cb80828f0f6f8ebfa22c3fd9a'),
        'fixture': ('tests/files/modeling/bevel_regression.blend', 2387547,
                    'dad2aa2c02cb6ceb9e025b729e1886a95b3d744c10dce56503adbd15ec312771'),
        'native_driver': ('run-native-retry.py', 8203,
                          '04c0e9d10a8dc95c5642721ef26ed43ec2f8704128e1bb1885efd46c993d8ea6'),
        'parser': ('run-native.py', 15139,
                   '98f2ebc9f46b28a0452e4e0dcb37c256d76ec76a24213475ae0d8795eabf1d33'),
        'producer_files': {
            'run-browser-v2.py': (21465, '0253d2d399fa6cc8aac5ccfed775e16427fa5663edd6667d8452324f96f9d487'),
            'launcher-v2.js': (8345, 'e35ca3b593406aa83b27e28197018ad12dfcb5ec278d13507aa69cc893dae84d'),
            'launcher-v2.html': (284, 'b0372c0527cc61f78abb65906b14b0dd82be343a83b43091d5915747c46db6cf'),
            'capture-process-v2.py': (2845, '344f7269004198d511f32ba15b3c3decfbddc71acb7131c662f356c8579a3fa3'),
        },
    },
    'operators-5.2': {
        'registration': 'operators', 'index': 74, 'count': 105, 'marker': 'OPERATORS_BROWSER_EVENT ',
        'source_dir': 'mesh-operators-source-native-5.2-2026-10-23',
        'native_dir': 'mesh-operators-source-native-5.2-2026-10-23',
        'browser_dir': 'mesh-operators-browser-essentials-5.2-2026-10-23',
        'attempt': 'attempt-01-elevated',
        'profile': 'original-mesh-operators-essentials-chromium-custom-launcher-v2',
        'browser_kind': 'original-mesh-operators-browser-invocation',
        'host_kind': 'browser-operators-host-process-capture',
        'script': ('tests/python/operators.py', 39415,
                   'a9e934a9281b8a7746d414e868b42a9dd93bf163b99b8add98ace8bd1fa4983f'),
        'fixture': ('tests/files/modeling/operators.blend', 4028858,
                    '345857f0185fc38799d26e671e88ed06bf7754163c0ea58b4b8475c57908f9cc'),
        'native_driver': ('run-native.py', 16473,
                          '5bd8f7d04927f420233861416512e68cfdfa5ad115a64d4c8a2716fe7cbbf7df'),
        'parser': ('run-native.py', 16473,
                   '5bd8f7d04927f420233861416512e68cfdfa5ad115a64d4c8a2716fe7cbbf7df'),
        'producer_files': {
            'run-browser-v2.py': (21570, '6c82d08ef4eed768ecf91a15f5e95192615d4d6899b951cb1c76f56592eb2ba8'),
            'launcher-v2.js': (8357, '0b5c320a3a4e66db3524832b500f8bbadf7e565fe9a009735116da678770c204'),
            'launcher-v2.html': (288, '0fe2bd362e7370bdd1f03ad80087567c3b635e1d122d3afcea03de19c944253c'),
            'capture-process-v2.py': (2849, '363f827aca2924e3dd01e490a0f9fca4af77b8024d56e5cb038912db098310b7'),
        },
    },
}
POLICY = {
    'schema': 1, 'name': 'unchanged-original-spec-mesh-run-all-v1',
    'entrypoint': 'The original script main and --run-all-tests branch with comparison enabled.',
    'case_identity': 'Original upstream commit, registration, source path, line, name and specification SHA256.',
    'oracle': 'Unchanged original mesh_test.py comparison and validation; no invented subtest identities.',
    'passed': 'Exactly one original PASSED marker, Mesh Comparison : Same, and Mesh Validation : Valid.',
    'failed': 'Original FAILED marker and its complete original comparison and validation diagnostics.',
    'expected_failure': 'These selected original drivers have no expectedFailure annotation.',
    'completion': 'Case observations are distinct from original main and host process completion.',
}


def exact(value: Any, expected: Any, label: str) -> None:
    """JSON equality that does not silently identify booleans with integers."""
    require(canonical_sha256(value) == canonical_sha256(expected), label)


def integer(value: Any, label: str, *, nullable: bool = False) -> int | None:
    require(type(value) is int or nullable and value is None, label + ' must be an integer' + (' or null' if nullable else ''))
    return value


def boolean(value: Any, label: str) -> bool:
    require(type(value) is bool, label + ' must be boolean')
    return value


def duration(value: Any, label: str) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            label + ' must be a finite nonnegative number')
    return value


def document(value: Any, kind: str) -> dict:
    require(isinstance(value, dict) and type(value.get('schema')) is int and value['schema'] == 1
            and value.get('kind') == kind, 'unexpected document kind or schema: ' + kind)
    return value


def pin_identity(pin: Any, label: str) -> tuple[str, int]:
    require(isinstance(pin, dict) and type(pin.get('bytes')) is int and pin['bytes'] >= 0,
            label + ' requires an integer byte count')
    return digest(pin.get('sha256'), label + ' sha256'), pin['bytes']


def pinned_source(captured: Captured, expected: tuple, label: str) -> None:
    require(pin_identity(captured.ref, label) == (expected[-1], expected[-2]),
            label + ' differs from reviewed exact source')


class MeshEvidence(Evidence):
    """Relocate only the explicit historical checkout and exact saved producer."""

    def __init__(self, root: Path, output: Path):
        self.seen: dict[str, dict] = {}
        self.saved_bindings: dict[str, dict] = {}
        super().__init__(root, output)

    def resolve(self, name: str | Path, base: Path | None = None) -> Path:
        name = str(name)
        require(name and '\\' not in name and not name.startswith('//')
                and all(ord(char) >= 32 and ord(char) != 127 for char in name), 'unsafe mesh evidence path')
        path = PurePosixPath(name)
        require(path.as_posix() == name and '.' not in path.parts, 'noncanonical mesh evidence path')
        if path.is_absolute():
            require('..' not in path.parts, 'noncanonical absolute mesh evidence path')
            if path.is_relative_to(HISTORICAL_ROOT):
                relative = path.relative_to(HISTORICAL_ROOT)
                path = PurePosixPath(self.root) / relative
            else:
                require(path.is_relative_to(PurePosixPath(self.root)), 'unbound external mesh evidence path')
        else:
            require(base is not None or '..' not in path.parts, 'unsafe relative mesh evidence path')
            path = PurePosixPath(base or self.root) / path
        # The shared reader checks every lexical component for symlinks and
        # confinement before reading. Context pins may use an explicit ../.
        return super().resolve(str(path))

    def capture(self, path: str | Path, pin: dict | None = None, base: Path | None = None) -> Captured:
        resolved = self.resolve(path, base)
        relative = resolved.relative_to(self.root).as_posix()
        if pin is not None:
            pin_identity(pin, 'mesh evidence')
        captured = super().capture(resolved, pin or self.seen.get(relative))
        if relative in self.seen:
            exact(captured.ref, self.seen[relative], 'mesh evidence changed during normalization: ' + relative)
        self.seen[relative] = captured.ref
        return captured

    def reference(self, pin: dict, base: Path | None = None) -> Captured:
        require(isinstance(pin, dict) and isinstance(pin.get('path'), str), 'bound mesh evidence reference is missing')
        original = str(HISTORICAL_ROOT / PROBE[0])
        if pin['path'] == original:
            require(pin_identity(pin, 'historical probe') == (PROBE[2], PROBE[1]),
                    'historical probe differs from reviewed exact source')
            result = self.capture(SAVED_PROBE, pin)
            self.saved_bindings[original] = {'original_path': original, 'saved_path': SAVED_PROBE,
                                            'bytes': PROBE[1], 'sha256': PROBE[2], 'raw_evidence': result.ref}
            return result
        return self.capture(pin['path'], pin, base)

    def verify_unchanged(self) -> None:
        for path, pin in list(self.seen.items()):
            self.capture(path, pin)


def selector_paths(profile: dict) -> dict[str, str]:
    native = EV + profile['native_dir'] + '/'
    browser = EV + profile['browser_dir'] + '/'
    return {
        'native_execution': native + 'execution.json',
        'native_summary': native + 'summary.json',
        'browser_execution': browser + profile['attempt'] + '/execution.json',
        'host_capture': browser + profile['attempt'] + '-host/execution.json',
        'browser_summary': browser + 'summary.json',
        'native_context': EV + 'runtime-context-2026-10-23/native-context.json',
        'browser_context': EV + 'runtime-context-essentials-2026-10-23/browser-context.json',
    }


def read_selector(evidence: MeshEvidence, path: Path) -> tuple[Captured, dict, dict[str, Captured]]:
    captured = evidence.capture(path)
    selected = document(captured.json(), 'retained-original-mesh-profile')
    exact(selected.get('target'), TARGET, 'selector targets another upstream revision')
    require(selected.get('id') in PROFILES, 'unknown original mesh profile')
    profile = PROFILES[selected['id']]
    exact(selected.get('registration'), {'name': profile['registration'], 'source_declaration_index': profile['index'],
                                       'observed_native_case_count': profile['count']}, 'selector registration changed')
    require(selected.get('historical_repository_root') == str(HISTORICAL_ROOT), 'unknown historical checkout')
    exact(selected.get('claim_limits'), {'configured_ctest_execution': False, 'all_upstream_test_parity': False,
                                       'full_feature_parity': False, 'new_original_executions': 0,
                                       'extends_829_unittest_scope': False}, 'selector expands its claim scope')
    exact(selected.get('saved_copies'), [{'original_path': str(HISTORICAL_ROOT / PROBE[0]),
                                          'path': SAVED_PROBE, 'bytes': PROBE[1], 'sha256': PROBE[2]}],
          'selector lacks its exact historical producer mapping')
    inputs = selected.get('inputs')
    require(isinstance(inputs, dict) and set(inputs) == set(selector_paths(profile)), 'selector input roles changed')
    retained = {}
    for role, expected in selector_paths(profile).items():
        require(isinstance(inputs[role], dict) and inputs[role].get('path') == expected,
                'selector does not identify the selected original ' + role)
        retained[role] = evidence.reference(inputs[role])
    return captured, profile, retained


def static_specs(script: bytes, upstream_path: str) -> list[dict]:
    """Inspect literal declarations solely to bind already observed identities."""
    source = script.decode('utf-8')
    tree = ast.parse(source)
    mains = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main']
    require(len(mains) == 1, 'original mesh driver must have one main declaration')
    assignments = [node for node in mains[0].body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'tests' for target in node.targets)]
    require(len(assignments) == 1 and isinstance(assignments[0].value, ast.List),
            'original mesh specification list changed')
    rows = []
    for node in assignments[0].value.elts:
        require(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'SpecMeshTest' and bool(node.args), 'unknown original mesh specification')
        name = ast.literal_eval(node.args[0])
        require(isinstance(name, str) and bool(name), 'mesh case name must be literal text')
        segment = ast.get_source_segment(source, node)
        require(segment is not None, 'original mesh specification source is missing')
        rows.append({'name': name, 'line': node.lineno, 'upstream_path': upstream_path,
                     'source_sha256': sha(script), 'spec_sha256': sha(segment.encode('utf-8'))})
    require(len({row['name'] for row in rows}) == len(rows), 'duplicate original mesh specification')
    return rows


def original_observations(text: str, declarations: list[dict]) -> dict:
    """Independently parse original markers; never execute a captured producer."""
    lines, starts, active = text.splitlines(), [], None
    for index, line in enumerate(lines):
        match = re.fullmatch(r'START (.+) test\.', line)
        if match:
            active = match[1]
            starts.append((index, active))
        terminal = re.fullmatch(r'(?:PASSED (.+) test successfully\.|FAILED (.+) test with the following: )', line)
        if terminal:
            require(active is not None and (terminal[1] or terminal[2]) == active,
                    'orphan or mismatched original terminal marker')
        elif line.startswith(('START ', 'PASSED ', 'FAILED ')):
            require(match is not None, 'malformed original mesh marker')
    declared = {row['name']: row for row in declarations}
    observations = []
    for position, (index, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        segment = lines[index + 1:end]
        passed = [line for line in segment if line == f'PASSED {name} test successfully.']
        failed = [line for line in segment if line == f'FAILED {name} test with the following: ']
        require(len(passed) + len(failed) <= 1, 'duplicate or contradictory original terminal marker')
        comparison = [line.split(' : ', 1)[1] for line in segment if line.startswith('Mesh Comparison : ')]
        validation = [line.split(' : ', 1)[1] for line in segment if line.startswith('Mesh Validation : ')]
        if passed and comparison == ['Same'] and validation == ['Valid']:
            status = 'passed'
        elif failed:
            status = 'failed'
        else:
            status = 'ambiguous_or_incomplete'
        row = {'name': name, 'status': status, 'start_log_line': index + 1,
               'terminal_log_lines': passed + failed, 'mesh_comparison': comparison, 'mesh_validation': validation}
        if name in declared:
            row['original_source_declaration'] = declared[name]
        observations.append(row)
    counts = Counter(row['name'] for row in observations)
    return {
        'kind': 'original-mesh-test-stdout-observations', 'observations': observations,
        'observed_starts': len(observations),
        'observed_passes': sum(row['status'] == 'passed' for row in observations),
        'observed_failures': sum(row['status'] == 'failed' for row in observations),
        'observed_ambiguous_or_incomplete': sum(row['status'] == 'ambiguous_or_incomplete' for row in observations),
        'duplicate_names': sorted(name for name, count in counts.items() if count > 1),
        'missing_declared_names': sorted(set(declared) - set(counts)),
        'unexpected_names': sorted(set(counts) - set(declared)),
        'static_declarations_used_only_to_detect_missing_or_unexpected_cases': True,
    }


def original_id(profile: dict, specification: dict) -> str:
    return ':'.join(str(value) for value in (UPSTREAM_SHA, profile['registration'], specification['upstream_path'],
                                            specification['line'], specification['name'], specification['spec_sha256']))


def check_context_profile(context: dict) -> None:
    """These historical launcher profiles belong to one exact measured pair."""
    native = document(context.get('native'), 'artifact-bound-native-context')
    browser = document(context.get('browser'), 'artifact-bound-browser-context')
    checks = {
        'native_archive': native.get('archive'), 'native_executable': native.get('executable'),
        'browser_executable': browser.get('browser'),
        'engine_archive': browser.get('engine_archive'), 'source_build': context['source'].ref,
        'cmake_cache': browser.get('build_configuration'),
    }
    for name, pin in checks.items():
        size, hash_value = CONTEXT_IDENTITIES[name]
        require(pin_identity(pin, name) == (hash_value, size),
                'selected mesh profile differs from its exact historical ' + name)
    require(context['contexts'][CONTEXT_NATIVE]['build_config_sha256'] == CONTEXT_IDENTITIES['native_configuration'][1],
            'selected mesh profile differs from its exact historical native configuration measurement')
    require(context.get('engine_files') == ENGINE_IDENTITIES, 'selected mesh profile changed its measured engine members')
    require(browser['browser'].get('version') == 'Google Chrome for Testing 155.0.8059.39',
            'selected mesh profile changed its measured Chrome version')
    require(context.get('overlay') is not None and context.get('producer') is None,
            'selected mesh profiles require the original Essentials context, not a newer source build')


def check_native(evidence: MeshEvidence, profile: dict, inputs: dict, context: dict) -> dict:
    native = inputs['native_execution'].json()
    kind = 'source-derived-original-blender-native-execution'
    if profile['registration'] == 'bmesh_bevel':
        kind += '-elevated-retry'
    document(native, kind)
    require(native.get('source_commit') == UPSTREAM_SHA and native.get('ctest_name_from_source') == profile['registration']
            and native.get('configured_ctest_execution') is False, 'native invocation identity changed')
    require(native.get('actual_process_started') is True and native.get('timed_out') is False
            and integer(native.get('actual_process_returncode'), 'native exit') == 0
            and native.get('termination_reason') is None and native.get('completed_successfully') is True,
            'selected native inventory requires a successfully completed original process')
    require(integer(native.get('original_blender_invocations_executed'), 'native invocation count') == 1,
            'native inventory combines invocations')
    prospective_file = evidence.reference(native.get('prospective_command'))
    prospective = prospective_file.json()
    original_file = (evidence.reference(prospective['original_prospective_command'])
                     if profile['registration'] == 'bmesh_bevel' else prospective_file)
    original = document(original_file.json(), 'source-derived-original-blender-invocation')
    require(pin_identity(original.get('source_archive'), 'original source archive') == (SOURCE_ARCHIVE[1], SOURCE_ARCHIVE[0])
            and original['source_archive'].get('path') == str(HISTORICAL_RUNTIME / 'upstream-5.2.tar.gz'),
            'original source archive identity changed')
    driver = evidence.reference(native.get('capture_driver'))
    pinned_source(driver, profile['native_driver'], 'native capture driver')
    exact(prospective.get('capture_driver'), native['capture_driver'], 'native prospective driver mismatch')
    parser = evidence.reference(original.get('capture_driver'))
    pinned_source(parser, profile['parser'], 'original log parser')
    if profile['registration'] == 'bmesh_bevel':
        document(prospective, 'source-derived-original-blender-invocation-elevated-retry')
        exact(native.get('reused_capture_helper'), original['capture_driver'], 'native retry helper changed')
        exact(prospective.get('reused_capture_helper'), original['capture_driver'], 'prospective retry helper changed')
        exact(native.get('original_attempt_preserved'), prospective.get('original_attempt'), 'native retry lost its first attempt')
        evidence.reference(native['original_attempt_preserved'])
        require(prospective.get('original_argv_unchanged') is True
                and prospective.get('source_fixture_and_executable_identities_unchanged') is True,
                'native retry changed original execution')
    catalog = evidence.reference(original.get('declaration_catalog'))
    pinned_source(catalog, CATALOG, 'original declaration catalog')
    declaration = catalog.json()['declarations'][profile['index']]
    exact(original.get('original_declaration'), declaration, 'original CMake declaration changed')
    source_root = str(HISTORICAL_ROOT / (EV + profile['source_dir'] + '/source'))
    expected_sources = [(row['upstream_path'], row['bytes'], row['sha256']) for row in CMAKE_SOURCES]
    expected_sources.append(('build_files/cmake/testing.cmake', 14453,
                             '87f69e23584842dad3f4942754f6e9891543c718ee16d8f4db774d524487c8c8'))
    expected_sources += [profile['script'], HELPER, profile['fixture']]
    pins = original.get('inputs')
    require(isinstance(pins, list) and len(pins) == len(expected_sources), 'original source closure changed')
    captured_sources = []
    for pin, spec in zip(pins, expected_sources):
        require(pin.get('path') == source_root + '/' + spec[0], 'original source path changed')
        source = evidence.reference(pin)
        pinned_source(source, spec, 'original source or fixture ' + spec[0])
        captured_sources.append(source)
    exact(native.get('inputs_after'), pins, 'native original inputs changed')
    exact(prospective.get('inputs'), pins, 'native prospective inputs changed')
    require(native.get('all_original_inputs_unchanged') is True, 'native original input preservation is absent')
    fixture = pins[-1]
    pointer = evidence.reference(original.get('fixture_original_pointer')).data.decode('ascii')
    require(pointer == f'version https://git-lfs.github.com/spec/v1\noid sha256:{fixture["sha256"]}\nsize {fixture["bytes"]}\n',
            'original fixture differs from its exact LFS pointer')
    require(original.get('fixture_expected_sha256') == fixture['sha256']
            and type(original.get('fixture_expected_bytes')) is int
            and original['fixture_expected_bytes'] == fixture['bytes'], 'original fixture expectation changed')
    require(pin_identity(original.get('fixture_payload_source'), 'fixture payload') == pin_identity(fixture, 'fixture'),
            'original fixture payload provenance differs')
    exact(native.get('native_executable'), context['native']['executable'], 'native executable differs from measured context')
    exact(original.get('native_executable'), native['native_executable'], 'original native executable differs')
    command = [native['native_executable']['path'], *BACKGROUND_ARGUMENTS, pins[-1]['path'],
               '--python', pins[-3]['path'], '--', '--run-all-tests']
    cwd = str(HISTORICAL_ROOT / (EV + profile['source_dir']))
    for value in (original, prospective):
        exact(value.get('command'), command, 'exact original --run-all-tests command changed')
        require(value.get('cwd') == cwd and value.get('source_commit') == UPSTREAM_SHA
                and value.get('configured_ctest_execution') is False, 'original native cwd or source scope changed')
        exact(value.get('environment_overrides'), THREAD_ENVIRONMENT, 'original native environment changed')
        require(value.get('oracle_update_environment_absent') is True and value.get('verbose_environment_present') is False,
                'original native update or verbose mode is enabled or unobserved')
    require(original.get('ctest_configuration_receipt') is None
            and original.get('original_sources_modified') is False
            and original.get('original_assertions_or_tolerances_modified') is False
            and original.get('static_declared_specs_are_runtime_results') is False
            and original.get('native_source_build_correspondence_verified') is False
            and original.get('full_feature_parity') is False, 'original source claim boundary changed')
    if profile['registration'] == 'operators':
        exact(original.get('test_selection'), {'full_original_run_all_tests': True, 'case_filter': None,
              'failfast': False, 'shard': None, 'random_seed': 'Original operators.py calls seed(0), unchanged.'},
              'original operator selection changed')
    specifications = static_specs(captured_sources[-3].data, profile['script'][0])
    exact(original.get('static_declared_specs'), specifications, 'original specification declarations changed')
    native_log = evidence.reference(native.get('raw_log'))
    observations = original_observations(native_log.data.decode('utf-8'), specifications)
    exact(native.get('original_case_observations'), observations, 'native observations contradict original stdout')
    require(not observations['duplicate_names'] and not observations['unexpected_names']
            and not observations['missing_declared_names'] and observations['observed_passes'] == profile['count']
            and observations['observed_starts'] == profile['count'], 'native original inventory is incomplete or ambiguous')
    summary = inputs['native_summary'].json()
    exact(summary.get('case_evidence'), observations['observations'], 'native summary differs from original runtime observations')
    require(summary.get('source_commit') == UPSTREAM_SHA
            and summary.get('source_declaration_index') == profile['index']
            and summary.get('ctest_name_from_source') == profile['registration'], 'native summary identity changed')
    begin, end = timestamp(prospective.get('started_utc'), 'native start'), timestamp(native.get('finished_utc'), 'native finish')
    require(begin <= end, 'native process interval is reversed')
    require(duration(native.get('elapsed_seconds'), 'native duration') <= (end - begin).total_seconds() + 0.1,
            'native duration exceeds its recorded interval')
    return {'receipt': native, 'prospective': prospective, 'prospective_file': prospective_file,
            'original': original, 'declaration': declaration, 'specifications': specifications,
            'observations': observations, 'command': command, 'cwd': cwd, 'inputs': pins,
            'started_utc': prospective['started_utc'], 'finished_utc': native['finished_utc']}


def check_producers(evidence: MeshEvidence, profile: dict, browser: dict, native: dict, inputs: dict) -> None:
    base = str(HISTORICAL_ROOT / (EV + profile['browser_dir']))
    expected = []
    for name in ('run-browser-v2.py', 'launcher-v2.js', 'launcher-v2.html'):
        size, hash_value = profile['producer_files'][name]
        expected.append({'path': base + '/' + name, 'bytes': size, 'sha256': hash_value})
    if profile['registration'] == 'operators':
        expected.extend([
            {'path': base + '/prepare-launcher.py', 'bytes': 4275,
             'sha256': '7d872b0588caef0d9b29956d5dbd4065976669c3e20bbf36e9938fbcebf85811'},
            {'path': base + '/launcher-derivation.json', 'bytes': 6132,
             'sha256': '927e1b8611709249dca2ab70c60053e64bd764f35ee8f37a9e3d59b9f0b25505'},
        ])
    expected.extend([
        native['original']['capture_driver'],
        {'path': str(HISTORICAL_ROOT / selector_paths(profile)['native_summary']),
         **{key: inputs['native_summary'].ref[key] for key in ('bytes', 'sha256')}},
        native['receipt']['prospective_command'],
        {'path': str(HISTORICAL_ROOT / PROBE[0]), 'bytes': PROBE[1], 'sha256': PROBE[2]},
        {'path': str(HISTORICAL_ROOT / OVERLAY_TOOL[0]), 'bytes': OVERLAY_TOOL[1], 'sha256': OVERLAY_TOOL[2]},
    ])
    exact(browser.get('capture_inputs_before'), expected, 'browser producer closure differs from reviewed snapshots')
    exact(browser.get('capture_inputs_after'), expected, 'browser producer bytes changed during capture')
    require(browser.get('capture_inputs_unchanged') is True, 'browser producer preservation was not observed')
    for pin in expected:
        evidence.reference(pin)
    exact(browser.get('original_log_parser'), native['original']['capture_driver'], 'browser original parser identity changed')
    exact(browser.get('original_log_parser_reverified_before_import'), native['original']['capture_driver'],
          'browser original parser was not reverified')
    if profile['registration'] == 'operators':
        derivation = evidence.reference(expected[4]).json()
        document(derivation, 'evidence-only-original-mesh-launcher-derivation')
        require(derivation.get('source_launcher') == PROFILES['bmesh-bevel-5.2']['profile']
                and derivation.get('output_launcher') == profile['profile']
                and type(derivation.get('tests_executed_by_derivation')) is int
                and derivation['tests_executed_by_derivation'] == 0
                and derivation.get('full_feature_parity') is False, 'operator launcher derivation changed its scope')
        for field, selected in (('source_files', PROFILES['bmesh-bevel-5.2']), ('output_files', profile)):
            rows = derivation.get(field)
            require(isinstance(rows, list) and len(rows) == 4, 'incomplete original launcher derivation')
            wanted = {}
            for name, (size, hash_value) in selected['producer_files'].items():
                wanted[str(HISTORICAL_ROOT / (EV + selected['browser_dir'] + '/' + name))] = (hash_value, size)
            require(len({row.get('path') for row in rows}) == 4, 'duplicate launcher derivation file')
            for row in rows:
                require(row.get('path') in wanted and pin_identity(row, 'launcher derivation') == wanted[row['path']],
                        'launcher derivation substitutes source or output bytes')
                evidence.reference(row)
        exact(derivation.get('derivation_script'), expected[3], 'launcher derivation producer changed')


def raw_browser_artifacts(evidence: MeshEvidence, profile: dict, browser: dict) -> dict[str, Captured]:
    base = str(HISTORICAL_ROOT / (EV + profile['browser_dir'] + '/' + profile['attempt'])) + '/'
    rows = browser.get('raw_evidence')
    require(isinstance(rows, list) and bool(rows), 'original browser raw evidence is missing')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get('path'), str) and row['path'].startswith(base),
                'raw browser evidence is outside the selected attempt')
        name = row['path'][len(base):]
        require(name and '/' not in name and name not in result, 'duplicate or ambiguous browser raw evidence')
        result[name] = evidence.reference(row)
    required = {'browser-console.jsonl', 'browser-state.json', 'chrome.stderr.log', 'chrome.stdout.log', 'http.log',
                'input-manifest.json', 'launcher-events.jsonl', 'original-stderr.log', 'original-stdout.log',
                'prospective-command.json'}
    require(required <= set(result), 'selected browser attempt has an incomplete raw evidence closure')
    return result


def json_lines(captured: Captured) -> list[dict]:
    rows = [load_json(line) for line in captured.data.decode('utf-8').splitlines()]
    require(all(isinstance(row, dict) for row in rows), 'JSONL observations must be objects')
    return rows


def check_runtime_events(profile: dict, browser: dict, events: list[dict], console: list[dict],
                         state: dict, stdout: str, stderr: str, native: dict,
                         manifest: dict, observations: dict) -> tuple[dict, list[str]]:
    """Check independently observed boundaries and recompute producer checks.

    Honest nonzero or missing exits produce blockers. Contradictory observations,
    altered original arguments, duplicate event identities and invalid types
    are malformed evidence and raise ValueError.
    """
    require(isinstance(state, dict) and type(state.get('schema')) is int and state['schema'] == 1,
            'original runtime state schema is missing')
    exact(events, state.get('events'), 'launcher stream differs from retained browser state')
    exact(state, browser.get('runtime_state'), 'retained browser state differs from execution receipt')
    require(isinstance(events, list), 'launcher events must be a list')
    allowed = {'fetched_original_input', 'launch_original_main', 'original_inputs_queued_before_main',
               'verified_original_inputs_before_main', 'module_resolved', 'stdout', 'stderr',
               'original_inputs_observed_at_original_quit', 'runtime_exit', 'runtime_abort',
               'launcher_error', 'original_quit_file_observation_error'}
    previous_time = 0
    for index, row in enumerate(events):
        require(isinstance(row, dict) and set(row) == {'sequence', 'milliseconds', 'kind', 'detail'},
                'malformed launcher event')
        require(integer(row['sequence'], 'launcher sequence') == index, 'launcher event sequence is incomplete or duplicated')
        elapsed = duration(row['milliseconds'], 'launcher event time')
        require(elapsed >= previous_time, 'launcher event time moved backwards')
        previous_time = elapsed
        require(row['kind'] in allowed, 'unknown event in exact historical launcher')
        if row['kind'] in {'stdout', 'stderr', 'runtime_abort', 'original_quit_file_observation_error'}:
            require(isinstance(row['detail'], str), 'launcher text event is not text')
        else:
            require(isinstance(row['detail'], dict), 'launcher structured event is not an object')
    # The clocks are read separately. Permit at most 100 ms of capture-clock
    # rounding or scheduling discrepancy, not an unbounded event timeline.
    require(not events or events[-1]['milliseconds'] <=
            1000 * (duration(browser.get('execution_elapsed_seconds'), 'browser execution duration') + 0.1),
            'launcher timeline exceeds the recorded execution interval')
    marker_events = []
    for row in console:
        require(isinstance(row.get('text'), str) and isinstance(row.get('kind'), str), 'invalid console observation')
        if row['text'].startswith(profile['marker']):
            require(row['kind'] == 'log', 'original launcher marker has an unexpected console kind')
            marker_events.append(load_json(row['text'][len(profile['marker']):]))
    exact(marker_events, events, 'console marker stream differs from launcher events')
    require(integer(browser.get('observed_console_events'), 'console count') == len(console), 'console event count mismatch')
    for kind, original in (('stdout', stdout), ('stderr', stderr)):
        exact(''.join(row['detail'] + '\n' for row in events if row['kind'] == kind), original,
              'original ' + kind + ' differs from launcher events')
    require(browser.get('event_stream_matches_browser_state') is bool(events), 'contradictory console completeness claim')
    for field in ('automaticMain', 'runtimeInitialized', 'moduleResolved', 'finished'):
        boolean(state.get(field), 'runtime state ' + field)
    require(integer(state.get('manualMainCalls'), 'manual main count') >= 0, 'manual main count is negative')
    for field in ('runtimeExitCodes', 'aborts', 'errors'):
        require(isinstance(state.get(field), list), 'runtime state ' + field + ' must be a list')
    codes = state['runtimeExitCodes']
    for code in codes:
        integer(code, 'Wasm exit')
    groups = {kind: [row for row in events if row['kind'] == kind] for kind in allowed}
    exact([row['detail'] for row in groups['runtime_abort']], state['aborts'], 'runtime abort observations differ')
    exact([row['detail'] for row in groups['launcher_error']], state['errors'], 'launcher error observations differ')
    for row in groups['runtime_exit']:
        integer(row['detail'].get('code'), 'observed Wasm exit')
    exact([row['detail']['code'] for row in groups['runtime_exit']], codes, 'Wasm exit events contradict runtime state')
    command, cwd = native['command'], native['cwd']
    expected_files = [
        {'virtual_path': row['path'], 'url': '/original-input-' + str(index),
         'bytes': row['bytes'], 'sha256': row['sha256']}
        for index, row in enumerate(native['inputs']) if index >= 3
    ]
    exact(manifest, {'schema': 1, 'command': command, 'cwd': cwd, 'environment': BROWSER_ENVIRONMENT,
                     'files': expected_files, 'upstream_commit': UPSTREAM_SHA}, 'original mounted-input manifest changed')
    exact(browser.get('browser_environment'), BROWSER_ENVIRONMENT, 'original browser environment changed')
    if 'preMainEnvironment' in state:
        require(isinstance(state['preMainEnvironment'], dict)
                and not {'BLENDER_TEST_UPDATE', 'BLENDER_VERBOSE'} & state['preMainEnvironment'].keys(),
                'forbidden original update or verbose environment key is present')
        exact(state['preMainEnvironment'], BROWSER_ENVIRONMENT, 'observed pre-main environment changed')
    for field, expected in (
        ('originalCommand', command), ('requestedCwd', cwd), ('actualCwdBeforeMain', cwd),
        ('argumentTailBeforeAutomaticMain', command[1:]), ('actualArgvAfterFactoryResolution', command),
        ('actualArgvAtRuntimeExit', command),
    ):
        if field in state:
            exact(state[field], expected, 'original runtime argv or cwd changed: ' + field)
    mounted = [{'virtual_path': row['virtual_path'], 'bytes': row['bytes'],
                'sha256_of_verified_input': row['sha256'], 'byte_for_byte_equal_to_verified_input': True}
               for row in expected_files]
    exact(browser.get('expected_mounted_file_rows'), mounted, 'expected mounted originals changed')
    fetched = [{'virtual_path': row['virtual_path'], 'bytes': row['bytes'], 'sha256': row['sha256']}
               for row in expected_files]
    exact([row['detail'] for row in groups['fetched_original_input']], fetched[:len(groups['fetched_original_input'])],
          'fetched original input bytes or identities changed')
    require(len(groups['fetched_original_input']) <= 3, 'duplicate fetched original input')
    expected_details = {
        'launch_original_main': {'command': command, 'cwd': cwd, 'cross_origin_isolated': True, 'automatic_main': True},
        'original_inputs_queued_before_main': {'count': 3, 'environment': BROWSER_ENVIRONMENT, 'forbidden_keys_absent': True},
        'verified_original_inputs_before_main': {'files': mounted, 'cwd': cwd, 'argument_tail': command[1:]},
        'module_resolved': {'actual_argv': command},
    }
    for kind, expected in expected_details.items():
        require(len(groups[kind]) <= 1, 'duplicate original launch boundary: ' + kind)
        if groups[kind]:
            exact(groups[kind][0]['detail'], expected, 'original launch boundary changed: ' + kind)
    sequence = [row['kind'] for row in events[:7]]
    startup = (sequence == ['fetched_original_input'] * 3 + list(expected_details)
               and state['automaticMain'] is True and state['manualMainCalls'] == 0
               and state['runtimeInitialized'] is True and state['moduleResolved'] is True
               and state.get('crossOriginIsolated') is True)
    if groups['verified_original_inputs_before_main']:
        exact(state.get('mountedFilesBeforeMain'), mounted, 'pre-main bytes differ from observed boundary')
        require(state.get('forbiddenEnvironmentKeysAbsent') is True, 'pre-main forbidden-key absence is unobserved')
    quits = [row for row in groups['stdout'] if row['detail'] == 'Blender quit']
    readbacks, exits = groups['original_inputs_observed_at_original_quit'], groups['runtime_exit']
    require(len(quits) <= 1 and len(readbacks) <= 1, 'duplicate original quit or input readback')
    if quits:
        require(integer(state.get('originalQuitObservations'), 'original quit count') == 1
                and integer(state.get('originalQuitStdoutSequence'), 'original quit sequence') == quits[0]['sequence'],
                'original quit state contradicts event stream')
    else:
        require('originalQuitObservations' not in state and 'originalQuitStdoutSequence' not in state,
                'original quit state exists without a quit event')
    if readbacks:
        require(bool(quits), 'input readback has no original quit boundary')
        exact(readbacks[0]['detail'], {'original_quit_stdout_sequence': quits[0]['sequence'], 'files': mounted,
              'boundary': 'original Blender quit stdout before Emscripten runtime teardown'},
              'original quit input readback changed')
        exact(state.get('mountedFilesAtOriginalQuit'), mounted, 'quit bytes differ from observed readback')
    case_events = [row for row in groups['stdout'] if row['detail'].startswith(
        ('START ', 'PASSED ', 'FAILED ', 'Mesh Comparison : ', 'Mesh Validation : '))]
    complete_boundary = (len(quits) == len(readbacks) == len(exits) == 1 and bool(case_events)
                         and max(row['sequence'] for row in case_events) < quits[0]['sequence']
                         and quits[0]['sequence'] + 1 == readbacks[0]['sequence'] < exits[0]['sequence'])
    if exits:
        for event in exits:
            expected = {'code': event['detail']['code'], 'actual_argv': command,
                        'filesystem_capture_boundary': 'original Blender quit stdout before runtime teardown'}
            if quits:
                expected['original_quit_stdout_sequence'] = quits[0]['sequence']
            exact(event['detail'], expected, 'runtime exit boundary or original argv changed')
    require(browser.get('original_quit_byte_observation_boundary_verified') is complete_boundary,
            'original byte-boundary claim contradicts event stream')
    for field in ('errors', 'page_errors', 'failed_requests'):
        require(isinstance(browser.get(field), list), field + ' must be a list')
    for field in ('timed_out', 'browser_crashed', 'capture_inputs_unchanged', 'original_host_inputs_unchanged'):
        boolean(browser.get(field), field)
    if 'chrome_forced_termination' in browser:
        boolean(browser['chrome_forced_termination'], 'Chrome forced termination')
    chrome_exit = integer(browser.get('actual_chrome_process_returncode'), 'Chrome process exit', nullable=True)
    checks = {
        'runtime_initialized': state['runtimeInitialized'],
        'original_command_observed_at_runtime_exit': state.get('actualArgvAtRuntimeExit') == command,
        'original_cwd_observed_before_main': state.get('actualCwdBeforeMain') == cwd,
        'oracle_update_and_verbose_keys_absent': state.get('forbiddenEnvironmentKeysAbsent') is True,
        'environment_matches_declared': state.get('preMainEnvironment') == BROWSER_ENVIRONMENT,
        'pre_main_original_bytes_verified': state.get('mountedFilesBeforeMain') == mounted,
        'original_bytes_unchanged_at_original_quit': state.get('mountedFilesAtOriginalQuit') == mounted,
        'byte_observation_after_all_original_case_results_before_runtime_exit': complete_boundary,
        'automatic_main_only': state['automaticMain'] is True and state['manualMainCalls'] == 0,
        'exactly_one_successful_runtime_exit': codes == [0],
        'no_runtime_abort_or_launcher_error': not state['aborts'] and not state['errors'],
        'no_host_or_page_errors': not browser['errors'] and not browser['page_errors'] and not browser['browser_crashed'],
        'no_failed_requests': not browser['failed_requests'],
        'no_timeout': browser['timed_out'] is False,
        'chrome_process_exited_successfully': chrome_exit == 0 and not browser.get('chrome_forced_termination'),
        'console_stream_complete': bool(events),
        'capture_inputs_unchanged': browser['capture_inputs_unchanged'],
        'original_host_inputs_unchanged': browser['original_host_inputs_unchanged'],
        'all_native_runtime_names_observed_once': not observations['missing_declared_names']
            and not observations['unexpected_names'] and not observations['duplicate_names'],
        'all_original_mesh_oracles_passed': observations['observed_passes'] == profile['count']
            and not observations['observed_failures'] and not observations['observed_ambiguous_or_incomplete'],
    }
    exact(browser.get('qualification_checks'), checks, 'qualification checks contradict independently parsed evidence')
    qualified = all(checks.values())
    require(browser.get('qualified_original_invocation') is qualified
            and browser.get('status') == ('passed' if qualified else 'failed_or_blocked'),
            'browser invocation qualification contradicts original observations')
    require(integer(browser.get('qualified_original_browser_passes'), 'qualified browser count')
            == (observations['observed_passes'] if qualified else 0), 'qualified pass count contradicts invocation')
    blockers = [name for name, passed in checks.items() if not passed]
    if not startup:
        blockers.append('original_automatic_main_startup_not_observed_once')
    if not state['finished']:
        blockers.append('original_runtime_not_finished')
    if len(exits) != 1 or exits[-1]['sequence'] != len(events) - 1:
        blockers.append('single_final_runtime_exit_not_observed')
    if groups['original_quit_file_observation_error']:
        blockers.append('original_quit_file_readback_error')
    return checks, sorted(set(blockers))


def check_host(evidence: MeshEvidence, profile: dict, inputs: dict, browser: dict,
               observations: dict, checks: dict) -> tuple[dict, list[str]]:
    host = document(inputs['host_capture'].json(), profile['host_kind'])
    base = str(HISTORICAL_ROOT / (EV + profile['browser_dir']))
    attempt = base + '/' + profile['attempt']
    command = [str(HISTORICAL_RUNTIME / 'browser-python/bin/python'), base + '/run-browser-v2.py',
               '--output', attempt, '--timeout-seconds', '180']
    exact(host.get('command'), command, 'capture host command differs from selected producer and attempt')
    require(host.get('cwd') == str(HISTORICAL_ROOT) and type(host.get('deadline_seconds')) is int
            and host['deadline_seconds'] == 300, 'capture host cwd or deadline changed')
    boolean(host.get('timed_out'), 'capture timeout')
    code = integer(host.get('actual_process_returncode'), 'capture process exit', nullable=True)
    for field, name in (('runner_before', 'run-browser-v2.py'), ('runner_after', 'run-browser-v2.py'),
                        ('capture_script', 'capture-process-v2.py')):
        pin = host.get(field)
        size, hash_value = profile['producer_files'][name]
        exact(pin, {'path': base + '/' + name, 'bytes': size, 'sha256': hash_value}, 'capture host producer changed: ' + field)
        evidence.reference(pin)
    require(host.get('runner_unchanged') is True, 'capture host did not preserve its runner')
    child = evidence.reference(host.get('child_receipt'))
    exact(child.ref, inputs['browser_execution'].ref, 'capture host binds another child receipt')
    prospective = evidence.capture(EV + profile['browser_dir'] + '/' + profile['attempt'] + '-host/prospective-command.json').json()
    initial_fields = ('schema', 'kind', 'command', 'cwd', 'capture_script', 'runner_before',
                      'started_utc', 'deadline_seconds', 'timed_out')
    expected_prospective = {key: host[key] for key in initial_fields}
    expected_prospective['timed_out'] = False
    exact(prospective, expected_prospective, 'host prospective command differs from captured process')
    host_stdout = evidence.reference(host.get('stdout'))
    evidence.reference(host.get('stderr'))
    stdout = load_json(host_stdout.data)
    exact(stdout, {
        'status': browser['status'], 'receipt': host['child_receipt'],
        'runtime_exit_codes': browser['runtime_state']['runtimeExitCodes'],
        'observed_starts': observations['observed_starts'], 'observed_passes': observations['observed_passes'],
        'observed_failures': observations['observed_failures'],
        'qualified_original_browser_passes': browser['qualified_original_browser_passes'],
        'failed_checks': [name for name, value in checks.items() if not value],
    }, 'capture host stdout contradicts the selected child and its original observations')
    start = timestamp(host.get('started_utc'), 'capture host start')
    elapsed = duration(host.get('elapsed_seconds'), 'capture host duration')
    child_start = timestamp(browser.get('started_utc'), 'browser capture start')
    child_end = timestamp(browser.get('completed_utc'), 'browser capture finish')
    require(start <= child_start <= child_end <= start + timedelta(seconds=elapsed),
            'child browser capture is outside the recorded host interval')
    # No completed_utc exists in these host receipts. This upper bound is
    # inferred from the recorded wall start plus measured monotonic duration.
    bounds = {'started_utc': host['started_utc'], 'elapsed_seconds': elapsed,
              'inferred_upper_bound_utc': (start + timedelta(seconds=elapsed)).isoformat(),
              'finish_is_inferred_not_an_observed_timestamp': True}
    require(duration(browser.get('elapsed_seconds'), 'browser capture duration')
            <= (child_end - child_start).total_seconds() + 0.1, 'browser duration exceeds recorded interval')
    duration(browser.get('execution_elapsed_seconds'), 'browser execution duration')
    blockers = []
    if host['timed_out']:
        blockers.append('capture_host_timed_out')
    if code != 0:
        blockers.append('capture_host_exit_not_zero')
    return {'receipt': host, 'bounds': bounds}, blockers


def check_browser(evidence: MeshEvidence, profile: dict, inputs: dict, native: dict, context: dict) -> dict:
    browser = document(inputs['browser_execution'].json(), profile['browser_kind'])
    require(browser.get('upstream_commit') == UPSTREAM_SHA
            and browser.get('launcher_profile_id') == profile['profile']
            and browser.get('original_invocation_kind') == 'source-derived original Blender command',
            'browser original invocation or launcher profile changed')
    for field in ('configured_ctest_execution', 'original_ui_shell_used', 'source_correspondence_verified',
                  'full_feature_parity', 'test_files_modified', 'oracle_modified'):
        require(browser.get(field) is False, 'browser claim or original-input boundary changed: ' + field)
    require(type(browser.get('timeout_seconds')) is int and browser['timeout_seconds'] == 180,
            'browser timeout differs from selected original capture')
    for field, captured in (('native_execution', inputs['native_execution']), ('native_summary', inputs['native_summary']),
                            ('native_prospective_command', native['prospective_file'])):
        exact(evidence.reference(browser.get(field)).ref, captured.ref, 'browser references another ' + field)
    exact(browser.get('command'), native['command'], 'browser exact original --run-all-tests command changed')
    require(browser.get('cwd') == native['cwd'], 'browser original cwd changed')
    exact(browser.get('original_inputs_before'), native['inputs'], 'browser original source or fixture closure changed')
    exact(browser.get('original_inputs_after'), native['inputs'], 'browser original host inputs changed')
    require(browser.get('original_host_inputs_unchanged') is True, 'original host input preservation is missing')
    for pin in browser['original_inputs_after']:
        evidence.reference(pin)
    check_producers(evidence, profile, browser, native, inputs)
    exact(browser.get('artifact'), context['browser']['engine_archive'], 'browser engine differs from independent context')
    require(engine_files(browser.get('actual_engine_files')) == context['engine_files'],
            'actual browser engine members differ from independently measured package')
    engine_paths = [PurePosixPath(row['path']) for row in browser['actual_engine_files']]
    require(len({path.parent for path in engine_paths}) == 1
            and all(path.is_absolute() and path.as_posix() == row['path'] and '..' not in path.parts
                    for path, row in zip(engine_paths, browser['actual_engine_files'])),
            'browser engine extraction paths are ambiguous or noncanonical')
    exact(browser.get('browser_executable'), {key: context['browser']['browser'][key] for key in ('path', 'bytes', 'sha256')},
          'browser executable differs from independently measured context')
    require(context['overlay'] is not None and context['producer'] is None,
            'selected mesh captures require the original Essentials package context')
    exact(browser.get('package_verification'), context['overlay']['verified'], 'browser package verification differs from context')
    exact(evidence.reference(browser.get('base_source_build_receipt')).ref, context['source'].ref,
          'browser source build receipt differs from measured context')
    version = context['browser']['browser'].get('version', '')
    require(isinstance(browser.get('browser_version'), str) and version == 'Google Chrome for Testing ' + browser['browser_version'],
            'actual browser version differs from independently measured executable')
    chrome = browser.get('chrome_command')
    require(isinstance(chrome, list) and len(chrome) == 12, 'Chrome command shape changed')
    exact(chrome[:9], [browser['browser_executable']['path'], '--headless=new', *context['browser']['requested_flags'],
                       '--remote-debugging-address=127.0.0.1'], 'Chrome flags differ from exact original software profile')
    require(chrome[9] == '--remote-debugging-port=0' and isinstance(chrome[10], str)
            and re.fullmatch(r'--user-data-dir=' + re.escape(str(HISTORICAL_RUNTIME))
                             + r'/(?:bevel|operators)-browser-[a-z0-9_]+/chrome-profile', chrome[10])
            and chrome[11] == 'about:blank', 'Chrome debug or profile selection changed')
    temporary_root = PurePosixPath(chrome[10].split('=', 1)[1]).parent
    require(engine_paths[0].parent == temporary_root / 'engine/blender-source-development/bin',
            'measured engine and Chrome do not belong to the same original capture directory')
    require(isinstance(browser.get('origin'), str) and re.fullmatch(r'http://127\.0\.0\.1:[0-9]+', browser['origin']),
            'browser launcher origin is not the original local capture')
    raw = raw_browser_artifacts(evidence, profile, browser)
    exact(evidence.reference(browser.get('input_manifest')).ref, raw['input-manifest.json'].ref,
          'browser selected another input manifest')
    prospective = raw['prospective-command.json'].json()
    fields = {
        'schema', 'kind', 'status', 'started_utc', 'upstream_commit', 'configured_ctest_execution',
        'original_invocation_kind', 'scope', 'launcher_profile_id', 'original_ui_shell_used',
        'source_correspondence_verified', 'full_feature_parity', 'timeout_seconds', 'errors',
        'timed_out', 'page_errors', 'failed_requests', 'browser_crashed', 'test_files_modified',
        'oracle_modified', 'capture_inputs_before', 'native_summary', 'native_execution',
        'native_prospective_command', 'original_log_parser', 'original_inputs_before', 'artifact',
        'base_source_build_receipt', 'actual_engine_files', 'input_manifest', 'command', 'cwd',
        'argv0_note', 'browser_environment', 'browser_executable', 'chrome_command',
    }
    require(set(prospective) == fields and fields <= set(browser), 'browser prospective receipt fields are incomplete or unbound')
    initial = {'status': 'blocked', 'errors': [], 'timed_out': False, 'page_errors': [],
               'failed_requests': [], 'browser_crashed': False}
    for key, value in prospective.items():
        exact(value, initial.get(key, browser[key]), 'browser prospective observation changed: ' + key)
    stdout, stderr = raw['original-stdout.log'].data.decode('utf-8'), raw['original-stderr.log'].data.decode('utf-8')
    observations = original_observations(stdout, native['specifications'])
    exact(browser.get('original_stdout_observations'), observations, 'browser observations contradict original stdout')
    require(not observations['duplicate_names'] and not observations['unexpected_names'],
            'duplicate or unexpected original browser case identity')
    events, console = json_lines(raw['launcher-events.jsonl']), json_lines(raw['browser-console.jsonl'])
    state = raw['browser-state.json'].json()
    checks, blockers = check_runtime_events(profile, browser, events, console, state, stdout, stderr, native,
                                            raw['input-manifest.json'].json(), observations)
    host, host_blockers = check_host(evidence, profile, inputs, browser, observations, checks)
    require(timestamp(native['finished_utc'], 'native completion') <= timestamp(browser['started_utc'], 'browser start'),
            'browser capture predates its selected native inventory')
    native_by_name = {row['name']: row for row in native['observations']['observations']}
    expected_reconciliation = [{
        'name': row['name'], 'native_status': native_by_name[row['name']]['status'],
        'browser_observed_status': row['status'], 'source_declaration': row.get('original_source_declaration'),
        'qualified_browser_status': row['status'] if browser['qualified_original_invocation'] else 'invocation_not_qualified',
    } for row in observations['observations']]
    exact(browser.get('native_browser_case_reconciliation'), expected_reconciliation,
          'producer case reconciliation contradicts original stdout')
    summary = inputs['browser_summary'].json()
    require(summary.get('upstream_commit') == UPSTREAM_SHA and summary.get('ctest_name_from_source') == profile['registration']
            and summary.get('source_declaration_index') == profile['index']
            and summary.get('launcher_profile_id') == profile['profile']
            and summary.get('configured_ctest_execution') is False and summary.get('full_feature_parity') is False,
            'historical browser summary identity or claim scope changed')
    for field, selected in (('browser_execution', inputs['browser_execution']), ('capture_host_execution', inputs['host_capture'])):
        exact(evidence.reference(summary.get(field)).ref, selected.ref, 'historical browser summary selects another capture')
    summary_rows = summary.get('cases')
    require(isinstance(summary_rows, list) and len(summary_rows) == profile['count'], 'historical summary lost native obligations')
    observed_by_name = {row['name']: row for row in observations['observations']}
    expected_ids = [original_id(profile, row['original_source_declaration']) for row in native['observations']['observations']]
    exact([row.get('case_id') for row in summary_rows], expected_ids, 'historical original case IDs changed')
    for summary_row, native_row in zip(summary_rows, native['observations']['observations']):
        exact(summary_row.get('source_declaration'), native_row['original_source_declaration'], 'summary original specification changed')
        require(summary_row.get('name') == native_row['name'] and summary_row.get('native_status') == native_row['status'],
                'summary native case identity or outcome changed')
        observed = observed_by_name.get(native_row['name'])
        if observed is not None:
            field = 'browser_status' if profile['registration'] == 'bmesh_bevel' else 'browser_observed_status'
            exact(summary_row.get(field), observed['status'], 'summary browser case outcome contradicts original stdout')
            exact(summary_row.get('original_mesh_comparison'), observed['mesh_comparison'], 'summary original comparison changed')
            exact(summary_row.get('original_mesh_validation'), observed['mesh_validation'], 'summary original validation changed')
            require(type(summary_row.get('browser_stdout_line')) is int
                    and summary_row['browser_stdout_line'] == observed['start_log_line'], 'summary case log location changed')
    return {'receipt': browser, 'observations': observations, 'checks': checks,
            'blockers': sorted(set(blockers + host_blockers)), 'host': host, 'events_verified': len(events)}


def case_outcome(profile: dict, row: dict | None, specification: dict) -> dict:
    status = row['status'] if row else 'missing'
    outcome = {'passed': 'passed', 'failed': 'failed', 'ambiguous_or_incomplete': 'blocked', 'missing': 'not_run'}[status]
    diagnostics = {key: row[key] for key in ('terminal_log_lines', 'mesh_comparison', 'mesh_validation')} if row else None
    result = {'id': original_id(profile, specification), 'outcome': outcome,
              'started': row is not None, 'completed': status in {'passed', 'failed'},
              'comparison': {'status': 'passed' if status == 'passed' else 'failed' if status == 'failed' else 'not_run',
                             'policy_sha256': canonical_sha256(POLICY)},
              'subtests': [], 'original_mesh_diagnostics': diagnostics}
    if outcome != 'passed':
        result['detail_sha256'] = canonical_sha256(diagnostics)
    return result


def normalization_sources(evidence: MeshEvidence) -> tuple[list[dict], str]:
    names = ['reconcile_original_mesh.py', 'test_parity_ledger.py', 'reconcile_unittest_matrix.py',
             'unittest_cohort.py', 'upstream_invocations.py', 'upstream_invocations_5_2.json',
             'upstream_resources.py', 'probe_blender_fixtures.py', 'browser_package_overlay.py']
    program = []
    for name in names:
        captured = evidence.capture('tools/' + name)
        require(captured.data == Path(__file__).with_name(name).read_bytes(),
                'normalization source differs from the executing tool: ' + name)
        program.append(evidence.write('normalizer/' + name, captured.data))
    plan_path = 'compatibility/package-overlays/essentials-brushes-5.2.json'
    plan = evidence.capture(plan_path)
    require(plan.data == (ROOT / plan_path).read_bytes(), 'normalization package plan differs from the executing context reader')
    program.append(evidence.write(plan_path, plan.data))
    return program, canonical_sha256(program)


def reconcile(repo_root: Path, selector_path: Path, output: Path) -> dict:
    evidence = MeshEvidence(repo_root, output)
    selector, profile, selected = read_selector(evidence, selector_path)
    program, adapter = normalization_sources(evidence)
    context = read_contexts(evidence, selected['native_context'].path, selected['browser_context'].path, adapter)
    check_context_profile(context)
    native = check_native(evidence, profile, selected, context)
    browser = check_browser(evidence, profile, selected, native, context)
    criteria = {
        'id': profile['registration'],
        'invocation_sha256': canonical_sha256({'original_declaration': native['declaration'],
              'command': native['command'], 'cwd': native['cwd'], 'environment_overrides': THREAD_ENVIRONMENT}),
        'fixture_manifest_sha256': canonical_sha256(native['inputs']),
        'comparison_policy_sha256': canonical_sha256(POLICY),
    }
    native_context, browser_context = context['contexts'][CONTEXT_NATIVE], context['contexts'][CONTEXT_BROWSER]
    contract = {
        'schema': 1, 'target': TARGET, 'scope': 'retained-original-mesh:' + profile['profile'],
        'configurations': [{'id': CONFIGURATION, 'registrations': [criteria]}],
        'profiles': [
            {'id': NATIVE, 'role': 'reference', 'runtime_kind': 'native', 'contexts': {CONFIGURATION: native_context}},
            {'id': profile['profile'], 'role': 'candidate', 'runtime_kind': 'browser',
             'contexts': {CONFIGURATION: browser_context}},
        ],
        'coverage': {'source_registration_reconciliation_complete': False, 'configuration_matrix_complete': False,
                     'fixture_closure_complete': True,
                     'blockers': ['Only one selected source-derived original mesh registration is assessed.',
                                  'The original TEST_SRC_DIR_EXISTS condition is preserved; no configured CTest inventory is claimed.',
                                  'This independent profile does not extend the 829-obligation unittest scope.']},
        'original_declaration': native['declaration'], 'comparison_policy': POLICY,
        'normalization_sources': program, 'selected_profile': selector.ref,
        'historical_engine_context': selected['browser_context'].ref,
    }
    contract_hash = canonical_sha256(contract)
    cases = native['observations']['observations']
    ids = [original_id(profile, row['original_source_declaration']) for row in cases]
    native_process = {'started': True, 'completed': True, 'exit_code': 0, 'timed_out': False, 'crashed': False}
    base = {'schema': 1, 'target': TARGET, 'contract_sha256': contract_hash,
            'configuration': CONFIGURATION, 'registration_id': profile['registration'],
            **criteria, 'selection': {'filters': [], 'shard': None}}
    raw = unique_refs(list(evidence.origins.values()))
    discovery = {**base, 'kind': 'blender-test-discovery', 'profile': NATIVE, 'runtime_kind': 'native',
                 'context': native_context, 'process': native_process,
                 'case_ids': ids, 'disabled_case_ids': [], 'raw_evidence': raw,
                 'inventory_basis': 'Selected successfully completed original native runtime log; AST only verifies its identities.'}
    discovery_ref = evidence.json('receipts/' + profile['registration'] + '/discovery.json', discovery)
    inventory = {'schema': 1, 'target': TARGET, 'contract_sha256': contract_hash,
                 'registrations': [{'configuration': CONFIGURATION, 'id': profile['registration'], 'status': 'expanded',
                                     'case_ids': ids, 'disabled_case_ids': [], 'discovery': discovery_ref}]}
    inventory_hash = canonical_sha256(inventory)
    runs = []
    observed = {row['name']: row for row in browser['observations']['observations']}
    native_cases = [case_outcome(profile, row, row['original_source_declaration']) for row in cases]
    browser_cases = [case_outcome(profile, observed.get(row['name']), row['original_source_declaration']) for row in cases]
    state = browser['receipt']['runtime_state']
    exit_codes = state['runtimeExitCodes']
    chrome_exit = browser['receipt']['actual_chrome_process_returncode']
    host_exit = browser['host']['receipt']['actual_process_returncode']
    browser_process = {'started': any(event['kind'] == 'launch_original_main' for event in state['events']),
                       'completed': len(exit_codes) == 1 and state['finished'] is True,
                       'exit_code': exit_codes[0] if len(exit_codes) == 1 else None,
                       'timed_out': browser['receipt']['timed_out'] or browser['host']['receipt']['timed_out'],
                       'crashed': browser['receipt']['browser_crashed'] or bool(state['aborts'])
                           or chrome_exit is not None and chrome_exit < 0 or host_exit is not None and host_exit < 0}
    for pid, runtime_kind, ctx, process, rows, blockers in (
        (NATIVE, 'native', native_context, native_process, native_cases, []),
        (profile['profile'], 'browser', browser_context, browser_process, browser_cases, browser['blockers']),
    ):
        run_id = selector.json()['id'] + ':' + pid
        receipt = {**base, 'kind': 'blender-test-execution', 'inventory_sha256': inventory_hash,
                   'profile': pid, 'runtime_kind': runtime_kind, 'context': ctx, 'process': process,
                   'run_id': run_id, 'cases': rows, 'validation_blockers': blockers, 'raw_evidence': raw}
        ref = evidence.json('receipts/' + profile['registration'] + '/' + pid + '.json', receipt)
        runs.append({'configuration': CONFIGURATION, 'registration_id': profile['registration'],
                     'profile': pid, 'run_id': run_id, 'receipt': ref})
    executions = {'schema': 1, 'target': TARGET, 'contract_sha256': contract_hash,
                  'inventory_sha256': inventory_hash, 'runs': runs}
    report = assess(contract, inventory, executions, evidence.output)
    diagnostic_rows = []
    for nr, br, native_row in zip(native_cases, browser_cases, cases):
        row = observed.get(native_row['name'])
        matches = (nr['completed'] and br['completed'] and nr['outcome'] == br['outcome']
                   and nr['original_mesh_diagnostics'] == br['original_mesh_diagnostics'])
        diagnostic_rows.append({'case_id': nr['id'], 'name': native_row['name'],
                                'source_declaration': native_row['original_source_declaration'],
                                'native_outcome': nr['outcome'], 'browser_outcome': br['outcome'],
                                'raw_terminal_outcome_agreement': matches,
                                'native_stdout_line': native_row['start_log_line'],
                                'browser_stdout_line': row['start_log_line'] if row else None,
                                'browser_mesh_diagnostics': br['original_mesh_diagnostics']})
    report.update({
        'raw_terminal_outcome_agreement_count': sum(row['raw_terminal_outcome_agreement'] for row in diagnostic_rows),
        'raw_terminal_outcome_agreement_is_whole_invocation_qualification': False,
        'original_observations_diagnostics': {
            'native_case_count': len(cases), 'browser_observed_case_count': browser['observations']['observed_starts'],
            'browser_pass_observations': browser['observations']['observed_passes'],
            'browser_failure_observations': browser['observations']['observed_failures'],
            'browser_ambiguous_or_incomplete_observations': browser['observations']['observed_ambiguous_or_incomplete'],
            'wasm_exit_codes': exit_codes, 'chrome_exit_code': chrome_exit, 'capture_host_exit_code': host_exit,
            'whole_invocation_blockers': browser['blockers'], 'cases': diagnostic_rows,
        },
        'normalization_only': True, 'new_original_executions': 0, 'extends_829_unittest_scope': False,
    })
    conversion = {
        'schema': 1, 'kind': 'retained-original-mesh-conversion', 'target': TARGET,
        'selected_profile': selector.ref, 'profile_id': profile['profile'], 'original_declaration': native['declaration'],
        'original_command': native['command'], 'original_cwd': native['cwd'],
        'original_case_ids_from_native_runtime': ids, 'case_count': len(ids),
        'program': program, 'adapter_sha256': adapter, 'historical_host_interval': browser['host']['bounds'],
        'launcher_events_verified': browser['events_verified'], 'qualification_checks': browser['checks'],
        'saved_copy_bindings': list(evidence.saved_bindings.values()),
        'inputs': [{'path': path, 'raw_evidence': ref} for path, ref in sorted(evidence.origins.items())],
        'new_original_executions': 0, 'extends_829_unittest_scope': False,
        'all_upstream_test_parity': False, 'full_feature_parity': False,
        'limitations': ['Retained producer observations and context measurements are consumed, not independently re-executed.',
                        'External engine archives, native binary and Chrome binary are historical measured identities; their payloads are not reread.',
                        'Raw terminal outcome matches do not qualify a failed or incomplete whole invocation.',
                        'This captured Essentials launcher profile cannot be combined with another build or launcher profile.'],
    }
    evidence.verify_unchanged()
    for name, value in (('contract', contract), ('inventory', inventory), ('executions', executions),
                        ('conversion', conversion), ('report', report)):
        evidence.json(name + '.json', value)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--profile', type=Path, required=True, help='One explicit retained original mesh profile selector')
    parser.add_argument('--output', type=Path, required=True, help='A new immutable output directory')
    parser.add_argument('--report-only', action='store_true', help='Return 0 for valid blocked evidence; malformed input still returns 2')
    args = parser.parse_args(argv)
    output_existed = args.output.exists()
    try:
        report = reconcile(args.repo_root, args.profile, args.output)
        status = 0 if args.report_only or report['declared_scope_test_parity'] else 1
    except (OSError, ValueError, TypeError, KeyError, SyntaxError) as error:
        report = {'schema': 1, 'gate': 'invalid', 'declared_scope_test_parity': False,
                  'all_upstream_test_parity': False, 'full_feature_parity': False, 'normalization_only': True,
                  'new_original_executions': 0, 'error': str(error)}
        status = 2
        if not output_existed and args.output.is_dir() and not args.output.is_symlink():
            error_path = args.output / 'invalid.json'
            if not error_path.exists():
                with error_path.open('xb') as stream:
                    stream.write(encoded(report))
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {'pairs', 'registrations', 'coverage_review', 'original_observations_diagnostics'}},
                     sort_keys=True, allow_nan=False))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
