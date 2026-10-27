2026-10-26 current final-validation checkpoint: all planned native lifecycle VM groups passed by user report, including recovery restart. The normal lifecycle is integrated into the actual app draft and its render differs from the tested normal graph only in x-notes. Official scoped schema, library/hash, rendering and Compose validation and Linux regression suites passed. Official metadata-derived fields applied; FULL metadata validation remains blocked on the real approved CDN icon URL (expected URL currently404). See SUBMISSION-PREPARATION.md; older pending-test text below is historical.

2026-10-23 current checkpoint: worker procedure passed by user report; active-job timing at VM Stop remains uncertain. Native catalog lab packaging is COMPLETE. generated/erpnext-native-lab-01.tar.gz contains schema-validated source/target catalog packages and a reversible single-app staging tool. Official renders, Compose validation, local lifecycle regressions, overlay ownership/recovery tests and actual unchanged native-graph restart passed. NEXT USER STEP: NATIVE-CATALOG-TEST.md step 1 on the disposable VM. Native VM installation/upgrade has not yet run. See NATIVE-CATALOG-PROGRESS.md. This checkpoint supersedes earlier pending-worker and pending-packaging statements below.

# Catalog draft validation

Upstream apps commit: 85c0b1f21b9ad4e9c667a170a02b5663b9236287
Library: 2.3.17 (loaded from actual upstream source, not mocked).
Four local tests passed on Linux; two bootstrap execution tests skip on Windows.
Native library rendering succeeded with ixVolume fixtures and host-path fixtures.
Python configs were parsed, no Docker socket is mounted, only frontend publishes
a port, runtime depends on successful initialization, and ownership is explicit.
Port validation selected 30530 and passed after the draft was added.

Windows preview on 2026-10-18: two render tests passed with Python 3.13.9;
two Linux bootstrap execution tests skipped as expected. Repository port validation
passed with Python -X utf8. See docs/TEST-RESULTS.md for local evidence limits.

Catalog VM deployment: README step 5 passed after the frontend supplementary
group 0 fix, per user report. See docs/TEST-RESULTS.md for scope and evidence limits.

Additional checks using the checkout's actual generate_metadata.py functions:
questions/container enums PASS; image registry rule PASS; app library import
rule PASS (no vendored app modules yet); app metadata FAIL because icon URL is empty.
These individual function checks do not replace the official full validation.

Duplicate-work search through GitHub's public API found open Frappeverse request
https://github.com/truenas/apps/issues/174 and closed ERPNext request
https://github.com/truenas/apps/issues/3496. No ERPNext PR was returned by that
search. Recheck before submission; no messages or PRs were posted.

Not run: interactive TrueNAS form, application-container CI startup,
catalog installation/update, HexOS. Official schema/render results appear below.
Pre-submission blockers: complete generated metadata, icon,
image pin/digest policy, runtime healthchecks and catalog lifecycle upgrades.
Image-version changes are blocked by bootstrap until upgrade coordination exists.

Ubuntu WSL environment: installed Docker Engine 29.1.3 and Compose 2.40.3
from Ubuntu packages. All four local tests passed on Linux (no skips), including
fresh/repeated bootstrap, image-change refusal and unmanaged-storage refusal.
Official validation image download and Docker checks are tracked separately;
local unit tests are not evidence of official CI success.

## Official container checks after VM acceptance

Validator image digest:
`sha256:40052bb779a9c5c15fa2f51ecdb7ee4201e1d895ac2587ac05ed08d2a457acfa`.

- Official `apps_catalog_hash_generate --train community --app erpnext`: PASS.
  Library 2.3.17 and its generated hash copied back only into this app.
- Official `validate_dev_directory_structure` for community/erpnext: PASS in an
  isolated catalog containing this app and matching library. This is the actual
  validator function called by the CLI, scoped explicitly rather than using a
  Git diff to select apps. It is not a whole-catalog or hosted GitHub CI run.
- Official `.github/scripts/ci.py --train community --app erpnext
  --test-file basic-values.yaml --render-only=true --skip-metadata`: PASS.
  Docker Compose config validation of its rendered result: PASS.
- Docker Compose config validation of the private VM YAML: PASS, without output
  of secrets and without starting containers.
- Full metadata generator: BLOCKED by empty icon URL. Its `build_item` helper
  generated item.yaml, allowing the schema check above. No fabricated CDN URL.
- Fixed labels enum: exclude permissions because the official metadata analyzer
  omits temporary services whose restart policy begins with on-failure.

The Windows-mounted checkout does not support the official tool's atomic rename
operation. Checks ran in `/tmp/erpnext-catalog-scoped` on WSL's Linux filesystem.
Python __pycache__ directories were removed from that isolated source library
before official hashing, because the upstream hash includes every file.
Only app.yaml, item.yaml and the generated ERPNext library were copied back.
The main checkout's global library hash file and unrelated apps were not changed.

Still pending: CDN icon and full metadata generation; verified digest transition;
catalog update design and failure/recovery
tests. The tested VM deployment was not changed by this work.

## Healthcheck revision

- Eight Linux tests passed, including rejection of stale/wrong-host/wrong-queue
  worker heartbeats, acceptance of idle workers, dependency failure and missing
  scheduler lock, and preservation/idempotence of the health-only YAML update.
- A disposable WSL stack initialized using fixture credentials and dedicated
  /var/tmp storage. All nine persistent services reported healthy.
- Final probes passed inside all six runtime containers using the exact pulled
  ERPNext v16.51.1 image. Both worker probes and scheduler rejected a stopped
  queue Redis; services recovered after Redis restart. Final worker outage check
  emitted only the exception type, without upstream connection-URL logging.
- Official render-only, schema and Compose checks repeated for the revision.
- Private healthchecks-ready.yaml prepared from the existing installed YAML,
  retaining credentials, storage and images. Subsequent VM pass is recorded below.

See HEALTHCHECK-TEST.md for the next VM test. Heartbeats do not prove successful
job execution; the scheduler lock does not detect a hung loop. Paused scheduling
is valid and is never changed by a probe. Docker marks unhealthy status but does
not automatically restart an unhealthy container. The local lab is stopped after
testing, retaining its disposable data.

## Same-image runtime guard revision

Healthcheck VM rollout: user reported HEALTHCHECK-TEST.md checks 1-5 passed on
2026-10-19. Raw VM logs were not independently inspected.

Added shared runtime locks, per-start site/image/upgrade-state verification, and
a non-root supervisor preserving the official image entrypoint and forwarding
shutdown signals. No database migration or marker/image transition is enabled.

Eleven Linux tests passed. Real WSL container checks verified that running
runtime blocks exclusive access, stopped runtime releases it, and exclusive
access blocks new runtime startup. Official render/schema/Compose checks were
repeated. Private runtime-guards YAML preserves the exact healthcheck baseline's
data services, storage, credentials and images. User subsequently reported all
RUNTIME-GUARD-TEST.md checks passed on 2026-10-19, including unchanged YAML save,
app restart, healthy services and retained data. Raw VM logs were not independently
inspected. This is not a catalog upgrade test.

All nine long-running services reported healthy after the guarded lab restart;
all six runtime probes also passed when invoked directly. The local lab was
stopped afterward. A redundant latest-image refresh stalled and was cancelled;
final official renderer/schema functions passed using the cached official image.

## Catalog same-version rehearsal

Added catalog-specific tooling, separate from scripts/prepare_upgrade.py and its
standalone storage assumptions. Only exact same-image v16 rehearsals are allowed.
The five-stage generator preserves installed images, credentials and mounts,
requires runtime guards, and refuses output overwrite. Backup/migration/resume
hold the runtime lock exclusively. Recovery files are outside the site's private
files tree; checksums are verified before migration and resume. Migration state
is persisted before bench migrate and an interrupted migration cannot retry.

Sixteen Linux tests passed (eleven catalog/runtime plus five rehearsal tests).
The mocked interrupted-command test establishes state-machine refusal, not actual
mid-patch database recovery. Corrupt backup and wrong-operation tests also passed.
All five prepared private VM stages passed Docker Compose config validation.

Two complete WSL rehearsal cycles passed: backup, deliberate pre-migration
failure, blocked initializer/runtime, actual same-version migration and guarded
resume. The second plan used the first successful resume YAML and preserved a
deliberately paused scheduler. A completed migration was refused as a repeat
(MIGRATION ALREADY COMPLETE). A backup attempted against active guarded runtime
was rejected before operation state was created.

Fictional ToDo and private File survived migration/resume; final backup gzip SQL
and private tar contents contained those fixtures and all inventoried checksums
matched. Nine persistent services and all runtime probes passed after resume.
The lab was then stopped. These checks do not establish independent restore,
encrypted credential recovery, image/patch upgrade, queue recovery, interrupted
patch recovery or native catalog update support.

VM follow-up on 2026-10-19: user reported the five-stage rehearsal, app stop/start
and VM restart passed, with a post-test snapshot created. A separate copy of the
recovery directory was not made. Results are user-reported; raw logs, recovery
inventory and snapshot were not independently inspected. Independent restore and
off-VM recovery preservation remain unverified. The successful 05-resume.yaml is
the baseline for subsequent plans.

## Independent restore clone

Nineteen Linux tests passed (eleven catalog/runtime, five rehearsal, three
restore). The clone generator rejects source-overlapping storage, source-port
reuse and image mismatches. It creates fresh database credentials and an explicit
separate network; only the restore job sees the source recovery directory, bound
read-only with automatic source-directory creation disabled. All three private
VM-stage files passed Compose config validation.

First local attempt was interrupted during SQL import (TLS unexpected EOF).
Persisted restoring state correctly blocked runtime; that failed destination's
data was retained and not retried. WSL idle shutdown was suspected, consistent
with Microsoft's documented systemd lifecycle. A fresh destination was tested
with a foreground WSL process kept active throughout initialization and restore.

The complete fresh-clone database/file restore and migration passed. A source
ToDo and private attachment were recovered, clone scheduling stayed paused,
destination-only and source-only records proved bidirectional isolation, and
clone restart retained data with six runtime probes passing. Source recovery
file checksums were unchanged afterward. Both local stacks were stopped.

VM independent restore passed by user report on 2026-10-19, including login with
the source credentials. Off-VM copy has not
been confirmed; SSH on the test VM was reachable but the user's first login was
rejected with publickey authentication. No automated VM login was attempted.
Encrypted-field decryption, real patch upgrade/failure recovery and native catalog
updates remain unverified. See REVIEW-DRAFT.md for an unposted scope-review draft.

WSL lifecycle reference: https://learn.microsoft.com/en-us/windows/wsl/systemd

## Same-content digest pinning

The VM's reported repository index digest a856e7f6... resolves through its amd64
manifest to config ID 0ce48f9b..., matching the reported running backend. The
explicit prepare_pinning.py helper preserves secrets, storage and dependency
images, requires the dedicated restore-test network and previous operation,
and supports only same-version, same-content tag-to-digest transitions.
The default catalog image guard is unchanged.

Twenty-three Linux tests cover catalog/runtime (11), restore (3), rehearsal (5)
and additional pinning cases (4). All five local pinning stages passed: backup,
intentional failure, blocked bootstrap with unchanged marker, migration and
guarded pinned resume. All nine persistent services became healthy. Prior
maintenance/scheduling flags were retained; source and clone-only ToDos survived,
and private attachment content matched the source. Unchanged-YAML recreation
passed and the local clone was stopped afterward.

The user reported the five VM stages passed, including the expected pinned
reference and unchanged image config ID. This is not a real patch-upgrade test.
Actual patch-failure recovery and native catalog updates remain unimplemented.

## Restore of the same-content pinning backup

The restore helper now accepts catalog-upgrade-v1 manifests only when the source
version, target digest and observed source proof describe the same content. It
continues to support catalog-rehearsal-v1. Unknown layouts and differing versions,
digests, operation IDs or backup status are rejected before database changes.
Only two explicit disposable destination app names are supported; overlapping
source storage/network/port is rejected. The new pinned-recovery app has its own
network, database credentials, storage and port 18086. Source backup is read-only.

Twenty-six distinct Linux tests pass (11 catalog/runtime, 6 restore, 9 combined
rehearsal/pinning), including pinning manifest validation, deployment isolation
and refusal to retry an interrupted restore before invoking database commands.
All three private VM recovery stages pass Compose validation. The full local
fresh initialization, pinned-backup restore and resumed startup passed. Backup-era
records and private attachment bytes recovered; post-backup source data was absent,
scheduling stayed paused, and the source recovery checksums remained intact.
Unchanged-YAML recreation retained the recovery-only record and returned all nine
persistent services healthy; the local recovery app was stopped afterward.
VM recovery is pending CATALOG-PINNED-RECOVERY-TEST.md, with files prepared in
generated/catalog-pinned-recovery-01/. Existing VM apps have not been changed.

## Verified image pins in the catalog defaults

The user subsequently reported the pinned-backup VM recovery procedure passed
in full. They supplied MariaDB and both Redis containers' configured references,
config IDs and RepoDigests. Registry linux/amd64 manifest inspection confirmed
the reported config IDs; IMAGE-REVIEW.md records them. Catalog ix_values.yaml
now pins ERPNext, MariaDB and Redis to those verified repository digests.
Existing private deployment YAML was not regenerated or modified.

Twenty-six Linux regressions passed after the default change. Legacy restore
fixtures retain their installed tag references, and the restore generator now
explicitly preserves source image references for all three dependencies while
rejecting unsupported versions. A local recovered site started with all three
digest pins, retained its recovery-only record and paused scheduling, and all
nine persistent services became healthy; the local stack was stopped afterward.

The cached official validator passed app rendering, Compose config and scoped
validate_dev_directory_structure checks using FAKE_ENV=1. The CI wrapper's
mandatory latest-validator pull stalled and was stopped; that wrapper rerun did
not complete. These direct official checks do not imply full CI or metadata
acceptance. Full metadata remains blocked on the empty icon URL; native upgrades,
encrypted-field decryption and actual interrupted-migration recovery remain work.

## Actual same-image migration interruption

Twenty-nine distinct Linux tests passed: catalog/runtime (11), restore (6),
rehearsal (5), additional pinning (4) and interruption guards/planning (3).
Same-image rehearsal now supports digest-pinned references and verifies previous
restored-operation identity. Acknowledgement and phase checks protect the
test-only ephemeral hook wrapper; the catalog template does not include it.

In the local disposable recovery clone, a real bench migrate before_migrate hook
committed a ToDo fixture and waited. Killing only that container returned 137.
Durable state remained migrating; a read-only DB diagnostic confirmed the fixture
was committed. Both migration retry and normal runtime startup were blocked.
The interrupted source was left stopped with its state and backup intact.

A fresh independent destination initialized, restored the pre-interruption
backup and resumed. Pre-test records and private attachment bytes recovered;
the committed interruption fixture was absent, scheduling remained paused,
and source recovery inventory hashes still matched. Unchanged-YAML recreation
retained that data, the partial fixture remained absent and all nine persistent
services became healthy. Both local test stacks were stopped; failed-source
evidence was retained. VM execution remains pending
CATALOG-INTERRUPTION-TEST.md. Four interruption and three recovery files are
prepared privately and pass Compose configuration validation.

This proves this controlled same-image committed-hook interruption and separate
restore path. It does not prove recovery from every DDL/versioned patch failure,
external side effects, encrypted fields, queue draining or native catalog updates.

VM follow-up: the user reported all interruption/recovery checks passed. After
restart, 18086 remained crashed/blocked and 18087 was working; no other apps were
running. Record this as user-reported evidence, not independent log inspection
or a fresh restart check of 18084/18085. The working baseline is
generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml, with app
name erpnext-catalog-interrupt-recovery-test. Retain failed 18086 state and backup.

## Single-deployment coordinator prototype

Thirty-four distinct Linux tests pass, including five coordinator-specific tests
for sequencing, lifetime exclusion, idempotence, migration/resume failure handling
and source configuration preservation. The helper targets only the successful
interruption-recovery clone and preserves images, credentials, storage and port.
The one private VM YAML passes Compose validation.

Real local runtime holding shared locks rejected coordinator startup with
BlockingIOError before its previous restore state changed. After stopping that
runtime, one deployment completed backup, migration, original initialization and
durable resume while holding the exclusive lock throughout. Unchanged-YAML
recreation reused the same completed backup/migration, preserved the recovery
manifest, recovered records/private attachments and paused scheduling, and all
nine persistent services became healthy. The local clone was stopped afterward;
the earlier failed source remains stopped with evidence retained.

The default catalog template is unchanged. This is a same-image coordinator and
Compose dependency-graph test, not a native catalog upgrade or image-version
transition. VM execution is pending CATALOG-COORDINATOR-TEST.md using
generated/catalog-coordinator-01.yaml on 18087. The user separately confirmed
the failed 18086 app has no running containers despite its Crashed UI label.

VM follow-up on 2026-10-20: the user reported all coordinator guide checks passed.
The current working 18087 baseline is generated/catalog-coordinator-01.yaml.
This is user-reported evidence, without independently collected VM logs.

## Bounded real patch graph and source-version recovery

Forty distinct Linux tests pass, including six patch-specific checks for the
exact image pair, source/target version phases, failed-migration state, integrity,
durable marker commit, repeated execution and source-version recovery selection.
The default catalog guard is unchanged. The private graph permits ONLY:

- v16.51.0 index f2d409c5..., amd64 config e43ea1a1... as source.
- v16.51.1 index a856e7f6..., amd64 config 0ce48f9b... as target.

Registry manifests and the downloaded source image confirmed these identities;
full references are recorded in patch_policy.py. A new isolated older-version
site was initialized; no existing DB was downgraded. It received a ToDo, private
attachment and synthetic __Auth encrypted-secret fixture before backup.

The real graph ran source-image offline backup before target-image migration.
Managed marker/state checks and exclusive locks block old runtime during the
handoff. Target identity was committed only after successful migration and
verification of the official baked-asset symlink. The upgraded site reported
ERPNext 16.51.1, retained its record/private content and decrypted the fixture.
Login HTML and three referenced CSS/JS assets returned HTTP 200. Recreating the
upgrade graph reused completed backup/migration and returned healthy.

A separate fresh old-version destination restored the pre-patch backup through
a read-only source mount. It reported ERPNext 16.51.0 and recovered the record,
exact private content and encrypted fixture with successful decryption; scheduling
was paused. Its restart returned nine healthy persistent services. Both local
patch apps were stopped, retaining source backup and recovery data.

Five private VM YAML files pass Compose validation. VM execution is pending
CATALOG-PATCH-TEST.md: NEW 18088 patch source and NEW 18089 old-version recovery,
leaving 18087 unchanged. This is a specific real patch pair and synthetic secret
fixture, not arbitrary patch/DDL failure, all real encrypted credentials, queue
draining, automatic rollback or a native catalog update test.

VM follow-up: the user reported all CATALOG-PATCH-TEST.md checks passed on
2026-10-20. Version transition and source-version recovery are user-reported
passes; local synthetic-secret decryption is not extrapolated to the VM.

## Worker warm shutdown and queue migration gate

The supervisor now forwards worker signals to the actual worker PID (bench
execs it), protecting its job child from group SIGTERM. Other runtime process
groups retain signal forwarding. Both worker services have 120-second grace.
New backup/migration runs require empty queued/started/deferred/scheduled/failed
work, inspected without registry cleanup, before writing new operation state.
Already-completed operations retain idempotent normal restart behavior.

Forty-four distinct Linux tests pass. A real active job finished during worker
SIGTERM stop (worker exit 0). A full-app stop also allowed active work to finish;
restart verified finished status and the empty queue passed inspection. A
deliberate forced worker stop (exit 137) left a started job, and the gate refused
it. The lab was stopped with that fixture and Redis evidence retained. Do not
silently clean or restart that local failure fixture as if it were a fresh lab.

Cached official scoped schema, app rendering and Compose validation pass. The
private VM update preserves image/storage/credential/operation identities and
passes Compose validation. VM execution is pending CATALOG-WORKER-SHUTDOWN-TEST.md
with generated/catalog-worker-shutdown-01.yaml on 18088. Default catalog image
changes/native upgrades remain blocked; this is bounded warm stop plus strict
queue review, not unlimited drain or automatic replay/side-effect recovery.

## TrueNAS UI save request size

On 2026-10-23 the user reported immediate TrueNAS logout on Save, with no YAML
update persisted. The original normalized YAML's JSON string measured 65,962
characters before request fields. TrueNAS TS-25.10.7 utils/limits.py sets the
authenticated message cap to 65,536 and raises MESSAGE_TOO_BIG; app.update is not
an extended-size exception. This strongly matches the symptom, though no VM log
was independently collected.

The replacement generated/catalog-worker-shutdown-01.ui-safe.yaml retains all
service definitions, credentials, scripts, operation IDs and storage. Only the
unreferenced catalog_bootstrap config is omitted. Standard YAML anchors/literal
blocks reduce JSON size to 54,318 LF / 57,116 CRLF characters. Both files expand
to identical Compose models after unused config removal. Four serializer tests
pass, including round-trip secrets/scripts, anchor equivalence, config references
and rejection of oversized output. The worker generator now enforces a 60 KiB
JSON-string budget, including CRLF, leaving room for app.update fields.
VM save retry is pending; no host message-size limit was changed.

Source: https://github.com/truenas/middleware/blob/TS-25.10.7/src/middlewared/middlewared/utils/limits.py
