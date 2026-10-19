# Verify the same-image runtime guard in the disposable VM

Prerequisite: HEALTHCHECK-TEST.md checks 1-5 passed. No image upgrade or migration
is included in this test.

1. Take a snapshot of the passing VM baseline. Keep its exact installed private
   YAML. The prepared `generated/catalog-test.runtime-guards.yaml` was based on
   `generated/catalog-test.healthchecks-ready.yaml`; if your installed YAML has
   changed since then, export it and prepare a new output using the helper below.
2. Stop `erpnext-catalog-test` in TrueNAS and wait until its runtime services stop.
   This explicitly retires the old containers that do not yet hold runtime locks.
3. Edit the same app using the complete runtime-guards YAML, then start it if
   saving did not start it. Retain the same images, directories and credentials.
4. Allow startup to settle. Six runtime services, MariaDB and both Redis services
   should report healthy. One-shot permissions/bootstrap/initializer should exit
   0. A short assets-linking message is expected; no migration runs.
5. Use the portal and verify login, CSS/JS, the existing customer, Issue and
   attachment. Stop/start once and repeat health and persistence checks.
6. Save unchanged YAML once. Verify startup, healthy services and unchanged data.
   Record results and any service that failed. Do not remove lock files or image
   guards to work around a failure; send the service and final logs instead.

This verifies the guard rollout only. Do not change image tags, edit state files,
or test failed-migration state manually in the VM yet. Lock exclusion and rejection
of unfinished state are tested separately in the local disposable lab.

## Prepare from an exact installed configuration

Run from erpnext-truenas, choosing a fresh private output filename:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_runtime_update.py --installed-yaml catalog-dev/generated/catalog-test.healthchecks-ready.yaml --apps-root ..\apps --output catalog-dev/generated/catalog-test.runtime-guards.yaml
```

The helper does not overwrite input or existing output. It rejects unexpected
runtime image changes and custom entrypoints, preserving data services, storage,
credentials and commands while adding runtime gates and current health probes.
