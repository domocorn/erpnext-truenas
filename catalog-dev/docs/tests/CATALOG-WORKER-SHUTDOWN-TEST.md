# Warm worker shutdown and queue migration checks

The real patch and source-version recovery passed in your VM. This updates only
**erpnext-catalog-patch-test on 18088** using one private YAML file; no new app or
directory is needed. Leave 18087 and the recovered 18089 app unchanged.

The supervisor now signals an RQ worker's PID so its active job can finish.
Sending SIGTERM to its whole process group would also kill the job process.
Both worker services get a 120-second stop grace period. Work longer than the
grace period can still be forcibly stopped; this is bounded shutdown, not an
unlimited job-drain guarantee. RQ describes its warm-stop behavior in the
[worker documentation](https://python-rq.org/docs/workers/).

Before any NEW backup/migration, a read-only queue check refuses queued, started,
deferred, scheduled or failed work requiring review. It does not clear or expire
registry entries. Normal restarts of the already-completed operation can reuse
that operation without migrating again. No automatic replay or job cleanup is
implemented.

## 1. Apply the same-image update

Take a fresh VM snapshot and retain `generated/catalog-patch-01/02-upgrade.yaml`
privately. While the patch-test app is idle, stop it and wait for runtimes to stop.
Apply the complete **generated/catalog-worker-shutdown-01.ui-safe.yaml** and start it.
Use this smaller equivalent file: the original exceeded TrueNAS's WebSocket
request limit after JSON encoding, consistent with the reported immediate
save failure/logout. VM retry with the smaller file is pending.
It uses standard YAML anchors; preserve them when copying the complete file.
Require nine healthy persistent services, successful one-shot exits, ERPNext
16.51.1, existing data/attachments and paused scheduling. Images, operation ID,
credentials and storage paths are preserved; this does not rerun a version upgrade.

## 2. Start a controlled background job

This fixture only runs Python sleep for 60 seconds on the short queue; it does
not send mail, call an external integration or edit business records. In the VM
HOST shell:

```bash
backend=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-catalog-patch-test --filter label=com.docker.compose.service=backend)
# STOP if the lookup is empty or contains multiple IDs.
sudo docker exec "$backend" /home/frappe/frappe-bench/env/bin/python /catalog/worker-drain-test.py enqueue --disposable-patch-test
sudo docker exec "$backend" /home/frappe/frappe-bench/env/bin/python /catalog/worker-drain-test.py guard --disposable-patch-test
```

The first command must print `STARTED: stop the patch-test app now`.
The guard should exit nonzero with `Worker fixture/gate blocked: RuntimeError`
while that job is still running. This is the expected read-only refusal.
If the job did not start, or it already finished before stopping the app, report
that; do not count it as an active-job shutdown pass. Repeating enqueue with the
fixture file already present reports its existing status instead of creating
duplicate jobs.

## 3. Stop while the job is active, then restart

Promptly stop ONLY the patch-test app through TrueNAS while the 60-second job is
still active. Allow it to finish stopping; a warm stop can take the remainder of
the job's runtime. Start the same app again using the unchanged updated YAML.
Require nine healthy persistent services and successful one-shot exits.

Refresh the backend ID and query the fixture:

```bash
backend=$(sudo docker ps -q --filter label=com.docker.compose.project=ix-erpnext-catalog-patch-test --filter label=com.docker.compose.service=backend)
# STOP if the lookup is empty or contains multiple IDs.
sudo docker exec "$backend" /home/frappe/frappe-bench/env/bin/python /catalog/worker-drain-test.py status --disposable-patch-test
sudo docker exec "$backend" /home/frappe/frappe-bench/env/bin/python /catalog/worker-drain-test.py guard --disposable-patch-test
```

Require `Fixture status: finished` and `QUEUE GATE PASSED`. If a job is failed,
started, stopped or missing, preserve worker/initializer logs and report it.
Do not clear registries, force requeue, remove guards or delete the fixture to
make the check pass. Other unresolved jobs can correctly keep the gate blocked.

## 4. Verify normal operation

Check login, records and attachments on 18088, then unchanged YAML save and a VM
restart. Scheduling should remain paused. The finished fixture result is retained
for one day; inspect it promptly. Keep **generated/catalog-worker-shutdown-01.ui-safe.yaml**
as this app's new baseline after success. The other apps may stay stopped.

Report steps 1-4, including whether stopping waited for the active job. The local
lab additionally tested forced worker exit 137 and verified the resulting started
registry entry blocked migration; do not deliberately force-kill VM jobs for this
procedure. This milestone does not enable native catalog upgrades or guarantee
recovery of every job/external side effect.
