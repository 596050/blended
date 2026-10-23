from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

workspace = Path('/workspace/scratch/d63596d831b2')
repo = workspace / 'blended'
evidence = repo / 'compatibility/evidence/product-fixture-hydration-2026-10-23'
log_path = workspace / 'runtime/product-fixture-hydration-2026-10-23.host.log'
command = [sys.executable, '-u', str(repo / 'tools/hydrate_product_fixtures.py'),
           '--inventory', str(repo / 'compatibility/evidence/source-inventory-2026-10-23/product-source-inventory.json'),
           '--source-archive', str(workspace / 'runtime/blender-product-94363991.tar.gz'),
           '--source-root', str(workspace / 'runtime/upstream-product/blender-94363991e7dcf39e2d70614aa002ab6f67764a5d'),
           '--source-commit', '94363991e7dcf39e2d70614aa002ab6f67764a5d',
           '--archive-sha256', 'e2c8bc5911c178f96ff747763a980c68f54929ffd1cced31b2fd79e32bc80cb7',
           '--evidence', str(evidence),
           '--object-cache', str(workspace / 'runtime/product-test-lfs-objects'), '--workers', '8']
started = datetime.now(timezone.utc).isoformat()
with log_path.open('xb') as log:
    process = subprocess.run(command, cwd=repo, stdout=log, stderr=subprocess.STDOUT)
if evidence.is_dir():
    shutil.copyfile(log_path, evidence / 'host.log')
    shutil.copyfile(__file__, evidence / 'run-hydration.py')
    data = log_path.read_bytes()
    record = {'command': command, 'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
              'returncode': process.returncode, 'tests_executed': 0,
              'log': {'path': 'host.log', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}}
    (evidence / 'host-process.json').write_text(json.dumps(record, indent=2) + '\n')
print(log_path.read_text()[-5000:])
raise SystemExit(process.returncode)
