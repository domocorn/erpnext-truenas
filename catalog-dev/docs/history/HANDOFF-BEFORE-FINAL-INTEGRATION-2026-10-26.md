# Historical snapshot — superseded by ../../HANDOFF.md

2026-10-26 confirmed recovery creation failure: job 9474 failed at template rendering because the library forbids a host_path under /mnt/.ix-apps. No restore ran. native_failure_lab.py now verifies/copies the original backup to private /mnt/labpool/erpnext-native-recovery-input-01, verifies hashes and UID-1000 read permissions, and uses that permitted path read-only. Original backup and failed source remain unchanged. Three new copy/render regression tests (including exact forbidden internal path) and nine helper tests passed; the real copied backup was readable/checksum-valid as UID 1000 in the exact source image. Transfer updated helper only and rerun recover; VM recovery remains pending. No snapshot reset or app deletion required.

2026-10-26 confirmed VM checkpoint: recovery staging role source, no pending operation, journal matches bundle; recovery catalog entry AND app directory are absent (consistent with catalog sync). Recovery app remains uncreated. native_failure_lab.py now restores the missing owned overlay from verified bundle files, backs up the current index, preserves unrelated entries and rejects foreign/modified/concurrently changed content. Nine host-helper tests and a real-metadata repair/reuse check inside the official validator passed. Transfer only updated helper and rerun recover; do not remove the journal or recreate the failed app. VM restore still pending.

2026-10-26 recovery resume fix: VM reports the expected failed source (native 1.0.0 CRASHED) and no recovery app. verify-failed passes. recover stopped because its recovery catalog was already staged. native_failure_lab.py now verifies and reuses a completed owned source overlay before app.create; changed or pending staging and existing destination apps remain refused. Six host-helper tests pass, including three new resume/ownership cases. Transfer only the updated helper into the existing /tmp/erpnext-native-failure-transfer-01/erpnext-native-failure-recovery-01 directory and rerun recover; no VM recovery success claimed yet.

2026-10-23 native failure/recovery package READY: generated/erpnext-native-failure-recovery-01.tar.gz. Next user action: NATIVE-FAILURE-RECOVERY-TEST.md step 1, separate apps on 18091/18092. Actual local committed migration failure, refused restart, independent old-image native restore, record/private-file/encrypted-secret verification and recovery restart passed. Failed source preserved; both local Docker stacks stopped. Official schema/index/render/Compose checks and affected regression tests passed. New profile builders do not enable failure hooks or recovery in the default catalog app. Current VM 18090 success and overlay removal remain recorded below; preserve that app/data.

2026-10-23 latest: native VM install/upgrade and unchanged restart passed by user report. Status: erpnext-native-test, version 1.0.0, RUNNING, custom_app false, upgrade_available false. User successfully removed the temporary overlay; preserve the installed 18090 app and backup. Next is the separate native failure/recovery group on 18091/18092. Earlier pending-native-VM statements below are superseded.

2026-10-23 current checkpoint: worker procedure passed by user report; active-job timing at VM Stop remains uncertain. Native catalog lab packaging is COMPLETE. generated/erpnext-native-lab-01.tar.gz contains schema-validated source/target catalog packages and a reversible single-app staging tool. Official renders, Compose validation, local lifecycle regressions, overlay ownership/recovery tests and actual unchanged native-graph restart passed. NEXT USER STEP: NATIVE-CATALOG-TEST.md step 1 on the disposable VM. Native VM installation/upgrade has not yet run. See NATIVE-CATALOG-PROGRESS.md. This checkpoint supersedes earlier pending-worker and pending-packaging statements below.

# Local Codex handoff — ERPNext for TrueNAS

2026-10-23: worker YAML save immediately logged the user out of TrueNAS and did
not persist. The YAML's JSON string alone measured 65,962 characters, exceeding
the versioned 25.10.7 authenticated WebSocket cap of 65,536 (app.update is not an
extended-size exception). This strongly explains the behavior; no VM log was read.
Use generated/catalog-worker-shutdown-01.ui-safe.yaml instead of the original.
It is semantically identical after removing the unused catalog_bootstrap config,
using YAML anchors/literal blocks; Docker Compose expanded-model comparison passed.
Encoded sizes are 54,318 LF / 57,116 CRLF, leaving request-envelope headroom.
compose_output.py now enforces that budget for prepare_worker_shutdown output.
Four serializer tests pass. VM retry/save and worker test remain pending; do not
mark the logout or worker rollout resolved until the user confirms the new save.

Latest: user reported all CATALOG-PATCH-TEST.md VM checks passed (2026-10-20).
18088 is the working v16.51.1 patch app using generated/catalog-patch-01/02-upgrade.yaml;
18089 is its independent v16.51.0 recovery using catalog-patch-recovery-01/03-start-restored-clone.yaml.
Next is CATALOG-WORKER-SHUTDOWN-TEST.md with one private same-image update,
generated/catalog-worker-shutdown-01.yaml, on 18088 only. VM execution pending.
Worker supervisor now signals only the worker PID so active jobs can finish;
worker stop grace is 120 seconds. New backups/migrations require empty pending,
started, deferred, scheduled and failed queues, inspected without cleanup.
Local worker stop and full-app stop preserved active jobs. A deliberately forced
worker exit 137 left started work and queue guard correctly refused migration.
The local lab is stopped with forced-job evidence in its queue_data and
sites/.catalog-worker-drain-fixture.json; do not silently clear/restart that
evidence. The app is /var/tmp/erpnext-worker-shutdown.yaml with data under
/mnt/erpnext-wsl-lab/catalog-real-patch. Forty-four distinct Linux tests pass.
Cached official scoped schema, render and Compose checks passed. No native
catalog upgrade support or general job/side-effect recovery is claimed.

2026-10-20: user reported all CATALOG-COORDINATOR-TEST.md VM checks passed.
Current working 18087 baseline is generated/catalog-coordinator-01.yaml.
Next milestone is CATALOG-PATCH-TEST.md on a NEW patch-test app at 18088,
using only the exact reviewed v16.51.0-to-v16.51.1 digest pair in patch_policy.py.
Do not downgrade or modify 18087. A separate old-version backup recovery app at
18089 uses generated/catalog-patch-recovery-01/. No native catalog upgrade is
claimed; default catalog image guard remains unchanged. VM patch execution pending.
Local real patch and source-version recovery both passed, including record,
exact private content and synthetic encrypted-secret decryption. Target version
16.51.1 and recovered source version 16.51.0 were verified; target login/assets,
upgrade repeat and old-version recovery restart passed. Both local apps stopped.
Forty distinct Linux tests pass; all five private VM patch/recovery files validate.
Read CATALOG-PATCH-TEST.md next. Never apply its old source YAML to a migrated DB.

Current milestone: one-deployment same-image coordinator implemented under
catalog-dev (not enabled in the default catalog template). See
CATALOG-COORDINATOR-TEST.md and generated/catalog-coordinator-01.yaml for the next
completed VM test on the successful 18087 app. It consolidates offline backup, migration
and guarded resume under one exclusive lifetime lock. Real local active runtime
blocked it before mutation; stopped-app deployment succeeded. Native catalog
updates and general image changes remain unsupported. VM coordinator passed by user report.
User clarified 18086 has only Created/Exited containers and no running containers;
TrueNAS still displaying Crashed is consistent with the intentional failure.

Latest continuation (2026-10-19): user reported all independent catalog restore
VM checks passed, including source-credential login. User then reported all VM
pinning checks passed and supplied the exact expected pinned image reference and
unchanged image config ID. The clone baseline is now
generated/catalog-pinning-01/05-resume.yaml; the original source remains on
catalog-rehearsal-01/05-resume.yaml. Next is CATALOG-PINNED-RECOVERY-TEST.md:
restore the pinning backup into a NEW erpnext-catalog-pinned-recovery-test on
18086, using generated/catalog-pinned-recovery-01/. Existing apps stay intact.
The user subsequently reported the pinned recovery VM procedure passed in full.
The recovery app baseline is catalog-pinned-recovery-01/03-start-restored-clone.yaml.
All three apps remain independent. VM dependency image config IDs and RepoDigests
were supplied and registry-verified; fresh-install defaults now pin ERPNext,
MariaDB and Redis. Existing generated VM configurations remain unchanged.
No submission has been posted.

Latest work: CATALOG-INTERRUPTION-TEST.md prepares actual same-image bench migrate
interruption after an ephemeral before_migrate hook commits a ToDo fixture. Local
kill returned 137, durable state stayed migrating, the partial fixture was confirmed
in the failed source DB, and retry/startup were blocked. VM execution passed by
user report: all checks passed, 18086 remained crashed/blocked after restart,
18087 worked, and no other apps were running. No authenticated VM inspection
or new restart verification of 18084/18085 was performed. The working baseline is
generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml. Leave
18086 stopped/guarded with its failure state and backup preserved. Prepared
files are under generated/catalog-interruption-01/ (four stages) and
generated/catalog-interruption-recovery-01/ (three independent recovery stages).
Only the disposable 18086 recovery app is the interruption target; original apps
stay untouched. The new recovery app is erpnext-catalog-interrupt-recovery-test
on 18087. Do not imply a real versioned patch or native upgrade has been tested.
Local independent recovery and unchanged-YAML recreation subsequently passed:
pre-test records/private attachment bytes restored, partial fixture absent,
scheduling paused, backup hashes intact and all nine persistent services healthy.
Both local stacks were stopped with interrupted-source evidence preserved.
Twenty-nine distinct Linux tests pass; all seven private VM YAML files validate.
Five coordinator-specific tests bring the distinct Linux total to 34. Existing
tests remain passing. The private coordinator YAML passes Compose validation.
The shorter recovery app name is 39 characters. Native upgrades, real versioned
patches, encrypted-field decryption and queue draining remain separate work.

Open both local repositories in a VS Code workspace: `erpnext-truenas` and `apps`.
Read each repository's AGENTS.md if present and apps/CONTRIBUTIONS.md before changes.

User: domocorn. GitHub project https://github.com/domocorn/erpnext-truenas.
User forked/cloned truenas/apps. TrueNAS test target 25.10.7 in VMware Workstation
on Windows with 32 GB RAM; VM allocated ~12 GB RAM. Production NAS exists and MUST
remain untouched. Testing uses fictional business data in a disposable VM.

## Already tested by the user

Standalone Compose generator automatically installs ERPNext with official images.
Initialization, app/VM restart, unchanged configuration save, multiple isolated
instances, database/public-private file restore, simulated pre-migration failure,
guarded startup, same-version migration and real ERPNext 16.51.0→16.51.1 patch
upgrade passed. Frappe was 16.52.0 before/after that patch. Results are user-reported;
see docs/TEST-RESULTS.md. Encrypted credential decryption and recovery from an actual
mid-patch database failure remain untested. No general major-upgrade claim.

## Existing development

scripts/build.py generates private YAML, supports --erpnext-version, defaults to
v16.51.1, and refuses output overwrite. scripts/prepare_upgrade.py reads the EXACT
installed private YAML, preserving secrets/storage and generating offline backup,
simulated failure, guarded resume and migration stages. --numbered-stages gives
unique 01–05 filenames. Operation IDs and persisted .nas-upgrade-state.json prevent
blind repeats. New operation plans must use the previous successful resume YAML.
Never regenerate build.py output to modify an existing deployment's database password.

## Current milestone

New catalog draft under apps/ix-dev/community/erpnext, local render tools under
erpnext-truenas/catalog-dev. Uses native TrueNAS library 2.3.17. Form schema,
metadata, image values, permissions, MariaDB dependency, port and portal metadata.
Dataset-backed mounts require bootstrap of Frappe assets from image sites directory;
bootstrap runs before mounting the real sites path into initializer/runtime.

This catalog draft is FRESH INSTALL ONLY and version-locked: bootstrap blocks image
tag changes. It is not catalog accepted, not update-ready and not HexOS curated.
Do not transfer the prototype's upgrade promises to it without reengineering and
retesting the different mount/permissions/deployment lifecycle.

## Next work

1. Read catalog-dev/README.md. Run local render checks, then user tests rendered
   YAML as NEW erpnext-catalog-test on port 18084 with dedicated lab directories.
2. Complete official middleware/schema/Docker catalog validation, official library
   vendoring and metadata generation, icon and image policy review, worker healthchecks.
3. Integrate safe catalog upgrades (stop/drain old workers, backup, migration gate,
   new runtime). Prevent false claims about automatic rollback after DB patches.
4. Check existing issues/PRs before a reviewed community-train submission.
5. Later build a thin HexOS curation wrapper; community submissions are supported,
   but official inclusion requires HexOS review. Verify current scripts/docs first.

Keep generated YAML/passwords/site configs/backups private. Never stage .venv,
generated/ or private data. User uses GitHub Desktop; explain which repository and
branch receives each change. Do not push, submit PRs, or post messages without
explicit user instructions. Provide meaningful tests and clear evidence limits.
