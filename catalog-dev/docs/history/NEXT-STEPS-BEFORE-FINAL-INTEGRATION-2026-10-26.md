# Historical snapshot — superseded by ../../NEXT-STEPS.md

2026-10-26 confirmed recovery creation failure: job 9474 failed at template rendering because the library forbids a host_path under /mnt/.ix-apps. No restore ran. native_failure_lab.py now verifies/copies the original backup to private /mnt/labpool/erpnext-native-recovery-input-01, verifies hashes and UID-1000 read permissions, and uses that permitted path read-only. Original backup and failed source remain unchanged. Three new copy/render regression tests (including exact forbidden internal path) and nine helper tests passed; the real copied backup was readable/checksum-valid as UID 1000 in the exact source image. Transfer updated helper only and rerun recover; VM recovery remains pending. No snapshot reset or app deletion required.

2026-10-26 confirmed VM checkpoint: recovery staging role source, no pending operation, journal matches bundle; recovery catalog entry AND app directory are absent (consistent with catalog sync). Recovery app remains uncreated. native_failure_lab.py now restores the missing owned overlay from verified bundle files, backs up the current index, preserves unrelated entries and rejects foreign/modified/concurrently changed content. Nine host-helper tests and a real-metadata repair/reuse check inside the official validator passed. Transfer only updated helper and rerun recover; do not remove the journal or recreate the failed app. VM restore still pending.

2026-10-26 current VM checkpoint: failed-source verification passed; recovery app is absent and its catalog is already staged. Apply the updated native_failure_lab.py helper, then resume recover (step 3). Do not remove the staged entry or repeat the failure test. Native recovery has not yet passed in the VM.

# Current next steps

Updated 2026-10-23. This is the current starting point. Historical status text is
preserved in history/NEXT-STEPS-BEFORE-NATIVE-TEST.md.

## Completed: native catalog install and reviewed upgrade

The user reported NATIVE-CATALOG-TEST.md passed. Middleware showed
`erpnext-native-test`, version `1.0.0`, `RUNNING`, `custom_app: false`, and
`upgrade_available: false`. The user successfully removed that temporary catalog
overlay. This preserves the installed app, its datasets and backup on **18090**.
Do not repeat the successful group or reapply its overlay.

## Next: native failure and independent recovery

Follow [NATIVE-FAILURE-RECOVERY-TEST.md](../tests/NATIVE-FAILURE-RECOVERY-TEST.md), step 1.
Use only the disposable **172.22.237.80 / TrueNAS-25.10.7** VM. This separate
package uses `erpnext-native-failure-test` on **18091** and an automatically
created `erpnext-native-recovery-test` on **18092**, both with fresh ixVolumes.

Transfer only `generated/erpnext-native-failure-recovery-01.tar.gz`. The source,
deliberately failing target and recovery profiles passed official scoped schema,
publication, catalog/version-index, rendering and Compose validation. An actual
local partial native migration, blocked restart, independent source-image restore,
data/private-file/encrypted-value checks and recovery restart all passed. The
failed local source is preserved; both local stacks are stopped. The corresponding
VM test remains pending. Six new safety tests and affected regressions passed.

The runbook's PowerShell commands assume:
`D:\Users\Dominic\Documents\_04 Tech & Coding\GitHub`.
SSH passwords must be entered in your terminal; do not send them in chat. The
agent has no accepted key for unattended VM SSH access.

## After this group

Finish default catalog integration, icon/full metadata and final official
acceptance checks for the final revision. Prepare the contribution for user
review. No extra manual rehearsal group is planned before that final packaging
work unless this test uncovers a defect.

Neither repository has been committed/pushed by the agent. Nothing has been
submitted to TrueNAS, and no maintainer approval is pending. Commit, push and PR
publication remain separate user-authorized actions.

See [../WORKSPACE.md](../../../WORKSPACE.md) for folder handling and
[../docs/TEST-RESULTS.md](../../../docs/TEST-RESULTS.md) for evidence. Generated YAML,
credentials and recovery material remain ignored and private. General upgrades,
production readiness and HexOS curation are not established by the lab results.
