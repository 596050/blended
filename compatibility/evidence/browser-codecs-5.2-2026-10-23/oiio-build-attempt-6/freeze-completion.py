#!/usr/bin/env python3
"""Freeze the completed real OIIO build and its installed configuration."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EXPECTED_MANIFEST = 'b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708'


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def reference(path: Path) -> dict:
    row = identity(path)
    row['path'] = path.relative_to(REPO).as_posix()
    return row


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def main() -> int:
    result_path = HERE / 'completion-summary.json'
    require(not result_path.exists(), 'Completion summary is immutable once written')
    execution_path = HERE / 'execution.json'
    execution = json.loads(execution_path.read_text())
    manifest_path = REPO / 'patches/browser-codecs/manifest.json'
    require(reference(manifest_path)['sha256'] == EXPECTED_MANIFEST, 'Selected manifest changed')
    require(execution['manifest']['sha256'] == EXPECTED_MANIFEST, 'Execution used a different manifest')
    require(execution['status'] == 'openimageio_dependency_build_passed', 'Full dependency build did not pass')
    require(len(execution['commands']) == 22, 'Expected one application and 21 dependency recipes')
    for command in execution['commands']:
        require(command['returncode'] == 0 and command['timed_out'] is False, 'Incomplete or failed command')
        require(identity(Path(command['log']['path'])) == command['log'], 'A command log changed')
    for entry in execution['libraries']:
        require(identity(Path(entry['path'])) == entry, 'An installed library changed after execution')
    for entry in execution['recipes']:
        require(identity(Path(entry['path'])) == entry, 'A selected recipe changed during execution')
    oiio = [row for row in execution['commands'] if row['name'] == 'openimageio']
    require(len(oiio) == 1, 'Expected one original OIIO recipe execution')
    log = (HERE / 'openimageio.log').read_text()
    marker = 'openimageio: verify static codecs, AV1 backends, link and physical-memory runtime OK'
    require(marker in log, 'Real OIIO runtime success marker missing')
    memory = re.findall(r'^physical_memory=(\d+) heap_size=(\d+) heap_max=(\d+)$', log, re.M)
    require(len(memory) == 1, 'Expected one runtime physical-memory observation')
    physical, heap, maximum = map(int, memory[0])
    require(physical == maximum and physical > heap, 'Physical-memory runtime observation failed')
    application = json.loads((HERE / 'patch-application.json').read_text())
    port = Path(application['port_root'])
    prefix = port / 'lib/wasm'
    cache = prefix / 'share/blended/openimageio-codecs-CMakeCache.txt'
    values = {}
    for line in cache.read_text().splitlines():
        match = re.fullmatch(r'([^:#][^:]*):[^=]+=(.*)', line)
        if match:
            values[match[1]] = match[2]
    required = {'USE_WEBP': 'ON', 'USE_OPENJPEG': 'ON', 'USE_LIBHEIF': 'ON',
                'EMBEDPLUGINS': 'ON', 'BUILD_SHARED_LIBS': 'OFF'}
    require(all(values.get(key) == value for key, value in required.items()), 'Required OIIO cache flag absent')
    sources = [cache, *sorted((prefix / 'lib/cmake/OpenImageIO').glob('*.cmake'))]
    preserved = []
    for source in sources:
        destination = HERE / ('openimageio-CMakeCache.txt' if source == cache else source.name)
        require(not destination.exists(), 'Refusing to replace preserved configuration')
        shutil.copyfile(source, destination)
        require(identity(source)['sha256'] == reference(destination)['sha256'], 'Configuration copy differs')
        preserved.append({'original': identity(source), 'preserved': reference(destination)})
    report = {
        'schema': 1, 'kind': 'completed-pinned-openimageio-wasm-integration',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'summary_is_new_execution_evidence': False,
        'summary_generator': reference(Path(__file__).resolve()),
        'actual_execution': reference(execution_path),
        'selected_manifest': reference(manifest_path),
        'patch_application': reference(HERE / 'patch-application.json'),
        'raw_oiio_log': reference(HERE / 'openimageio.log'),
        'successful_dependency_recipes': [row['name'] for row in execution['commands'] if row['name'] != 'apply-codecs'],
        'all_21_dependency_recipes_completed_successfully': True,
        'all_child_recipe_returncodes': [row['returncode'] for row in execution['commands']],
        'sum_of_recorded_command_durations_seconds': round(sum(row['duration_seconds'] for row in execution['commands']), 6),
        'oiio_recipe_duration_seconds': oiio[0]['duration_seconds'],
        'oiio_recipe_returncode': oiio[0]['returncode'],
        'runtime_smoke_scope': 'Real linked Node/Wasm OIIO dependency executable, with the selected Emscripten compiler. No Blender application.',
        'runtime_completion_evidence': 'The preserved set-e shell recipe runs node, observes its exit status, emits the success marker, validates the cache and completes with exit 0. The outer runner does not claim a separately instrumented Node process receipt.',
        'runtime_smoke_success_marker_observed': True,
        'readers_and_writers_required_by_executed_smoke': ['webp', 'jpeg2000', 'heif', 'dpx'],
        'av1_encoder_and_decoder_required_by_executed_smoke': True,
        'observed_memory_bytes': {'physical_memory': physical, 'heap_size': heap, 'heap_max': maximum},
        'required_generated_configuration': required,
        'preserved_installed_configuration': preserved,
        'previous_completed_summary_unchanged': reference(HERE.parent / 'completed-summary.json'),
        'new_blender_cases_executed': 0,
        'new_browser_application_passes': 0,
        'full_feature_parity': False,
        'remaining_application_gate': 'Run the unchanged original ImBuf invocation on the rebuilt browser: all 80 parent IDs, all 57 native subtest IDs, original zero WebP/JPEG2000 tolerance and AVIF tolerance 1.',
    }
    result_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(reference(result_path)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
