# First backup/restore acceptance test

Use only the disposable TrueNAS VM. This runbook restores the named test backup
into a separately initialized app. It does not operate on the production NAS.
Commands in the host section require access to Docker; use the TrueNAS Shell.

## 1. Create the destination from Windows

In PowerShell in the repository:

```powershell
.\.venv\Scripts\python.exe scripts/build.py --site erpnext.test --port 18082 --output generated/erpnext-restore-test.yaml
```

Choose an initial destination password. In the VM, install this generated YAML
as **erpnext-restore-test**, a NEW app. Do not edit the existing erpnext-test app.
Wait for initialization to succeed. Verify `http://VM-IP:18082` opens and the
source customer's records are absent. No need to complete the setup wizard.
The same internal site name is intentional; Docker volumes and networks are
isolated by the distinct app names. Retain the destination generated YAML.

## 2. Identify containers in the TrueNAS VM host shell

These commands run in **TrueNAS System Shell**, not a container shell.
If either result is empty or has more than one ID, stop and inspect `sudo docker ps`.
The label values assume the exact app names above.

```bash
SOURCE_BACKEND=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-test --filter label=com.docker.compose.service=backend)
DEST_BACKEND=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-restore-test --filter label=com.docker.compose.service=backend)
printf 'Source backend: %s\nDestination backend: %s\n' "$SOURCE_BACKEND" "$DEST_BACKEND"
```

Do not continue unless these are two different, single IDs.

## 3. Transfer the four existing backup files

Still in the VM host shell, use a private staging directory. The original backup
is a point-in-time snapshot from 2026-10-18; newer edits will not be included.
A 10 KB tar can contain a very small file or be empty; size alone does not prove
an attachment was captured. Verify your known attachment after restoration.

```bash
RESTORE_STAGE=$(mktemp -d /tmp/erpnext-restore.XXXXXXXX)
BACKUP_PREFIX=20261018_175820-erpnext_test
for SUFFIX in database.sql.gz files.tar private-files.tar site_config_backup.json; do
  sudo docker cp "${SOURCE_BACKEND}:/home/frappe/frappe-bench/sites/erpnext.test/private/backups/${BACKUP_PREFIX}-${SUFFIX}" "$RESTORE_STAGE/" || break
done
sudo ls -lh "$RESTORE_STAGE"
```

Check that all FOUR exact files are present. Then:

```bash
sudo docker exec "$DEST_BACKEND" mkdir -p /home/frappe/frappe-bench/sites/restore-input
sudo docker cp "$RESTORE_STAGE/." "${DEST_BACKEND}:/home/frappe/frappe-bench/sites/restore-input/"
sudo docker exec --user root "$DEST_BACKEND" chown -R frappe /home/frappe/frappe-bench/sites/restore-input
```

No public/private backup URL, share, or Git commit is needed. The staging folder
contains sensitive backups; keep it private.

## 4. Quiesce only the destination

In the VM host shell:

```bash
sudo docker exec "$DEST_BACKEND" bench --site erpnext.test set-maintenance-mode on
sudo docker exec "$DEST_BACKEND" bench --site erpnext.test disable-scheduler
for SERVICE in frontend websocket queue-short queue-long scheduler; do
  CONTAINER=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-restore-test --filter "label=com.docker.compose.service=$SERVICE")
  if [ -n "$CONTAINER" ]; then sudo docker stop "$CONTAINER"; fi
done
```

Check that the five destination runtime services stopped. Leave destination
backend, MariaDB and Redis running. Never stop source services with these commands.
Do not save/redeploy the destination app during restoration.

## 5. Restore in the DESTINATION backend shell

Open the shell for **erpnext-restore-test → backend** in TrueNAS.
This replaces the destination test database. It does not merge records.

```bash
cd /home/frappe/frappe-bench
bench --site erpnext.test restore \
  /home/frappe/frappe-bench/sites/restore-input/20261018_175820-erpnext_test-database.sql.gz \
  --db-root-username root \
  --with-public-files /home/frappe/frappe-bench/sites/restore-input/20261018_175820-erpnext_test-files.tar \
  --with-private-files /home/frappe/frappe-bench/sites/restore-input/20261018_175820-erpnext_test-private-files.tar
```

If asked for the database root password, use the **destination** generated YAML's
`db.environment.MARIADB_ROOT_PASSWORD`. It is not either ERPNext login password.
If restoration fails, stop here and preserve logs. Do not add --force.

After successful restore, copy ONLY the encryption key from the source backup
configuration. Do not overwrite destination db_name/db_password or host settings.
The following runs in the same destination backend shell and prints no secrets:

```bash
./env/bin/python - <<'PY'
import json
from pathlib import Path
source = Path('sites/restore-input/20261018_175820-erpnext_test-site_config_backup.json')
target = Path('sites/erpnext.test/site_config.json')
original = json.loads(source.read_text())
config = json.loads(target.read_text())
key = original.get('encryption_key')
if not key:
    raise SystemExit('Source backup has no encryption key; stop and inspect privately.')
config['encryption_key'] = key
config['maintenance_mode'] = 1
config['pause_scheduler'] = 1
temporary = target.with_name('site_config.restore-tmp')
temporary.write_text(json.dumps(config, indent=2) + '\n')
temporary.chmod(0o600)
temporary.replace(target)
print('Source encryption key installed; destination connection settings preserved.')
PY
bench --site erpnext.test migrate
```

If migration fails, leave the destination stopped and share the final error lines.
After it succeeds:

```bash
bench --site erpnext.test disable-scheduler
bench --site erpnext.test set-maintenance-mode off
```

Keep scheduling disabled on the clone for now. The source database may contain
email integrations or scheduled actions; this test uses fictional data only.

## 6. Bring the destination back and verify

Use TrueNAS to Stop and then Start **erpnext-restore-test**. Initialization should
verify its managed site and skip creation. Open `http://VM-IP:18082` in a private
browser window. Log in using the SOURCE ERPNext Administrator password from the
backup, because the restored database contains the source accounts.

Verify:

- Source test customer and Issue are present.
- The known attachment opens and has the expected contents.
- Public and private attachments are both checked if both existed at backup time.
- A new destination-only test record does not appear in the source app on 18081.
- Destination restart preserves restored records and attachment.

This confirms database/file restoration and isolation. Copying the encryption key
alone is not an end-to-end test of encrypted credentials; add a safe encrypted
field test later before claiming encrypted-setting recovery is validated.

Record PASS/FAIL and details in docs/TEST-RESULTS.md. Do not publish backups, site
config, passwords, or generated YAML. Once verified, remove the temporary host
staging directory and destination sites/restore-input directory using their exact
paths. Retain an independent private copy of the backup if needed.

## References

- https://docs.frappe.io/framework/user/en/bench/reference/restore
- https://docs.frappe.io/framework/user/en/bench/reference/backup
