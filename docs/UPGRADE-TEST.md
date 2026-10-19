# Controlled upgrade rehearsal — TEST VM ONLY

This is a three-stage lab workflow, not one-click catalog upgrading. Current
verified latest ERPNext release equals the installed v16.51.1, so rehearse on that
same version first. A successful rehearsal does not establish a real version
transition. Use only **erpnext-restore-test**, port 18082.

## Before starting

- Confirm your restored records and attachment work, and take a VM snapshot.
- Keep the exact private YAML currently installed in erpnext-restore-test.
  It should be generated/erpnext-restore-test.yaml from the restore test.
- Do NOT rerun build.py: that would generate a different database password.
- Changes made after the snapshot may be lost if you revert it.
- Do not use the live NAS, source test app, or business data for this prototype.

## 1. Generate the four configurations on Windows

Copy the update's source files into your repository. In its PowerShell window:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/prepare_upgrade.py --from-config generated/erpnext-restore-test.yaml --target v16.51.1 --rehearsal
```

Output: generated/upgrade/01-backup.yaml, 02-migrate.yaml,
02-test-failure.yaml, 03-resume.yaml. All contain PRIVATE configuration. Never
commit or share them. The generator retains credentials, volumes and ports from
the supplied configuration. It will not overwrite an existing operation folder.
Do not regenerate a different operation halfway through this test.

## 2. Fully stop the destination app

In TrueNAS stop **erpnext-restore-test**. In the **TrueNAS host shell**, verify:

```bash
sudo docker ps --filter label=com.docker.compose.project=ix-erpnext-restore-test --format '{{.Names}}'
```

This must produce NO container names. If anything is still running, stop here.
This full stop is required: Compose dependencies alone do not stop old workers.
Confirm source erpnext-test was not stopped.

## 3. Backup stage

Edit the SAME erpnext-restore-test app and replace its entire YAML with
generated/upgrade/01-backup.yaml. Save, and start the app if TrueNAS leaves it
stopped. Do not install as a new app; the same app identity preserves volumes.

In the host shell run the Docker listing above again. Only db, redis-cache,
redis-queue, and optionally upgrade-job may be running for this app. Old backend,
frontend, worker, websocket and scheduler containers must NOT be running. If they
are, stop the app and report this before continuing.

Inspect upgrade-job logs. It must exit 0 and print `BACKUP COMPLETE.` (or
`BACKUP ALREADY COMPLETE` after a repeat deployment). All normal app services are
absent from the maintenance configuration. The web page is unavailable by design.

The recovery directory under sites/erpnext.test/private/nas-upgrades/OPERATION-ID
contains the backup files and site_config.before.json, preserving the original
configuration before maintenance mode. This is in the SAME storage failure domain;
it is a pre-migration recovery copy, not an independent disaster-recovery backup.
Retain the VM snapshot and your previous independent backup too.

If backup fails, DO NOT migrate or restore the old normal YAML to bypass the
guard. Preserve logs and recover from the VM snapshot or discuss the failure.

## 4. Deliberate failure test (before any migration)

Replace the SAME app YAML with 02-test-failure.yaml. Inspect upgrade-job logs.
Expected: nonzero exit and `EXPECTED TEST FAILURE before migration.`

Apply 03-resume.yaml now to test the startup guard. Expected: initializer fails
with `Migration has not succeeded; startup blocked.` Runtime services must not
start and the login page must remain unavailable. An error/degraded app status
is expected at this point.

This deliberate failure happens before database patches. It does not model every
failure during a real patch; actual migration failure retains status `migrating`
and refuses an automatic retry.

## 5. Successful migration rehearsal

Stop the app and verify no containers are running, as in step 2. Replace its YAML
with 02-migrate.yaml and start if needed. Check only maintenance services run.
Wait for upgrade-job to exit 0 and print `MIGRATION COMPLETE.`

If the migration fails, leave the app offline and send the final error lines.
Do not delete state files, change image back, or add force flags. For this lab,
restore the pre-test VM snapshot if we need a clean retry.

## 6. Resume and verify

Replace the SAME app YAML with 03-resume.yaml. The initializer checks that the
matching operation migrated successfully, verifies ERPNext, and restores previous
maintenance and scheduler settings. Configurator and initializer exiting 0 is
normal. Other services should run.

Open http://VM-IP:18082 and check the restored customer, Issue and attachment.
Verify source app on port 18081 is unchanged. Restart the destination and repeat.
The restored clone had its scheduler disabled; it should remain disabled, not
silently begin sending scheduled messages.

Keep 03-resume.yaml as the CURRENT installed configuration. A future operation
must use it as --from-config, not the original pre-rehearsal file.

Record in docs/TEST-RESULTS.md:

| Check | Result |
|---|---|
| Backup job produced four components and preserved config | Pending |
| Maintenance stages had no running normal services | Pending |
| Deliberate failure blocked guarded resume | Pending |
| Same-version migration completed | Pending |
| Resume restored records and attachment | Pending |
| App restart after resume | Pending |
| Disabled scheduler remained disabled | Pending |
| Real version-to-version upgrade | NOT TESTED |
| Recovery from an actual mid-migration failure | NOT TESTED |

## Limits and next milestone

Do not manually start the old normal configuration during this process: its
embedded initializer predates the new guard. Guarded 03-resume.yaml blocks unsafe
startup; it cannot prevent someone deliberately reverting to old unguarded code.
No Docker socket is exposed to the jobs. Stopping services is explicit for now.
Jobs use a filesystem lock and operation state to avoid concurrent/blind retries.

After the rehearsal passes, test a real same-major version increase using a
verified image tag. The tool refuses floating tags, downgrades, major upgrades,
inconsistent source versions, and overwritten operation directories. It does not
independently query the running site or prove an input YAML matches it; supplying
the exact installed YAML and verifying the app identity remain operator duties.

Upstream migration reference:
https://docs.frappe.io/framework/user/en/bench/reference/migrate
