# Verify the healthcheck revision in the disposable VM

The local WSL stack is separate from your TrueNAS VM. Do these VM checks when
convenient; the VM can remain shut down until then.

1. Start the test VM and take a snapshot of the passing baseline.
2. Edit the existing `erpnext-catalog-test` app. Use the complete private file
   `catalog-dev/generated/catalog-test.healthchecks-ready.yaml` from erpnext-truenas.
   Keep the original `catalog-test.yaml`. Do not regenerate passwords or select
   new storage. If the installed YAML changed since that original was saved,
   export the exact current YAML and use it as input to the helper below first.
3. Save and allow startup and healthchecks to settle. The six runtime services
   (backend, frontend, websocket, queue-short, queue-long and scheduler) should
   report healthy. Database and both Redis services should also report healthy.
   Permissions, bootstrap and initializer are one-shot services: exited with
   status 0 is expected; they do not run continuous healthchecks.
4. If a runtime service remains unhealthy after five minutes, stop/start the app
   to ensure its inline config is reloaded. WSL Compose needed runtime recreation
   after the config changed. Send the failing service's health output and final
   log lines if the problem persists. Do not alter permissions or remove guards.
5. Use the portal, log in, and verify the existing customer, Issue and attachment.
   Stop/start the app once and verify all runtime services return healthy and the
   data remains. Record results separately from the earlier fresh-install pass.

These probes do not restart unhealthy containers automatically. Worker checks
verify local RQ heartbeat, queue membership and dependencies; they do not prove
every submitted job succeeds. Scheduler checks verify the local process lock and
dependencies; a paused scheduler is valid and a lock cannot prove event-loop
progress. Probes never enable scheduling or enqueue test jobs.

## Prepare a fresh update from the exact installed YAML

Run in the erpnext-truenas repository, using a new private output filename:

```powershell
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/prepare_healthcheck_update.py --installed-yaml catalog-dev/generated/catalog-test.yaml --apps-root ..\apps --output catalog-dev/generated/catalog-test.healthchecks-ready.yaml
```

The helper refuses existing output and mismatched runtime images. It changes only
the health config, runtime healthchecks, config mounts and SITE_NAME environment
values. Credentials, images, storage, bootstrap marker identity and initialization
remain from the exact input. It does not deploy anything.
