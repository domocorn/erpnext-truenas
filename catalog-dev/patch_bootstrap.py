"""Verify existing managed source/finished target without changing identity."""
import fcntl
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('patch_bootstrap_job', '/catalog/rehearsal.py')
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)
job.ROOT = Path('/persistent/sites')
with (job.ROOT / '.catalog-runtime.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    site, operation, image = job.identities(allow_target=True)
    if (job.ROOT / '.catalog-image').read_text().strip() != image:
        state = json.loads((job.ROOT / site / '.nas-upgrade-state.json').read_text())
        if not job.matching_state(state, operation, image) or state.get('status') not in ('migrated', 'resumed'):
            raise RuntimeError('Matching successful patch state required for target marker')
    print('Managed patch source/target identity verified.', flush=True)
