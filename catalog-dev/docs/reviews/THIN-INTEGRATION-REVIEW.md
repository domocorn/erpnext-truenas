# Thin catalog integration - 2026-10-30

Stavros-k requested changes to PR #6267 because the catalog should not maintain
scripts implementing app internals. The previous scripts were intentional, but
their ownership boundary was wrong for this contribution. This revision removes
that framework rather than moving or obscuring it in another generated file.

## Current design

- Catalog package 2.0.0; unchanged ERPNext 16.52.1 / Frappe 16.53.0 image pin.
- Eleven services: normal TrueNAS library permissions, MariaDB, two Redis
  instances, upstream configurator and six upstream runtime services.
- No custom Python code, mounted app scripts, runtime wrappers, identity markers,
  storage locks, automatic backup/migration/recovery, RQ inspection or signal supervisor.
- The only configurator command block follows upstream `compose.yaml`: `ls apps`
  and `bench set-config` for connection settings. It uses bash `-e` for command failure.
- Image entrypoints and normal upstream runtime commands are used directly.
- First site creation is manual via upstream `bench new-site` in the backend shell.
  Administrator passwords are entered interactively, not collected in the form.
- Backup/upgrade/restore are explicitly operator-managed upstream procedures.
  Startup no longer provides interrupted-migration exclusion or automatic rollback.
- Use fresh storage; this is not an in-place update for guarded prototype apps.
- Custom app health code is gone; DB/Redis checks and the library TCP frontend
  probe remain. Worker/backend/websocket/scheduler health introspection is disabled.
- Generated base-library copies/tests were removed from Git tracking. Upstream
  tooling prepares them from `library/`; the hash now matches the current repository.

Reference reviewed:
https://github.com/frappe/frappe_docker/blob/61d35da827ebc04d01b64c9e78385597ccebc9d8/compose.yaml
and that commit's `pwd.yml` and `docs/04-operations/01-site-operations.md`.
The upstream example's insecure default passwords and floating tags are not used.

## Preservation

Both repositories have pushed archive branches named
`archive/erpnext-guarded-lifecycle-2026-10-30`. Earlier tests and recovery evidence
refer to that design only. Historical helper scripts retained in this development
repository are not shipped in the catalog and must not be used against the thin
entry. `test_catalog.py` now runs the thin render suite; old tests are on the archive.
Existing VM apps, datasets, recovery state and production were not changed.

## Validation and limits

- Three Windows render tests passed with the actual repository library: service
  graph/entrypoint boundaries, upstream commands/dependencies, storage/ports,
  matching image pins and literal dollar-sign passwords.
- Official repository metadata analyzer and question/image/app-library validators
  passed using the local renderer as input. Metadata users/capabilities regenerated.
- The only rendered config is standard library permissions JSON, not application code.
- Full metadata still rejects the absent approved CDN icon URL. No fake URL added.
- Runtime/Compose-daemon/native acceptance for this revision is PENDING: the
  disposable VM at 172.22.237.80 timed out and local WSL could not start. This is
  an environment limit, not a runtime pass. Earlier guarded-framework acceptance
  results are explicitly not attributed to this different architecture.

Before declaring this ready, get maintainer agreement on the reduced integration
and manual site-setup model, then test fresh install, manual site creation,
login/assets, job execution, backup and unchanged restart in new isolated storage.
Any manual upgrade/restore support needs its own upstream-procedure rehearsal.
Keep the PR a draft pending that work, full CI and approved artwork.

Publication: thin revision pushed as apps commit `6ee726510ddfb436734f858b54c0c13f37943aa1`.
Reviewer response: https://github.com/truenas/apps/pull/6267#issuecomment-6525202369 .
