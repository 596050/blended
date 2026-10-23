#!/usr/bin/env python3
"""Summarize immutable completed codec evidence without inventing executions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[2]
EXPECTED_MANIFEST = 'b2881dbf9366a9e1ad6bbf9ffe4d61b0b53d47745472bd2b14f02da5730f2708'


def reference(path: Path) -> dict:
    data = path.read_bytes()
    return {'path': path.relative_to(REPO).as_posix(), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def main() -> int:
    output = EVIDENCE / 'completed-summary.json'
    if output.exists():
        raise SystemExit('Refusing to replace an existing completed evidence summary')
    manifest_path = REPO / 'patches/browser-codecs/manifest.json'
    selected = reference(manifest_path)
    assert selected['sha256'] == EXPECTED_MANIFEST
    manifest = json.loads(manifest_path.read_text())
    baseline = json.loads((EVIDENCE / 'baseline-gap.json').read_text())
    validation = json.loads((EVIDENCE / 'validation-attempt-1/execution.json').read_text())
    assert validation['status'] == 'dependency_validation_passed'
    assert all(row['returncode'] == 0 and not row['timed_out'] for row in validation['commands'])
    application = json.loads((EVIDENCE / 'oiio-build-attempt-5/patch-application.json').read_text())
    application_process = json.loads((EVIDENCE / 'oiio-build-attempt-5/execution.json').read_text())
    assert application['manifest_sha256'] == EXPECTED_MANIFEST
    assert application['status'] == 'applied_and_verified'
    assert application_process['commands'][0]['name'] == 'apply-codecs'
    assert application_process['commands'][0]['returncode'] == 0
    completed = []
    for name in ('build-attempt-1', 'build-attempt-2', 'build-attempt-3', 'build-attempt-4',
                 'validation-attempt-1', 'oiio-build-attempt-1', 'oiio-build-attempt-2',
                 'oiio-build-attempt-4', 'oiio-build-attempt-5'):
        path = EVIDENCE / name / 'execution.json'
        value = json.loads(path.read_text())
        assert value['status'] != 'running'
        for row in value['commands']:
            assert 'returncode' in row and 'completed_at' in row
            log = Path(row['log']['path'])
            assert reference(log)['sha256'] == row['log']['sha256']
        completed.append({'receipt': reference(path), 'status': value['status'],
                          'commands': [{'name': row['name'], 'returncode': row['returncode'],
                                        'timed_out': row['timed_out']} for row in value['commands']]})
    document = {
        'schema': 1,
        'kind': 'completed-browser-codec-preparation-summary',
        'summary_generator': reference(Path(__file__).resolve()),
        'summary_is_new_execution_evidence': False,
        'selected_manifest': selected,
        'selected_patch': reference(REPO / 'patches/browser-codecs/0001-enable-original-image-codecs.patch'),
        'source_inputs': reference(EVIDENCE / 'source-inputs.json'),
        'dependency_inputs': reference(EVIDENCE / 'dependency-inputs.json'),
        'baseline_gap': reference(EVIDENCE / 'baseline-gap.json'),
        'current_patch_application': reference(EVIDENCE / 'oiio-build-attempt-5/patch-application.json'),
        'current_patch_application_process': reference(EVIDENCE / 'oiio-build-attempt-5/execution.json'),
        'standalone_runtime_receipt': reference(EVIDENCE / 'validation-attempt-1/execution.json'),
        'standalone_runtime_log': reference(EVIDENCE / 'validation-attempt-1/runtime.log'),
        'standalone_runtime_manifest_sha256': validation['manifest']['sha256'],
        'completed_attempts': completed,
        'compiler_scope': 'Pinned Emscripten 6.0.5, static pthread codec libraries. Standalone Node/Wasm consumer only.',
        'observed_dependency_runtime': {
            'webp_1_6_0_lossless_rgba_max_channel_error': 0,
            'openjpeg_2_5_3_lossless_rgba_max_channel_error': 0,
            'aom_3_13_1_libheif_1_20_2_avif_max_channel_error': 1,
        },
        'recipe_version_limitations': [
            'The successful runtime receipt binds the earlier 44e3f3 manifest. The final b2881d manifest adds OIIO generated-cache preservation and validation; the four codec recipes and package-discovery fragment are unchanged between these manifests.',
            'The successful libheif compile used the retained full-context guard diff. The final recipe uses an equivalent zero-context diff with the same verified source postimage, 12b0d0fe77f06d4fa4861469638c2bb832c22edea9c63e9055567ec7cabb6ff3. The earlier build receipt is not relabeled as a final-recipe execution.',
            'Completed OIIO attempts failed before OIIO at local host-tool/cache setup. Their logs remain failed evidence. Attempt 3 failed in host preflight and has no fabricated child-process receipt.',
        ],
        'oiio_build_qualified': False,
        'oiio_active_attempt_excluded': 'compatibility/evidence/browser-codecs-5.2-2026-10-23/oiio-build-attempt-6/',
        'future_oiio_evidence_policy': 'Append a completed attempt in a later checkpoint; this completed summary does not change when that attempt finishes.',
        'acceptance_obligation': {
            'original_parent_ids': baseline['native_parent_inventory'],
            'original_subtest_ids': baseline['native_subtest_events'],
            'previous_browser_missing_subtest_ids': len(baseline['missing_subtest_ids']),
            'unchanged_upstream_test_sha256': baseline['upstream_test']['sha256'],
            'webp_and_jpeg2000_pixel_tolerance': 0,
            'avif_pixel_tolerance': 1,
            'requires_rebuilt_browser_original_invocation': True,
        },
        'new_blender_cases_executed': 0,
        'new_browser_application_passes': 0,
        'full_feature_parity': False,
    }
    old = json.loads((EVIDENCE / 'validation-attempt-1/package/manifest.json').read_text())
    old_files = {entry['path']: entry for entry in old['files']}
    new_files = {entry['path']: entry for entry in manifest['files']}
    assert set(old_files) == set(new_files)
    changed = [name for name in new_files if new_files[name]['after_sha256'] != old_files[name]['after_sha256']]
    assert changed == ['scripts/deps/openimageio.sh'], changed
    document['files_changed_since_runtime_validation'] = changed
    output.write_text(json.dumps(document, indent=2) + '\n')
    print(json.dumps(reference(output)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
