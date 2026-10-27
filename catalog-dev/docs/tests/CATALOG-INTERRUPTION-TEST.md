# Interrupted migration and recovery: disposable VM only

This intentionally interrupts the **erpnext-catalog-pinned-recovery-test** app
on port **18086**, leaving it stopped and guarded afterward. The original apps
on 18084 and 18085 stay unchanged. Recovery goes to a NEW app on **18087**.
Take a fresh VM snapshot first and preserve existing recovery directories.

The test injects an ephemeral hook into the migration job container's ERPNext
files. During real `bench migrate`, the hook commits a clearly named ToDo and
waits. You then kill only that job container. The image and persistent app code
are unchanged. This tests a committed partial change and abrupt migration
interruption using the same ERPNext version, not every possible versioned patch
failure. No automatic rollback or in-place repair is provided.

Use the exact private files already prepared. Never use this on production or
the original source app. If any unexpected result occurs, stop and preserve logs;
do not remove markers, change database state or retry blindly.

## 1. Back up the disposable recovery app

Record a known record and attachment currently present on 18086. Its current
baseline should be `generated/catalog-pinned-recovery-01/03-start-restored-clone.yaml`.
Stop this app and wait for all runtime containers to stop. Apply the complete
`generated/catalog-interruption-01/01-backup.yaml` and start it.
Require rehearsal-job exit 0 with `BACKUP COMPLETE`. Retain the printed recovery
directory. Only database, Redis, permissions and rehearsal-job should exist.

## 2. Interrupt a real migration

Stop the same app, apply `02-interrupt-migration.yaml` and start it.
The migration job deliberately stays running after the test hook commits.
In the VM HOST shell, obtain exactly one job ID:

```bash
job=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-catalog-pinned-recovery-test --filter label=com.docker.compose.service=rehearsal-job)
printf '%s\n' "$job"
```

If this is empty or more than one line, STOP. Do not use another container ID.
Check the hook marker with this read-only command:

```bash
sudo docker exec "$job" /home/frappe/frappe-bench/env/bin/python -c 'import json,os; from pathlib import Path; r=Path("/home/frappe/frappe-bench/sites"); o=os.environ["OPERATION_ID"]; s=json.loads((r/os.environ["SITE_NAME"]/".nas-upgrade-state.json").read_text()); assert s["status"]=="migrating" and s["operation"]==o; assert (r/(".catalog-interrupt-entered-"+o)).is_file(); print("Hook committed; this test job is ready to interrupt.")'
```

If the marker is not present yet, wait briefly and repeat the read-only check.
If the job exited or logged another error, stop. Once the check succeeds:

```bash
sudo docker kill --signal KILL "$job"
sudo docker inspect --format '{{.State.ExitCode}}' "$job"
```

The exit code must be **137**. This is the expected deliberate failure.

## 3. Confirm retry is blocked

Stop the same app, apply `04-blocked-retry.yaml`, and start it.
Require a nonzero job exit with:
`Interrupted migration; restore recovery required before retry`.
The job must not run migration again.

## 4. Confirm normal startup is blocked

Stop the same app, apply `03-blocked-resume.yaml`, and start it.
Require initializer failure with:
`Successful matching migration required; resume blocked`.
The portal on 18086 must remain unavailable. Stop the app and retain this YAML
and the failed state for inspection. Do not switch to the older successful YAML
or delete `.nas-upgrade-state.json`. That would bypass recovery safeguards.

## 5. Initialize a new recovery destination

In the disposable VM host shell:

```bash
sudo test ! -e /mnt/labpool/erpnext-catalog-interruption-recovery-test && \
sudo mkdir -p /mnt/labpool/erpnext-catalog-interruption-recovery-test/sites \
  /mnt/labpool/erpnext-catalog-interruption-recovery-test/logs \
  /mnt/labpool/erpnext-catalog-interruption-recovery-test/db_data \
  /mnt/labpool/erpnext-catalog-interruption-recovery-test/queue_data
```

If the destination exists, stop; never erase it to fit this plan.
Install a NEW app named **erpnext-catalog-interrupt-recovery-test** (39 characters), using
`generated/catalog-interruption-recovery-01/01-initialize-clone.yaml`.
Wait for successful initialization and nine healthy persistent services.
The storage directory above retains its longer name; the app-name limit does
not require renaming those directories. The prepared YAML keeps those paths.

## 6. Restore the pre-migration backup

Stop only the NEW app. Apply `02-restore-clone.yaml` from the same recovery
directory and start it. Require restore-job exit 0 and `RESTORE COMPLETE`.
The backup from step 1 is mounted read-only; the interrupted source is unchanged.
Stop on any unexpected failure; do not retry an interrupted restore blindly.

## 7. Verify the recovered app

Stop the new app, apply `03-start-restored-clone.yaml`, and start it.
Require nine healthy persistent services and successful one-shot exits.
Open http://172.22.237.80:18087 with the original catalog-test credentials as
they were at backup time. Verify the step-1 records and attachments are present.
The ToDo whose description starts `Catalog interrupted migration fixture ` must
be ABSENT. Scheduling must remain paused. A new recovery-only record must be
absent on 18084/18085. Check new-app stop/start and unchanged YAML save retain
data and health. After a VM restart the recovered app should remain usable.
The interrupted 18086 app must not become usable; if TrueNAS attempts to start
it, the saved migration state must still block runtime. Leave it stopped.

The new working baseline is
`generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml`.
Keep the interrupted app, state and backup for diagnostics. Original 18084 and
18085 baselines remain unchanged. Report steps 1-7 and any unexpected output.

This establishes recovery into separate storage, not automatic rollback or
recovery of external side effects. Encrypted-field decryption, queue draining,
real versioned patches and native catalog updates still need separate work.
