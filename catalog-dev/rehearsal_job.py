"""Catalog-layout offline same-image rehearsal; embedded in private stage YAML."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path('/home/frappe/frappe-bench/sites')


def write_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as output:
        os.chmod(temporary, 0o600)
        json.dump(value, output, indent=2)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def identities():
    site = os.environ['SITE_NAME']
    operation = os.environ['OPERATION_ID']
    image = os.environ['SOURCE_IMAGE']
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise RuntimeError('Invalid site name')
    if not re.fullmatch(r'[a-f0-9]{32}', operation):
        raise RuntimeError('Invalid operation ID')
    if not re.fullmatch(r'frappe/erpnext:v16\.\d+\.\d+', image):
        raise RuntimeError('Expected pinned ERPNext v16 image')
    if os.environ['TARGET_IMAGE'] != image:
        raise RuntimeError('Only same-image rehearsal is implemented')
    if (ROOT / '.catalog-site-name').read_text().strip() != site:
        raise RuntimeError('Site identity mismatch')
    if (ROOT / '.catalog-image').read_text().strip() != image:
        raise RuntimeError('Image identity mismatch')
    if not (ROOT / site / '.nas-initialized').is_file():
        raise RuntimeError('Managed initialized site required')
    return site, operation, image


def matching_state(state, operation, image):
    return state and all(state.get(key) == value for key, value in (
        ('layout', 'catalog-rehearsal-v1'), ('operation', operation),
        ('source', image), ('target', image)))


def verify_backup(state):
    recovery = ROOT / '.catalog-recovery' / state['operation']
    files = state.get('backup_files', {})
    if len(files) < 8:
        raise RuntimeError('Backup inventory incomplete')
    for name, metadata in files.items():
        if Path(name).name != name:
            raise RuntimeError('Invalid backup filename')
        path = recovery / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size != metadata['size'] or digest(path) != metadata['sha256']:
            raise RuntimeError('Backup integrity check failed')


def run_job():
    with (ROOT / '.catalog-runtime.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        site, operation, image = identities()
        folder = ROOT / site
        state_path = folder / '.nas-upgrade-state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else None

        def bench(*arguments):
            subprocess.run(['bench', '--site', site, *arguments], check=True,
                           cwd=ROOT.parent)

        if os.environ['UPGRADE_PHASE'] == 'backup':
            if state and state.get('operation') == operation:
                if matching_state(state, operation, image) and state.get('status') in ('backed_up', 'migrated', 'resumed'):
                    verify_backup(state)
                    print('BACKUP ALREADY COMPLETE.', flush=True)
                    return
                raise RuntimeError('Interrupted or mismatched operation; automatic retry refused')
            if state and (state.get('layout') != 'catalog-rehearsal-v1' or state.get('status') != 'resumed'):
                raise RuntimeError('A different unfinished or unsupported operation exists')
            config = json.loads((folder / 'site_config.json').read_text())
            recovery = ROOT / '.catalog-recovery' / operation
            recovery.mkdir(mode=0o700, parents=True, exist_ok=False)
            os.chmod(recovery.parent, 0o700)
            state = dict(layout='catalog-rehearsal-v1', operation=operation,
                source=image, target=image, status='backing_up',
                previous_maintenance=config.get('maintenance_mode', 0),
                previous_pause=config.get('pause_scheduler', 0))
            write_json(state_path, state)
            for source, name in ((folder / 'site_config.json', 'site_config.before.json'),
                    (ROOT / 'common_site_config.json', 'common_site_config.before.json'),
                    (ROOT / '.catalog-site-name', 'catalog-site-name.before'),
                    (ROOT / '.catalog-image', 'catalog-image.before')):
                shutil.copyfile(source, recovery / name)
                os.chmod(recovery / name, 0o600)
            config.update(maintenance_mode=1, pause_scheduler=1)
            write_json(folder / 'site_config.json', config)
            bench('backup', '--with-files', '--ignore-backup-conf', '--backup-path', str(recovery))
            names = [path.name for path in recovery.iterdir() if path.is_file()]
            for suffix in ('-database.sql.gz', '-files.tar', '-private-files.tar', '-site_config_backup.json'):
                matches = [name for name in names if name.endswith(suffix)]
                if suffix == '-files.tar':
                    matches = [name for name in matches if not name.endswith('-private-files.tar')]
                if len(matches) != 1:
                    raise RuntimeError('Missing or ambiguous backup component: ' + suffix)
            files = {}
            for path in recovery.iterdir():
                if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
                    raise RuntimeError('Invalid backup component')
                os.chmod(path, 0o600)
                with path.open('rb') as completed:
                    os.fsync(completed.fileno())
                files[path.name] = {'size': path.stat().st_size, 'sha256': digest(path)}
            state['backup_files'] = files
            verify_backup(state)
            state['status'] = 'backed_up'
            write_json(recovery / 'manifest.json', state)
            write_json(state_path, state)
            print('BACKUP COMPLETE: .catalog-recovery/' + operation, flush=True)
            return

        if os.environ['UPGRADE_PHASE'] != 'migrate' or not matching_state(state, operation, image):
            raise RuntimeError('Matching backup state required')
        verify_backup(state)
        if state['status'] in ('migrated', 'resumed'):
            print('MIGRATION ALREADY COMPLETE.', flush=True)
            return
        if state['status'] != 'backed_up':
            raise RuntimeError('Interrupted migration; restore recovery required before retry')
        if os.environ.get('SIMULATE_FAILURE') == '1':
            raise RuntimeError('EXPECTED TEST FAILURE before migration; resume must remain blocked')
        state['status'] = 'migrating'
        write_json(state_path, state)
        bench('migrate')
        config = json.loads((folder / 'site_config.json').read_text())
        config.update(maintenance_mode=1, pause_scheduler=1)
        write_json(folder / 'site_config.json', config)
        state['status'] = 'migrated'
        write_json(state_path, state)
        print('MIGRATION COMPLETE. Use matching guarded resume.', flush=True)


if __name__ == '__main__':
    run_job()
