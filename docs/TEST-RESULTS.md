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
Restore validation is pending. Follow docs/RESTORE-TEST.md.

| Check | Result |
|---|---|
| Restore to separate app | Pending |
| Customer and Issue restored | Pending |
| Attachment content verified | Pending |
| Source/destination isolation | Pending |
| Restored app restart | Pending |
| Encrypted setting decryption | Not tested |
