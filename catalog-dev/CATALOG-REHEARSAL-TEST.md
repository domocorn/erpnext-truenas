# Catalog same-version backup and migration rehearsal

TEST VM ONLY. Prerequisite: runtime-guard VM tests passed. This deliberately runs
`bench migrate` against the same ERPNext version. No image changes are permitted.
It tests the catalog dataset layout, not native one-click catalog updates.

The five private files are in `catalog-dev/generated/catalog-rehearsal-01/`.
They were prepared from the exact saved `catalog-test.runtime-guards.yaml`.
If you changed the installed YAML, export that exact current configuration and
prepare a different output directory before proceeding. Do not rerun build.py.

## Before starting

- Take a fresh snapshot of the passing VM. Record the existing fictional customer,
  Issue and attachment and whether scheduling is currently paused.
- Keep the exact installed YAML privately. Check the app name is still
  `erpnext-catalog-test`, with its dedicated test directories. This plan preserves
  the configured images, credentials and mounts; mutable image tags are still a
  limitation. Do not update/pull new images as part of this rehearsal.
- Use the SAME app throughout. Before EACH stage, stop it and wait for runtime
  services to stop. Replace its complete YAML, save, and start it if necessary.
  Never create a second app against the same storage, remove guards, delete state
  files or change passwords to work around failure.

## Apply the stages in order

| Stage | Expected result |
| --- | --- |
| `01-backup.yaml` | Only dependencies, permissions and rehearsal-job exist. Job exits 0 with BACKUP COMPLETE. No frontend/workers/scheduler. |
| `02-simulated-failure.yaml` | Job exits nonzero with EXPECTED TEST FAILURE before migration. This is intentional; database migration has not run. |
| `03-verify-startup-blocked.yaml` | Initializer fails because migration has not succeeded. All six runtime services must remain stopped/not started. A deployment failure is expected. |
| `04-migrate.yaml` | Runtime remains absent. Job exits 0 with MIGRATION COMPLETE after same-version migration. Any actual failure here is unexpected; stop and send logs. |
| `05-resume.yaml` | Initializer verifies operation and backup checksums, restores prior flags, then runtime starts. Nine persistent services become healthy; permissions/bootstrap/initializer exit 0. |

After stage 1, preserve a private copy of the recovery directory shown in the job
log before proceeding to stage 4. On the VM host it is under your configured
sites directory: `.catalog-recovery/<operation-ID>/`. It contains the database,
public/private file archives, site/config snapshots, catalog markers and checksum
manifest. Keep encryption keys and credentials private. The copy on the same
dataset is not protection against loss of that dataset. Do not paste these files
into chat or commit them.

Stages 2 and 3 MUST fail as described. If stage 3 starts runtime, stop the app and
report it; do not continue. Portal access is intentionally unavailable in stages
1-4. Do not interpret those deliberate failures as a request to remove guards.

## Verify after resume

1. Check healthy services, portal/login, CSS/JS, existing records and attachment.
2. Check scheduling retained its prior enabled/paused setting. Healthchecks do not
   enable scheduling; a deliberately paused scheduler can report healthy.
3. Stop/start, then save unchanged resume YAML. Verify health and data again.
4. Retain `05-resume.yaml` as the current installed baseline. Future plans must
   use that successful resume YAML, with a NEW operation ID/output directory.

If real migration fails, status remains migrating and both resume and blind
migration retries are refused. Preserve logs and recovery files. Restoring the
pre-test VM snapshot is the lab fallback; this implementation does not perform
automatic database rollback. Independent backup restore, real patch upgrade,
queue-state recovery and actual interrupted-patch recovery are separate tests.

## Generate another plan

From erpnext-truenas, with a new output directory each time:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_rehearsal.py --installed-yaml catalog-dev/generated/catalog-test.runtime-guards.yaml --output-dir catalog-dev/generated/catalog-rehearsal-01 --rehearsal
```

For a later operation, replace installed-yaml with the previous successful
05-resume.yaml and choose a fresh output directory. The generator refuses an
existing directory; never overwrite an in-progress operation's IDs.
