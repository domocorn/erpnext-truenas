# Test record

## Native failure/recovery VM group complete — user reported, 2026-10-26

The user reported verification passed before and after recovered-app stop/start, with successful login and ERPNext 16.51.0 checks. Output confirmed the failed native source remained migrating with its old identity, no ERPNext runtime running and checksum-valid backup; the recovered original record, private attachment and synthetic encrypted value passed, the failed-migration record was absent, and app/storage/database credentials were independent. Preserve 18090, failed18091, recovered18092 and backup/input copy. The catalog entry now integrates the tested normal graph; final comparison differed only in explanatory notes. Official schema/library/render/Compose checks and Linux regressions passed. Full metadata validation is blocked only at the approved CDN icon URL check; no fully green CI or submission claim is made. See catalog-dev/docs/submission/SUBMISSION-PREPARATION.md.


## Native catalog VM test — user reported successful, 2026-10-23

The user reported the native install, reviewed patch upgrade, data checks and
unchanged restart passed. Reported middleware status was native app
`erpnext-native-test`, version `1.0.0`, state `RUNNING`, `custom_app: false`, and
`upgrade_available: false`; the staging journal had target role and no pending
operation. The user also ran removal successfully. This removes the temporary
catalog overlay, not the installed app, datasets or recovery backup. No maintainer
submission or approval is implied.

Native failure/recovery preparation then passed locally: an actual reviewed
patch migration committed its test hook and failed, leaving migrating state,
the old image marker and no running ERPNext runtime. Unchanged redeployment
refused the interrupted operation. A separate native source-image initializer
restored its checksum-verified backup with independent storage/database identity.
Original record, exact private attachment bytes and synthetic encrypted-value
decryption passed; the failed-migration record was absent. Recovery restart
passed without restoring again, and failed-source state stayed unchanged.
Both local stacks are stopped with evidence preserved. Official schema/index,
rendering and Compose checks passed for all three profiles. Six additional
native restore/host-isolation tests and affected regressions passed.
The corresponding native failure/recovery VM group remains pending; follow
catalog-dev/docs/tests/NATIVE-FAILURE-RECOVERY-TEST.md.

## 2026-10-23 native catalog packaging checkpoint

Worker-shutdown VM procedure passed by user report, including the UI-safe save
and unchanged restart. Whether the fixture was still active at Stop is uncertain.
Native lab source/target packages passed official scoped schema checks,
publication, catalog/version-index schemas, official rendering and Compose config
validation. Local lifecycle regressions and four overlay ownership/recovery tests
passed. The actual local 16.51.0 to 16.51.1 upgrade preserved a record, private
attachment and synthetic encrypted value. Unchanged restart reused the migration
and retained one backup. The local lab is stopped with its data preserved.

Native middleware VM installation/upgrade is pending; follow
catalog-dev/docs/tests/NATIVE-CATALOG-TEST.md. Final app integration, icon/full metadata and
submission remain pending. The agent has not changed the VM catalog.

Deployed initial ERPNext Setup -> Created fake company and added some fake data:
	Database stayed intact through container restarts, server restarts, and opening and saving the YAML with no changes made

## Author-side validation

Python compilation, generated YAML round-trip, and local unit tests are run when
packaging this starter. Five unit tests passed, including interrupted-install and
unmanaged-site refusal, password interpolation, and existing-site preservation.
All Python source parsed successfully. These do not establish real Docker/TrueNAS
compatibility; Docker is unavailable in the authoring environment.

## VM results — user reported successful on 2026-10-18

| Check | Result | Notes |
|---|---|---|
| TrueNAS version | PASS (user reported) | Target 25.10.7 |
| Images pulled | PASS (user reported) | |
| Fresh site/login | PASS (user reported) | |
| Customer/Issue/attachment | PASS (user reported) | |
| App restart | PASS (user reported) | |
| VM restart | PASS (user reported) | |
| Edit/save | PASS (user reported) | |
| Second app isolated | Pending | |

## Backup and restore

Backup command completed and four expected files were listed on 2026-10-18.
Restore validation passed in the test VM, as reported by the tester. See docs/RESTORE-TEST.md for the procedure.

| Check | Result |
|---|---|
| Restore to separate app | PASS |
| Customer and Issue restored | PASS |
| Attachment content verified | PASS |
| Source/destination isolation | PASS |
| Restored app restart | PASS |
| Encrypted setting decryption | Not tested |

## Backup and upgrade

| Check | Result |
|---|---|
| Backup job produced four components and preserved config | PASS |
| Maintenance stages had no running normal services | PASS |
| Deliberate failure blocked guarded resume | PASS |
| Same-version migration completed | PASS |
| Resume restored records and attachment | PASS |
| App restart after resume | PASS |
| Disabled scheduler remained disabled | PASS |
| Real version-to-version upgrade | PASS: 16.51.0 → 16.51.1; see below |
| Recovery from an actual mid-migration failure | NOT TESTED |

## Real upgrade

Before upgrade: ERPNext **16.51.0**, Frappe **16.52.0**.

| Actual version upgrade check | Result / evidence |
|---|---|
| New app initialized on ERPNext 16.51.0 | PASS |
| Pre-upgrade Frappe version | PASS |
| Source-image backup completed | PASS |
| No normal services running during offline stages | PASS |
| Intentional failure blocked startup | PASS |
| Migration with 16.51.1 completed | PASS |
| Post-upgrade ERPNext/site versions | 16.51.1 |
| Post-upgrade Frappe version | 16.52.0 |
| Customer, Issue and attachment survived | PASS |
| New record saved after upgrade | PASS |
| Optional draft invoice/Item survived | N/A |
| App and VM restart preserved upgraded site | PASS |
| Other apps remained isolated | PASS |

Evidence is tester-reported from the TrueNAS 25.10.7 VM; raw logs were not independently inspected.
The real upgrade was one patch transition. Actual mid-migration failure recovery
and encrypted-setting decryption remain untested. Optional draft-invoice testing
was not performed. No claim of general or major-version upgrade compatibility is made.

## Catalog-rendered draft / library 2.3.17

First VM deployment: user reported frontend exit with permission denied writing
`/etc/nginx/conf.d/frappe.conf`. Added supplementary group 0 to the non-root
frontend for the image's group-writable nginx paths. Local render regression
checks passed (two passed, two Linux-only skipped). User subsequently reported
README step 5 passed after the frontend fix.

### Catalog VM checks (user-reported PASS)

- Fresh installation and Administrator login.
- CSS, JavaScript and icons loaded.
- Fictional customer and Issue created; attachment uploaded and opened.
- App stop/start preserved records, assets and attachment.
- VM restart preserved records, assets and attachment.
- Unchanged YAML save did not recreate the site or reset its password.
- Existing apps remained unchanged.

The user reported step 5 as passed; raw logs were not independently inspected.
The user confirmed the Web Portal button appeared and worked, and the Notes
section appeared on the right-hand side.

Local Windows checks performed by Codex on 2026-10-18, using Python 3.13.9
and apps checkout 85c0b1f21b9ad4e9c667a170a02b5663b9236287.

- Native rendering/dependency test: PASS.
- Host-path rendering, dollar-password escaping and embedded Python parsing: PASS.
- Two Linux bootstrap execution tests: SKIPPED on Windows, as designed.
- Repository port validation: PASS using Python `-X utf8`; the default Windows
  encoding failed while reading another catalog file. No upstream files changed.
- Private deployment YAML was generated and used for the user's VM test.
- These results do not establish middleware/schema validation, official Docker
  CI, catalog upgrade support or catalog acceptance.

### Step 6 local preparation

- Docker Engine 29.1.3 and Compose 2.40.3 installed in Ubuntu WSL.
- All four local tests passed in Linux, including bootstrap image-change and
  unmanaged-storage refusal (no skips).
- Actual upstream metadata helper checks: questions/container enums and image
  registry policy passed. Metadata validation fails on the empty icon URL.
- Upstream 512x512 ERPNext PNG icon candidate prepared in catalog-dev/assets;
  TrueNAS CDN publication remains pending.
- Full official container validation and safe catalog upgrade lifecycle remain
  separate from these local checks.

Official container follow-up: app-scoped library vendoring/hash generation,
catalog schema validation in an isolated Linux catalog, official CI render-only
with metadata skipped, and Docker Compose config validation all passed.
The private VM YAML also passed Compose config validation without starting it.
Full metadata generation remains blocked by the empty icon URL; item.yaml was
generated with the upstream helper. These are not hosted CI or catalog-update
test results. See catalog-dev/docs/reviews/VALIDATION.md for the validator digest and scope.

### Runtime healthcheck revision (local WSL)

Eight Linux tests passed. A separate WSL deployment initialized successfully;
all six runtime services plus MariaDB and both Redis services reported healthy.
Worker and scheduler probes rejected a queue-Redis outage, with recovery after
restart. Final probes executed successfully inside the exact ERPNext image.
Official render/schema and Compose validation repeated successfully.

A separate private healthchecks-ready.yaml preserves the original installed
credentials, storage and images.

### Runtime healthcheck revision (TrueNAS VM)

On 2026-10-19 the user reported completing HEALTHCHECK-TEST.md checks 1-5 with
normal operation: runtime health, portal/login, existing customer/Issue/attachment,
and app stop/start persistence passed. This is user-reported evidence; raw health
logs and the VM snapshot were not independently inspected. Catalog upgrades and
migration failure recovery remain untested for this storage layout.

### Runtime upgrade guard foundation (local WSL)

Eleven Linux tests passed, including migration-state rejection, shared/exclusive
lock lifetime, signal forwarding, and preservation/idempotence of the same-image
update. Real container checks verified runtime blocks exclusive access, stopping
all runtime releases it, and a held exclusive lock blocks runtime startup.
Official rendering, schema and Compose validation passed for the new revision.
Actual catalog migration remains pending; see catalog-dev/docs/reviews/LIFECYCLE-REVIEW.md.

### Runtime upgrade guard foundation (TrueNAS VM)

On 2026-10-19 the user reported all RUNTIME-GUARD-TEST.md checks passed:
same-image guard rollout, healthy runtime/dependencies, portal/login and assets,
existing customer/Issue/attachment, app stop/start persistence, and unchanged
YAML save. Results are user-reported; raw VM logs and the snapshot were not
independently inspected. No catalog database migration, image upgrade, offline
backup or migration-failure recovery is established by this test.

### Catalog-layout same-version rehearsal (local WSL)

Sixteen Linux tests passed. Two complete operations in the disposable WSL lab
passed offline backup, deliberate failure before migration, blocked resume with
no runtime started, same-version bench migrate, and guarded resume. The second
operation was generated from the first successful resume and retained paused
scheduling. Backup refused live guarded runtime; completed migration did not
repeat. Interrupted-command and corrupt-backup refusal passed unit tests.

The fictional ToDo and private attachment survived migration/resume. SQL gzip and
private tar fixture contents and backup checksums were verified. All nine
long-running services were healthy after resume. The lab was stopped afterward.
Private VM stages were generated and Compose-validated without deployment.

### Catalog-layout same-version rehearsal (TrueNAS VM)

On 2026-10-19 the user reported the five-stage rehearsal passed, including the
expected pre-migration failure and blocked resume, successful same-version
migration/resume, app stop/start, and VM restart. A post-test snapshot was created.
Scheduler logs showed only the image entrypoint's assets-linking message; no
abnormal operation was reported. Raw logs and snapshots were not inspected.

The separate recovery-directory copy was NOT made. This does not invalidate the
reported migration/persistence results, but off-VM backup preservation and
independent restore are not established. The recovery directory is expected to
remain under sites/.catalog-recovery/<operation-ID>; existence and integrity on
the VM have not been independently checked. Keep the successful 05-resume.yaml
as the installed baseline for future plans.

Still untested: independent restore, real patch upgrade, actual mid-patch failure
recovery, encrypted credentials and native one-click catalog upgrades.

### Independent catalog restore (local WSL)

Nineteen Linux tests passed. A new clone with separate sites/logs/database/queue
storage, credentials and network restored the checksummed source backup through
a read-only mount. Source ToDo and private attachment recovered, clone scheduling
remained paused, bidirectional record isolation passed, and clone restart/data
persistence plus six runtime probes passed. Source backup checksums remained
unchanged. Both local stacks were stopped after tests.

An earlier SQL import interruption left restoring state and blocked runtime as
intended. Its failed destination was retained; the successful test used a fresh
destination with WSL held active throughout. This is not an automatic retry or
proof of recovery from a failed patch. VM restore and off-VM backup preservation
remain pending. See catalog-dev/docs/tests/CATALOG-RESTORE-TEST.md and RECOVERY-COPY.md.

### Independent catalog restore (TrueNAS VM)

On 2026-10-19 the user reported all catalog restore tests passed and login using
the source catalog-test credentials succeeded. This records the restore guide's
record/attachment, isolation and clone-restart checks as user-reported passes;
raw logs and encrypted-field decryption were not independently inspected.
Keep the source's 05-resume.yaml and the clone's 03-start-restored-clone.yaml as
separate current baselines. Off-VM recovery-copy completion has not been confirmed.

### Same-content digest pinning (local WSL; VM pending)

The user reported running v16.51.1 with image config ID
sha256:0ce48f9b465e15869540282c8f203bdbe24b2ae9fe5419c2f32c7e462fba5591
and repository index digest
sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268.
Registry manifest inspection confirmed the amd64 config ID matches.

On the local restored clone, backup, intentional failure, blocked startup,
migration and guarded digest-pinned resume passed. Failed startup preserved the
old marker. All nine persistent services became healthy, paused scheduling and
maintenance flags were preserved, source and clone-only records survived, and
the private attachment bytes matched the source. Unchanged-YAML recreation also
passed; the local clone was stopped. Twenty-three distinct Linux tests passed.
VM stages are prepared but not executed: catalog-dev/docs/tests/CATALOG-PINNING-TEST.md.
Only same-version same-content pinning is supported by this helper; no actual
patch upgrade, native catalog update or pinning-backup restore is claimed.

### Same-content digest pinning (TrueNAS VM)

On 2026-10-19 the user reported all other pinning tests passed and supplied:
frappe/erpnext:v16.51.1@sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268
sha256:0ce48f9b465e15869540282c8f203bdbe24b2ae9fe5419c2f32c7e462fba5591.
The configured reference and unchanged image config ID match expectations.
The shell backend assignment printing nothing is normal. This records guide
checks as user-reported; no authenticated VM inspection was performed.
The restored clone's baseline is now catalog-pinning-01/05-resume.yaml.

### Recovering the pinning backup (local WSL; VM pending)

The restore helper now validates same-content pinning manifests and initializes
the destination using the exact pinned image. Twenty-six distinct Linux tests
passed, covering catalog/runtime, rehearsal/pinning and six restore checks.
These include mismatched pinning metadata and interrupted-restore retry refusal.

A new independent pinned-recovery app initialized, restored the pinning backup
through a read-only source mount and resumed with all nine persistent services
healthy. Backup-era source and restore-clone-only records were present, the
post-backup source-only fixture was absent, private attachment bytes matched the
source, paused scheduling was preserved and source recovery checksums remained
intact. A recovery-only record survived unchanged-YAML recreation; all nine
services returned healthy. The local recovery app was stopped after verification.

Three private VM stages were prepared and Compose-validated, but not deployed.
Next: catalog-dev/docs/tests/CATALOG-PINNED-RECOVERY-TEST.md on NEW
erpnext-catalog-pinned-recovery-test, port 18086. This is recovery of a same-content
pinning backup, not a real failed-patch recovery or encrypted-field decryption test.

### Pinning-backup recovery (TrueNAS VM)

On 2026-10-19 the user reported CATALOG-PINNED-RECOVERY-TEST.md worked in full.
This records initialization, restore, source-credential login, backup-era data,
attachment/isolation, paused scheduling and restart checks as user-reported passes.
No authenticated VM inspection was performed. The recovery app's current baseline
is catalog-pinned-recovery-01/03-start-restored-clone.yaml on port 18086.

The user supplied dependency image identities from that recovery app. MariaDB's
RepoDigest f16d7a34... resolves to config ID c1d04d5c..., and both Redis services'
RepoDigest ac2da09b... resolves to config ID 166f6f14.... Registry inspection of
the linux/amd64 manifests confirmed both exact config IDs. The catalog default
ERPNext, MariaDB and Redis references now include these verified digest pins.
Existing VM YAML and credentials were not changed.

After adding these pins to the catalog defaults, all 26 Linux regressions passed.
The local recovered site started with pinned ERPNext, MariaDB and Redis, retained
its recovery-only record and paused scheduling, and all nine persistent services
became healthy. The local stack was stopped. Cached official app rendering,
Compose configuration and scoped schema checks passed. The CI wrapper rerun was
stopped while waiting for its mandatory validator-image pull; full wrapper/metadata
validation was not completed in this turn. No new VM rollout or submission occurred.

### Actual same-image migration interruption (local WSL; VM pending)

Twenty-nine distinct Linux tests passed, including three new interruption guards
and plan checks. A test-only wrapper injected an ephemeral before_migrate hook
into the disposable migration job. The hook committed a fixture ToDo and waited;
the container was then killed (exit 137). State stayed migrating and read-only
database diagnostics confirmed the partial fixture persisted. Retry and resume
were blocked. The failed source was retained stopped with its backup intact.

A new independent destination restored the pre-migration backup. Earlier test
records and private attachment bytes recovered, the partial fixture was absent,
scheduling remained paused and source backup hashes were unchanged. Recreation
from unchanged YAML retained recovered data, excluded the partial fixture and
returned all nine persistent services healthy. Both local test stacks were stopped
with failed-source evidence retained. Four private
VM interruption stages and three recovery stages passed Compose validation;
VM execution is pending catalog-dev/docs/tests/CATALOG-INTERRUPTION-TEST.md.
This is a controlled real bench migrate interruption with committed application
data, not a real ERPNext version transition or arbitrary patch/DDL failure test.

### Recovering the pinning backup (local WSL; VM pending)

The restore helper now validates same-content pinning manifests and initializes
the destination using the exact pinned image. Twenty-six distinct Linux tests
passed, covering catalog/runtime, rehearsal/pinning and six restore checks.
These include mismatched pinning metadata and interrupted-restore retry refusal.

A new independent pinned-recovery app initialized, restored the pinning backup
through a read-only source mount and resumed with all nine persistent services
healthy. Backup-era source and restore-clone-only records were present, the
post-backup source-only fixture was absent, private attachment bytes matched the
source, paused scheduling was preserved and source recovery checksums remained
intact. A recovery-only record survived unchanged-YAML recreation; all nine
services returned healthy. The local recovery app was stopped after verification.

Three private VM stages were prepared and Compose-validated, but not deployed.
Next: catalog-dev/docs/tests/CATALOG-PINNED-RECOVERY-TEST.md on NEW
erpnext-catalog-pinned-recovery-test, port 18086. This is recovery of a same-content
pinning backup, not a real failed-patch recovery or encrypted-field decryption test.


### Interrupted migration recovery (TrueNAS VM, user-reported pass)

The user reported all CATALOG-INTERRUPTION-TEST.md checks passed. After restart,
18086 remained crashed/blocked, while the recovered app on 18087 worked well.
No other apps were running. This records the guide checks as user-reported;
raw logs were not independently inspected and 18084/18085 were not newly checked.

The active recovered baseline is
catalog-dev/generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml
for erpnext-catalog-interrupt-recovery-test (39 characters). Preserve the failed
18086 state and recovery backup; do not clear guards or apply its old success YAML.
This remains a same-image committed-hook interruption and separate restore test,
not a versioned patch/DDL failure, encrypted-field or native-upgrade claim.

### Single-deployment lifecycle coordinator (local WSL; VM pending)

The user clarified the failed 18086 app has only Created/Exited containers and
none are running, despite TrueNAS showing Crashed. No further action is needed
to force that guarded app to run.

A private coordinator now runs same-image backup, migration and original
initialization/resume under one exclusive lifetime lock. Thirty-four distinct
Linux tests pass, including five new coordinator checks. In real containers,
active runtime blocked it with BlockingIOError before state mutation; after
stopping runtime, the single deployment completed successfully. Recreating from
unchanged YAML reused completed backup/migration, retained the recovery manifest,
records, private attachments and paused scheduling, and all nine persistent
services became healthy. The local clone was stopped afterward.

The private VM plan passes Compose validation but has not been applied. Next is
catalog-dev/docs/tests/CATALOG-COORDINATOR-TEST.md on the working 18087 app. Default catalog
template and VM apps remain unchanged. No native update/version transition,
queue-draining or general patch-recovery claim is made.

### Single-deployment coordinator (TrueNAS VM)

On 2026-10-20 the user reported all CATALOG-COORDINATOR-TEST.md checks passed.
Record backup/migration/resume, data/attachment retention, unchanged save,
app/VM restart and repeat safety as user-reported results; raw VM logs were not
independently inspected. The working 18087 baseline is catalog-coordinator-01.yaml.
The failed 18086 app remains guarded with no running containers. Native catalog
upgrades and arbitrary source/target images remain outside this result.

### Real v16.51.0 to v16.51.1 graph (local WSL; VM pending)

Forty distinct Linux tests pass. A fresh isolated v16.51.0 site, pinned to registry
index f2d409c5... (amd64 config e43ea1a1...), received a record, private attachment
and synthetic encrypted-secret fixture. Source-image backup preceded target-image
migration to v16.51.1 index a856e7f6.... The target version, retained record,
private content and decrypted fixture passed. Login HTML and three referenced
asset bundles returned HTTP 200. Recreating the graph correctly reused completed
backup/migration. The default catalog image guard was not relaxed.

The pre-patch backup restored into a separate fresh v16.51.0 destination, with
the source backup mounted read-only. Record, private content and synthetic secret
decryption passed; scheduling stayed paused. Recovery restart returned nine healthy
services. Both local patch apps were stopped. Five private VM files validate;
next is catalog-dev/docs/tests/CATALOG-PATCH-TEST.md using new apps on 18088/18089 while
leaving the successful 18087 app unchanged. No native catalog update, arbitrary
patch/DDL-failure recovery or automatic rollback is claimed.

### Real patch and source-version recovery (TrueNAS VM)

On 2026-10-20 the user reported all CATALOG-PATCH-TEST.md steps passed. Record
fresh v16.51.0 initialization, the reviewed v16.51.1 transition, data/attachment
retention, repeat safety and independent old-image backup recovery as user-reported
passes. Raw VM logs were not independently collected. The synthetic encrypted
fixture was only tested locally, not asserted as a VM result. Current baselines:
catalog-patch-01/02-upgrade.yaml on 18088 and
catalog-patch-recovery-01/03-start-restored-clone.yaml on 18089.

### Worker shutdown and queue gate (local WSL; VM pending)

Fixed worker signal forwarding: bench execs the worker, so worker commands now
receive signals at the child PID instead of the whole process group. Other runtime
commands retain group forwarding. Both workers have 120-second stop grace.

Forty-four distinct Linux tests pass, including queue emptiness checks with no
cleanup, pre-mutation gate refusal and update preservation/idempotence. The local
worker completed an active 20-second sleep job during SIGTERM stop and exited 0.
A separate full-app stop also preserved an active job; restart saw it finished.
The empty queue passed the migration gate. An intentional two-second forced-stop
timeout then killed a longer test job's worker (exit 137), leaving started work;
the read-only gate rejected it. No unresolved job was removed or automatically
replayed. The lab was stopped with queue/fixture evidence retained.

Cached official scoped schema, render and Compose checks passed for the catalog
worker changes. A private same-image VM update is prepared and Compose-validated,
not applied. Next is catalog-dev/docs/tests/CATALOG-WORKER-SHUTDOWN-TEST.md on 18088 only.
Native upgrades, unlimited draining and general job/side-effect recovery remain
outside these results.

### Worker update UI save size (2026-10-23; VM retry pending)

The user reported an immediate TrueNAS login redirect when saving the worker
update, and text comparison showed the YAML was not saved. Its encoded YAML
string measured 65,962 characters, above the 25.10.7 ordinary authenticated
WebSocket cap of 65,536 even before request-envelope fields. Versioned middleware
source confirms that policy; no VM rejection log was independently read.

Prepared catalog-worker-shutdown-01.ui-safe.yaml with standard anchors/literal
blocks and unused-config removal: 54,318 JSON characters, or 57,116 with CRLF.
All service/script/credential/operation/storage values are preserved. Expanded
Compose-model equivalence and four serializer tests passed. The generator now
checks a conservative 60 KiB serialized-string budget. Retry the SAME worker
procedure with this replacement; VM save/worker success is not yet confirmed.

### Real patch and source-version recovery (TrueNAS VM)

On 2026-10-20 the user reported all CATALOG-PATCH-TEST.md steps passed. Record
fresh v16.51.0 initialization, the reviewed v16.51.1 transition, data/attachment
retention, repeat safety and independent old-image backup recovery as user-reported
passes. Raw VM logs were not independently collected. The synthetic encrypted
fixture was only tested locally, not asserted as a VM result. Current baselines:
catalog-patch-01/02-upgrade.yaml on 18088 and
catalog-patch-recovery-01/03-start-restored-clone.yaml on 18089.

### Worker shutdown and queue gate (local WSL; VM pending)

Fixed worker signal forwarding: bench execs the worker, so worker commands now
receive signals at the child PID instead of the whole process group. Other runtime
commands retain group forwarding. Both workers have 120-second stop grace.

Forty-four distinct Linux tests pass, including queue emptiness checks with no
cleanup, pre-mutation gate refusal and update preservation/idempotence. The local
worker completed an active 20-second sleep job during SIGTERM stop and exited 0.
A separate full-app stop also preserved an active job; restart saw it finished.
The empty queue passed the migration gate. An intentional two-second forced-stop
timeout then killed a longer test job's worker (exit 137), leaving started work;
the read-only gate rejected it. No unresolved job was removed or automatically
replayed. The lab was stopped with queue/fixture evidence retained.

Cached official scoped schema, render and Compose checks passed for the catalog
worker changes. A private same-image VM update is prepared and Compose-validated,
not applied. Next is catalog-dev/docs/tests/CATALOG-WORKER-SHUTDOWN-TEST.md on 18088 only.
Native upgrades, unlimited draining and general job/side-effect recovery remain
outside these results.
