# Actual ERPNext v16.51.0 → v16.51.1 acceptance test

Run in the disposable TrueNAS VM only. Fresh source app: **erpnext-version-test**,
port **18083**. Existing apps on 18081/18082 remain untouched. Do not downgrade
an existing site or restore its newer backup into the older image.

## 1. Install the source files

Extract the update into the repository folder and retain your existing generated
files and TEST-RESULTS.md. In PowerShell in that repository:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/build.py --erpnext-version v16.51.0 --site erpnext.test --port 18083 --output generated/erpnext-version-test.yaml
```

Choose a fresh test Administrator password. The generator now refuses to overwrite
an existing output file to protect stored database credentials. Do not regenerate
or edit the password after initializing the database.

## 2. Install a NEW app and create OLD-version data

Install generated/erpnext-version-test.yaml via YAML in TrueNAS as the NEW app
**erpnext-version-test**. Do not edit either existing test app. Let the initializer
finish. Visit http://VM-IP:18083 and finish the wizard with fictional information.
If image pulling fails, stop and report the image error; release existence alone
does not prove Docker registry availability.

In this new app's backend shell:

```bash
cd /home/frappe/frappe-bench
bench version
```

Record the ERPNext and Frappe versions. ERPNext must be **16.51.0**. Stop if not.
Create recognizable test records, e.g. Customer `VERSION-UPGRADE-CUSTOMER`, an
Issue linked to that customer, and one harmless attachment with known contents.
Optionally add a non-stock service Item and a DRAFT Sales Invoice, recording its
number and total. Do not submit fictional transactions on the business NAS.

Verify the records and attachment open. Take a powered-off VMware snapshot now,
then boot the VM again. This snapshot is the clean old-version starting point.

## 3. Generate a REAL upgrade (no --rehearsal)

In Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_upgrade.py --from-config generated/erpnext-version-test.yaml --target v16.51.1 --numbered-stages --output-dir generated/real-upgrade-16510-to-16511
```

This preserves database credentials, volumes, web port, and infrastructure image
versions. All generated YAML contains credentials; do not commit it.

Distinct stages:

| File | Expected result |
|---|---|
| 01-backup.yaml | Source v16.51.0 backs up successfully |
| 02-simulated-failure.yaml | Intentional failure before database patches |
| 03-verify-startup-blocked.yaml | Initializer refuses startup |
| 04-migrate.yaml | Target v16.51.1 applies migration |
| 05-resume.yaml | Target runtime starts after successful migration |

The blocked-startup and final-resume files intentionally contain the same guarded
configuration. The persistent operation state determines whether startup succeeds.

## 4. Stop the app before replacing each stage

Use this same stop/verify routine before applying EACH YAML below. In the
TrueNAS HOST shell (not inside a container), run:

```bash
sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-version-test | xargs -r sudo docker stop --time 60
sudo docker ps --filter label=com.docker.compose.project=ix-erpnext-version-test --format '{{.Names}}'
```

The second command must produce no names. It stops only this test project's
running containers, including its database. Volumes are retained. Do not use
`down -v`. If any container remains running, stop and inspect before editing.

In TrueNAS, edit the SAME **erpnext-version-test** app with the desired stage's
complete YAML. Save and start if necessary. Never create another app from a stage.
Wait for the stage to finish and inspect its logs before proceeding.

## 5. Apply the stages in this exact order

1. Stop/verify; apply **01-backup.yaml**. `upgrade-job` must exit 0 and report
   `BACKUP COMPLETE`. Inspect its recovery directory path in the logs. Only db,
   redis-cache, redis-queue and upgrade-job may run; normal runtime must be absent.
2. Stop/verify; apply **02-simulated-failure.yaml**. Expected nonzero exit:
   `EXPECTED TEST FAILURE before migration`. No database patch has run.
3. Stop/verify; apply **03-verify-startup-blocked.yaml**. Expected initializer
   error: `Migration has not succeeded; startup blocked.` No web access or workers.
4. Stop/verify; apply **04-migrate.yaml**. `upgrade-job` must exit 0 and report
   `MIGRATION COMPLETE`. This is the actual new-version migration.
5. Stop/verify; apply **05-resume.yaml**. Configurator and initializer exit 0;
   normal runtime starts. Previous scheduler/maintenance settings are restored.

An expected failure may make TrueNAS display Crashed/Error/Degraded. Use the
host-shell stop routine above before moving to the next stage. Do not restore the
original old YAML or reuse configurations from another operation. If any failure
is NOT the explicitly simulated failure or blocked startup, stop and send logs.
An actual migration failure leaves blocking state and must not be blindly retried.

## 6. Prove the version changed and data survived

Open http://VM-IP:18083. In the resumed app's backend shell:

```bash
cd /home/frappe/frappe-bench
bench version
bench --site erpnext.test list-apps
```

Record both outputs. ERPNext must now report **16.51.1**, and the site's installed
app list should reflect the new version after migration. Frappe's version does
not have to numerically equal ERPNext's version.

Verify:

- Customer, linked Issue, and attachment contents survived.
- Optional draft invoice/Item remain and totals match.
- A new post-upgrade Issue can be saved.
- Source apps on 18081/18082 are unchanged.
- Stop/start this app, then restart the VM; repeat login and record checks.

Keep 05-resume.yaml as this app's current deployment configuration. Future upgrade
plans for THIS app must use that file as --from-config.

## 7. Record evidence, then commit source and results

Append this table to docs/TEST-RESULTS.md and fill only verified results:

| Actual version upgrade check | Result / evidence |
|---|---|
| New app initialized on ERPNext 16.51.0 | Pending |
| Pre-upgrade Frappe version | Pending |
| Source-image backup completed | Pending |
| No normal services running during offline stages | Pending |
| Intentional failure blocked startup | Pending |
| Migration with 16.51.1 completed | Pending |
| Post-upgrade ERPNext/site versions | Pending |
| Post-upgrade Frappe version | Pending |
| Customer, Issue and attachment survived | Pending |
| New record saved after upgrade | Pending |
| Optional draft invoice/Item survived | Pending or N/A |
| App and VM restart preserved upgraded site | Pending |
| Other apps remained isolated | Pending |

Do not mark recovery from an ACTUAL mid-migration failure as passed: the injected
failure occurs before database patches. A successful patch upgrade also does not
validate every future v16 upgrade or a major-version upgrade.

The cleanup of old restore-input/staging folders is optional for the disposable
lab. Do not delete private/nas-upgrades, original backup files or the upgrade-state
file to make an operation retry. Retain recovery material until testing completes.

## Upstream releases

- https://github.com/frappe/erpnext/releases/tag/v16.51.0
- https://github.com/frappe/erpnext/releases/tag/v16.51.1
