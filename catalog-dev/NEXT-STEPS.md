# Catalog preparation after the VM test

The first rendered deployment passed README step 5 according to the user.
This establishes fresh-install behavior only. Keep that VM installation intact
while validating new revisions separately.

Completed so far: Ubuntu WSL Docker setup, all four Linux tests, official scoped
library vendoring/hash, item.yaml generation, official app-scoped schema check,
official CI render-only (metadata skipped), and Compose config validation.
See VALIDATION.md for exact limits. Full metadata is blocked on the icon URL.

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
