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

## Catalog-rendered draft / library 2.3.17

First VM deployment: user reported frontend exit with permission denied writing
`/etc/nginx/conf.d/frappe.conf`. Added supplementary group 0 to the non-root
frontend for the image's group-writable nginx paths. Local render regression
checks passed (two passed, two Linux-only skipped). User subsequently reported
README step 5 passed after the frontend fix.

### Catalog VM checks (user-reported PASS)

- Fresh installation and Administrator login.
- CSS, JavaScript and icons loaded.
- Fictional customer and Issue created; attachment uploaded and opened.
- App stop/start preserved records, assets and attachment.
- VM restart preserved records, assets and attachment.
- Unchanged YAML save did not recreate the site or reset its password.
- Existing apps remained unchanged.

The user reported step 5 as passed; raw logs were not independently inspected.
Whether custom-app mode displayed a Web Portal button was not specified.

Local Windows checks performed by Codex on 2026-10-18, using Python 3.13.9
and apps checkout 85c0b1f21b9ad4e9c667a170a02b5663b9236287.

- Native rendering/dependency test: PASS.
- Host-path rendering, dollar-password escaping and embedded Python parsing: PASS.
- Two Linux bootstrap execution tests: SKIPPED on Windows, as designed.
- Repository port validation: PASS using Python `-X utf8`; the default Windows
  encoding failed while reading another catalog file. No upstream files changed.
- Private deployment YAML was generated and used for the user's VM test.
- These results do not establish middleware/schema validation, official Docker
  CI, catalog upgrade support or catalog acceptance.

### Step 6 local preparation

- Docker Engine 29.1.3 and Compose 2.40.3 installed in Ubuntu WSL.
- All four local tests passed in Linux, including bootstrap image-change and
  unmanaged-storage refusal (no skips).
- Actual upstream metadata helper checks: questions/container enums and image
  registry policy passed. Metadata validation fails on the empty icon URL.
- Upstream 512x512 ERPNext PNG icon candidate prepared in catalog-dev/assets;
  TrueNAS CDN publication remains pending.
- Full official container validation and safe catalog upgrade lifecycle remain
  separate from these local checks.

Official container follow-up: app-scoped library vendoring/hash generation,
catalog schema validation in an isolated Linux catalog, official CI render-only
with metadata skipped, and Docker Compose config validation all passed.
The private VM YAML also passed Compose config validation without starting it.
Full metadata generation remains blocked by the empty icon URL; item.yaml was
generated with the upstream helper. These are not hosted CI or catalog-update
test results. See catalog-dev/VALIDATION.md for the validator digest and scope.
