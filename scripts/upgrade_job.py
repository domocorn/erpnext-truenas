"""Offline job embedded in generated YAML. Requires stopped application services."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def run_job():
    site = os.environ['SITE_NAME']
    operation = os.environ['OPERATION_ID']
    target = os.environ['TARGET_IMAGE']
    source = os.environ['SOURCE_IMAGE']
    phase = os.environ['UPGRADE_PHASE']
    folder = Path('sites') / site
    state_file = folder / '.nas-upgrade-state.json'
    if not (folder / '.nas-initialized').is_file():
        raise SystemExit('Managed site marker missing; refusing upgrade.')
    with (folder / '.nas-upgrade.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads(state_file.read_text()) if state_file.exists() else None

        def bench(*arguments):
            subprocess.run(['bench', '--site', site, *arguments], check=True)

        if phase == 'backup':
            if state and state.get('operation') == operation:
                if state.get('status') in ('backed_up', 'migrated', 'resumed'):
                    print('BACKUP ALREADY COMPLETE for this operation.', flush=True)
                    return
                raise SystemExit('Interrupted operation: inspect logs and recover; no automatic retry.')
            if state and state.get('status') != 'resumed':
                raise SystemExit('A different unfinished operation exists.')
            config = json.loads((folder / 'site_config.json').read_text())
            recovery = folder / 'private' / 'nas-upgrades' / operation
            recovery.mkdir(parents=True, exist_ok=False)
            recovery.chmod(0o700)
            shutil.copyfile(folder / 'site_config.json', recovery / 'site_config.before.json')
            (recovery / 'site_config.before.json').chmod(0o600)
            state = dict(operation=operation, source=source, target=target, status='backing_up',
                         previous_maintenance=config.get('maintenance_mode', 0),
                         previous_pause=config.get('pause_scheduler', 0))
            write_json(state_file, state)
            bench('set-maintenance-mode', 'on')
            bench('disable-scheduler')
            backup_dir = folder / 'private' / 'backups'
            before = set(backup_dir.iterdir()) if backup_dir.exists() else set()
            bench('backup', '--with-files')
            created = sorted(set(backup_dir.iterdir()) - before)
            names = [p.name for p in created]
            for suffix in ('-database.sql.gz', '-files.tar', '-private-files.tar', '-site_config_backup.json'):
                matches = [n for n in names if n.endswith(suffix)]
                if suffix == '-files.tar':
                    matches = [n for n in matches if not n.endswith('-private-files.tar')]
                if not matches:
                    raise SystemExit('Expected backup component missing: ' + suffix)
            for p in created:
                if p.is_file():
                    shutil.copyfile(p, recovery / p.name)
                    (recovery / p.name).chmod(0o600)
            state['status'] = 'backed_up'
            state['backup_directory'] = str(recovery)
            state['backup_files'] = names
            write_json(state_file, state)
            print('BACKUP COMPLETE. Recovery directory: ' + str(recovery), flush=True)
            return

        if phase != 'migrate':
            raise SystemExit('Unknown upgrade phase')
        if not state or any(state.get(k) != v for k, v in (
                ('operation', operation), ('source', source), ('target', target))):
            raise SystemExit('Matching successful backup state required.')
        if state['status'] in ('migrated', 'resumed'):
            print('MIGRATION ALREADY COMPLETE.', flush=True)
            return
        if state['status'] != 'backed_up':
            raise SystemExit('Migration previously interrupted or failed. Recover before retrying.')
        if os.environ.get('SIMULATE_FAILURE') == '1':
            raise SystemExit('EXPECTED TEST FAILURE before migration. Database unchanged; resume must remain blocked.')
        # Mark BEFORE any database patch. A failed actual migration cannot retry blindly.
        state['status'] = 'migrating'
        write_json(state_file, state)
        bench('migrate')
        # Keep maintenance mode on until the target initializer verifies the site.
        bench('set-maintenance-mode', 'on')
        bench('disable-scheduler')
        state['status'] = 'migrated'
        write_json(state_file, state)
        print('MIGRATION COMPLETE. Apply the matching resume configuration.', flush=True)


if __name__ == '__main__':
    run_job()
