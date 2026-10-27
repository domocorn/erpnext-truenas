"""Explicit same-content image identity transition, after a verified migration."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import runpy


def main():
    spec = importlib.util.spec_from_file_location('pinning_job', '/catalog/rehearsal.py')
    job = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job)
    bootstrap = os.environ.get('PINNING_GATE') == 'bootstrap'
    if bootstrap:
        job.ROOT = Path('/persistent/sites')
    with (job.ROOT / '.catalog-runtime.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        site, operation, source = job.identities(allow_target=True)
        state_path = job.ROOT / site / '.nas-upgrade-state.json'
        state = json.loads(state_path.read_text())
        if not job.matching_state(state, operation, source) or state.get('status') not in ('migrated', 'resumed'):
            raise RuntimeError('Successful matching migration required; resume blocked')
        job.verify_backup(state)
        marker = job.ROOT / '.catalog-image'
        if bootstrap:
            # Only the proven same-content transition may change this marker.
            old, _ = job.image_parts(source)
            new, digest = job.image_parts(os.environ['TARGET_IMAGE'])
            if old != new or digest != os.environ['SOURCE_DIGEST']:
                raise RuntimeError('Gate supports same-content pinning only')
            temporary = marker.with_name(marker.name + '.tmp')
            with temporary.open('w') as output:
                output.write(os.environ['TARGET_IMAGE'] + '\n')
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(marker)
            descriptor = os.open(marker.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            print('Verified same-content image identity pinned.', flush=True)
            return
        if marker.read_text().strip() != os.environ['TARGET_IMAGE']:
            raise RuntimeError('Bootstrap has not completed the identity transition')
        runpy.run_path('/catalog/initialize.py', run_name='__main__')
        # Reconcile and durably persist flags even if an earlier resume was interrupted.
        config_path = job.ROOT / site / 'site_config.json'
        config = json.loads(config_path.read_text())
        config.update(maintenance_mode=state['previous_maintenance'], pause_scheduler=state['previous_pause'])
        job.write_json(config_path, config)
        state['status'] = 'resumed'
        job.write_json(state_path, state)


if __name__ == '__main__':
    main()
