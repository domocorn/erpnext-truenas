# Historical next-steps snapshot — 2026-10-23

Superseded by ../NEXT-STEPS.md. Paths in the snapshot refer to catalog-dev, not this history directory. Retained as evidence; do not follow it as current instructions.

2026-10-23 current checkpoint: worker procedure passed by user report; active-job timing at VM Stop remains uncertain. Native catalog lab packaging is COMPLETE. generated/erpnext-native-lab-01.tar.gz contains schema-validated source/target catalog packages and a reversible single-app staging tool. Official renders, Compose validation, local lifecycle regressions, overlay ownership/recovery tests and actual unchanged native-graph restart passed. NEXT USER STEP: NATIVE-CATALOG-TEST.md step 1 on the disposable VM. Native VM installation/upgrade has not yet run. See NATIVE-CATALOG-PROGRESS.md. This checkpoint supersedes earlier pending-worker and pending-packaging statements below.

# Catalog preparation after the VM test

The first rendered deployment passed README step 5 according to the user.
This establishes fresh-install behavior only. Keep that VM installation intact
while validating new revisions separately.

Completed so far: Ubuntu WSL Docker setup, all four Linux tests, official scoped
library vendoring/hash, item.yaml generation, official app-scoped schema check,
official CI render-only (metadata skipped), and Compose config validation.
See VALIDATION.md for exact limits. Full metadata is blocked on the icon URL.

HEALTHCHECK-TEST.md checks 1-5 passed in the user's VM on 2026-10-19.
RUNTIME-GUARD-TEST.md checks 1-6 also passed in the user's VM on 2026-10-19.
The same-image runtime guard baseline is now verified by user report.
Catalog-layout offline backup, exclusive migration locking, same-version
rehearsal and guarded failure/resume stages are now implemented and tested in
the disposable WSL lab. The user also reported the five-stage VM rehearsal,
app stop/start and VM restart passed on 2026-10-19, and created a post-test
snapshot. A separate recovery-directory copy was not made. Preserve that
directory privately before further destructive experiments. Independent restore
to separate lab storage passed locally and the user reported all VM restore
checks, including login with source credentials, passed on 2026-10-19.
The user subsequently reported all VM pinning checks passed, with the expected
digest-pinned reference and unchanged image config ID. The user also reported
CATALOG-PINNED-RECOVERY-TEST.md passed, including recovery into the separate app
on port 18086. Subsequently CATALOG-INTERRUPTION-TEST.md passed by user report:
18086 remained crashed/blocked after restart, 18087 worked and no other apps
were running. The working recovered baseline is now
generated/catalog-interruption-recovery-01/03-start-restored-clone.yaml for
erpnext-catalog-interrupt-recovery-test (39 characters). Preserve the interrupted
18086 app's state and backup; do not apply its older successful YAML or clear
guards. The user confirmed 18086 has no running containers (only Created/Exited);
its Crashed UI label is expected. No repetition of these procedures is needed.
CATALOG-COORDINATOR-TEST.md subsequently passed by user report on 2026-10-20;
the current 18087 baseline is generated/catalog-coordinator-01.yaml.
Next is CATALOG-PATCH-TEST.md: create NEW 18088 source at v16.51.0, upgrade it
to v16.51.1 with the exact reviewed digest pair, then recover its pre-patch backup
into NEW old-version storage/app on 18089. Files are under generated/catalog-patch-01/
and generated/catalog-patch-recovery-01/. These VM patch/recovery tests passed
by user report on 2026-10-20. Current 18088 baseline remains the successful
generated/catalog-patch-01/02-upgrade.yaml until the next update passes; 18089
uses catalog-patch-recovery-01/03-start-restored-clone.yaml.
Next: CATALOG-WORKER-SHUTDOWN-TEST.md with the single private
generated/catalog-worker-shutdown-01.ui-safe.yaml on 18088. The original file
exceeded the TrueNAS request-size cap after JSON encoding and was not saved;
the smaller equivalent replacement is validated locally, VM retry pending.
This tests active-job warm
shutdown and read-only queue migration checks. Keep 18087 unchanged.
This is a custom-app patch graph, not native catalog upgrade support. The original apps on
18084/18085 were not newly verified in this latest test.
RECOVERY-COPY.md provides SSH/archive/download commands for 172.22.237.80.
Use the successful
generated/catalog-rehearsal-01/05-resume.yaml as the current installed baseline.
The clone now uses generated/catalog-pinning-01/05-resume.yaml.
The catalog fresh-install defaults now pin ERPNext, MariaDB and Redis to the
verified image digests. This changes future renders, not existing VM YAML.
General image upgrades and native one-click upgrades remain blocked. The explicit
pinning helper permits only the same version and observed repository content.
See LIFECYCLE-REVIEW.md.

## Remaining work packages before an update-ready submission

1. Independent restore VM test passed; preserve recovery material outside the VM
   when possible (copy completion remains unconfirmed).
2. Digest transition, controlled same-image interruption recovery and coordinated
   same-image deployment passed in the VM. The exact real patch pair, source-image
   backup recovery passed in the VM by user report; synthetic encrypted-secret
   decryption passed locally. Warm worker/full-app stop and forced-stop queue
   refusal now pass locally; their VM procedure is next. General patch/DDL-failure
   recovery, real integration credentials and native catalog integration remain.
   The private patch graph does not enable native one-click catalog upgrades.
3. Finish packaging: icon/CDN coordination, full generated metadata, current
   upstream policy review and complete official validation of the final revision.
4. Submit for maintainer review only with user authorization; address feedback.

An early architecture/scope review can happen before all of this is complete.
REVIEW-DRAFT.md is a prepared but unposted draft with explicit evidence limits.
There is no fixed number of test cycles or guarantee of catalog acceptance.
IMAGE-REVIEW.md records observed digests and the marker transition constraint.

## Submission preparation

- Use the official `ghcr.io/truenas/apps_validation` container for library
  vendoring and full schema/render validation. Never hand-copy library modules.
- Generate metadata with the checkout's `.github/scripts/generate_metadata.py`,
  scoped to `--train community --app erpnext --no-bump` while this is unpublished.
- An empty icon is an actual metadata failure. Prepare an upstream-derived icon
  for reviewer upload; do not invent a live TrueNAS CDN URL to pass validation.
- Review immutable image digests against the exact tested tags and architecture.
  Pinning a digest must preserve the bootstrap image marker's identity across
  unchanged deployments. Never regenerate existing deployment credentials.
- Add and exercise frontend/backend/websocket and worker/scheduler health probes.
  Worker probes must distinguish a live process from working Redis/database
  connectivity. A healthy backend alone does not prove workers are healthy.
- Recheck https://github.com/truenas/apps/issues/174 and
  https://github.com/truenas/apps/issues/3496 before proposing a submission.
  The initial public issue search returned no matching ERPNext PR.

## Catalog upgrades are a separate implementation milestone

Before relaxing the bootstrap image guard, verify TrueNAS's actual update order
and prove that old schedulers and workers have stopped before any database patch.
A Compose dependency only orders containers in the new deployment and does not
prove old-version containers have stopped.

Required sequence: stop/drain runtime, capture an offline database/files/config
backup, persist an operation ID and target image, migrate once under an exclusive
lock, persist success, then start target runtime and restore prior maintenance and
scheduler settings. Every runtime startup must verify the operation's state.
Failures must leave runtime blocked and preserve backup and diagnostic evidence.

Test with fictional data: same-version migration, a real patch transition,
failure before migration, actual interrupted migration, repeated save/restart,
backup restore to a separate deployment, and old/new worker exclusion. Database
patch failure requires explicit restore recovery; there is no automatic rollback
claim. Do not transfer the standalone prototype's upgrade results to this layout.

Only after these checks should a reviewed community-train submission be prepared.
Posting, PR submission and HexOS curation remain separate user-authorized actions.
