> User confirmed browser login and the expected version on the upgraded test app. Candidate acceptance is complete for the documented scope; upstream icon/CI and review remain pending.

> Automated update testing: [2026-10-28 report](docs/reviews/UPDATE-16.52.1-AUTOMATED-TESTS.md). Native install/upgrade/failure/recovery, local Docker and actual VM reboot checks passed. Read the report before doing more tests.

> Current local update work: [ERPNext 16.52.1 candidate](docs/reviews/UPDATE-16.52.1.md). Local-only update branches; submitted PR unchanged. No Docker/VM acceptance tests yet. This note supersedes baseline-only next-step statements below.

> Submitted on 2026-10-26: [TrueNAS apps draft PR #6267](https://github.com/truenas/apps/pull/6267), targeting master from domocorn:erpnext-catalog-draft.
> This supersedes references below to an unposted PR or pending publication authorization. Maintainer review and an approved CDN icon URL remain outstanding; catalog inclusion has not been accepted. No further manual VM test group is requested now.

# Current handoff — 2026-10-26

Workspace: D:\Users\Dominic\Documents\_04 Tech & Coding\GitHub.
Repositories: erpnext-truenas and apps, both on erpnext-catalog-draft. The user
authorized committing and pushing both origin branches on 2026-10-26. GitHub CLI
is authenticated as domocorn. Opening a PR is a separate action. No subagents requested.
Production NAS untouched. Disposable VM: 172.22.237.80, truenas_admin,
TrueNAS-25.10.7, catalog /mnt/.ix-apps/truenas_catalog. SSH password access is
manual; no accepted unattended key. Never request passwords in chat.

USER-REPORTED VM LIFECYCLE GROUPS COMPLETE, including native install/patch/restart,
actual migration failure blocking and independent recovery/restart. Working
normal native app erpnext-native-test:18090 (1.0.0); its overlay was removed.
Failed erpnext-native-failure-test:18091 stays Crashed/migrating; preserve guards.
Recovered erpnext-native-recovery-test:18092 uses source ERPNext 16.51.0 and paused
scheduling. Final verification reported original record/private attachment and
synthetic encrypted value preserved, failed-migration record absent, independent
storage/database password and failed source preserved; repeated after restart.
Original backup and /mnt/labpool/erpnext-native-recovery-input-01 private copy stay.

Normal native code is NOW integrated into apps/ix-dev/community/erpnext. Its final
render matches the tested normal graph except x-notes. No lab failure/recovery
hook ships in the default entry. Old custom-YAML generators/tests explicitly use
render_catalog.render_legacy to preserve their historical protocol; native form
defaults enable consts.native_lifecycle. Builder supports already integrated base.
Native helpers embedded in macros are generated from catalog-dev canonical files.

Final isolated official validation workspace:
/var/tmp/erpnext-final-catalog-validation-01. Scoped schema, official library/hash,
render, Compose and official metadata analysis passed; generated fields applied.
The vendored library is unchanged and matches official output. Library2.3.17 is
still the latest upstream2.x by current API check. Linux regression suites passed.
All local Docker test stacks are stopped, with data preserved.

BLOCKER: full metadata generator rejects icon:''; actual expected ERPNext CDN
URL is 404. Assets/erpnext-logo.png is an unmodified upstream candidate. Current
CONTRIBUTIONS explicitly permits attaching artwork in a PR for reviewer CDN
upload. Ready for DRAFT REVIEW, not a full-CI/merge-ready claim. No fake URL.
Read docs/submission/SUBMISSION-PREPARATION.md and docs/submission/REVIEW-DRAFT.md. PR publication requires user
publication instruction; after real icon URL, regenerate metadata/full validation.

Only exact reviewed ERPNext16.51.0->16.51.1 pins are enabled; general ERPNext
upgrades, dependency upgrades, production/business-data readiness, automatic
rollback and HexOS curation are not established. See ../docs/TEST-RESULTS.md.

Previous detailed handoff and next-step status are preserved under docs/history/.
Do not restart completed VM test groups or delete generated plans/recovery data.
