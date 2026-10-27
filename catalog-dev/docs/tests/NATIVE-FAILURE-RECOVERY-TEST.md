# Native failure and independent recovery test

This is the remaining lifecycle test group before final catalog integration and
acceptance checks. Use only the disposable VM at 172.22.237.80 / TrueNAS-25.10.7.
Leave the successful **erpnext-native-test on 18090** and all previous lab data
unchanged. Removing its earlier temporary catalog overlay was fine; this group
uses different app names, staging records, ports and dedicated ixVolume datasets.

## 1. Transfer and stage the failure candidate

Take a VM snapshot. In PowerShell at
`D:\Users\Dominic\Documents\_04 Tech & Coding\GitHub`:

```powershell
Get-FileHash .\erpnext-truenas\catalog-dev\generated\erpnext-native-failure-recovery-01.tar.gz -Algorithm SHA256
scp .\erpnext-truenas\catalog-dev\generated\erpnext-native-failure-recovery-01.tar.gz truenas_admin@172.22.237.80:/tmp/
```

In the VM host shell, run individually; stop on any unexpected failure:

```bash
sha256sum /tmp/erpnext-native-failure-recovery-01.tar.gz
mkdir -m 700 /tmp/erpnext-native-failure-transfer-01
tar --no-same-owner -xzf /tmp/erpnext-native-failure-recovery-01.tar.gz -C /tmp/erpnext-native-failure-transfer-01
sudo python3 /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01/failure/native_catalog_lab.py source --disposable-vm
```

Require matching Windows/VM hashes before extracting and `STAGED: source 0.9.0`.
Do not Sync/Refresh Catalog during the group; ordinary browser refresh is fine.

Discover Apps -> **ERPNext Native Failure Lab** -> Install:

- App name: **erpnext-native-failure-test**.
- Site: `erpnext.localhost`; new private Administrator/database passwords of at
  least 12 characters. Keep the Administrator password for recovery login.
- WebUI port: **18091**.
- Keep all four default **ixVolume** storage entries. Do not select earlier data.

Wait for Running / ERPNext 16.51.0. The following helper creates a fictional ToDo,
private attachment and synthetic encrypted value, then pauses the scheduler:

```bash
sudo python3 /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01/native_failure_lab.py fixture --disposable-vm
```

Require `SOURCE FIXTURE CREATED` and `SOURCE SCHEDULER PAUSED`. Do not rerun this
command to create duplicates. The fixture does not send messages or use a real
integration credential.

## 2. Exercise the deliberate native upgrade failure

Keep the source app Running and stage its target:

```bash
sudo python3 /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01/failure/native_catalog_lab.py target --disposable-vm
```

Refresh Apps and Upgrade **erpnext-native-failure-test** to catalog version 1.0.0.
Keep the snapshot option enabled. This upgrade is SUPPOSED TO FAIL: after the
old-image backup, a test-only before_migrate hook commits a fictional record and
raises an error. The initializer log should include `NATIVE FAILURE HOOK ENTERED`.
Do not choose Roll Back, clear guards, edit state files or apply older YAML.

Check the actual persisted failure and checksum-valid pre-upgrade backup:

```bash
sudo python3 /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01/native_failure_lab.py verify-failed --disposable-vm
```

Require `FAILED NATIVE UPGRADE VERIFIED`. The site's status must remain migrating,
the stored image identity must remain 16.51.0 and none of its six ERPNext runtime
services may be running. Database/Redis services may remain running; the Crashed
UI state is expected.

Stop and start **only erpnext-native-failure-test** once through TrueNAS. Startup
must fail closed again. Run the same verify-failed command again and require the
same successful verification. Leave this failed source and its backup intact.

## 3. Recover automatically into a separate native app

Run:

```bash
sudo python3 /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01/native_failure_lab.py recover --disposable-vm
```

The helper verifies the failed source, stages the separate recovery catalog entry,
and calls native app.create for **erpnext-native-recovery-test on 18092**. It uses
new database credentials and new ixVolumes. TrueNAS forbids host-path mounts from
the internal `.ix-apps` directory, so the helper first copies the checksum-verified
backup into the private `/mnt/labpool/erpnext-native-recovery-input-01` directory.
It verifies the copy again, gives the container read-only access and leaves the
original backup unchanged. The disposable `labpool` must be online. Only this
verified copy is mounted read-only. It restores with the exact original 16.51.0 image, copies the
source encryption key, migrates at that source version and leaves scheduling
paused. It never clears the failed source's guards or changes its database.

Require `NATIVE RECOVERY CREATE JOB: <number>`, then wait for the recovery app to
be Running. The recovery initializer should report `NATIVE RECOVERY COMPLETE`.
A recovery failure must stay blocked; do not retry it by editing state.

If an earlier attempt staged the recovery catalog but never created the app,
the updated helper verifies that the existing staged entry/files match its saved
manifest and reuses that entry. It still refuses an existing recovery app or
changed/incomplete staging. The original helper stopped with `Source was already
staged`; update only native_failure_lab.py before retrying in that case.
If a catalog sync removed the temporary entry and app directory while retaining
the staging journal, the updated helper verifies journal/bundle ownership and
reinstates only the missing recovery overlay. It saves the current index before
restaging, preserves unrelated entries and refuses foreign entries, changed files
or concurrent index changes. No failed-source guards or data are reset.

## 4. Verify data and unchanged recovery restart

```bash
sudo python3 /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01/native_failure_lab.py verify-recovered --disposable-vm
```

Require `RECOVERY DATA VERIFIED` and `NATIVE RECOVERY VERIFIED`. These verify the
original ToDo, exact private attachment content, synthetic encrypted-value
decryption, absence of the failed-migration record, independent storage/database
credentials, paused scheduling and preservation of the failed source.

Sign in at `http://172.22.237.80:18092` with Administrator and the password you
chose for the FAILURE source app (the restored database carries that password).
Require ERPNext 16.51.0. Stop/start only the recovery app and rerun
verify-recovered. Initializer should report `NATIVE RESTORE ALREADY COMPLETE`.

Report whether steps 1-4 passed and the final helper output. Do not paste passwords,
full app configuration or backup contents. Preserve both apps and the backup;
leave these temporary overlays in place until final packaging instructions.
