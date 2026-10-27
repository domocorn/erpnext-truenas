"""Restore a checksummed catalog backup into an isolated initialized lab clone."""
import fcntl
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('/home/frappe/frappe-bench/sites')
INPUT = Path('/recovery')


def write_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as output:
        os.chmod(temporary, 0o600)
        json.dump(value, output, indent=2)
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def inventory(image, operation):
    manifest = json.loads((INPUT / 'manifest.json').read_text())
    if any(manifest.get(key) != value for key, value in (
            ('operation', operation), ('status', 'backed_up'))):
        raise RuntimeError('Backup manifest identity mismatch')
    if manifest.get('layout') == 'catalog-patch-v1':
        from patch_policy import SOURCE, validate_patch
        if image != SOURCE or manifest.get('source') != image:
            raise RuntimeError('Restore patch backup using its original source image')
        validate_patch(manifest['source'], manifest.get('target'), manifest.get('source_digest'), manifest.get('observed_source_image_id'))
    elif manifest.get('target') != image:
        raise RuntimeError('Backup manifest identity mismatch')
    if manifest.get('layout') == 'catalog-rehearsal-v1':
        if manifest.get('source') != image:
            raise RuntimeError('Backup manifest identity mismatch')
    elif manifest.get('layout') == 'catalog-upgrade-v1':
        match = re.fullmatch(r'(frappe/erpnext:v16\.\d+\.\d+)@(sha256:[a-f0-9]{64})', image)
        if (not match or manifest.get('source') not in (match[1], image)
                or manifest.get('source_digest') != match[2]
                or not re.fullmatch(r'sha256:[a-f0-9]{64}', manifest.get('observed_source_image_id', ''))):
            raise RuntimeError('Backup pinning identity mismatch')
    elif manifest.get('layout') != 'catalog-patch-v1':
        raise RuntimeError('Unsupported backup layout')
    files = manifest.get('backup_files', {})
    if len(files) < 8:
        raise RuntimeError('Incomplete backup manifest')
    for name, expected in files.items():
        if Path(name).name != name:
            raise RuntimeError('Invalid backup filename')
        path = INPUT / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected['size']:
            raise RuntimeError('Invalid backup component')
        with path.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != expected['sha256']:
                raise RuntimeError('Backup checksum mismatch')
    result = {}
    for key, suffix in (('database', '-database.sql.gz'), ('public', '-files.tar'),
            ('private', '-private-files.tar'), ('config', '-site_config_backup.json')):
        matches = [name for name in files if name.endswith(suffix)
            and (key != 'public' or not name.endswith('-private-files.tar'))]
        if len(matches) != 1:
            raise RuntimeError('Missing or ambiguous backup component')
        result[key] = INPUT / matches[0]
    return result


def run(locked=False, native=False):
    site = os.environ['SITE_NAME']
    operation = os.environ['RESTORE_OPERATION']
    image = os.environ['CATALOG_IMAGE']
    if not re.fullmatch(r'[a-f0-9]{32}', operation):
        raise RuntimeError('Invalid restore operation')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise RuntimeError('Invalid site name')
    destination = os.environ['DESTINATION_APP']
    if native:
        from patch_policy import SOURCE
        from native_policy import operation_id
        if (destination != 'erpnext-native-recovery-test' or image != SOURCE or
                os.environ.get('NATIVE_RESTORE_ACK') != 'disposable-native-recovery'):
            raise RuntimeError('Dedicated native recovery destination required')
    elif destination not in ('erpnext-catalog-restore-test', 'erpnext-catalog-pinned-recovery-test', 'erpnext-catalog-interrupt-recovery-test', 'erpnext-catalog-patch-recovery-test'):
        raise RuntimeError('Disposable restore destination required')
    with (nullcontext() if locked else (ROOT / '.catalog-runtime.lock').open('a')) as lock:
        if not locked:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (ROOT / '.catalog-site-name').read_text().strip() != site or (ROOT / '.catalog-image').read_text().strip() != image:
            raise RuntimeError('Destination identity mismatch')
        folder = ROOT / site
        if not (folder / '.nas-initialized').is_file():
            raise RuntimeError('Initialize the isolated destination first')
        state_path = folder / '.nas-upgrade-state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if native and all(state.get(k) == v for k, v in (
                    ('layout', 'catalog-native-v1'), ('installation', 'fresh'),
                    ('operation', operation_id(site, image)), ('source', image),
                    ('target', image), ('status', 'resumed'))):
                if state.get('restoration') == operation:
                    print('NATIVE RESTORE ALREADY COMPLETE.', flush=True)
                    return
                if state.get('restoration') is not None:
                    raise RuntimeError('Native destination already restored from another operation')
                # A known fresh native installation may be replaced once. The
                # restoring state is persisted below before any database changes.
            elif not native and all(state.get(k) == v for k, v in (('layout', 'catalog-restore-v1'),
                    ('operation', operation), ('status', 'resumed'), ('target', image))):
                print('RESTORE ALREADY COMPLETE.', flush=True)
                return
            else:
                raise RuntimeError('Restore state exists; interrupted restore cannot retry blindly')
        elif native:
            raise RuntimeError('Expected a managed fresh native destination')
        backups = inventory(image, os.environ['BACKUP_OPERATION'])
        config_before = json.loads((folder / 'site_config.json').read_text())
        state = dict(layout='catalog-restore-v1', operation=operation, target=image,
            source=image, status='restoring', previous_maintenance=0, previous_pause=1)
        write_json(state_path, state)
        write_json(folder / '.catalog-before-restore.json', config_before)

        def bench(*arguments):
            subprocess.run(['bench', '--site', site, *arguments], cwd=ROOT.parent,
                check=True, stdin=subprocess.DEVNULL)

        bench('restore', str(backups['database']), '--db-root-username', 'root',
            '--db-root-password', os.environ['DEST_DB_ROOT_PASSWORD'],
            '--with-public-files', str(backups['public']),
            '--with-private-files', str(backups['private']))
        config = json.loads((folder / 'site_config.json').read_text())
        if config['db_name'] != config_before['db_name']:
            raise RuntimeError('Destination database identity changed unexpectedly')
        source = json.loads(backups['config'].read_text())
        if source.get('encryption_key'):
            config['encryption_key'] = source['encryption_key']
        else:
            # Do not retain the unrelated fresh destination encryption key.
            config.pop('encryption_key', None)
        config.update(maintenance_mode=1, pause_scheduler=1)
        write_json(folder / 'site_config.json', config)
        bench('migrate')
        config = json.loads((folder / 'site_config.json').read_text())
        config.update(maintenance_mode=0, pause_scheduler=1)
        write_json(folder / 'site_config.json', config)
        state['status'] = 'resumed'
        if native:
            state.update(layout='catalog-native-v1', installation='fresh',
                         operation=operation_id(site,image), restoration=operation,
                         backup_operation=os.environ['BACKUP_OPERATION'])
        write_json(state_path, state)
        print('RESTORE COMPLETE. Clone scheduling remains paused.', flush=True)


if __name__ == '__main__':
    try: run()
    except Exception as error:
        # Subprocess exceptions can contain the destination DB password in argv.
        print('Restore blocked or failed: ' + type(error).__name__, flush=True)
        sys.exit(1)
