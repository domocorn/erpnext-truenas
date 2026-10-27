"""TEST ONLY: fresh native initialization followed by isolated source-image restore."""
import fcntl
import os
import runpy
from pathlib import Path
import native
import restore_job
from native_policy import operation_id
from patch_policy import SOURCE, TARGET


def main():
    root=Path('/home/frappe/frappe-bench/sites')
    if os.environ['CATALOG_IMAGE'] != SOURCE:
        raise RuntimeError('Restore only with the original source image')
    with (root/'.catalog-runtime.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        native.initialize(root,lambda:runpy.run_path('/catalog/initialize.py',run_name='__main__'))
        site=os.environ['SITE_NAME']
        os.environ.update(DESTINATION_APP='erpnext-native-recovery-test',
            NATIVE_RESTORE_ACK='disposable-native-recovery',
            RESTORE_OPERATION=operation_id(site,SOURCE),
            BACKUP_OPERATION=operation_id(site,TARGET),
            DEST_DB_ROOT_PASSWORD=os.environ['DB_ROOT_PASSWORD'])
        restore_job.run(locked=True,native=True)
        print('NATIVE RECOVERY COMPLETE. Scheduling remains paused.',flush=True)


if __name__=='__main__':
    try: main()
    except Exception as error:
        print('Native recovery blocked: '+type(error).__name__,flush=True)
        raise SystemExit(1)
