# Restore a catalog backup into an independent test app

This is a NEW disposable app, `erpnext-catalog-restore-test`, on port 18085.
Leave `erpnext-catalog-test` and its successful 05-resume.yaml unchanged.
The source recovery backup is mounted READ ONLY for the restore job. Destination
database, queue, sites and logs use separate storage and a separate network.

Prerequisites: retain the source VM snapshot and confirm the installed source is still the successful
generated/catalog-rehearsal-01/05-resume.yaml. If it changed, prepare from the
exact installed YAML instead. Never use the older standalone RESTORE-TEST.md for
this catalog layout. An off-VM backup copy (RECOVERY-COPY.md) is recommended for
independent preservation; the restore job reads the existing recovery directory
read-only and does not require SSH or the downloaded archive to operate.

## 1. Create fresh destination directories

In the test VM HOST shell, not an app container:

```bash
sudo test ! -e /mnt/labpool/erpnext-catalog-restore-test && \
sudo mkdir -p /mnt/labpool/erpnext-catalog-restore-test/sites \
  /mnt/labpool/erpnext-catalog-restore-test/logs \
  /mnt/labpool/erpnext-catalog-restore-test/db_data \
  /mnt/labpool/erpnext-catalog-restore-test/queue_data
```

If that path already exists, stop and inspect; choose a fresh destination and
regenerate to a new output directory. Do not delete existing data to make it fit.
The source remains /mnt/labpool/erpnext-catalog-test, a different directory.

## 2. Initialize a NEW app

Install NEW `erpnext-catalog-restore-test` using the entire private
generated/catalog-restore-01/01-initialize-clone.yaml. Check the name and port
18085. Allow initialization to finish and services to become healthy.
The generated YAML contains fresh temporary admin and database passwords.
No source records should exist in this initial destination.

## 3. Restore only the destination

Stop the NEW restore app and wait for its runtime services to stop. Replace its
YAML with 02-restore-clone.yaml from the same directory, then start it.
Only permissions, MariaDB, Redis and restore-job should exist. The job verifies
the recovery manifest and file checksums, restores the destination DB and both
file archives, transfers the source encryption key if present, and migrates.
Success is restore-job exit 0 with RESTORE COMPLETE. Scheduling stays paused.

An interrupted restore is blocked from automatic retry and runtime startup.
If it fails, retain logs and stop. Do not use --force, change the source app,
remove guards or reuse the destination against a different backup. Recover the
disposable clone separately; this flow does not repair the source.

## 4. Start the restored destination

Stop the restore app again. Apply 03-start-restored-clone.yaml and start it.
All nine persistent services should become healthy; one-shot services exit 0.
Open http://172.22.237.80:18085 in a private browser window. Use the SOURCE ERPNext
Administrator password as it was when the backup was made. The database restore
replaces the temporary destination login credentials.

Check:

- Customer, Issue and expected attachments from the source backup are present.
- Both public/private attachments open if both existed at backup time.
- A new destination-only record does not appear in the source on port 18084.
- Source edits do not appear in the clone: these are independent databases.
- Clone scheduling is paused. Do not enable it during this test.
- Clone stop/start retains its data and returns healthy; the source is unchanged.

Retain both apps' exact current YAML independently. The clone's current baseline
is 03-start-restored-clone.yaml. Copying the source encryption key is not itself
proof of encrypted-field recovery; that requires an explicit decryption fixture.

## Preparation command (only if a new plan is needed)

From erpnext-truenas, choosing a fresh output directory:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_restore.py --source-config catalog-dev/generated/catalog-rehearsal-01/05-resume.yaml --apps-root ..\apps --lab-root /mnt/labpool/erpnext-catalog-restore-test --port 18085 --output-dir catalog-dev/generated/catalog-restore-01
```

The source recovery directory must exist. The helper refuses overlapping storage,
source-port reuse, image mismatches and output-directory overwrite. No deployment
or source mutation is performed by generation. This tests independent restore
within the lab VM; the off-VM archive additionally protects against losing it.
