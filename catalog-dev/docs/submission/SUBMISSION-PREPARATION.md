> Submitted on 2026-10-26: [TrueNAS apps draft PR #6267](https://github.com/truenas/apps/pull/6267), targeting master from domocorn:erpnext-catalog-draft.
> This supersedes references below to an unposted PR or pending publication authorization. Maintainer review and an approved CDN icon URL remain outstanding; catalog inclusion has not been accepted. No further manual VM test group is requested now.

# Draft submission preparation — 2026-10-26

The planned lifecycle VM groups are complete by user report. The normal native
lifecycle is integrated into `apps/ix-dev/community/erpnext`; the test-only failure
hook and recovery helper are not included in that catalog entry.

## Reviewable result

- The final render's services, scripts, images, dependencies, storage and ports
  match the VM-tested normal native graph. Only explanatory notes differ.
- The Linux catalog/lifecycle/restore/queue/isolation/serializer suites passed.
- Official app-scoped schema, library vendoring/hash comparison, rendering and
  Docker Compose validation passed in an isolated final-validation workspace.
- Metadata service/user/capability fields were derived from the official analyzer.
  The current upstream library remains 2.3.17, matching this draft.
- Native failure/recovery, recovered login and unchanged recovery restart passed
  by user report on TrueNAS 25.10.7 / amd64. Recovery used a private, verified copy
  outside `.ix-apps`, because TrueNAS forbids host-path mounts of internal storage.

The final validation workspace is `/var/tmp/erpnext-final-catalog-validation-01`
inside Ubuntu WSL. Historical custom-YAML fixtures use an explicit development
`render_legacy` helper. The actual catalog defaults enable native lifecycle;
legacy rendering is not exposed as an installation-form option.

## Remaining external metadata item

Full metadata validation currently fails with `Invalid icon URL` because the
icon field is empty. The expected ERPNext CDN URL returned 404 on 2026-10-26.
No fabricated or unapproved CDN URL has been inserted. The unmodified upstream
artwork is ready in [assets/erpnext-logo.png](../../assets/erpnext-logo.png), with
provenance in [assets/README.md](../../assets/README.md).

The [current contribution guide](https://github.com/truenas/apps/blob/master/CONTRIBUTIONS.md)
allows artwork to be attached to the PR; the reviewer uploads it to the CDN and
provides the correct URL. Therefore this is ready for **draft maintainer review**,
not a claim that full CI is green or that the catalog contribution is merge-ready.
After the reviewer supplies the URL, set it, regenerate metadata and rerun full
metadata/CI checks on that final revision.

## Publication plan

1. Review and commit development source/docs/tests in `erpnext-truenas`, then
   push its working branch so the evidence and test tools can be linked.
2. Review and commit only `ix-dev/community/erpnext` changes in the `apps` fork,
   then push its working branch.
3. Open a **draft** PR to `truenas/apps` using [REVIEW-DRAFT.md](REVIEW-DRAFT.md),
   attach the artwork and state the metadata/icon blocker explicitly.

The user authorized committing and pushing both working branches on 2026-10-26;
GitHub CLI authentication as domocorn is confirmed. Opening the draft PR remains
a separate action and has not been performed. Do not send tokens or passwords
in chat.
Keep private generated YAML, recovery archives, `.env` files and virtual
environments out of both commits. The TrueNAS contribution contains the app's
source and official vendored library, not published `trains/` or catalog indexes.

Current upstream issue search returned Frappeverse #174 open, ERPNext #3496 closed
and no ERPNext PR. Recheck when publishing. Maintainer acceptance, future ERPNext
image pairs, dependency upgrades and HexOS curation remain separate work.

## VM preservation

Preserve the successful native app on 18090, failed source on 18091, recovered
app on 18092, original recovery backup and private permitted-path input copy.
No further manual VM test group is requested now. Do not clear the failed source's
guards or delete recovery material during repository cleanup.
