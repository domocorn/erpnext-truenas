"""Target-image migration and durable identity commit under exclusive exclusion."""
import fcntl
from contextlib import nullcontext
import importlib.util
import json
import os
from pathlib import Path
import runpy

BAKED = Path('/home/frappe/frappe-bench/assets')

def finish(job, initialize, locked=False):
    with (nullcontext() if locked else (job.ROOT / '.catalog-runtime.lock').open('a')) as lock:
        if not locked:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.environ['UPGRADE_PHASE'] = 'migrate'
        site, operation, source = job.identities(allow_target=True)
        state_path = job.ROOT / site / '.nas-upgrade-state.json'
        job.run_job(locked=True)
        state = json.loads(state_path.read_text())
        if not job.matching_state(state, operation, source) or state.get('status') not in ('migrated', 'resumed'):
            raise RuntimeError('Successful matching patch migration required')
        job.verify_backup(state)
        assets = job.ROOT / 'assets'
        baked = BAKED
        if not baked.is_dir() or not assets.is_symlink() or assets.readlink() != baked:
            raise RuntimeError('Expected official baked asset symlink required')
        marker = job.ROOT / '.catalog-image'
        temporary = marker.with_name(marker.name + '.patch-tmp')
        with temporary.open('w') as output:
            output.write(os.environ['TARGET_IMAGE'] + '\n')
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(marker)
        descriptor = os.open(marker.parent, os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
        initialize()
        config_path = job.ROOT / site / 'site_config.json'
        config = json.loads(config_path.read_text())
        config.update(maintenance_mode=state['previous_maintenance'], pause_scheduler=state['previous_pause'])
        job.write_json(config_path, config)
        state['status'] = 'resumed'
        job.write_json(state_path, state)
        print('PATCH LIFECYCLE COMPLETE.', flush=True)


def main():
    spec = importlib.util.spec_from_file_location('patch_job', '/catalog/rehearsal.py')
    job = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job)
    finish(job, lambda: runpy.run_path('/catalog/initialize.py', run_name='__main__'))


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print('Patch lifecycle blocked: ' + type(error).__name__, flush=True)
        raise SystemExit(1)
