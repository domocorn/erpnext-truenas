"""Offline same-image backup, migration and resume under one lifetime lock."""
import fcntl
import importlib.util
import json
import os
import runpy


def coordinate(job, initialize):
    with (job.ROOT / '.catalog-runtime.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if os.environ['SOURCE_IMAGE'] != os.environ['TARGET_IMAGE']:
            raise RuntimeError('Coordinator currently supports same-image transitions only')
        os.environ['UPGRADE_PHASE'] = 'backup'
        site, operation, image = job.identities()
        state_path = job.ROOT / site / '.nas-upgrade-state.json'
        job.run_job(locked=True)
        os.environ['UPGRADE_PHASE'] = 'migrate'
        job.run_job(locked=True)
        state = json.loads(state_path.read_text())
        if not job.matching_state(state, operation, image) or state.get('status') not in ('migrated', 'resumed'):
            raise RuntimeError('Successful matching migration required before initialization')
        job.verify_backup(state)
        initialize()
        config_path = job.ROOT / site / 'site_config.json'
        config = json.loads(config_path.read_text())
        config.update(maintenance_mode=state['previous_maintenance'], pause_scheduler=state['previous_pause'])
        job.write_json(config_path, config)
        state['status'] = 'resumed'
        job.write_json(state_path, state)
        print('COORDINATED LIFECYCLE COMPLETE.', flush=True)


def main():
    spec = importlib.util.spec_from_file_location('coordinator_job', '/catalog/rehearsal.py')
    job = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(job)
    coordinate(job, lambda: runpy.run_path('/catalog/initialize.py', run_name='__main__'))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Coordinated lifecycle blocked: ' + type(error).__name__, flush=True)
        raise SystemExit(1)
