"""Integrated catalog candidate: bootstrap, source backup and target initialization."""
import fcntl
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
from native_policy import operation_id
from patch_policy import SOURCE, TARGET, SOURCE_DIGEST, SOURCE_ID, validate_patch
import rehearsal as job

BENCH = Path('/home/frappe/frappe-bench')


def configure(root):
    site = os.environ['SITE_NAME']
    image = os.environ['CATALOG_IMAGE']
    if image not in (SOURCE, TARGET):
        raise RuntimeError('Native candidate supports only the reviewed image pair')
    operation = operation_id(site, image)
    job.ROOT = root
    os.environ.update(OPERATION_ID=operation, SOURCE_IMAGE=SOURCE, TARGET_IMAGE=image,
        SOURCE_DIGEST=SOURCE_DIGEST, OBSERVED_SOURCE_IMAGE_ID=SOURCE_ID,
        PREVIOUS_UPGRADE_OPERATION=operation_id(site,SOURCE),
        CATALOG_OPERATION_LAYOUT='catalog-patch-v1', SIMULATE_FAILURE='0',
        EXPECTED_UPGRADE_OPERATION=operation, EXPECTED_UPGRADE_IMAGE=image)
    return site, image, operation


def read_state(root, site):
    path = root/site/'.nas-upgrade-state.json'
    return json.loads(path.read_text()) if path.exists() else None


def fresh_state(state, image, operation):
    return state and all(state.get(key)==value for key,value in (
        ('layout','catalog-native-v1'),('installation','fresh'),('operation',operation),
        ('source',image),('target',image),('status','resumed')))


def write_text(path, value):
    temporary=path.with_name(path.name+'.native-tmp')
    with temporary.open('w') as output:
        output.write(value+'\n'); output.flush(); os.fsync(output.fileno())
    temporary.replace(path)
    descriptor=os.open(path.parent,os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def bootstrap(root):
    site,image,operation=configure(root)
    marker=root/'.catalog-image'
    if marker.exists():
        installed=marker.read_text().strip()
        if (root/'.catalog-site-name').read_text().strip()!=site:
            raise RuntimeError('Native site name changed')
        if installed!=image:
            validate_patch(installed,image,SOURCE_DIGEST,SOURCE_ID)
            if not (root/site/'.nas-initialized').is_file():
                raise RuntimeError('Initialized source required before patch')
        print('Native managed storage verified.',flush=True)
        return
    if any(path.name not in ('.catalog-runtime.lock','.catalog-bootstrap.lock','.zfs') for path in root.iterdir()):
        raise RuntimeError('Non-empty unmanaged native storage')
    shutil.copytree(BENCH/'sites',root,dirs_exist_ok=True,symlinks=True)
    write_text(root/'.catalog-site-name',site)
    write_text(marker,image)
    print('Native fresh storage prepared.',flush=True)


def backup(root):
    site,image,operation=configure(root)
    installed=(root/'.catalog-image').read_text().strip()
    state=read_state(root,site)
    initialized=(root/site/'.nas-initialized').is_file()
    if installed==image:
        if not initialized and state is None:
            print('Native fresh install: source backup not needed.',flush=True)
            return
        if fresh_state(state,image,operation):
            print('Native unchanged fresh installation: no migration.',flush=True)
            return
        if job.matching_state(state,operation,SOURCE) and state.get('status') in ('migrated','resumed'):
            job.verify_backup(state)
            print('Native completed source backup verified.',flush=True)
            return
        raise RuntimeError('Native target state is incomplete or unsupported')
    validate_patch(installed,image,SOURCE_DIGEST,SOURCE_ID)
    if not state or state.get('operation')!=operation:
        if not fresh_state(state,SOURCE,operation_id(site,SOURCE)):
            raise RuntimeError('Expected managed native source installation required')
    os.environ['UPGRADE_PHASE']='backup'
    job.run_job(locked=True)


def initialize(root, install):
    site,image,operation=configure(root)
    marker=root/'.catalog-image'
    state=read_state(root,site)
    initialized=(root/site/'.nas-initialized').is_file()
    if not initialized:
        if state is not None or marker.read_text().strip()!=image:
            raise RuntimeError('Incomplete native installation state')
        saved={key:os.environ.pop(key) for key in ('EXPECTED_UPGRADE_OPERATION','EXPECTED_UPGRADE_IMAGE')}
        try: install()
        finally: os.environ.update(saved)
        if not (root/site/'.nas-initialized').is_file():
            raise RuntimeError('Native initializer did not complete')
        job.write_json(root/site/'.nas-upgrade-state.json',dict(layout='catalog-native-v1',
            installation='fresh',operation=operation,source=image,target=image,status='resumed'))
        print('NATIVE FRESH INSTALL COMPLETE.',flush=True)
        return
    if fresh_state(state,image,operation) and marker.read_text().strip()==image:
        install()
        print('NATIVE UNCHANGED INSTALL VERIFIED.',flush=True)
        return
    if image!=TARGET:
        raise RuntimeError('Native downgrade or unsupported state refused')
    import patch_target
    patch_target.finish(job,install,locked=True)
    print('NATIVE PATCH COMPLETE.',flush=True)


def main():
    action=sys.argv[1]
    root=Path('/persistent/sites') if action=='bootstrap' else BENCH/'sites'
    with (root/'.catalog-runtime.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if action=='bootstrap': bootstrap(root)
        elif action=='backup': backup(root)
        elif action=='initialize': initialize(root,lambda:runpy.run_path('/catalog/initialize.py',run_name='__main__'))
        else: raise RuntimeError('Unknown native lifecycle action')


if __name__=='__main__':
    try: main()
    except Exception as error:
        print('Native lifecycle blocked: '+type(error).__name__,flush=True)
        raise SystemExit(1)
