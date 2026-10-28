# ERPNext 16.52.1 automated acceptance - 2026-10-28

Executed directly by Codex over the dedicated SSH connection to disposable
TrueNAS 25.10.7 at 172.22.237.80. Production was not accessed. Both update
branches remain local; the submitted branches and PR #6267 were not modified.

## Candidate and isolation

The target image is the immutable index
`frappe/erpnext:v16.52.1@sha256:bc21532268c35cec5756c44a11fe510bfccbf23fb4ad651a38644d0c25b56299`.
The native upgraded backend actually reported ERPNext 16.52.1 and Frappe 16.53.0.
Source was the submitted pinned 16.51.1 image, not the floating production tag.
Database, Redis and permissions-image pins were unchanged.

Official cached validator tooling built healthy source/target lab indexes and
validated scoped schema and library hashes. These are isolated lab identities:
package 0.9.0 represents the source and 1.0.0 the target; the actual update
candidate package is 1.1.0. No claim is made that full upstream CI passed.

New app names use `erpnext-upd16521-*`, with independent ixVolumes, credentials,
ports, catalog entries and staging journals. The catalog dataset was snapshotted
before staging; TrueNAS also created native upgrade snapshots. These are ZFS
snapshots, not hypervisor snapshots. Old app data and prior recovery input were
preserved. The three new catalog overlays were removed after successful tests;
installed test apps, backups and staging archives remain.

## Results

| Check | Result |
| --- | --- |
| Native source installation and fixture creation | PASS |
| Native 16.51.1 to 16.52.1 upgrade through app.upgrade | PASS |
| Original record, exact private-attachment bytes and synthetic encrypted value preserved | PASS |
| Nine persistent services healthy; four one-shots exited successfully | PASS |
| Upgraded-app authenticated login and 24 HTML-referenced assets | PASS |
| CSS/JavaScript returned HTTP 200 with appropriate content types | PASS |
| Upgraded-app stop/start; state and backup hashes unchanged | PASS |
| Clean native target installation, login, 24 assets and stop/start | PASS |
| Actual migration failure after a committed test record | PASS |
| Failed app retained source identity, migrating state and checksummed backup | PASS |
| All six ERPNext runtime services blocked after failure and retry | PASS |
| Independent native source-image recovery with different DB credentials/storage | PASS |
| Recovery preserved original data/key; failed-migration record absent | PASS |
| Recovered-app stop/start and repeated data verification | PASS |
| Local Docker actual failure, refused retry, independent recovery and restart | PASS |
| Earlier native failure/recovery state-file fingerprints | UNCHANGED before and after reboot |
| VM reboot persistence; actual boot ID changed | PASS |
| Post-reboot login/assets and authenticated private-file downloads in upgraded/recovered apps | PASS |

The local Docker integration stacks were stopped without removing their data.
The native failed app intentionally remains CRASHED: that is the expected guard
result, not an unexplained failure.

Additional Linux regressions passed: rehearsal 5, restore 6, pinning 9,
interruption 8, coordinator 10, patch 11, queue guard 9, native lifecycle 9,
Compose output 4. Counts include inherited cases. Prior candidate staging,
recovery-helper and rendering regressions also passed during groundwork.
One legacy pinning fixture was corrected to use the candidate catalog version
instead of hardcoding 16.51.1. No runtime guard was weakened.

## Evidence and remaining work

- VM private evidence: `/root/update16521-automated-01/`, including results,
  runner, middleware job diagnostics and generated test credentials.
- Windows generated package: `catalog-dev/generated/update16521-automated-01.tar.gz`;
  SHA256 `6bccdbd08c56d9a3ab82c1866013be81ea90460a6c6804f3e3a580675c7dcafb`.
  All generated bundles and private plans remain ignored by Git.
- Local Docker evidence/storage: `/var/tmp/update-16521-local-plans-01` and
  `/mnt/erpnext-wsl-lab/update-16521-01` in Ubuntu WSL.
- Generated browser logins are saved outside Git at
  `C:\Users\domin\.ssh\erpnext-testvm-test-logins.json`; no passwords are in this report.

The user subsequently reported successful browser login to the upgraded test app and confirmed the expected version.
HTTP authentication/assets and server-side fixture assertions are automated;
interactive browser JavaScript and real business workflows were not exercised.
Full official metadata/CI still needs the approved CDN icon URL and a later full
validation pass. Maintainer review and publication are separate outstanding steps.
No user action or public follow-up was sent automatically.

## Final VM state and user check

- Upgraded target: `erpnext-upd16521-test`, RUNNING at http://172.22.237.80:18093 .
- Independent source-image recovery: `erpnext-upd16521-recovery-test`, RUNNING
  at http://172.22.237.80:18095 (ERPNext 16.51.1, intentionally paused scheduler).
- Fresh target: `erpnext-upd16521-fresh-test`, STOPPED after passing tests, port 18096.
- Deliberate failure: `erpnext-upd16521-failure-test`, CRASHED with runtime blocked.
- Earlier native recovery remains RUNNING, earlier native failure remains CRASHED,
  and earlier normal native app remains STOPPED. No prior test data was removed.

User-reported browser login and version confirmation on the upgraded app (port
18093) passed. No repeated shell-command test group is requested. Full interactive
business-workflow testing is not claimed. Full official CI/icon completion and
maintainer approval remain outstanding.
