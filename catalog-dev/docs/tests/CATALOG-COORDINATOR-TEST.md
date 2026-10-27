# One-deployment same-image lifecycle

This replaces the manual backup/migrate/resume stages with one coordinated
initializer deployment. Use the working **erpnext-catalog-interrupt-recovery-test**
app on **18087**. No new app or storage directories are needed. Leave the failed
18086 app's state and backup intact; Created/Exited containers mean they are not
running even if TrueNAS still displays Crashed.

This is an integration test of the Compose service graph on the custom test app.
It is not a native catalog upgrade or ERPNext version change. The default catalog
still refuses image changes. Queue draining and real patch upgrades remain work.

## 1. Preserve the baseline

Take a fresh VM snapshot and privately retain
`generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml`.
Record a known record/attachment on 18087. Keep scheduling paused.
The prepared update preserves the exact ERPNext/dependency images, credentials,
storage paths, port and network from this successful baseline.

## 2. Apply the single update

Stop the app on 18087 and wait for its runtime containers to stop.
Replace its complete YAML with **generated/catalog-coordinator-01.yaml** and
start it. Do not apply it to another app or to the failed source on 18086.

The initializer now holds one exclusive runtime lock through verified backup,
same-image migration and guarded initialization/resume. Runtime services depend
on successful completion. Existing runtime holding the shared lock prevents
the coordinator from changing state; it cannot force that runtime to stop.

## 3. Verify the coordinated run

Require initializer exit 0 and these messages in its logs:

- `BACKUP COMPLETE` (retain the printed new recovery directory).
- `MIGRATION COMPLETE`.
- `COORDINATED LIFECYCLE COMPLETE`.

All nine persistent services should become healthy. Open
http://172.22.237.80:18087 with the restored credentials and verify the known
records/attachments. Scheduling should remain paused; the coordinator preserves
the site's previous maintenance and scheduling settings.

Unexpected backup/migration/resume errors are a stop condition. Keep logs and
recovery files. Do not clear state or switch back to old YAML to bypass guards.
An interrupted migration must continue to block automatic retry and startup.

## 4. Verify repetition is safe

Save unchanged YAML and check that data/health remain correct. Stop/start the
app and restart the disposable VM, checking it again afterward. When the
initializer reruns for the same operation, it should report `BACKUP ALREADY
COMPLETE`, `MIGRATION ALREADY COMPLETE` and `COORDINATED LIFECYCLE COMPLETE`;
it must not create another backup operation or rerun migration. If an unchanged
save does not rerun the initializer, inspect this on the next stop/start instead.

The failed 18086 app must remain blocked with no running containers; its Crashed
label alone is expected and is not a request to clear its guards. Other apps
may stay stopped throughout this test.

After success, **generated/catalog-coordinator-01.yaml** becomes the current
18087 baseline. Preserve it unchanged for subsequent saves/restarts and report
checks 1-4. No native catalog update or versioned patch result is implied.

## Preparing another plan

Only when preparing a new operation, choose a fresh output filename:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_coordinator.py --installed-yaml catalog-dev/generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml --output catalog-dev/generated/catalog-coordinator-01.yaml
```

The generator refuses overwrite and limits this test to the named recovery
clone's network. Private YAML and recovery backups contain secrets; keep them
outside Git. Generating a new plan intentionally creates a new operation ID.
