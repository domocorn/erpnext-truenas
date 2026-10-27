# Same-content digest pinning: restored test clone only

This test changes the image reference, retaining exactly ERPNext v16.51.1's
observed content. It does not test a newer ERPNext release or native catalog
updates. Use only the existing **erpnext-catalog-restore-test** app on the
disposable VM, port 18085. Leave the original catalog-test app on 18084 intact.

The running clone reported:

```text
frappe/erpnext:v16.51.1
image config ID: sha256:0ce48f9b465e15869540282c8f203bdbe24b2ae9fe5419c2f32c7e462fba5591
repository digest: sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268
```

The repository digest is an OCI multi-platform index; its amd64 manifest points
to the reported config ID. These two digest types need not be identical.

## Before starting

Take a fresh VM snapshot. Preserve the successful clone YAML
`generated/catalog-restore-01/03-start-restored-clone.yaml` privately.
Record a clone-only test record and attachment you can check afterward.
Keep scheduling paused. Recovery files and generated YAML contain secrets;
keep them outside Git. RECOVERY-COPY.md covers an additional off-VM copy.

Use the five files in `generated/catalog-pinning-01/`, in order. Before EVERY
stage, stop the restore-test app and wait for its containers to stop, then edit
its YAML using the complete next file and start it. Do not combine stages or
apply them to the source app. One-shot containers exiting 0 are expected.

## 1. Backup

Apply `01-backup.yaml`. Only permissions, database, Redis and rehearsal-job
should run. Require rehearsal-job exit 0 and `BACKUP COMPLETE` in its logs.
Keep the printed `.catalog-recovery/<operation>` directory. This is a new
backup in the clone's sites directory, separate from the original source backup.

## 2. Intentional migration failure

Apply `02-simulated-failure.yaml`. The job must exit nonzero with
`EXPECTED TEST FAILURE before migration; resume must remain blocked`.
This failure is the expected result of this stage.

## 3. Verify startup is blocked

Apply `03-verify-startup-blocked.yaml`. Bootstrap must fail with
`Successful matching migration required; resume blocked`.
Runtime services must not start successfully; the portal should be unavailable.
This stage must not change the stored image marker. Do not remove any guards.

## 4. Migrate

Apply `04-migrate.yaml`. Require rehearsal-job exit 0 and `MIGRATION COMPLETE`.
An unexpected failure or interrupted migration is a stop condition: preserve
logs and recovery files and report it. Do not retry blindly or use older YAML
to bypass the state. Snapshot recovery is manual; automatic rollback is absent.

## 5. Resume with pinned image

Apply `05-resume.yaml`. Bootstrap should print
`Verified same-content image identity pinned.` The initializer must exit 0 and
all nine persistent services should become healthy.

Check login at http://172.22.237.80:18085 using the restored source credentials,
the clone-only record and attachment, and paused scheduling. Confirm the original
app on 18084 still works independently. Stop/start the clone, save its unchanged
YAML, and restart the disposable VM; verify health and data after each.

Run this read-only check in the VM host shell:

```bash
backend=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-catalog-restore-test --filter label=com.docker.compose.service=backend)
# Stop if the lookup is empty or has more than one ID.
sudo docker inspect --format '{{.Config.Image}} {{.Image}}' "$backend"
```

The configured reference must end in
`v16.51.1@sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268`.
The image config ID should remain the observed `sha256:0ce48f9b...` above.

After success, `generated/catalog-pinning-01/05-resume.yaml` becomes the clone's
baseline. Keep using it for unchanged edits and restarts. The original app's
baseline remains `generated/catalog-rehearsal-01/05-resume.yaml`.

After pinning passes, use CATALOG-PINNED-RECOVERY-TEST.md to test restoring this
backup into another independent app. The restore helper accepts only verified
same-content pinning backups, in addition to earlier same-image rehearsal
backups. The earlier source backup and pre-test snapshot remain recovery
options. Real patch upgrades, encrypted-field decryption checks and native
lifecycle integration remain work.

## Regeneration (only when explicitly preparing a new plan)

From erpnext-truenas, choose a fresh output directory; never overwrite a plan:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_pinning.py --installed-yaml catalog-dev/generated/catalog-restore-01/03-start-restored-clone.yaml --source-digest sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268 --observed-image-id sha256:0ce48f9b465e15869540282c8f203bdbe24b2ae9fe5419c2f32c7e462fba5591 --output-dir catalog-dev/generated/catalog-pinning-01
```
