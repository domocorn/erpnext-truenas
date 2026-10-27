"""Disposable VM fixture, fail-closed verification and native recovery creation."""
import argparse
import fcntl
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
from native_catalog_lab import call, guard_host
from native_catalog_lab import dump
from native_policy import operation_id
from patch_policy import SOURCE, TARGET
import restore_job

FAILURE='erpnext-native-failure-test'
RECOVERY='erpnext-native-recovery-test'
SITE='erpnext.localhost'
RUNTIME=('backend','frontend','websocket','queue-short','queue-long','scheduler')
RECOVERY_INPUT=Path('/mnt/labpool/erpnext-native-recovery-input-01')


class RecoveryStagingError(RuntimeError):
    """Only fixed, credential-free staging diagnostics may be shown directly."""

FIXTURE=r'''import frappe, json, os
from pathlib import Path
from frappe.utils.password import set_encrypted_password
root=Path('/home/frappe/frappe-bench/sites')
os.chdir(root)
path=root/'.catalog-native-failure-fixture.json'
if path.exists():
    raise RuntimeError('Fixture already exists; do not create duplicates')
frappe.init(site='erpnext.localhost',sites_path=str(root)); frappe.connect()
todo=frappe.get_doc({'doctype':'ToDo','description':'Native recovery preserved fixture'}).insert(ignore_permissions=True)
file=frappe.get_doc({'doctype':'File','file_name':'native-recovery-test.txt','is_private':1,
    'content':'Fictional native recovery attachment\n','attached_to_doctype':'ToDo','attached_to_name':todo.name}).insert(ignore_permissions=True)
set_encrypted_password('Native Recovery Fixture','native-recovery-fixture','Fictional-Native-Recovery-Secret','test_secret')
frappe.db.commit()
path.write_text(json.dumps({'todo':todo.name,'file':file.name,'file_url':file.file_url}))
frappe.destroy()
print('SOURCE FIXTURE CREATED: record, private attachment and synthetic encrypted value.')
'''

VERIFY=r'''import frappe, json, os
from pathlib import Path
from frappe.utils.password import get_decrypted_password
root=Path('/home/frappe/frappe-bench/sites')
os.chdir(root)
fixture=json.loads((root/'.catalog-native-failure-fixture.json').read_text())
frappe.init(site='erpnext.localhost',sites_path=str(root)); frappe.connect()
assert frappe.db.exists('ToDo',fixture['todo'])
assert not frappe.db.exists('ToDo',{'description':'Native failed migration fixture'})
file=frappe.get_doc('File',fixture['file'])
content=file.get_content()
if isinstance(content,bytes): content=content.decode()
assert content=='Fictional native recovery attachment\n'
assert get_decrypted_password('Native Recovery Fixture','native-recovery-fixture','test_secret')=='Fictional-Native-Recovery-Secret'
assert frappe.conf.pause_scheduler==1
frappe.destroy()
print('RECOVERY DATA VERIFIED: original record, private attachment and encrypted value; failed-migration record absent.')
'''


def app(name, version, state=None):
    items=call('app.query',[['id','=',name]])
    if (len(items)!=1 or items[0]['custom_app'] or items[0]['version']!=version or
            items[0]['metadata'].get('name') != name.replace('-test','-lab')):
        raise RuntimeError('Unexpected native lab app identity')
    if state and items[0]['state']!=state:
        raise RuntimeError('Unexpected native lab app state')
    return items[0]


def container(name,service,running=True):
    ids=subprocess.check_output(['docker','ps','-q' if running else '-aq',
        '--filter','label=com.docker.compose.project=ix-'+name,
        '--filter','label=com.docker.compose.service='+service],text=True).split()
    if len(ids)!=1:
        raise RuntimeError('Expected exactly one '+service+' container for '+name)
    return json.loads(subprocess.check_output(['docker','inspect',ids[0]],text=True))[0]


def sites(name, running=True):
    # Bootstrap has completed even when dependency failure prevents the backend
    # from being created or started. Do not depend on a failed runtime existing.
    info=container(name,'backend' if running else 'bootstrap',running)
    target='/home/frappe/frappe-bench/sites' if running else '/persistent/sites'
    mounts=[m for m in info['Mounts'] if m['Destination']==target]
    if len(mounts)!=1 or mounts[0]['Type']!='bind':
        raise RuntimeError('Unexpected sites mount')
    root=Path(mounts[0]['Source'])
    expected=Path('/mnt/.ix-apps/app_mounts')/name/'sites'
    if root!=expected or root.is_symlink():
        raise RuntimeError('Expected dedicated native ixVolume sites dataset')
    return root


def execute(name, program):
    info=container(name,'backend')
    result=subprocess.run(['docker','exec','-i',info['Id'],
        '/home/frappe/frappe-bench/env/bin/python','-c','import sys; exec(sys.stdin.read())'],
        input=program,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError('Fixture verification failed; inspect the lab backend privately')
    print(result.stdout.strip())


def fixture():
    app(FAILURE,'0.9.0','RUNNING')
    info=container(FAILURE,'backend')
    if info['Config']['Image']!=SOURCE:
        raise RuntimeError('Expected reviewed source image')
    execute(FAILURE,FIXTURE)
    subprocess.run(['docker','exec',info['Id'],'bench','--site',SITE,
                    'set-config','pause_scheduler','1'],check=True,capture_output=True)
    print('SOURCE SCHEDULER PAUSED. Ready for the deliberate native upgrade failure.')


def failed():
    app(FAILURE,'1.0.0')
    root=sites(FAILURE,running=False)
    state=json.loads((root/SITE/'.nas-upgrade-state.json').read_text())
    if (state.get('status')!='migrating' or state.get('operation')!=operation_id(SITE,TARGET)
            or (root/'.catalog-image').read_text().strip()!=SOURCE
            or not (root/'.catalog-native-failure-entered').is_file()):
        raise RuntimeError('Expected actual partial native migration with uncommitted target identity')
    for service in RUNTIME:
        ids=subprocess.check_output(['docker','ps','-q','--filter',
            'label=com.docker.compose.project=ix-'+FAILURE,'--filter',
            'label=com.docker.compose.service='+service],text=True).split()
        if ids:
            raise RuntimeError('Unexpected running source runtime: '+service)
    recovery=root/'.catalog-recovery'/operation_id(SITE,TARGET)
    restore_job.INPUT=recovery
    restore_job.inventory(SOURCE,operation_id(SITE,TARGET))
    print('FAILED NATIVE UPGRADE VERIFIED: migrating state, old identity, runtime blocked, backup checksums valid.')
    return root,recovery


def ensure_recovery_catalog(bundle):
    """Reuse only an intact, owned source overlay after app creation stopped."""
    script=bundle/'recovery/native_catalog_lab.py'
    spec=importlib.util.spec_from_file_location('native_recovery_stager',script)
    stager=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stager)
    if (stager.APP!='erpnext-native-recovery-lab' or
            stager.STATE!=Path('/root/erpnext-native-recovery-catalog-lab')):
        raise RecoveryStagingError('Unexpected recovery staging helper')
    stage_recovery_catalog(stager,bundle)


def stage_recovery_catalog(stager,bundle):
    script=bundle/'recovery/native_catalog_lab.py'
    state_file=stager.STATE/'state.json'
    if not state_file.exists():
        subprocess.run([sys.executable,str(script),'source','--disposable-vm'],check=True)
        return
    with (stager.STATE/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stager.guard_host()
        state=json.loads(state_file.read_text())
        if state.get('pending') or state.get('role')!='source' or (stager.STATE/'removed-state.json').exists():
            raise RecoveryStagingError('Recovery staging is incomplete or removed')
        manifest=json.loads((bundle/'recovery/manifest.json').read_text())
        entry=manifest['entries']['source']
        files=manifest['app_files']['source']
        index=stager.CATALOG/'catalog.json'
        before=index.read_bytes()
        catalog=json.loads(before)
        if state.get('entry')!=entry or state.get('files')!=files:
            raise RecoveryStagingError('Recovery staging journal does not match this bundle')
        current=catalog.get('community',{}).get(stager.APP)
        live=stager.CATALOG/'trains/community'/stager.APP
        if current is not None and current!=entry:
            raise RecoveryStagingError('Another catalog entry occupies the recovery name; preserving it')
        present=live.exists() or live.is_symlink()
        if present and stager.tree_hash(live)!=files:
            raise RecoveryStagingError('Recovery app files changed externally; preserving them')
        if current is None or not present:
            incoming=bundle/'recovery/source/trains/community'/stager.APP
            if stager.tree_hash(incoming)!=files:
                raise RecoveryStagingError('Recovery bundle files failed verification')
            updated=stager.merge_entry(catalog,current,entry)
            stager.validate_catalog(updated)
            saved=stager.STATE/('catalog-before-restage-'+hashlib.sha256(before).hexdigest()[:16]+'.json')
            if not saved.exists():
                stager.atomic(saved,before)
            staged=None
            if not present:
                staged=Path(tempfile.mkdtemp(prefix='.'+stager.APP+'-restage-',dir=live.parent))
                shutil.copytree(incoming,staged,dirs_exist_ok=True)
                if stager.tree_hash(staged)!=files:
                    raise RecoveryStagingError('Copied recovery app failed verification')
            if index.read_bytes()!=before:
                raise RecoveryStagingError('Catalog changed during recovery restaging; no index was overwritten')
            if staged:
                if live.exists() or live.is_symlink():
                    raise RecoveryStagingError('Recovery app directory appeared during restaging; preserving it')
                staged.rename(live)
            if current is None:
                stager.dump(index,updated)
            print('RECOVERY CATALOG RESTORED: verified bundle restored the missing lab overlay.')
        stager.refresh()
        print('RECOVERY CATALOG VERIFIED: reusing the intact staged source entry.')


def prepare_recovery_input(source):
    """Copy verified backup components outside the restricted .ix-apps tree."""
    source=Path(source)
    previous=restore_job.INPUT
    try:
        restore_job.INPUT=source
        restore_job.inventory(SOURCE,operation_id(SITE,TARGET))
        manifest_bytes=(source/'manifest.json').read_bytes()
        manifest=json.loads(manifest_bytes)
        base=RECOVERY_INPUT
        if base.resolve()!=base or not base.parent.is_dir():
            raise RecoveryStagingError('Recovery input directory must be on the existing lab pool without symlinks')
        identity={'purpose':'disposable-native-recovery-input','source':str(source),
                  'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest()}
        marker=base/'.native-recovery-input.json'
        if base.exists():
            if base.is_symlink() or not marker.is_file() or marker.is_symlink() or json.loads(marker.read_text())!=identity:
                raise RecoveryStagingError('Recovery input directory is not owned by this backup operation')
        else:
            base.mkdir(mode=0o700)
            dump(marker,identity)
        destination=base/manifest['operation']
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or (destination/'manifest.json').read_bytes()!=manifest_bytes:
                raise RecoveryStagingError('Existing recovery input does not match the original backup')
            restore_job.INPUT=destination
            restore_job.inventory(SOURCE,operation_id(SITE,TARGET))
            print('RECOVERY INPUT VERIFIED: reusing the checksum-valid private lab copy.')
            return destination
        staged=Path(tempfile.mkdtemp(prefix='.copy-',dir=base))
        for name in [*manifest['backup_files'],'manifest.json']:
            target=staged/name
            with target.open('xb') as output:
                if name=='manifest.json':
                    output.write(manifest_bytes)
                else:
                    with (source/name).open('rb') as original:
                        shutil.copyfileobj(original,output)
                output.flush(); os.fsync(output.fileno())
            os.chown(target,1000,1000)
            os.chmod(target,0o400)
        restore_job.INPUT=staged
        restore_job.inventory(SOURCE,operation_id(SITE,TARGET))
        os.chown(staged,1000,1000)
        os.chmod(staged,0o500)
        staged.rename(destination)
        descriptor=os.open(base,os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
        print('RECOVERY INPUT COPIED AND VERIFIED: original backup unchanged; private lab copy mounted read-only.')
        return destination
    finally:
        restore_job.INPUT=previous


def recover():
    root,recovery=failed()
    if call('app.query',[['id','=',RECOVERY]]):
        raise RuntimeError('Recovery destination already exists; do not replace it')
    pools=call('pool.query',[['name','=','labpool']])
    if len(pools)!=1 or pools[0].get('status')!='ONLINE':
        raise RecoveryStagingError('Expected the online disposable labpool pool before copying backup input')
    recovery=prepare_recovery_input(recovery)
    bundle=Path(__file__).resolve().parent
    ensure_recovery_catalog(bundle)
    values={'erpnext':{'site_name':SITE,'admin_password':secrets.token_urlsafe(24),
                      'db_password':secrets.token_urlsafe(24),'recovery_path':str(recovery)},
            'network':{'web_port':{'bind_mode':'published','port_number':18092,'host_ips':[]}}}
    print('CREATING NATIVE RECOVERY APP: separate ixVolumes and database credentials.')
    job=call('app.create',{'app_name':RECOVERY,'catalog_app':'erpnext-native-recovery-lab',
                          'train':'community','version':'0.9.0','values':values})
    print('NATIVE RECOVERY CREATE JOB:',job)
    print('Wait for erpnext-native-recovery-test to become Running on port 18092.')


def verified():
    failed_root,_=failed()
    app(RECOVERY,'0.9.0','RUNNING')
    recovered=sites(RECOVERY)
    if recovered==failed_root:
        raise RuntimeError('Recovery shares source storage')
    state=json.loads((recovered/SITE/'.nas-upgrade-state.json').read_text())
    if state.get('status')!='resumed' or state.get('restoration')!=operation_id(SITE,SOURCE):
        raise RuntimeError('Native recovery state mismatch')
    if container(RECOVERY,'backend')['Config']['Image']!=SOURCE or (recovered/'.catalog-image').read_text().strip()!=SOURCE:
        raise RuntimeError('Native recovery is not using the exact source image')
    # The fixture inventory is not a Bench backup component. Copy this small
    # identifier-only test file; restored records/files themselves must exist.
    fixture_path=recovered/'.catalog-native-failure-fixture.json'
    if fixture_path.is_symlink():
        raise RuntimeError('Unexpected recovery fixture symlink')
    original=(failed_root/'.catalog-native-failure-fixture.json').read_bytes()
    if fixture_path.exists() and fixture_path.read_bytes()!=original:
        raise RuntimeError('Recovery fixture inventory mismatch')
    if not fixture_path.exists():
        fixture_path.write_bytes(original)
    execute(RECOVERY,VERIFY)
    def database_password(name):
        env=dict(item.split('=',1) for item in container(name,'db')['Config']['Env'] if '=' in item)
        return env.get('MARIADB_ROOT_PASSWORD')
    first=database_password(FAILURE)
    second=database_password(RECOVERY)
    if not first or not second or first==second:
        raise RuntimeError('Recovery database root password is not independent')
    print('NATIVE RECOVERY VERIFIED: independent app/storage/database password; failed source preserved.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('fixture','verify-failed','recover','verify-recovered'))
    parser.add_argument('--disposable-vm',action='store_true',required=True)
    args=parser.parse_args()
    try:
        guard_host()
        {'fixture':fixture,'verify-failed':failed,'recover':recover,'verify-recovered':verified}[args.action]()
    except Exception as error:
        if isinstance(error,RecoveryStagingError):
            raise SystemExit('STOP: '+str(error))
        raise SystemExit('STOP: '+type(error).__name__+'; preserve the lab state and report this step.')
