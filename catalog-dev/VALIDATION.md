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
patch recovery or native catalog update support. VM rehearsal remains pending;
follow CATALOG-REHEARSAL-TEST.md.
