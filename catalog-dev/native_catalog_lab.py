"""Reversible single-app catalog overlay for the disposable TrueNAS 25.10.7 VM."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

APP = 'erpnext-native-lab'
CATALOG = Path('/mnt/.ix-apps/truenas_catalog')
STATE = Path('/root/erpnext-native-catalog-lab')
INSTANCE = 'erpnext-native-test'


def call(method, *args):
    result = subprocess.run(['midclt', 'call', method, *[json.dumps(a) for a in args]],
                            check=True, text=True, capture_output=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()


def atomic(path, content, mode=0o600):
    fd, name = tempfile.mkstemp(prefix='.native-lab-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        if path.exists():
            stat = path.stat()
            os.chmod(name, stat.st_mode & 0o777)
            os.chown(name, stat.st_uid, stat.st_gid)
        os.replace(name, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def dump(path, data):
    atomic(path, (json.dumps(data, indent=2)+'\n').encode())


def tree_hash(root):
    result = {}
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError('Expected a real lab app directory')
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('Symlinks are not allowed in the lab bundle')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise RuntimeError('Unsupported lab bundle entry')
    return result


def merge_entry(catalog, expected, replacement):
    """Compare ownership before changing only this one catalog entry."""
    result = copy.deepcopy(catalog)
    community = result.setdefault('community', {})
    if community.get(APP) != expected:
        raise RuntimeError('Lab entry changed externally; preserving the catalog')
    if replacement is None:
        community.pop(APP, None)
    else:
        community[APP] = replacement
    return result


def guard_host():
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo in the disposable VM host shell')
    if call('system.version') != 'TrueNAS-25.10.7':
        raise RuntimeError('This lab procedure requires exactly TrueNAS-25.10.7')
    config = call('catalog.config')
    if config['location'] != str(CATALOG) or config['label'] != 'TRUENAS':
        raise RuntimeError('Unexpected catalog configuration')
    if CATALOG.is_symlink() or not (CATALOG/'catalog.json').is_file():
        raise RuntimeError('Unexpected catalog filesystem layout')
    if call('core.get_jobs', [['method', '=', 'catalog.sync'], ['state', 'in', ['RUNNING', 'WAITING']]]):
        raise RuntimeError('Wait for catalog sync to finish before staging')


def refresh():
    call('catalog.apps', {'cache': False, 'retrieve_all_trains': True})


def validate_catalog(data):
    from jsonschema import validate
    from apps_validation.json_schema_utils import CATALOG_JSON_SCHEMA
    validate(data, CATALOG_JSON_SCHEMA)


def stage(bundle, role):
    index = CATALOG/'catalog.json'
    live = CATALOG/'trains/community'/APP
    state_file = STATE/'state.json'
    state = json.loads(state_file.read_text()) if state_file.exists() else None
    if (STATE/'removed-state.json').exists():
        raise RuntimeError('This lab staging run was removed; preserve its evidence and use a fresh VM snapshot for a new run')
    if state and state.get('pending'):
        raise RuntimeError('Incomplete staging operation: use remove before staging again')
    if role == 'source' and state:
        raise RuntimeError('Source was already staged; use status or remove')
    if role == 'target' and (not state or state['role'] != 'source'):
        raise RuntimeError('Stage and test the native source installation first')
    if role == 'target':
        apps = call('app.query', [['id', '=', INSTANCE]])
        if len(apps) != 1 or apps[0]['custom_app'] or apps[0]['version'] != '0.9.0' or apps[0]['state'] != 'RUNNING':
            raise RuntimeError('Expected the running native 0.9.0 test instance')
        if apps[0]['metadata'].get('name') != APP:
            raise RuntimeError('Unexpected native test instance metadata')
    incoming = bundle/role/'trains/community'/APP
    catalog = json.loads((bundle/role/'catalog.json').read_text())
    entry = catalog['community'][APP]
    version = '0.9.0' if role == 'source' else '1.0.0'
    manifest = json.loads((bundle/'manifest.json').read_text())
    hashes = tree_hash(incoming)
    if manifest['app_files'][role] != hashes or entry != manifest['entries'][role]:
        raise RuntimeError('Bundle content does not match its manifest')
    if not entry['healthy'] or entry['latest_version'] != version:
        raise RuntimeError('Unexpected native lab catalog entry')
    before = index.read_bytes()
    prior = json.loads(before)
    expected = state['entry'] if state else None
    updated = merge_entry(prior, expected, entry)
    validate_catalog(updated)
    if state:
        if tree_hash(live) != state['files']:
            raise RuntimeError('Live lab app files changed externally')
    elif live.exists():
        raise RuntimeError('Lab app directory already exists; refusing to replace it')
    # Renames must stay on the catalog filesystem, even if /root is elsewhere.
    staged = live.parent/('.'+APP+'-'+role+'-staged')
    if staged.exists():
        raise RuntimeError('Staging directory already exists; inspect prior attempt')
    shutil.copytree(incoming, staged)
    if tree_hash(staged) != hashes:
        raise RuntimeError('Copied bundle failed verification')
    # Record all owned states before any live mutation, so remove can recover.
    if not state:
        atomic(STATE/'original-catalog.json', before)
        state = {'role': role, 'entry': None, 'files': None}
    state['pending'] = {'role': role, 'entry': entry, 'files': hashes}
    dump(state_file, state)
    if index.read_bytes() != before:
        raise RuntimeError('Catalog changed during staging; no index was overwritten')
    if live.exists():
        preserved = live.parent/('.'+APP+'-source-preserved')
        if preserved.exists():
            raise RuntimeError('Preserved source already exists; inspect prior attempt')
        live.rename(preserved)
    staged.rename(live)
    dump(index, updated)
    state.update(role=role, entry=entry, files=hashes, pending=None)
    dump(state_file, state)
    refresh()
    print('STAGED:', role, version, '— unrelated catalog entries preserved.')
    print('Backups and staging record:', STATE)


def remove():
    state_file = STATE/'state.json'
    state = json.loads(state_file.read_text())
    live = CATALOG/'trains/community'/APP
    index = CATALOG/'catalog.json'
    before = index.read_bytes()
    catalog = json.loads(before)
    current = catalog.get('community', {}).get(APP)
    allowed = [state['entry']]
    files = [state['files']]
    if state.get('pending'):
        allowed.append(state['pending']['entry'])
        files.append(state['pending']['files'])
    # Sync may have removed the overlay. Never remove a different app entry.
    if current is not None and current not in allowed:
        raise RuntimeError('Catalog entry is no longer owned by this lab')
    if live.exists() and tree_hash(live) not in files:
        raise RuntimeError('Lab files changed externally; preserving them')
    updated = merge_entry(catalog, current, None)
    validate_catalog(updated)
    if index.read_bytes() != before:
        raise RuntimeError('Catalog changed during removal')
    if live.exists():
        removed = live.parent/('.'+APP+'-removed')
        if removed.exists():
            raise RuntimeError('Removed app archive already exists')
        live.rename(removed)
    dump(index, updated)
    state_file.rename(STATE/'removed-state.json')
    refresh()
    print('Lab catalog entry removed; original app data and other catalog entries preserved.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('source', 'target', 'status', 'remove'))
    parser.add_argument('--disposable-vm', action='store_true', required=True)
    args = parser.parse_args()
    guard_host()
    STATE.mkdir(mode=0o700, exist_ok=True)
    with (STATE/'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action in ('source', 'target'):
            stage(Path(__file__).resolve().parent, args.action)
        elif args.action == 'remove':
            remove()
        else:
            state_file = STATE/'state.json'
            state = json.loads(state_file.read_text()) if state_file.exists() else None
            print(json.dumps({'staged_role': state and state['role'],
                              'pending': bool(state and state.get('pending'))}))
            apps = call('app.query', [['id', '=', INSTANCE]])
            for app in apps:
                print(json.dumps({k: app[k] for k in ('name', 'version', 'state', 'custom_app', 'upgrade_available')}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('STOP: '+str(error))
