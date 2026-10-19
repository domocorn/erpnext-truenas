# Test record

Deployed initial ERPNext Setup -> Created fake company and added some fake data:
	Database stayed intact through container restarts, server restarts, and opening and saving the YAML with no changes made

## Author-side validation

Python compilation, generated YAML round-trip, and local unit tests are run when
packaging this starter. Five unit tests passed, including interrupted-install and
unmanaged-site refusal, password interpolation, and existing-site preservation.
All Python source parsed successfully. These do not establish real Docker/TrueNAS
compatibility; Docker is unavailable in the authoring environment.

## VM results — user reported successful on 2026-10-18

| Check | Result | Notes |
|---|---|---|
| TrueNAS version | PASS (user reported) | Target 25.10.7 |
| Images pulled | PASS (user reported) | |
| Fresh site/login | PASS (user reported) | |
| Customer/Issue/attachment | PASS (user reported) | |
| App restart | PASS (user reported) | |
| VM restart | PASS (user reported) | |
| Edit/save | PASS (user reported) | |
| Second app isolated | Pending | |

## Backup and restore

Backup command completed and four expected files were listed on 2026-10-18.
Restore validation passed in the test VM, as reported by the tester. See docs/RESTORE-TEST.md for the procedure.

| Check | Result |
|---|---|
| Restore to separate app | PASS |
| Customer and Issue restored | PASS |
| Attachment content verified | PASS |
| Source/destination isolation | PASS |
| Restored app restart | PASS |
| Encrypted setting decryption | Not tested |

## Backup and upgrade

| Check | Result |
|---|---|
| Backup job produced four components and preserved config | PASS |
| Maintenance stages had no running normal services | PASS |
| Deliberate failure blocked guarded resume | PASS |
| Same-version migration completed | PASS |
| Resume restored records and attachment | PASS |
| App restart after resume | PASS |
| Disabled scheduler remained disabled | PASS |
| Real version-to-version upgrade | PASS: 16.51.0 → 16.51.1; see below |
| Recovery from an actual mid-migration failure | NOT TESTED |

## Real upgrade

Before upgrade: ERPNext **16.51.0**, Frappe **16.52.0**.

| Actual version upgrade check | Result / evidence |
|---|---|
| New app initialized on ERPNext 16.51.0 | PASS |
| Pre-upgrade Frappe version | PASS |
| Source-image backup completed | PASS |
| No normal services running during offline stages | PASS |
| Intentional failure blocked startup | PASS |
| Migration with 16.51.1 completed | PASS |
| Post-upgrade ERPNext/site versions | 16.51.1 |
| Post-upgrade Frappe version | 16.52.0 |
| Customer, Issue and attachment survived | PASS |
| New record saved after upgrade | PASS |
| Optional draft invoice/Item survived | N/A |
| App and VM restart preserved upgraded site | PASS |
| Other apps remained isolated | PASS |

Evidence is tester-reported from the TrueNAS 25.10.7 VM; raw logs were not independently inspected.
The real upgrade was one patch transition. Actual mid-migration failure recovery
and encrypted-setting decryption remain untested. Optional draft-invoice testing
was not performed. No claim of general or major-version upgrade compatibility is made.
