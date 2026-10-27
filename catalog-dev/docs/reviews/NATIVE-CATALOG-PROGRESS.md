# Native catalog integration checkpoint — 2026-10-23

Current result, 2026-10-26: the native install/upgrade and failure/recovery groups
both passed by user report, including recovered-app restart. The normal lifecycle
is integrated into the default catalog draft. See
[submission preparation](../submission/SUBMISSION-PREPARATION.md) for the remaining
icon/review work. The dated checkpoints below are historical; do not repeat them.

Earlier checkpoint: the separate NATIVE-FAILURE-RECOVERY-TEST.md group is prepared as
generated/erpnext-native-failure-recovery-01.tar.gz. Its three catalog profiles
passed official schema/index, render and Compose checks. An actual local committed
patch failure, blocked unchanged restart, independent old-image native restore,
record/private attachment/encrypted-value checks and recovery restart passed.
The failed source is preserved and both local Docker stacks are stopped. Six new
native restore/host isolation tests and affected regressions passed. The VM group
is pending; it uses different app names/storage on 18091 and 18092 and a separate
staging record, so the earlier overlay removal does not prevent this test.

The user reported NATIVE-CATALOG-TEST.md passed in the actual VM, including
native version 1.0.0 Running/custom_app false/no upgrade pending and successful
overlay removal. The installed app and backup on 18090 are preserved. Native
failure/recovery is now the next group; earlier pending-VM statements below are
historical checkpoints.

User confirmed TrueNAS-25.10.7 and catalog location
`/mnt/.ix-apps/truenas_catalog` on the disposable VM at 172.22.237.80.
No VM catalog files have been changed, and no submission has been made.

The user reported all worker-shutdown procedure checks passed, including the
smaller UI-safe YAML save and subsequent unchanged restart. The observed job
finished and the queue gate passed. Whether that job was still active at the
instant Stop was clicked is uncertain; do not claim VM active-job drain proof.

## Implemented locally

`build_native_candidate.py` builds an isolated `erpnext-native-lab` app from the
real catalog template. Native hooks add source-image backup before target-image
initialization, a stable operation ID derived from site/image, exclusive storage
locking, queue gating, target-marker commit after migration, and unchanged-start
verification. Only the reviewed 16.51.0 to 16.51.1 digest pair is allowed.
The default app has not been switched to these experimental hooks.

Linux `test_native_lifecycle.py --apps-root ../../apps` passed all nine executed
tests (four native cases and five inherited rehearsal cases). They cover fresh
and repeated initialization, the reviewed upgrade, interrupted migration refusal,
and refusal of downgrade or unrecognized initialized storage.

An actual isolated Docker deployment completed source fresh installation,
source-image backup and target migration. Verification confirmed ERPNext 16.51.1,
a preserved ToDo, exact private attachment bytes and synthetic encrypted-value
decryption. This is local integration evidence, not a native middleware VM test.
The project `erpnext-native-test` is now stopped; storage remains at
`/mnt/erpnext-wsl-lab/catalog-native-integration`.

## Packaging checkpoint

Isolated WSL catalog roots:

- `/var/tmp/erpnext-native-source-catalog` (app version 0.9.0)
- `/var/tmp/erpnext-native-target-catalog` (app version 1.0.0)

The source passed official scoped development validation and official publication
to `trains/community/erpnext-native-lab/0.9.0`. Regenerating hashes and republishing
resolved a stale published library-hash mismatch. Index generation then failed
the catalog schema because `last_update` is null for this non-Git lab root.
The cached official updater itself contains a FIXME about its last-update field.
Target publication/index generation remains to be completed; do not call these
roots ready-to-install native catalogs. Final icon/full metadata work also remains.

## Packaging completed later on 2026-10-23

The earlier packaging errors above are resolved for the lab bundle. A clean
build with Python bytecode disabled preserves the official library hashes.
`package_native_index.py` uses an explicitly recorded UTC build timestamp in
place of Git-derived dates for this uncommitted lab build. It still calls the
official index generator and its catalog/version schema validators; no Git
history or maintainer approval is implied.

`build_native_bundle.py` generated the secret-free
`generated/erpnext-native-lab-01.tar.gz`. Its source 0.9.0 and target 1.0.0 each
passed official scoped development validation, official publication, healthy
catalog/version-index generation, official rendering and Docker Compose config
validation. The complete local lifecycle regression suite passed, along with
four overlay ownership/recovery tests. An actual unchanged target restart also
passed: it reported MIGRATION ALREADY COMPLETE and retained one recovery backup.
The isolated local Docker app is stopped again, with data preserved.

`native_catalog_lab.py` stages only the lab app on the exact disposable release
and catalog path, saves the original index, checks owned entries/file hashes,
preserves unrelated catalog changes, and provides removal of its own overlay.
Its journal supports removing a partially staged operation. It does not prevent
an external catalog sync; do not sync during the test. The script has local
filesystem tests but has not yet been executed on the actual VM.

Next: follow NATIVE-CATALOG-TEST.md starting at step 1. This is the native catalog
test group, using Discover Apps and Upgrade. After it passes, the remaining groups
are native failure/recovery and final catalog acceptance checks. The final app
integration, icon/full metadata, submission preparation and user-authorized
publication remain; the lab bundle is not the final catalog contribution.
