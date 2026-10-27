# Native catalog install and upgrade — disposable VM only

This is one test group: native installation, the reviewed patch upgrade, and an
unchanged restart. It uses TrueNAS's catalog form and Upgrade action, rather than
another Custom App YAML. No submission to TrueNAS has been made.

Use only the disposable **172.22.237.80 / TrueNAS-25.10.7** VM. Leave the previous
test apps and their data unchanged. Take a VM snapshot before staging. The bundle
is an unpublished lab candidate; the app's final icon/metadata are still pending.
Do not refresh/sync the catalog during this test: a sync can replace the temporary
entry. The script refuses to overwrite externally changed entries or app files.

## 1. Transfer the prepared bundle

The generated archive contains app code and metadata, not your ERPNext passwords
or database contents. In Windows PowerShell, from the GitHub workspace:

```powershell
Get-FileHash .\erpnext-truenas\catalog-dev\generated\erpnext-native-lab-01.tar.gz -Algorithm SHA256
scp .\erpnext-truenas\catalog-dev\generated\erpnext-native-lab-01.tar.gz truenas_admin@172.22.237.80:/tmp/
```

Enter your SSH password only in your terminal. If SSH still reports
`Permission denied (publickey)`, stop here and report that; the package is not at
fault. See RECOVERY-COPY.md for the existing SSH setup notes.

In the TrueNAS **host shell**, run individually and stop on any error:

```bash
sha256sum /tmp/erpnext-native-lab-01.tar.gz
mkdir -m 700 /tmp/erpnext-native-lab-transfer-01
tar --no-same-owner -xzf /tmp/erpnext-native-lab-01.tar.gz -C /tmp/erpnext-native-lab-transfer-01
sudo python3 /tmp/erpnext-native-lab-transfer-01/erpnext-native-lab-01/native_catalog_lab.py source --disposable-vm
```

Require the SHA256 to match Windows before extracting. The expected staging
output is `STAGED: source 0.9.0`. The tool backs up the original catalog index
under `/root/erpnext-native-catalog-lab`, adds only `community/erpnext-native-lab`,
and refreshes the middleware cache. It never invokes catalog sync.

## 2. Install using the native catalog form

Refresh the Apps page, open **Discover Apps**, and search for **ERPNext Native Lab**.
Install with:

- Application name: **erpnext-native-test** (under the 40-character limit).
- Site Name: `erpnext.localhost`.
- New Administrator and database passwords of at least 12 characters; save them
  privately. Do not reuse a production password or send it in chat.
- WebUI Port: **18090**.
- Keep all four storage entries on their default **ixVolume** settings. TrueNAS
  creates dedicated datasets for this new app; do not point it at previous labs.

Require the app to be Running and ERPNext **16.51.0** at
`http://172.22.237.80:18090`. Sign in as Administrator. Create a ToDo called
`Native catalog upgrade fixture` and attach a small test text file; retain the
original file for comparison after upgrading.

Pause this test site's scheduler before upgrading. In the VM host shell, run this
complete block (variable assignment normally prints nothing):

```bash
backend=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-native-test --filter label=com.docker.compose.service=backend)
if [ -n "$backend" ] && [ "$(printf '%s\n' "$backend" | wc -l)" -eq 1 ]; then
  sudo docker exec "$backend" bench --site erpnext.localhost set-config pause_scheduler 1
else
  echo 'STOP: expected exactly one running native-test backend'
fi
```

If it prints STOP or a command fails, do not proceed. The upgrade's read-only
queue gate refuses pending or failed jobs; it does not erase them.

## 3. Publish the target locally and use Upgrade

Keep the source app **Running**. In the VM host shell:

```bash
sudo python3 /tmp/erpnext-native-lab-transfer-01/erpnext-native-lab-01/native_catalog_lab.py target --disposable-vm
sudo python3 /tmp/erpnext-native-lab-transfer-01/erpnext-native-lab-01/native_catalog_lab.py status --disposable-vm
```

Require `STAGED: target 1.0.0` and status showing `custom_app: false`, version
`0.9.0`, and `upgrade_available: true`. Refresh Apps if needed, then choose
**Upgrade** for **erpnext-native-test** to catalog version **1.0.0**. Leave the
snapshot option enabled. Do not choose Roll Back if this fails: preserve the
state and report the failing service's logs instead.

TrueNAS stops the old app before native upgrade. The new graph then runs the
16.51.0 backup container before the 16.51.1 migration/initializer and runtime.
This ordering was checked against the versioned middleware implementation:
https://github.com/truenas/middleware/blob/TS-25.10.7/src/middlewared/middlewared/plugins/apps/upgrade.py

## 4. Verify upgrade and unchanged restart

Require Running, catalog version **1.0.0**, ERPNext **16.51.1**, successful login,
the same ToDo, and a downloaded attachment with unchanged contents. In Workloads,
require the four one-shots to exit successfully and the nine persistent
containers to be healthy. The upgrade-backup log should report `BACKUP COMPLETE`,
and initializer should report `NATIVE PATCH COMPLETE`.

Stop and start **only erpnext-native-test**, then repeat login/data checks. This
must reuse the completed migration rather than create another backup/migration.
Expected initializer output includes `MIGRATION ALREADY COMPLETE`.

Run the status command above again and report its short output, whether the
record/attachment survived, and whether stop/start passed. Do not send passwords,
full app configuration or recovery contents. Keep the app and its backups for
the next failure/recovery test group; do not remove the overlay yet.

## Removing the temporary catalog overlay later

Only after testing is finished or to abandon an incomplete staging attempt:

```bash
sudo python3 /tmp/erpnext-native-lab-transfer-01/erpnext-native-lab-01/native_catalog_lab.py remove --disposable-vm
```

This removes only the owned lab catalog entry, preserves unrelated index changes,
and moves the lab catalog app files to a hidden archive beside their original
directory. It preserves the installed app, its datasets and the original-index
backup. The installed app cannot receive native lab updates while its catalog
entry is absent. Staging is deliberately a single run; preserve the evidence and
use a fresh VM snapshot for a new run.
