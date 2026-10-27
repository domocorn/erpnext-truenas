# Real patch transition and source-version backup recovery

The same-image coordinator passed in your VM. This next test creates a NEW
**erpnext-catalog-patch-test** on **18088**, initializes v16.51.0, then upgrades
that test site to v16.51.1. Your working 18087 app stays unchanged. No existing
site is downgraded. The earlier failed 18086 app may remain stopped/guarded.

The helper permits only the reviewed immutable image pair in patch_policy.py.
This is a custom-app lifecycle test, not a native catalog upgrade. Keep snapshots
and backups; unexpected failures require investigation, not clearing guards or
reapplying the older YAML over migrated data.

## 1. Create fresh patch-test storage

In the disposable VM host shell:

```bash
sudo test ! -e /mnt/labpool/erpnext-catalog-patch-test && \
sudo mkdir -p /mnt/labpool/erpnext-catalog-patch-test/sites \
  /mnt/labpool/erpnext-catalog-patch-test/logs \
  /mnt/labpool/erpnext-catalog-patch-test/db_data \
  /mnt/labpool/erpnext-catalog-patch-test/queue_data
```

If the destination already exists, stop; do not erase it to fit this plan.

## 2. Initialize the older-version test source

Install a NEW app named **erpnext-catalog-patch-test**, using the complete private
`generated/catalog-patch-01/01-initialize-source.yaml`. Wait for successful
initialization and nine healthy persistent services. Open
http://172.22.237.80:18088 and log in as Administrator using the NEW password
in this file's initializer `ADMIN_PASSWORD`. It differs from earlier test apps.

Run this in the VM host shell:

```bash
backend=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-catalog-patch-test --filter label=com.docker.compose.service=backend)
# STOP if the lookup is empty or contains multiple IDs.
sudo docker exec "$backend" /home/frappe/frappe-bench/env/bin/python -c 'import erpnext; print(erpnext.__version__)'
sudo docker exec "$backend" bench --site erpnext.localhost set-config pause_scheduler 1
```

The version must be **16.51.0**. Create a fictional record and attach a private
file (also public if desired). Note their names and verify the attachments open.
Take a fresh pre-upgrade VM snapshot after these fixtures exist.

## 3. Apply the single patch deployment

Stop ONLY the patch-test app and wait for its runtimes to stop. Replace its full
YAML with **generated/catalog-patch-01/02-upgrade.yaml** and start it.

The bootstrap verifies the managed source. `patch-backup` runs in the OLD image,
checks exclusive runtime access and creates the offline backup. The initializer
then runs migration in the NEW image under exclusive access, verifies the baked
asset link, commits the target marker and restores prior maintenance/scheduling
settings. Runtime depends on successful completion. Pending migration state
blocks runtime during the handoff between source and target jobs.

Require patch-backup exit 0 with `BACKUP COMPLETE` and initializer exit 0 with
`PATCH LIFECYCLE COMPLETE`. Retain the printed recovery directory. All nine
persistent services should become healthy. Re-run the version lookup from step 2
(refresh `backend` first); it must now report **16.51.1**.

Verify login with the same new patch-test credentials, the test record and
attachments, normal page assets, and paused scheduling. Any unexpected failure
is a stop condition: preserve logs, state and backup. Do not retry an interrupted
migration blindly or put the older initialization YAML onto this migrated site.

## 4. Verify repeat behavior

Save unchanged upgrade YAML, stop/start the patch app and restart the disposable
VM. Verify version 16.51.1, data and health again. When one-shot services rerun,
patch-backup should report `BACKUP ALREADY COMPLETE` and initializer should report
`MIGRATION ALREADY COMPLETE` plus `PATCH LIFECYCLE COMPLETE`. The completed
operation must be reused. Keep **02-upgrade.yaml** as this app's baseline.

## 5. Initialize a separate OLD-version recovery destination

This recovers the pre-patch backup using v16.51.0 in separate storage. It does
not change the upgraded source. Create fresh directories in the host shell:

```bash
sudo test ! -e /mnt/labpool/erpnext-catalog-patch-recovery-test && \
sudo mkdir -p /mnt/labpool/erpnext-catalog-patch-recovery-test/sites \
  /mnt/labpool/erpnext-catalog-patch-recovery-test/logs \
  /mnt/labpool/erpnext-catalog-patch-recovery-test/db_data \
  /mnt/labpool/erpnext-catalog-patch-recovery-test/queue_data
```

Stop if this path already exists. Install NEW
**erpnext-catalog-patch-recovery-test** (35 characters) using
`generated/catalog-patch-recovery-01/01-initialize-clone.yaml`. Its port is
**18089**. Wait for successful initialization and healthy services.

## 6. Restore and verify the source-version backup

Stop only the new recovery app. Apply `02-restore-clone.yaml` from that same
recovery directory and start it. Require restore-job exit 0 and `RESTORE COMPLETE`.
The source backup is mounted read-only. Its patch manifest must match the reviewed
pair, and restore must use the SOURCE image; using the target image is refused.

Stop the recovery app again, apply `03-start-restored-clone.yaml`, and start it.
Require nine healthy persistent services. Visit http://172.22.237.80:18089 and
log in with the NEW patch-test source credentials from step 2, not the temporary
recovery initialization password. Verify backup-era records and attachments,
paused scheduling, stop/start and unchanged-YAML persistence. A recovery-only
record must be absent in the upgraded source on 18088.

The recovery backend must report **16.51.0**, using the step-2 lookup with project
`ix-erpnext-catalog-patch-recovery-test`. The source on 18088 must remain 16.51.1.
The recovery baseline is `generated/catalog-patch-recovery-01/03-start-restored-clone.yaml`.

Report steps 1-6. Local testing also uses a synthetic encrypted-secret fixture;
its successful decryption is not a claim that all real integration credentials
or encrypted fields have been tested in your VM. No automatic rollback, arbitrary
DDL-failure recovery, queue draining or native catalog upgrade is implied.
