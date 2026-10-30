> Published thin revision: apps commit `6ee726510ddfb436734f858b54c0c13f37943aa1`, seven tracked app files. Reviewer reply: https://github.com/truenas/apps/pull/6267#issuecomment-6525202369 . PR description updated; runtime validation remains pending. Archive branches preserve the prior implementation.

> Current architecture: [thin upstream integration](docs/reviews/THIN-INTEGRATION-REVIEW.md), replacing the guarded framework after maintainer feedback. Manual site setup/operations; no app-internal scripts shipped. Old acceptance results are historical and do not validate this rewrite. Runtime tests pending because the VM is unreachable and WSL cannot start.

> Published: tested 16.52.1 update pushed to submission and update branches in both repositories. PR #6267 now targets apps commit 6e06135e8711956392f602cb01ce70209270b916; description and test evidence updated. Review request: https://github.com/truenas/apps/pull/6267#issuecomment-6472245993 . This supersedes earlier local-only restrictions. PR remains a draft; full CI/icon and review are pending.

> User confirmed browser login and the expected version on the upgraded test app. Candidate acceptance is complete for the documented scope; upstream icon/CI and review remain pending.

> Automated update testing: [2026-10-28 report](docs/reviews/UPDATE-16.52.1-AUTOMATED-TESTS.md). Native install/upgrade/failure/recovery, local Docker and actual VM reboot checks passed. Read the report before doing more tests.

> Current local update work: [ERPNext 16.52.1 candidate](docs/reviews/UPDATE-16.52.1.md). Local-only update branches; submitted PR unchanged. No Docker/VM acceptance tests yet. This note supersedes baseline-only next-step statements below.

> Submitted on 2026-10-26: [TrueNAS apps draft PR #6267](https://github.com/truenas/apps/pull/6267), targeting master from domocorn:erpnext-catalog-draft.
> This supersedes references below to an unposted PR or pending publication authorization. Maintainer review and an approved CDN icon URL remain outstanding; catalog inclusion has not been accepted. No further manual VM test group is requested now.

# Current next steps — 2026-10-26

The planned native lifecycle VM tests are complete by user report, including
failed-migration blocking, independent recovery, login and recovered-app restart.
No further manual VM test group is requested now. Preserve the apps and backups.

The normal native lifecycle is integrated into the actual catalog draft at
`apps/ix-dev/community/erpnext`. Its service/script/image/storage/dependency model
matches the tested native graph; only explanatory notes differ. Regression,
official scoped schema, rendering, library/hash and Compose checks passed.

Read [SUBMISSION-PREPARATION.md](docs/submission/SUBMISSION-PREPARATION.md) for the final review
result and publication steps. [REVIEW-DRAFT.md](docs/submission/REVIEW-DRAFT.md) contains the local,
unposted draft PR description. Artwork is ready in assets/erpnext-logo.png.

Full metadata validation is blocked on the approved TrueNAS CDN icon URL. The
contribution guide allows artwork to be attached to a draft PR for the reviewer
to upload. This is ready for draft review, not merge-ready or fully green CI.
After the reviewer supplies the URL, regenerate metadata and rerun full checks.

The user authorized committing and pushing both `erpnext-catalog-draft` branches
on 2026-10-26. GitHub authentication is confirmed. Creating a draft PR or sending
maintainer messages remains a separate action; no PR has been opened.
Generated YAML, credentials and recovery material remain private and ignored.

The Windows workspace is:
`D:\Users\Dominic\Documents\_04 Tech & Coding\GitHub`.
See [../WORKSPACE.md](../WORKSPACE.md) for the two repositories and folder handling.
Historical instructions are retained under docs/history/; do not repeat their tests.
