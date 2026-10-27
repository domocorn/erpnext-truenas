# Recover the digest-pinning backup into a new test app

The user reported all VM pinning checks passed and the inspected backend image
matches the expected pinned reference and unchanged image config ID. Keep the
existing apps intact: catalog-test on 18084 and restore-test on 18085.

This procedure creates **erpnext-catalog-pinned-recovery-test** on **18086**.
It restores the pre-pinning backup from the restore-test app into separate
storage, using the exact same digest-pinned ERPNext content. It does not exercise
a different ERPNext version or an actual mid-patch failure.

Keep a VM snapshot and the existing recovery directories. The backup represents
the point at pinning stage 1: edits made afterward are not part of that backup.
Generated files and backups contain secrets and must stay outside Git.

## 1. Create new storage

In the disposable VM host shell:

```bash
sudo test ! -e /mnt/labpool/erpnext-catalog-pinned-recovery-test && \
sudo mkdir -p /mnt/labpool/erpnext-catalog-pinned-recovery-test/sites \
  /mnt/labpool/erpnext-catalog-pinned-recovery-test/logs \
  /mnt/labpool/erpnext-catalog-pinned-recovery-test/db_data \
  /mnt/labpool/erpnext-catalog-pinned-recovery-test/queue_data
```

If the path already exists, stop; do not erase it. Use a fresh plan/destination.

## 2. Initialize the new app

Install a NEW custom YAML app named exactly
`erpnext-catalog-pinned-recovery-test`, using the complete private file
`generated/catalog-pinned-recovery-01/01-initialize-clone.yaml`.
Wait for initialization to finish and all nine persistent services to become
healthy. Bootstrap and initializer should exit 0. This initial database is empty
of source business records. Temporary destination credentials are in this YAML.

## 3. Restore the backup

Stop only the new pinned-recovery app and wait for its runtime services to stop.
Replace its YAML with `02-restore-clone.yaml` from the same generated directory
and start it. Only permissions, database, Redis and restore-job should exist.
Require restore-job exit 0 and `RESTORE COMPLETE` in its logs.

The source backup is mounted read-only. The job checks its operation, same-content
pinning identity, file sizes and SHA-256 hashes before database changes. An
unexpected failure is a stop condition: preserve logs and report it. Do not
retry an interrupted restore blindly, remove guards, use --force or reuse the
destination with another backup.

## 4. Start and verify recovery

Stop the new app again, apply `03-start-restored-clone.yaml`, then start it.
Require nine healthy persistent services and successful one-shot exits.
Visit http://172.22.237.80:18086 and log in with the original catalog-test
credentials as they were at backup time. The restore replaces the temporary
destination login credentials.

Verify records and attachments that existed at pinning stage 1, including any
restore-clone-only test record already present then. Newer source edits should
not appear. Create a new recovery-only record and confirm it is absent on 18085
and 18084. Scheduling must stay paused. Stop/start the recovery app and save its
unchanged YAML; data and health should survive. A disposable VM restart should
also preserve all three apps and their independent data.

Retain these current baselines separately:

- Original catalog-test: `generated/catalog-rehearsal-01/05-resume.yaml`.
- Pinned restore-test: `generated/catalog-pinning-01/05-resume.yaml`.
- New recovery-test: `generated/catalog-pinned-recovery-01/03-start-restored-clone.yaml`.

Report checks 1-4 and any unexpected logs. Restoring encrypted fields needs an
explicit decryption fixture; transferring the encryption key alone does not
prove it. Native catalog upgrades and actual patch-failure recovery remain work.

## Preparing another plan

Run from erpnext-truenas with a fresh destination and output directory:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_restore.py --source-config catalog-dev/generated/catalog-pinning-01/05-resume.yaml --apps-root ..\apps --lab-root /mnt/labpool/erpnext-catalog-pinned-recovery-test --port 18086 --app-name erpnext-catalog-pinned-recovery-test --output-dir catalog-dev/generated/catalog-pinned-recovery-01
```
